"""Evaluate the precommitted Decisio scorer gate from a comparison report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PRIMARY = "semantic"
BASELINES = ("semantic-independent", "letters", "generated")
EXPECTED_EXAMPLES = 64
EXPECTED_INPUT_SHA256 = "087ee8bbec3393609689046ea9c5d8219d0f39562e322180ca8f1e08eb368d3a"
QUALITY_MARGIN = 0.05
FAMILY_MAX_CORRECT_GAP = 2
MAX_ORDER_CHANGES = 1
SIGNIFICANCE_ALPHA = 0.05


def _criterion(passed: bool, **evidence: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **evidence}


def evaluate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("examples") != EXPECTED_EXAMPLES:
        raise ValueError(f"expected {EXPECTED_EXAMPLES} examples")
    if report.get("input_sha256") != EXPECTED_INPUT_SHA256:
        raise ValueError("comparison report does not use the frozen scorer-gate input")
    if report.get("primary_scorer") != PRIMARY:
        raise ValueError(f"primary scorer must be {PRIMARY!r}")

    scorers = report["scorers"]
    missing = [key for key in (PRIMARY, *BASELINES) if key not in scorers]
    if missing:
        raise ValueError(f"comparison report missing scorers: {missing}")

    primary_normal = scorers[PRIMARY]["normal"]
    primary_accuracy = float(primary_normal["accuracy"])
    baseline_correct = {
        key: int(scorers[key]["normal"]["correct"]) for key in BASELINES
    }
    strongest_correct = max(baseline_correct.values())
    strongest = [key for key in BASELINES if baseline_correct[key] == strongest_correct]
    strongest_accuracy = max(
        float(scorers[key]["normal"]["accuracy"]) for key in strongest
    )
    strongest_reference = min(
        strongest,
        key=lambda key: (
            int(scorers[key]["order_sensitivity"]["choice_changes"]),
            BASELINES.index(key),
        ),
    )

    quality_margin_passed = primary_accuracy >= strongest_accuracy - QUALITY_MARGIN
    paired_violations: list[dict[str, Any]] = []
    for baseline in BASELINES:
        paired = report["paired_vs_primary"][baseline]["none"]
        delta = float(paired["accuracy_delta"])
        pvalue = float(paired["exact_mcnemar_pvalue"])
        if delta < 0.0 and pvalue < SIGNIFICANCE_ALPHA:
            paired_violations.append(
                {
                    "baseline": baseline,
                    "accuracy_delta": delta,
                    "exact_mcnemar_pvalue": pvalue,
                }
            )
    overall_quality = _criterion(
        quality_margin_passed and not paired_violations,
        primary_accuracy=primary_accuracy,
        strongest_baseline_accuracy=strongest_accuracy,
        strongest_baselines=strongest,
        margin=QUALITY_MARGIN,
        paired_significance_alpha=SIGNIFICANCE_ALPHA,
        significant_baseline_wins=paired_violations,
    )

    primary_families = primary_normal["families"]
    family_evidence: dict[str, Any] = {}
    family_passed = True
    for family, primary_family in primary_families.items():
        primary_correct = int(primary_family["correct"])
        baseline_correct = {
            key: int(scorers[key]["normal"]["families"][family]["correct"])
            for key in BASELINES
        }
        strongest_correct = max(baseline_correct.values())
        gap = strongest_correct - primary_correct
        passed = gap <= FAMILY_MAX_CORRECT_GAP
        family_passed = family_passed and passed
        family_evidence[family] = {
            "passed": passed,
            "primary_correct": primary_correct,
            "strongest_baseline_correct": strongest_correct,
            "baseline_correct": baseline_correct,
            "gap": gap,
            "max_allowed_gap": FAMILY_MAX_CORRECT_GAP,
        }
    family_guardrail = _criterion(family_passed, families=family_evidence)

    primary_changes = int(scorers[PRIMARY]["order_sensitivity"]["choice_changes"])
    reference_changes = int(
        scorers[strongest_reference]["order_sensitivity"]["choice_changes"]
    )
    order_robustness = _criterion(
        primary_changes <= MAX_ORDER_CHANGES and primary_changes <= reference_changes,
        primary_choice_changes=primary_changes,
        max_primary_choice_changes=MAX_ORDER_CHANGES,
        reference_baseline=strongest_reference,
        reference_choice_changes=reference_changes,
        tie_rule=(
            "highest normal accuracy; if tied, use the tied baseline with the fewest "
            "order changes, then fixed baseline order"
        ),
    )

    normal_generated = int(scorers[PRIMARY]["normal"]["generated_tokens"])
    reverse_generated = int(
        scorers[PRIMARY]["reverse_candidates"]["generated_tokens"]
    )
    native_invariant = _criterion(
        normal_generated == 0 and reverse_generated == 0,
        normal_generated_tokens=normal_generated,
        reversed_generated_tokens=reverse_generated,
    )

    performance = report["performance"]
    performance_enabled = bool(performance.get("enabled"))
    position_balanced = bool(performance.get("position_balanced"))
    if performance_enabled:
        primary_perf = performance["scorers"][PRIMARY]["duration_seconds"]
        generated_perf = performance["scorers"]["generated"]["duration_seconds"]
        primary_p50 = float(primary_perf["p50"])
        primary_p95 = float(primary_perf["p95"])
        generated_p50 = float(generated_perf["p50"])
        generated_p95 = float(generated_perf["p95"])
        latency_passed = primary_p50 < generated_p50 and primary_p95 < generated_p95
    else:
        primary_p50 = primary_p95 = generated_p50 = generated_p95 = None
        latency_passed = False
    generation_tradeoff = _criterion(
        performance_enabled and position_balanced and latency_passed,
        performance_enabled=performance_enabled,
        position_balanced=position_balanced,
        measured_rounds=int(performance.get("measured_rounds", 0)),
        primary_p50_seconds=primary_p50,
        primary_p95_seconds=primary_p95,
        generated_p50_seconds=generated_p50,
        generated_p95_seconds=generated_p95,
        peak_memory_role="diagnostic_only",
    )

    criteria = {
        "overall_quality": overall_quality,
        "family_guardrail": family_guardrail,
        "order_robustness": order_robustness,
        "native_zero_generation": native_invariant,
        "generation_tradeoff": generation_tradeoff,
    }
    return {
        "schema_version": 1,
        "gate": "scorer-gate-v1",
        "primary_scorer": PRIMARY,
        "input_sha256": report["input_sha256"],
        "examples": report["examples"],
        "passed": all(item["passed"] for item in criteria.values()),
        "criteria": criteria,
    }


def render_markdown(evaluation: dict[str, Any]) -> str:
    status = "PASS" if evaluation["passed"] else "FAIL"
    lines = [
        "# Decisio scorer gate v1 evaluation",
        "",
        f"**Gate result: {status}**",
        "",
        f"- input SHA-256: `{evaluation['input_sha256']}`",
        f"- examples: {evaluation['examples']}",
        f"- primary scorer: `{evaluation['primary_scorer']}`",
        "",
        "| criterion | result |",
        "| --- | --- |",
    ]
    for name, item in evaluation["criteria"].items():
        lines.append(f"| {name} | {'PASS' if item['passed'] else 'FAIL'} |")
    lines.extend(
        [
            "",
            "The gate result applies only to the pinned model, workload, scorer/compiler "
            "identity and CPU runtime recorded by the source comparison report.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Decisio scorer-gate v1")
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="return a non-zero status when the precommitted gate does not pass",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = json.loads(args.comparison.read_text(encoding="utf-8"))
    evaluation = evaluate_report(report)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "gate-evaluation.json").write_text(
        json.dumps(evaluation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "gate-evaluation.md").write_text(
        render_markdown(evaluation),
        encoding="utf-8",
    )
    print(json.dumps(evaluation, indent=2, sort_keys=True))
    return int(args.require_pass and not evaluation["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
