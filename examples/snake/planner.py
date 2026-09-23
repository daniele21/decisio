"""Bounded dynamic-body planner used as an independent Snake benchmark oracle."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from examples.snake.game import DIRECTIONS, OPPOSITE, SnakeGame

PLANNER_VERSION = "snake_dynamic_body_planner_v1"


@dataclass(frozen=True, slots=True)
class _SearchState:
    body: tuple[tuple[int, int], ...]
    direction: str


@dataclass(frozen=True, slots=True)
class ActionPlan:
    direction: str
    status: str
    safe_food_steps: int | None
    post_food_survival_depth: int | None
    post_food_reachable_cells: int | None
    projected_survival_depth: int
    projected_reachable_cells: int
    safe_moves_after: int
    food_distance_after: int | None
    nodes_expanded: int

    @property
    def has_proven_safe_food_path(self) -> bool:
        return self.status == "proven_safe_food"

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "status": self.status,
            "safe_food_steps": self.safe_food_steps,
            "post_food_survival_depth": self.post_food_survival_depth,
            "post_food_reachable_cells": self.post_food_reachable_cells,
            "projected_survival_depth": self.projected_survival_depth,
            "projected_reachable_cells": self.projected_reachable_cells,
            "safe_moves_after": self.safe_moves_after,
            "food_distance_after": self.food_distance_after,
            "nodes_expanded": self.nodes_expanded,
        }


@dataclass(frozen=True, slots=True)
class PlannerResult:
    planner: str
    max_nodes: int
    max_depth: int
    post_food_escape_horizon: int
    projected_survival_horizon: int
    complete: bool
    best_actions: tuple[str, ...]
    ranks: dict[str, int]
    actions: dict[str, ActionPlan]

    def to_dict(self) -> dict[str, Any]:
        return {
            "planner": self.planner,
            "max_nodes": self.max_nodes,
            "max_depth": self.max_depth,
            "post_food_escape_horizon": self.post_food_escape_horizon,
            "projected_survival_horizon": self.projected_survival_horizon,
            "complete": self.complete,
            "best_actions": list(self.best_actions),
            "ranks": dict(self.ranks),
            "actions": {key: value.to_dict() for key, value in self.actions.items()},
        }


def _failure_reason(
    state: _SearchState,
    direction: str,
    *,
    width: int,
    height: int,
    food: tuple[int, int] | None,
) -> str | None:
    if direction == OPPOSITE[state.direction]:
        return "reverse_direction"
    dx, dy = DIRECTIONS[direction]
    hx, hy = state.body[0]
    new_head = (hx + dx, hy + dy)
    x, y = new_head
    if not (0 <= x < width and 0 <= y < height):
        return "wall_collision"
    ate_food = food is not None and new_head == food
    occupied = set(state.body if ate_food else state.body[:-1])
    return "body_collision" if new_head in occupied else None


def _safe_directions(
    state: _SearchState,
    *,
    width: int,
    height: int,
    food: tuple[int, int] | None,
) -> tuple[str, ...]:
    return tuple(
        direction
        for direction in DIRECTIONS
        if _failure_reason(state, direction, width=width, height=height, food=food) is None
    )


def _advance(
    state: _SearchState,
    direction: str,
    *,
    food: tuple[int, int] | None,
) -> tuple[_SearchState, bool]:
    dx, dy = DIRECTIONS[direction]
    hx, hy = state.body[0]
    new_head = (hx + dx, hy + dy)
    ate_food = food is not None and new_head == food
    body = (new_head, *state.body) if ate_food else (new_head, *state.body[:-1])
    return _SearchState(body=body, direction=direction), ate_food


def _reachable_cells(state: _SearchState, *, width: int, height: int) -> int:
    start = state.body[0]
    blocked = set(state.body[1:])
    seen = {start}
    frontier = [start]
    while frontier:
        x, y = frontier.pop()
        for dx, dy in DIRECTIONS.values():
            candidate = (x + dx, y + dy)
            cx, cy = candidate
            if not (0 <= cx < width and 0 <= cy < height):
                continue
            if candidate in blocked or candidate in seen:
                continue
            seen.add(candidate)
            frontier.append(candidate)
    return len(seen)


def _survival_depth(
    start: _SearchState,
    *,
    width: int,
    height: int,
    horizon: int,
) -> int:
    if horizon <= 0:
        return 0
    frontier = {start}
    reached = 0
    for depth in range(1, horizon + 1):
        next_frontier: set[_SearchState] = set()
        for state in frontier:
            for direction in _safe_directions(
                state, width=width, height=height, food=None
            ):
                next_state, _ = _advance(state, direction, food=None)
                next_frontier.add(next_state)
        if not next_frontier:
            break
        reached = depth
        frontier = next_frontier
    return reached


class SnakePlanner:
    """Evaluate safe first moves with bounded BFS over the moving Snake body."""

    def __init__(
        self,
        *,
        max_nodes: int = 50_000,
        max_depth: int = 96,
        post_food_escape_horizon: int = 4,
        projected_survival_horizon: int = 8,
    ) -> None:
        if max_nodes < 1 or max_depth < 1:
            raise ValueError("planner bounds must be positive")
        if post_food_escape_horizon < 1 or projected_survival_horizon < 1:
            raise ValueError("planner survival horizons must be positive")
        self.max_nodes = max_nodes
        self.max_depth = max_depth
        self.post_food_escape_horizon = post_food_escape_horizon
        self.projected_survival_horizon = projected_survival_horizon

    def _search_after_first(
        self,
        first_state: _SearchState,
        *,
        first_ate_food: bool,
        width: int,
        height: int,
        food: tuple[int, int],
    ) -> tuple[str, int | None, int | None, int | None, int]:
        board_cells = width * height
        nodes = 0
        saw_trapping_food = False

        def goal_metrics(state: _SearchState, steps: int) -> tuple[int, int] | None:
            nonlocal saw_trapping_food
            if len(state.body) == board_cells:
                return 0, 1
            survival = _survival_depth(
                state,
                width=width,
                height=height,
                horizon=self.post_food_escape_horizon,
            )
            if survival >= self.post_food_escape_horizon:
                return survival, _reachable_cells(state, width=width, height=height)
            saw_trapping_food = True
            return None

        if first_ate_food:
            metrics = goal_metrics(first_state, 1)
            if metrics is not None:
                return "proven_safe_food", 1, metrics[0], metrics[1], nodes
            return "trapping_food", None, None, None, nodes

        queue: deque[tuple[_SearchState, int]] = deque([(first_state, 1)])
        visited = {first_state}
        bounded = False
        while queue:
            state, steps = queue.popleft()
            if steps >= self.max_depth:
                bounded = True
                continue
            for direction in _safe_directions(
                state, width=width, height=height, food=food
            ):
                if nodes >= self.max_nodes:
                    bounded = True
                    queue.clear()
                    break
                next_state, ate_food = _advance(state, direction, food=food)
                nodes += 1
                next_steps = steps + 1
                if ate_food:
                    metrics = goal_metrics(next_state, next_steps)
                    if metrics is not None:
                        return (
                            "proven_safe_food",
                            next_steps,
                            metrics[0],
                            metrics[1],
                            nodes,
                        )
                    continue
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, next_steps))

        if bounded:
            return "bounded_unknown", None, None, None, nodes
        if saw_trapping_food:
            return "trapping_food", None, None, None, nodes
        return "proven_no_safe_food", None, None, None, nodes

    @staticmethod
    def _rank_key(plan: ActionPlan) -> tuple[int, int, int, int, int, int]:
        if plan.status == "proven_safe_food":
            return (
                3,
                -(plan.safe_food_steps or 10**9),
                plan.post_food_survival_depth or 0,
                plan.post_food_reachable_cells or 0,
                plan.projected_survival_depth,
                plan.projected_reachable_cells,
            )
        status_priority = 2 if plan.status == "bounded_unknown" else 1
        return (
            status_priority,
            plan.projected_survival_depth,
            plan.projected_reachable_cells,
            plan.safe_moves_after,
            -(plan.food_distance_after or 0),
            0,
        )

    def evaluate(self, game: SnakeGame) -> PlannerResult:
        if game.food is None:
            raise ValueError("planner requires an active food target")
        base = _SearchState(tuple(game.snake), game.direction)
        actions: dict[str, ActionPlan] = {}
        features = game.candidate_features(game.safe_directions())
        for direction in game.safe_directions():
            first_state, ate_food = _advance(base, direction, food=game.food)
            status, steps, post_survival, post_area, nodes = self._search_after_first(
                first_state,
                first_ate_food=ate_food,
                width=game.width,
                height=game.height,
                food=game.food,
            )
            action_features = features[direction]
            actions[direction] = ActionPlan(
                direction=direction,
                status=status,
                safe_food_steps=steps,
                post_food_survival_depth=post_survival,
                post_food_reachable_cells=post_area,
                projected_survival_depth=_survival_depth(
                    first_state,
                    width=game.width,
                    height=game.height,
                    horizon=self.projected_survival_horizon,
                ),
                projected_reachable_cells=int(action_features["reachable_free_cells_after"]),
                safe_moves_after=int(action_features["safe_moves_after"]),
                food_distance_after=action_features["food_distance_after"],
                nodes_expanded=nodes,
            )

        if not actions:
            return PlannerResult(
                planner=PLANNER_VERSION,
                max_nodes=self.max_nodes,
                max_depth=self.max_depth,
                post_food_escape_horizon=self.post_food_escape_horizon,
                projected_survival_horizon=self.projected_survival_horizon,
                complete=True,
                best_actions=(),
                ranks={},
                actions={},
            )

        keys = {direction: self._rank_key(plan) for direction, plan in actions.items()}
        ordered_keys = sorted(set(keys.values()), reverse=True)
        rank_by_key = {key: index + 1 for index, key in enumerate(ordered_keys)}
        ranks = {direction: rank_by_key[key] for direction, key in keys.items()}
        best_rank = min(ranks.values())
        best_actions = tuple(direction for direction in actions if ranks[direction] == best_rank)
        return PlannerResult(
            planner=PLANNER_VERSION,
            max_nodes=self.max_nodes,
            max_depth=self.max_depth,
            post_food_escape_horizon=self.post_food_escape_horizon,
            projected_survival_horizon=self.projected_survival_horizon,
            complete=all(plan.status != "bounded_unknown" for plan in actions.values()),
            best_actions=best_actions,
            ranks=ranks,
            actions=actions,
        )
