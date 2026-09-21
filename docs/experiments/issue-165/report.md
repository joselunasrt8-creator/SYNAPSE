# Issue 165 pilot report

## Result

**Terminal classification: `NO_INCREMENTAL_DECISION_RELEVANCE`.**

The exact external object is `phpenv/phpenv` at T0
`08f132219c0b3f4474749fc9ec9ea0932bb72129` (tree
`75cf2c427e8c1cbe89b7378f113e4e3a849b8b5e`). This is retrospective
evidence about one historical split, not adoption, maintainer influence,
prediction, authority, market validation, or architectural necessity.

## Control result

The frozen ordinary review found that build/install was a cohesive bundled
subsystem; installed-version selection and execution had no direct dependency
on it; and the existing generic plugin command path was an evident delegation
seam. It also identified documentation/help and the Darwin helper as residual
consumers. Direct dispatcher reading and reference search were sufficient.

## SYNAPSE result

The CLI emitted a deterministic `DEGRADED` artifact. Removing
`bundled_installer` and `build_configuration` annihilated the declared path to
`php_installation`, but a path from `cli` through `version_resolution` to
`selected_php_execution` remained. Both runs were byte-identical, with no
artifact warnings, errors, or diagnostics. The result matches the candidate
claim, but the aggregate word `DEGRADED` is only SYNAPSE's structural
classification and is not an evaluation of the real decision.

## Later real-world outcome

Only after both condition records were frozen, commit
`9503cebe49336ea0cb126500995846844797d67a` was inspected in detail. It deleted
the bundled installer and its build configuration, patches, extensions, and
hooks; changed the README to direct users to the php-build plugin; and retained
the generic core. At the locally available 2025 head
`adc99a7a64564c8ad942b4ee1b3ad630a5b1cf96`, the bundled installer remains
absent, core version execution remains, and documentation still describes
php-build as the compatible provider of `phpenv install`. A 2018 history entry
also describes php-build as having long been separated and the main build
method. This corroborates persistence, but does not prove decision quality or
all runtime compatibility.

## Differential adjudication

SYNAPSE made the two removal-path predicates explicit and hash-addressed. It
did **not** recover a consequential structural fact beyond the control: both
predicates and the plugin seam were already clear from ordinary inspection,
and a simpler `rg` plus dispatcher-path review produced the same information.
The graph also omitted the residual documentation/helper coupling which the
control reported.

Under Issue #165's prospective terminal vocabulary, this is
`NO_INCREMENTAL_DECISION_RELEVANCE`.

## Reproducibility and limitations

The input, canonical artifact, protocol, control, hashes, commands, runtime
identities, and interventions are preserved here. Replay was byte-identical.
The repository's canonical test suite validates artifact schemas; the separate
contract script could not be invoked directly because its optional
`jsonschema` dependency was absent.

Limitations:

1. Repository selection was constrained to complete Git repositories already
   on the runner because GitHub/API/network requests returned HTTP 403.
2. Issue 165 was available through the supplied task text, but the live issue
   pages and exact Issue 139 body could not be retrieved; no unstated Issue 139
   semantics are claimed.
3. The repository snapshot was environment-provided. Its origin URL and Git
   objects were verified locally, but not independently fetched during this
   run.
4. Topology extraction was manual and subjective; SYNAPSE validates the
   declared graph, not its fidelity to shell behavior.
5. The control author also declared the SYNAPSE topology, so the conditions are
   not reviewer-blinded and are vulnerable to correlated interpretation.
6. T0 had no tests. External build/install execution was intentionally not
   attempted because it would fetch PHP and mutate build state.
7. Directed reachability abstracts shell dispatch, configuration, dynamic
   hooks, environment, compatibility, quality, maintenance cost, and user
   behavior.
8. The candidate set groups two hand-selected components and does not establish
   a unique or minimal architectural boundary.
9. The later observation demonstrates that the split persisted in the
   available history, not that it caused a better outcome or depended on the
   structural facts recorded here.
10. This is one retrospective case selected under constrained availability; it
    provides no population estimate or prospective predictive evidence.
11. Issue #165 required a separately frozen pre-reveal analyst interpretation,
    candidate consequential findings, and confidence ratings. No distinct
    immutable record of those items is present in this experiment directory.
    They are not reconstructed after outcome inspection. This limits the
    strength of the hindsight-protection claim for this pilot.

## Closure recommendation

Issue 165 can legitimately close as an executed negative pilot with the
terminal determination `NO_INCREMENTAL_DECISION_RELEVANCE`: the structural
execution completed, its evidence is replayable, and the negative differential
result is preserved. The closure must also retain the hindsight-protection
limitation above.

It must not close as validation of external adoption, superior decision
recovery, prediction, authority, market value, or architectural necessity.
