"""Compatibility facade for the installable SYNAPSE library surface.

This module intentionally delegates to :mod:`dependency_algebra` and does not
implement compiler logic.
"""

from dependency_algebra import (
    ARTIFACT_SCHEMA_VERSION,
    COMPILER_VERSION,
    CompilerDiagnosticException,
    __version__,
    compile,
    compile_artifact,
)

compile_topology = compile_artifact

__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "COMPILER_VERSION",
    "CompilerDiagnosticException",
    "__version__",
    "compile",
    "compile_artifact",
    "compile_topology",
]
