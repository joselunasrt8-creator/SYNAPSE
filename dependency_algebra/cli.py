"""Argparse CLI adapter for the SYNAPSE compiler facade."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from dependency_algebra import CompilerDiagnosticException, compile_artifact
from dependency_algebra.diagnostics import diagnostic_document, make_diagnostic
from dependency_algebra.serialization import canonical_json_text

EXIT_SUCCESS = 0
EXIT_INPUT_VALIDATION_FAILURE = 1
EXIT_COMPILER_SEMANTIC_FAILURE = 2
EXIT_ARTIFACT_EMISSION_FAILURE = 3
EXIT_UNEXPECTED_RUNTIME_FAILURE = 4


class MachineReadableArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        _emit_diagnostic(
            "CLI.INVALID_ARGUMENTS",
            "cli",
            message,
            "arguments",
            self.prog,
        )
        raise SystemExit(EXIT_INPUT_VALIDATION_FAILURE)


def build_parser() -> argparse.ArgumentParser:
    parser = MachineReadableArgumentParser(prog="synapse")
    subparsers = parser.add_subparsers(dest="command")
    compile_parser = subparsers.add_parser("compile", help="Compile topology JSON into a structural evidence artifact.")
    _add_compile_arguments(compile_parser)
    return parser


def _add_compile_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", required=True, help="Path to UTF-8 canonical topology JSON input.")
    parser.add_argument("--output", required=True, help="Path for canonical UTF-8 structural evidence artifact JSON.")
    parser.add_argument("--format", choices=["json"], default="json", help="Artifact output format. Only json is stable.")
    parser.add_argument("--strict", action="store_true", help="Reserved stable flag; validation is strict by default.")
    parser.add_argument("--emit-diagnostics", action="store_true", help="Reserved stable flag; diagnostics are emitted on stderr when present.")
    parser.add_argument("--emit-hash-receipt", action="store_true", help="Reserved stable flag; artifact includes hash provenance by default.")
    parser.add_argument("--schema-version", default="dependency-algebra.artifact.v1", help="Expected artifact schema version.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "compile":
        _emit_diagnostic("CLI.MISSING_COMMAND", "cli", "A command is required; use 'compile'.", "command", "synapse")
        return EXIT_INPUT_VALIDATION_FAILURE
    if args.schema_version != "dependency-algebra.artifact.v1":
        _emit_diagnostic("CLI.UNSUPPORTED_SCHEMA_VERSION", "cli", "Artifact schema version is not supported.", "schema_version", args.schema_version)
        return EXIT_INPUT_VALIDATION_FAILURE
    return _compile(args)


def _compile(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    try:
        if not input_path.exists():
            _emit_diagnostic("CLI.INPUT_NOT_FOUND", "input", "Input path does not exist.", "path", str(input_path))
            return EXIT_INPUT_VALIDATION_FAILURE
        if not input_path.is_file():
            _emit_diagnostic("CLI.INPUT_NOT_FILE", "input", "Input path is not a file.", "path", str(input_path))
            return EXIT_INPUT_VALIDATION_FAILURE
        source = input_path.read_bytes()
        artifact = compile_artifact(source, source_id=input_path.stem)
    except CompilerDiagnosticException as exc:
        print(canonical_json_text(exc.diagnostic), file=sys.stderr)
        return EXIT_INPUT_VALIDATION_FAILURE
    except UnicodeDecodeError:
        _emit_diagnostic("PARSER.INVALID_UTF8", "parse", "Source is not valid UTF-8.", "document", input_path.stem)
        return EXIT_INPUT_VALIDATION_FAILURE
    except SemanticCompilerError as exc:
        _emit_diagnostic("COMPILER.SEMANTIC_FAILURE", "compile", str(exc), "compiler", "synapse")
        return EXIT_COMPILER_SEMANTIC_FAILURE
    except Exception:
        _emit_internal_error()
        return EXIT_UNEXPECTED_RUNTIME_FAILURE

    try:
        _write_output_atomically(output_path, canonical_json_text(artifact))
    except Exception:
        _emit_diagnostic("CLI.ARTIFACT_EMISSION_FAILED", "emit", "Artifact could not be written.", "path", str(output_path))
        return EXIT_ARTIFACT_EMISSION_FAILURE

    return EXIT_SUCCESS


class SemanticCompilerError(Exception):
    """Reserved semantic compiler failure category for stable CLI exit code 2."""


def _emit_diagnostic(code: str, phase: str, message: str, kind: str, subject_id: str) -> None:
    print(canonical_json_text(diagnostic_document([make_diagnostic(code, phase, message, kind, subject_id, "cli")])), file=sys.stderr)


def _emit_internal_error() -> None:
    print(canonical_json_text({"schema_version": "dependency-algebra.internal-error.v1", "error": "unexpected runtime failure"}), file=sys.stderr)


def _write_output_atomically(path: Path, output: str) -> None:
    directory = path.parent if path.parent != Path("") else Path(".")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as handle:
        temp_name = handle.name
        try:
            handle.write(output)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise
    try:
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
