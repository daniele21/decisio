"""JSONL benchmark runner for reproducible scorer comparisons."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any, Protocol

from .schema import ChoiceRequest, DecisionResult


class Scorer(Protocol):
    name: str

    def score(self, request: ChoiceRequest) -> DecisionResult: ...


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


def run_benchmark(input_path: Path, output_path: Path, scorer: Scorer) -> dict[str, Any]:
    rows = load_jsonl(input_path)
    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    correct = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for row in rows:
        if "label" not in row:
            raise ValueError("each benchmark row requires a label")
        request = ChoiceRequest.from_dict(row)
        started = time.perf_counter()
        result = scorer.score(request)
        latency = time.perf_counter() - started
        latencies.append(latency)
        expected = str(row["label"])
        is_correct = result.choice == expected
        correct += int(is_correct)
        results.append(
            {
                "id": request.id,
                "label": expected,
                "correct": is_correct,
                "latency_seconds": latency,
                "result": result.to_dict(),
            }
        )

    with output_path.open("w", encoding="utf-8") as stream:
        for record in results:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "scorer": scorer.name,
        "examples": len(results),
        "correct": correct,
        "accuracy": correct / len(results),
        "latency_seconds": {
            "median": statistics.median(latencies),
            "mean": statistics.fmean(latencies),
            "total": sum(latencies),
        },
        "generated_tokens": 0,
        "output": str(output_path),
    }
    return summary
