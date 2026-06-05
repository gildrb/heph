"""Frontend-neutral command-line entrypoint for Heph."""

from __future__ import annotations

from heph.cli.main import build_parser, main, run_argv

__all__ = ["build_parser", "main", "run_argv"]
