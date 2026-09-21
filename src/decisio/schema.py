"""Small dependency-free public data contracts for the decision laboratory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Candidate:
    id: str
    description: str

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("candidate id must be non-empty")
        if not self.description or not self.description.strip():
            raise ValueError(f"candidate {self.id!r} description must be non-empty")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Candidate:
        return cls(id=str(value["id"]), description=str(value["description"]))

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "description": self.description}


@dataclass(frozen=True, slots=True)
class ChoiceRequest:
    state: Any
    question: str
    candidates: tuple[Candidate, ...]
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.question or not self.question.strip():
            raise ValueError("question must be non-empty")
        if len(self.candidates) < 2:
            raise ValueError("choice requires at least two candidates")
        ids = [candidate.id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate ids must be unique")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ChoiceRequest:
        raw = value.get("candidates")
        if not isinstance(raw, list):
            raise ValueError("candidates must be a list")
        return cls(
            id=str(value["id"]) if value.get("id") is not None else None,
            state=value.get("state"),
            question=str(value["question"]),
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
    probability_status: str = "uncalibrated_conditional_scores"
    generated_tokens: int = 0
    prompt_sha256: dict[str, str] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.generated_tokens != 0:
            raise ValueError("native Decisio scoring must not report generated answer tokens")
        if self.choice not in self.distribution:
            raise ValueError("choice must be present in distribution")
        if set(self.distribution) != set(self.scores):
            raise ValueError("distribution and scores must cover the same candidates")
        total = sum(self.distribution.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"distribution must sum to one, got {total}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice": self.choice,
            "distribution": self.distribution,
            "scores": self.scores,
            "scorer": self.scorer,
            "probability_status": self.probability_status,
            "generated_tokens": self.generated_tokens,
            "prompt_sha256": self.prompt_sha256,
            "model": self.model,
        }
