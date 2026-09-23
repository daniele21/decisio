"""Evaluate the precommitted repeated-state gate v3."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

from benchmarks.build_repeated_state_gate_fixture import (
    EXPECTED_EXAMPLES,
    EXPECTED_GROUPS,
    EXPECTED_SHA256,
)

OVERALL_MAX_CORRECT_GAP = 2
FAMILY_MAX_CORRECT_GAP = 1
CANDIDATE_COUNT_MAX_CORRECT_GAP = 1
SIGNIFICANCE_ALPHA = 0.05
MAX_SEMANTIC_ORDER_CHANGES = 0
MAX_SEMANTIC_TO_GENERATED_P50_RATIO = 0.50
MAX_SEMANTIC_TO_GENERATED_P95_RATIO = 0.50
MAX_PHYSICAL_TO_LOGICAL_RATIO = 0.50
EXPECTED_CACHE_HITS = 40
EXPECTED_CACHE_MISSES = 8
EXPECTED_GROUP_CACHE_HITS = 5
EXPECTED_GROUP_CACHE_MISSES = 1
EXPECTED_FAMILIES = (
    "support_routing",
    "rule_application",
    "evidence_entailment",
    "comparative_nuance",
)
EXPECTED_CANDIDATE_COUNTS = ("2", "4", "8")
EXPECTED_STATE_TIERS = ("short", "medium", "long")
EXPECTED_BACKEND_IDENTITY = {
    "backend": "llama-cpp-python",
    "runtime": "llama.cpp",
    "binding_version": "0.3.35",
    "artifact_filename": "Qwen3.5-2B-Q4_K_M.gguf",
    "artifact_sha256": "aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223",
    "artifact_size_bytes": 1280835840,
    "quantization": "Q4_K_M",
    "device": "cpu",
    "n_ctx": 8192,
    "n_batch": 512,
    "n_ubatch": 512,
    "n_threads": 2,
    "n_threads_batch": 2,
    "zero_generation_native_scoring": True,
    "shared_context_state": True,
    "shared_prefix_primitive": "single_sequence_state_snapshot_restore",
    "repeated_state_cache": "exact_compiler_token_prefix_lru",
    "repeated_state_cache_max_entries": 2,
    "repeated_state_cache_max_bytes": 256 * 1024 * 1024,
    "selected_vocab_projection": False,
}


def _criterion(passed: bool, **evidence: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **evidence}


def _exact_mcnemar_pvalue(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    tail = min(left_only, right_only)
    probability = sum(
        math.comb(discordant, index)
        for index in range(tail + 1)
    ) / (2**discordant)
    return min(1.0, 2.0 * probability)


def _duration_summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("duration summary requires at least one value")
    ordered = sorted(values)

    def percentile(q: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        position = q * (len(ordered) - 1)
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        fraction = position - lower
        return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction

    return {
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "mean": statistics.fmean(ordered),
    }


def _paired_quality(
    semantic_rows: list[dict[str, Any]],
    generated_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    semantic = {str(row["id"]): bool(row["correct"]) for row in semantic_rows}
    generated = {str(row["id"]): bool(row["correct"]) for row in generated_rows}
    if set(semantic) != set(generated):
        raise ValueError("semantic/generated repeated-state rows do not match")
    semantic_only = sum(
        semantic[key] and not generated[key]
        for key in semantic
    )
    generated_only = sum(
        generated[key] and not semantic[key]
        for key in semantic
    )
    return {
        "semantic_only_correct": semantic_only,
        "generated_only_correct": generated_only,
        "exact_mcnemar_pvalue": _exact_mcnemar_pvalue(
            semantic_only,
            generated_only,
        ),
    }


def _runtime_identity(report: dict[str, Any]) -> dict[str, Any]:
    actual = report.get("backend_identity")
    if not isinstance(actual, dict):
        actual = {}
    mismatches = {
        key: {"expected": expected, "actual": actual.get(key)}
        for key, expected in EXPECTED_BACKEND_IDENTITY.items()
        if actual.get(key) != expected
    }
    return _criterion(
        not mismatches,
        expected=EXPECTED_BACKEND_IDENTITY,
        actual=actual,
        mismatches=mismatches,
    )


def _quality_criteria(
    semantic: dict[str, Any],
    generated: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    semantic_correct = int(semantic["correct"])
    generated_correct = int(generated["correct"])
    gap = generated_correct - semantic_correct
    paired = _paired_quality(semantic["rows"], generated["rows"])
    significant_generated_win = (
        paired["generated_only_correct"] > paired["semantic_only_correct"]
        and paired["exact_mcnemar_pvalue"] < SIGNIFICANCE_ALPHA
    )
    overall = _criterion(
        gap <= OVERALL_MAX_CORRECT_GAP and not significant_generated_win,
        semantic_correct=semantic_correct,
        generated_correct=generated_correct,
        generated_minus_semantic_correct=gap,
        max_allowed_correct_gap=OVERALL_MAX_CORRECT_GAP,
        paired_significance_alpha=SIGNIFICANCE_ALPHA,
        **paired,
    )

    family_evidence: dict[str, Any] = {}
    family_passed = True
    for family in EXPECTED_FAMILIES:
        semantic_family = semantic["families"][family]
        generated_family = generated["families"][family]
        family_gap = int(generated_family["correct"]) - int(semantic_family["correct"])
        passed = family_gap <= FAMILY_MAX_CORRECT_GAP
        family_passed = family_passed and passed
        family_evidence[family] = {
            "passed": passed,
            "semantic_correct": int(semantic_family["correct"]),
            "generated_correct": int(generated_family["correct"]),
            "generated_minus_semantic_correct": family_gap,
            "max_allowed_correct_gap": FAMILY_MAX_CORRECT_GAP,
        }
    families = _criterion(family_passed, families=family_evidence)

    candidate_evidence: dict[str, Any] = {}
    candidate_passed = True
    for candidate_count in EXPECTED_CANDIDATE_COUNTS:
        semantic_bucket = semantic["candidate_counts"][candidate_count]
        generated_bucket = generated["candidate_counts"][candidate_count]
        bucket_gap = int(generated_bucket["correct"]) - int(semantic_bucket["correct"])
        passed = bucket_gap <= CANDIDATE_COUNT_MAX_CORRECT_GAP
        candidate_passed = candidate_passed and passed
        candidate_evidence[candidate_count] = {
            "passed": passed,
            "semantic_correct": int(semantic_bucket["correct"]),
            "generated_correct": int(generated_bucket["correct"]),
            "generated_minus_semantic_correct": bucket_gap,
            "max_allowed_correct_gap": CANDIDATE_COUNT_MAX_CORRECT_GAP,
        }
    candidate_counts = _criterion(
        candidate_passed,
        candidate_counts=candidate_evidence,
    )
    return overall, families, candidate_counts


def _cache_reuse(semantic: dict[str, Any]) -> dict[str, Any]:
    runtime = semantic["runtime_totals"]
    logical = int(runtime["logical_input_tokens"])
    physical = int(runtime["physically_evaluated_tokens"])
    physical_ratio = physical / logical if logical else 1.0
    group_evidence: dict[str, Any] = {}
    groups_passed = True
    for group_id, group in sorted(semantic["groups"].items()):
        metrics = group["runtime_totals"]
        hits = int(metrics["repeated_state_cache_hits"])
        misses = int(metrics["repeated_state_cache_misses"])
        entries = int(group["cache_entries_after_clear"])
        bytes_after_clear = int(group["cache_bytes_after_clear"])
        passed = (
            hits == EXPECTED_GROUP_CACHE_HITS
            and misses == EXPECTED_GROUP_CACHE_MISSES
            and entries == 0
            and bytes_after_clear == 0
        )
        groups_passed = groups_passed and passed
        group_evidence[group_id] = {
            "passed": passed,
            "hits": hits,
            "misses": misses,
            "expected_hits": EXPECTED_GROUP_CACHE_HITS,
            "expected_misses": EXPECTED_GROUP_CACHE_MISSES,
            "cache_entries_after_clear": entries,
            "cache_bytes_after_clear": bytes_after_clear,
        }

    hits = int(runtime["repeated_state_cache_hits"])
    misses = int(runtime["repeated_state_cache_misses"])
    fallbacks = int(runtime["shared_prefix_fallbacks"])
    passed = (
        hits == EXPECTED_CACHE_HITS
        and misses == EXPECTED_CACHE_MISSES
        and physical_ratio <= MAX_PHYSICAL_TO_LOGICAL_RATIO
        and fallbacks == 0
        and groups_passed
    )
    return _criterion(
        passed,
        hits=hits,
        expected_hits=EXPECTED_CACHE_HITS,
        misses=misses,
        expected_misses=EXPECTED_CACHE_MISSES,
        logical_input_tokens=logical,
        physically_evaluated_tokens=physical,
        physical_to_logical_ratio=physical_ratio,
        max_physical_to_logical_ratio=MAX_PHYSICAL_TO_LOGICAL_RATIO,
        shared_prefix_fallbacks=fallbacks,
        groups=group_evidence,
    )


def _latency_tradeoff(
    semantic: dict[str, Any],
    generated: dict[str, Any],
    execution_order: list[dict[str, Any]],
) -> dict[str, Any]:
    semantic_group = semantic["group_duration_seconds"]
    generated_group = generated["group_duration_seconds"]
    p50_ratio = float(semantic_group["p50"]) / float(generated_group["p50"])
    p95_ratio = float(semantic_group["p95"]) / float(generated_group["p95"])

    normal_orders = [
        item["arms"]
        for item in execution_order
        if item["perturbation"] == "none"
    ]
    first_counts = {
        arm: sum(order[0] == arm for order in normal_orders)
        for arm in ("semantic", "generated")
    }
    position_balanced = first_counts == {"semantic": 4, "generated": 4}

    state_tier_evidence: dict[str, Any] = {}
    state_tiers_passed = True
    for tier in EXPECTED_STATE_TIERS:
        semantic_values = [
            float(group["duration_seconds"])
            for group in semantic["groups"].values()
            if group["state_tier"] == tier
        ]
        generated_values = [
            float(group["duration_seconds"])
            for group in generated["groups"].values()
            if group["state_tier"] == tier
        ]
        semantic_summary = _duration_summary(semantic_values)
        generated_summary = _duration_summary(generated_values)
        tier_ratio = semantic_summary["p50"] / generated_summary["p50"]
        tier_passed = tier_ratio < 1.0
        state_tiers_passed = state_tiers_passed and tier_passed
        state_tier_evidence[tier] = {
            "passed": tier_passed,
            "semantic_p50_seconds": semantic_summary["p50"],
            "generated_p50_seconds": generated_summary["p50"],
            "semantic_to_generated_p50_ratio": tier_ratio,
        }

    passed = (
        position_balanced
        and p50_ratio <= MAX_SEMANTIC_TO_GENERATED_P50_RATIO
        and p95_ratio <= MAX_SEMANTIC_TO_GENERATED_P95_RATIO
        and state_tiers_passed
    )
    return _criterion(
        passed,
        sequence_definition="one cold decision plus five same-state follow-up decisions",
        position_balanced=position_balanced,
        first_arm_counts=first_counts,
        semantic_group_p50_seconds=float(semantic_group["p50"]),
        generated_group_p50_seconds=float(generated_group["p50"]),
        semantic_to_generated_p50_ratio=p50_ratio,
        max_semantic_to_generated_p50_ratio=MAX_SEMANTIC_TO_GENERATED_P50_RATIO,
        semantic_group_p95_seconds=float(semantic_group["p95"]),
        generated_group_p95_seconds=float(generated_group["p95"]),
        semantic_to_generated_p95_ratio=p95_ratio,
        max_semantic_to_generated_p95_ratio=MAX_SEMANTIC_TO_GENERATED_P95_RATIO,
        state_tiers=state_tier_evidence,
    )


def evaluate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("gate") != "repeated-state-gate-v3":
        raise ValueError("unexpected repeated-state gate id")
    if report.get("input_sha256") != EXPECTED_SHA256:
        raise ValueError("report does not use the frozen repeated-state fixture")
    if int(report.get("examples", 0)) != EXPECTED_EXAMPLES:
        raise ValueError(f"expected {EXPECTED_EXAMPLES} repeated-state examples")
    if int(report.get("group_count", 0)) != EXPECTED_GROUPS:
        raise ValueError(f"expected {EXPECTED_GROUPS} repeated-state groups")

    results = report["results"]
    semantic = results["none"]["semantic"]
    generated = results["none"]["generated"]
    semantic_reverse = results["reverse_candidates"]["semantic"]

    overall, families, candidate_counts = _quality_criteria(
        semantic,
        generated,
    )
    order_changes = int(report["order_sensitivity"]["semantic"]["choice_changes"])
    order_robustness = _criterion(
        order_changes <= MAX_SEMANTIC_ORDER_CHANGES,
        semantic_choice_changes=order_changes,
        max_semantic_choice_changes=MAX_SEMANTIC_ORDER_CHANGES,
        changed_ids=report["order_sensitivity"]["semantic"]["changed_ids"],
    )
    native_zero_generation = _criterion(
        int(semantic["generated_tokens"]) == 0
        and int(semantic_reverse["generated_tokens"]) == 0,
        normal_generated_tokens=int(semantic["generated_tokens"]),
        reversed_generated_tokens=int(semantic_reverse["generated_tokens"]),
    )
    criteria = {
        "runtime_identity": _runtime_identity(report),
        "overall_quality": overall,
        "family_guardrails": families,
        "candidate_count_guardrails": candidate_counts,
        "order_robustness": order_robustness,
        "native_zero_generation": native_zero_generation,
        "cache_reuse": _cache_reuse(semantic),
        "latency_tradeoff": _latency_tradeoff(
            semantic,
            generated,
            report["execution_order"],
        ),
    }
    return {
        "schema_version": 1,
        "gate": "repeated-state-gate-v3",
        "scope": "many decisions over one unchanged long state",
        "input_sha256": EXPECTED_SHA256,
        "examples": EXPECTED_EXAMPLES,
        "groups": EXPECTED_GROUPS,
        "passed": all(item["passed"] for item in criteria.values()),
        "criteria": criteria,
    }


def render_markdown(evaluation: dict[str, Any]) -> str:
    status = "PASS" if evaluation["passed"] else "FAIL"
    lines = [
        "# Decisio repeated-state gate v3 evaluation",
        "",
        f"**Gate result: {status}**",
        "",
        f"- scope: {evaluation['scope']}",
        f"- input SHA-256: `{evaluation['input_sha256']}`",
        f"- examples: {evaluation['examples']}",
        f"- shared-state groups: {evaluation['groups']}",
        "",
        "| criterion | result |",
        "| --- | --- |",
    ]
    for name, item in evaluation["criteria"].items():
        lines.append(f"| {name} | {'PASS' if item['passed'] else 'FAIL'} |")
    lines.extend(
        [
            "",
            "A PASS supports only the repeated-state scope on the pinned artifact/runtime. "
            "It does not override the scorer-gate v2 FAIL for short/fresh general-purpose use.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate repeated-state gate v3")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--require-pass", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
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
