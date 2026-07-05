# AST and IR Contract

## Executive assessment

This contract freezes the boundary between validated topology JSON, a source-faithful Abstract Syntax Tree (AST), and the normalized Intermediate Representation (IR) consumed by later deterministic analysis passes.

The repository remains planning-first. The contract defines schemas, fixtures, ordering, invariants, hash boundaries, and diagnostic lineage expectations only. It does not introduce a parser, AST builder, IR normalizer, reachability engine, complement projection engine, dependency predicate evaluator, artifact emitter, CLI, runtime surface, governance surface, authority surface, proof surface, policy surface, execution surface, or external-state mutation surface.

## Canonical pipeline boundary

```text
Topology JSON
→ Parser
→ AST
→ IR
→ Reachability
→ Complement Projection
→ Dependency Predicate
→ Compiler Artifact
```

The AST/IR boundary is a compiler architecture contract:

- **AST** is source-faithful and diagnostic-oriented.
- **IR** is canonical, normalized, graph-oriented, and analysis-ready.
- Invalid topology is rejected before IR construction and is never classified as `NULL`.

## AST contract

The AST represents validated topology input closely enough to produce deterministic diagnostics against source-declared structure.

### AST responsibilities

The AST MUST retain:

- `schema_version` with value `dependency-algebra.ast.v1`.
- `topology_id` copied from source topology identity.
- Source-declared components.
- Source-declared directed edges.
- Source-declared workloads.
- Workload roots.
- Workload target.
- Workload candidate component set.
- Expected structural classification.
- Optional component metadata retained from topology labels.
- Optional edge metadata retained from topology labels.
- Optional stable source identity metadata when available.
- Source ordering metadata where useful for deterministic diagnostics.

The AST MUST preserve source-declared identifiers exactly. It MAY preserve source array order through explicit `source_order` integers rather than relying on array order as semantics.

### AST non-responsibilities

The AST MUST NOT contain:

- Computed reachability.
- Complement projections.
- Dependency predicate results.
- Compiler artifacts.
- Normalized adjacency tables.
- Governance decisions.
- Authority propagation.
- Runtime authorization.
- Proof generation.
- Runtime policy.
- Execution eligibility.
- External-state mutation semantics.
- ContinuityOS legitimacy outcomes.

## IR contract

The IR is the canonical normalized graph representation consumed by deterministic structural analysis passes.

### IR responsibilities

The IR MUST define:

- `schema_version` with value `dependency-algebra.ir.v1`.
- `topology_id`.
- A canonical component table.
- A canonical edge table.
- Deterministic forward adjacency.
- Deterministic reverse adjacency in v1.
- A normalized workload table.
- Canonical root sets.
- Canonical target identity.
- Canonical candidate sets.
- Stable identifier ordering.
- Stable source-to-IR lineage references.
- Cycle representation without traversal or expansion.
- Disconnected component representation without error.

The IR MUST be representable without running reachability, complement projection, or dependency predicate evaluation.

### Primary representation decision

Canonical IR is represented primarily as **arrays of records** for ordered component, edge, and workload tables, plus **maps** for adjacency tables keyed by canonical component identifier.

Rationale: arrays provide deterministic table ordering and map entries provide direct adjacency lookup without making map iteration order semantically relevant.

## AST-to-IR normalization contract

Normalization from AST to IR MUST:

1. Validate all topology semantic references before emitting IR.
2. Reject duplicate component identifiers.
3. Reject duplicate edge identifiers.
4. Reject duplicate workload identifiers.
5. Resolve every edge endpoint to a declared component.
6. Resolve every workload root to a declared component.
7. Resolve every workload target to a declared component.
8. Resolve every candidate component to a declared component.
9. Reject empty candidate sets in v1.
10. Deduplicate duplicate roots within a workload after validation.
11. Deduplicate duplicate candidate components within a workload after validation.
12. Sort set-like collections lexicographically by canonical identifier.
13. Preserve graph direction exactly as `from → to`.
14. Preserve cycles as graph structure without traversal-derived fields.
15. Preserve isolated components in the component table and adjacency maps.
16. Convert component and edge `labels` to IR `metadata` when present.
17. Exclude volatile source positions, local paths, environment values, timestamps, and random identifiers from hash-participating IR.
18. Fail normalization deterministically when any invariant cannot be satisfied.

Duplicate roots and duplicate candidates are deduplicated, not rejected, because they are set-like workload declarations. Duplicate component, edge, and workload identifiers are rejected because they define tables and lineage anchors.

## Canonical ordering rules

The following ordering is canonical in normalized IR:

- Components: lexicographic by `id`.
- Edges: lexicographic by `id`; edge identifiers are the stable edge keys.
- Workloads: lexicographic by `id`.
- Workload roots: lexicographic by component identifier after deduplication.
- Candidate sets: lexicographic by component identifier after deduplication.
- Forward adjacency keys: lexicographic by component identifier in canonical serialization.
- Forward adjacency edge lists: lexicographic by edge identifier.
- Reverse adjacency keys: lexicographic by component identifier in canonical serialization.
- Reverse adjacency edge lists: lexicographic by edge identifier.
- Diagnostics: lexicographic by `code`, then source lineage identifier, then affected canonical identifier.
- Metadata maps: lexicographic by key during canonical serialization.

Source order is retained only for diagnostics and does not affect IR equality.

## IR invariants

A valid IR MUST guarantee:

- All component identifiers are unique.
- All edge identifiers are unique.
- All workload identifiers are unique.
- All edge endpoints resolve to component identifiers.
- All workload roots resolve to component identifiers.
- Every workload target resolves to a component identifier.
- All candidate components resolve to component identifiers.
- Candidate sets are non-empty in v1.
- Candidate sets contain components only.
- Duplicate roots are normalized by deduplication.
- Duplicate candidate components are normalized by deduplication.
- Graph direction is explicit and preserved.
- Self-loop edges are valid.
- Parallel edges are valid when edge identifiers differ.
- Cycles remain representable.
- Isolated and disconnected components remain representable.
- Roots may include the target.
- Candidate sets may include roots.
- Candidate sets may include the target.
- Ordering is canonical.
- No unresolved references remain.
- No invalid topology is silently converted into IR.
- Invalid input is rejected rather than classified as `NULL`.

## IR equality semantics

Two IR documents are equivalent when their hash-participating canonical IR content is byte-identical after canonical serialization.

Equivalent topology inputs MUST produce equivalent normalized IR even if they differ in:

- JSON object key order.
- Set-like array order.
- Duplicate roots or duplicate candidate declarations that normalize to the same set.
- Irrelevant source formatting.
- Source-only diagnostic ordering metadata.

Inputs MUST produce different normalized IR when they differ in:

- Component identifiers.
- Edge identifiers.
- Workload identifiers.
- Graph direction.
- Workload roots after normalization.
- Workload targets.
- Candidate sets after normalization.
- Semantic graph structure.
- Hash-participating metadata.

## `normalized_ir_hash` boundary

`normalized_ir_hash` is SHA-256 over canonical UTF-8 JSON bytes of the normalized IR hash payload.

The canonical serialized IR hash payload MUST:

- Omit `normalized_ir_hash` itself.
- Omit transient diagnostics unless a future contract explicitly declares a diagnostic subset hash-participating.
- Omit wall-clock timestamps.
- Omit random identifiers.
- Omit absolute machine paths.
- Omit environment-derived fields.
- Omit governance, authority, proof, runtime, policy, execution, and mutation fields.
- Use lexicographically sorted object keys.
- Use canonical ordering for set-like arrays.
- Use compact JSON separators: comma `,` and colon `:` with no extra spaces.
- Use UTF-8 encoding.
- Use no trailing newline in the bytes passed to SHA-256.

In v1, hash-participating fields are:

- `schema_version`.
- `topology_id`.
- `components`.
- `edges`.
- `adjacency`.
- `reverse_adjacency`.
- `workloads`.
- Hash-participating `metadata` retained from topology labels.
- Stable source lineage identifiers when present.

Hash-excluded fields include transient diagnostics and volatile source locations. The v1 IR schema therefore does not include diagnostics or volatile source-location fields.

## Source-lineage policy

Source lineage policy is option **B with a restricted stable subset**:

- The AST retains source-order and optional source-location information for diagnostics.
- The canonical IR retains stable source identifiers only, such as source topology identifiers and source declaration identifiers.
- Machine-local file paths, line numbers, columns, byte offsets, wall-clock timestamps, and environment-derived fields do not affect `normalized_ir_hash`.
- Volatile source positions are AST-only unless a future diagnostics contract introduces a hash-excluded diagnostic envelope outside normalized IR.

## Explicit decisions for open questions

1. Duplicate workload IDs are rejected.
2. Duplicate roots are deduplicated after validation.
3. Duplicate candidate components are deduplicated after validation.
4. Self-loop edges are valid.
5. Parallel edges are valid if edge IDs differ.
6. Isolated components are valid.
7. Roots are allowed to include the target.
8. Candidate sets are allowed to include roots.
9. Candidate sets are allowed to include the target.
10. IR includes reverse adjacency in v1.
11. Component and edge labels survive normalization as `metadata`; AST-only source locations do not.
12. Hash-participating fields are the normalized structural IR fields listed in the hash boundary.
13. Diagnostic and volatile source-location fields are hash-excluded.
14. Canonical IR is represented as ordered arrays for tables and maps for adjacency.

## Deferred questions

- Whether future versions support edge candidates, group candidates, or empty candidate sets.
- Whether future versions define a diagnostic envelope alongside but outside normalized IR.
- Whether future versions add typed metadata beyond string-valued labels.
- Whether future versions include precomputed strongly connected components. v1 represents cycles without computing them.
- Whether future artifact hashes include selected diagnostics once compiler artifacts exist.

## Remaining gaps before parser implementation

The parser-facing planning gaps are closed by `COMPILER_FRONTEND_CONTRACT.md`, `schemas/diagnostic.schema.json`, and `fixtures/diagnostics/`. Before a parser is implemented, the project still needs implementation work that consumes those contracts, but no parser or normalizer implementation is introduced here.

## Boundary confirmation

This contract is structural analysis only. It does not define or introduce governance decisions, execution eligibility, runtime authorization, proof generation, authority propagation, runtime policy, external-state mutation, or ContinuityOS legitimacy outcomes. `VALID`, `DEGRADED`, and `NULL` remain structural classifications only.
