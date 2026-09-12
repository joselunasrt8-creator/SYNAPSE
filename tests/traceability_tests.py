import fnmatch
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_traceability import DEFAULT_MANIFEST, validate_manifest
from scripts.check_traceability_symbols import validate_symbols

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TEST_COMMAND = "python -m pytest tests"


class TraceabilityManifestTests(unittest.TestCase):
    def test_clean_manifest_is_valid_and_indexes_normative_sections(self):
        errors, warnings = validate_manifest(DEFAULT_MANIFEST)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(any(entry["spec_ref"].startswith("SPEC.md#7-frozen-contract-index") for entry in manifest["entries"]))

    def test_static_traceability_command_does_not_import_project_modules(self):
        probe = """
import importlib.abc
import runpy
import sys

class RejectProjectImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        root = fullname.partition('.')[0]
        if root in {'dependency_algebra', 'conformance', 'scripts', 'tests'}:
            raise RuntimeError(f'project implementation import attempted: {fullname}')
        return None

sys.meta_path.insert(0, RejectProjectImports())
sys.argv = ['scripts/check_traceability.py', '--json']
runpy.run_path('scripts/check_traceability.py', run_name='__main__')
"""
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_imported_symbol_validation_is_separately_available(self):
        self.assertEqual(validate_symbols(DEFAULT_MANIFEST), [])
        result = subprocess.run(
            [sys.executable, "scripts/check_traceability_symbols.py", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "synapse.traceability-symbol-check.v1")
        self.assertTrue(report["valid"])

    def test_every_indexed_implementation_and_test_path_exists(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        for entry in manifest["entries"]:
            with self.subTest(spec_ref=entry["spec_ref"]):
                self.assertTrue((ROOT / entry["implementation_path"]).is_file())
                self.assertTrue((ROOT / entry["test_path"]).is_file())

    def test_missing_implementation_correspondence_fails(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        broken = dict(manifest)
        broken["entries"] = [dict(entry) for entry in manifest["entries"]]
        broken["entries"][0]["implementation_path"] = "dependency_algebra/does_not_exist.py"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traceability.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            errors, _ = validate_manifest(path)
        self.assertTrue(any("implementation_path does not exist" in error for error in errors))

    def test_missing_normative_test_correspondence_fails(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        broken = dict(manifest)
        broken["entries"] = [dict(entry) for entry in manifest["entries"]]
        broken["entries"][0]["test_path"] = "tests/does_not_exist_tests.py"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traceability.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            errors, _ = validate_manifest(path)
        self.assertTrue(any("test_path does not exist" in error for error in errors))

    def test_unresolved_static_specification_anchor_fails(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        broken = dict(manifest)
        broken["entries"] = [dict(entry) for entry in manifest["entries"]]
        broken["entries"][0]["spec_ref"] = "SPEC.md#does-not-exist"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traceability.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            errors, _ = validate_manifest(path)
        self.assertTrue(any("spec_ref anchor not found" in error for error in errors))

    def test_unresolved_imported_symbol_fails_separate_validation(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        broken = dict(manifest)
        broken["entries"] = [dict(entry) for entry in manifest["entries"]]
        broken["entries"][0]["implementation_symbol"] = "does_not_exist"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traceability.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            errors = validate_symbols(path)
        self.assertTrue(any("implementation_symbol not found" in error for error in errors))

    def test_canonical_ci_suite_collects_every_test_module(self):
        pytest_ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
        pattern_line = next(
            line for line in pytest_ini.splitlines() if line.startswith("python_files = ")
        )
        patterns = pattern_line.removeprefix("python_files = ").split()
        test_modules = sorted(
            path.name
            for path in (ROOT / "tests").glob("*.py")
            if path.name != "__init__.py"
        )

        self.assertGreater(len(test_modules), 0)
        self.assertEqual(
            [
                module
                for module in test_modules
                if not any(fnmatch.fnmatchcase(module, pattern) for pattern in patterns)
            ],
            [],
        )
        self.assertIn("test_representation_invariance.py", test_modules)

        workflows = [
            ROOT / ".github" / "workflows" / "test.yml",
            ROOT / ".github" / "workflows" / "package.yml",
        ]
        for workflow in workflows:
            with self.subTest(workflow=workflow.name):
                workflow_text = workflow.read_text(encoding="utf-8")
                self.assertIn("git rev-parse HEAD", workflow_text)
                self.assertIn(CANONICAL_TEST_COMMAND, workflow_text)

    def test_ci_reports_static_and_executable_traceability_separately(self):
        workflows = [
            ROOT / ".github" / "workflows" / "test.yml",
            ROOT / ".github" / "workflows" / "package.yml",
        ]
        for workflow in workflows:
            with self.subTest(workflow=workflow.name):
                workflow_text = workflow.read_text(encoding="utf-8")
                self.assertIn("name: Check static traceability", workflow_text)
                self.assertIn("python scripts/check_traceability.py", workflow_text)
                self.assertIn("name: Check imported traceability symbols", workflow_text)
                self.assertIn("python scripts/check_traceability_symbols.py", workflow_text)

    def test_undocumented_public_behavior_is_reported(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        behaviors = manifest["unspecified_public_behaviors"]
        self.assertGreaterEqual(len(behaviors), 1)
        self.assertTrue(all(behavior["status"] == "MISSING_SPECIFICATION" for behavior in behaviors))


if __name__ == "__main__":
    unittest.main()
