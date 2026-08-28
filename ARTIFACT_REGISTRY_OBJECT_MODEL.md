# Artifact Registry Object Model v1

## 1. Status and boundary

This document defines the canonical, documentation- and contract-first SYNAPSE Artifact object. Its schema identity is `synapse.artifact-registry-object.v1`. It defines portable records; it does **not** define or implement storage, a graph database, a registry service, an API, synchronization, UI, deployment, authority evaluation, or execution.

The model is an envelope for existing SYNAPSE objects, not a replacement for them. In particular, `dependency-algebra.artifact.v1` remains the byte-compatible compiler artifact and `dependency-algebra.structural-evidence.v2` remains the registered-analysis evidence envelope. Either may be named by this model's `artifact_type` and `content_hash` without changing its schema or hash boundary.

## 2. Canonical Artifact object

The normative machine-readable definition is [`schemas/artifact-registry-object.schema.json`](schemas/artifact-registry-object.schema.json). Every object contains:

| Field | Contract |
| --- | --- |
| `schema_version` | Exactly `synapse.artifact-registry-object.v1`. |
| `artifact_id` | Globally unique immutable version identity, derived as specified below. |
| `logical_id` | Stable identity shared by versions of one logical artifact. |
| `artifact_type` | Names the payload contract, for example `synapse.repository-snapshot.v1` or an existing SYNAPSE schema identity. |
| `version` | Positive, monotonically increasing integer within a `logical_id`; it is not mutable state. |
| `producer` | Stable producer identity and kind (`person`, `system`, `process`, or `repository`). |
| `input_references` | Artifact version identities directly consumed to produce this version, sorted and unique. |
| `output_references` | Artifact version identities directly emitted with/by this version, sorted and unique. These are declared links, not embedded objects. |
| `provenance` | Source references, deterministic activity identity/version, optional reproducibility parameters, and environment-independent reproduction instructions. |
| `content_hash` | SHA-256 of the exact immutable payload bytes represented by the object. |
| `lifecycle_state` | Administrative availability state, independent of validity. |
| `validity` | Explicit confidence/validity assessment with assessor and basis; `unassessed` is first-class. |
| `supersession` | Optional immediate predecessor version for the same `logical_id`. |
| `relationships` | Typed, directed, non-inheriting cross-artifact edges. |

All fields are required except `supersession`. Empty arrays and objects are explicit. Unknown fields are rejected.

## 3. Artifact identity contract

`artifact_id` has the canonical form:

```text
urn:synapse:artifact:<logical_id>:v<version>
```

`logical_id` uses lowercase letters, digits, dots, underscores, and hyphens, begins with a letter or digit, and is stable across versions. The schema checks the lexical forms; deterministic semantic validation additionally checks that the three identity fields agree.

An identity names exactly one immutable payload and envelope. Two records with the same `artifact_id` but different bytes or fields are an identity collision and invalid. Identical payload bytes used for distinct purposes may have the same `content_hash`, but they do not thereby have the same artifact identity. Conversely, a new version may retain a content hash only when its payload bytes are identical; its changed envelope still represents a distinct version record.

## 4. Versioning and immutability rules

1. A published artifact version is append-only and immutable: payload, producer, references, provenance, lifecycle, validity, supersession, and relationships cannot be edited in place.
2. Any correction, reassessment, lifecycle transition, relationship change, or metadata change creates a new version with a new `artifact_id`.
3. Versions increase monotonically within a `logical_id`; gaps are allowed. Version numbers do not imply validity, authority, or execution.
4. `supersession` is absent for a version with no declared predecessor. When present, `previous_artifact_id` must name another version of the same `logical_id`, its `previous_version` must be lower, and a matching `supersedes` relationship must exist.
5. Supersession does not erase or mutate the predecessor and does not transfer validity, authorization, proof, or legitimacy.
6. `content_hash` is `sha256:` plus lowercase SHA-256 over the exact payload bytes. Envelope identity is not a content hash and this contract does not silently re-hash existing SYNAPSE formats.
7. Arrays that are sets (`input_references`, `output_references`, `source_references`, and `relationships`) are unique and lexically sorted by artifact identity (relationships by `type`, then `target_artifact_id`). This makes validation and replay deterministic.

Rollback is append-only: publish a new version that supersedes the unwanted version and references the restored payload. Never rewrite history.

## 5. Provenance and lineage contract

`producer` answers who or what asserted production. `provenance.activity` answers which deterministic process produced the artifact. `source_references` identify non-artifact origins (repository/revision/path, URI, or another stable external locator). `input_references` name the exact artifact versions consumed. `parameters` contain only stable replay inputs; secrets, timestamps, host-local paths, and ambient environment state are forbidden. `reproduction` is an ordered, non-empty list of implementation-independent steps.

A reproducible chain requires every consumed artifact identity to resolve to the immutable version named, every payload to match its `content_hash`, producer activity/version and parameters to be available, and each step's inputs and outputs to agree in both directions where output declarations are used. The object model records these facts but does not claim that resolution or replay has occurred.

`derived_from` records intellectual/data lineage and may be broader than direct computational inputs. `input_references` record actual direct consumption. Neither substitutes for the other.

## 6. Relationship semantics

Every relationship is directed from the containing artifact (source) to `target_artifact_id`, carries an optional `basis`, and has `legitimacy_inherited: false`. No relationship implies any other relationship.

| Type | Exact meaning |
| --- | --- |
| `produced_by` | Target is the immutable artifact describing the production activity/receipt responsible for the source. This complements, but does not replace, `producer`. |
| `derived_from` | Source incorporates, transforms, or is reasoned from the target. It does not assert target validity or direct execution consumption. |
| `supports` | Source supplies evidence favoring a claim expressed by the target. Support is not proof, validity, or authority. |
| `contradicts` | Source supplies evidence inconsistent with a claim expressed by the target. It does not automatically invalidate either artifact. |
| `supersedes` | Source is a newer declared replacement for a target version with the same `logical_id`; the target remains immutable and addressable. |
| `implements` | Source realizes a specification or model expressed by the target. Conformance, validation, and authorization require separate edges. |
| `validated_by` | Target records an assessment of the source against an identified criterion. It does not authorize use or execution. |
| `authorized_by` | Target records a scoped authority decision permitting a use of the source. It does not show that execution occurred or was correct. |
| `executed_as` | Target is an immutable execution record for an attempted use of the source. It does not prove correctness, validity, or authorization. |

The following distinctions are invariant:

- **Artifact existence ≠ validity:** identity and storage eligibility do not make `validity.state` valid.
- **Evidence ≠ authority:** `supports` and evidence payloads cannot grant permission.
- **Validation ≠ authorization:** `validated_by` cannot replace `authorized_by`.
- **Authorization ≠ execution:** permission does not establish an execution record.
- **Execution ≠ proof:** `executed_as` records an attempt/outcome, not logical or governance proof.
- **Relationship ≠ inherited legitimacy:** every edge fixes `legitimacy_inherited` to `false`; legitimacy must be independently established for each artifact and use.

## 7. Lifecycle model

`lifecycle_state` is one of:

- `draft`: identified but not published for stable consumption;
- `active`: published and available to consumers;
- `deprecated`: available but discouraged in favor of another artifact;
- `superseded`: replaced by a declared newer version;
- `withdrawn`: intentionally unavailable for new use while its historical identity remains;
- `archived`: retained for history and replay rather than current use.

Lifecycle is orthogonal to `validity.state`, which is `unassessed`, `valid`, `invalid`, or `indeterminate`. Confidence is an optional number from 0 through 1 and never changes the categorical state. An active artifact can be invalid; a superseded artifact can remain valid. State changes require a new version.

## 8. Valid and invalid examples

A production-receipt support object accompanies the chain so `produced_by` has a correctly typed target. The valid fixtures under [`fixtures/artifact_registry/valid/`](fixtures/artifact_registry/valid/) form a compressed end-to-end chain:

```text
Repository Snapshot
→ Observation
→ Evidence Record
→ Model Object
→ Analysis Result
→ Decision Reference
```

They demonstrate direct input/output references, broader lineage, validation, support, and a decision reference without conflating the decision with authority or execution. The analysis-result pair demonstrates immutable supersession.

Invalid fixtures under [`fixtures/artifact_registry/invalid/`](fixtures/artifact_registry/invalid/) demonstrate a mismatched identity, a cross-logical supersession, forbidden inherited legitimacy, and an authorization/execution conflation. Schema-invalid examples fail JSON Schema; semantic-invalid examples pass shape validation but fail deterministic cross-field validation.

## 9. Questions and query contract

Given a set of conforming immutable objects, consumers can answer:

- **What artifact was produced?** `artifact_id`, `artifact_type`, `version`, and `content_hash`.
- **Where did it originate?** `producer`, `provenance.source_references`, and `produced_by`.
- **Which inputs produced it?** `input_references` and the production `activity`.
- **What does it relate to?** typed `relationships`, without inferred edges.
- **What superseded it?** reverse lookup of `supersedes`, corroborated by the successor's `supersession`.
- **Which result consumed it?** reverse lookup of `input_references` (or `derived_from` only for non-consumption lineage).
- **Can the chain be reproduced?** verify resolvable identities and hashes, then replay the recorded activity version, parameters, and ordered reproduction steps. Absence of any requirement means “not demonstrated,” not “yes.”

These are graph queries over portable contracts, not a graph-store requirement.
