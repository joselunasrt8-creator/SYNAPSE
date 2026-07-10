import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dependency_algebra import CompilerDiagnosticException, compile_artifact
from dependency_algebra.serialization import canonical_json_text
from conformance.foundation_adapter import canonical_json, topology_from_fixture
from conformance.research_objects.registry import get_handler
from conformance.research_objects.reachability_profile import (
    RESEARCH_OBJECT_ID,
    ReachabilityProfileInvariantError,
    project_reachability_profile,
    verify_reachability_profile,
)

ROOT = Path(__file__).resolve().parents[1]
REACHABILITY_FIXTURE = ROOT / "conformance" / "fixtures" / "canonical-reachability-profile.fixture.json"


def load_reachability_fixture():
    return json.loads(REACHABILITY_FIXTURE.read_text(encoding="utf-8"))


def compile_fixture(fixture):
    return compile_artifact(canonical_json(topology_from_fixture(fixture)), source_id=fixture["fixture_id"])


def semantic_projection(evidence):
    return {
        "canonical_outputs": evidence["canonical_outputs"],
        "structural_metrics": evidence["structural_metrics"],
        "structural_invariants": evidence["structural_invariants"],
        "required_diagnostics": evidence["required_diagnostics"],
    }


class ReachabilityProfileConformanceTests(unittest.TestCase):
    def test_projection_is_discoverable_through_existing_registry(self):
        self.assertIs(get_handler(RESEARCH_OBJECT_ID), get_handler("concept.structural-observation.reachability-profile"))

    def test_canonical_fixture_produces_expected_reachable_and_unreachable_pairs(self):
        fixture = load_reachability_fixture()
        projection = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        self.assertEqual(projection["canonical_outputs"], fixture["expected_semantics"]["canonical_outputs"])
        self.assertEqual(len(projection["canonical_outputs"]["reachable_pairs"]), 2)
        self.assertEqual(len(projection["canonical_outputs"]["unreachable_pairs"]), 2)

    def test_root_and_target_coverage_and_density_match_fixture(self):
        fixture = load_reachability_fixture()
        projection = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        expected = fixture["expected_semantics"]["canonical_outputs"]
        self.assertEqual(projection["canonical_outputs"]["root_coverage"], expected["root_coverage"])
        self.assertEqual(projection["canonical_outputs"]["target_coverage"], expected["target_coverage"])
        self.assertEqual(projection["canonical_outputs"]["reachability_density"], 0.5)

    def test_malformed_root_or_target_references_fail_deterministically(self):
        for field, replacement in [("roots", ["missing-root"]), ("targets", ["missing-target"] )]:
            with self.subTest(field=field):
                fixture = load_reachability_fixture()
                fixture["input"]["workload"][field] = replacement
                with self.assertRaises(CompilerDiagnosticException) as raised:
                    compile_fixture(fixture)
                first = canonical_json_text(raised.exception.diagnostic)
                with self.assertRaises(CompilerDiagnosticException) as raised_again:
                    compile_fixture(fixture)
                self.assertEqual(first, canonical_json_text(raised_again.exception.diagnostic))

    def test_incomplete_pair_classification_fails_invariant_verification(self):
        fixture = load_reachability_fixture()
        profile = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        incomplete = copy.deepcopy(profile)
        incomplete["canonical_outputs"]["unreachable_pairs"].pop()
        with self.assertRaises(ReachabilityProfileInvariantError):
            verify_reachability_profile(incomplete)

    def test_noncanonical_ordering_is_normalized(self):
        fixture = load_reachability_fixture()
        shuffled = copy.deepcopy(fixture)
        shuffled["input"]["graph"]["nodes"] = list(reversed(shuffled["input"]["graph"]["nodes"]))
        shuffled["input"]["graph"]["edges"] = list(reversed(shuffled["input"]["graph"]["edges"]))
        shuffled["input"]["workload"]["roots"] = list(reversed(shuffled["input"]["workload"]["roots"]))
        shuffled["input"]["workload"]["targets"] = list(reversed(shuffled["input"]["workload"]["targets"]))
        baseline = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        normalized = get_handler(shuffled["research_object_id"])(compile_fixture(shuffled))
        self.assertEqual(normalized, baseline)

    def test_replay_produces_identical_semantic_output(self):
        fixture = load_reachability_fixture()
        first = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        second = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        self.assertEqual(first, second)
        self.assertEqual(canonical_json_text(first), canonical_json_text(second))

    def test_adapter_emits_valid_evidence_envelope_and_conformance_pass(self):
        fixture = load_reachability_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            result = subprocess.run(
                [sys.executable, "-m", "conformance.foundation_adapter", "--fixture", str(REACHABILITY_FIXTURE), "--output", str(output)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            evidence = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(evidence["repository"], "SYNAPSE")
        self.assertEqual(evidence["research_object_id"], RESEARCH_OBJECT_ID)
        self.assertEqual(evidence["semantic_result"], "PASS")
        self.assertIn("generated_artifacts", evidence)
        self.assertEqual(semantic_projection(evidence), fixture["expected_semantics"])
        verify_reachability_profile(semantic_projection(evidence))


    def test_adapter_replay_produces_identical_evidence_envelopes(self):
        with tempfile.TemporaryDirectory() as tmp:
            first_output = Path(tmp) / "evidence-first.json"
            second_output = Path(tmp) / "evidence-second.json"
            for output in [first_output, second_output]:
                result = subprocess.run(
                    [sys.executable, "-m", "conformance.foundation_adapter", "--fixture", str(REACHABILITY_FIXTURE), "--output", str(output)],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first_output.read_text(encoding="utf-8"), second_output.read_text(encoding="utf-8"))
            first = json.loads(first_output.read_text(encoding="utf-8"))
            second = json.loads(second_output.read_text(encoding="utf-8"))
        self.assertEqual(first["generated_artifacts"], second["generated_artifacts"])

    def test_existing_dependency_predicate_conformance_remains_unchanged(self):
        fixture = {
            "fixture_id": "dependency-predicate-smoke",
            "research_object_id": "definition.dependency.dependency-predicate",
            "deterministic_timestamp": "2026-01-01T00:00:00Z",
            "input": {
                "graph": {
                    "nodes": ["root", "candidate", "target"],
                    "edges": [["root", "candidate"], ["candidate", "target"]],
                },
                "workload": {
                    "roots": ["root"],
                    "targets": ["target"],
                    "candidate_component_set": ["candidate"],
                },
            },
        }
        projection = get_handler(fixture["research_object_id"])(compile_fixture(fixture))
        self.assertEqual(projection["canonical_outputs"], {"is_dependency": True})
        self.assertEqual(projection["required_diagnostics"][0]["code"], "DEPENDENCY_PREDICATE_EVALUATED")


if __name__ == "__main__":
    unittest.main()
