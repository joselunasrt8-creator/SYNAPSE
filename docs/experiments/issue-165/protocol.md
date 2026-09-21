# Issue 165 retrospective external-repository pilot protocol

Status: frozen before detailed outcome inspection on 2026-09-21 (UTC).

## Boundaries and readiness

This pilot tests retrospective decision recovery, not external adoption or
prospective prediction.  A structural result is evidence, not authority.  It
cannot establish maintainer influence, workflow dependency, economic value,
market validation, or a need for SYNAPSE.  No new analysis, parser, or runtime
surface is authorized.

Current `main` at `975fbd743e4c310c5e41feac41698e2044f25b6d` provides the required
topology-v1 input, compiler CLI, deterministic artifact, hashes, diagnostics,
fixtures, and tests.  Issue 165 is executable only as a manually declared and
source-cited topology: SYNAPSE does not extract repository topology.  Manual
translation is therefore an intervention and a threat to validity, not a new
SYNAPSE capability.  Issue 139 is treated only as the downstream reporting
protocol described by the issue; this pilot creates no authority or adoption
claim.

## Prospective selection criteria

Before choosing a repository, candidates were required to be public, not
controlled by the Continufy owner, locally available with full Git history,
and to contain: (1) a documented consequential architecture, refactor, or
dependency decision; (2) an identifiable parent commit; (3) later history
adequate to observe the result; and (4) enough source and documentation for
both review methods.  Network access was unavailable, so locally cached
shallow repositories were excluded.  Exactly one candidate met all criteria:
`phpenv/phpenv` (origin recorded in `lineage.json`).

## Frozen object and question

* Repository: `https://github.com/phpenv/phpenv.git`.
* T0 commit: `08f132219c0b3f4474749fc9ec9ea0932bb72129`, the parent of the
  documented delegation commit identified during selection.
* Engineering question: could phpenv delegate PHP build/install capability to
  a plugin while retaining its core version-selection and execution path?
* Candidate claim: at T0 the bundled build subsystem is required for bundled
  installation, but is not a structural dependency of selecting and executing
  an already installed PHP; generic plugin command discovery provides a
  replacement attachment point.

## Frozen procedures

The **control** is one competent static review of the T0 README, file tree,
shell command dispatcher, direct references to install/build/hooks/plugins,
and available tests.  It records facts and uncertainty without graph tooling.
Its notes must be saved before SYNAPSE runs.

The **SYNAPSE condition** manually translates only those same T0 observations
into `input.json`, runs the repository CLI once, validates the emitted JSON,
then repeats the command and requires byte identity.  No later commit may
inform the topology.  Inputs, output, SHA-256 identities, runtime versions,
warnings, failures, and interventions are retained.

Only after both records are frozen may later commits and documentation be
examined.

## Adjudication rubric and terminal rules

A fact is **material** only if it bears on the later decision or its observed
result.  A fact is **additional** only if the preserved control did not state
it comparably clearly and a simpler direct-reference/path inspection did not
produce it.  Technical correctness alone does not qualify.

Exactly one terminal classification applies:

* **SUPPORTED RETROSPECTIVE DECISION-RECOVERY EVIDENCE** — SYNAPSE recovers at
  least one material, later-corroborated structural fact absent from both the
  control and a simpler method.
* **NOT SUPPORTED** — execution completes, but every correct material SYNAPSE
  fact was already in the control, is obtainable by a simpler method, is not
  consequential, or is contradicted.
* **BLOCKED** — a frozen object or required condition cannot be acquired or
  executed, so comparison cannot be completed.
* **INDETERMINATE** — both conditions execute but public later evidence cannot
  resolve consequence or correctness.

Any protocol contamination after this freeze is reported and yields
INDETERMINATE rather than being repaired by expanding SYNAPSE.
