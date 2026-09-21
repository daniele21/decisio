"""Regression cases for route accounting, source integrity and scoped inheritance."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("context", ROOT / "template/scripts/verify_agent_context.py")
context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context)


class ContextRoutes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "template", self.root, dirs_exist_ok=True)

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    def paths(self, result):
        return {f["path"] for f in result["routes"][0]["files"]}

    def test_route_counts_skills_and_configuration(self):
        report = context.report_context(self.root, "bug")
        self.assertIn("skills/validate-change/SKILL.md", self.paths(report))
        self.assertIn(".engineering/commands.json", self.paths(report))
        self.assertGreater(report["routes"][0]["estimated_tokens"], report["bootstrap_estimated_tokens"])

    def test_ancestor_chain_includes_nested_guides_not_unrelated_siblings(self):
        self.write("src/AGENTS.md", "a" * 100)
        self.write("src/core/AGENTS.md", "b" * 120)
        self.write("other/AGENTS.md", "c" * 40)
        report = context.report_context(self.root, "bug")
        self.assertTrue({"src/AGENTS.md", "src/core/AGENTS.md"}.issubset(self.paths(report)))
        self.assertNotIn("other/AGENTS.md", self.paths(report))

    def test_selected_changed_paths_union_both_owners_once(self):
        self.write("src/AGENTS.md", "a")
        self.write("src/core/AGENTS.md", "b")
        self.write("ui/AGENTS.md", "c")
        report = context.report_context(self.root, "bug", ["src/core/new.py", "ui/view.py"])
        self.assertTrue({"src/AGENTS.md", "src/core/AGENTS.md", "ui/AGENTS.md"}.issubset(self.paths(report)))
        self.assertEqual(len(report["routes"][0]["files"]), len(self.paths(report)))

    def test_generated_guides_are_not_bootstrap_context(self):
        self.write("node_modules/package/AGENTS.md", "a" * 100000)
        report = context.report_context(self.root, "bug")
        self.assertFalse(any("node_modules" in p for p in self.paths(report)))

    def test_missing_required_route_source_fails(self):
        (self.root / "skills/validate-change/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "missing context source"):
            context.report_context(self.root, "bug")

    def test_budget_detects_skill_growth(self):
        self.write("skills/validate-change/SKILL.md", "a" * 50000)
        report = context.report_context(self.root, "bug")
        self.assertEqual(report["result"], "FAIL")
        self.assertTrue(any("route bug" in e for e in report["errors"]))

    def test_workstream_is_explicit_and_included_once(self):
        self.write("docs/workstreams/active.md", "Status: active\nFacts and next action")
        report = context.report_context(self.root, "resume", workstream="docs/workstreams/active.md")
        self.assertIn("docs/workstreams/active.md", self.paths(report))
        self.write("docs/workstreams/active.md", "Status: complete")
        with self.assertRaisesRegex(ValueError, "completed"):
            context.report_context(self.root, "resume", workstream="docs/workstreams/active.md")

    def test_external_paths_and_symlink_sources_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            context.report_context(self.root, "bug", ["../outside"])
        (self.root / "skills/validate-change/SKILL.md").unlink()
        (self.root / "skills/validate-change/SKILL.md").symlink_to("/etc/hosts")
        with self.assertRaisesRegex(ValueError, "escapes"):
            context.report_context(self.root, "bug")

    def test_duplicate_route_files_count_once(self):
        path = self.root / ".engineering/documentation-policy.json"
        policy = json.loads(path.read_text())
        before = context.report_context(self.root, "bug")["routes"][0]["estimated_tokens"]
        policy["context_routes"]["bug"]["files"].append("AGENTS.md")
        path.write_text(json.dumps(policy))
        self.assertEqual(before, context.report_context(self.root, "bug")["routes"][0]["estimated_tokens"])

    def test_headless_project_does_not_need_design_files(self):
        shutil.rmtree(self.root / "design")
        report = context.report_context(self.root)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["skipped_routes"][0]["route"], "ui")
        with self.assertRaisesRegex(ValueError, "requires adopted profile"):
            context.report_context(self.root, "ui")

    def test_adopted_ui_profile_and_template_require_design_sources(self):
        (self.root / "design/ux-contract.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing context source"):
            context.report_context(self.root, template_mode=True)
        path = self.root / ".engineering/baseline.json"
        baseline = json.loads(path.read_text())
        baseline["profiles"] = ["product-ui"]
        path.write_text(json.dumps(baseline))
        with self.assertRaisesRegex(ValueError, "missing context source"):
            context.report_context(self.root)

    def test_focused_docs_does_not_charge_unrelated_active_workstream(self):
        self.write("docs/workstreams/large.md", "Status: active\n" + "a" * 25000)
        self.assertEqual(context.report_context(self.root, "docs")["result"], "PASS")
        self.assertEqual(context.report_context(self.root, "resume")["result"], "FAIL")

    def test_unknown_route_and_invalid_policy_are_actionable(self):
        with self.assertRaisesRegex(ValueError, "unknown context route"):
            context.report_context(self.root, "typo")
        p = self.root / ".engineering/documentation-policy.json"
        policy = json.loads(p.read_text())
        policy["estimated_token_characters"] = 0
        p.write_text(json.dumps(policy))
        with self.assertRaisesRegex(ValueError, "positive integer"):
            context.report_context(self.root)


if __name__ == "__main__":
    unittest.main()
