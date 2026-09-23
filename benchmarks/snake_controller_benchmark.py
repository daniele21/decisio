"""Core semantics for the Snake controller benchmark."""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from decisio.baselines import GeneratedJsonScorer
from decisio.schema import DecisionResult
from decisio.scorers import IndependentSemanticScorer, LetterTokenScorer, SemanticBinaryScorer
from examples.snake.game import RECENT_HEAD_LIMIT, SnakeGame
from examples.snake.planner import PlannerResult, SnakePlanner
from examples.snake.play import build_request

BENCHMARK_ID = "snake-controller-benchmark-v1"
SCHEMA_VERSION = 1
DEFAULT_FIXTURE = Path("benchmarks/fixtures/snake-controller-v1.jsonl")
DEFAULT_LEDGER = Path(".artifacts/snake-controller/history.jsonl")


@dataclass(frozen=True, slots=True)
class ControllerConfig:
    id: str
    scorer: str
    input_format: str
    reuse_prefix: bool
    controller: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scorer": self.scorer,
            "input_format": self.input_format,
            "reuse_prefix": self.reuse_prefix,
            "controller": self.controller,
        }


CONFIGS = {
    config.id: config
    for config in (
        ControllerConfig("direct-stateful-verbose", "direct", "verbose", True, "model"),
        ControllerConfig("direct-fresh-verbose", "direct", "verbose", False, "model"),
        ControllerConfig("direct-stateful-compact", "direct", "compact", True, "model"),
        ControllerConfig("semantic-verbose", "semantic", "verbose", False, "model"),
        ControllerConfig(
            "semantic-independent-verbose", "semantic-independent", "verbose", False, "model"
        ),
        ControllerConfig("direct-adjacent-food", "direct", "verbose", True, "adjacent-food"),
        ControllerConfig("generated-verbose", "generated", "verbose", False, "model"),
    )
}
DEFAULT_CONFIGS = tuple(key for key in CONFIGS if key != "generated-verbose")


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def source_identity() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD") or os.getenv("GITHUB_SHA") or "unknown",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD") or os.getenv("GITHUB_REF_NAME"),
        "dirty": bool(status) if status is not None else None,
    }


def append_ledger(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_fixture(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        raise ValueError("Snake controller fixture is empty")
    ids = [str(row["id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Snake controller fixture ids must be unique")
    return rows


def game_from_case(case: dict[str, Any]) -> SnakeGame:
    game = SnakeGame(width=int(case["width"]), height=int(case["height"]), seed=0)
    game.snake = [tuple(point) for point in case["snake"]]
    game.direction = str(case["direction"])
    game.food = tuple(case["food"])
    game.score = int(case.get("score", 0))
    game.steps = int(case.get("steps", 0))
    game.steps_since_food = int(case.get("steps_since_food", 0))
    game.alive = True
    recent = [tuple(point) for point in case.get("recent_heads", [game.head])]
    game._recent_heads = deque(recent, maxlen=RECENT_HEAD_LIMIT)
    return game


def build_scorer(config: ControllerConfig, backend: Any) -> Any:
    if config.scorer == "direct":
        return LetterTokenScorer(backend, reuse_prefix=config.reuse_prefix)
    if config.scorer == "semantic":
        return SemanticBinaryScorer(backend)
    if config.scorer == "semantic-independent":
        return IndependentSemanticScorer(backend)
    if config.scorer == "generated":
        return GeneratedJsonScorer(backend)
    raise ValueError(f"unknown scorer {config.scorer!r}")


def _deterministic(direction: str, scorer: str) -> DecisionResult:
    return DecisionResult(
        choice=direction,
        distribution={direction: 1.0},
        scores={direction: 0.0},
        scorer=scorer,
        probability_status="deterministic_application_policy",
        model={"backend": "deterministic"},
    )


def controller_decision(
    game: SnakeGame,
    scorer: Any,
    config: ControllerConfig,
    *,
    reverse_candidates: bool = False,
) -> tuple[str | None, float, str]:
    safe = game.safe_directions()
    if len(safe) == 1:
        return safe[0], 0.0, "deterministic_single_safe_action"
    if not safe:
        return None, 0.0, "deterministic_no_safe_action"
    features = game.candidate_features(safe)
    food_move = next(
        (
            direction
            for direction in safe
            if features[direction]["eats_food"] and features[direction]["safe_moves_after"] > 0
        ),
        None,
    )
    if config.controller == "adjacent-food" and food_move is not None:
        _deterministic(food_move, "snake_adjacent_food_policy_v1")
        return food_move, 0.0, "deterministic_adjacent_food_policy"
    directions = tuple(reversed(safe)) if reverse_candidates else safe
    request = build_request(game, directions, input_format=config.input_format)
    started = time.perf_counter()
    result = scorer.score(request)
    return result.choice, time.perf_counter() - started, "model"


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    return values[round((len(values) - 1) * q)]


def latency_summary(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "p50": statistics.median(values) if values else None,
        "p95": _percentile(values, 0.95),
        "mean": statistics.fmean(values) if values else None,
        "total": sum(values),
    }


def fixed_state_benchmark(
    cases: list[dict[str, Any]],
    scorer: Any,
    config: ControllerConfig,
    planner: SnakePlanner,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    latencies: list[float] = []
    for case in cases:
        plan: PlannerResult = planner.evaluate(game_from_case(case))
        choice, latency, mode = controller_decision(game_from_case(case), scorer, config)
        reverse_choice, reverse_latency, reverse_mode = controller_decision(
            game_from_case(case), scorer, config, reverse_candidates=True
        )
        latencies += [latency, reverse_latency]
        rank = plan.ranks.get(choice) if choice is not None else None
        chosen_plan = plan.actions.get(choice) if choice is not None else None
        safe_path_exists = any(item.has_proven_safe_food_path for item in plan.actions.values())
        catastrophic = bool(
            safe_path_exists
            and chosen_plan is not None
            and not chosen_plan.has_proven_safe_food_path
            and chosen_plan.status != "bounded_unknown"
        )
        records.append(
            {
                "id": case["id"],
                "family": case.get("family", "unclassified"),
                "choice": choice,
                "reversed_choice": reverse_choice,
                "mode": mode,
                "reverse_mode": reverse_mode,
                "best_actions": list(plan.best_actions),
                "agreement": choice in set(plan.best_actions) if choice else False,
                "rank": rank,
                "rank_regret": rank - 1 if rank is not None else None,
                "catastrophic_miss": catastrophic,
                "order_changed": choice != reverse_choice,
                "latency_seconds": latency,
                "reverse_latency_seconds": reverse_latency,
                "planner": plan.to_dict(),
            }
        )
    regrets = [row["rank_regret"] for row in records if row["rank_regret"] is not None]
    total = len(records)
    return {
        "cases": total,
        "optimal_set_agreement": sum(row["agreement"] for row in records) / total,
        "mean_rank_regret": statistics.fmean(regrets) if regrets else None,
        "catastrophic_miss_rate": sum(row["catastrophic_miss"] for row in records) / total,
        "order_change_rate": sum(row["order_changed"] for row in records) / total,
        "invalid_choice_rate": sum(row["choice"] is None for row in records) / total,
        "latency_seconds": latency_summary(latencies),
        "records": records,
    }


def run_episode(
    scorer: Any,
    config: ControllerConfig,
    *,
    seed: int,
    width: int,
    height: int,
    max_steps: int,
    stall_steps: int,
) -> dict[str, Any]:
    game = SnakeGame(width=width, height=height, seed=seed)
    initial_length = len(game.snake)
    seen = {game.head}
    revisits = 0
    max_without_food = 0
    latencies: list[float] = []
    model_decisions = 0
    reason = "max_steps"
    while game.alive and game.steps < max_steps:
        choice, latency, mode = controller_decision(game, scorer, config)
        latencies.append(latency)
        model_decisions += int(mode == "model")
        if choice is None:
            reason = "invalid_choice"
            break
        score_before = game.score
        outcome = game.step(choice)
        reason = outcome.reason or reason
        revisits += int(game.head in seen)
        if game.score > score_before:
            seen = {game.head}
        else:
            seen.add(game.head)
        max_without_food = max(max_without_food, game.steps_since_food)
        if not outcome.alive:
            break
    possible_food = width * height - initial_length
    return {
        "seed": seed,
        "steps": game.steps,
        "food_eaten": game.score,
        "completion_ratio": game.score / possible_food,
        "board_filled": reason == "board_filled",
        "stop_reason": reason,
        "moves_per_food": game.steps / game.score if game.score else None,
        "max_steps_since_food": max_without_food,
        "revisit_step_rate": revisits / game.steps if game.steps else 0.0,
        "stall": max_without_food >= stall_steps,
        "controller_failure": reason == "invalid_choice",
        "model_decisions": model_decisions,
        "latency_seconds": latency_summary(latencies),
    }


def episode_benchmark(
    scorer: Any,
    config: ControllerConfig,
    *,
    seeds: list[int],
    width: int,
    height: int,
    max_steps: int,
    stall_steps: int,
) -> dict[str, Any]:
    rows = [
        run_episode(
            scorer,
            config,
            seed=seed,
            width=width,
            height=height,
            max_steps=max_steps,
            stall_steps=stall_steps,
        )
        for seed in seeds
    ]
    return {
        "episodes": len(rows),
        "median_food_eaten": statistics.median(row["food_eaten"] for row in rows),
        "mean_food_eaten": statistics.fmean(row["food_eaten"] for row in rows),
        "median_completion_ratio": statistics.median(row["completion_ratio"] for row in rows),
        "median_survival_steps": statistics.median(row["steps"] for row in rows),
        "board_filled_rate": sum(row["board_filled"] for row in rows) / len(rows),
        "stall_rate": sum(row["stall"] for row in rows) / len(rows),
        "mean_revisit_step_rate": statistics.fmean(row["revisit_step_rate"] for row in rows),
        "controller_failure_rate": sum(row["controller_failure"] for row in rows) / len(rows),
        "records": rows,
    }


def runtime_metrics(backend: Any) -> dict[str, Any]:
    metrics = dict(backend.runtime_metrics())
    logical = int(metrics.get("logical_input_tokens", 0))
    physical = int(metrics.get("physically_evaluated_tokens", 0))
    metrics["physical_to_logical_ratio"] = physical / logical if logical else None
    return metrics
