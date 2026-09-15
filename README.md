# SYNAPSE

## Deterministic Structural Analysis Framework

SYNAPSE compiles declared software topology into deterministic structural-analysis results and reproducible evidence artifacts.

Its current research/engineering question is:

> **Given an explicitly declared topology and analysis contract, can SYNAPSE reproducibly compute structural properties of that model?**

```text
Declared topology
      ↓
Validation + canonical representation
      ↓
Registered deterministic analysis
      ↓
Structural result
      ↓
Reproducible evidence artifact
```

Dependency Algebra is the current reference implementation and first registered analysis. It demonstrates the framework's compiler and evidence architecture without establishing that SYNAPSE captures all meaningful properties of real software systems.

## What SYNAPSE currently establishes

For accepted inputs and implemented contracts, SYNAPSE can support claims about:

- deterministic parsing, validation, and normalization;
- canonical structural representation;
- deterministic complement projection and directed reachability;
- the implemented dependency predicate;
- deterministic structural classification under that predicate;
- canonical serialization and hash-addressed evidence; and
- byte-identical replay where specified by the determinism contract.

These are properties of the declared model and implemented analysis semantics.

## Core analysis boundary

The implemented Dependency Algebra predicate is:

```text
Dependency(S, W) ⇔ Reach(W | ¬S) = ∅
```

Where `W` is a declared workload, `S` is its candidate component set, `¬S` removes those components and incident edges, and `Reach` asks whether a directed path remains from a workload root to its target.

The predicate answers a precise graph-model question. It does not by itself establish runtime necessity, causal dependence, failure probability, business criticality, security risk, performance impact, organizational ownership, or execution legitimacy.

## Model versus system

SYNAPSE analyzes the topology supplied to it. Therefore:

```text
Deterministic result ≠ complete real-world model
Canonical topology ≠ observed runtime topology
Structural dependency ≠ causal necessity in every environment
VALID / DEGRADED / NULL ≠ execution permission
Evidence artifact ≠ authority
```

If the source topology omits a component, edge, dynamic dependency, conditional behavior, runtime configuration, external service, or relevant state transition, the deterministic result can still be internally correct for the declared model while being incomplete as a description of the deployed system.

Model fidelity is therefore a separate empirical problem from compiler determinism.

## Inputs

SYNAPSE currently accepts UTF-8 JSON topology documents constrained by `schemas/topology.schema.json`. Inputs declare components, directed edges, workloads, roots, targets, candidate component sets, and expected structural classifications under the current schema.

Invalid input is rejected before analysis. Accepted input is normalized into canonical IR as defined by `AST_IR_CONTRACT.md` and `schemas/ir.schema.json`.

The normalized representation has a deterministic SHA-256 identity over canonical UTF-8 JSON bytes.

## Registered analyses

The currently implemented registered analysis is Dependency Algebra, including:

- complement projection;
- directed reachability;
- dependency-predicate evaluation; and
- aggregate structural classification as `VALID`, `DEGRADED`, or `NULL`.

Unimplemented analyses are not capabilities of the current system.

A proposed future analysis should not be treated as part of SYNAPSE merely because it is conceptually compatible. It should enter the registry only after its structural question, semantics, schemas, fixtures, evidence boundary, and tests are explicit.

## Classification semantics

`VALID`, `DEGRADED`, and `NULL` are structural classifications within registered analysis contracts.

They do not mean:

- safe / unsafe;
- authorized / unauthorized;
- healthy / unhealthy;
- should deploy / should not deploy;
- legitimate / illegitimate; or
- economically valuable / valueless.

Any downstream system using a structural classification to make a decision owns the mapping from structural evidence to that decision.

## Structural evidence

SYNAPSE can emit deterministic structural evidence artifacts containing source/compiler versions, input and normalized-IR hashes, analysis results, provenance, diagnostics, and artifact identity as defined by the repository's schemas.

An evidence artifact supports reproducibility and inspection of the implemented analysis. It does not prove that the source topology was complete or correct, that the analysis question was the right one, or that a downstream interpretation is valid.

## Determinism boundary

SYNAPSE determinism requires canonical ordering/serialization, stable hash boundaries, deterministic diagnostics, and exclusion of nondeterministic environment values from compiler artifacts.

Run the current regression/conformance suite with:

```bash
python -m pytest tests
```

Repository traceability and executable symbol checks provide additional evidence that documented implementation references remain connected to repository code.

These checks establish implementation correspondence and reproducibility—not scientific truth about arbitrary external systems.

## CLI

The stable command shape is:

```bash
python -m dependency_algebra.cli compile --input fixtures/basic.json --output out/artifact.json
```

or, when installed:

```bash
synapse compile --input fixtures/basic.json --output out/artifact.json
```

The CLI compiles accepted topology JSON into a deterministic structural evidence artifact and does not mutate the input.

## Normative contracts

`SPEC.md` is the repository-level contract index. The implemented contract surface includes topology schemas, AST/IR semantics, frontend validation/diagnostics, complement projection, reachability, dependency predicate, classification, artifact/receipt evidence, fixtures, and determinism requirements.

Those contracts define what SYNAPSE computes. They should not be expanded by README language beyond what the implementation and tests support.

## Relationship to Structology

SYNAPSE is an analysis engine/framework. Structology, where used in the Continufy research ecosystem, is the broader investigation of structural properties, invariants, dependencies, boundaries, and transformations.

A useful separation is:

```text
Structology
Research questions / structural theory
        ↓ may define
Formal structural analysis
        ↓ may be implemented by
SYNAPSE
Deterministic compiler / analysis / evidence
```

SYNAPSE should not be treated as proof of a broader structural theory merely because it implements one formal analysis.

## Relationship to MindShift and ContinuityOS

SYNAPSE can provide structural evidence to other systems, but it does not own cognition or execution legitimacy.

```text
MindShift: context / candidate cognition
SYNAPSE: deterministic structural analysis
ContinuityOS: legitimacy / execution-boundary mechanisms
```

No mandatory dependency follows from ecosystem membership. A downstream consumer must justify why SYNAPSE evidence is relevant to its own decision.

## Evaluation program

The next high-value work is not simply adding analyses. It is testing whether the current structural model corresponds to consequential properties of real software systems.

Priority experiments:

1. **Model fidelity** — compare declared SYNAPSE topology against independently observed build/runtime/deployment dependencies.
2. **Perturbation validation** — remove or isolate components predicted to be dependencies and observe whether the real workload loses the modeled path/capability.
3. **Baseline comparison** — compare SYNAPSE outputs with standard graph/dependency tooling and determine what unique evidence it adds.
4. **Dynamic-topology challenge** — test systems with plugins, reflection, runtime service discovery, feature flags, generated code, and environment-dependent edges.
5. **Cross-repository replication** — apply the same frozen analysis to unrelated repositories without modifying semantics after seeing outcomes.
6. **Downstream usefulness** — test whether structural evidence improves a concrete engineering decision relative to a strong baseline.

Each experiment should freeze its topology-acquisition method, analysis version, comparator, outcome measure, and claim ceiling before execution.

## Falsification boundary

SYNAPSE should be narrowed or its claims weakened if evidence shows that:

- declared topology cannot achieve sufficient fidelity for the intended use;
- the dependency predicate does not correspond to consequential real-system behavior;
- standard existing tools produce equivalent results with lower complexity;
- deterministic evidence adds no meaningful downstream value;
- analyses fail to transfer across software architectures; or
- downstream users cannot reliably interpret the classifications without unsupported assumptions.

Negative results are valid research outcomes.

## Repository boundary

SYNAPSE is limited to deterministic structural analysis over declared inputs.

It does not:

- discover complete real-world topology by default;
- infer missing runtime edges as fact;
- establish causality from graph structure alone;
- create authority or permission;
- execute or mutate external systems;
- determine legitimacy;
- prove scientific theories by passing tests; or
- establish product value from internal conformance.

SYNAPSE deliberately ends at structural evidence.

## Current conclusion

SYNAPSE has a concrete implemented compiler/analysis/evidence architecture and a precise first analysis in Dependency Algebra. Its strongest supported claim is that it can deterministically analyze declared topology according to explicit contracts and emit reproducible structural evidence.

The next claim to earn is external correspondence: whether those structural results accurately capture consequential properties of real systems and improve engineering decisions beyond simpler baselines.
