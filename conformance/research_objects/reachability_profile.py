"""Reachability Profile research object projection.

The projection is implementation-owned and derives its semantic output from the
compiler reachability artifact. Foundation-owned fixture/schema documents define
which semantic result is canonical.
"""

from __future__ import annotations

from conformance.research_objects.registry import register


RESEARCH_OBJECT_ID = "concept.structural-observation.reachability-profile"

EVALUATED = "REACHABILITY_PROFILE_EVALUATED"
INVARIANTS_VERIFIED = "REACHABILITY_INVARIANTS_VERIFIED"
ORDERING_CONFIRMED = "CANONICAL_ORDERING_CONFIRMED"


class ReachabilityProfileInvariantError(ValueError):
    """Raised when a reachability profile cannot satisfy structural invariants."""


def reachability_profile_projection(artifact):
    profile = project_reachability_profile(artifact)
    return {
        "canonical_outputs": profile["canonical_outputs"],
        "structural_metrics": profile["structural_metrics"],
        "structural_invariants": profile["structural_invariants"],
        "required_diagnostics": profile["required_diagnostics"],
    }


def project_reachability_profile(artifact):
    results = sorted(
        artifact["reachability_graph"]["results"],
        key=lambda item: (item["target"], item["workload_id"]),
    )
    roots = sorted({root for result in results for root in result["roots"]})
    targets = sorted({result["target"] for result in results})
    if not roots:
        raise ReachabilityProfileInvariantError("reachability profile requires at least one root")
    if not targets:
        raise ReachabilityProfileInvariantError("reachability profile requires at least one target")

    reachable_pairs = []
    unreachable_pairs = []
    root_reachable_counts = {root: 0 for root in roots}
    target_reachable_counts = {target: 0 for target in targets}
    classified_pairs = set()

    result_by_target = {}
    for result in results:
        target = result["target"]
        if target in result_by_target:
            raise ReachabilityProfileInvariantError(f"duplicate target classification: {target}")
        result_by_target[target] = result

    for root in roots:
        for target in targets:
            result = result_by_target[target]
            reached_by = set(result["reached_by"])
            pair = {"root": root, "target": target}
            pair_key = (root, target)
            if pair_key in classified_pairs:
                raise ReachabilityProfileInvariantError(f"duplicate pair classification: {root}->{target}")
            classified_pairs.add(pair_key)
            if root in reached_by:
                reachable_pairs.append(pair)
                root_reachable_counts[root] += 1
                target_reachable_counts[target] += 1
            else:
                unreachable_pairs.append(pair)

    canonical_pair_count = len(roots) * len(targets)
    reachable_count = len(reachable_pairs)
    unreachable_count = len(unreachable_pairs)
    density = reachable_count / canonical_pair_count

    invariants = {
        "all_pairs_classified": classified_pairs == {(root, target) for root in roots for target in targets},
        "reachable_unreachable_disjoint": _pair_set(reachable_pairs).isdisjoint(_pair_set(unreachable_pairs)),
        "reachable_unreachable_union_complete": _pair_set(reachable_pairs) | _pair_set(unreachable_pairs) == classified_pairs,
        "root_coverage_counts_consistent": sum(root_reachable_counts.values()) == reachable_count,
        "target_coverage_counts_consistent": sum(target_reachable_counts.values()) == reachable_count,
        "pair_counts_consistent": reachable_count + unreachable_count == canonical_pair_count,
        "density_consistent": density == reachable_count / canonical_pair_count,
    }
    if not all(invariants.values()):
        failed = sorted(key for key, value in invariants.items() if not value)
        raise ReachabilityProfileInvariantError("reachability profile invariant failure: " + ",".join(failed))

    return {
        "canonical_outputs": {
            "reachable_pairs": reachable_pairs,
            "unreachable_pairs": unreachable_pairs,
            "root_coverage": [
                {
                    "root": root,
                    "reachable_target_count": root_reachable_counts[root],
                    "target_count": len(targets),
                }
                for root in roots
            ],
            "target_coverage": [
                {
                    "target": target,
                    "reachable_root_count": target_reachable_counts[target],
                    "root_count": len(roots),
                }
                for target in targets
            ],
            "reachability_density": density,
        },
        "structural_metrics": {
            "root_count": len(roots),
            "target_count": len(targets),
            "pair_count": canonical_pair_count,
            "reachable_pair_count": reachable_count,
            "unreachable_pair_count": unreachable_count,
        },
        "structural_invariants": invariants,
        "required_diagnostics": [
            {"code": EVALUATED, "level": "info"},
            {"code": INVARIANTS_VERIFIED, "level": "info"},
            {"code": ORDERING_CONFIRMED, "level": "info"},
        ],
    }


def verify_reachability_profile(profile):
    outputs = profile["canonical_outputs"]
    reachable_pairs = outputs["reachable_pairs"]
    unreachable_pairs = outputs["unreachable_pairs"]
    roots = sorted({item["root"] for item in outputs["root_coverage"]})
    targets = sorted({item["target"] for item in outputs["target_coverage"]})
    expected_pairs = {(root, target) for root in roots for target in targets}
    reachable = _pair_set(reachable_pairs)
    unreachable = _pair_set(unreachable_pairs)
    reachable_count = len(reachable_pairs)
    pair_count = len(expected_pairs)
    invariants = profile["structural_invariants"]

    checks = {
        "all_pairs_classified": reachable | unreachable == expected_pairs,
        "reachable_unreachable_disjoint": reachable.isdisjoint(unreachable),
        "reachable_unreachable_union_complete": reachable | unreachable == expected_pairs,
        "root_coverage_counts_consistent": all(
            item["reachable_target_count"] == sum(1 for pair in reachable_pairs if pair["root"] == item["root"])
            and item["target_count"] == len(targets)
            for item in outputs["root_coverage"]
        ),
        "target_coverage_counts_consistent": all(
            item["reachable_root_count"] == sum(1 for pair in reachable_pairs if pair["target"] == item["target"])
            and item["root_count"] == len(roots)
            for item in outputs["target_coverage"]
        ),
        "pair_counts_consistent": len(reachable_pairs) + len(unreachable_pairs) == pair_count,
        "density_consistent": outputs["reachability_density"] == reachable_count / pair_count,
    }
    checks.update({key: checks[key] and invariants.get(key) is True for key in checks})
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise ReachabilityProfileInvariantError("reachability profile invariant failure: " + ",".join(failed))
    return True


def _pair_set(pairs):
    return {(pair["root"], pair["target"]) for pair in pairs}


register(RESEARCH_OBJECT_ID, reachability_profile_projection)
