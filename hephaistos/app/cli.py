"""Compatibility exports for the canonical CLI entrypoint.

The canonical CLI lives in :mod:`hephaistos.cli.main`.  The Textual app remains
under :mod:`hephaistos.app`, but command routing is intentionally outside the
frontend package so automation does not depend on the TUI architecture.
"""

from __future__ import annotations

import sys

from hephaistos.cli.main import (
    HephaistosArgumentParser,
    _get_subcommand_names,  # pyright: ignore[reportPrivateUsage]
    _inject_default_subcommand,  # pyright: ignore[reportPrivateUsage]
    _normalise_tui_alias,  # pyright: ignore[reportPrivateUsage]
    _report_memory,  # pyright: ignore[reportPrivateUsage]
    _report_profile,  # pyright: ignore[reportPrivateUsage]
    build_parser,
    main,
    run_argv,
)

__all__ = [
    "HephaistosArgumentParser",
    "_get_subcommand_names",
    "_inject_default_subcommand",
    "_normalise_tui_alias",
    "_report_memory",
    "_report_profile",
    "build_parser",
    "main",
    "run_argv",
    "sys",
]
