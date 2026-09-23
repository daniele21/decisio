"""Diagnostic fixed-state input/runtime comparison, not a scorer promotion gate."""
from __future__ import annotations

import argparse
import json
import os
import resource
import time
import uuid
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from decisio.scorers import LetterTokenScorer
from examples.snake.game import SnakeGame
from examples.snake.play import build_request


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch", type=int, default=128)
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--threads-batch", type=int, default=11)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--variants", nargs="+",
                        choices=(
                            "verbose", "compact", "prefix_fresh", "prefix_shared",
                            "stateful_fresh", "stateful_shared",
                        ),
                        default=("verbose", "stateful_fresh", "stateful_shared"))
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    config = LlamaCppBackendConfig(
        model=args.model, n_ctx=8192, n_batch=args.batch, n_ubatch=args.batch,
        n_threads=args.threads, n_threads_batch=args.threads_batch,
    )
    backend = LlamaCppBackend(config)
    run_id = uuid.uuid4().hex
    recorded_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    variants = {
        "verbose": ("verbose", LetterTokenScorer(backend)),
        "compact": ("compact", LetterTokenScorer(backend)),
        "prefix_fresh": ("compact", LetterTokenScorer(backend.fresh_view(), reuse_prefix=True)),
        "prefix_shared": ("compact", LetterTokenScorer(backend, reuse_prefix=True)),
        "stateful_fresh": (
            "verbose",
            LetterTokenScorer(backend.fresh_view(), reuse_prefix=True),
        ),
        "stateful_shared": (
            "verbose",
            LetterTokenScorer(backend, reuse_prefix=True),
        ),
    }
    variants = {name: variants[name] for name in args.variants}
    run_config = {
        "batch": args.batch,
        "threads": args.threads,
        "threads_batch": args.threads_batch,
        "rounds": args.rounds,
        "variants": list(args.variants),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Load/warm all execution paths outside measured rows. Drop warm cache afterwards.
        for input_format, scorer in variants.values():
            scorer.score(build_request(SnakeGame(seed=7), input_format=input_format))
        backend.clear_repeated_state_cache()
        with args.output.open("a", encoding="utf-8") as stream:
            for repeat in range(args.rounds):
                for food in [(4, 2), (4, 3), (6, 4), (5, 4), (4, 6), (4, 5)]:
                    game = SnakeGame(seed=7)
                    game.food = food
                    expected = "up" if food[1] < 4 else "down" if food[1] > 4 else "right"
                    for reverse in (False, True):
                        items = list(variants.items())
                        if repeat % 2:
                            items.reverse()
                        for name, (input_format, scorer) in items:
                            request = build_request(game, input_format=input_format)
                            if reverse:
                                request = replace(request, candidates=request.candidates[::-1])
                            backend.reset_runtime_metrics()
                            started = time.perf_counter()
                            result = scorer.score(request)
                            elapsed = time.perf_counter() - started
                            row = {
                                "benchmark": "snake-input-efficiency-diagnostic-v1",
                                "run_id": run_id,
                                "recorded_at_utc": recorded_at_utc,
                                "run_config": run_config,
                                "model_runtime": backend.identity,
                                "round": repeat, "food": food, "reverse": reverse,
                                "variant": name, "expected": expected,
                                "request": request.to_dict(), "decision": result.to_dict(),
                                "seconds": elapsed, "runtime": backend.runtime_metrics(),
                                "process_max_rss_platform_units": resource.getrusage(
                                    resource.RUSAGE_SELF).ru_maxrss,
                            }
                            stream.write(json.dumps(row, sort_keys=True) + "\n")
                            stream.flush()
                            os.fsync(stream.fileno())
                    print(f"round={repeat} food={food} complete", flush=True)
    finally:
        backend.close()


if __name__ == "__main__":
    main()
