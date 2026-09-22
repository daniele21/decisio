"""Verify llama.cpp shared execution against a fresh scorer oracle."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from decisio.benchmark import load_jsonl
from decisio.schema import Candidate, ChoiceRequest
from decisio.scorers import SemanticBinaryScorer

SCORE_TOLERANCE = 1e-3
BINARY_TOLERANCE = 1e-4
DISTRIBUTION_TOLERANCE = 1e-4


def _deltas(shared: Any, fresh: Any) -> dict[str, float | bool]:
    return {
        "same_choice": shared.choice == fresh.choice,
        "max_abs_score_delta": max(
            abs(shared.scores[key] - fresh.scores[key]) for key in shared.scores
        ),
        "max_abs_binary_probability_delta": max(
            abs(
                shared.binary_conditional_probability[key]
                - fresh.binary_conditional_probability[key]
            )
            for key in shared.binary_conditional_probability
        ),
        "max_abs_distribution_delta": max(
            abs(shared.distribution[key] - fresh.distribution[key])
            for key in shared.distribution
        ),
    }


def _within_tolerance(item: dict[str, Any]) -> bool:
    return bool(
        item["same_choice"]
        and item["max_abs_score_delta"] <= SCORE_TOLERANCE
        and item["max_abs_binary_probability_delta"] <= BINARY_TOLERANCE
        and item["max_abs_distribution_delta"] <= DISTRIBUTION_TOLERANCE
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


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    backend = LlamaCppBackend(_config(args))
    try:
        shared_scorer = SemanticBinaryScorer(backend)
        fresh_scorer = SemanticBinaryScorer(backend.fresh_view())

        rows: list[dict[str, Any]] = []
        shared_physical = 0
        fresh_physical = 0
        max_score_delta = 0.0
        max_binary_delta = 0.0
        max_distribution_delta = 0.0
        changed_choices: list[str] = []
        shared_fast_path_rows = 0
        safe_fallback_rows = 0

        for row in load_jsonl(args.fixture):
            request = ChoiceRequest.from_dict(row)
            backend.reset_runtime_metrics()
            shared = shared_scorer.score(request)
            shared_metrics = backend.runtime_metrics()

            backend.reset_runtime_metrics()
            fresh = fresh_scorer.score(request)
            fresh_metrics = backend.runtime_metrics()

            if int(shared_metrics["shared_prefix_calls"]) > 0:
                shared_fast_path_rows += 1
            elif int(shared_metrics["fresh_calls"]) > 0:
                safe_fallback_rows += 1

            delta = _deltas(shared, fresh)
            example_id = request.id or "unknown"
            if not delta["same_choice"]:
                changed_choices.append(example_id)
            max_score_delta = max(max_score_delta, float(delta["max_abs_score_delta"]))
            max_binary_delta = max(
                max_binary_delta, float(delta["max_abs_binary_probability_delta"])
            )
            max_distribution_delta = max(
                max_distribution_delta, float(delta["max_abs_distribution_delta"])
            )
            shared_physical += int(shared_metrics["physically_evaluated_tokens"])
            fresh_physical += int(fresh_metrics["physically_evaluated_tokens"])
            rows.append(
                {
                    "id": example_id,
                    **delta,
                    "shared_runtime_metrics": shared_metrics,
                    "fresh_runtime_metrics": fresh_metrics,
                }
            )

        fixture_evidence = {
            "examples": len(rows),
            "changed_choices": changed_choices,
            "max_abs_score_delta": max_score_delta,
            "max_abs_binary_probability_delta": max_binary_delta,
            "max_abs_distribution_delta": max_distribution_delta,
            "shared_physically_evaluated_tokens": shared_physical,
            "fresh_physically_evaluated_tokens": fresh_physical,
            "physical_token_reduction": fresh_physical - shared_physical,
            "shared_fast_path_rows": shared_fast_path_rows,
            "safe_fallback_rows": safe_fallback_rows,
            "rows": rows,
        }
        fixture_evidence["passed"] = bool(
            not changed_choices
            and max_score_delta <= SCORE_TOLERANCE
            and max_binary_delta <= BINARY_TOLERANCE
            and max_distribution_delta <= DISTRIBUTION_TOLERANCE
            and shared_physical <= fresh_physical
            and shared_fast_path_rows + safe_fallback_rows == len(rows)
        )

        backend.clear_repeated_state_cache()
        candidates = (
            Candidate("billing", "Payments and invoices"),
            Candidate("technical", "Software bugs and device issues"),
        )
        state = {
            "document": (
                "duplicate payment evidence account ledger merchant reference " * 160
            )
        }
        first_request = ChoiceRequest(
            id="cache-prime",
            state=state,
            question="Which queue should receive a duplicate card charge?",
            candidates=candidates,
        )
        second_request = ChoiceRequest(
            id="cache-hit",
            state=state,
            question="Which queue should receive a disputed payment?",
            candidates=candidates,
        )

        backend.reset_runtime_metrics()
        shared_scorer.score(first_request)
        prime_metrics = backend.runtime_metrics()

        backend.reset_runtime_metrics()
        shared_started = time.perf_counter()
        shared = shared_scorer.score(second_request)
        shared_seconds = time.perf_counter() - shared_started
        hit_metrics = backend.runtime_metrics()

        backend.reset_runtime_metrics()
        fresh_started = time.perf_counter()
        fresh = fresh_scorer.score(second_request)
        fresh_seconds = time.perf_counter() - fresh_started
        fresh_metrics = backend.runtime_metrics()

        repeated_delta = _deltas(shared, fresh)
        backend.clear_repeated_state_cache()
        cleared_metrics = backend.runtime_metrics()

        repeated_evidence = {
            **repeated_delta,
            "prime_runtime_metrics": prime_metrics,
            "hit_runtime_metrics": hit_metrics,
            "fresh_runtime_metrics": fresh_metrics,
            "cleared_runtime_metrics": cleared_metrics,
            "shared_seconds": shared_seconds,
            "fresh_seconds": fresh_seconds,
            "latency_speedup": fresh_seconds / shared_seconds if shared_seconds > 0 else None,
        }
        repeated_evidence["passed"] = bool(
            _within_tolerance(repeated_evidence)
            and prime_metrics["repeated_state_cache_misses"] >= 1
            and prime_metrics["repeated_state_cache_entries"] >= 1
            and hit_metrics["repeated_state_cache_hits"] >= 1
            and hit_metrics["repeated_state_cache_reused_tokens"] > 0
            and hit_metrics["physically_evaluated_tokens"]
            < fresh_metrics["physically_evaluated_tokens"]
            and hit_metrics["repeated_state_cache_entries"] <= 2
            and hit_metrics["repeated_state_cache_bytes"] <= 256 * 1024 * 1024
            and cleared_metrics["repeated_state_cache_entries"] == 0
            and cleared_metrics["repeated_state_cache_bytes"] == 0
        )

        return {
            "schema_version": 1,
            "gate": "llama-runtime-equivalence-v2",
            "model_identity": backend.identity,
            "tolerances": {
                "score": SCORE_TOLERANCE,
                "binary_conditional_probability": BINARY_TOLERANCE,
                "distribution": DISTRIBUTION_TOLERANCE,
            },
            "passed": bool(
                fixture_evidence["passed"] and repeated_evidence["passed"]
            ),
            "fixture_equivalence": fixture_evidence,
            "repeated_state_cache": repeated_evidence,
        }
    finally:
        backend.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Decisio llama.cpp shared execution against fresh evaluation"
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-batch", type=int, default=512)
    parser.add_argument("--n-ubatch", type=int, default=512)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--threads-batch", type=int, default=2)
    parser.add_argument("--require-pass", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, sort_keys=True))
    return int(args.require_pass and not evidence["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
