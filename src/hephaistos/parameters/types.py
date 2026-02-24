"""Types for model parameters feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterProfile:
    """Named parameter profile."""

    name: str

