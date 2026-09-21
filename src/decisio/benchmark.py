"""JSONL benchmark runner for reproducible scorer comparisons."""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, Protocol

from .schema import ChoiceRequest


class BenchmarkResult(Protocol):
    choice: str | None
    generated_tokens: int

    def to_dict(self) -> dict[str, Any]: ...


class Scorer(Protocol):
    name: str

    def score(self, request: ChoiceRequest) -> BenchmarkResult: ...


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
    if not rows:
        raise ValueError("benchmark input is empty")
    return rows


def _input_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_benchmark(
    input_path: Path,
    output_path: Path,
    scorer: Scorer,
    *,
    reverse_candidates: bool = False,
) -> dict[str, Any]:
    rows = load_jsonl(input_path)
    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    correct = 0
    generated_tokens = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for row in rows:
        if "label" not in row:
            raise ValueError("each benchmark row requires a label")
        request = ChoiceRequest.from_dict(row)
        if reverse_candidates:
            request = ChoiceRequest(
                id=request.id,
                state=request.state,
                question=request.question,
                candidates=tuple(reversed(request.candidates)),
            )
        started = time.perf_counter()
        result = scorer.score(request)
        latency = time.perf_counter() - started
        latencies.append(latency)
        generated_tokens += result.generated_tokens
        expected = str(row["label"])
        is_correct = result.choice == expected
        correct += int(is_correct)
        results.append(
            {
                "id": request.id,
                "label": expected,
                "correct": is_correct,
                "perturbation": "reverse_candidates" if reverse_candidates else "none",
                "latency_seconds": latency,
                "result": result.to_dict(),
            }
        )

    with output_path.open("w", encoding="utf-8") as stream:
        for record in results:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "scorer": scorer.name,
        "input_sha256": _input_sha256(input_path),
        "perturbation": "reverse_candidates" if reverse_candidates else "none",
        "examples": len(results),
        "correct": correct,
        "accuracy": correct / len(results),
        "latency_seconds": {
            "median": statistics.median(latencies),
            "mean": statistics.fmean(latencies),
            "total": sum(latencies),
        },
        "generated_tokens": generated_tokens,
        "output": str(output_path),
    }
    return summary
