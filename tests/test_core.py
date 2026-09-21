from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from decisio.benchmark import run_benchmark
from decisio.compiler import compile_letter_choice, compile_semantic_candidate
from decisio.math import binary_log_odds, softmax
from decisio.schema import Candidate, ChoiceRequest
from decisio.scorers import LetterTokenScorer, SemanticBinaryScorer


class FakeTokenizer:
    """Character tokenizer with explicit one-token generation readouts."""

    SPECIAL = {"Yes": 10, "No": 11, **{chr(65 + i): 100 + i for i in range(26)}}

    def apply_chat_template(
        self, messages, *, tokenize=False, add_generation_prompt=True, **kwargs
    ):
        assert tokenize is False
        body = "".join(f"<{m['role']}>\n{m['content']}\n" for m in messages)
        return body + ("<assistant>\n" if add_generation_prompt else "")

    def encode(self, text, *, add_special_tokens=False):
        del add_special_tokens
        for literal, token_id in self.SPECIAL.items():
            if text.endswith(literal):
                prefix = text[: -len(literal)]
                return [1000 + ord(char) for char in prefix] + [token_id]
        return [1000 + ord(char) for char in text]


class QueueBackend:
    def __init__(self, responses):
        self.tokenizer = FakeTokenizer()
        self.responses = list(responses)
        self.calls = []

    @property
    def identity(self):
        return {"backend": "fake", "model": "unit-test"}

    def next_token_logits(self, input_ids, token_ids):
        self.calls.append((input_ids, token_ids))
        response = self.responses.pop(0)
        assert len(response) == len(token_ids)
        return response


def request():
    return ChoiceRequest(
        id="example",
        state="Duplicate card charge",
        question="Which queue?",
        candidates=(
            Candidate("billing", "Payments and invoices"),
            Candidate("technical", "Software bugs"),
            Candidate("sales", "Purchasing discussions"),
        ),
    )


def test_softmax_and_log_odds():
    assert binary_log_odds(3.5, 1.0) == 2.5
    values = softmax([0.0, 1.0, 2.0])
    assert math.isclose(sum(values), 1.0)
    assert values[2] > values[1] > values[0]


def test_semantic_compiler_keeps_candidate_ids_out_of_prompt():
    item = request()
    compiled = compile_semantic_candidate(FakeTokenizer(), item, item.candidates[0])
    assert "Payments and invoices" in compiled.prompt
    assert "billing" not in compiled.prompt
    assert compiled.readout == {"yes": 10, "no": 11}


def test_letter_compiler_maps_ids_to_distinct_tokens():
    compiled = compile_letter_choice(FakeTokenizer(), request())
    assert compiled.readout == {"billing": 100, "technical": 101, "sales": 102}


def test_semantic_scorer_uses_yes_no_log_odds():
    backend = QueueBackend(
        [
            [5.0, 1.0],  # billing +4
            [2.0, 2.0],  # technical 0
            [0.0, 3.0],  # sales -3
        ]
    )
    result = SemanticBinaryScorer(backend).score(request())
    assert result.choice == "billing"
    assert result.scores == {"billing": 4.0, "technical": 0.0, "sales": -3.0}
    assert result.generated_tokens == 0
    assert result.probability_status == "uncalibrated_conditional_scores"
    assert math.isclose(sum(result.distribution.values()), 1.0)
    assert len(backend.calls) == 3


def test_letter_scorer_is_a_single_forward_baseline():
    backend = QueueBackend([[1.0, 4.0, -1.0]])
    result = LetterTokenScorer(backend).score(request())
    assert result.choice == "technical"
    assert len(backend.calls) == 1


def test_request_rejects_duplicate_candidate_ids():
    with pytest.raises(ValueError, match="unique"):
        ChoiceRequest(
            state="x",
            question="q",
            candidates=(Candidate("same", "one"), Candidate("same", "two")),
        )


def test_benchmark_writes_auditable_jsonl(tmp_path: Path):
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"
    row = request().to_dict() | {"label": "billing"}
    input_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    backend = QueueBackend([[5.0, 1.0], [2.0, 2.0], [0.0, 3.0]])
    summary = run_benchmark(input_path, output_path, SemanticBinaryScorer(backend))
    assert summary["accuracy"] == 1.0
    record = json.loads(output_path.read_text(encoding="utf-8"))
    assert record["correct"] is True
    assert record["result"]["generated_tokens"] == 0
    assert record["result"]["model"]["model"] == "unit-test"


class GenerationQueueBackend(QueueBackend):
    def __init__(self, generated_text, generated_tokens):
        super().__init__([])
        self.generated_text = generated_text
        self.generated_token_count = generated_tokens

    def generate(self, input_ids, *, max_new_tokens):
        assert input_ids
        assert max_new_tokens > 0
        return self.generated_text, self.generated_token_count


def test_generated_json_baseline_counts_generated_tokens():
    from decisio.baselines import GeneratedJsonScorer

    backend = GenerationQueueBackend('{"choice":"billing"}', 6)
    result = GeneratedJsonScorer(backend).score(request())
    assert result.choice == "billing"
    assert result.valid is True
    assert result.generated_tokens == 6


def test_generated_json_baseline_rejects_invalid_output():
    from decisio.baselines import GeneratedJsonScorer

    backend = GenerationQueueBackend("Billing because it is a payment issue.", 9)
    result = GeneratedJsonScorer(backend).score(request())
    assert result.choice is None
    assert result.valid is False


def test_benchmark_can_reverse_candidate_order(tmp_path: Path):
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"
    row = request().to_dict() | {"label": "billing"}
    input_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    # Reversed candidates are sales, technical, billing.
    backend = QueueBackend([[0.0, 3.0], [2.0, 2.0], [5.0, 1.0]])
    summary = run_benchmark(
        input_path,
        output_path,
        SemanticBinaryScorer(backend),
        reverse_candidates=True,
    )
    assert summary["perturbation"] == "reverse_candidates"
    assert len(summary["input_sha256"]) == 64
