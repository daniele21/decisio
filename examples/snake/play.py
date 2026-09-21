"""Play Snake with Decisio as the controller.

Example:
    uv run python -m examples.snake.play --model Qwen/Qwen3.5-0.8B --revision 2fc06364
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from decisio.backends.qwen import (
    DEFAULT_MODEL,
    DEFAULT_REVISION,
    QwenBackendConfig,
    QwenTransformersBackend,
)
from decisio.schema import Candidate, ChoiceRequest, DecisionResult
from decisio.scorers import (
    IndependentSemanticScorer,
    LetterTokenScorer,
    SemanticBinaryScorer,
)
from examples.snake.game import DIRECTIONS, SnakeGame

QUESTION = (
    "Which single move should Snake take now? All supplied candidates are already known to avoid "
    "an immediate wall/body collision. Prefer progress toward the food while preserving future "
    "mobility and avoiding obvious traps."
)


def _candidate(direction: str) -> Candidate:
    return Candidate(
        id=direction,
        description=(
            f"Move {direction.upper()} by one grid cell with delta "
            f"(dx={DIRECTIONS[direction][0]}, dy={DIRECTIONS[direction][1]})."
        ),
    )


def build_request(
    game: SnakeGame,
    directions: tuple[str, ...] | None = None,
) -> ChoiceRequest:
    directions = directions or game.safe_directions()
    return ChoiceRequest(
        id=f"snake-step-{game.steps}",
        state=game.state(),
        question=QUESTION,
        candidates=tuple(_candidate(direction) for direction in directions),
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
    if args.scorer == "semantic-independent":
        return IndependentSemanticScorer(backend)
    return LetterTokenScorer(backend)


def _deterministic_decision(direction: str, scorer: str) -> DecisionResult:
    return DecisionResult(
        choice=direction,
        distribution={direction: 1.0},
        scores={direction: 0.0},
        scorer=scorer,
        probability_status="deterministic_constraint_resolution",
        model={"backend": "deterministic"},
    )


def _trace_request(game: SnakeGame, directions: tuple[str, ...]) -> dict[str, Any]:
    return {
        "id": f"snake-step-{game.steps}",
        "state": game.state(),
        "question": QUESTION,
        "candidates": [_candidate(direction).to_dict() for direction in directions],
    }


def choose_move(
    game: SnakeGame,
    scorer: Any,
) -> tuple[dict[str, Any], DecisionResult, float, dict[str, Any]]:
    constraints = game.action_constraints()
    safe = game.safe_directions()
    legal = game.candidate_directions()

    if len(safe) >= 2:
        request = build_request(game, safe)
        started = time.perf_counter()
        decision = scorer.score(request)
        latency = time.perf_counter() - started
        request_data = request.to_dict()
        mode = "model"
    elif len(safe) == 1:
        direction = safe[0]
        decision = _deterministic_decision(direction, "deterministic_single_safe_action_v1")
        latency = 0.0
        request_data = _trace_request(game, safe)
        mode = "deterministic_single_safe_action"
    else:
        direction = game.direction if game.direction in legal else legal[0]
        decision = _deterministic_decision(direction, "deterministic_no_safe_action_v1")
        latency = 0.0
        request_data = _trace_request(game, ())
        mode = "deterministic_no_safe_action"

    constraint_data = {
        "mode": mode,
        "legal_actions": list(legal),
        "safe_actions": list(safe),
        "filtered_actions": {
            direction: reason
            for direction, reason in constraints.items()
            if reason is not None
        },
    }
    return request_data, decision, latency, constraint_data


def append_trace(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a headless Snake episode controlled by Decisio"
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument(
        "--dtype", choices=["bfloat16", "float16", "float32"], default="bfloat16"
    )
    parser.add_argument(
        "--scorer",
        choices=["semantic", "semantic-independent", "letters"],
        default="semantic",
    )
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

    total_model_latency = 0.0
    model_decisions = 0
    while game.alive and game.steps < args.max_steps:
        if args.render:
            print(f"\nstep={game.steps} score={game.score} direction={game.direction}")
            print(game.render())

        request_data, decision, latency, constraints = choose_move(game, scorer)
        total_model_latency += latency
        model_decisions += int(constraints["mode"] == "model")
        chosen_probability = decision.distribution[decision.choice]
        outcome = game.step(decision.choice)

        print(
            f"step={game.steps:03d} choice={decision.choice:<5} "
            f"score={game.score:02d} p={chosen_probability:.4f} "
            f"latency={latency:.3f}s mode={constraints['mode']} "
            f"alive={outcome.alive} reason={outcome.reason or '-'}"
        )

        if args.trace is not None:
            append_trace(
                args.trace,
                {
                    "step": game.steps,
                    "request": request_data,
                    "constraints": constraints,
                    "decision_latency_seconds": latency,
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
                "model_decisions": model_decisions,
                "total_model_latency_seconds": total_model_latency,
                "mean_model_latency_seconds": (
                    total_model_latency / model_decisions if model_decisions else 0.0
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
