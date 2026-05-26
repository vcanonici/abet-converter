from pathlib import Path
import os
import subprocess
import sys

import pytest

from abet_converter.components.ingest.abet_to_sqlite import normalize_formats
from abet_converter.cli import _handle_support_command, _validate_output_path, build_parser


def test_cli_exposes_abet_converter_interface() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--input",
            "C:\\data\\input.ABETdb",
            "--output",
            "C:\\data\\exports",
            "--format",
            "sqlite",
            "--format",
            "csv",
            "--recursive",
        ]
    )

    assert args.input_path == Path("C:\\data\\input.ABETdb")
    assert args.output_path == Path("C:\\data\\exports")
    assert args.formats == ["sqlite", "csv"]
    assert args.recursive is True


def test_validate_output_path_rejects_directory_output_for_file_sqlite_only(tmp_path: Path) -> None:
    input_file = tmp_path / "input.ABETdb"
    output_dir = tmp_path / "out"
    input_file.write_text("x", encoding="utf-8")
    output_dir.mkdir()

    with pytest.raises(ValueError, match="file path"):
        _validate_output_path(input_file, output_dir, ("sqlite",))


def test_validate_output_path_rejects_file_output_for_directory_input(tmp_path: Path) -> None:
    input_dir = tmp_path / "incoming"
    output_file = tmp_path / "out.sqlite"
    input_dir.mkdir()
    output_file.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="directory"):
        _validate_output_path(input_dir, output_file, ("sqlite",))


def test_validate_output_path_rejects_file_output_for_multi_format_file_input(tmp_path: Path) -> None:
    input_file = tmp_path / "input.ABETdb"
    output_file = tmp_path / "out.sqlite"
    input_file.write_text("x", encoding="utf-8")
    output_file.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="directory"):
        _validate_output_path(input_file, output_file, ("sqlite", "csv"))


def test_normalize_formats_defaults_to_sqlite() -> None:
    assert normalize_formats(None) == ("sqlite",)


def test_module_execution_delegates_to_cli_help() -> None:
    env = os.environ.copy()
    source_path = Path(__file__).resolve().parents[2] / "src"
    env["PYTHONPATH"] = f"{source_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
    completed = subprocess.run(
        [sys.executable, "-m", "abet_converter", "--help"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "ABET CONVERTER" in completed.stdout
    assert "--input" in completed.stdout


def test_support_command_doctor_prints_installation_status(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    monkeypatch.setattr("abet_converter.path_support.get_script_dir", lambda: tmp_path)
    monkeypatch.setenv("PATH", "")

    assert _handle_support_command(["doctor"]) == 0

    output = capsys.readouterr().out
    assert "ABET Converter installation check" in output
    assert "Script directory on current terminal PATH: no" in output
    assert "python" in output.lower()


def test_support_command_path_show_prints_script_directory(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    monkeypatch.setattr("abet_converter.path_support.get_script_dir", lambda: tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))

    assert _handle_support_command(["path", "--show"]) == 0

    output = capsys.readouterr().out
    assert f"Script directory: {tmp_path}" in output
    assert "Script directory on current terminal PATH: yes" in output
