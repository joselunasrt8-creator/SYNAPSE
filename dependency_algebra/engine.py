"""Analysis orchestration for normalized Dependency Algebra IR."""

from __future__ import annotations

from typing import Any

from dependency_algebra.classification import classify_result
from dependency_algebra.ir import CanonicalIR
from dependency_algebra.predicate import evaluate as evaluate_dependency
from dependency_algebra.reachability import evaluate as evaluate_reachability
from dependency_algebra.serialization import sha256_digest


def analyze(ir: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    """Analyze normalized IR and return deterministic dependency results."""

    canonical_ir = CanonicalIR.from_dict(ir)
    reachability_result = evaluate_reachability(canonical_ir, max_depth=max_depth)
    dependencies = tuple(
        evaluate_dependency(canonical_ir, workload, max_depth=max_depth)
        for workload in canonical_ir.workloads
    )
    classification = classify_result(dependencies)
    result = {
        "schema_version": "dependency-algebra.analysis.v1",
        "topology_id": canonical_ir.topology_id,
        "normalized_ir_hash": canonical_ir.normalized_ir_hash,
        "classification": classification.classification,
        "reachability": reachability_result.to_dict(),
        "dependencies": [dependency.to_dict() for dependency in dependencies],
    }
    result["dependency_result_hash"] = sha256_digest(result)
    return result
