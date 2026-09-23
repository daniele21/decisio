from __future__ import annotations

from pathlib import Path

from benchmarks.build_repeated_state_gate_fixture import (
    EXPECTED_EXAMPLES,
    EXPECTED_SHA256,
    build_fixture,
    materialize,
    validate_fixture,
)
from benchmarks.evaluate_repeated_state_gate import (
    EXPECTED_BACKEND_IDENTITY,
    evaluate_report,
)
from benchmarks.run_repeated_state_gate import _progress_line


def _rows() -> list[dict]:
    rows: list[dict] = []
    for group in build_fixture()["groups"]:
        for question in group["questions"]:
            rows.append(
                {
                    "id": question["id"],
                    "group_id": group["id"],
                    "family": group["family"],
                    "state_tier": group["state_tier"],
                    "candidate_count": group["candidate_count"],
                    "label": question["label"],
                    "choice": question["label"],
                    "correct": True,
                    "latency_seconds": 1.0,
                    "generated_tokens": 0,
                    "runtime_metrics": {},
                }
            )
    return rows


def _duration(value: float, *, total: float | None = None) -> dict[str, float]:
    return {
        "mean": value,
        "p50": value,
        "p95": value,
        "min": value,
        "max": value,
        "total": value if total is None else total,
    }


def _bucket(rows: list[dict], key: str, latency: float) -> dict[str, dict]:
    values = sorted({str(row[key]) for row in rows})
    result: dict[str, dict] = {}
    for value in values:
        selected = [row for row in rows if str(row[key]) == value]
        correct = sum(bool(row["correct"]) for row in selected)
        result[value] = {
            "examples": len(selected),
            "correct": correct,
            "accuracy": correct / len(selected),
            "duration_seconds": _duration(
                latency,
                total=latency * len(selected),
            ),
        }
    return result


def _groups(rows: list[dict], *, arm: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for group in build_fixture()["groups"]:
        selected = [row for row in rows if row["group_id"] == group["id"]]
        semantic = arm == "semantic"
        result[group["id"]] = {
            "id": group["id"],
            "family": group["family"],
            "state_tier": group["state_tier"],
            "candidate_count": group["candidate_count"],
            "examples": len(selected),
            "correct": sum(bool(row["correct"]) for row in selected),
            "duration_seconds": 6.0 if semantic else 18.0,
            "runtime_totals": (
                {
                    "repeated_state_cache_hits": 5,
                    "repeated_state_cache_misses": 1,
                }
                if semantic
                else {}
            ),
            "cache_entries_after_clear": 0 if semantic else None,
            "cache_bytes_after_clear": 0 if semantic else None,
        }
    return result


def _summary(rows: list[dict], *, arm: str) -> dict:
    semantic = arm == "semantic"
    latency = 1.0 if semantic else 3.0
    group_duration = 6.0 if semantic else 18.0
    groups = _groups(rows, arm=arm)
    summary = {
        "examples": len(rows),
        "correct": sum(bool(row["correct"]) for row in rows),
        "accuracy": sum(bool(row["correct"]) for row in rows) / len(rows),
        "generated_tokens": 0 if semantic else len(rows) * 5,
        "duration_seconds": _duration(
            latency,
            total=latency * len(rows),
        ),
        "group_duration_seconds": _duration(
            group_duration,
            total=group_duration * len(groups),
        ),
        "families": _bucket(rows, "family", latency),
        "candidate_counts": _bucket(rows, "candidate_count", latency),
        "state_tiers": _bucket(rows, "state_tier", latency),
        "groups": groups,
        "rows": rows,
    }
    if semantic:
        summary["runtime_totals"] = {
            "logical_input_tokens": 100_000,
            "physically_evaluated_tokens": 30_000,
            "repeated_state_cache_hits": 40,
            "repeated_state_cache_misses": 8,
            "shared_prefix_fallbacks": 0,
        }
    return summary


def _report() -> dict:
    semantic_rows = _rows()
    generated_rows = [
        {
            **row,
            "latency_seconds": 3.0,
            "generated_tokens": 5,
        }
        for row in _rows()
    ]
    execution_order = []
    groups = build_fixture()["groups"]
    for perturbation_index, perturbation in enumerate(
        ("none", "reverse_candidates")
    ):
        for group_index, group in enumerate(groups):
            arms = ["semantic", "generated"]
            if (perturbation_index + group_index) % 2:
                arms.reverse()
            execution_order.append(
                {
                    "perturbation": perturbation,
                    "group_id": group["id"],
                    "arms": arms,
                }
            )

    return {
        "schema_version": 1,
        "gate": "repeated-state-gate-v3",
        "input_sha256": EXPECTED_SHA256,
        "examples": EXPECTED_EXAMPLES,
        "group_count": len(groups),
        "backend_identity": dict(EXPECTED_BACKEND_IDENTITY),
        "execution_order": execution_order,
        "results": {
            "none": {
                "semantic": _summary(semantic_rows, arm="semantic"),
                "generated": _summary(generated_rows, arm="generated"),
            },
            "reverse_candidates": {
                "semantic": _summary(semantic_rows, arm="semantic"),
                "generated": _summary(generated_rows, arm="generated"),
            },
        },
        "order_sensitivity": {
            "semantic": {
                "examples": EXPECTED_EXAMPLES,
                "choice_changes": 0,
                "changed_ids": [],
            },
            "generated": {
                "examples": EXPECTED_EXAMPLES,
                "choice_changes": 0,
                "changed_ids": [],
            },
        },
    }


def test_repeated_state_fixture_is_frozen_and_balanced(tmp_path: Path):
    payload = build_fixture()
    validate_fixture(payload)

    output = tmp_path / "fixture.json"
    digest = materialize(output)

    assert digest == EXPECTED_SHA256
    assert len(payload["groups"]) == 8
    assert sum(len(group["questions"]) for group in payload["groups"]) == 48
    assert {
        group["candidate_count"] for group in payload["groups"]
    } == {2, 4, 8}
    assert {
        group["state_tier"] for group in payload["groups"]
    } == {"short", "medium", "long"}


def test_repeated_state_gate_passes_when_all_precommitted_criteria_hold():
    evaluation = evaluate_report(_report())

    assert evaluation["passed"] is True
    assert all(item["passed"] for item in evaluation["criteria"].values())


def test_repeated_state_gate_rejects_quality_gap():
    report = _report()
    rows = report["results"]["none"]["semantic"]["rows"]
    for row in rows[:3]:
        row["correct"] = False
        row["choice"] = "wrong"
    report["results"]["none"]["semantic"]["correct"] -= 3
    report["results"]["none"]["semantic"]["accuracy"] = 45 / 48
    family = rows[0]["family"]
    report["results"]["none"]["semantic"]["families"][family]["correct"] -= 3

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    assert evaluation["criteria"]["overall_quality"]["passed"] is False


def test_repeated_state_gate_rejects_insufficient_cache_reuse():
    report = _report()
    report["results"]["none"]["semantic"]["runtime_totals"][
        "physically_evaluated_tokens"
    ] = 60_000

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    assert evaluation["criteria"]["cache_reuse"]["passed"] is False


def test_repeated_state_gate_rejects_less_than_two_x_p50_advantage():
    report = _report()
    report["results"]["none"]["semantic"]["group_duration_seconds"][
        "p50"
    ] = 10.0

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    assert evaluation["criteria"]["latency_tradeoff"]["passed"] is False


def test_repeated_state_gate_rejects_semantic_order_change():
    report = _report()
    report["order_sensitivity"]["semantic"] = {
        "examples": EXPECTED_EXAMPLES,
        "choice_changes": 1,
        "changed_ids": ["sr4-duplicate"],
    }

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    assert evaluation["criteria"]["order_robustness"]["passed"] is False


def test_repeated_state_gate_rejects_wrong_runtime_identity():
    report = _report()
    report["backend_identity"]["artifact_sha256"] = "wrong"

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    assert evaluation["criteria"]["runtime_identity"]["passed"] is False


def test_repeated_state_progress_reports_eta():
    line = _progress_line(
        completed=24,
        total=192,
        label="none | support-routing-4 | semantic | 3/6 sr4-crash",
        elapsed_seconds=240.0,
    )

    assert line == (
        "[gate 24/192 |  12.5%] "
        "none | support-routing-4 | semantic | 3/6 sr4-crash | "
        "elapsed 00:04:00 | ETA 00:28:00"
    )
