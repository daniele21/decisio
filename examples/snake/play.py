"""Play Snake with Decisio as the controller."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from decisio.backends.llama_cpp import LlamaCppBackend, LlamaCppBackendConfig
from decisio.schema import Candidate, ChoiceRequest, DecisionResult
from decisio.scorers import IndependentSemanticScorer, LetterTokenScorer, SemanticBinaryScorer
from examples.snake.game import SnakeGame

SCORER_CHOICES = ("direct", "semantic", "semantic-independent", "letters")

DECISION_CONTEXT_ID = "snake-stateful-v1"
STATIC_DECISION_CONTEXT = (
    "You control Snake on a rectangular grid. This text is the stable decision contract for the "
    "whole episode; the current board is supplied separately on every move. Coordinates use "
    "origin (0,0) at the top-left, x increases to the right, and y increases downward. In a "
    "rendered board H is the head, o is body, T is tail, * is food, and . is empty. "
    "The application has already removed moves that reverse direction or cause an immediate wall "
    "or body collision, so choose only among the supplied candidates. Treat those deterministic "
    "constraints as facts rather than something to second-guess probabilistically. "
    "Decision priority is: first preserve survival and future mobility; then avoid projected dead "
    "ends and severe loss of reachable space; then eat food when doing so leaves an escape; then "
    "prefer progress toward food when mobility remains healthy; finally prefer a less-revisited "
    "destination when otherwise comparable. Moving farther from food can be correct when it "
    "preserves escape space or avoids a loop. Candidate sensors are deterministic hints: food "
    "distance is Manhattan distance and ignores obstacles; exits are immediately safe next "
    "directions after the candidate; area is the number of cells reachable from the projected head "
    "while treating the projected body as static; visits counts recent visits to the destination "
    "and is summarized as loop risk. None of these local sensors proves a globally safe route. "
    "Use only the current decision state and candidate sensors supplied in this request. Do not "
    "invent previous boards, hidden history, or unavailable actions. Return exactly one supplied "
    "option."
)
DECISION_CONTEXT_SHA256 = hashlib.sha256(
    STATIC_DECISION_CONTEXT.encode("utf-8")
).hexdigest()

QUESTION = (
    STATIC_DECISION_CONTEXT
    + "\n\nCurrent decision: choose the single best move from the supplied safe actions. "
      "Use the current board plus the deterministic sensors attached to each option."
)
COMPACT_QUESTION = (
    STATIC_DECISION_CONTEXT
    + "\n\nCurrent decision: choose the single best move from the supplied safe actions. "
      "Compact option fields are next=(x,y), food=distance-before>distance-after, eat, exits, "
      "area, and visits."
)


def add_control_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input-format", choices=("verbose", "compact"), default="verbose")
    prefix = parser.add_mutually_exclusive_group()
    prefix.add_argument(
        "--reuse-prefix",
        dest="reuse_prefix",
        action="store_true",
        help="Force stateful fixed-context reuse for direct/letters scoring",
    )
    prefix.add_argument(
        "--fresh-prefix",
        dest="reuse_prefix",
        action="store_false",
        help="Disable fixed-context reuse and evaluate the full direct prompt fresh",
    )
    parser.set_defaults(reuse_prefix=None)
    parser.add_argument("--controller", choices=("model", "adjacent-food"), default="model",
                        help="adjacent-food applies an explicit local food policy before scoring")


def prefix_reuse_enabled(args: argparse.Namespace) -> bool:
    """Use stateful context reuse by default only for the direct choice path."""
    if args.reuse_prefix is not None:
        return bool(args.reuse_prefix)
    return args.scorer in {"direct", "letters"}


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
    reuse_prefix = prefix_reuse_enabled(args)
    if reuse_prefix and args.scorer not in {"direct", "letters"}:
        raise ValueError("--reuse-prefix requires --scorer direct or letters")
    backend = LlamaCppBackend(
        LlamaCppBackendConfig(
            model=args.model,
            device=args.device,
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
        return LetterTokenScorer(
            backend,
            reuse_prefix=True,
            shared_prefix_execution=reuse_prefix,
        )
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
    # Static coordinate/legend semantics live in STATIC_DECISION_CONTEXT. Keep the model request
    # focused on the current board and deterministic candidate sensors rather than replaying
    # bounded history or static instructions on every step.
    state.pop("decision_memory", None)
    state.pop("legend", None)
    board = dict(state["board"])
    board.pop("coordinates", None)
    state["board"] = board
    if input_format == "compact":
        state.pop("board_grid")
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
        "decision_context": {
            "id": DECISION_CONTEXT_ID,
            "sha256": DECISION_CONTEXT_SHA256,
            "state_scope": "current_only",
            "static_prefix_reusable": True,
        },
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
    parser.add_argument(
        "--device",
        choices=("cpu", "metal"),
        default="cpu",
        help="execution device; metal requires a Metal-enabled llama-cpp-python build",
    )
    add_control_arguments(parser)
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-batch", type=int, default=128)
    parser.add_argument("--n-ubatch", type=int, default=128)
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
    total_logical_input_tokens = 0
    total_physical_input_tokens = 0
    repeated_state_cache_hits = 0
    backend = scorer.backend
    try:
        while game.alive and game.steps < args.max_steps:
            if args.render:
                print(f"\nstep={game.steps} score={game.score} direction={game.direction}")
                print(game.render())
            reset_metrics = getattr(backend, "reset_runtime_metrics", None)
            if callable(reset_metrics):
                reset_metrics()
            request_data, decision, latency, constraints = choose_move(
                game, scorer, input_format=args.input_format, controller=args.controller,
            )
            runtime_metrics: dict[str, Any] = {}
            metrics = getattr(backend, "runtime_metrics", None)
            if callable(metrics):
                value = metrics()
                if isinstance(value, dict):
                    runtime_metrics = dict(value)
            total_model_latency += latency
            model_decisions += int(constraints["mode"] == "model")
            total_logical_input_tokens += int(runtime_metrics.get("logical_input_tokens", 0))
            total_physical_input_tokens += int(
                runtime_metrics.get("physically_evaluated_tokens", 0)
            )
            repeated_state_cache_hits += int(
                runtime_metrics.get("repeated_state_cache_hits", 0)
            )
            outcome = game.step(decision.choice)
            print(
                f"step={game.steps:03d} choice={decision.choice:<5} "
                f"score={game.score:02d} p={decision.distribution[decision.choice]:.4f} "
                f"latency={latency:.3f}s mode={constraints['mode']} "
                f"reuse={runtime_metrics.get('reuse_ratio', 0.0):.3f} "
                f"alive={outcome.alive} reason={outcome.reason or '-'}"
            )
            if args.trace is not None:
                append_trace(args.trace, {
                    "step": game.steps,
                    "request": request_data,
                    "constraints": constraints,
                    "decision_latency_seconds": latency,
                    "decision": decision.to_dict(),
                    "runtime_metrics": runtime_metrics,
                    "outcome": {
                        "alive": outcome.alive,
                        "ate_food": outcome.ate_food,
                        "reason": outcome.reason,
                        "game_score": game.score,
                    },
                })
    finally:
        close = getattr(backend, "close", None)
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
        "decision_context_id": DECISION_CONTEXT_ID,
        "prefix_reuse_enabled": prefix_reuse_enabled(args),
        "logical_input_tokens": total_logical_input_tokens,
        "physically_evaluated_tokens": total_physical_input_tokens,
        "repeated_state_cache_hits": repeated_state_cache_hits,
        "total_model_latency_seconds": total_model_latency,
        "mean_model_latency_seconds": (
            total_model_latency / model_decisions if model_decisions else 0.0
        ),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
