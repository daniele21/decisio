"""Small dependency-free public data contracts for the decision laboratory."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any


def _require_non_empty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _validate_json_state(value: Any) -> None:
    try:
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("state must be deterministic JSON-serializable data") from exc


@dataclass(frozen=True, slots=True)
class Candidate:
    id: str
    description: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.id, field_name="candidate id")
        _require_non_empty_string(self.description, field_name=f"candidate {self.id!r} description")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Candidate:
        if not isinstance(value, dict):
            raise ValueError("candidate must be an object")
        return cls(
            id=_require_non_empty_string(value.get("id"), field_name="candidate id"),
            description=_require_non_empty_string(
                value.get("description"),
                field_name="candidate description",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "description": self.description}


@dataclass(frozen=True, slots=True)
class ChoiceRequest:
    state: Any
    question: str
    candidates: tuple[Candidate, ...]
    id: str | None = None

    def __post_init__(self) -> None:
        _validate_json_state(self.state)
        _require_non_empty_string(self.question, field_name="question")
        if self.id is not None:
            _require_non_empty_string(self.id, field_name="request id")
        if len(self.candidates) < 2:
            raise ValueError("choice requires at least two candidates")
        ids = [candidate.id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate ids must be unique")
        descriptions = [candidate.description.strip() for candidate in self.candidates]
        if len(descriptions) != len(set(descriptions)):
            raise ValueError("candidate descriptions must be unique")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ChoiceRequest:
        if not isinstance(value, dict):
            raise ValueError("choice request must be an object")
        raw = value.get("candidates")
        if not isinstance(raw, list):
            raise ValueError("candidates must be a list")
        request_id = value.get("id")
        if request_id is not None:
            request_id = _require_non_empty_string(request_id, field_name="request id")
        return cls(
            id=request_id,
            state=value.get("state"),
            question=_require_non_empty_string(value.get("question"), field_name="question"),
            candidates=tuple(Candidate.from_dict(item) for item in raw),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "state": self.state,
            "question": self.question,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }
        if self.id is not None:
            data["id"] = self.id
        return data


@dataclass(frozen=True, slots=True)
class DecisionResult:
    choice: str
    distribution: dict[str, float]
    scores: dict[str, float]
    scorer: str
    binary_conditional_probability: dict[str, float] = field(default_factory=dict)
    probability_status: str = "uncalibrated_conditional_scores"
    generated_tokens: int = 0
    prompt_sha256: dict[str, str] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)
    execution_mode: str | None = None
    runtime_metrics: dict[str, int | float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty_string(self.choice, field_name="choice")
        _require_non_empty_string(self.scorer, field_name="scorer")
        _require_non_empty_string(self.probability_status, field_name="probability_status")
        if self.generated_tokens != 0:
            raise ValueError("native Decisio scoring must not report generated answer tokens")
        if self.execution_mode not in {None, "reuse", "fresh"}:
            raise ValueError("execution_mode must be reuse, fresh, or None")
        if any(
            not isinstance(key, str)
            or not key
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for key, value in self.runtime_metrics.items()
        ):
            raise ValueError("runtime_metrics must contain finite numeric values with string keys")
        if self.choice not in self.distribution:
            raise ValueError("choice must be present in distribution")
        if set(self.distribution) != set(self.scores):
            raise ValueError("distribution and scores must cover the same candidates")
        if self.binary_conditional_probability and (
            set(self.binary_conditional_probability) != set(self.scores)
        ):
            raise ValueError(
                "binary_conditional_probability and scores must cover the same candidates"
            )
        if not self.distribution:
            raise ValueError("distribution must not be empty")
        if any(
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
            for value in self.distribution.values()
        ):
            raise ValueError("distribution values must be finite values between zero and one")
        if any(
            not isinstance(value, (int, float)) or not math.isfinite(float(value))
            for value in self.scores.values()
        ):
            raise ValueError("scores must be finite numbers")
        if any(
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
            for value in self.binary_conditional_probability.values()
        ):
            raise ValueError(
                "binary_conditional_probability values must be finite values between zero and one"
            )
        total = math.fsum(float(value) for value in self.distribution.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"distribution must sum to one, got {total}")

    def to_dict(self) -> dict[str, Any]:
        data = {
            "choice": self.choice,
            "distribution": self.distribution,
            "scores": self.scores,
            "scorer": self.scorer,
            "probability_status": self.probability_status,
            "generated_tokens": self.generated_tokens,
            "prompt_sha256": self.prompt_sha256,
            "model": self.model,
        }
        if self.binary_conditional_probability:
            data["binary_conditional_probability"] = self.binary_conditional_probability
        if self.execution_mode is not None:
            data["execution_mode"] = self.execution_mode
        if self.runtime_metrics:
            data["runtime_metrics"] = self.runtime_metrics
        return data
