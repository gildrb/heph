"""Parameter profile storage placeholders."""

from __future__ import annotations

from hephaistos.parameters.types import ParameterProfile


def build_profile(name: str) -> ParameterProfile:
    """Build a profile object from a name."""
    return ParameterProfile(name=name)

