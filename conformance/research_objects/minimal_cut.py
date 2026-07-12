"""Minimal cut research object projection."""

from __future__ import annotations

from conformance.research_objects.registry import register


RESEARCH_OBJECT_ID = "analysis.separation.minimal-cut"


def project(artifact):
    dependency = artifact["dependency_lattice"][0]

    return {
        "projection": {
            "candidate_set": dependency["candidate_set"],
            "cut_set": dependency["candidate_set"],
            "separates_root_from_target": dependency["dependency"],
        },
        "canonical_outputs": {
            "minimal_cut_set": dependency["candidate_set"],
        },
        "required_diagnostics": [{
            "code": "MINIMAL_CUT_EVALUATED",
            "level": "info",
        }],
    }


register(RESEARCH_OBJECT_ID, project)
