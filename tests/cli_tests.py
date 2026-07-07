import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASIC = ROOT / "fixtures" / "basic.json"
INVALID_MALFORMED = ROOT / "fixtures" / "invalid" / "malformed-json.json"
INVALID_UNKNOWN = ROOT / "fixtures" / "invalid" / "unknown-node-reference.json"
INVALID_DUPLICATE = ROOT / "fixtures" / "invalid" / "duplicate-identifiers.json"


def run_cli(*args):
    return subprocess.run(
        [str(ROOT / "synapse"), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CompilerCliIntegrationTests(unittest.TestCase):
    def test_synapse_compile_writes_artifact_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "artifact.json"
            result = run_cli("compile", "--input", str(BASIC), "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            artifact = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(artifact["artifact_schema_version"], "dependency-algebra.artifact.v1")
        self.assertEqual(artifact["source_topology_schema_version"], "dependency-algebra.topology.v1")
        self.assertEqual(artifact["classification"], "VALID")
        self.assertIn("artifact_hash", artifact)
        self.assertEqual(artifact["provenance"]["pipeline"], ["parse_topology", "validate_and_normalize", "analyze", "emit_artifact"])

    def test_malformed_json_exit_code_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cli("compile", "--input", str(INVALID_MALFORMED), "--output", str(Path(tmp) / "artifact.json"))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        self.assertEqual(diagnostic["diagnostics"][0]["code"], "PARSER.INVALID_JSON")
        self.assertEqual(result.stdout, "")

    def test_unresolved_endpoint_exit_code_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cli("compile", "--input", str(INVALID_UNKNOWN), "--output", str(Path(tmp) / "artifact.json"))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        codes = [item["code"] for item in diagnostic["diagnostics"]]
        self.assertIn("NORMALIZE.UNRESOLVED_EDGE_TO", codes)

    def test_duplicate_component_exit_code_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cli("compile", "--input", str(INVALID_DUPLICATE), "--output", str(Path(tmp) / "artifact.json"))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        codes = [item["code"] for item in diagnostic["diagnostics"]]
        self.assertIn("NORMALIZE.DUPLICATE_COMPONENT_ID", codes)

    def test_missing_input_exit_code_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cli("compile", "--input", str(Path(tmp) / "missing.json"), "--output", str(Path(tmp) / "artifact.json"))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "CLI.INPUT_NOT_FOUND")

    def test_deterministic_repeated_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            first_output = Path(tmp) / "first.json"
            second_output = Path(tmp) / "second.json"
            first = run_cli("compile", "--input", str(BASIC), "--output", str(first_output))
            second = run_cli("compile", "--input", str(BASIC), "--output", str(second_output))
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first_output.read_text(encoding="utf-8"), second_output.read_text(encoding="utf-8"))
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first.stderr, second.stderr)

    def test_artifact_emission_failure_exit_code_three_without_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "missing" / "artifact.json"
            result = run_cli("compile", "--input", str(BASIC), "--output", str(output))
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "CLI.ARTIFACT_EMISSION_FAILED")

    def test_argument_errors_are_machine_readable(self):
        result = run_cli("compile", "--input", str(BASIC))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "CLI.INVALID_ARGUMENTS")


if __name__ == "__main__":
    unittest.main()
