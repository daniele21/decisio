from __future__ import annotations

import runpy
from pathlib import Path


def test_scorer_gate_fixture_is_frozen(tmp_path: Path):
    module = runpy.run_path("benchmarks/build_scorer_gate_fixture.py")
    cases = module["CASES"]
    materialize = module["materialize"]

    assert len(cases) == 64
    assert {
        family: sum(row["family"] == family for row in cases)
        for family in module["FAMILY_ORDER"]
    } == {
        "support_routing": 16,
        "rule_application": 16,
        "evidence_entailment": 16,
        "comparative_nuance": 16,
    }

    full_path = tmp_path / "full.jsonl"
    ci_path = tmp_path / "ci.jsonl"
    assert materialize(full_path) == module["FULL_SHA256"]
    assert materialize(ci_path, ci=True) == module["CI_SHA256"]
    assert len(full_path.read_text(encoding="utf-8").splitlines()) == 64
    assert len(ci_path.read_text(encoding="utf-8").splitlines()) == 8
