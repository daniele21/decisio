"""Summarize append-only Snake controller benchmark ledgers."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid ledger JSON at {path}:{line_number}") from exc
    if not records:
        raise ValueError("no Snake controller benchmark records found")
    return records


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    configuration_records = [
        record
        for record in records
        if record.get("configuration")
        and record.get("record_type", "configuration_result") == "configuration_result"
    ]
    for record in configuration_records:
        config = record["configuration"]
        model = record.get("model_runtime") or {}
        key = (
            str(config.get("id", "unknown")),
            str(model.get("artifact_sha256", "unknown")),
            str(record.get("fixture", {}).get("sha256", "unknown")),
            str(record.get("protocol", {}).get("sha256", "unknown")),
        )
        groups[key].append(record)

    rows: list[dict[str, Any]] = []
    for (config_id, model_sha, fixture_sha, protocol_sha), group in sorted(groups.items()):
        completed = [item for item in group if item.get("status") == "completed"]
        agreements = [
            float(item["fixed_state"]["optimal_set_agreement"])
            for item in completed
            if item.get("fixed_state")
        ]
        catastrophic = [
            float(item["fixed_state"]["catastrophic_miss_rate"])
            for item in completed
            if item.get("fixed_state")
        ]
        food = [
            float(item["episodes"]["median_food_eaten"])
            for item in completed
            if item.get("episodes")
        ]
        latency = [
            float(item["fixed_state"]["latency_seconds"]["p50"])
            for item in completed
            if item.get("fixed_state")
            and item["fixed_state"]["latency_seconds"].get("p50") is not None
        ]
        rows.append(
            {
                "configuration": config_id,
                "model_sha256": model_sha,
                "fixture_sha256": fixture_sha,
                "protocol_sha256": protocol_sha,
                "runs": len(group),
                "completed_runs": len(completed),
                "median_optimal_set_agreement": _median(agreements),
                "median_catastrophic_miss_rate": _median(catastrophic),
                "median_episode_food": _median(food),
                "median_fixed_p50_seconds": _median(latency),
                "latest_finished_at": max(str(item.get("finished_at", "")) for item in group),
            }
        )
    return {
        "schema_version": 1,
        "records": len(records),
        "run_manifests": sum(record.get("record_type") == "run_start" for record in records),
        "configuration_records": len(configuration_records),
        "groups": rows,
    }


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Snake controller benchmark history",
        "",
        (
            f"Ledger records: {summary['records']} "
            f"({summary.get('run_manifests', 0)} run manifests, "
            f"{summary.get('configuration_records', summary['records'])} configuration results)"
        ),
        "",
        "| Configuration | Runs | Agreement | Catastrophic | Median food | Fixed p50 (s) | Model SHA | Fixture SHA | Protocol SHA |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in summary["groups"]:
        def fmt(value: Any) -> str:
            return "-" if value is None else f"{float(value):.4f}"

        lines.append(
            "| {configuration} | {completed_runs}/{runs} | {agreement} | {catastrophic} | "
            "{food} | {latency} | `{model}` | `{fixture}` | `{protocol}` |".format(
                configuration=row["configuration"],
                completed_runs=row["completed_runs"],
                runs=row["runs"],
                agreement=fmt(row["median_optimal_set_agreement"]),
                catastrophic=fmt(row["median_catastrophic_miss_rate"]),
                food=fmt(row["median_episode_food"]),
                latency=fmt(row["median_fixed_p50_seconds"]),
                model=str(row["model_sha256"])[:12],
                fixture=str(row["fixture_sha256"])[:12],
                protocol=str(row["protocol_sha256"])[:12],
            )
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    summary = summarize(load_records(args.ledger))
    rendered = markdown(summary)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
