"""Run the versioned Snake controller matrix and append every configuration result."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from examples.snake.planner import PLANNER_VERSION, SnakePlanner

from .snake_controller_benchmark import (
    BENCHMARK_ID,
    CONFIGS,
    DEFAULT_CONFIGS,
    DEFAULT_FIXTURE,
    DEFAULT_LEDGER,
    SCHEMA_VERSION,
    append_ledger,
    build_scorer,
    canonical_sha256,
    episode_benchmark,
    file_sha256,
    fixed_state_benchmark,
    load_fixture,
    runtime_metrics,
    source_identity,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ledger_record(
    *,
    run_id: str,
    started_at: str,
    source: dict[str, Any],
    fixture: dict[str, Any],
    protocol: dict[str, Any],
    config: Any,
    model: dict[str, Any],
    fixed: dict[str, Any] | None,
    episodes: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark": BENCHMARK_ID,
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": _now(),
        "status": status,
        "error": error,
        "source": source,
        "fixture": fixture,
        "protocol": protocol,
        "configuration": config.to_dict(),
        "model_runtime": model,
        "fixed_state": fixed,
        "episodes": episodes,
        "runtime_metrics": runtime,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    cases = load_fixture(args.fixture, args.fixed_limit)
    source = source_identity()
    run_id = (
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-"
        f"{str(source['commit'])[:8]}-{uuid.uuid4().hex[:8]}"
    )
    fixture = {
        "path": str(args.fixture),
        "sha256": file_sha256(args.fixture),
        "selected_cases": len(cases),
    }
    planner = SnakePlanner(
        max_nodes=args.planner_max_nodes,
        max_depth=args.planner_max_depth,
        post_food_escape_horizon=args.post_food_escape_horizon,
        projected_survival_horizon=args.projected_survival_horizon,
    )
    protocol_payload = {
        "selected_case_ids": [str(case["id"]) for case in cases],
        "planner": {
            "version": PLANNER_VERSION,
            "max_nodes": planner.max_nodes,
            "max_depth": planner.max_depth,
            "post_food_escape_horizon": planner.post_food_escape_horizon,
            "projected_survival_horizon": planner.projected_survival_horizon,
        },
        "episodes": {
            "seeds": args.episode_seeds,
            "width": args.width,
            "height": args.height,
            "max_steps": args.episode_max_steps,
            "stall_steps": args.stall_steps,
        },
    }
    protocol = {**protocol_payload, "sha256": canonical_sha256(protocol_payload)}
    backend = LlamaCppBackend(
        LlamaCppBackendConfig(
            model=args.model,
            n_ctx=args.n_ctx,
            n_batch=args.n_batch,
            n_ubatch=args.n_ubatch,
            n_threads=args.threads,
            n_threads_batch=args.threads_batch,
            max_sequences=args.max_sequences,
            use_mmap=not args.no_mmap,
            use_mlock=args.mlock,
        )
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark": BENCHMARK_ID,
        "run_id": run_id,
        "source": source,
        "fixture": fixture,
        "protocol": protocol,
        "model_runtime": backend.identity,
        "configurations": {},
    }
    try:
        for config_id in args.configs:
            config = CONFIGS[config_id]
            started = _now()
            fixed = episodes = runtime = None
            try:
                backend.clear_repeated_state_cache()
                backend.reset_runtime_metrics()
                scorer = build_scorer(config, backend)
                fixed = fixed_state_benchmark(cases, scorer, config, planner)
                episodes = episode_benchmark(
                    scorer,
                    config,
                    seeds=args.episode_seeds,
                    width=args.width,
                    height=args.height,
                    max_steps=args.episode_max_steps,
                    stall_steps=args.stall_steps,
                )
                runtime = runtime_metrics(backend)
                row = _ledger_record(
                    run_id=run_id,
                    started_at=started,
                    source=source,
                    fixture=fixture,
                    protocol=protocol,
                    config=config,
                    model=backend.identity,
                    fixed=fixed,
                    episodes=episodes,
                    runtime=runtime,
                    status="completed",
                )
                append_ledger(args.ledger, row)
                report["configurations"][config_id] = row
                print(
                    f"config={config_id} agreement={fixed['optimal_set_agreement']:.3f} "
                    f"catastrophic={fixed['catastrophic_miss_rate']:.3f} "
                    f"median_food={episodes['median_food_eaten']}",
                    flush=True,
                )
            except Exception as exc:
                row = _ledger_record(
                    run_id=run_id,
                    started_at=started,
                    source=source,
                    fixture=fixture,
                    protocol=protocol,
                    config=config,
                    model=backend.identity,
                    fixed=fixed,
                    episodes=episodes,
                    runtime=runtime,
                    status="failed",
                    error=f"{type(exc).__name__}: {exc}",
                )
                append_ledger(args.ledger, row)
                report["configurations"][config_id] = row
                if not args.continue_on_error:
                    raise
    finally:
        backend.close()
    report["finished_at"] = _now()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--model", type=Path, required=True)
    result.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    result.add_argument("--configs", nargs="+", choices=sorted(CONFIGS), default=list(DEFAULT_CONFIGS))
    result.add_argument("--fixed-limit", type=int)
    result.add_argument("--episode-seeds", nargs="+", type=int, default=[7, 19, 43, 71])
    result.add_argument("--width", type=int, default=8)
    result.add_argument("--height", type=int, default=8)
    result.add_argument("--episode-max-steps", type=int, default=256)
    result.add_argument("--stall-steps", type=int, default=32)
    result.add_argument("--planner-max-nodes", type=int, default=50_000)
    result.add_argument("--planner-max-depth", type=int, default=96)
    result.add_argument("--post-food-escape-horizon", type=int, default=4)
    result.add_argument("--projected-survival-horizon", type=int, default=8)
    result.add_argument("--n-ctx", type=int, default=8192)
    result.add_argument("--n-batch", type=int, default=128)
    result.add_argument("--n-ubatch", type=int, default=128)
    result.add_argument("--threads", type=int)
    result.add_argument("--threads-batch", type=int)
    result.add_argument("--max-sequences", type=int, default=8)
    result.add_argument("--mlock", action="store_true")
    result.add_argument("--no-mmap", action="store_true")
    result.add_argument("--continue-on-error", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.fixed_limit is not None and args.fixed_limit < 1:
        raise ValueError("--fixed-limit must be positive")
    report = run(args)
    print(json.dumps({"run_id": report["run_id"], "ledger": str(args.ledger)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
