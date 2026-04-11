"""CLI parameter loading: TOML config merged with environment variables."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

from hephaistos.chat.engine import ChatConfig

_DEFAULTS_FILE = Path(__file__).parent / "default.toml"


def _parse_toml_simple(path: Path) -> dict[str, str]:
    """Minimal TOML parser for flat key=value files.

    Handles strings (quoted), integers, floats, and booleans.
    Skips comments and blank lines.
    """
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "[")):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value.startswith('"'):
            end = value.find('"', 1)
            if end != -1:
                value = value[1:end]
        elif "#" in value:
            value = value[: value.index("#")].strip()
        result[key] = value
    return result


def load_config(armory_path: Path | None = None) -> ChatConfig:
    """Load ChatConfig from TOML defaults + provider config + env overrides.

    Priority: env vars > provider config > TOML file > ChatConfig defaults.
    """
    config = ChatConfig()
    toml_path = _DEFAULTS_FILE
    if toml_path.is_file():
        toml = _parse_toml_simple(toml_path)
        if toml.get("base_url"):
            config.base_url = toml["base_url"]
        if toml.get("model_id"):
            config.model = toml["model_id"]
        if toml.get("max_tokens"):
            with contextlib.suppress(ValueError):
                config.max_tokens = int(toml["max_tokens"])
    try:
        from hephaistos.providers.config import ProviderConfig

        pc = ProviderConfig.load()
        pc.apply_to_config(config)
    except Exception as exc:
        import sys

        print(f"warning: could not load provider config: {exc}", file=sys.stderr)

    base_url = os.environ.get("HEPHAISTOS_BASE_URL")
    if base_url:
        config.base_url = base_url

    model = os.environ.get("HEPHAISTOS_MODEL")
    if model:
        config.model = model

    max_tokens = os.environ.get("HEPHAISTOS_MAX_TOKENS")
    if max_tokens:
        with contextlib.suppress(ValueError):
            config.max_tokens = int(max_tokens)

    rag_context_budget = os.environ.get("HEPHAISTOS_RAG_CONTEXT_BUDGET")
    if rag_context_budget:
        with contextlib.suppress(ValueError):
            config.rag_context_budget = int(rag_context_budget)

    return config


def register() -> None:
    """Register CLI commands (placeholder for future CLI hooks)."""
