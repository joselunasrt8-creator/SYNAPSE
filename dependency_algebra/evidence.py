"""Canonical structural evidence artifact emission for registered analyses.

This module owns the registered-analysis evidence boundary. It deliberately does
not change the legacy dependency-algebra.artifact.v1 compiler artifact contract;
v2 evidence is an explicit successor with a separate schema and hash boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from dependency_algebra.analysis import (
    ANALYSIS_RESULT_OUTPUT_CONTRACT,
    CANONICAL_IR_INPUT_CONTRACT,
    DEPENDENCY_ANALYSIS_ID,
    AnalysisPass,
    AnalysisPassMetadata,
    DependencyAnalysisPass,
)
from dependency_algebra.analysis_registry import AnalysisRegistry, UnknownAnalysisPassError, core_analysis_registry
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import AnalysisResult, CanonicalIR
from dependency_algebra.serialization import analysis_result_hash, analysis_result_to_dict, canonical_json_bytes, sha256_bytes, sha256_digest
from dependency_algebra.version import __version__

STRUCTURAL_EVIDENCE_SCHEMA_VERSION = "dependency-algebra.structural-evidence.v2"
RESULT_VALIDATION_CONTRACT = "dependency-algebra.result-validation.v1"
IMPLEMENTATION_IDENTITY = "dependency_algebra.analysis.DependencyAnalysisPass"


class StructuralEvidenceValidationError(ValueError):
    """Raised when registered-analysis evidence cannot be emitted safely."""


def compile_structural_evidence_artifact(
    source: str | bytes,
    *,
    source_id: str = "stdin",
    max_depth: int | None = None,
    registry: AnalysisRegistry | None = None,
    analysis_id: str = DEPENDENCY_ANALYSIS_ID,
) -> dict[str, Any]:
    """Compile raw topology JSON into a v2 canonical structural evidence artifact."""

    source_text, source_bytes = _source_text_and_bytes(source)
    topology = parse_topology(source_text, source_id)
    ir_dict = validate_and_normalize(topology, source_id)
    ir = CanonicalIR.from_dict(ir_dict)
    pass_definition = (registry or core_analysis_registry()).get(analysis_id)
    if not isinstance(pass_definition, DependencyAnalysisPass):
        raise StructuralEvidenceValidationError(f"unsupported registered analysis implementation: {type(pass_definition).__name__}")
    configured_pass = pass_definition.with_configuration(max_depth=max_depth)
    result = configured_pass.execute(ir)
    return structural_evidence_artifact(
        analysis_pass=configured_pass,
        canonical_ir=ir,
        source_topology_hash=sha256_bytes(source_bytes),
        result=result,
    )


def structural_evidence_artifact(
    *,
    analysis_pass: AnalysisPass,
    canonical_ir: CanonicalIR,
    source_topology_hash: str,
    result: AnalysisResult,
    diagnostics: tuple[Mapping[str, Any], ...] = (),
) -> dict[str, Any]:
    """Validate a registered deterministic result and wrap it in the v2 evidence envelope."""

    metadata = _validate_metadata(analysis_pass.metadata)
    result_hash = analysis_result_hash(result)
    validation = validate_analysis_result(metadata, canonical_ir, result, result_hash=result_hash)
    payload = analysis_result_to_dict(result)
    artifact = {
        "artifact_schema_version": STRUCTURAL_EVIDENCE_SCHEMA_VERSION,
        "analysis": {
            "analysis_id": metadata.analysis_id,
            "analysis_version": metadata.analysis_version,
            "accepted_input": metadata.accepted_input,
            "deterministic_configuration": dict(metadata.deterministic_configuration),
            "specification_references": list(metadata.specification_references),
            "implementation_identity": IMPLEMENTATION_IDENTITY,
            "output_contract_identity": metadata.output_contract_identity,
        },
        "input": {
            "source_topology_hash": source_topology_hash,
            "normalized_ir_hash": canonical_ir.normalized_ir_hash,
        },
        "result": {
            "validation_contract": RESULT_VALIDATION_CONTRACT,
            "validation_status": validation["validation_status"],
            "result_hash": result_hash,
            "payload": payload,
        },
        "diagnostics": [dict(item) for item in sorted(diagnostics, key=lambda item: canonical_json_bytes(dict(item)))],
        "provenance": {
            "compiler_package_version": __version__,
        },
    }
    artifact["artifact_hash"] = structural_evidence_artifact_hash(artifact)
    return artifact


def validate_analysis_result(
    metadata: AnalysisPassMetadata,
    canonical_ir: CanonicalIR,
    result: AnalysisResult,
    *,
    result_hash: str | None = None,
) -> dict[str, str]:
    """Fail closed unless a result exactly matches the registered evidence contract."""

    _validate_metadata(metadata)
    if metadata.analysis_id != DEPENDENCY_ANALYSIS_ID:
        raise UnknownAnalysisPassError(f"unknown analysis id: {metadata.analysis_id}")
    if metadata.accepted_input != CANONICAL_IR_INPUT_CONTRACT:
        raise StructuralEvidenceValidationError("invalid accepted input contract")
    if metadata.output_contract_identity != ANALYSIS_RESULT_OUTPUT_CONTRACT:
        raise StructuralEvidenceValidationError("invalid output contract identity")
    if result.schema_version != "dependency-algebra.analysis.v1":
        raise StructuralEvidenceValidationError("invalid analysis result schema_version")
    if result.normalized_ir_hash != canonical_ir.normalized_ir_hash:
        raise StructuralEvidenceValidationError("result normalized_ir_hash does not match canonical input")
    if result.topology_id != canonical_ir.topology_id:
        raise StructuralEvidenceValidationError("result topology_id does not match canonical input")
    if result.reachability.normalized_ir_hash != canonical_ir.normalized_ir_hash:
        raise StructuralEvidenceValidationError("reachability normalized_ir_hash does not match canonical input")
    workload_ids = tuple(workload.id for workload in canonical_ir.workloads)
    dependency_ids = tuple(dependency.workload_id for dependency in result.dependencies)
    if dependency_ids != workload_ids:
        raise StructuralEvidenceValidationError("dependency workload ordering does not match canonical input")
    for dependency in result.dependencies:
        if dependency.normalized_ir_hash != canonical_ir.normalized_ir_hash:
            raise StructuralEvidenceValidationError("dependency normalized_ir_hash does not match canonical input")
        if dependency.dependency_result_hash and dependency.dependency_result_hash != sha256_digest({k: v for k, v in dependency.to_dict().items() if k != "dependency_result_hash"}):
            raise StructuralEvidenceValidationError("dependency result hash mismatch")
    computed_hash = analysis_result_hash(result)
    if result_hash is not None and result_hash != computed_hash:
        raise StructuralEvidenceValidationError("analysis result hash mismatch")
    return {"validation_status": "VALIDATED"}


def structural_evidence_artifact_hash(artifact: Mapping[str, Any]) -> str:
    """Hash a v2 artifact, excluding its own derived artifact_hash field."""

    return sha256_digest({key: value for key, value in artifact.items() if key != "artifact_hash"})


def _validate_metadata(metadata: AnalysisPassMetadata) -> AnalysisPassMetadata:
    if not metadata.analysis_id or not isinstance(metadata.analysis_id, str):
        raise StructuralEvidenceValidationError("analysis_id is required")
    if not metadata.analysis_version or not isinstance(metadata.analysis_version, str):
        raise StructuralEvidenceValidationError("analysis_version is required")
    if not metadata.specification_references:
        raise StructuralEvidenceValidationError("specification_references are required")
    for reference in metadata.specification_references:
        if not isinstance(reference, str) or not reference:
            raise StructuralEvidenceValidationError("specification_references must be non-empty strings")
    canonical_configuration = canonical_json_bytes(dict(metadata.deterministic_configuration))
    if canonical_configuration != canonical_json_bytes(dict(sorted(metadata.deterministic_configuration.items()))):
        raise StructuralEvidenceValidationError("deterministic_configuration must be canonical")
    return metadata


def _source_text_and_bytes(source: str | bytes) -> tuple[str, bytes]:
    if isinstance(source, bytes):
        return source.decode("utf-8"), source
    return source, source.encode("utf-8")
