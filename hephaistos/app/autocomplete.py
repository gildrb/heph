"""Slash command autocomplete suggestions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str
