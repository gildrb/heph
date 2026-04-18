"""CLI parameter loading: TOML config merged with environment variables."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

from hephaistos.chat.engine import ChatConfig

_DEFAULTS_FILE = Path(__file__).parent / "default.toml"
_USER_CONFIG_DIR = Path.home() / ".config" / "hephaistos"
_USER_CONFIG_FILE = _USER_CONFIG_DIR / "config.json"


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


def _load_user_overrides() -> dict[str, str]:
    """Load persisted user config overrides from ``~/.config/hephaistos/config.json``."""
    if not _USER_CONFIG_FILE.is_file():
        return {}
    with contextlib.suppress(Exception):
        data = json.loads(_USER_CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k: str(v) for k, v in data.items() if k in _CONFIG_KEY_TO_ENV}
    return {}


def _save_user_override(key: str, value: str) -> None:
    """Persist a single config override to the user config file."""
    _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    overrides = _load_user_overrides()
    overrides[key] = value
    _USER_CONFIG_FILE.write_text(json.dumps(overrides, indent=2) + "\n", encoding="utf-8")


def load_config(armory_path: Path | None = None) -> ChatConfig:
    """Load ChatConfig from TOML defaults + provider config + user overrides + env vars.

    Priority: env vars > user config file > provider config > TOML file > ChatConfig defaults.
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

    # Apply persisted user overrides (higher priority than provider config).
    user_overrides = _load_user_overrides()
    if user_overrides.get("base_url"):
        config.base_url = user_overrides["base_url"]
    if user_overrides.get("model"):
        config.model = user_overrides["model"]
    if user_overrides.get("max_tokens"):
        with contextlib.suppress(ValueError):
            config.max_tokens = int(user_overrides["max_tokens"])
    if user_overrides.get("rag_context_budget"):
        with contextlib.suppress(ValueError):
            config.rag_context_budget = int(user_overrides["rag_context_budget"])
    if user_overrides.get("feature_flags"):
        config.feature_flags = _parse_feature_flags(user_overrides["feature_flags"])

    # Environment variables have the highest priority.
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

    feature_flags = os.environ.get("HEPHAISTOS_FEATURE_FLAGS")
    if feature_flags:
        config.feature_flags = _parse_feature_flags(feature_flags)

    return config


_CONFIG_KEY_TO_ENV = {
    "base_url": "HEPHAISTOS_BASE_URL",
    "model": "HEPHAISTOS_MODEL",
    "max_tokens": "HEPHAISTOS_MAX_TOKENS",
    "rag_context_budget": "HEPHAISTOS_RAG_CONTEXT_BUDGET",
    "feature_flags": "HEPHAISTOS_FEATURE_FLAGS",
}


def _parse_feature_flags(raw: str) -> frozenset[str]:
    """Parse comma-separated feature-flag slugs into a frozenset."""
    return frozenset(slug.strip().lower() for slug in raw.split(",") if slug.strip())


def _cmd_config_show(args: argparse.Namespace) -> None:
    """Display the current configuration."""
    config = load_config()
    print("Current configuration:")
    print(f"  base_url: {config.base_url or '(not set)'}")
    print(f"  model: {config.model or '(not set)'}")
    print(f"  max_tokens: {config.max_tokens}")
    print(f"  rag_context_budget: {config.rag_context_budget}")
    flags = ", ".join(sorted(config.feature_flags)) if config.feature_flags else "(none)"
    print(f"  feature_flags: {flags}")


def _cmd_config_set(args: argparse.Namespace) -> None:
    """Persist a configuration parameter to the user config file."""
    key = args.key
    value = args.value
    if key not in _CONFIG_KEY_TO_ENV:
        print(f"error: unknown config key '{key}'.", file=sys.stderr)
        print(
            f"  valid keys: {', '.join(_CONFIG_KEY_TO_ENV)}",
            file=sys.stderr,
        )
        sys.exit(1)
    _save_user_override(key, value)
    print(f"Set {key} = {value} (persisted to {_USER_CONFIG_FILE})")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register config subcommands."""
    config = subparsers.add_parser("config", help="View and set configuration values.")
    config_sub = config.add_subparsers(dest="config_command", required=True)

    show = config_sub.add_parser("show", help="Display current configuration.")
    show.set_defaults(handler=_cmd_config_show)

    set_cmd = config_sub.add_parser("set", help="Set a configuration parameter.")
    set_cmd.add_argument(
        "key", help="Config key (base_url, model, max_tokens, rag_context_budget, feature_flags)."
    )
    set_cmd.add_argument("value", help="Value to set.")
    set_cmd.set_defaults(handler=_cmd_config_set)
