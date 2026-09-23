"""Measure repeated-state semantic scoring against generated JSON on the pinned runtime.

This is intentionally diagnostic-only. It does not implement a promotion threshold.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from decisio.baselines.generation import GeneratedJsonScorer, compile_generated_choice
from decisio.schema import Candidate, ChoiceRequest
from decisio.scorers import SemanticBinaryScorer


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _progress_line(
    *,
    round_index: int,
    rounds: int,
    arm: str,
    completed: int,
    total: int,
    label: str,
    elapsed_seconds: float,
) -> str:
    if rounds < 1 or round_index < 1 or round_index > rounds:
        raise ValueError("round index must be within configured rounds")
    if total < 1:
        raise ValueError("progress total must be positive")
    if completed < 0 or completed > total:
        raise ValueError("progress completed must be between zero and total")

    percent = (completed / total) * 100.0
    if completed == 0:
        eta = "--:--:--"
    elif completed == total:
        eta = "00:00:00"
    else:
        seconds_per_item = elapsed_seconds / completed
        eta = _format_duration(seconds_per_item * (total - completed))
    return (
        f"[round {round_index}/{rounds}] "
        f"[{arm} {completed}/{total} | {percent:5.1f}%] "
        f"{label} | elapsed {_format_duration(elapsed_seconds)} | ETA {eta}"
    )


def _report_progress(
    *,
    round_index: int,
    rounds: int,
    arm: str,
    completed: int,
    total: int,
    label: str,
    started_at: float,
) -> None:
    print(
        _progress_line(
            round_index=round_index,
            rounds=rounds,
            arm=arm,
            completed=completed,
            total=total,
            label=label,
            elapsed_seconds=time.perf_counter() - started_at,
        ),
        file=sys.stderr,
        flush=True,
    )


def _requests() -> list[tuple[ChoiceRequest, str]]:
    candidates = (
        Candidate("billing", "Payments, invoices, refunds, or card charges"),
        Candidate("technical", "Software bugs, crashes, or device issues"),
        Candidate("security", "Credential exposure or suspected compromise"),
        Candidate("sales", "Purchasing, pricing, or product-plan questions"),
    )
    cases = [
        ("case-a", "The same invoice was charged twice.", "billing"),
        ("case-b", "A cardholder disputes a payment they do not recognize.", "billing"),
        ("case-c", "The desktop client crashes immediately after launch.", "technical"),
        ("case-d", "A report now takes fourteen minutes instead of twenty seconds.", "technical"),
        ("case-e", "An active API token was posted in a public issue.", "security"),
        ("case-f", "A production credential was committed to a public repository.", "security"),
        ("case-g", "A customer asks for pricing for fifty seats.", "sales"),
        ("case-h", "A prospect asks which paid plan includes audit logs.", "sales"),
    ]
    state = {
        "cases": [{"id": case_id, "evidence": evidence} for case_id, evidence, _ in cases],
        "reference_notes": [
            f"Reference note {index:03d}: no additional constraint changes the case facts above."
            for index in range(180)
        ],
    }
    return [
        (
            ChoiceRequest(
                id=case_id,
                state=state,
                question=f"Which queue best matches this situation: {evidence}",
                candidates=candidates,
            ),
            expected,
        )
        for case_id, evidence, expected in cases
    ]


def _summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("latency summary requires at least one value")

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
    }


def _config(args: argparse.Namespace) -> LlamaCppBackendConfig:
    return LlamaCppBackendConfig(
        model=args.model,
        n_ctx=args.n_ctx,
        n_batch=args.n_batch,
        n_ubatch=args.n_ubatch,
        n_threads=args.threads,
        n_threads_batch=args.threads_batch,
    )


def _semantic_arm(
    args: argparse.Namespace,
    *,
    round_index: int,
    rounds: int,
) -> dict[str, Any]:
    requests = _requests()
    total = len(requests) - 1
    arm_started = time.perf_counter()
    _report_progress(
        round_index=round_index,
        rounds=rounds,
        arm="semantic",
        completed=0,
        total=total,
        label="loading model/runtime",
        started_at=arm_started,
    )
    backend = LlamaCppBackend(_config(args))
    try:
        scorer = SemanticBinaryScorer(backend)
        backend.clear_repeated_state_cache()
        _report_progress(
            round_index=round_index,
            rounds=rounds,
            arm="semantic",
            completed=0,
            total=total,
            label=f"warmup {requests[0][0].id}",
            started_at=arm_started,
        )
        scorer.score(requests[0][0])

        rows: list[dict[str, Any]] = []
        measured_started = time.perf_counter()
        for index, (request, expected) in enumerate(requests[1:], start=1):
            _report_progress(
                round_index=round_index,
                rounds=rounds,
                arm="semantic",
                completed=index - 1,
                total=total,
                label=f"running {request.id}",
                started_at=measured_started,
            )
            backend.reset_runtime_metrics()
            started = time.perf_counter()
            result = scorer.score(request)
            elapsed = time.perf_counter() - started
            rows.append(
                {
                    "id": request.id,
                    "expected": expected,
                    "choice": result.choice,
                    "correct": result.choice == expected,
                    "seconds": elapsed,
                    "generated_tokens": result.generated_tokens,
                    "runtime_metrics": backend.runtime_metrics(),
                }
            )
            _report_progress(
                round_index=round_index,
                rounds=rounds,
                arm="semantic",
                completed=index,
                total=total,
                label=(
                    f"completed {request.id} in "
                    f"{_format_duration(elapsed)}"
                ),
                started_at=measured_started,
            )
        return {"identity": backend.identity, "rows": rows}
    finally:
        backend.close()


def _generated_arm(
    args: argparse.Namespace,
    *,
    round_index: int,
    rounds: int,
) -> dict[str, Any]:
    requests = _requests()
    total = len(requests) - 1
    arm_started = time.perf_counter()
    _report_progress(
        round_index=round_index,
        rounds=rounds,
        arm="generated",
        completed=0,
        total=total,
        label="loading model/runtime",
        started_at=arm_started,
    )
    backend = LlamaCppBackend(_config(args))
    try:
        scorer = GeneratedJsonScorer(backend)
        _report_progress(
            round_index=round_index,
            rounds=rounds,
            arm="generated",
            completed=0,
            total=total,
            label=f"warmup {requests[0][0].id}",
            started_at=arm_started,
        )
        scorer.score(requests[0][0])

        rows: list[dict[str, Any]] = []
        measured_started = time.perf_counter()
        for index, (request, expected) in enumerate(requests[1:], start=1):
            _report_progress(
                round_index=round_index,
                rounds=rounds,
                arm="generated",
                completed=index - 1,
                total=total,
                label=f"running {request.id}",
                started_at=measured_started,
            )
            _, input_ids, _ = compile_generated_choice(backend.tokenizer, request)
            started = time.perf_counter()
            result = scorer.score(request)
            elapsed = time.perf_counter() - started
            rows.append(
                {
                    "id": request.id,
                    "expected": expected,
                    "choice": result.choice,
                    "correct": result.choice == expected,
                    "seconds": elapsed,
                    "logical_input_tokens": len(input_ids),
                    "generated_tokens": result.generated_tokens,
                }
            )
            _report_progress(
                round_index=round_index,
                rounds=rounds,
                arm="generated",
                completed=index,
                total=total,
                label=(
                    f"completed {request.id} in "
                    f"{_format_duration(elapsed)}"
                ),
                started_at=measured_started,
            )
        return {"identity": backend.identity, "rows": rows}
    finally:
        backend.close()


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    arm_results: dict[str, list[dict[str, Any]]] = {"semantic": [], "generated": []}
    execution_order: list[list[str]] = []
    experiment_started = time.perf_counter()
    for round_index in range(args.rounds):
        order = ["semantic", "generated"]
        if round_index % 2:
            order.reverse()
        execution_order.append(order)
        current_round = round_index + 1
        print(
            f"[experiment] round {current_round}/{args.rounds} "
            f"order: {' -> '.join(order)}",
            file=sys.stderr,
            flush=True,
        )
        for arm in order:
            if arm == "semantic":
                result = _semantic_arm(
                    args,
                    round_index=current_round,
                    rounds=args.rounds,
                )
            else:
                result = _generated_arm(
                    args,
                    round_index=current_round,
                    rounds=args.rounds,
                )
            arm_results[arm].append(result)
    print(
        f"[experiment] complete in "
        f"{_format_duration(time.perf_counter() - experiment_started)}",
        file=sys.stderr,
        flush=True,
    )

    report: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "repeated-state-diagnostic-v2",
        "design_note": "questions include the relevant case evidence explicitly; opaque case-id lookup is not part of the task",
        "diagnostic_only": True,
        "promotion_threshold": None,
        "rounds": args.rounds,
        "execution_order": execution_order,
        "measured_requests_per_arm_per_round": len(_requests()) - 1,
        "arms": {},
    }
    for arm, rounds in arm_results.items():
        rows = [row for item in rounds for row in item["rows"]]
        latencies = [float(row["seconds"]) for row in rows]
        arm_summary: dict[str, Any] = {
            "identity": rounds[0]["identity"],
            "correct": sum(bool(row["correct"]) for row in rows),
            "examples": len(rows),
            "latency_seconds": _summary(latencies),
            "generated_tokens": sum(int(row["generated_tokens"]) for row in rows),
            "rows": rows,
        }
        if arm == "semantic":
            arm_summary["runtime_totals"] = {
                key: sum(int(row["runtime_metrics"].get(key, 0)) for row in rows)
                for key in (
                    "logical_input_tokens",
                    "physically_evaluated_tokens",
                    "reused_prefix_tokens",
                    "repeated_state_cache_hits",
                    "repeated_state_cache_misses",
                    "repeated_state_cache_reused_tokens",
                )
            }
        else:
            arm_summary["logical_input_tokens"] = sum(
                int(row["logical_input_tokens"]) for row in rows
            )
        report["arms"][arm] = arm_summary

    semantic_p50 = report["arms"]["semantic"]["latency_seconds"]["p50"]
    generated_p50 = report["arms"]["generated"]["latency_seconds"]["p50"]
    report["observed"] = {
        "semantic_over_generated_p50_ratio": (
            semantic_p50 / generated_p50 if generated_p50 > 0 else None
        ),
        "generated_over_semantic_p50_speedup": (
            generated_p50 / semantic_p50 if semantic_p50 > 0 else None
        ),
    }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnose repeated-state semantic scoring versus generated JSON"
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-batch", type=int, default=512)
    parser.add_argument("--n-ubatch", type=int, default=512)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--threads-batch", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rounds < 1:
        raise ValueError("rounds must be positive")
    report = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["observed"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
