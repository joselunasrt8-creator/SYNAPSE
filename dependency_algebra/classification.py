"""Aggregate workload dependency predicates into structural classifications."""

from __future__ import annotations

from dependency_algebra.ir import ClassificationResult, DependencyResult


def classify_result(dependencies: tuple[DependencyResult, ...]) -> ClassificationResult:
    """Aggregate per-workload dependency predicates."""

    if all(item.dependency for item in dependencies):
        return ClassificationResult("NULL")
    if any(item.dependency for item in dependencies):
        return ClassificationResult("DEGRADED")
    return ClassificationResult("VALID")


def classify(dependencies) -> str:
    """Backward-compatible classification wrapper."""

    typed = tuple(item if isinstance(item, DependencyResult) else DependencyResult.from_dict(item) for item in dependencies)
    return classify_result(typed).classification
