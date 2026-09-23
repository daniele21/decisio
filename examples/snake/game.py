"""Dependency-free deterministic Snake environment for Decisio examples."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Any

DIRECTIONS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "right": (1, 0),
    "down": (0, 1),
    "left": (-1, 0),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
RECENT_HEAD_LIMIT = 12


@dataclass(frozen=True, slots=True)
class StepResult:
    alive: bool
    ate_food: bool
    reason: str | None = None


class SnakeGame:
    """Small deterministic Snake implementation with bounded decision memory."""

    def __init__(self, *, width: int = 8, height: int = 8, seed: int = 0):
        if width < 5 or height < 5:
            raise ValueError("Snake board must be at least 5x5")
        self.width = width
        self.height = height
        self._rng = random.Random(seed)
        cy = height // 2
        cx = width // 2
        self.snake: list[tuple[int, int]] = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = "right"
        self.score = 0
        self.steps = 0
        self.steps_since_food = 0
        self.alive = True
        self._recent_heads: deque[tuple[int, int]] = deque(
            [self.head],
            maxlen=RECENT_HEAD_LIMIT,
        )
        self.food: tuple[int, int] | None = self._spawn_food()

    @property
    def head(self) -> tuple[int, int]:
        return self.snake[0]

    def candidate_directions(self) -> tuple[str, ...]:
        """Return legal turn actions, excluding an immediate 180-degree reversal."""
        reverse = OPPOSITE[self.direction]
        return tuple(direction for direction in DIRECTIONS if direction != reverse)

    @staticmethod
    def _manhattan(left: tuple[int, int], right: tuple[int, int]) -> int:
        return abs(left[0] - right[0]) + abs(left[1] - right[1])

    def _failure_reason_for(
        self,
        *,
        body: list[tuple[int, int]],
        current_direction: str,
        direction: str,
        food: tuple[int, int] | None,
    ) -> str | None:
        if direction not in DIRECTIONS:
            raise ValueError(f"unknown direction {direction!r}")
        if direction == OPPOSITE[current_direction]:
            return "reverse_direction"

        dx, dy = DIRECTIONS[direction]
        hx, hy = body[0]
        new_head = (hx + dx, hy + dy)
        x, y = new_head
        if not (0 <= x < self.width and 0 <= y < self.height):
            return "wall_collision"

        ate_food = food is not None and new_head == food
        occupied = set(body if ate_food else body[:-1])
        if new_head in occupied:
            return "body_collision"
        return None

    def immediate_failure_reason(self, direction: str) -> str | None:
        """Return a deterministic immediate-failure reason without mutating the game."""
        return self._failure_reason_for(
            body=self.snake,
            current_direction=self.direction,
            direction=direction,
            food=self.food,
        )

    def safe_directions(self) -> tuple[str, ...]:
        """Return actions that cannot cause an immediate deterministic death."""
        return tuple(
            direction
            for direction in self.candidate_directions()
            if self.immediate_failure_reason(direction) is None
        )

    def action_constraints(self) -> dict[str, str | None]:
        """Expose why each direction is accepted or rejected before model scoring."""
        return {
            direction: self.immediate_failure_reason(direction)
            for direction in DIRECTIONS
        }

    def _body_after(self, direction: str) -> tuple[list[tuple[int, int]], bool]:
        if self.immediate_failure_reason(direction) is not None:
            raise ValueError(f"cannot project unsafe direction {direction!r}")
        dx, dy = DIRECTIONS[direction]
        hx, hy = self.head
        new_head = (hx + dx, hy + dy)
        ate_food = self.food is not None and new_head == self.food
        if ate_food:
            return [new_head, *self.snake], True
        return [new_head, *self.snake[:-1]], False

    def _safe_after(
        self,
        *,
        body: list[tuple[int, int]],
        current_direction: str,
        food: tuple[int, int] | None,
    ) -> tuple[str, ...]:
        reverse = OPPOSITE[current_direction]
        return tuple(
            direction
            for direction in DIRECTIONS
            if direction != reverse
            and self._failure_reason_for(
                body=body,
                current_direction=current_direction,
                direction=direction,
                food=food,
            )
            is None
        )

    def _reachable_cells(self, body: list[tuple[int, int]]) -> int:
        """Count cells reachable from the projected head with the body as static obstacles."""
        start = body[0]
        blocked = set(body[1:])
        seen = {start}
        frontier = [start]
        while frontier:
            x, y = frontier.pop()
            for dx, dy in DIRECTIONS.values():
                candidate = (x + dx, y + dy)
                cx, cy = candidate
                if not (0 <= cx < self.width and 0 <= cy < self.height):
                    continue
                if candidate in blocked or candidate in seen:
                    continue
                seen.add(candidate)
                frontier.append(candidate)
        return len(seen)

    def action_features(self, direction: str) -> dict[str, Any]:
        """Return deterministic sensors for one safe candidate action."""
        body_after, eats_food = self._body_after(direction)
        next_head = body_after[0]
        distance_before = (
            None if self.food is None else self._manhattan(self.head, self.food)
        )
        distance_after = (
            None if self.food is None else self._manhattan(next_head, self.food)
        )
        if eats_food:
            food_progress = "eats_food"
        elif distance_before is None or distance_after is None:
            food_progress = "unknown"
        elif distance_after < distance_before:
            food_progress = "closer"
        elif distance_after > distance_before:
            food_progress = "farther"
        else:
            food_progress = "same"

        projected_food = None if eats_food else self.food
        safe_after = self._safe_after(
            body=body_after,
            current_direction=direction,
            food=projected_food,
        )
        recent_visit_count = sum(
            position == next_head for position in self._recent_heads
        )
        if recent_visit_count >= 2:
            loop_risk = "high"
        elif recent_visit_count == 1:
            loop_risk = "medium"
        else:
            loop_risk = "low"

        return {
            "next_position": {"x": next_head[0], "y": next_head[1]},
            "eats_food": eats_food,
            "food_distance_before": distance_before,
            "food_distance_after": distance_after,
            "food_progress": food_progress,
            "safe_moves_after": len(safe_after),
            "safe_directions_after": list(safe_after),
            "reachable_free_cells_after": self._reachable_cells(body_after),
            "recent_visit_count": recent_visit_count,
            "loop_risk": loop_risk,
        }

    def candidate_features(
        self,
        directions: tuple[str, ...] | None = None,
    ) -> dict[str, dict[str, Any]]:
        selected = directions or self.safe_directions()
        return {
            direction: self.action_features(direction)
            for direction in selected
        }

    def _spawn_food(self) -> tuple[int, int] | None:
        free = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.snake
        ]
        return self._rng.choice(free) if free else None

    def state(self) -> dict[str, Any]:
        return {
            "board": {
                "width": self.width,
                "height": self.height,
                "coordinates": "origin=(0,0) top-left; x increases right; y increases down",
            },
            "snake": {
                "body_head_first": [{"x": x, "y": y} for x, y in self.snake],
                "current_direction": self.direction,
                "length": len(self.snake),
            },
            "food": None if self.food is None else {"x": self.food[0], "y": self.food[1]},
            "score": self.score,
            "decision_memory": {
                "steps_since_food": self.steps_since_food,
                "recent_window_size": len(self._recent_heads),
                "recent_unique_head_cells": len(set(self._recent_heads)),
            },
            "rules": [
                "A move into a wall ends the game.",
                "A move into the snake body ends the game.",
                "The snake cannot reverse directly into the opposite direction.",
                "Eating food grows the snake by one cell and increases score.",
            ],
        }

    def step(self, direction: str) -> StepResult:
        if not self.alive:
            raise RuntimeError("cannot step a finished game")
        if direction not in DIRECTIONS:
            raise ValueError(f"unknown direction {direction!r}")
        if direction == OPPOSITE[self.direction]:
            raise ValueError("direct reversal is not a legal Snake action")

        dx, dy = DIRECTIONS[direction]
        hx, hy = self.head
        new_head = (hx + dx, hy + dy)
        self.direction = direction
        self.steps += 1

        x, y = new_head
        if not (0 <= x < self.width and 0 <= y < self.height):
            self.alive = False
            return StepResult(False, False, "wall_collision")

        ate_food = self.food is not None and new_head == self.food
        occupied = set(self.snake if ate_food else self.snake[:-1])
        if new_head in occupied:
            self.alive = False
            return StepResult(False, False, "body_collision")

        self.snake.insert(0, new_head)
        if ate_food:
            self.score += 1
            self.steps_since_food = 0
            self._recent_heads.clear()
            self._recent_heads.append(new_head)
            self.food = self._spawn_food()
        else:
            self.snake.pop()
            self.steps_since_food += 1
            self._recent_heads.append(new_head)

        if self.food is None:
            self.alive = False
            return StepResult(False, ate_food, "board_filled")

        return StepResult(True, ate_food)

    def render(self) -> str:
        cells = [["." for _ in range(self.width)] for _ in range(self.height)]
        if self.food is not None:
            fx, fy = self.food
            cells[fy][fx] = "*"
        for x, y in reversed(self.snake[1:]):
            cells[y][x] = "o"
        hx, hy = self.head
        cells[hy][hx] = "O"
        return "\n".join(" ".join(row) for row in cells)
