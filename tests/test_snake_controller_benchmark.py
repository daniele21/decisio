import json
from pathlib import Path

from benchmarks.snake_controller_benchmark import (
    CONFIGS,
    SnakePlanner,
    append_ledger,
    fixed_state_benchmark,
    game_from_case,
)
from benchmarks.summarize_snake_controller_history import summarize
from decisio.schema import DecisionResult


class FirstCandidateScorer:
    name = "first-candidate-test"

    def score(self, request):
        choice = request.candidates[0].id
        return DecisionResult(
            choice=choice,
            distribution={
                candidate.id: float(candidate.id == choice)
                for candidate in request.candidates
            },
            scores={
                candidate.id: float(candidate.id == choice)
                for candidate in request.candidates
            },
            scorer=self.name,
        )


def _case():
    return {
        "id": "easy-up",
        "family": "direct-food",
        "width": 8,
        "height": 8,
        "snake": [[4, 4], [3, 4], [2, 4]],
        "direction": "right",
        "food": [4, 1],
    }


def test_stateful_and_fresh_direct_compare_same_prompt_mode():
    shared = CONFIGS["direct-stateful-verbose"]
    fresh = CONFIGS["direct-fresh-verbose"]

    assert shared.prompt_mode == fresh.prompt_mode == "question-first-stateful"
    assert shared.execution_mode == "shared"
    assert fresh.execution_mode == "fresh"


def test_game_from_case_restores_benchmark_state():
    game = game_from_case(_case())
    assert game.head == (4, 4)
    assert game.direction == "right"
    assert game.food == (4, 1)


def test_fixed_state_benchmark_measures_oracle_and_order_sensitivity():
    summary = fixed_state_benchmark(
        [_case()],
        FirstCandidateScorer(),
        CONFIGS["direct-stateful-verbose"],
        SnakePlanner(max_nodes=10_000),
    )

    assert summary["optimal_set_agreement"] == 1.0
    assert summary["mean_rank_regret"] == 0.0
    assert summary["order_change_rate"] == 1.0
    assert summary["records"][0]["choice"] == "up"
    assert summary["records"][0]["reversed_choice"] == "down"


def test_ledger_is_append_only_and_preserves_parameters(tmp_path: Path):
    ledger = tmp_path / "history.jsonl"
    first = {
        "run_id": "a",
        "configuration": {"id": "direct"},
        "model_runtime": {"artifact_sha256": "1"},
    }
    second = {
        "run_id": "b",
        "configuration": {"id": "semantic"},
        "model_runtime": {"artifact_sha256": "2"},
    }

    append_ledger(ledger, first)
    append_ledger(ledger, second)

    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert rows == [first, second]


def test_history_summary_keeps_model_fixture_and_protocol_identity_separate():
    records = [
        {
            "record_type": "run_start",
            "run_id": "run-a",
            "model_runtime": {"artifact_sha256": "model-a"},
            "fixture": {"sha256": "fixture-a"},
            "protocol": {"sha256": "protocol-a"},
        },
        {
            "status": "completed",
            "finished_at": "2026-09-23T10:00:00Z",
            "configuration": {"id": "direct-stateful-verbose"},
            "model_runtime": {"artifact_sha256": "model-a"},
            "fixture": {"sha256": "fixture-a"},
            "protocol": {"sha256": "protocol-a"},
            "fixed_state": {
                "optimal_set_agreement": 0.75,
                "catastrophic_miss_rate": 0.1,
                "latency_seconds": {"p50": 1.0},
            },
            "episodes": {"median_food_eaten": 4},
        },
        {
            "status": "completed",
            "finished_at": "2026-09-23T11:00:00Z",
            "configuration": {"id": "direct-stateful-verbose"},
            "model_runtime": {"artifact_sha256": "model-b"},
            "fixture": {"sha256": "fixture-a"},
            "protocol": {"sha256": "protocol-a"},
            "fixed_state": {
                "optimal_set_agreement": 0.5,
                "catastrophic_miss_rate": 0.2,
                "latency_seconds": {"p50": 0.5},
            },
            "episodes": {"median_food_eaten": 2},
        },
        {
            "status": "completed",
            "finished_at": "2026-09-23T12:00:00Z",
            "configuration": {"id": "direct-stateful-verbose"},
            "model_runtime": {"artifact_sha256": "model-a"},
            "fixture": {"sha256": "fixture-a"},
            "protocol": {"sha256": "protocol-b"},
            "fixed_state": {
                "optimal_set_agreement": 1.0,
                "catastrophic_miss_rate": 0.0,
                "latency_seconds": {"p50": 2.0},
            },
            "episodes": {"median_food_eaten": 5},
        },
    ]

    summary = summarize(records)

    assert summary["run_manifests"] == 1
    assert summary["configuration_records"] == 3
    assert len(summary["groups"]) == 3
    assert {row["model_sha256"] for row in summary["groups"]} == {"model-a", "model-b"}
    assert {row["protocol_sha256"] for row in summary["groups"]} == {
        "protocol-a",
        "protocol-b",
    }
