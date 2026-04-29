"""Inline menu helpers for TTY workflows.

Selection flows render directly into the current terminal stream so they feel
like part of the shell rather than a separate full-screen mode.

The implementation lives in ``hephaistos.terminal``; this module re-exports
for backward compatibility within the ``app`` package.
"""

from __future__ import annotations

from hephaistos.terminal import (  # noqa: F401 — re-exports for backward compat
    MenuOption,
    browse_directory,
    confirm,
    select_option,
)
