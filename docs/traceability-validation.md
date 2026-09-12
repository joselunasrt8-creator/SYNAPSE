# Traceability validation boundaries

SYNAPSE reports repository-static correspondence separately from imported-symbol
validity. Validation is evidence about the checked object; it is not authority or a
scientific correctness claim.

## Check classification

Every check formerly reached through `scripts/check_traceability.py` has exactly one
classification:

| Check | Classification | Current path |
| --- | --- | --- |
| Manifest readability and JSON decoding | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Traceability schema identity | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Exact allowed-status vocabulary | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Non-empty entry array and object shape | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Required fields and required non-empty values | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Status membership and `exact_gap` requirements | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Duplicate mapping rejection | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Specification file and Markdown-anchor resolution | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Implementation, test, schema, and fixture path resolution | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Frozen-contract-index coverage | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Unspecified-public-behavior status warning | `STATIC_TRACEABILITY` | `check_traceability.py` |
| Import each referenced Python implementation module | `IMPORT_BASED_SYMBOL_VALIDATION` | `check_traceability_symbols.py` |
| Resolve each declared symbol with `hasattr` | `IMPORT_BASED_SYMBOL_VALIDATION` | `check_traceability_symbols.py` |

The former traceability path performed no `RUNTIME_CONFORMANCE` or
`EXTERNAL_CONFORMANCE` checks. Those classes remain outside these two commands.

## Execution boundary

Previously, `_validate_symbol` called `importlib.import_module` for every existing
Python `implementation_path` in both `entries` and `unspecified_public_behaviors`.
That silently executed module top-level code while reporting a single “traceability”
result. The static command no longer imports project modules. The separately named
symbol command intentionally imports all such referenced modules and therefore
executes their import-time code.

Both commands fail closed in their own scope: unresolved files and specification
anchors fail the static command, while missing modules and symbols fail imported-symbol
validation. Source correspondence is not imported-symbol validity; imported-symbol
validity is not runtime conformance; runtime conformance is not external conformance.
