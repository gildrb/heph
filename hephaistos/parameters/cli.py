"""CLI parameter loading: TOML defaults + persisted settings + environment."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path

from hephaistos.parameters import settings as settings_store
from hephaistos.providers.config import (
    ProviderConfig,
    default_config,
)
from hephaistos.runtime import ChatConfig, is_keyless_endpoint
from hephaistos.telemetry import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)

_DEFAULTS_FILE = settings_store._DEFAULTS_FILE  # type: ignore[reportPrivateUsage]
_USER_CONFIG_DIR = settings_store._USER_CONFIG_DIR  # type: ignore[reportPrivateUsage]
_USER_CONFIG_FILE = settings_store._USER_CONFIG_FILE  # type: ignore[reportPrivateUsage]


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


def _save_user_override(  # pyright: ignore[reportUnusedFunction]
    key: str, value: str
) -> None:
    settings_store.save_setting(key, value)


def load_config(armory_path: Path | None = None) -> ChatConfig:
    """Load ChatConfig from defaults + provider config + user overrides + env vars."""
    _ = armory_path
    config = ChatConfig()
    toml_path = settings_store._DEFAULTS_FILE  # type: ignore[reportPrivateUsage]
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
        pc = ProviderConfig.load()
        pc.apply_to_config(config)
        if (
            config.base_url
            and not is_keyless_endpoint(config.base_url)
            and not config.resolved_api_key
        ):
            print(
                f"warning: active provider '{config._provider_slug}' has no API key, "  # type: ignore[reportPrivateUsage]
                "falling back to Pollinations AI (free)",
                file=sys.stderr,
            )
            default_config().apply_to_config(config)
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
    "analytics_enabled": "HEPHAISTOS_ANALYTICS_ENABLED",
    "crash_reports_enabled": "HEPHAISTOS_CRASH_REPORTS_ENABLED",
    "supermemory_enabled": "",
    "supermemory_profile": "",
}

_BOOL_KEYS = {"analytics_enabled", "crash_reports_enabled", "supermemory_enabled"}


def _effective_setting_value(key: str) -> str:
    app_settings = settings_store.load_app_settings()
    if key == "theme":
        return app_settings.theme
    if key == "default_armory_path":
        return app_settings.default_armory_path or "(not set)"
    if key == "analytics_enabled":
        suffix = " (env override)" if analytics_env_override() else ""
        availability = "available" if analytics_backend_available() else "unavailable"
        return f"{str(analytics_enabled()).lower()}{suffix} [{availability}]"
    if key == "crash_reports_enabled":
        suffix = " (env override)" if crash_reports_env_override() else ""
        availability = "available" if crash_reports_backend_available() else "unavailable"
        return f"{str(crash_reports_enabled()).lower()}{suffix} [{availability}]"
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
    print(f"  analytics_enabled: {_display_setting_value('analytics_enabled')}")
    print(f"  crash_reports_enabled: {_display_setting_value('crash_reports_enabled')}")
    print(f"  supermemory_enabled: {_display_setting_value('supermemory_enabled')}")
    print(f"  supermemory_profile: {_display_setting_value('supermemory_profile')}")


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
            print(f"Set {key} = {normalized} (persisted to {settings_store._USER_CONFIG_FILE})")  # type: ignore[reportPrivateUsage]
            return
        settings_store.save_setting(key, value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Set {key} = {value} (persisted to {settings_store._USER_CONFIG_FILE})")  # type: ignore[reportPrivateUsage]


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # type: ignore[reportPrivateUsage]
    """Register config subcommands."""
    config = subparsers.add_parser("config", help="View and set configuration values.")
    config_sub = config.add_subparsers(dest="config_command", required=True)

    show = config_sub.add_parser("show", help="Display current configuration.")
    show.set_defaults(handler=_cmd_config_show)

    set_cmd = config_sub.add_parser("set", help="Set a configuration parameter.")
    set_cmd.add_argument(
        "key",
        help=(
            "Config key "
            "(base_url, model, max_tokens, rag_context_budget, feature_flags, theme, "
            "default_armory_path, analytics_enabled, crash_reports_enabled, "
            "supermemory_enabled, supermemory_profile)."
        ),
    )
    set_cmd.add_argument("value", help="Value to set.")
    set_cmd.set_defaults(handler=_cmd_config_set)
