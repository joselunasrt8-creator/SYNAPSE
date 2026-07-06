"""Immutable structural domain objects for the compiler pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def _proxy(mapping: Mapping[str, tuple["Edge", ...]]) -> Mapping[str, tuple["Edge", ...]]:
    return MappingProxyType(dict(mapping))


@dataclass(frozen=True, slots=True)
class Edge:
    edge_id: str
    component_id: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Edge":
        return cls(edge_id=value["edge_id"], component_id=value["component_id"])

    def to_dict(self) -> dict[str, str]:
        return {"edge_id": self.edge_id, "component_id": self.component_id}


@dataclass(frozen=True, slots=True)
class Workload:
    id: str
    roots: tuple[str, ...]
    target: str
    candidate_set: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Workload":
        return cls(
            id=value["id"],
            roots=tuple(value["roots"]),
            target=value["target"],
            candidate_set=tuple(value["candidate_set"]),
        )


@dataclass(frozen=True, slots=True)
class CanonicalIR:
    topology_id: str
    normalized_ir_hash: str
    components: tuple[str, ...]
    adjacency: Mapping[str, tuple[Edge, ...]]
    workloads: tuple[Workload, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "components", tuple(self.components))
        object.__setattr__(self, "workloads", tuple(self.workloads))
        object.__setattr__(self, "adjacency", _proxy({key: tuple(value) for key, value in self.adjacency.items()}))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CanonicalIR":
        return cls(
            topology_id=value["topology_id"],
            normalized_ir_hash=value["normalized_ir_hash"],
            components=tuple(component["id"] for component in value["components"]),
            adjacency={
                key: tuple(Edge.from_dict(edge) for edge in edges)
                for key, edges in value["adjacency"].items()
            },
            workloads=tuple(Workload.from_dict(workload) for workload in value["workloads"]),
        )


@dataclass(frozen=True, slots=True)
class ProjectedIR:
    removed: frozenset[str]
    adjacency: Mapping[str, tuple[Edge, ...]]
    roots: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "removed", frozenset(self.removed))
        object.__setattr__(self, "roots", tuple(self.roots))
        object.__setattr__(self, "adjacency", _proxy({key: tuple(value) for key, value in self.adjacency.items()}))


@dataclass(frozen=True, slots=True)
class TraversalEdge:
    edge_id: str
    source: str
    target: str

    def to_dict(self) -> dict[str, str]:
        return {"edge_id": self.edge_id, "from": self.source, "to": self.target}


@dataclass(frozen=True, slots=True)
class WorkloadReachability:
    workload_id: str
    roots: tuple[str, ...]
    target: str
    reachable: bool
    reached_by: tuple[str, ...]
    visited_nodes: tuple[str, ...]
    traversal_edges: tuple[TraversalEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workload_id": self.workload_id,
            "roots": list(self.roots),
            "target": self.target,
            "reachable": self.reachable,
            "reached_by": list(self.reached_by),
            "visited_nodes": list(self.visited_nodes),
            "traversal_edges": [edge.to_dict() for edge in self.traversal_edges],
            "diagnostics": [],
        }


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    schema_version: str
    topology_id: str
    normalized_ir_hash: str
    results: tuple[WorkloadReachability, ...]
    reachability_result_hash: str | None = None

    def with_hash(self, value: str) -> "ReachabilityResult":
        return ReachabilityResult(self.schema_version, self.topology_id, self.normalized_ir_hash, self.results, value)

    def to_dict(self) -> dict[str, Any]:
        doc = {
            "schema_version": self.schema_version,
            "topology_id": self.topology_id,
            "normalized_ir_hash": self.normalized_ir_hash,
            "results": [result.to_dict() for result in self.results],
        }
        if self.reachability_result_hash is not None:
            doc["reachability_result_hash"] = self.reachability_result_hash
        return doc


@dataclass(frozen=True, slots=True)
class DependencyResult:
    schema_version: str
    workload_id: str
    normalized_ir_hash: str
    roots: tuple[str, ...]
    target: str
    candidate_set: tuple[str, ...]
    projected_ir_hash: str
    reachability_result_hash: str
    dependency: bool
    dependency_reason: str
    reachable_after_projection: tuple[str, ...]
    diagnostics: tuple[Mapping[str, Any], ...]
    dependency_result_hash: str | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DependencyResult":
        return cls(
            schema_version=value["schema_version"],
            workload_id=value["workload_id"],
            normalized_ir_hash=value["normalized_ir_hash"],
            roots=tuple(value["roots"]),
            target=value["target"],
            candidate_set=tuple(value["candidate_set"]),
            projected_ir_hash=value["projected_ir_hash"],
            reachability_result_hash=value["reachability_result_hash"],
            dependency=bool(value["dependency"]),
            dependency_reason=value["dependency_reason"],
            reachable_after_projection=tuple(value["reachable_after_projection"]),
            diagnostics=tuple(MappingProxyType(dict(item)) for item in value["diagnostics"]),
            dependency_result_hash=value.get("dependency_result_hash"),
        )

    def with_hash(self, value: str) -> "DependencyResult":
        return DependencyResult(
            self.schema_version,
            self.workload_id,
            self.normalized_ir_hash,
            self.roots,
            self.target,
            self.candidate_set,
            self.projected_ir_hash,
            self.reachability_result_hash,
            self.dependency,
            self.dependency_reason,
            self.reachable_after_projection,
            self.diagnostics,
            value,
        )

    def to_dict(self) -> dict[str, Any]:
        doc = {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "normalized_ir_hash": self.normalized_ir_hash,
            "roots": list(self.roots),
            "target": self.target,
            "candidate_set": list(self.candidate_set),
            "projected_ir_hash": self.projected_ir_hash,
            "reachability_result_hash": self.reachability_result_hash,
            "dependency": self.dependency,
            "dependency_reason": self.dependency_reason,
            "reachable_after_projection": list(self.reachable_after_projection),
            "diagnostics": [dict(item) for item in self.diagnostics],
        }
        if self.dependency_result_hash is not None:
            doc["dependency_result_hash"] = self.dependency_result_hash
        return doc


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    classification: str
