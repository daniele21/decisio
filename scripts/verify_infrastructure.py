#!/usr/bin/env python3
"""Validate repository infrastructure-as-code policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

MANAGED_MECHANISMS = {"terraform", "opentofu", "cdk", "cloudformation", "pulumi", "other"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    return parser.parse_args()


def expect_true(section: dict, key: str, errors: list[str], prefix: str) -> None:
    if section.get(key) is not True:
        errors.append(f"{prefix}.{key} must be true")


def expect_false(section: dict, key: str, errors: list[str], prefix: str) -> None:
    if section.get(key) is not False:
        errors.append(f"{prefix}.{key} must be false")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    path = root / ".engineering" / "infrastructure.json"
    errors: list[str] = []

    if not path.is_file():
        print("Infrastructure as code check")
        print("FAIL: missing .engineering/infrastructure.json")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print("Infrastructure as code check")
        print(f"FAIL: invalid .engineering/infrastructure.json: {exc}")
        return 1

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("contract_version") != "0.1.0":
        errors.append("contract_version must be 0.1.0")
    if data.get("default_for_new_cloud_projects_without_existing_iac") != "terraform":
        errors.append("default_for_new_cloud_projects_without_existing_iac must be terraform")
    expect_true(data, "preserve_existing_iac_when_fit", errors, "infrastructure")
    if data.get("manual_shared_infrastructure") != "exception_only":
        errors.append("manual_shared_infrastructure must be exception_only")
    expect_true(data, "drift_reconciled_to_code", errors, "infrastructure")

    status = data.get("status")
    if status not in {"n/a", "managed"}:
        errors.append("status must be n/a or managed")

    baseline_path = root / ".engineering" / "baseline.json"
    profiles: set[str] = set()
    if baseline_path.is_file():
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            profiles = set(baseline.get("profiles") or [])
        except (json.JSONDecodeError, OSError):
            pass
    if "aws-cloud" in profiles and status != "managed":
        errors.append("aws-cloud profile requires infrastructure.status=managed")

    if status == "managed":
        mechanism = data.get("mechanism")
        if mechanism not in MANAGED_MECHANISMS:
            errors.append(f"managed mechanism must be one of {sorted(MANAGED_MECHANISMS)}")
        root_value = data.get("root")
        if not isinstance(root_value, str) or not root_value.strip() or root_value == "n/a":
            errors.append("managed infrastructure requires a repository root path")

    environment = data.get("environment_policy")
    if not isinstance(environment, dict):
        errors.append("environment_policy must be an object")
        environment = {}
    expect_true(environment, "explicit_target_required", errors, "environment_policy")
    expect_true(environment, "production_implicit_default_forbidden", errors, "environment_policy")
    expect_false(environment, "feature_branch_production_apply", errors, "environment_policy")
    if environment.get("production_apply_stage") != "release":
        errors.append("environment_policy.production_apply_stage must be release")

    plan = data.get("plan_apply_policy")
    if not isinstance(plan, dict):
        errors.append("plan_apply_policy must be an object")
        plan = {}
    for key in ("plan_before_apply", "review_destructive_changes", "review_policy_network_data_cost_risk", "post_apply_verification"):
        expect_true(plan, key, errors, "plan_apply_policy")

    state = data.get("state")
    if not isinstance(state, dict):
        errors.append("state must be an object")
        state = {}
    for key in ("shared_environment_remote_state", "environment_isolation", "locking_or_concurrency_guard", "state_is_sensitive"):
        expect_true(state, key, errors, "state")
    expect_false(state, "state_files_committed", errors, "state")

    secrets = data.get("secrets")
    if not isinstance(secrets, dict):
        errors.append("secrets must be an object")
        secrets = {}
    expect_true(secrets, "secret_values_in_source_forbidden", errors, "secrets")
    expect_true(secrets, "secret_resources_and_references_in_iac_allowed", errors, "secrets")

    terraform = data.get("terraform_defaults")
    if not isinstance(terraform, dict):
        errors.append("terraform_defaults must be an object")
        terraform = {}
    for key in (
        "preferred_for_new_cloud_projects_without_existing_iac",
        "provider_lock_file_committed",
        "remote_state_for_shared_environments",
        "state_locking_or_equivalent",
    ):
        expect_true(terraform, key, errors, "terraform_defaults")
    for key in ("generated_directory_committed", "plan_files_committed"):
        expect_false(terraform, key, errors, "terraform_defaults")

    if status == "managed" and data.get("mechanism") == "terraform":
        gitignore = root / ".gitignore"
        if not gitignore.is_file():
            errors.append("Terraform-managed repository requires .gitignore")
        else:
            text = gitignore.read_text(encoding="utf-8")
            for marker in (".terraform/", "*.tfstate", "*.tfplan"):
                if marker not in text:
                    errors.append(f"Terraform-managed repository .gitignore missing {marker}")

    print("Infrastructure as code check")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
