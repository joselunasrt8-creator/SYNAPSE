# Compiler Frontend Contract

## Purpose

This document closes the planning gaps that must be resolved before any parser or normalizer implementation begins. It defines contracts only: parser diagnostic taxonomy, AST construction rules, normalization design rules, machine-readable diagnostics, and conformance vectors for frontend failures.

No parser, AST builder, IR normalizer, reachability engine, complement projection engine, dependency predicate evaluator, artifact emitter, CLI, library API, GitHub Action consumer, runtime surface, authority surface, proof surface, governance surface, policy surface, execution surface, or external-state mutation surface is introduced by this contract.

## Frontend phases

The compiler frontend is specified as three future phases:

1. **Parse**: convert source bytes into a JSON value or emit deterministic parse diagnostics.
2. **AST construction**: convert a validated topology JSON value into a source-faithful AST or emit deterministic AST diagnostics.
3. **Normalization**: convert AST into canonical IR or emit deterministic normalization diagnostics.

Each phase has an exact input and output boundary. A failed phase stops the pipeline; later phases MUST NOT run on failed input.

## Parser error taxonomy

Future parser diagnostics MUST use stable diagnostic codes. Codes are strings and sort lexicographically.

| Code | Phase | Meaning |
| --- | --- | --- |
| `PARSER.INVALID_JSON` | parse | Source bytes are not valid JSON. |
| `PARSER.NON_OBJECT_DOCUMENT` | parse | The top-level JSON value is not an object. |
| `PARSER.UNSUPPORTED_ENCODING` | parse | Source bytes are not valid UTF-8. |
| `PARSER.EMPTY_INPUT` | parse | Source bytes are empty or contain no JSON token. |

Parser diagnostics MUST NOT classify input as `NULL`. They reject the source before AST construction.

## AST construction rules from topology JSON

AST construction is a future pure transformation from validated topology JSON shape into `dependency-algebra.ast.v1`.

Rules:

1. Copy `topology_id` exactly.
2. Convert topology `schema_version` to AST `schema_version` with value `dependency-algebra.ast.v1`.
3. Preserve each source-declared component identifier exactly.
4. Preserve each source-declared edge identifier and directed `from → to` endpoints exactly.
5. Preserve each source-declared workload identifier, roots, target, candidate set, and expected structural classification exactly.
6. Convert topology component `labels` to AST component `metadata` when present.
7. Convert topology edge `labels` to AST edge `metadata` when present.
8. Preserve source array order for diagnostics through `source_location.source_order` when source order is retained.
9. Retain only stable source identity in `source.source_id`; local file paths are not part of the AST contract.
10. Do not compute reachability, dependency results, complement projections, artifacts, or normalized adjacency.

AST construction diagnostics MUST use these stable codes:

| Code | Phase | Meaning |
| --- | --- | --- |
| `AST.SCHEMA_VERSION_UNSUPPORTED` | ast_construction | Topology schema version is missing or unsupported. |
| `AST.SCHEMA_SHAPE_INVALID` | ast_construction | Topology JSON fails the topology schema shape. |
| `AST.IDENTIFIER_INVALID` | ast_construction | A declared identifier is malformed. |
| `AST.CLASSIFICATION_INVALID` | ast_construction | A workload expected classification is not structural `VALID`, `DEGRADED`, or `NULL`. |

## Normalizer design contract

Normalization is a future pure transformation from AST to canonical IR.

Rules:

1. Reject duplicate component identifiers.
2. Reject duplicate edge identifiers.
3. Reject duplicate workload identifiers.
4. Reject unresolved edge endpoints.
5. Reject unresolved workload roots.
6. Reject unresolved workload targets.
7. Reject unresolved candidate components.
8. Reject empty candidate sets in v1.
9. Deduplicate duplicate roots after reference validation.
10. Deduplicate duplicate candidates after reference validation.
11. Sort components, edges, workloads, roots, candidates, and adjacency entries according to `AST_IR_CONTRACT.md`.
12. Preserve self-loops and parallel edges with distinct edge identifiers.
13. Preserve cycles without traversal-derived summaries.
14. Preserve disconnected and isolated components.
15. Produce no partial IR on failure.

Normalization diagnostics MUST use these stable codes:

| Code | Phase | Meaning |
| --- | --- | --- |
| `NORMALIZE.DUPLICATE_COMPONENT_ID` | normalization | More than one component declares the same identifier. |
| `NORMALIZE.DUPLICATE_EDGE_ID` | normalization | More than one edge declares the same identifier. |
| `NORMALIZE.DUPLICATE_WORKLOAD_ID` | normalization | More than one workload declares the same identifier. |
| `NORMALIZE.UNRESOLVED_EDGE_FROM` | normalization | An edge source endpoint does not resolve to a component. |
| `NORMALIZE.UNRESOLVED_EDGE_TO` | normalization | An edge target endpoint does not resolve to a component. |
| `NORMALIZE.UNRESOLVED_WORKLOAD_ROOT` | normalization | A workload root does not resolve to a component. |
| `NORMALIZE.UNRESOLVED_WORKLOAD_TARGET` | normalization | A workload target does not resolve to a component. |
| `NORMALIZE.UNRESOLVED_CANDIDATE` | normalization | A candidate component does not resolve to a component. |
| `NORMALIZE.EMPTY_CANDIDATE_SET` | normalization | A workload candidate set is empty in v1. |

## Diagnostic ordering

Diagnostics are ordered deterministically by:

1. `code` lexicographically.
2. `subject.kind` lexicographically.
3. `subject.id` lexicographically.
4. `source.source_id` lexicographically.
5. `source.source_order` numerically, with missing values sorted last.

Diagnostic ordering does not depend on wall-clock time, environment variables, absolute paths, filesystem layout, map iteration order, or host locale.

## Diagnostic schema boundary

`schemas/diagnostic.schema.json` defines a machine-readable diagnostic envelope for parser, AST construction, and normalization failures.

Diagnostics MAY include stable source identity and source order. Diagnostics MUST NOT include:

- Absolute machine paths.
- Wall-clock timestamps.
- Random identifiers.
- Environment-derived fields.
- Runtime authorization claims.
- Authority propagation fields.
- Proof claims.
- Governance outcomes.
- Runtime policy decisions.
- Execution eligibility decisions.
- External mutation results.

Diagnostics are not part of normalized IR v1 and are excluded from `normalized_ir_hash`.

## Conformance vectors

Frontend failure fixtures live under `fixtures/diagnostics/` and are diagnostics-only fixtures. They are not parser or normalizer outputs produced by implementation code.

Required vectors:

- Malformed JSON parse failure.
- Unsupported topology schema version.
- Duplicate component identifier normalization failure.
- Duplicate workload identifier normalization failure.
- Unresolved edge endpoint normalization failure.
- Unresolved workload root normalization failure.
- Empty candidate set normalization failure.
- Deterministic ordering across multiple diagnostics.

## Boundary confirmation

This document implements remaining planning gaps as contracts and fixtures only. It does not implement parser behavior, AST construction behavior, IR normalization behavior, analysis behavior, artifact emission, CLI behavior, integration behavior, runtime behavior, authority behavior, proof behavior, governance behavior, policy behavior, execution behavior, or mutation behavior.
