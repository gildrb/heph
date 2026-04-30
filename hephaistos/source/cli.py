"""Compatibility CLI registration for the legacy ``source`` namespace."""

from __future__ import annotations

import argparse

from hephaistos.materials.cli import register_source_alias


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
) -> None:
    """Register source subcommands as aliases for materials commands."""
    register_source_alias(subparsers)
