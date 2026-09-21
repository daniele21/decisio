"""Paired scorer comparison for the Decisio scorer decision gate."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .benchmark import Scorer, run_benchmark

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


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decisio scorer comparison",
        "",
        f"- input SHA-256: `{report['input_sha256']}`",
        f"- examples: {report['examples']}",
        f"- primary scorer: `{report['primary_scorer']}`",
        "",
        "## Aggregate",
        "",
        (\n            "| scorer | normal acc | reversed acc | order changes | invalid normal | "\n            "median latency normal | generated tokens |"\n        ),
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

    lines.extend(
        [
            "",
            "## Paired correctness versus semantic v2",
            "",
            (\n                "| baseline | perturbation | accuracy delta | v2-only correct | "\n                "baseline-only correct | exact McNemar p |"\n            ),
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
            (\n                "This report is evidence, not an automatic product verdict. A stable-scorer "\n                "decision requires the pinned Qwen3.5-4B BF16/CUDA run described by the scorer-gate "\n                "methodology. Hosted CPU or smaller-model runs are integration/directional evidence "\n                "only."\n            ),
            "",
        ]
    )
    return "\n".join(lines)


def run_comparison(
    input_path: Path,
    output_dir: Path,
    scorers: dict[str, Scorer],
) -> dict[str, Any]:
    if tuple(scorers) != SCORER_KEYS:
        raise ValueError(f"scorers must be supplied in order {SCORER_KEYS!r}")
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

    report = {
        "schema_version": 1,
        "primary_scorer": PRIMARY_SCORER_KEY,
        "input_sha256": primary["input_sha256"],
        "examples": primary["examples"],
        "scorers": summaries,
        "paired_vs_primary": paired,
    }
    (output_dir / "comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "comparison.md").write_text(_render_markdown(report), encoding="utf-8")
    return report
