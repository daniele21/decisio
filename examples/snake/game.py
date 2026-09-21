"""Dependency-free deterministic Snake environment for Decisio examples."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

DIRECTIONS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "right": (1, 0),
    "down": (0, 1),
    "left": (-1, 0),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


@dataclass(frozen=True, slots=True)
class StepResult:
    alive: bool
    ate_food: bool
    reason: str | None = None


class SnakeGame:
    """Small deterministic Snake implementation with head-first body coordinates."""

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
        self.alive = True
        self.food: tuple[int, int] | None = self._spawn_food()

    @property
    def head(self) -> tuple[int, int]:
        return self.snake[0]

    def candidate_directions(self) -> tuple[str, ...]:
        """Return standard Snake actions, excluding an immediate 180-degree reversal."""
        reverse = OPPOSITE[self.direction]
        return tuple(direction for direction in DIRECTIONS if direction != reverse)

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
            self.food = self._spawn_food()
        else:
            self.snake.pop()

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
