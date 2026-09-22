from __future__ import annotations

from copy import deepcopy

from benchmarks.evaluate_scorer_gate import evaluate_report


def _summary(*, correct: int, generated_tokens: int = 0):
    return {
        "examples": 64,
        "correct": correct,
        "accuracy": correct / 64,
        "generated_tokens": generated_tokens,
        "families": {
            name: {"examples": 16, "correct": family_correct}
            for name, family_correct in {
                "support_routing": correct // 4,
                "rule_application": correct // 4,
                "evidence_entailment": correct // 4,
                "comparative_nuance": correct // 4,
            }.items()
        },
    }


def _report() -> dict:
    scorer_specs = {
        "semantic": (60, 0),
        "semantic-independent": (59, 1),
        "letters": (58, 1),
        "generated": (57, 2),
    }
    scorers = {}
    for key, (correct, changes) in scorer_specs.items():
        generated = 64 if key == "generated" else 0
        normal = _summary(correct=correct, generated_tokens=generated)
        reverse = _summary(correct=correct, generated_tokens=generated)
        scorers[key] = {
            "normal": normal,
            "reverse_candidates": reverse,
            "order_sensitivity": {
                "examples": 64,
                "choice_changes": changes,
            },
        }

    return {
        "schema_version": 2,
        "primary_scorer": "semantic",
        "input_sha256": (
            "087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a"
        ),
        "examples": 64,
        "scorers": scorers,
        "paired_vs_primary": {
            baseline: {
                "none": {
                    "accuracy_delta": (60 - correct) / 64,
                    "exact_mcnemar_pvalue": 0.5,
                }
            }
            for baseline, correct in {
                "semantic-independent": 59,
                "letters": 58,
                "generated": 57,
            }.items()
        },
        "performance": {
            "enabled": True,
            "position_balanced": True,
            "measured_rounds": 4,
            "scorers": {
                "semantic": {
                    "duration_seconds": {"p50": 10.0, "p95": 11.0},
                },
                "generated": {
                    "duration_seconds": {"p50": 15.0, "p95": 17.0},
                },
            },
        },
    }


def test_scorer_gate_passes_when_all_precommitted_criteria_hold():
    evaluation = evaluate_report(_report())

    assert evaluation["passed"] is True
    assert all(item["passed"] for item in evaluation["criteria"].values())
    assert (
        evaluation["criteria"]["order_robustness"]["reference_baseline"]
        == "semantic-independent"
    )


def test_scorer_gate_rejects_significant_baseline_win():
    report = _report()
    report["scorers"]["semantic-independent"]["normal"]["correct"] = 64
    report["scorers"]["semantic-independent"]["normal"]["accuracy"] = 1.0
    report["paired_vs_primary"]["semantic-independent"]["none"] = {
        "accuracy_delta": -4 / 64,
        "exact_mcnemar_pvalue": 0.03125,
    }

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    quality = evaluation["criteria"]["overall_quality"]
    assert quality["passed"] is False
    assert quality["significant_baseline_wins"][0]["baseline"] == "semantic-independent"


def test_scorer_gate_uses_strict_order_tiebreak_for_equal_accuracy():
    report = _report()
    report["scorers"]["letters"]["normal"] = deepcopy(
        report["scorers"]["semantic-independent"]["normal"]
    )
    report["scorers"]["letters"]["order_sensitivity"]["choice_changes"] = 0
    report["scorers"]["semantic"]["order_sensitivity"]["choice_changes"] = 1

    evaluation = evaluate_report(report)

    order = evaluation["criteria"]["order_robustness"]
    assert order["reference_baseline"] == "letters"
    assert order["passed"] is False


def test_scorer_gate_rejects_generation_latency_regression():
    report = _report()
    report["performance"]["scorers"]["semantic"]["duration_seconds"]["p95"] = 18.0

    evaluation = evaluate_report(report)

    assert evaluation["passed"] is False
    assert evaluation["criteria"]["generation_tradeoff"]["passed"] is False
