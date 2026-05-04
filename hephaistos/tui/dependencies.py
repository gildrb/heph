"""Optional Textual/Rich dependency helpers for the TUI adapter."""

from __future__ import annotations

import sys


class TuiDependencyError(RuntimeError):
    """Raised when the optional Textual dependency group is missing."""


def tui_dependency_message() -> str:
    return (
        "Textual UI dependencies are not available in this Python environment.\n"
        f"Current Python: {sys.executable}\n"
        "From a source checkout, sync dependencies from the repository root:\n"
        "  uv sync --frozen\n"
        "For an installed or editable `heph` entrypoint, reinstall Hephaistos "
        "into that same Python environment from the repository root:\n"
        f"  {sys.executable} -m pip install -e ."
    )
