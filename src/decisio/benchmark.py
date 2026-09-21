"""JSONL benchmark runner for reproducible scorer comparisons."""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from collections import defaultdict
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


def _family(row: dict[str, Any]) -> str:
    family = row.get("family")
    if family is None:
        metadata = row.get("metadata")
        if isinstance(metadata, dict):
            family = metadata.get("family")
    return str(family) if family is not None else "unclassified"


def _latency_summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "total": sum(values),
    }


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
    invalid = 0
    generated_tokens = 0
    family_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for row_number, row in enumerate(rows, 1):
        if "label" not in row:
            raise ValueError("each benchmark row requires a label")
        request = ChoiceRequest.from_dict(row)
        example_id = request.id or f"row-{row_number}"
        if example_id in seen_ids:
            raise ValueError(f"benchmark example ids must be unique, duplicate {example_id!r}")
        seen_ids.add(example_id)

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
        is_valid = result.choice is not None
        is_correct = result.choice == expected
        correct += int(is_correct)
        invalid += int(not is_valid)
        family = _family(row)
        record = {
            "id": example_id,
            "family": family,
            "label": expected,
            "correct": is_correct,
            "valid": is_valid,
            "perturbation": "reverse_candidates" if reverse_candidates else "none",
            "latency_seconds": latency,
            "result": result.to_dict(),
        }
        results.append(record)
        family_rows[family].append(record)

    with output_path.open("w", encoding="utf-8") as stream:
        for record in results:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    family_summary: dict[str, Any] = {}
    for family, records in sorted(family_rows.items()):
        family_latencies = [float(record["latency_seconds"]) for record in records]
        family_correct = sum(bool(record["correct"]) for record in records)
        family_invalid = sum(not bool(record["valid"]) for record in records)
        family_summary[family] = {
            "examples": len(records),
            "correct": family_correct,
            "accuracy": family_correct / len(records),
            "invalid": family_invalid,
            "invalid_rate": family_invalid / len(records),
            "latency_seconds": _latency_summary(family_latencies),
        }

    summary = {
        "scorer": scorer.name,
        "input_sha256": _input_sha256(input_path),
        "perturbation": "reverse_candidates" if reverse_candidates else "none",
        "examples": len(results),
        "correct": correct,
        "accuracy": correct / len(results),
        "invalid": invalid,
        "invalid_rate": invalid / len(results),
        "latency_seconds": _latency_summary(latencies),
        "generated_tokens": generated_tokens,
        "families": family_summary,
        "output": str(output_path),
    }
    return summary
