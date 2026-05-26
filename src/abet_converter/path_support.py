from __future__ import annotations

import os
import platform
import shutil
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abet_converter import __version__


WINDOWS_PATH_SEPARATOR = ";"
UNIX_PATH_SEPARATOR = ":"
ABET_PATH_BLOCK_START = "# ABET Converter PATH"
ABET_PATH_BLOCK_END = "# End ABET Converter PATH"


@dataclass(frozen=True)
class PathStatus:
    python_executable: Path
    package_version: str
    script_dir: Path
    script_dir_in_path: bool
    repair_command: str


@dataclass(frozen=True)
class PathUpdateResult:
    changed: bool
    message: str
    target: Path | str


def get_script_dir() -> Path:
    return Path(sysconfig.get_path("scripts")).resolve()


def path_contains(directory: Path, path_value: str | None = None, *, path_separator: str | None = None) -> bool:
    value = os.environ.get("PATH", "") if path_value is None else path_value
    separator = os.pathsep if path_separator is None else path_separator
    target = _normalize_path_for_compare(directory)
    for entry in value.split(separator):
        if entry and _normalize_path_for_compare(Path(entry)) == target:
            return True
    return False


def build_path_status(path_value: str | None = None) -> PathStatus:
    script_dir = get_script_dir()
    return PathStatus(
        python_executable=Path(sys.executable).resolve(),
        package_version=__version__,
        script_dir=script_dir,
        script_dir_in_path=path_contains(script_dir, path_value),
        repair_command=f"{sys.executable} -m abet_converter path --add",
    )


def format_doctor(status: PathStatus | None = None) -> str:
    current = build_path_status() if status is None else status
    lines = [
        "ABET Converter installation check",
        f"Version: {current.package_version}",
        f"Python: {current.python_executable}",
        f"Script directory: {current.script_dir}",
        f"Script directory on PATH: {'yes' if current.script_dir_in_path else 'no'}",
    ]
    if current.script_dir_in_path:
        lines.append("The abet-converter command should be available in a new terminal.")
    else:
        lines.append("To repair PATH, run:")
        lines.append(f"  {current.repair_command}")
        lines.append("Open a new terminal after repairing PATH.")
    return "\n".join(lines)


def format_path_show(status: PathStatus | None = None) -> str:
    current = build_path_status() if status is None else status
    return "\n".join(
        [
            f"Script directory: {current.script_dir}",
            f"Script directory on PATH: {'yes' if current.script_dir_in_path else 'no'}",
        ]
    )


def add_script_dir_to_user_path(script_dir: Path | None = None) -> PathUpdateResult:
    target = get_script_dir() if script_dir is None else script_dir.resolve()
    if sys.platform.startswith("win"):
        return add_windows_user_path(target)
    return add_unix_user_path(target)


def add_windows_user_path(script_dir: Path, winreg_module: Any | None = None) -> PathUpdateResult:
    winreg = _import_winreg(winreg_module)
    key_path = "Environment"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            current_path, value_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""
            value_type = getattr(winreg, "REG_EXPAND_SZ", getattr(winreg, "REG_SZ", 1))
        if path_contains(script_dir, current_path, path_separator=WINDOWS_PATH_SEPARATOR):
            return PathUpdateResult(False, "Script directory is already present in the user PATH.", "HKCU\\Environment\\Path")
        next_path = _append_path_entry(current_path, script_dir, WINDOWS_PATH_SEPARATOR)
        winreg.SetValueEx(key, "Path", 0, value_type, next_path)
    return PathUpdateResult(
        True,
        "Added script directory to the user PATH. Open a new terminal before running abet-converter.",
        "HKCU\\Environment\\Path",
    )


def add_unix_user_path(script_dir: Path, profile_path: Path | None = None) -> PathUpdateResult:
    profile = _choose_unix_profile() if profile_path is None else profile_path
    existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
    if str(script_dir) in existing:
        return PathUpdateResult(False, "Script directory is already present in the shell profile.", profile)

    if profile.exists():
        backup = profile.with_name(f"{profile.name}.bak")
        shutil.copy2(profile, backup)
    profile.parent.mkdir(parents=True, exist_ok=True)
    block = "\n".join(
        [
            ABET_PATH_BLOCK_START,
            f'export PATH="{script_dir}:$PATH"',
            ABET_PATH_BLOCK_END,
        ]
    )
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    profile.write_text(f"{existing}{prefix}{block}\n", encoding="utf-8")
    return PathUpdateResult(True, f"Added script directory to {profile}. Restart your shell before running abet-converter.", profile)


def _choose_unix_profile() -> Path:
    explicit = os.environ.get("ABET_CONVERTER_SHELL_PROFILE")
    if explicit:
        return Path(explicit).expanduser()

    home = Path.home()
    shell_name = Path(os.environ.get("SHELL", "")).name
    if shell_name == "zsh":
        return home / ".zshrc"
    if shell_name == "bash":
        bashrc = home / ".bashrc"
        return bashrc if bashrc.exists() else home / ".profile"
    return home / ".profile"


def _import_winreg(winreg_module: Any | None) -> Any:
    if winreg_module is not None:
        return winreg_module
    if not platform.system().lower().startswith("win"):
        raise RuntimeError("Windows PATH repair is only available on Windows.")
    import winreg

    return winreg


def _append_path_entry(path_value: str, directory: Path, separator: str) -> str:
    if not path_value:
        return str(directory)
    return f"{path_value.rstrip(separator)}{separator}{directory}"


def _normalize_path_for_compare(path: Path) -> str:
    value = os.path.normpath(os.path.expandvars(os.path.expanduser(str(path))))
    if sys.platform.startswith("win"):
        return os.path.normcase(value)
    return value
