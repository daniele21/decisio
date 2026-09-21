"""Paired scorer comparison for the Decisio scorer decision gate."""

from __future__ import annotations

import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

from .benchmark import Scorer, load_jsonl, run_benchmark
from .schema import ChoiceRequest

SCORER_KEYS = ("semantic", "semantic-independent", "letters", "generated")
PRIMARY_SCORER_KEY = "semantic"


def _load_records(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            example_id = str(record["id"])
            if example_id in records:
                raise ValueError(f"duplicate result id {example_id!r} in {path}:{line_number}")
            records[example_id] = record
    return records


def _load_requests(path: Path) -> list[ChoiceRequest]:
    return [ChoiceRequest.from_dict(row) for row in load_jsonl(path)]


def _exact_two_sided_binomial_pvalue(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    tail = min(left_only, right_only)
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def _paired_correctness(
    primary: dict[str, dict[str, Any]],
    baseline: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if set(primary) != set(baseline):
        raise ValueError("paired scorer result ids do not match")
    primary_only = 0
    baseline_only = 0
    both_correct = 0
    both_incorrect = 0
    for example_id in primary:
        left = bool(primary[example_id]["correct"])
        right = bool(baseline[example_id]["correct"])
        if left and right:
            both_correct += 1
        elif left:
            primary_only += 1
        elif right:
            baseline_only += 1
        else:
            both_incorrect += 1
    examples = len(primary)
    return {
        "examples": examples,
        "both_correct": both_correct,
        "primary_only_correct": primary_only,
        "baseline_only_correct": baseline_only,
        "both_incorrect": both_incorrect,
        "accuracy_delta": (primary_only - baseline_only) / examples,
        "exact_mcnemar_pvalue": _exact_two_sided_binomial_pvalue(
            primary_only,
            baseline_only,
        ),
    }


def _order_sensitivity(
    normal: dict[str, dict[str, Any]],
    reversed_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if set(normal) != set(reversed_records):
        raise ValueError("normal and reversed result ids do not match")
    changed = 0
    regressions = 0
    recoveries = 0
    stable_correct = 0
    stable_incorrect = 0
    for example_id in normal:
        left = normal[example_id]
        right = reversed_records[example_id]
        if left["result"].get("choice") != right["result"].get("choice"):
            changed += 1
        left_correct = bool(left["correct"])
        right_correct = bool(right["correct"])
        if left_correct and right_correct:
            stable_correct += 1
        elif left_correct and not right_correct:
            regressions += 1
        elif not left_correct and right_correct:
            recoveries += 1
        else:
            stable_incorrect += 1
    examples = len(normal)
    return {
        "examples": examples,
        "choice_changes": changed,
        "choice_change_rate": changed / examples,
        "correctness_regressions": regressions,
        "correctness_recoveries": recoveries,
        "stable_correct": stable_correct,
        "stable_incorrect": stable_incorrect,
    }


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be between zero and one")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = quantile * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _backend(scorer: Scorer) -> Any | None:
    return getattr(scorer, "backend", None)


def _synchronize(scorer: Scorer) -> None:
    method = getattr(_backend(scorer), "synchronize", None)
    if callable(method):
        method()


def _reset_peak_memory(scorer: Scorer) -> None:
    method = getattr(_backend(scorer), "reset_peak_memory", None)
    if callable(method):
        method()


def _peak_memory_bytes(scorer: Scorer) -> int | None:
    method = getattr(_backend(scorer), "peak_memory_bytes", None)
    if callable(method):
        value = method()
        return None if value is None else int(value)
    return None


def _rotate_scorer_keys(offset: int) -> tuple[str, ...]:
    amount = offset % len(SCORER_KEYS)
    return SCORER_KEYS[amount:] + SCORER_KEYS[:amount]


def _run_performance_trial(
    requests: list[ChoiceRequest],
    scorer: Scorer,
) -> dict[str, Any]:
    _synchronize(scorer)
    _reset_peak_memory(scorer)
    started = time.perf_counter()
    for request in requests:
        scorer.score(request)
    _synchronize(scorer)
    duration = time.perf_counter() - started
    return {
        "duration_seconds": duration,
        "decisions_per_second": len(requests) / duration,
        "peak_memory_bytes": _peak_memory_bytes(scorer),
    }


def _run_performance_trials(
    input_path: Path,
    scorers: dict[str, Scorer],
    *,
    warmup_rounds: int,
    measured_rounds: int,
) -> dict[str, Any]:
    if warmup_rounds < 0:
        raise ValueError("warmup_rounds must be non-negative")
    if measured_rounds < 1:
        raise ValueError("measured_rounds must be positive")

    requests = _load_requests(input_path)
    for round_index in range(warmup_rounds):
        for key in _rotate_scorer_keys(round_index):
            _run_performance_trial(requests, scorers[key])

    trials: dict[str, list[dict[str, Any]]] = {key: [] for key in SCORER_KEYS}
    execution_order: list[list[str]] = []
    for round_index in range(measured_rounds):
        order = _rotate_scorer_keys(warmup_rounds + round_index)
        execution_order.append(list(order))
        for position, key in enumerate(order):
            trial = _run_performance_trial(requests, scorers[key])
            trials[key].append(
                {
                    "round": round_index + 1,
                    "position": position + 1,
                    **trial,
                }
            )

    summaries: dict[str, Any] = {}
    for key in SCORER_KEYS:
        durations = [float(item["duration_seconds"]) for item in trials[key]]
        throughputs = [float(item["decisions_per_second"]) for item in trials[key]]
        memory = [
            int(item["peak_memory_bytes"])
            for item in trials[key]
            if item["peak_memory_bytes"] is not None
        ]
        summaries[key] = {
            "trials": trials[key],
            "duration_seconds": {
                "mean": statistics.fmean(durations),
                "p50": _percentile(durations, 0.50),
                "p95": _percentile(durations, 0.95),
                "min": min(durations),
                "max": max(durations),
            },
            "decisions_per_second": {
                "mean": statistics.fmean(throughputs),
                "p50": _percentile(throughputs, 0.50),
            },
            "peak_memory_bytes": {
                "max": max(memory),
                "p50": int(_percentile([float(value) for value in memory], 0.50)),
            }
            if memory
            else None,
        }

    backend = _backend(scorers[PRIMARY_SCORER_KEY])
    identity = getattr(backend, "identity", None)
    return {
        "enabled": True,
        "timing_scope": "full normal-order workload, in-process wall clock",
        "examples_per_trial": len(requests),
        "warmup_rounds": warmup_rounds,
        "measured_rounds": measured_rounds,
        "position_balanced": measured_rounds % len(SCORER_KEYS) == 0,
        "execution_order": execution_order,
        "backend_identity": identity if isinstance(identity, dict) else None,
        "scorers": summaries,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decisio scorer comparison",
        "",
        f"- input SHA-256: `{report['input_sha256']}`",
        f"- examples: {report['examples']}",
        f"- primary scorer: `{report['primary_scorer']}`",
        "",
        "## Quality and order robustness",
        "",
        (
            "| scorer | normal acc | reversed acc | order changes | invalid normal | "
            "single-pass median/example | generated tokens |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in SCORER_KEYS:
        item = report["scorers"][key]
        normal = item["normal"]
        reversed_summary = item["reverse_candidates"]
        order = item["order_sensitivity"]
        lines.append(
            "| "
            + " | ".join(
                [
                    key,
                    f"{normal['accuracy']:.3f}",
                    f"{reversed_summary['accuracy']:.3f}",
                    f"{order['choice_changes']}/{order['examples']}",
                    f"{normal['invalid']}/{normal['examples']}",
                    f"{normal['latency_seconds']['median']:.4f}s",
                    str(normal["generated_tokens"]),
                ]
            )
            + " |"
        )

    performance = report["performance"]
    if performance["enabled"]:
        lines.extend(
            [
                "",
                "## Repeated performance trials",
                "",
                (
                    f"Warm-up rounds: {performance['warmup_rounds']}; measured rounds: "
                    f"{performance['measured_rounds']}; scope: {performance['timing_scope']}."
                ),
                "",
                "| scorer | total p50 | total p95 | decisions/s p50 | peak memory |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for key in SCORER_KEYS:
            item = performance["scorers"][key]
            peak = item["peak_memory_bytes"]
            peak_text = f"{peak['max'] / (1024**3):.3f} GiB" if peak is not None else "n/a"
            lines.append(
                "| "
                + " | ".join(
                    [
                        key,
                        f"{item['duration_seconds']['p50']:.4f}s",
                        f"{item['duration_seconds']['p95']:.4f}s",
                        f"{item['decisions_per_second']['p50']:.3f}",
                        peak_text,
                    ]
                )
                + " |"
            )
    else:
        lines.extend(
            [
                "",
                "## Repeated performance trials",
                "",
                "Disabled for this run. Single-pass per-example timings above are diagnostic only.",
            ]
        )

    lines.extend(
        [
            "",
            "## Paired correctness versus semantic v2",
            "",
            (
                "| baseline | perturbation | accuracy delta | v2-only correct | "
                "baseline-only correct | exact McNemar p |"
            ),
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for baseline, perturbations in report["paired_vs_primary"].items():
        for perturbation in ("none", "reverse_candidates"):
            item = perturbations[perturbation]
            lines.append(
                "| "
                + " | ".join(
                    [
                        baseline,
                        perturbation,
                        f"{item['accuracy_delta']:+.3f}",
                        str(item["primary_only_correct"]),
                        str(item["baseline_only_correct"]),
                        f"{item['exact_mcnemar_pvalue']:.4f}",
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            (
                "This report is evidence, not an automatic product verdict. A stable-scorer "
                "decision requires the pinned Qwen3.5-4B BF16/CUDA run described by the "
                "scorer-gate methodology. Hosted CPU or smaller-model runs are "
                "integration/directional evidence only."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def run_comparison(
    input_path: Path,
    output_dir: Path,
    scorers: dict[str, Scorer],
    *,
    warmup_rounds: int = 0,
    performance_rounds: int = 0,
) -> dict[str, Any]:
    if tuple(scorers) != SCORER_KEYS:
        raise ValueError(f"scorers must be supplied in order {SCORER_KEYS!r}")
    if warmup_rounds < 0 or performance_rounds < 0:
        raise ValueError("performance round counts must be non-negative")
    if warmup_rounds and not performance_rounds:
        raise ValueError("warmup_rounds requires performance_rounds")
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries: dict[str, dict[str, Any]] = {}
    records: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}

    for key, scorer in scorers.items():
        normal_path = output_dir / f"{key}.jsonl"
        reverse_path = output_dir / f"{key}.reverse_candidates.jsonl"
        normal_summary = run_benchmark(input_path, normal_path, scorer)
        reverse_summary = run_benchmark(
            input_path,
            reverse_path,
            scorer,
            reverse_candidates=True,
        )
        normal_records = _load_records(normal_path)
        reverse_records = _load_records(reverse_path)
        records[(key, "none")] = normal_records
        records[(key, "reverse_candidates")] = reverse_records
        summaries[key] = {
            "normal": normal_summary,
            "reverse_candidates": reverse_summary,
            "order_sensitivity": _order_sensitivity(normal_records, reverse_records),
        }

    primary = summaries[PRIMARY_SCORER_KEY]["normal"]
    paired: dict[str, dict[str, Any]] = {}
    for baseline in SCORER_KEYS:
        if baseline == PRIMARY_SCORER_KEY:
            continue
        paired[baseline] = {
            perturbation: _paired_correctness(
                records[(PRIMARY_SCORER_KEY, perturbation)],
                records[(baseline, perturbation)],
            )
            for perturbation in ("none", "reverse_candidates")
        }

    performance = (
        _run_performance_trials(
            input_path,
            scorers,
            warmup_rounds=warmup_rounds,
            measured_rounds=performance_rounds,
        )
        if performance_rounds
        else {
            "enabled": False,
            "warmup_rounds": warmup_rounds,
            "measured_rounds": 0,
        }
    )

    report = {
        "schema_version": 2,
        "primary_scorer": PRIMARY_SCORER_KEY,
        "input_sha256": primary["input_sha256"],
        "examples": primary["examples"],
        "scorers": summaries,
        "paired_vs_primary": paired,
        "performance": performance,
    }
    (output_dir / "comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "comparison.md").write_text(_render_markdown(report), encoding="utf-8")
    return report
