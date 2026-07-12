"""Common projection interface for research objects."""

from __future__ import annotations

from typing import Any, Dict, Protocol


Projection = Dict[str, Any]


class ProjectionHandler(Protocol):
    def __call__(self, artifact: dict) -> Projection:
        ...
