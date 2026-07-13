import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_traceability import DEFAULT_MANIFEST, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


class TraceabilityManifestTests(unittest.TestCase):
    def test_clean_manifest_is_valid_and_indexes_normative_sections(self):
        errors, warnings = validate_manifest(DEFAULT_MANIFEST)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(any(entry["spec_ref"].startswith("SPEC.md#7-frozen-contract-index") for entry in manifest["entries"]))

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

    def test_undocumented_public_behavior_is_reported(self):
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        behaviors = manifest["unspecified_public_behaviors"]
        self.assertGreaterEqual(len(behaviors), 1)
        self.assertTrue(all(behavior["status"] == "MISSING_SPECIFICATION" for behavior in behaviors))


if __name__ == "__main__":
    unittest.main()
