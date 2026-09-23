from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from decisio.benchmark import run_benchmark
from decisio.compiler import (
    compile_independent_semantic_candidate,
    compile_letter_choice,
    compile_semantic_candidate,
)
from decisio.math import binary_log_odds, softmax
from decisio.schema import Candidate, ChoiceRequest
from decisio.scorers import (
    IndependentSemanticScorer,
    LetterTokenScorer,
    SemanticBinaryScorer,
)


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
        self.batch_calls = []

    @property
    def identity(self):
        return {"backend": "fake", "model": "unit-test"}

    def next_token_logits(self, input_ids, token_ids):
        self.calls.append((input_ids, token_ids))
        response = self.responses.pop(0)
        assert len(response) == len(token_ids)
        return response

    def batch_next_token_logits(self, input_ids_batch, token_ids_batch):
        self.batch_calls.append((input_ids_batch, token_ids_batch))
        responses = self.responses[: len(input_ids_batch)]
        del self.responses[: len(input_ids_batch)]
        assert len(responses) == len(input_ids_batch)
        for response, token_ids in zip(responses, token_ids_batch, strict=True):
            assert len(response) == len(token_ids)
        return responses


class SharedPrefixQueueBackend(QueueBackend):
    def __init__(self, responses):
        super().__init__(responses)
        self.shared_prefix_calls = []

    def shared_prefix_batch_next_token_logits(self, input_ids_batch, token_ids_batch):
        self.shared_prefix_calls.append((input_ids_batch, token_ids_batch))
        responses = self.responses[: len(input_ids_batch)]
        del self.responses[: len(input_ids_batch)]
        assert len(responses) == len(input_ids_batch)
        for response, token_ids in zip(responses, token_ids_batch, strict=True):
            assert len(response) == len(token_ids)
        return responses


class ReusablePrefixQueueBackend(SharedPrefixQueueBackend):
    supports_reusable_prefix_hint = True

    def shared_prefix_batch_next_token_logits(
        self,
        input_ids_batch,
        token_ids_batch,
        *,
        reusable_prefix_len=None,
    ):
        self.shared_prefix_calls.append(
            (input_ids_batch, token_ids_batch, reusable_prefix_len)
        )
        responses = self.responses[: len(input_ids_batch)]
        del self.responses[: len(input_ids_batch)]
        return responses


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


def test_comparative_semantic_compiler_contains_all_alternatives():
    item = request()
    compiled = compile_semantic_candidate(FakeTokenizer(), item, item.candidates[0])
    assert "Payments and invoices" in compiled.prompt
    assert "Software bugs" in compiled.prompt
    assert "Purchasing discussions" in compiled.prompt
    assert "billing" not in compiled.prompt
    assert "best answer among the supplied alternatives" in compiled.prompt
    assert compiled.readout == {"yes": 10, "no": 11}
    assert compiled.reusable_prefix_len is not None
    assert 0 < compiled.reusable_prefix_len < len(compiled.input_ids)


def test_reusable_state_prefix_is_stable_across_questions():
    item = request()
    other = ChoiceRequest(
        id="other",
        state=item.state,
        question="Which specialist should receive this?",
        candidates=item.candidates,
    )
    left = compile_semantic_candidate(FakeTokenizer(), item, item.candidates[0])
    right = compile_semantic_candidate(FakeTokenizer(), other, other.candidates[0])
    assert left.reusable_prefix_len is not None
    assert right.reusable_prefix_len is not None
    left_prefix = left.input_ids[: left.reusable_prefix_len]
    right_prefix = right.input_ids[: right.reusable_prefix_len]
    assert left_prefix == right_prefix


def test_comparative_prompt_is_invariant_to_candidate_presentation_order():
    item = request()
    candidate = item.candidates[0]
    reversed_request = ChoiceRequest(
        id=item.id,
        state=item.state,
        question=item.question,
        candidates=tuple(reversed(item.candidates)),
    )
    left = compile_semantic_candidate(FakeTokenizer(), item, candidate)
    right = compile_semantic_candidate(FakeTokenizer(), reversed_request, candidate)
    assert left.prompt == right.prompt
    assert left.sha256 == right.sha256


def test_independent_compiler_remains_available_as_v1_baseline():
    item = request()
    compiled = compile_independent_semantic_candidate(
        FakeTokenizer(), item, item.candidates[0]
    )
    assert "ALTERNATIVES" not in compiled.prompt
    assert "Does this candidate correctly answer" in compiled.prompt


def test_letter_compiler_maps_ids_to_distinct_tokens():
    compiled = compile_letter_choice(FakeTokenizer(), request())
    assert compiled.readout == {"billing": 100, "technical": 101, "sales": 102}


def test_semantic_scorer_batches_candidate_prompts():
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
    assert result.scorer == "semantic_comparative_logodds_v2"
    assert result.generated_tokens == 0
    assert result.probability_status == "uncalibrated_conditional_scores"
    assert result.binary_conditional_probability.keys() == result.scores.keys()
    assert math.isclose(
        result.binary_conditional_probability["billing"],
        softmax([5.0, 1.0])[0],
    )
    assert math.isclose(result.binary_conditional_probability["technical"], 0.5)
    assert math.isclose(
        result.binary_conditional_probability["sales"],
        softmax([0.0, 3.0])[0],
    )
    assert math.isclose(sum(result.distribution.values()), 1.0)
    assert len(backend.batch_calls) == 1
    assert backend.calls == []


def test_semantic_scorer_prefers_shared_prefix_backend_capability():
    backend = SharedPrefixQueueBackend(
        [[5.0, 1.0], [2.0, 2.0], [0.0, 3.0]]
    )
    result = SemanticBinaryScorer(backend).score(request())
    assert result.choice == "billing"
    assert len(backend.shared_prefix_calls) == 1
    assert backend.batch_calls == []
    assert backend.calls == []


def test_semantic_scorer_passes_reusable_prefix_hint_when_supported():
    backend = ReusablePrefixQueueBackend(
        [[5.0, 1.0], [2.0, 2.0], [0.0, 3.0]]
    )
    SemanticBinaryScorer(backend).score(request())
    assert len(backend.shared_prefix_calls) == 1
    _, _, reusable_prefix_len = backend.shared_prefix_calls[0]
    assert reusable_prefix_len is not None
    assert reusable_prefix_len > 0


def test_independent_scorer_keeps_v1_semantics_but_uses_batch_runtime():
    backend = QueueBackend([[5.0, 1.0], [2.0, 2.0], [0.0, 3.0]])
    result = IndependentSemanticScorer(backend).score(request())
    assert result.scorer == "semantic_binary_logodds_v1"
    assert result.choice == "billing"
    assert len(backend.batch_calls) == 1


def test_letter_scorer_is_a_single_forward_baseline():
    backend = QueueBackend([[1.0, 4.0, -1.0]])
    result = LetterTokenScorer(backend).score(request())
    assert result.choice == "technical"
    assert result.binary_conditional_probability == {}
    assert "binary_conditional_probability" not in result.to_dict()
    assert len(backend.calls) == 1


def test_letter_prefix_reuse_matches_compiler_hint_and_falls_back_fresh():
    backend = ReusablePrefixQueueBackend([[1.0, 4.0, -1.0]])
    result = LetterTokenScorer(backend, reuse_prefix=True).score(request())
    compiled = compile_letter_choice(backend.tokenizer, request(), reuse_prefix=True)
    inputs, _, hint = backend.shared_prefix_calls[0]
    assert inputs == [compiled.input_ids]
    assert hint == compiled.reusable_prefix_len
    assert hint > 0
    assert compiled.prompt.index("QUESTION:") < compiled.prompt.index("EVIDENCE:")
    fresh = QueueBackend([[1.0, 4.0, -1.0]])
    oracle = LetterTokenScorer(fresh, reuse_prefix=True).score(request())
    assert result.scores == oracle.scores
    assert result.prompt_sha256 == oracle.prompt_sha256
    assert fresh.calls[0][0] == compiled.input_ids


def test_letter_stateful_prompt_can_force_fresh_execution_without_prompt_change():
    shared_backend = ReusablePrefixQueueBackend([[1.0, 4.0, -1.0]])
    shared = LetterTokenScorer(
        shared_backend,
        reuse_prefix=True,
        shared_prefix_execution=True,
    ).score(request())

    fresh_backend = ReusablePrefixQueueBackend([[1.0, 4.0, -1.0]])
    fresh = LetterTokenScorer(
        fresh_backend,
        reuse_prefix=True,
        shared_prefix_execution=False,
    ).score(request())

    assert shared.prompt_sha256 == fresh.prompt_sha256
    assert shared.scores == fresh.scores
    assert len(shared_backend.shared_prefix_calls) == 1
    assert fresh_backend.shared_prefix_calls == []
    assert len(fresh_backend.calls) == 1


def test_letter_prefix_excludes_changing_state():
    first = request()
    second = ChoiceRequest(state={"different": "state"}, question=first.question,
                           candidates=first.candidates)
    left = compile_letter_choice(FakeTokenizer(), first, reuse_prefix=True)
    right = compile_letter_choice(FakeTokenizer(), second, reuse_prefix=True)
    assert left.reusable_prefix_len == right.reusable_prefix_len
    size = left.reusable_prefix_len
    assert left.input_ids[:size] == right.input_ids[:size]
    assert left.input_ids[size:] != right.input_ids[size:]




def test_semantic_scorer_breaks_exact_ties_by_candidate_id():
    backend = QueueBackend([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]])
    result = SemanticBinaryScorer(backend).score(request())
    assert result.choice == "billing"


def test_letter_scorer_breaks_exact_ties_by_candidate_id():
    backend = QueueBackend([[1.0, 1.0, 1.0]])
    result = LetterTokenScorer(backend).score(request())
    assert result.choice == "billing"

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
    assert record["result"]["binary_conditional_probability"]["billing"] > 0.98
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
