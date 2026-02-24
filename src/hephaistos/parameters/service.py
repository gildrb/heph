"""Parameter feature use-cases."""

from __future__ import annotations

from hephaistos.parameters.store import build_profile


def list_parameters() -> str:
    """Placeholder list flow."""
    return "[todo] parameters list"


def set_parameter(key: str, value: str) -> str:
    """Placeholder set flow."""
    return f"[todo] parameters set {key}={value}"


def save_parameters(name: str) -> str:
    """Placeholder save flow."""
    profile = build_profile(name)
    return f"[todo] parameters save name={profile.name}"

