"""Build the frozen repeated-state gate v3 fixture."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

EXPECTED_GROUPS = 8
EXPECTED_EXAMPLES = 48
EXPECTED_SHA256 = "f9e5f56128f93efb952f1fc3f4f38441150cb0c29906f688977ffa69ea61338a"
EXPECTED_FAMILY_COUNTS = {
    "support_routing": 12,
    "rule_application": 12,
    "evidence_entailment": 12,
    "comparative_nuance": 12,
}
EXPECTED_CANDIDATE_COUNTS = {2: 12, 4: 24, 8: 12}
EXPECTED_STATE_TIERS = {"short": 12, "medium": 18, "long": 18}

_COMPRESSED_SPECS = "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"


def _group_specs() -> list[dict[str, Any]]:
    raw = zlib.decompress(base64.b64decode(_COMPRESSED_SPECS)).decode("utf-8")
    value = json.loads(raw)
    if not isinstance(value, list):
        raise ValueError("repeated-state group specs must decode to a list")
    return value


def _reference_context(group_id: str, repeat: int) -> str:
    sentence = (
        f"Persistent context for {group_id}: the shared policy remains authoritative; "
        "no additional exception applies. "
    )
    return sentence * repeat


def build_fixture() -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for spec in _group_specs():
        groups.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "state_tier": spec["state_tier"],
                "candidate_count": spec["candidate_count"],
                "state": {
                    "policy": spec["policy"],
                    "reference_context": _reference_context(
                        str(spec["id"]),
                        int(spec["padding_repeat"]),
                    ),
                },
                "candidates": spec["candidates"],
                "questions": spec["questions"],
            }
        )
    return {
        "schema_version": 1,
        "gate": "repeated-state-gate-v3",
        "groups": groups,
    }


def serialize_fixture(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def validate_fixture(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ValueError("unexpected repeated-state fixture schema")
    if payload.get("gate") != "repeated-state-gate-v3":
        raise ValueError("unexpected repeated-state gate id")
    groups = payload.get("groups")
    if not isinstance(groups, list) or len(groups) != EXPECTED_GROUPS:
        raise ValueError(f"expected {EXPECTED_GROUPS} repeated-state groups")

    example_ids: set[str] = set()
    family_counts: dict[str, int] = {}
    candidate_counts: dict[int, int] = {}
    state_tier_counts: dict[str, int] = {}
    for group in groups:
        group_id = str(group["id"])
        family = str(group["family"])
        state_tier = str(group["state_tier"])
        candidates = group["candidates"]
        questions = group["questions"]
        candidate_count = int(group["candidate_count"])
        if candidate_count != len(candidates):
            raise ValueError(f"{group_id} candidate_count does not match candidates")
        if len(questions) != 6:
            raise ValueError(f"{group_id} must contain exactly six unique questions")
        candidate_ids = {str(item["id"]) for item in candidates}
        if len(candidate_ids) != candidate_count:
            raise ValueError(f"{group_id} candidate ids must be unique")

        for question in questions:
            example_id = str(question["id"])
            if example_id in example_ids:
                raise ValueError(f"duplicate repeated-state example id {example_id!r}")
            example_ids.add(example_id)
            if str(question["label"]) not in candidate_ids:
                raise ValueError(f"{example_id} label is not a candidate id")
        count = len(questions)
        family_counts[family] = family_counts.get(family, 0) + count
        candidate_counts[candidate_count] = candidate_counts.get(candidate_count, 0) + count
        state_tier_counts[state_tier] = state_tier_counts.get(state_tier, 0) + count

    if len(example_ids) != EXPECTED_EXAMPLES:
        raise ValueError(f"expected {EXPECTED_EXAMPLES} unique examples")
    if family_counts != EXPECTED_FAMILY_COUNTS:
        raise ValueError(f"unexpected family counts: {family_counts}")
    if candidate_counts != EXPECTED_CANDIDATE_COUNTS:
        raise ValueError(f"unexpected candidate-count buckets: {candidate_counts}")
    if state_tier_counts != EXPECTED_STATE_TIERS:
        raise ValueError(f"unexpected state-tier buckets: {state_tier_counts}")


def materialize(output: Path) -> str:
    payload = build_fixture()
    validate_fixture(payload)
    serialized = serialize_fixture(payload)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(
            f"repeated-state fixture hash mismatch: expected {EXPECTED_SHA256}, got {digest}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8")
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build frozen repeated-state gate v3 fixture")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    digest = materialize(args.output)
    print(json.dumps({"output": str(args.output), "sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
