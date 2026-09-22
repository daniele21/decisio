from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from decisio.benchmark import run_benchmark
from decisio.comparison import run_comparison
from decisio.schema import ChoiceRequest


@dataclass
class FakeResult:
    choice: str | None
    scorer: str
    generated_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice": self.choice,
            "scorer": self.scorer,
            "generated_tokens": self.generated_tokens,
        }


class TimingBackend:
    def __init__(self):
        self.sync_calls = 0
        self.reset_calls = 0

    @property
    def identity(self):
        return {
            "backend": "fake",
            "device": "cpu",
            "dtype": "bfloat16",
            "memory_metric": "process_max_rss",
        }

    def synchronize(self):
        self.sync_calls += 1

    def reset_peak_memory(self):
        self.reset_calls += 1

    def peak_memory_bytes(self):
        return 1024


class FakeScorer:
    def __init__(
        self,
        name: str,
        choices: dict[str, str | None],
        *,
        reverse_choices: dict[str, str | None] | None = None,
        generated_tokens: int = 0,
        backend: Any | None = None,
    ):
        self.name = name
        self.choices = choices
        self.reverse_choices = reverse_choices or {}
        self.generated_tokens = generated_tokens
        self.backend = backend

    def score(self, request: ChoiceRequest) -> FakeResult:
        assert request.id is not None
        is_reversed = request.candidates[0].id == "no"
        choice = (
            self.reverse_choices.get(request.id, self.choices[request.id])
            if is_reversed
            else self.choices[request.id]
        )
        return FakeResult(choice, self.name, self.generated_tokens)


def _write_fixture(path: Path) -> None:
    rows = [
        {
            "id": "a",
            "family": "routing",
            "state": "a",
            "question": "choose",
            "candidates": [
                {"id": "yes", "description": "yes"},
                {"id": "no", "description": "no"},
            ],
            "label": "yes",
        },
        {
            "id": "b",
            "family": "routing",
            "state": "b",
            "question": "choose",
            "candidates": [
                {"id": "yes", "description": "yes"},
                {"id": "no", "description": "no"},
            ],
            "label": "no",
        },
        {
            "id": "c",
            "family": "policy",
            "state": "c",
            "question": "choose",
            "candidates": [
                {"id": "yes", "description": "yes"},
                {"id": "no", "description": "no"},
            ],
            "label": "yes",
        },
        {
            "id": "d",
            "family": "policy",
            "state": "d",
            "question": "choose",
            "candidates": [
                {"id": "yes", "description": "yes"},
                {"id": "no", "description": "no"},
            ],
            "label": "no",
        },
    ]
    path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_benchmark_reports_invalid_and_family_breakdown(tmp_path: Path):
    input_path = tmp_path / "fixture.jsonl"
    output_path = tmp_path / "result.jsonl"
    _write_fixture(input_path)
    scorer = FakeScorer(
        "fake",
        {"a": "yes", "b": None, "c": "yes", "d": "yes"},
        generated_tokens=2,
    )
    summary = run_benchmark(input_path, output_path, scorer)
    assert summary["examples"] == 4
    assert summary["correct"] == 2
    assert summary["invalid"] == 1
    assert summary["invalid_rate"] == 0.25
    assert summary["generated_tokens"] == 8
    assert summary["families"]["routing"]["accuracy"] == 0.5
    assert summary["families"]["routing"]["invalid"] == 1
    assert summary["families"]["policy"]["accuracy"] == 0.5


def _comparison_scorers(*, backend: Any | None = None):
    truth = {"a": "yes", "b": "no", "c": "yes", "d": "no"}
    return {
        "semantic": FakeScorer("semantic-v2", truth, backend=backend),
        "semantic-independent": FakeScorer(
            "semantic-v1",
            {"a": "yes", "b": "yes", "c": "yes", "d": "no"},
            backend=backend,
        ),
        "letters": FakeScorer(
            "letters",
            truth,
            reverse_choices={"a": "no"},
            backend=backend,
        ),
        "generated": FakeScorer(
            "generated",
            {"a": "yes", "b": "no", "c": None, "d": "no"},
            generated_tokens=3,
            backend=backend,
        ),
    }


def test_comparison_is_paired_and_measures_order_sensitivity(tmp_path: Path):
    input_path = tmp_path / "fixture.jsonl"
    output_dir = tmp_path / "matrix"
    _write_fixture(input_path)

    report = run_comparison(input_path, output_dir, _comparison_scorers())

    assert report["examples"] == 4
    assert report["schema_version"] == 2
    assert report["performance"]["enabled"] is False
    assert report["scorers"]["semantic"]["normal"]["accuracy"] == 1.0
    assert report["scorers"]["letters"]["order_sensitivity"]["choice_changes"] == 1
    assert report["scorers"]["generated"]["normal"]["invalid"] == 1

    paired_v1 = report["paired_vs_primary"]["semantic-independent"]["none"]
    assert paired_v1["primary_only_correct"] == 1
    assert paired_v1["baseline_only_correct"] == 0
    assert paired_v1["accuracy_delta"] == 0.25

    paired_generated = report["paired_vs_primary"]["generated"]["none"]
    assert paired_generated["primary_only_correct"] == 1
    assert paired_generated["baseline_only_correct"] == 0

    assert (output_dir / "comparison.json").is_file()
    markdown = (output_dir / "comparison.md").read_text(encoding="utf-8")
    assert "Paired correctness versus semantic v2" in markdown
    assert "integration/directional evidence only" in markdown


def test_comparison_performance_trials_rotate_order_and_capture_memory(tmp_path: Path):
    input_path = tmp_path / "fixture.jsonl"
    output_dir = tmp_path / "matrix"
    _write_fixture(input_path)
    backend = TimingBackend()

    report = run_comparison(
        input_path,
        output_dir,
        _comparison_scorers(backend=backend),
        warmup_rounds=1,
        performance_rounds=4,
    )

    performance = report["performance"]
    assert performance["enabled"] is True
    assert performance["warmup_rounds"] == 1
    assert performance["measured_rounds"] == 4
    assert len({tuple(order) for order in performance["execution_order"]}) == 4
    assert performance["backend_identity"]["device"] == "cpu"
    assert performance["memory_metric"] == "process_max_rss"
    assert performance["scorers"]["semantic"]["peak_memory_bytes"]["max"] == 1024
    assert performance["scorers"]["semantic"]["duration_seconds"]["p95"] >= 0.0
    assert backend.reset_calls == 20
    assert backend.sync_calls == 40


def test_comparison_rejects_warmup_without_measurement(tmp_path: Path):
    input_path = tmp_path / "fixture.jsonl"
    _write_fixture(input_path)

    try:
        run_comparison(
            input_path,
            tmp_path / "matrix",
            _comparison_scorers(),
            warmup_rounds=1,
        )
    except ValueError as exc:
        assert "requires performance_rounds" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected invalid performance configuration")
