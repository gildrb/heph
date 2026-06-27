"""Structured SDK settings snapshots for native clients."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from harness.parameters.settings import (
    ACTIVITY_TRACE_LABELS,
    ACTIVITY_TRACE_MODES,
    THEME_LABELS,
    THEME_PRESETS,
    THINKING_VISIBILITY_LABELS,
    THINKING_VISIBILITY_MODES,
    VOCAB_STRICTNESS_LABELS,
    VOCAB_STRICTNESS_MODES,
    AppSettings,
    load_app_settings,
    load_raw_settings,
    normalize_setting_value,
    save_raw_settings,
)
from harness.privacy.consent import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)


@dataclass(frozen=True, slots=True)
class SdkAppSettingContract:
    name: str
    value_type: str
    choices: tuple[str, ...] = ()


SDK_APP_SETTING_CONTRACTS = (
    SdkAppSettingContract("theme", "string", THEME_PRESETS),
    SdkAppSettingContract("default_armory_path", "string"),
    SdkAppSettingContract("activity_trace_mode", "string", ACTIVITY_TRACE_MODES),
    SdkAppSettingContract("vocab_strictness", "string", VOCAB_STRICTNESS_MODES),
    SdkAppSettingContract("thinking_visibility", "string", THINKING_VISIBILITY_MODES),
    SdkAppSettingContract("live_tokens_visible", "boolean"),
    SdkAppSettingContract("live_cost_visible", "boolean"),
)
SDK_MUTABLE_APP_SETTINGS = tuple(contract.name for contract in SDK_APP_SETTING_CONTRACTS)
_SDK_MUTABLE_APP_SETTINGS = frozenset(SDK_MUTABLE_APP_SETTINGS)
SDK_APP_SETTING_VALUE_TYPES = tuple(
    (contract.name, contract.value_type) for contract in SDK_APP_SETTING_CONTRACTS
)
_STRING_APP_SETTINGS = frozenset(
    name for name, value_type in SDK_APP_SETTING_VALUE_TYPES if value_type == "string"
)
_BOOL_APP_SETTINGS = frozenset(
    name for name, value_type in SDK_APP_SETTING_VALUE_TYPES if value_type == "boolean"
)


class SdkSettingsError(ValueError):
    """Raised when an SDK settings update is not supported or valid."""


@dataclass(frozen=True, slots=True)
class SettingChoice:
    value: str
    label: str

    def to_dict(self) -> dict[str, object]:
        return {"value": self.value, "label": self.label}


@dataclass(frozen=True, slots=True)
class SettingsChoices:
    themes: tuple[SettingChoice, ...]
    activity_trace_modes: tuple[SettingChoice, ...]
    thinking_visibility_modes: tuple[SettingChoice, ...]
    vocab_strictness_modes: tuple[SettingChoice, ...]

    @classmethod
    def current(cls) -> SettingsChoices:
        return cls(
            themes=_setting_choices(THEME_PRESETS, THEME_LABELS),
            activity_trace_modes=_setting_choices(ACTIVITY_TRACE_MODES, ACTIVITY_TRACE_LABELS),
            thinking_visibility_modes=_setting_choices(
                THINKING_VISIBILITY_MODES,
                THINKING_VISIBILITY_LABELS,
            ),
            vocab_strictness_modes=_setting_choices(
                VOCAB_STRICTNESS_MODES,
                VOCAB_STRICTNESS_LABELS,
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "themes": [choice.to_dict() for choice in self.themes],
            "activity_trace_modes": [choice.to_dict() for choice in self.activity_trace_modes],
            "thinking_visibility_modes": [
                choice.to_dict() for choice in self.thinking_visibility_modes
            ],
            "vocab_strictness_modes": [choice.to_dict() for choice in self.vocab_strictness_modes],
        }


@dataclass(frozen=True, slots=True)
class PrivacySettingsSummary:
    analytics_enabled: bool
    analytics_available: bool
    analytics_env_override: bool
    crash_reports_enabled: bool
    crash_reports_available: bool
    crash_reports_env_override: bool

    @classmethod
    def current(cls) -> PrivacySettingsSummary:
        return cls(
            analytics_enabled=analytics_enabled(),
            analytics_available=analytics_backend_available(),
            analytics_env_override=analytics_env_override(),
            crash_reports_enabled=crash_reports_enabled(),
            crash_reports_available=crash_reports_backend_available(),
            crash_reports_env_override=crash_reports_env_override(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "analytics_enabled": self.analytics_enabled,
            "analytics_available": self.analytics_available,
            "analytics_env_override": self.analytics_env_override,
            "crash_reports_enabled": self.crash_reports_enabled,
            "crash_reports_available": self.crash_reports_available,
            "crash_reports_env_override": self.crash_reports_env_override,
        }


@dataclass(frozen=True, slots=True)
class SdkAppSettings:
    theme: str
    default_armory_path: str
    last_armory_path: str
    activity_trace_mode: str
    vocab_strictness: str
    thinking_visibility: str
    live_tokens_visible: bool
    live_cost_visible: bool
    privacy: PrivacySettingsSummary
    choices: SettingsChoices
    mutable_keys: tuple[str, ...] = SDK_MUTABLE_APP_SETTINGS

    @classmethod
    def from_app_settings(cls, settings: AppSettings) -> SdkAppSettings:
        return cls(
            theme=settings.theme,
            default_armory_path=settings.default_armory_path,
            last_armory_path=settings.last_armory_path,
            activity_trace_mode=settings.activity_trace_mode,
            vocab_strictness=settings.vocab_strictness,
            thinking_visibility=settings.thinking_visibility,
            live_tokens_visible=settings.live_tokens_visible,
            live_cost_visible=settings.live_cost_visible,
            privacy=PrivacySettingsSummary.current(),
            choices=SettingsChoices.current(),
        )

    @classmethod
    def load(cls) -> SdkAppSettings:
        return cls.from_app_settings(load_app_settings())

    def to_dict(self) -> dict[str, object]:
        return {
            "theme": self.theme,
            "default_armory_path": self.default_armory_path,
            "last_armory_path": self.last_armory_path,
            "activity_trace_mode": self.activity_trace_mode,
            "vocab_strictness": self.vocab_strictness,
            "thinking_visibility": self.thinking_visibility,
            "live_tokens_visible": self.live_tokens_visible,
            "live_cost_visible": self.live_cost_visible,
            "privacy": self.privacy.to_dict(),
            "choices": self.choices.to_dict(),
            "mutable_keys": list(self.mutable_keys),
        }


def load_sdk_app_settings() -> SdkAppSettings:
    return SdkAppSettings.load()


def update_sdk_app_settings(params: Mapping[str, object]) -> SdkAppSettings:
    normalized = _normalized_sdk_app_settings(params)
    _save_sdk_app_settings(normalized)
    return load_sdk_app_settings()


def _normalized_sdk_app_settings(params: Mapping[str, object]) -> dict[str, object]:
    _raise_for_unsupported_sdk_settings(params)
    return {key: _normalized_sdk_setting(key, value) for key, value in params.items()}


def _raise_for_unsupported_sdk_settings(params: Mapping[str, object]) -> None:
    unknown = _unsupported_sdk_setting_names(params)
    if unknown:
        names = ", ".join(unknown)
        raise SdkSettingsError(f"Unsupported SDK app setting: {names}")


def _unsupported_sdk_setting_names(params: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(sorted(key for key in params if key not in _SDK_MUTABLE_APP_SETTINGS))


def _normalized_sdk_setting(key: str, value: object) -> object:
    _validate_sdk_setting_type(key, value)
    try:
        return normalize_setting_value(key, value)
    except (KeyError, TypeError, ValueError) as exc:
        raise SdkSettingsError(f"Invalid SDK app setting '{key}': {exc}") from exc


def _save_sdk_app_settings(normalized: Mapping[str, object]) -> None:
    if normalized:
        raw_settings = load_raw_settings()
        raw_settings.update(normalized)
        save_raw_settings(raw_settings)


def _validate_sdk_setting_type(key: str, value: object) -> None:
    if key in _STRING_APP_SETTINGS and not isinstance(value, str):
        raise SdkSettingsError(f"SDK app setting '{key}' must be a string.")
    if key in _STRING_APP_SETTINGS and isinstance(value, str) and "\0" in value:
        raise SdkSettingsError(f"SDK app setting '{key}' must not contain null bytes.")
    if key in _BOOL_APP_SETTINGS and not isinstance(value, bool):
        raise SdkSettingsError(f"SDK app setting '{key}' must be a boolean.")


def _setting_choices(
    values: tuple[str, ...],
    labels: Mapping[str, str],
) -> tuple[SettingChoice, ...]:
    return tuple(SettingChoice(value=value, label=labels.get(value, value)) for value in values)


__all__ = [
    "SDK_APP_SETTING_CONTRACTS",
    "SDK_APP_SETTING_VALUE_TYPES",
    "SDK_MUTABLE_APP_SETTINGS",
    "PrivacySettingsSummary",
    "SdkAppSettingContract",
    "SdkAppSettings",
    "SdkSettingsError",
    "SettingChoice",
    "SettingsChoices",
    "load_sdk_app_settings",
    "update_sdk_app_settings",
]
