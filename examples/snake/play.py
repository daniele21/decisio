"""Play Snake with Decisio as the controller."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from decisio.schema import Candidate, ChoiceRequest, DecisionResult
from decisio.scorers import IndependentSemanticScorer, LetterTokenScorer, SemanticBinaryScorer
from examples.snake.game import SnakeGame

SCORER_CHOICES = ("direct", "semantic", "semantic-independent", "letters")

QUESTION = (
    "Which single move should Snake take now? All supplied moves avoid immediate collision. "
    "Use the board and the sensors on each option. Prefer eating food or getting closer when "
    "future mobility remains healthy. Avoid dead ends and repeated cells with high loop risk; "
    "moving farther can be necessary to escape a trap. Reachable space treats the body as static, "
    "and Manhattan distance ignores obstacles; neither guarantees a safe route."
)
COMPACT_QUESTION = (
    "Choose a safe Snake move: eat food or get closer while preserving escape space. "
    "Avoid dead ends and repeated visits. "
    "food=Manhattan distance before>after (ignores obstacles); "
    "exits=safe next directions; area=reachable cells with static body; "
    "visits=recent visits to destination. Coordinates: x right, y down."
)


def add_control_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input-format", choices=("verbose", "compact"), default="verbose")
    parser.add_argument("--reuse-prefix", action="store_true",
                        help="Experimental question-first direct scoring with exact prefix reuse")
    parser.add_argument("--controller", choices=("model", "adjacent-food"), default="model",
                        help="adjacent-food applies an explicit local food policy before scoring")


def _candidate(game: SnakeGame, direction: str, input_format: str = "verbose") -> Candidate:
    features = game.action_features(direction)
    position = features["next_position"]
    safe_after = ", ".join(features["safe_directions_after"]) or "none"
    if input_format == "compact":
        return Candidate(id=direction, description=(
            f"{direction.upper()} next=({position['x']},{position['y']}); "
            f"food={features['food_distance_before']}>{features['food_distance_after']}; "
            f"eat={str(features['eats_food']).lower()}; exits={safe_after}; "
            f"area={features['reachable_free_cells_after']}; "
            f"visits={features['recent_visit_count']}"
        ))
    return Candidate(
        id=direction,
        description=(
            f"Move {direction.upper()} to (x={position['x']}, y={position['y']}). "
            f"Food progress: {features['food_progress']}; "
            f"Manhattan distance {features['food_distance_before']} -> "
            f"{features['food_distance_after']}; eats food: "
            f"{str(features['eats_food']).lower()}. "
            f"Future mobility: {features['safe_moves_after']} safe next moves ({safe_after}); "
            f"{features['reachable_free_cells_after']} reachable cells with static body. "
            f"Recent path: next cell visited {features['recent_visit_count']} times "
            f"in the bounded window; loop risk {features['loop_risk']}."
        ),
    )


def build_request(
    game: SnakeGame, directions: tuple[str, ...] | None = None, *, input_format: str = "verbose",
) -> ChoiceRequest:
    return ChoiceRequest.from_dict(
        build_request_data(game, game.safe_directions() if directions is None else directions,
                       input_format=input_format)
    )


def build_scorer(args: argparse.Namespace) -> Any:
    if args.reuse_prefix and args.scorer not in {"direct", "letters"}:
        raise ValueError("--reuse-prefix requires --scorer direct or letters")
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
    if args.scorer == "semantic":
        return SemanticBinaryScorer(backend)
    if args.scorer == "semantic-independent":
        return IndependentSemanticScorer(backend)
    if args.scorer in {"direct", "letters"}:
        return LetterTokenScorer(backend, reuse_prefix=args.reuse_prefix)
    raise ValueError(f"unsupported Snake scorer: {args.scorer}")


def _deterministic_decision(
    direction: str, scorer: str, *, status: str = "deterministic_constraint_resolution",
) -> DecisionResult:
    return DecisionResult(
        choice=direction,
        distribution={direction: 1.0},
        scores={direction: 0.0},
        scorer=scorer,
        probability_status=status,
        model={"backend": "deterministic"},
    )


def build_request_data(
    game: SnakeGame, directions: tuple[str, ...], *, input_format: str = "verbose",
) -> dict[str, Any]:
    if input_format not in {"verbose", "compact"}:
        raise ValueError(f"unknown input format: {input_format}")
    state = game.state()
    if input_format == "compact":
        state.pop("board_grid")
        state.pop("legend")
    return {
        "id": f"snake-step-{game.steps}",
        "state": state,
        "question": COMPACT_QUESTION if input_format == "compact" else QUESTION,
        "candidates": [_candidate(game, direction, input_format).to_dict()
                       for direction in directions],
    }


def choose_move(
    game: SnakeGame, scorer: Any, *, input_format: str = "verbose", controller: str = "model",
):
    if controller not in {"model", "adjacent-food"}:
        raise ValueError(f"unknown controller: {controller}")
    constraints = game.action_constraints()
    safe = game.safe_directions()
    legal = game.candidate_directions()
    features = game.candidate_features(safe)
    food_move = next((d for d in safe if features[d]["eats_food"]
                     and features[d]["safe_moves_after"] > 0), None)
    if len(safe) >= 2 and controller == "adjacent-food" and food_move is not None:
        decision = _deterministic_decision(
            food_move, "snake_adjacent_food_policy_v1",
            status="deterministic_application_policy",
        )
        request_data = build_request_data(game, safe, input_format=input_format)
        latency = 0.0
        mode = "deterministic_adjacent_food_policy"
    elif len(safe) >= 2:
        request = build_request(game, safe, input_format=input_format)
        started = time.perf_counter()
        decision = scorer.score(request)
        latency = time.perf_counter() - started
        request_data = request.to_dict()
        mode = "model"
    elif len(safe) == 1:
        direction = safe[0]
        decision = _deterministic_decision(direction, "deterministic_single_safe_action_v1")
        latency = 0.0
        request_data = build_request_data(game, safe, input_format=input_format)
        mode = "deterministic_single_safe_action"
    else:
        direction = game.direction if game.direction in legal else legal[0]
        decision = _deterministic_decision(direction, "deterministic_no_safe_action_v1")
        latency = 0.0
        request_data = build_request_data(game, (), input_format=input_format)
        mode = "deterministic_no_safe_action"
    return request_data, decision, latency, {
        "mode": mode,
        "legal_actions": list(legal),
        "safe_actions": list(safe),
        "candidate_features": features,
        "filtered_actions": {
            direction: reason
            for direction, reason in constraints.items()
            if reason is not None
        },
    }


def append_trace(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a headless Snake episode controlled by Decisio"
    )
    parser.add_argument("--model", type=Path, required=True)
    add_control_arguments(parser)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-batch", type=int, default=512)
    parser.add_argument("--n-ubatch", type=int, default=512)
    parser.add_argument("--threads", type=int)
    parser.add_argument("--threads-batch", type=int)
    parser.add_argument("--max-sequences", type=int, default=8)
    parser.add_argument("--mlock", action="store_true")
    parser.add_argument("--no-mmap", action="store_true")
    parser.add_argument(
        "--scorer",
        choices=SCORER_CHOICES,
        default="direct",
        help=(
            "direct performs one A/B/C/... choice-logit forward pass; "
            "semantic modes remain available for comparison"
        ),
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--height", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--trace", type=Path)
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
    try:
        while game.alive and game.steps < args.max_steps:
            if args.render:
                print(f"\nstep={game.steps} score={game.score} direction={game.direction}")
                print(game.render())
            request_data, decision, latency, constraints = choose_move(
                game, scorer, input_format=args.input_format, controller=args.controller,
            )
            total_model_latency += latency
            model_decisions += int(constraints["mode"] == "model")
            outcome = game.step(decision.choice)
            print(
                f"step={game.steps:03d} choice={decision.choice:<5} "
                f"score={game.score:02d} p={decision.distribution[decision.choice]:.4f} "
                f"latency={latency:.3f}s mode={constraints['mode']} "
                f"alive={outcome.alive} reason={outcome.reason or '-'}"
            )
            if args.trace is not None:
                append_trace(args.trace, {
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
                })
    finally:
        close = getattr(scorer.backend, "close", None)
        if callable(close):
            close()

    if args.render:
        print("\nfinal board")
        print(game.render())

    print(json.dumps({
        "alive": game.alive,
        "steps": game.steps,
        "score": game.score,
        "snake_length": len(game.snake),
        "stop_reason": "max_steps" if game.alive else "game_over",
        "scorer": args.scorer,
        "model": args.model.name,
        "seed": args.seed,
        "model_decisions": model_decisions,
        "total_model_latency_seconds": total_model_latency,
        "mean_model_latency_seconds": (
            total_model_latency / model_decisions if model_decisions else 0.0
        ),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
