"""Run the frozen repeated-state gate v3 on one pinned llama.cpp backend."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from benchmarks.build_repeated_state_gate_fixture import (
    EXPECTED_EXAMPLES,
    EXPECTED_GROUPS,
    EXPECTED_SHA256,
    validate_fixture,
)
from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from decisio.baselines.generation import GeneratedJsonScorer
from decisio.schema import Candidate, ChoiceRequest
from decisio.scorers import SemanticBinaryScorer

PERTURBATIONS = ("none", "reverse_candidates")
ARMS = ("semantic", "generated")
RUNTIME_METRIC_KEYS = (
    "logical_input_tokens",
    "physically_evaluated_tokens",
    "reused_prefix_tokens",
    "fresh_calls",
    "shared_prefix_calls",
    "shared_prefix_fallbacks",
    "prefix_state_snapshot_bytes",
    "prefix_state_restore_bytes",
    "prefix_state_restores",
    "repeated_state_cache_hits",
    "repeated_state_cache_misses",
    "repeated_state_cache_reused_tokens",
    "repeated_state_cache_evictions",
    "repeated_state_cache_store_skips",
)


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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
        "mean": statistics.fmean(ordered),
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "min": ordered[0],
        "max": ordered[-1],
        "total": sum(ordered),
    }


def _progress_line(
    *,
    completed: int,
    total: int,
    label: str,
    elapsed_seconds: float,
) -> str:
    if total < 1:
        raise ValueError("progress total must be positive")
    if completed < 0 or completed > total:
        raise ValueError("progress completed must be between zero and total")
    percent = completed / total * 100.0
    if completed == 0:
        eta = "--:--:--"
    elif completed == total:
        eta = "00:00:00"
    else:
        eta = _format_duration((elapsed_seconds / completed) * (total - completed))
    return (
        f"[gate {completed}/{total} | {percent:5.1f}%] {label} | "
        f"elapsed {_format_duration(elapsed_seconds)} | ETA {eta}"
    )


def _report_progress(
    *,
    completed: int,
    total: int,
    label: str,
    started_at: float,
) -> None:
    print(
        _progress_line(
            completed=completed,
            total=total,
            label=label,
            elapsed_seconds=time.perf_counter() - started_at,
        ),
        file=sys.stderr,
        flush=True,
    )


def _config(args: argparse.Namespace) -> LlamaCppBackendConfig:
    return LlamaCppBackendConfig(
        model=args.model,
        n_ctx=args.n_ctx,
        n_batch=args.n_batch,
        n_ubatch=args.n_ubatch,
        n_threads=args.threads,
        n_threads_batch=args.threads_batch,
    )


def _load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_fixture(payload)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(
            f"repeated-state fixture SHA mismatch: expected {EXPECTED_SHA256}, got {digest}"
        )
    return payload


def _request(
    group: dict[str, Any],
    question: dict[str, Any],
    *,
    reverse_candidates: bool,
) -> ChoiceRequest:
    candidates = tuple(Candidate.from_dict(item) for item in group["candidates"])
    if reverse_candidates:
        candidates = tuple(reversed(candidates))
    return ChoiceRequest(
        id=str(question["id"]),
        state=group["state"],
        question=str(question["question"]),
        candidates=candidates,
    )


def _runtime_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        key: sum(int(row.get("runtime_metrics", {}).get(key, 0)) for row in rows)
        for key in RUNTIME_METRIC_KEYS
    }


def _bucket_summary(
    rows: list[dict[str, Any]],
    key: str,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[str(row[key])].append(row)
    result: dict[str, dict[str, Any]] = {}
    for value, items in sorted(buckets.items()):
        correct = sum(bool(item["correct"]) for item in items)
        result[value] = {
            "examples": len(items),
            "correct": correct,
            "accuracy": correct / len(items),
            "duration_seconds": _duration_summary(
                [float(item["latency_seconds"]) for item in items]
            ),
        }
    return result


def _summarize_arm(
    rows: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    *,
    arm: str,
) -> dict[str, Any]:
    correct = sum(bool(row["correct"]) for row in rows)
    summary: dict[str, Any] = {
        "examples": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows),
        "generated_tokens": sum(int(row["generated_tokens"]) for row in rows),
        "duration_seconds": _duration_summary(
            [float(row["latency_seconds"]) for row in rows]
        ),
        "group_duration_seconds": _duration_summary(
            [float(group["duration_seconds"]) for group in groups]
        ),
        "families": _bucket_summary(rows, "family"),
        "candidate_counts": _bucket_summary(rows, "candidate_count"),
        "state_tiers": _bucket_summary(rows, "state_tier"),
        "groups": {str(group["id"]): group for group in groups},
        "rows": rows,
    }
    if arm == "semantic":
        summary["runtime_totals"] = _runtime_totals(rows)
    return summary


def _run_group(
    *,
    backend: LlamaCppBackend,
    scorer: Any,
    arm: str,
    perturbation: str,
    group: dict[str, Any],
    gate_started: float,
    progress_completed: int,
    progress_total: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    reverse_candidates = perturbation == "reverse_candidates"
    if arm == "semantic":
        backend.clear_repeated_state_cache()

    rows: list[dict[str, Any]] = []
    group_id = str(group["id"])
    for question_index, question in enumerate(group["questions"], start=1):
        example_id = str(question["id"])
        _report_progress(
            completed=progress_completed,
            total=progress_total,
            label=(
                f"{perturbation} | {group_id} | {arm} | "
                f"{question_index}/{len(group['questions'])} {example_id}"
            ),
            started_at=gate_started,
        )
        request = _request(
            group,
            question,
            reverse_candidates=reverse_candidates,
        )
        if arm == "semantic":
            backend.reset_runtime_metrics()
        started = time.perf_counter()
        result = scorer.score(request)
        latency = time.perf_counter() - started
        runtime_metrics = backend.runtime_metrics() if arm == "semantic" else {}
        row = {
            "id": example_id,
            "group_id": group_id,
            "family": str(group["family"]),
            "state_tier": str(group["state_tier"]),
            "candidate_count": int(group["candidate_count"]),
            "label": str(question["label"]),
            "choice": result.choice,
            "correct": result.choice == str(question["label"]),
            "latency_seconds": latency,
            "generated_tokens": int(result.generated_tokens),
            "runtime_metrics": runtime_metrics,
        }
        rows.append(row)
        progress_completed += 1
        _report_progress(
            completed=progress_completed,
            total=progress_total,
            label=(
                f"completed {example_id} | {arm} | "
                f"{_format_duration(latency)}"
            ),
            started_at=gate_started,
        )

    runtime_totals = _runtime_totals(rows) if arm == "semantic" else {}
    cache_entries_after_clear = None
    cache_bytes_after_clear = None
    if arm == "semantic":
        backend.clear_repeated_state_cache()
        cleared = backend.runtime_metrics()
        cache_entries_after_clear = int(cleared["repeated_state_cache_entries"])
        cache_bytes_after_clear = int(cleared["repeated_state_cache_bytes"])

    group_summary = {
        "id": group_id,
        "family": str(group["family"]),
        "state_tier": str(group["state_tier"]),
        "candidate_count": int(group["candidate_count"]),
        "examples": len(rows),
        "correct": sum(bool(row["correct"]) for row in rows),
        "duration_seconds": sum(float(row["latency_seconds"]) for row in rows),
        "runtime_totals": runtime_totals,
        "cache_entries_after_clear": cache_entries_after_clear,
        "cache_bytes_after_clear": cache_bytes_after_clear,
    }
    return rows, group_summary, progress_completed


def _order_sensitivity(
    normal_rows: list[dict[str, Any]],
    reversed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    normal = {str(row["id"]): row for row in normal_rows}
    reversed_by_id = {str(row["id"]): row for row in reversed_rows}
    if set(normal) != set(reversed_by_id):
        raise ValueError("normal/reversed repeated-state rows do not match")
    changed = [
        example_id
        for example_id in sorted(normal)
        if normal[example_id]["choice"] != reversed_by_id[example_id]["choice"]
    ]
    return {
        "examples": len(normal),
        "choice_changes": len(changed),
        "changed_ids": changed,
    }


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    fixture = _load_fixture(args.fixture)
    groups = list(fixture["groups"])
    progress_total = (
        len(PERTURBATIONS)
        * len(groups)
        * len(ARMS)
        * len(groups[0]["questions"])
    )
    if progress_total != EXPECTED_EXAMPLES * len(PERTURBATIONS) * len(ARMS):
        raise ValueError("unexpected repeated-state progress cardinality")

    backend = LlamaCppBackend(_config(args))
    gate_started = time.perf_counter()
    try:
        semantic = SemanticBinaryScorer(backend)
        generated = GeneratedJsonScorer(backend)
        first_group = groups[0]
        first_question = first_group["questions"][0]

        print("[gate] warming semantic and generated paths", file=sys.stderr, flush=True)
        backend.clear_repeated_state_cache()
        semantic.score(_request(first_group, first_question, reverse_candidates=False))
        backend.clear_repeated_state_cache()
        generated.score(_request(first_group, first_question, reverse_candidates=False))

        rows_by: dict[str, dict[str, list[dict[str, Any]]]] = {
            perturbation: {arm: [] for arm in ARMS}
            for perturbation in PERTURBATIONS
        }
        groups_by: dict[str, dict[str, list[dict[str, Any]]]] = {
            perturbation: {arm: [] for arm in ARMS}
            for perturbation in PERTURBATIONS
        }
        execution_order: list[dict[str, Any]] = []
        completed = 0

        for perturbation_index, perturbation in enumerate(PERTURBATIONS):
            for group_index, group in enumerate(groups):
                arm_order = ["semantic", "generated"]
                if (perturbation_index + group_index) % 2:
                    arm_order.reverse()
                execution_order.append(
                    {
                        "perturbation": perturbation,
                        "group_id": str(group["id"]),
                        "arms": arm_order,
                    }
                )
                for arm in arm_order:
                    scorer = semantic if arm == "semantic" else generated
                    rows, group_summary, completed = _run_group(
                        backend=backend,
                        scorer=scorer,
                        arm=arm,
                        perturbation=perturbation,
                        group=group,
                        gate_started=gate_started,
                        progress_completed=completed,
                        progress_total=progress_total,
                    )
                    rows_by[perturbation][arm].extend(rows)
                    groups_by[perturbation][arm].append(group_summary)

        report_results: dict[str, Any] = {}
        for perturbation in PERTURBATIONS:
            report_results[perturbation] = {
                arm: _summarize_arm(
                    rows_by[perturbation][arm],
                    groups_by[perturbation][arm],
                    arm=arm,
                )
                for arm in ARMS
            }

        report = {
            "schema_version": 1,
            "gate": "repeated-state-gate-v3",
            "input_sha256": EXPECTED_SHA256,
            "examples": EXPECTED_EXAMPLES,
            "group_count": EXPECTED_GROUPS,
            "backend_identity": backend.identity,
            "execution_order": execution_order,
            "results": report_results,
            "order_sensitivity": {
                arm: _order_sensitivity(
                    rows_by["none"][arm],
                    rows_by["reverse_candidates"][arm],
                )
                for arm in ARMS
            },
            "elapsed_seconds": time.perf_counter() - gate_started,
            "peak_memory_bytes": backend.peak_memory_bytes(),
        }
        _report_progress(
            completed=progress_total,
            total=progress_total,
            label="complete",
            started_at=gate_started,
        )
        return report
    finally:
        backend.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repeated-state gate v3")
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-batch", type=int, default=512)
    parser.add_argument("--n-ubatch", type=int, default=512)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--threads-batch", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "semantic_accuracy": report["results"]["none"]["semantic"]["accuracy"],
                "generated_accuracy": report["results"]["none"]["generated"]["accuracy"],
                "semantic_group_p50_seconds": report["results"]["none"]["semantic"][
                    "group_duration_seconds"
                ]["p50"],
                "generated_group_p50_seconds": report["results"]["none"]["generated"][
                    "group_duration_seconds"
                ]["p50"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
