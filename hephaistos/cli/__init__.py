"""Frontend-neutral command-line entrypoint for Hephaistos."""

from __future__ import annotations

from hephaistos.cli.main import build_parser, main, run_argv

__all__ = ["build_parser", "main", "run_argv"]
