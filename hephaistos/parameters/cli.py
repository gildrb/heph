"""CLI parameter loading: TOML defaults + persisted settings + environment."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos.parameters import settings as settings_store

if TYPE_CHECKING:
    from hephaistos.runtime import ChatConfig

_DEFAULTS_FILE = settings_store._DEFAULTS_FILE
_USER_CONFIG_DIR = settings_store._USER_CONFIG_DIR
_USER_CONFIG_FILE = settings_store._USER_CONFIG_FILE


def _parse_toml_simple(path: Path) -> dict[str, str]:
    return settings_store.parse_toml_simple(path)


def _parse_feature_flags(raw: str) -> frozenset[str]:
    return settings_store.parse_feature_flags(raw)


def _load_user_overrides() -> dict[str, str]:
    raw = settings_store.load_raw_settings()
    result: dict[str, str] = {}
    for key, value in raw.items():
        if key not in _CONFIG_KEY_TO_ENV:
            continue
        result[str(key)] = str(value)
    return result


def _save_user_override(key: str, value: str) -> None:
    settings_store.save_setting(key, value)


def load_config(armory_path: Path | None = None) -> ChatConfig:
    """Load ChatConfig from defaults + provider config + user overrides + env vars."""
    providers_config = importlib.import_module("hephaistos.providers.config")
    runtime = importlib.import_module("hephaistos.runtime")

    _ = armory_path
    config = runtime.ChatConfig()
    toml_path = settings_store._DEFAULTS_FILE
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
        pc = providers_config.ProviderConfig.load()
        pc.apply_to_config(config)
        if (
            config.base_url
            and not runtime.is_keyless_endpoint(config.base_url)
            and not config.resolved_api_key
        ):
            print(
                f"warning: active provider '{config._provider_slug}' has no API key, "
                "falling back to Pollinations AI (free)",
                file=sys.stderr,
            )
            providers_config.default_config().apply_to_config(config)
    except Exception as exc:
        print(f"warning: could not load provider config: {exc}", file=sys.stderr)

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
    "theme": "",
    "default_armory_path": "",
    "interface_mode": "",
    "analytics_enabled": "HEPHAISTOS_ANALYTICS_ENABLED",
    "crash_reports_enabled": "HEPHAISTOS_CRASH_REPORTS_ENABLED",
    "supermemory_enabled": "",
    "supermemory_profile": "",
}

_BOOL_KEYS = {"analytics_enabled", "crash_reports_enabled", "supermemory_enabled"}
_SETTING_DESCRIPTIONS = {
    "base_url": "OpenAI-compatible API base URL",
    "model": "Model identifier",
    "max_tokens": "Maximum response tokens",
    "rag_context_budget": "Retrieval context token budget",
    "feature_flags": "Comma-separated feature flags",
    "theme": "TUI theme preset",
    "default_armory_path": "Startup armory fallback path",
    "interface_mode": "Interface mode",
    "analytics_enabled": "Anonymous usage analytics opt-in",
    "crash_reports_enabled": "Redacted crash reporting opt-in",
    "supermemory_enabled": "Supermemory sync opt-in",
    "supermemory_profile": "Supermemory profile name",
}


def _effective_setting_value(key: str) -> str:
    privacy = importlib.import_module("hephaistos.privacy.consent")

    app_settings = settings_store.load_app_settings()
    if key == "theme":
        return app_settings.theme
    if key == "default_armory_path":
        return app_settings.default_armory_path or "(not set)"
    if key == "interface_mode":
        return app_settings.interface_mode
    if key == "analytics_enabled":
        suffix = " (env override)" if privacy.analytics_env_override() else ""
        availability = "available" if privacy.analytics_backend_available() else "unavailable"
        return f"{str(privacy.analytics_enabled()).lower()}{suffix} [{availability}]"
    if key == "crash_reports_enabled":
        suffix = " (env override)" if privacy.crash_reports_env_override() else ""
        avail = "available" if privacy.crash_reports_backend_available() else "unavailable"
        return f"{str(privacy.crash_reports_enabled()).lower()}{suffix} [{avail}]"
    if key == "supermemory_enabled":
        return str(app_settings.supermemory_enabled).lower()
    if key == "supermemory_profile":
        return app_settings.supermemory_profile
    return "(not set)"


def _display_setting_value(key: str) -> str:
    try:
        return _effective_setting_value(key)
    except KeyError:
        return "(not set)"


def _cmd_config_show(_args: argparse.Namespace) -> None:
    config = load_config()
    print("Current configuration:")
    print(f"  base_url: {config.base_url or '(not set)'}")
    print(f"  model: {config.model or '(not set)'}")
    print(f"  max_tokens: {config.max_tokens}")
    print(f"  rag_context_budget: {config.rag_context_budget}")
    flags = ", ".join(sorted(config.feature_flags)) if config.feature_flags else "(none)"
    print(f"  feature_flags: {flags}")
    print(f"  theme: {_display_setting_value('theme')}")
    print(f"  default_armory_path: {_display_setting_value('default_armory_path')}")
    print(f"  interface_mode: {_display_setting_value('interface_mode')}")
    print(f"  analytics_enabled: {_display_setting_value('analytics_enabled')}")
    print(f"  crash_reports_enabled: {_display_setting_value('crash_reports_enabled')}")
    print(f"  supermemory_enabled: {_display_setting_value('supermemory_enabled')}")
    print(f"  supermemory_profile: {_display_setting_value('supermemory_profile')}")


def _cmd_config_list(_args: argparse.Namespace) -> None:
    print("Configurable settings:")
    for key, env in _CONFIG_KEY_TO_ENV.items():
        env_text = f" env: {env}" if env else ""
        print(f"  {key}: {_SETTING_DESCRIPTIONS[key]}{env_text}")


def _cmd_config_path(_args: argparse.Namespace) -> None:
    print(settings_store._USER_CONFIG_FILE)


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
    path_cmd.set_defaults(handler=_cmd_config_path)

    set_cmd = config_sub.add_parser("set", help="Set a configuration parameter.")
    set_cmd.add_argument(
        "key",
        help=(
            "Config key "
            "(base_url, model, max_tokens, rag_context_budget, feature_flags, theme, "
            "default_armory_path, interface_mode, analytics_enabled, "
            "crash_reports_enabled, supermemory_enabled, supermemory_profile)."
        ),
    )
    set_cmd.add_argument("value", help="Value to set.")
    set_cmd.set_defaults(handler=_cmd_config_set)

    unset_cmd = config_sub.add_parser("unset", help="Remove a persisted configuration value.")
    unset_cmd.add_argument("key", help="Config key to remove.")
    unset_cmd.set_defaults(handler=_cmd_config_unset)
