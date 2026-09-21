#!/usr/bin/env python3
"""Measure representative instruction/configuration routes; never select risk gates."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

REQUIRED_ROUTES = {"docs", "bug", "contract", "ui", "integration", "release", "resume"}


def positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip() or Path(relative).is_absolute():
        raise ValueError(f"expected repository-relative path: {relative!r}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"path escapes repository: {relative}")
    return path


def report_context(root: Path, selected_route: str | None = None,
                   paths: list[str] | None = None, workstream: str | None = None,
                   template_mode: bool = False) -> dict:
    root = root.resolve()
    policy = json.loads((root / ".engineering/documentation-policy.json").read_text())
    if not isinstance(policy, dict) or policy.get("schema_version") != 2:
        raise ValueError("documentation policy schema_version must be 2; migrate explicitly")
    chars_per_token = policy.get("estimated_token_characters")
    if not positive_int(chars_per_token):
        raise ValueError("estimated_token_characters must be a positive integer")
    routes = policy.get("context_routes")
    if not isinstance(routes, dict) or not REQUIRED_ROUTES.issubset(routes):
        raise ValueError(f"context_routes must include {sorted(REQUIRED_ROUTES)}")
    targets = policy.get("context_targets")
    if not isinstance(targets, dict) or not all(positive_int(targets.get(k)) for k in (
        "bootstrap_max_estimated_tokens", "root_scoped_workstream_max_estimated_tokens"
    )):
        raise ValueError("context_targets must contain positive bootstrap and focused budgets")
    excluded = policy.get("context_exclude_directories", [])
    if not isinstance(excluded, list) or not all(isinstance(x, str) and x for x in excluded):
        raise ValueError("context_exclude_directories must be a string list")
    if selected_route is not None and selected_route not in routes:
        raise ValueError(f"unknown context route: {selected_route}")

    baseline = json.loads((root / ".engineering/baseline.json").read_text())
    profiles = baseline.get("profiles") if isinstance(baseline, dict) else None
    if not isinstance(profiles, list) or not all(isinstance(p, str) for p in profiles):
        raise ValueError("baseline profiles must be a string list")
    markers = policy.get("completed_workstream_markers", [])
    if not isinstance(markers, list) or not all(isinstance(m, str) and m for m in markers):
        raise ValueError("completed_workstream_markers must be a nonempty-string list")

    errors: list[str] = []
    cache: dict[Path, int] = {}

    def cost(path: Path) -> int:
        if path not in cache:
            if not path.is_file():
                raise ValueError(f"missing context source: {path.relative_to(root)}")
            cache[path] = math.ceil(len(path.read_text(encoding="utf-8")) / chars_per_token)
        return cache[path]

    root_guide = inside(root, "AGENTS.md")
    root_tokens = cost(root_guide)
    scoped: list[Path] = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in excluded and not (Path(directory) / d).is_symlink()]
        if "AGENTS.md" in files and Path(directory) != root:
            guide = inside(root, str((Path(directory) / "AGENTS.md").relative_to(root)))
            scoped.append(guide)

    if paths:
        affected = [inside(root, p) for p in paths]
        # Existing files and not-yet-created paths both inherit ancestor guides.
        scope = {g for g in scoped if any(p == g.parent or g.parent in p.parents for p in affected)}
        scope_mode = "selected-path-union"
    else:
        chains = [{g for g in scoped if g.parent == leaf.parent or g.parent in leaf.parent.parents}
                  for leaf in scoped]
        scope = max(chains, key=lambda c: sum(cost(p) for p in c), default=set())
        scope_mode = "largest-ancestor-chain"

    work_root = root / "docs/workstreams"
    if workstream:
        work = inside(root, workstream)
        if not work.is_relative_to(work_root) or work.suffix != ".md" or work.name == "README.md" or work.name.startswith("_"):
            raise ValueError("--workstream must name an active Markdown plan under docs/workstreams")
        cost(work)
        if any(m.lower() in work.read_text().lower() for m in markers):
            raise ValueError("selected workstream is completed, not active")
    else:
        candidates = [inside(root, str(p.relative_to(root))) for p in work_root.glob("*.md")
                      if p.name != "README.md" and not p.name.startswith("_")]
        active = [p for p in candidates if not any(m.lower() in p.read_text().lower() for m in markers)]
        work = max(active, key=cost, default=None)

    scoped_tokens = sum(cost(p) for p in scope)
    focused = root_tokens + scoped_tokens + (cost(work) if work else 0)
    if root_tokens > targets["bootstrap_max_estimated_tokens"]:
        errors.append(f"bootstrap ~{root_tokens} exceeds {targets['bootstrap_max_estimated_tokens']}")
    check_focused = selected_route is None or workstream or routes[selected_route].get("include_workstream")
    if check_focused and focused > targets["root_scoped_workstream_max_estimated_tokens"]:
        errors.append(f"root+scoped chain+active workstream ~{focused} exceeds {targets['root_scoped_workstream_max_estimated_tokens']}")

    reports = []
    skipped_routes = []
    for name, route in routes.items():
        if not isinstance(route, dict) or not positive_int(route.get("max_estimated_tokens")):
            raise ValueError(f"route {name} needs a positive budget")
        files = route.get("files")
        if not isinstance(files, list) or not files or not all(isinstance(f, str) for f in files):
            raise ValueError(f"route {name} needs a nonempty file list")
        if "AGENTS.md" not in files:
            raise ValueError(f"route {name} must include AGENTS.md")
        if not isinstance(route.get("read_when"), str) or not route["read_when"].strip():
            raise ValueError(f"route {name} needs read_when")
        for key in ("include_scoped_guides", "include_workstream"):
            if not isinstance(route.get(key), bool):
                raise ValueError(f"route {name}.{key} must be boolean")
        required_profile = route.get("requires_profile")
        if required_profile is not None and (not isinstance(required_profile, str) or not required_profile):
            raise ValueError(f"route {name}.requires_profile must be a profile name")
        if name == "ui" and required_profile != "product-ui":
            raise ValueError("route ui must require product-ui")
        if required_profile and required_profile not in profiles and not template_mode:
            if selected_route == name:
                raise ValueError(f"route {name} requires adopted profile {required_profile}")
            skipped_routes.append({"route": name, "reason": f"profile {required_profile} not adopted"})
            continue
        # Validate route paths even when only one report is requested.
        declared = {inside(root, f) for f in files}
        if selected_route is not None and name != selected_route:
            continue
        sources = declared | (scope if route["include_scoped_guides"] else set())
        if work is not None and (route["include_workstream"] or workstream):
            sources.add(work)
        detail = [{"path":str(p.relative_to(root)), "estimated_tokens":cost(p)} for p in sorted(sources)]
        total = sum(f["estimated_tokens"] for f in detail)
        budget = route["max_estimated_tokens"]
        if total > budget:
            errors.append(f"route {name} ~{total} exceeds {budget}")
        reports.append({"route":name, "read_when":route["read_when"], "files":detail,
                        "estimated_tokens":total, "budget":budget})
    return {"measurement":"characters-divided-by-policy-factor; not runtime token usage",
            "scope_mode":scope_mode, "bootstrap_estimated_tokens":root_tokens,
            "focused_guides_workstream_estimated_tokens":focused,
            "routes":reports, "skipped_routes":skipped_routes, "errors":errors, "result":"FAIL" if errors else "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true", help="Measure dormant profile routes in the source template too")
    parser.add_argument("--route", help="Report one configured reading route")
    parser.add_argument("--path", action="append", default=[], help="Affected repository-relative path; repeat for multiple owners")
    parser.add_argument("--workstream", help="Actual active plan to include instead of the largest active plan")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        report = report_context(Path(args.root), args.route, args.path, args.workstream, args.template_mode)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        report = {"result":"FAIL", "errors":[str(exc)]}
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("Agent context health (estimated instruction/configuration cost)")
        if "routes" in report:
            print(f"bootstrap: ~{report['bootstrap_estimated_tokens']} tokens; scope: {report['scope_mode']}")
            for route in report["routes"]:
                print(f"{route['route']}: ~{route['estimated_tokens']} / {route['budget']} tokens ({len(route['files'])} files)")
                if args.route:
                    for source in route["files"]:
                        print(f"  {source['path']}: ~{source['estimated_tokens']}")
        for skipped in report.get("skipped_routes", []):
            print(f"SKIP {skipped['route']}: {skipped['reason']}")
        for error in report["errors"]:
            print(f"FAIL: {error}")
        print(f"RESULT: {report['result']}")
    return int(report["result"] != "PASS")


if __name__ == "__main__":
    sys.exit(main())
