"""Factory helpers for fully wired SDK sessions and services."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ai.runtime import ChatConfig
from hephaion.armory.storage import normalize_path
from hephaion.parameters.cli import load_config

from heph.sdk.config import apply_sdk_config_updates, sdk_config_update
from heph.sdk.runtime import HephRuntime, HephSdkError, HephSession
from heph.sdk.service import HephService


@dataclass(frozen=True, slots=True)
class HephSdkOptions:
    armory_path: str | Path | None = None
    create_armory: bool = False
    session_id: str | None = None
    start_session: bool = True
    config: ChatConfig | None = None
    base_url: str | None = None
    model: str | None = None
    max_tokens: int | None = None
    rag_context_budget: int | None = None
    reasoning_level: str | None = None
    thinking_visibility: str | None = None
    temperature: float | None = None
    feature_flags: frozenset[str] | None = None


@dataclass(frozen=True, slots=True)
class CreateHephRuntimeResult:
    runtime: HephRuntime
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateHephServiceResult:
    service: HephService
    runtime: HephRuntime
    session: HephSession | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateHephSessionResult:
    session: HephSession
    runtime: HephRuntime
    service: HephService
    warnings: tuple[str, ...] = ()


def create_chat_config(options: HephSdkOptions | None = None) -> ChatConfig:
    resolved_options = options or HephSdkOptions()
    armory_path = _normalized_optional_path(resolved_options.armory_path)
    config = (
        replace(resolved_options.config)
        if resolved_options.config is not None
        else load_config(armory_path)
    )
    _apply_config_overrides(config, resolved_options)
    return config


def create_heph_runtime(
    options: HephSdkOptions | None = None,
) -> CreateHephRuntimeResult:
    resolved_options = options or HephSdkOptions()
    _validate_runtime_options(resolved_options)
    config = create_chat_config(resolved_options)
    armory_path = resolved_options.armory_path
    if armory_path is None:
        return CreateHephRuntimeResult(runtime=HephRuntime.plain(config=config))
    if resolved_options.create_armory:
        return CreateHephRuntimeResult(
            runtime=HephRuntime.create_armory(armory_path, config=config)
        )
    return CreateHephRuntimeResult(runtime=HephRuntime.open_armory(armory_path, config=config))


def create_heph_service(
    options: HephSdkOptions | None = None,
) -> CreateHephServiceResult:
    resolved_options = options or HephSdkOptions()
    _validate_service_options(resolved_options)
    runtime_result = create_heph_runtime(replace(resolved_options, session_id=None))
    service = HephService(runtime=runtime_result.runtime)
    session = _start_session_if_requested(service, resolved_options)
    return CreateHephServiceResult(
        service=service,
        runtime=runtime_result.runtime,
        session=session,
        warnings=runtime_result.warnings,
    )


def create_heph_session(
    options: HephSdkOptions | None = None,
) -> CreateHephSessionResult:
    resolved_options = options or HephSdkOptions()
    _validate_session_options(resolved_options)
    service_result = create_heph_service(
        replace(resolved_options, start_session=True),
    )
    if service_result.session is None:
        raise HephSdkError("SDK session creation did not produce a session.")
    return CreateHephSessionResult(
        session=service_result.session,
        runtime=service_result.runtime,
        service=service_result.service,
        warnings=service_result.warnings,
    )


def _start_session_if_requested(
    service: HephService,
    options: HephSdkOptions,
) -> HephSession | None:
    if not options.start_session:
        return None
    if options.session_id is not None:
        service.resume_session(options.session_id)
    else:
        service.new_session()
    return service.session


def _validate_runtime_options(options: HephSdkOptions) -> None:
    if options.create_armory and options.armory_path is None:
        raise HephSdkError("create_armory=True requires an armory_path.")
    if options.session_id is not None:
        raise HephSdkError("session_id cannot be used with create_heph_runtime().")


def _validate_service_options(options: HephSdkOptions) -> None:
    if options.session_id is not None and not options.start_session:
        raise HephSdkError("session_id cannot be used with start_session=False.")


def _validate_session_options(options: HephSdkOptions) -> None:
    if not options.start_session:
        raise HephSdkError("create_heph_session() requires start_session=True.")


def _normalized_optional_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    path_issue = _sdk_option_path_issue(path, "armory_path")
    if path_issue is not None:
        raise HephSdkError(path_issue)
    try:
        return normalize_path(path)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise HephSdkError(f"SDK option 'armory_path' is invalid: {exc}") from exc


def _sdk_option_path_issue(path: object, label: str) -> str | None:
    if not isinstance(path, str | Path):
        return f"SDK option '{label}' must be a path string or Path."
    path_text = str(path)
    if not path_text.strip():
        return f"SDK option '{label}' must be a non-empty path."
    if "\0" in path_text:
        return f"SDK option '{label}' must not contain null bytes."
    return None


def _apply_config_overrides(config: ChatConfig, options: HephSdkOptions) -> None:
    updates = tuple(
        update
        for update in (
            sdk_config_update("base_url", options.base_url),
            sdk_config_update("model", options.model),
            sdk_config_update("max_tokens", options.max_tokens),
            sdk_config_update("rag_context_budget", options.rag_context_budget),
            sdk_config_update("reasoning_level", options.reasoning_level),
            sdk_config_update("thinking_visibility", options.thinking_visibility),
            sdk_config_update("temperature", options.temperature),
            sdk_config_update("feature_flags", options.feature_flags),
        )
        if update is not None
    )
    apply_sdk_config_updates(config, updates)


__all__ = [
    "CreateHephRuntimeResult",
    "CreateHephServiceResult",
    "CreateHephSessionResult",
    "HephSdkOptions",
    "create_chat_config",
    "create_heph_runtime",
    "create_heph_service",
    "create_heph_session",
]
