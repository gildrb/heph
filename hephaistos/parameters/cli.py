"""CLI parameter loading: TOML config merged with environment variables."""

from __future__ import annotations

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
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Remove inline comments
        if value.startswith('"'):
            end = value.find('"', 1)
            if end != -1:
                value = value[1:end]
        else:
            # Unquoted value: strip trailing comment
            if "#" in value:
                value = value[: value.index("#")].strip()
        result[key] = value
    return result


def load_config(armory_path: Path | None = None) -> ChatConfig:
    """Load ChatConfig from TOML defaults + provider config + env overrides.

    Priority: env vars > provider config > TOML file > ChatConfig defaults.
    """
    config = ChatConfig()

    # Read TOML defaults
    toml_path = _DEFAULTS_FILE
    if toml_path.is_file():
        toml = _parse_toml_simple(toml_path)
        if toml.get("base_url"):
            config.base_url = toml["base_url"]
        if toml.get("model_id"):
            config.model = toml["model_id"]
        if toml.get("max_tokens"):
            try:
                config.max_tokens = int(toml["max_tokens"])
            except ValueError:
                pass

    # Apply provider config (overrides TOML defaults)
    try:
        from hephaistos.providers.config import ProviderConfig

        pc = ProviderConfig.load()
        pc.apply_to_config(config)
    except Exception as exc:
        import sys
        print(f"warning: could not load provider config: {exc}", file=sys.stderr)

    # Environment variable overrides (highest priority for non-key settings)
    api_key = os.environ.get("HEPHAISTOS_API_KEY") or os.environ.get(
        "OPENAI_API_KEY", ""
    )
    # Do NOT store raw key in config.api_key. The resolved_api_key property
    # will pick it up from env vars at call time.
    # We only set api_key field for backward-compat tests that check it directly.
    # Real code should use config.resolved_api_key.
    if api_key:
        config.api_key = "(env)"  # sentinel — actual key resolved lazily

    base_url = os.environ.get("HEPHAISTOS_BASE_URL")
    if base_url:
        config.base_url = base_url

    model = os.environ.get("HEPHAISTOS_MODEL")
    if model:
        config.model = model

    max_tokens = os.environ.get("HEPHAISTOS_MAX_TOKENS")
    if max_tokens:
        try:
            config.max_tokens = int(max_tokens)
        except ValueError:
            pass

    rag_context_budget = os.environ.get("HEPHAISTOS_RAG_CONTEXT_BUDGET")
    if rag_context_budget:
        try:
            config.rag_context_budget = int(rag_context_budget)
        except ValueError:
            pass

    return config


def register() -> None:
    """Register CLI commands (placeholder for future CLI hooks)."""
    pass
