"""Research object projection registry."""

from __future__ import annotations

from conformance.research_objects.dependency_predicate import (
    dependency_projection,
)

HANDLERS = {
    "definition.dependency.dependency-predicate": dependency_projection,
}
