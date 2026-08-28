#!/usr/bin/env python3
"""Deterministically validate portable Artifact Registry Object documents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "artifact-registry-object.schema.json"
ARTIFACT_ID = re.compile(r"^urn:synapse:artifact:([a-z0-9][a-z0-9._-]*):v([1-9][0-9]*)$")
VOLATILE_PARAMETER_KEYS = {"timestamp", "generated_at", "hostname", "absolute_path", "secret", "token"}


def load_document(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("document root must be an object")
    return value


def validate_document(document: dict[str, Any]) -> list[str]:
    """Return stable schema and cross-field errors for one document."""
    from jsonschema import Draft202012Validator

    schema = load_document(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = [
        f"schema:{'/'.join(map(str, error.absolute_path)) or '<root>'}:{error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: (list(item.absolute_path), item.message))
    ]
    if errors:
        return errors

    expected_id = f"urn:synapse:artifact:{document['logical_id']}:v{document['version']}"
    if document["artifact_id"] != expected_id:
        errors.append(f"identity:artifact_id must equal {expected_id}")
    for field in ("input_references", "output_references"):
        if document[field] != sorted(document[field]):
            errors.append(f"ordering:{field} must be lexically sorted")
    sources = document["provenance"]["source_references"]
    if sources != sorted(sources):
        errors.append("ordering:provenance.source_references must be lexically sorted")
    relationships = document["relationships"]
    if relationships != sorted(relationships, key=lambda edge: (edge["type"], edge["target_artifact_id"])):
        errors.append("ordering:relationships must be sorted by type then target_artifact_id")
    relationship_keys = [(edge["type"], edge["target_artifact_id"]) for edge in relationships]
    if len(relationship_keys) != len(set(relationship_keys)):
        errors.append("relationship:duplicate type and target pair")
    if any(edge["target_artifact_id"] == document["artifact_id"] for edge in relationships):
        errors.append("relationship:self-reference is forbidden")
    _check_parameters(document["provenance"]["parameters"], "provenance.parameters", errors)

    supersession = document.get("supersession")
    supersedes = [edge["target_artifact_id"] for edge in relationships if edge["type"] == "supersedes"]
    if supersession is None and supersedes:
        errors.append("supersession:supersedes relationship requires supersession metadata")
    if supersession is not None:
        previous_id = supersession["previous_artifact_id"]
        match = ARTIFACT_ID.fullmatch(previous_id)
        if not match or match.group(1) != document["logical_id"]:
            errors.append("supersession:predecessor must share logical_id")
        if supersession["previous_version"] >= document["version"]:
            errors.append("supersession:previous_version must be lower than version")
        if match and int(match.group(2)) != supersession["previous_version"]:
            errors.append("supersession:previous_artifact_id and previous_version disagree")
        if supersedes != [previous_id]:
            errors.append("supersession:exactly one matching supersedes relationship is required")
    return errors


def validate_collection(documents: list[dict[str, Any]]) -> list[str]:
    """Validate identity resolution and declared production links in a collection."""
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for document in documents:
        artifact_id = document.get("artifact_id", "<missing>")
        if artifact_id in by_id:
            errors.append(f"collection:duplicate artifact_id {artifact_id}")
        by_id[artifact_id] = document
    for artifact_id in sorted(by_id):
        document = by_id[artifact_id]
        referenced = set(document.get("input_references", [])) | set(document.get("output_references", []))
        referenced |= {edge.get("target_artifact_id") for edge in document.get("relationships", [])}
        referenced.discard(None)
        for target in sorted(referenced - set(by_id)):
            errors.append(f"collection:{artifact_id} has unresolved reference {target}")
        for output_id in document.get("output_references", []):
            target = by_id.get(output_id)
            if target is not None and artifact_id not in target.get("input_references", []):
                errors.append(f"collection:{output_id} does not declare input {artifact_id}")
    return errors


def _check_parameters(value: Any, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            if key.lower() in VOLATILE_PARAMETER_KEYS:
                errors.append(f"provenance:{location}.{key} is volatile or sensitive")
            _check_parameters(value[key], f"{location}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_parameters(item, f"{location}[{index}]", errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    paths = sorted(path for supplied in args.paths for path in ([supplied] if supplied.is_file() else supplied.glob("*.json")))
    documents: list[dict[str, Any]] = []
    report_errors: list[str] = []
    for path in paths:
        try:
            document = load_document(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            report_errors.append(f"{path}:read:{exc}")
            continue
        documents.append(document)
        report_errors.extend(f"{path}:{error}" for error in validate_document(document))
    if not report_errors:
        report_errors.extend(validate_collection(documents))
    report = {"schema_version": "synapse.artifact-contract-validation.v1", "valid": not report_errors, "documents": len(documents), "errors": report_errors}
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not report_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
