"""Play Snake with Decisio as the controller.

Example:
    uv run python examples/snake/play.py --model Qwen/Qwen3.5-0.8B --revision 2fc06364
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from decisio.backends.qwen import (
    DEFAULT_MODEL,
    DEFAULT_REVISION,
    QwenBackendConfig,
    QwenTransformersBackend,
)
from decisio.schema import Candidate, ChoiceRequest
from decisio.scorers import LetterTokenScorer, SemanticBinaryScorer

from examples.snake.game import DIRECTIONS, SnakeGame

QUESTION = (
    "Which single move should Snake take now? Highest priority: avoid an immediate wall or "
    "body collision. Among safe moves, prefer progress toward the food while preserving future "
    "mobility and avoiding obvious traps."
)


def build_request(game: SnakeGame) -> ChoiceRequest:
    candidates = tuple(
        Candidate(
            id=direction,
            description=(
                f"Move {direction.upper()} by one grid cell with delta "
                f"(dx={DIRECTIONS[direction][0]}, dy={DIRECTIONS[direction][1]})."
            ),
        )
        for direction in game.candidate_directions()
    )
    return ChoiceRequest(
        id=f"snake-step-{game.steps}",
        state=game.state(),
        question=QUESTION,
        candidates=candidates,
    )


def build_scorer(args: argparse.Namespace) -> Any:
    backend = QwenTransformersBackend(
        QwenBackendConfig(
            model=args.model,
            revision=args.revision,
            device=args.device,
            dtype=args.dtype,
            local_files_only=args.local_files_only,
        )
    )
    if args.scorer == "semantic":
        return SemanticBinaryScorer(backend)
    return LetterTokenScorer(backend)


def append_trace(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a headless Snake episode controlled by Decisio")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument(
        "--dtype", choices=["bfloat16", "float16", "float32"], default="bfloat16"
    )
    parser.add_argument("--scorer", choices=["semantic", "letters"], default="semantic")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--height", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--local-files-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_steps < 1:
        raise ValueError("--max-steps must be positive")
    game = SnakeGame(width=args.width, height=args.height, seed=args.seed)
    scorer = build_scorer(args)

    if args.trace is not None:
        args.trace.unlink(missing_ok=True)

    while game.alive and game.steps < args.max_steps:
        if args.render:
            print(f"\nstep={game.steps} score={game.score} direction={game.direction}")
            print(game.render())

        request = build_request(game)
        before = request.to_dict()
        decision = scorer.score(request)
        chosen_probability = decision.distribution[decision.choice]
        outcome = game.step(decision.choice)

        print(
            f"step={game.steps:03d} choice={decision.choice:<5} "
            f"score={game.score:02d} p={chosen_probability:.4f} "
            f"alive={outcome.alive} reason={outcome.reason or '-'}"
        )

        if args.trace is not None:
            append_trace(
                args.trace,
                {
                    "step": game.steps,
                    "request": before,
                    "decision": decision.to_dict(),
                    "outcome": {
                        "alive": outcome.alive,
                        "ate_food": outcome.ate_food,
                        "reason": outcome.reason,
                        "game_score": game.score,
                    },
                },
            )

    if args.render:
        print("\nfinal board")
        print(game.render())

    print(
        json.dumps(
            {
                "alive": game.alive,
                "steps": game.steps,
                "score": game.score,
                "snake_length": len(game.snake),
                "stop_reason": "max_steps" if game.alive else "game_over",
                "scorer": args.scorer,
                "model": args.model,
                "seed": args.seed,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
