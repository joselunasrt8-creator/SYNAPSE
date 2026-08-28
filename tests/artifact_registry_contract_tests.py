import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

if importlib.util.find_spec("jsonschema") is None:
    Draft202012Validator = None
else:
    from jsonschema import Draft202012Validator
    from scripts.validate_artifact_contract import load_document, validate_collection, validate_document

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "artifact_registry"
SCHEMA = ROOT / "schemas" / "artifact-registry-object.schema.json"


@unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
class ArtifactRegistryObjectContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_document(SCHEMA)
        cls.validator = Draft202012Validator(cls.schema)
        cls.valid_paths = sorted((FIXTURES / "valid").glob("*.json"))

    def test_schema_is_valid_draft_2020_12(self):
        Draft202012Validator.check_schema(self.schema)

    def test_end_to_end_fixtures_are_schema_and_semantically_valid(self):
        self.assertEqual(len(self.valid_paths), 8)
        documents = []
        for path in self.valid_paths:
            with self.subTest(path=path):
                document = load_document(path)
                self.validator.validate(document)
                self.assertEqual(validate_document(document), [])
                documents.append(document)
        self.assertEqual(validate_collection(documents), [])

    def test_compressed_chain_has_required_types_in_order(self):
        self.assertEqual(
            [load_document(path)["logical_id"] for path in self.valid_paths if "analysis1" not in path.name and "production-receipt" not in path.name],
            ["repository-snapshot", "observation", "evidence-record", "model-object", "analysis-result", "decision-reference"],
        )

    def test_all_relationship_semantics_are_exercised(self):
        relationship_types = {
            edge["type"]
            for path in self.valid_paths
            for edge in load_document(path)["relationships"]
        }
        self.assertEqual(
            relationship_types,
            {"produced_by", "derived_from", "supports", "contradicts", "supersedes", "implements", "validated_by", "authorized_by", "executed_as"},
        )

    def test_schema_invalid_fixtures_fail_for_the_intended_boundary(self):
        for name in ("inherited-legitimacy.json", "authorization-execution-conflation.json"):
            with self.subTest(name=name):
                errors = list(self.validator.iter_errors(load_document(FIXTURES / "invalid" / name)))
                self.assertTrue(errors)

    def test_semantic_invalid_fixtures_fail_deterministically(self):
        expected = {
            "identity-mismatch.json": ["identity:artifact_id must equal urn:synapse:artifact:repository-snapshot:v1"],
            "cross-logical-supersession.json": [
                "supersession:predecessor must share logical_id",
            ],
        }
        for name, errors in expected.items():
            with self.subTest(name=name):
                document = load_document(FIXTURES / "invalid" / name)
                self.validator.validate(document)
                self.assertEqual(validate_document(document), errors)

    def test_existence_validity_authority_and_execution_are_independent(self):
        artifact = load_document(self.valid_paths[0])
        self.assertEqual(artifact["validity"]["state"], "unassessed")
        mutated = copy.deepcopy(artifact)
        mutated["relationships"] = [{"type": "supports", "target_artifact_id": artifact["artifact_id"], "basis": "self", "legitimacy_inherited": False}]
        self.assertIn("relationship:self-reference is forbidden", validate_document(mutated))
        self.assertNotIn("authorized_by", {edge["type"] for edge in artifact["relationships"]})
        self.assertNotIn("executed_as", {edge["type"] for edge in artifact["relationships"]})

    def test_cli_validation_is_deterministic(self):
        command = [sys.executable, "scripts/validate_artifact_contract.py", "fixtures/artifact_registry/valid"]
        first = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        second = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(json.loads(first.stdout), {"schema_version": "synapse.artifact-contract-validation.v1", "valid": True, "documents": 8, "errors": []})
