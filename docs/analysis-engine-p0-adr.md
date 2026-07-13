# ADR: P0 Core Analysis Engine Boundary

Status: accepted for P0

## Decision

SYNAPSE exposes its existing deterministic structural analysis through a minimal analysis-engine boundary:

```text
CanonicalIR
    ↓
Analysis Pass
    ↓
Deterministic Registry
    ↓
Analysis Engine
```

For P0, this is an architectural boundary and registration foundation only. Existing compiler and CLI execution paths remain unchanged.

## Canonical analysis input

The canonical analysis input is `dependency_algebra.ir.CanonicalIR`.

`CanonicalIR` is already the normalized, deterministic structural input produced by the compiler frontend. The analysis pass boundary therefore starts after parsing, validation, normalization, and canonical IR construction.

## Canonical analysis output

The canonical analysis output is `dependency_algebra.ir.AnalysisResult` with schema identity `dependency-algebra.analysis.v1`.

The pass output is the existing immutable structural analysis result. Serialized compiler artifacts and research-object projections remain downstream consumers or parallel conformance surfaces, not pass outputs.

## Responsibility split

### Analysis engine

The analysis engine is responsible for deterministic execution of structural analysis over a `CanonicalIR` and returning an `AnalysisResult`. In P0 the existing `dependency_algebra.engine.analyze_artifact` implementation remains the engine behavior.

### Analysis pass

An analysis pass is a small deterministic adapter around an existing analysis implementation. It exposes only:

- `analysis_id`
- `analysis_version`
- accepted input contract
- deterministic `execute()`
- deterministic configuration
- specification references
- output contract identity

A pass does not own plugin loading, discovery, orchestration, dependency migration, artifact metadata, validation pipeline behavior, or serialization policy.

### Deterministic registry

The registry owns explicit repository-defined registration only. It provides stable IDs, duplicate rejection, deterministic enumeration, explicit lookup, and fail-closed unknown-ID behavior.

The registry does not scan packages, dynamically load plugins, alter research-object registration, or change CLI behavior.

### Compiler artifacts

Compiler artifacts remain serialized evidence products emitted by `dependency_algebra.compiler.compile_artifact`. They are not analysis passes and are not registry entries. Artifact schema, hash boundaries, provenance shape, CLI output, and fixture compatibility remain unchanged.

## Boundary preservation

P0 preserves the distinction:

```text
Analysis Pass ≠ Research Object Projection ≠ Compiler Artifact
```

- An analysis pass adapts deterministic structural analysis over `CanonicalIR`.
- A research object projection is a conformance/governance representation used by the research-object subsystem.
- A compiler artifact is a serialized evidence product with its own schema and hash boundary.

These concepts intentionally do not share registration, metadata, or serialization ownership in P0.

## Why this boundary is minimal

The boundary starts at `CanonicalIR` because that is the smallest existing deterministic input that avoids re-owning parser, validator, normalization, schema, and CLI responsibilities.

The boundary ends at `AnalysisResult` because that is the smallest existing immutable output that avoids re-owning compiler artifact schemas, hash receipts, provenance fields, or research-object projections.

The registry is explicit and in-memory because P0 only needs deterministic core registration, not plugin discovery or orchestration.

## Compatibility guarantees

P0 guarantees no behavior changes to:

- `dependency_algebra.engine.analyze`
- `dependency_algebra.compiler.compile_artifact`
- `dependency_algebra.predicate.evaluate`
- dependency result hashes
- compiler artifact hashes
- `CanonicalIR` semantics
- CLI output
- existing fixtures
- traceability behavior

The new pass and registry are additive surfaces. Existing execution paths are not rewired.

## Migration strategy

1. P0 introduces the stable pass contract and deterministic core registry as additive APIs.
2. Existing deterministic structural analysis is represented by a pass adapter without changing execution semantics.
3. Future P1 work may choose to route orchestration through this boundary, but that migration is intentionally out of scope for P0.
4. Research-object registration and compiler artifact emission remain separate unless a later issue explicitly authorizes migration.
