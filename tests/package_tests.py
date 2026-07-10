import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASIC = ROOT / "fixtures" / "basic.json"

_SCHEMA_TESTS_SPEC = importlib.util.spec_from_file_location("schema_tests", ROOT / "tests" / "schema_tests.py")
_SCHEMA_TESTS = importlib.util.module_from_spec(_SCHEMA_TESTS_SPEC) if _SCHEMA_TESTS_SPEC else None
try:
    if _SCHEMA_TESTS_SPEC is None or _SCHEMA_TESTS_SPEC.loader is None or _SCHEMA_TESTS is None:
        raise ImportError("schema_tests spec is unavailable")
    _SCHEMA_TESTS_SPEC.loader.exec_module(_SCHEMA_TESTS)
    json_schema_validator = _SCHEMA_TESTS.json_schema_validator
    SCHEMAS = _SCHEMA_TESTS.SCHEMAS
except Exception:  # pragma: no cover - jsonschema may be unavailable
    json_schema_validator = None
    SCHEMAS = None


class InstalledPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.venv_path = Path(cls._tmp.name) / "venv"
        venv.EnvBuilder(with_pip=True).create(cls.venv_path)
        if os.name == "nt":
            cls.python = cls.venv_path / "Scripts" / "python.exe"
            cls.synapse = cls.venv_path / "Scripts" / "synapse.exe"
        else:
            cls.python = cls.venv_path / "bin" / "python"
            cls.synapse = cls.venv_path / "bin" / "synapse"
        cls.install_result = subprocess.run(
            [str(cls.python), "-m", "pip", "install", "."],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def assert_install_succeeded(self):
        output = self.install_result.stdout + self.install_result.stderr
        if self.install_result.returncode != 0 and (
            "Cannot connect to proxy" in output
            or "No matching distribution found for setuptools" in output
            or "Could not find a version that satisfies the requirement setuptools" in output
        ):
            self.skipTest("pip could not fetch isolated build dependencies in this environment")
        self.assertEqual(self.install_result.returncode, 0, output)

    def run_installed(self, *args):
        self.assert_install_succeeded()
        return subprocess.run(
            [str(self.synapse), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_pip_install_dot_succeeds_in_clean_environment(self):
        self.assert_install_succeeded()

    def test_installed_synapse_help_works(self):
        result = self.run_installed("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: synapse", result.stdout)

    def test_installed_import_surfaces_work(self):
        self.assert_install_succeeded()
        for module in ["synapse", "dependency_algebra"]:
            with self.subTest(module=module):
                result = subprocess.run(
                    [str(self.python), "-c", f"import {module}; print({module}.__version__)"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertRegex(result.stdout.strip(), r"^\d+\.\d+\.\d+")

    def test_installed_synapse_compile_is_deterministic_and_schema_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            first_output = Path(tmp) / "first.json"
            second_output = Path(tmp) / "second.json"
            first = self.run_installed("compile", "--input", str(BASIC), "--output", str(first_output))
            second = self.run_installed("compile", "--input", str(BASIC), "--output", str(second_output))
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, "")
            self.assertEqual(first.stderr, "")
            self.assertEqual(first_output.read_text(encoding="utf-8"), second_output.read_text(encoding="utf-8"))
            artifact = json.loads(first_output.read_text(encoding="utf-8"))
        self.assertEqual(artifact["artifact_schema_version"], "dependency-algebra.artifact.v1")
        self.assertIn("package_version", artifact)
        if json_schema_validator is not None:
            json_schema_validator(SCHEMAS / "artifact.schema.json").validate(artifact)


if __name__ == "__main__":
    unittest.main()
