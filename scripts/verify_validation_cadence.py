#!/usr/bin/env python3
"""Validate feature-oriented CI cadence for adopted repositories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PLACEHOLDER = "<REPLACE_WITH_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []

    commands_path = root / ".engineering" / "commands.json"
    workflow_path = root / ".github" / "workflows" / "integration-preflight.yml"

    if not commands_path.is_file():
        errors.append("missing .engineering/commands.json")
        data = {}
    else:
        try:
            data = json.loads(commands_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid .engineering/commands.json: {exc}")
            data = {}

    cadence = data.get("ci_cadence")
    if not isinstance(cadence, dict):
        errors.append("ci_cadence must be an object")
        cadence = {}

    if cadence.get("principle") != "feature_candidate_not_commit":
        errors.append("ci_cadence.principle must be feature_candidate_not_commit")

    iteration = cadence.get("iteration")
    if not isinstance(iteration, dict):
        errors.append("ci_cadence.iteration must be an object")
        iteration = {}
    expected_iteration = {
        "draft_pull_request": True,
        "remote_full_suite": False,
        "automatic_e2e": False,
        "validation": "targeted_only",
    }
    for key, expected in expected_iteration.items():
        if iteration.get(key) != expected:
            errors.append(f"ci_cadence.iteration.{key} must be {expected!r}")

    integration = cadence.get("integration")
    if not isinstance(integration, dict):
        errors.append("ci_cadence.integration must be an object")
        integration = {}
    if integration.get("validation") != "risk_selected":
        errors.append("ci_cadence.integration.validation must be risk_selected")
    if integration.get("e2e") != "affected_only":
        errors.append("ci_cadence.integration.e2e must be affected_only")
    for key in (
        "exact_head_required",
        "cancel_superseded_runs",
        "rerun_only_missing_stale_or_affected_evidence",
    ):
        if integration.get(key) is not True:
            errors.append(f"ci_cadence.integration.{key} must be true")
    events = integration.get("trigger_events")
    required_events = {"ready_for_review", "synchronize_when_ready", "manual"}
    if not isinstance(events, list) or not required_events.issubset(set(events)):
        errors.append("ci_cadence.integration.trigger_events must include ready_for_review, synchronize_when_ready and manual")

    release = cadence.get("release")
    if not isinstance(release, dict):
        errors.append("ci_cadence.release must be an object")
        release = {}
    if release.get("validation") != "full":
        errors.append("ci_cadence.release.validation must be full")
    if release.get("e2e") != "release_critical":
        errors.append("ci_cadence.release.e2e must be release_critical")

    if cadence.get("heavy_jobs_separate_from_repository_health") is not True:
        errors.append("ci_cadence.heavy_jobs_separate_from_repository_health must be true")

    if not workflow_path.is_file():
        errors.append("missing .github/workflows/integration-preflight.yml")
    else:
        text = workflow_path.read_text(encoding="utf-8")
        for required in (
            "ready_for_review",
            "synchronize",
            "github.event.pull_request.draft == false",
            "cancel-in-progress: true",
        ):
            if required not in text:
                errors.append(f"integration-preflight workflow missing cadence guard: {required}")
        if "push:" in text:
            errors.append("integration-preflight must not run on every branch push")
        if not args.template_mode and PLACEHOLDER in text:
            errors.append("integration-preflight contains unresolved command placeholder")

    print("Validation cadence check")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
