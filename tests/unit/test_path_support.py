from __future__ import annotations

from pathlib import Path

import pytest

from abet_converter.path_support import (
    PathStatus,
    add_unix_user_path,
    add_windows_user_path,
    build_path_status,
    format_doctor,
    format_path_show,
    get_windows_user_path,
    path_contains,
)


class FakeKey:
    def __init__(self, registry: "FakeWinreg") -> None:
        self.registry = registry

    def __enter__(self) -> "FakeKey":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class FakeWinreg:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_WRITE = 2
    REG_EXPAND_SZ = 2

    def __init__(self, path_value: str = "") -> None:
        self.path_value = path_value
        self.value_type = self.REG_EXPAND_SZ

    def OpenKey(self, *_args: object) -> FakeKey:
        return FakeKey(self)

    def QueryValueEx(self, _key: FakeKey, name: str) -> tuple[str, int]:
        if name != "Path" or self.path_value == "__missing__":
            raise FileNotFoundError
        return self.path_value, self.value_type

    def SetValueEx(self, _key: FakeKey, name: str, _reserved: int, value_type: int, value: str) -> None:
        assert name == "Path"
        self.value_type = value_type
        self.path_value = value


def test_path_contains_uses_platform_separator(tmp_path: Path) -> None:
    script_dir = tmp_path / "Scripts"

    assert path_contains(script_dir, f"C:\\Other;{script_dir}", path_separator=";")
    assert not path_contains(script_dir, "C:\\Other", path_separator=";")


def test_format_doctor_reports_missing_path(tmp_path: Path) -> None:
    status = PathStatus(
        python_executable=Path("C:/Python/python.exe"),
        package_version="0.3.6",
        script_dir=tmp_path,
        script_dir_in_path=False,
        user_path_includes_script_dir=None,
        repair_command="python -m abet_converter path --add",
    )

    output = format_doctor(status)

    assert "Version: 0.3.6" in output
    assert "Script directory on current terminal PATH: no" in output
    assert "python -m abet_converter path --add" in output


def test_format_path_show_separates_current_terminal_from_windows_user_path(tmp_path: Path) -> None:
    status = PathStatus(
        python_executable=Path("C:/Python/python.exe"),
        package_version="0.3.6",
        script_dir=tmp_path,
        script_dir_in_path=False,
        user_path_includes_script_dir=True,
        repair_command="python -m abet_converter path --add",
    )

    output = format_path_show(status)

    assert "Script directory on current terminal PATH: no" in output
    assert "Script directory on Windows user PATH: yes" in output
    assert "Open a new PowerShell/Terminal window" in output


def test_build_path_status_reads_windows_user_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_winreg = FakeWinreg(f"C:\\Other;{tmp_path}")
    monkeypatch.setattr("abet_converter.path_support.sys.platform", "win32")
    monkeypatch.setattr("abet_converter.path_support.get_script_dir", lambda: tmp_path)
    monkeypatch.setenv("PATH", "C:\\Other")

    status = build_path_status(winreg_module=fake_winreg)

    assert status.script_dir_in_path is False
    assert status.user_path_includes_script_dir is True


def test_get_windows_user_path_reads_registry_value() -> None:
    fake_winreg = FakeWinreg("C:\\Existing")

    assert get_windows_user_path(fake_winreg) == "C:\\Existing"


def test_windows_path_update_moves_script_dir_to_front_once(tmp_path: Path) -> None:
    fake_winreg = FakeWinreg("C:\\Existing")
    script_dir = tmp_path / "Python" / "Scripts"

    first = add_windows_user_path(script_dir, winreg_module=fake_winreg)
    second = add_windows_user_path(script_dir, winreg_module=fake_winreg)

    assert first.changed is True
    assert second.changed is False
    assert fake_winreg.path_value.startswith(f"{script_dir};")
    assert fake_winreg.path_value.count(str(script_dir)) == 1


def test_windows_path_update_repairs_priority_and_removes_duplicates(tmp_path: Path) -> None:
    script_dir = tmp_path / "Python" / "Scripts"
    fake_winreg = FakeWinreg(f"C:\\Earlier;{script_dir};C:\\Later;{script_dir}")

    result = add_windows_user_path(script_dir, winreg_module=fake_winreg)

    assert result.changed is True
    assert fake_winreg.path_value == f"{script_dir};C:\\Earlier;C:\\Later"


def test_windows_path_update_handles_missing_user_path(tmp_path: Path) -> None:
    fake_winreg = FakeWinreg("__missing__")
    script_dir = tmp_path / "Scripts"

    result = add_windows_user_path(script_dir, winreg_module=fake_winreg)

    assert result.changed is True
    assert fake_winreg.path_value == str(script_dir)


def test_unix_path_update_writes_profile_with_backup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    profile = tmp_path / ".zshrc"
    profile.write_text("# existing\n", encoding="utf-8")
    script_dir = tmp_path / "bin"
    monkeypatch.setenv("PATH", "/usr/bin")

    first = add_unix_user_path(script_dir, profile_path=profile)
    second = add_unix_user_path(script_dir, profile_path=profile)

    assert first.changed is True
    assert second.changed is False
    assert profile.with_name(".zshrc.bak").exists()
    content = profile.read_text(encoding="utf-8")
    assert "# ABET Converter PATH" in content
    assert f'export PATH="{script_dir}:$PATH"' in content
    assert content.count(str(script_dir)) == 1
