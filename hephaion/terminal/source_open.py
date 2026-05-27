from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceOpenResult:
    path: Path
    line: int | None
    used_line: bool

    @property
    def message(self) -> str:
        if self.line is None:
            return f"Opened {self.path}"
        if self.used_line:
            return f"Opened {self.path}:{self.line}"
        return f"Opened {self.path} (target line {self.line})"


def _editor_command(editor: str, path: Path, line: int | None) -> tuple[list[str], bool]:
    parts = shlex.split(editor)
    if not parts:
        return [str(path)], False
    executable = Path(parts[0]).name.lower()
    if line is None:
        return [*parts, str(path)], False
    if executable in {"code", "codium", "cursor", "windsurf"}:
        return [*parts, "-g", f"{path}:{line}"], True
    if executable in {"vim", "nvim", "vi", "nano", "emacs", "micro"}:
        return [*parts, f"+{line}", str(path)], True
    if executable in {"hx", "helix"}:
        return [*parts, f"{path}:{line}"], True
    return [*parts, str(path)], False


def _system_open_command(path: Path) -> list[str]:
    if sys.platform == "darwin":
        return ["open", str(path)]
    if sys.platform.startswith("linux"):
        return ["xdg-open", str(path)]
    if os.name == "nt":
        return ["cmd", "/c", "start", "", str(path)]
    return [str(path)]


def open_source_file(path: Path, line: int | None = None) -> SourceOpenResult:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        command, used_line = _editor_command(editor, path, line)
    else:
        command = _system_open_command(path)
        used_line = False
    subprocess.Popen(command)
    return SourceOpenResult(path=path, line=line, used_line=used_line)
