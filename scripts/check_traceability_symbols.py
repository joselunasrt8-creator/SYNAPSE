#!/usr/bin/env python3
"""Validate traceability symbols by importing referenced Python modules."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from check_traceability import DEFAULT_MANIFEST, ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Traceability manifest path.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable validation report.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    errors = validate_symbols(manifest_path)
    report = {
        "schema_version": "synapse.traceability-symbol-check.v1",
        "manifest": str(manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path),
        "valid": not errors,
        "errors": errors,
    }
    if args.json or errors:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        print("traceability imported-symbol validation passed")
    return 0 if not errors else 1


def validate_symbols(path: Path) -> list[str]:
    try:
        manifest: Any = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # deterministic validation surface, not an import guard
        return [f"manifest unreadable: {exc}"]

    errors: list[str] = []
    for collection in ("entries", "unspecified_public_behaviors"):
        records = manifest.get(collection, [])
        if not isinstance(records, list):
            errors.append(f"manifest {collection} must be an array")
            continue
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"{collection}[{index}] must be an object")
                continue
            _validate_symbol(
                record.get("implementation_path", ""),
                record.get("implementation_symbol", ""),
                f"{collection}[{index}]",
                errors,
            )
    return errors


def _validate_symbol(path_text: str, symbol: str, prefix: str, errors: list[str]) -> None:
    if not path_text or not symbol or not path_text.endswith(".py"):
        return
    path = ROOT / path_text
    if not path.is_file():
        errors.append(f"{prefix}.implementation_path does not exist: {path_text}")
        return
    module_name = path_text[:-3].replace("/", ".")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # importing is the explicit purpose of this validation path
        errors.append(f"{prefix}.implementation_path could not be imported: {module_name}: {exc}")
        return
    if not hasattr(module, symbol):
        errors.append(f"{prefix}.implementation_symbol not found: {module_name}.{symbol}")


if __name__ == "__main__":
    raise SystemExit(main())
