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


class FakeScorer:
    def __init__(
        self,
        name: str,
        choices: dict[str, str | None],
        *,
        reverse_choices: dict[str, str | None] | None = None,
        generated_tokens: int = 0,
    ):
        self.name = name
        self.choices = choices
        self.reverse_choices = reverse_choices or {}
        self.generated_tokens = generated_tokens

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


def test_comparison_is_paired_and_measures_order_sensitivity(tmp_path: Path):
    input_path = tmp_path / "fixture.jsonl"
    output_dir = tmp_path / "matrix"
    _write_fixture(input_path)

    truth = {"a": "yes", "b": "no", "c": "yes", "d": "no"}
    scorers = {
        "semantic": FakeScorer("semantic-v2", truth),
        "semantic-independent": FakeScorer(
            "semantic-v1",
            {"a": "yes", "b": "yes", "c": "yes", "d": "no"},
        ),
        "letters": FakeScorer(
            "letters",
            truth,
            reverse_choices={"a": "no"},
        ),
        "generated": FakeScorer(
            "generated",
            {"a": "yes", "b": "no", "c": None, "d": "no"},
            generated_tokens=3,
        ),
    }

    report = run_comparison(input_path, output_dir, scorers)

    assert report["examples"] == 4
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
