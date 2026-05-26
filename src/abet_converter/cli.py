from __future__ import annotations

import argparse
import sys
from pathlib import Path

from abet_converter.components.ingest.abet_to_sqlite import (
    build_conversion_targets,
    convert_many,
    discover_abet_sources,
    normalize_formats,
)
from abet_converter.drivers.mdbtools import resolve_mdbtools_runtime
from abet_converter.path_support import add_script_dir_to_user_path, format_doctor, format_path_show


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abet-converter", description="ABET CONVERTER")
    parser.add_argument("--input", required=True, type=Path, dest="input_path")
    parser.add_argument("--output", required=True, type=Path, dest="output_path")
    parser.add_argument("--format", dest="formats", action="append", choices=["sqlite", "sql", "csv", "xlsx"])
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--mdbtools-dir", type=Path)
    return parser


def _handle_support_command(argv: list[str]) -> int | None:
    if not argv:
        return None

    command = argv[0]
    if command == "doctor":
        if len(argv) != 1:
            raise ValueError("doctor does not accept extra arguments.")
        print(format_doctor())
        return 0

    if command == "path":
        if len(argv) == 2 and argv[1] == "--show":
            print(format_path_show())
            return 0
        if len(argv) == 2 and argv[1] == "--add":
            result = add_script_dir_to_user_path()
            print(result.message)
            return 0
        raise ValueError("path requires either --show or --add.")

    return None


def _validate_output_path(input_path: Path, output_path: Path, formats: tuple[str, ...]) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    needs_directory_output = input_path.is_dir() or formats != ("sqlite",)

    if input_path.is_file() and not needs_directory_output:
        if output_path.exists() and output_path.is_dir():
            raise ValueError("--output must be a file path when converting one file to sqlite only.")
        if output_path.suffix.lower() != ".sqlite":
            raise ValueError("--output must end with .sqlite when --format is only sqlite for file input.")
        return

    if output_path.exists() and output_path.is_file():
        raise ValueError("--output must be a directory for directory input or multi-format export.")


def main(argv: list[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    support_result = _handle_support_command(effective_argv)
    if support_result is not None:
        return support_result

    parser = build_parser()
    args = parser.parse_args(effective_argv)

    input_path = args.input_path.resolve()
    output_path = args.output_path.resolve()
    formats = normalize_formats(args.formats)
    runtime = resolve_mdbtools_runtime(override_dir=args.mdbtools_dir.resolve() if args.mdbtools_dir else None)

    _validate_output_path(input_path, output_path, formats)

    sources = discover_abet_sources(input_path, recursive=args.recursive)
    if not sources:
        raise RuntimeError(f"No .ABETdb/.mdb files found in {input_path}")

    targets = build_conversion_targets(
        sources=sources,
        input_path=input_path,
        output_path=output_path,
        formats=formats,
    )
    written_paths = convert_many(targets, runtime)
    for written_path in written_paths:
        print(written_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
