"""Command suggestion data shared by command registry and adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str
    aliases: tuple[str, ...] = ()
