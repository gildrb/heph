"""CLI parameter loading: TOML defaults + persisted settings + environment."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Mapping
from pathlib import Path

from ai.providers.config import ProviderConfig, default_config
from ai.runtime import (
    ChatConfig,
    has_configured_access,
    is_keyless_endpoint,
    normalize_thinking_visibility,
)

from harness.parameters import settings as settings_store


def _load_user_overrides() -> dict[str, str]:
    raw = settings_store.load_raw_settings()
    result: dict[str, str] = {}
    for key, value in raw.items():
        if key not in _CONFIG_KEY_TO_ENV:
            continue
        result[str(key)] = str(value)
    return result


def load_config(armory_path: Path | None = None) -> ChatConfig:
    """Load ChatConfig from defaults + provider config + user overrides + env vars."""
    _ = armory_path
    config = ChatConfig()
    _apply_toml_defaults(config)
    _apply_provider_config(config)
    _apply_mapping_overrides(config, _load_user_overrides())
    _apply_mapping_overrides(config, _env_overrides())
    return config


def _apply_toml_defaults(config: ChatConfig) -> None:
    toml_path = settings_store._DEFAULTS_FILE
    if not toml_path.is_file():
        return

    toml = settings_store.parse_toml_simple(toml_path)
    if base_url := toml.get("base_url"):
        config.base_url = base_url
    if model_id := toml.get("model_id"):
        config.model = model_id
    _apply_int_override(config, "max_tokens", toml.get("max_tokens"))
    _apply_float_override(config, "temperature", toml.get("temperature"))


def _apply_provider_config(config: ChatConfig) -> None:
    try:
        pc = ProviderConfig.load()
        pc.apply_to_config(config)
        if (
            config.base_url
            and not is_keyless_endpoint(config.base_url)
            and not has_configured_access(config)
        ):
            print(
                f"warning: active provider '{config._provider_slug}' has no API key, "
                "falling back to Pollinations AI (free)",
                file=sys.stderr,
            )
            default_config().apply_to_config(config)
    except Exception as exc:
        print(f"warning: could not load provider config: {exc}", file=sys.stderr)


def _apply_mapping_overrides(config: ChatConfig, values: Mapping[str, str]) -> None:
    if base_url := values.get("base_url"):
        config.base_url = base_url
    if model := values.get("model"):
        config.model = model
    _apply_int_override(config, "max_tokens", values.get("max_tokens"))
    _apply_int_override(config, "rag_context_budget", values.get("rag_context_budget"))
    _apply_float_override(config, "temperature", values.get("temperature"))
    if feature_flags := values.get("feature_flags"):
        config.feature_flags = settings_store.parse_feature_flags(feature_flags)
    if thinking_visibility := values.get("thinking_visibility"):
        config.thinking_visibility = normalize_thinking_visibility(thinking_visibility)


def _apply_int_override(config: ChatConfig, field_name: str, value: str | None) -> None:
    if value:
        with contextlib.suppress(ValueError):
            parsed = int(value)
            if field_name == "max_tokens":
                config.max_tokens = parsed
            elif field_name == "rag_context_budget":
                config.rag_context_budget = parsed


def _apply_float_override(config: ChatConfig, field_name: str, value: str | None) -> None:
    if value is None:
        return
    with contextlib.suppress(ValueError):
        parsed = float(value)
        if field_name == "temperature":
            config.temperature = min(2.0, max(0.0, parsed))


def _env_overrides() -> dict[str, str]:
    result: dict[str, str] = {}
    for key, env_name in _CONFIG_KEY_TO_ENV.items():
        if not env_name:
            continue
        value = os.environ.get(env_name)
        if value:
            result[key] = value
    return result


_CONFIG_KEY_TO_ENV = {
    "base_url": "HARNESS_BASE_URL",
    "model": "HARNESS_MODEL",
    "max_tokens": "HARNESS_MAX_TOKENS",
    "rag_context_budget": "HARNESS_RAG_CONTEXT_BUDGET",
    "temperature": "HARNESS_TEMPERATURE",
    "feature_flags": "HARNESS_FEATURE_FLAGS",
    "theme": "",
    "default_armory_path": "",
    "activity_trace_mode": "",
    "thinking_visibility": "",
    "live_tokens_visible": "",
    "live_cost_visible": "",
}

_BOOL_KEYS = {
    "live_tokens_visible",
    "live_cost_visible",
}
_SETTING_DESCRIPTIONS = {
    "base_url": "OpenAI-compatible API base URL",
    "model": "Model identifier",
    "max_tokens": "Maximum response tokens",
    "rag_context_budget": "Retrieval context token budget",
    "temperature": "Model sampling temperature",
    "feature_flags": "Comma-separated feature flags",
    "theme": "TUI theme preset",
    "default_armory_path": "Startup armory fallback path",
    "activity_trace_mode": "Live activity trace verbosity",
    "thinking_visibility": "Model thinking visibility: off, minimal, or all",
    "live_tokens_visible": "Show token estimates in the TUI status bar",
    "live_cost_visible": "Show cost estimates in the TUI status bar",
}


def _effective_setting_value(key: str) -> str:
    app_settings = settings_store.load_app_settings()
    app_value = {
        "theme": app_settings.theme,
        "default_armory_path": app_settings.default_armory_path or "(not set)",
        "activity_trace_mode": app_settings.activity_trace_mode,
        "thinking_visibility": app_settings.thinking_visibility,
        "live_tokens_visible": str(app_settings.live_tokens_visible).lower(),
        "live_cost_visible": str(app_settings.live_cost_visible).lower(),
    }.get(key)
    if app_value is not None:
        return app_value
    return "(not set)"


def _cmd_config_show(_args: argparse.Namespace) -> None:
    config = load_config()
    print("Current configuration:")
    print(f"  base_url: {config.base_url or '(not set)'}")
    print(f"  model: {config.model or '(not set)'}")
    print(f"  max_tokens: {config.max_tokens}")
    print(f"  rag_context_budget: {config.rag_context_budget}")
    print(f"  temperature: {config.temperature}")
    flags = ", ".join(sorted(config.feature_flags)) if config.feature_flags else "(none)"
    print(f"  feature_flags: {flags}")
    print(f"  theme: {_effective_setting_value('theme')}")
    print(f"  default_armory_path: {_effective_setting_value('default_armory_path')}")
    print(f"  activity_trace_mode: {_effective_setting_value('activity_trace_mode')}")
    print(f"  thinking_visibility: {_effective_setting_value('thinking_visibility')}")
    print(f"  live_tokens_visible: {_effective_setting_value('live_tokens_visible')}")
    print(f"  live_cost_visible: {_effective_setting_value('live_cost_visible')}")


def _cmd_config_list(_args: argparse.Namespace) -> None:
    print("Configurable settings:")
    for key, env in _CONFIG_KEY_TO_ENV.items():
        env_text = f" env: {env}" if env else ""
        print(f"  {key}: {_SETTING_DESCRIPTIONS[key]}{env_text}")


def _cmd_config_set(args: argparse.Namespace) -> None:
    key = args.key
    value = args.value
    if key not in _CONFIG_KEY_TO_ENV:
        print(f"error: unknown config key '{key}'.", file=sys.stderr)
        print(f"  valid keys: {', '.join(_CONFIG_KEY_TO_ENV)}", file=sys.stderr)
        sys.exit(1)

    try:
        if key in _BOOL_KEYS:
            settings_store.save_setting(key, value)
            normalized = str(getattr(settings_store.load_app_settings(), key)).lower()
            print(f"Set {key} = {normalized} (persisted to {settings_store._USER_CONFIG_FILE})")
            return
        settings_store.save_setting(key, value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Set {key} = {value} (persisted to {settings_store._USER_CONFIG_FILE})")


def _cmd_config_unset(args: argparse.Namespace) -> None:
    key = args.key
    if key not in _CONFIG_KEY_TO_ENV:
        print(f"error: unknown config key '{key}'.", file=sys.stderr)
        print(f"  valid keys: {', '.join(_CONFIG_KEY_TO_ENV)}", file=sys.stderr)
        sys.exit(1)
    settings_store.clear_setting(key)
    print(f"Unset {key} (persisted to {settings_store._USER_CONFIG_FILE})")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register config subcommands."""
    config = subparsers.add_parser("config", help="View and set configuration values.")
    config_sub = config.add_subparsers(dest="config_command", required=True)

    show = config_sub.add_parser("show", help="Display current configuration.")
    show.set_defaults(handler=_cmd_config_show)

    list_cmd = config_sub.add_parser("list", help="List configurable settings.")
    list_cmd.set_defaults(handler=_cmd_config_list)

    path_cmd = config_sub.add_parser("path", help="Print the persistent config file path.")
    path_cmd.set_defaults(handler=lambda _args: print(settings_store._USER_CONFIG_FILE))

    set_cmd = config_sub.add_parser("set", help="Set a configuration parameter.")
    set_cmd.add_argument(
        "key",
        help=f"Config key ({', '.join(_CONFIG_KEY_TO_ENV)}).",
    )
    set_cmd.add_argument("value", help="Value to set.")
    set_cmd.set_defaults(handler=_cmd_config_set)

    unset_cmd = config_sub.add_parser("unset", help="Remove a persisted configuration value.")
    unset_cmd.add_argument("key", help="Config key to remove.")
    unset_cmd.set_defaults(handler=_cmd_config_unset)
