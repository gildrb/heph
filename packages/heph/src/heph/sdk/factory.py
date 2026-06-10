"""Factory helpers for fully wired SDK sessions and services."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ai.runtime import ChatConfig, normalize_thinking_visibility
from hephaion.armory.storage import normalize_path
from hephaion.parameters.cli import load_config

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
    config = create_chat_config(resolved_options)
    armory_path = resolved_options.armory_path
    if armory_path is None:
        if resolved_options.create_armory:
            raise HephSdkError("create_armory=True requires an armory_path.")
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
    runtime_result = create_heph_runtime(resolved_options)
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


def _normalized_optional_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    return normalize_path(path)


def _apply_config_overrides(config: ChatConfig, options: HephSdkOptions) -> None:
    if options.base_url is not None:
        config.base_url = options.base_url
    if options.model is not None:
        config.model = options.model
    if options.max_tokens is not None:
        config.max_tokens = options.max_tokens
    if options.rag_context_budget is not None:
        config.rag_context_budget = options.rag_context_budget
    if options.reasoning_level is not None:
        config.reasoning_level = options.reasoning_level
    if options.thinking_visibility is not None:
        config.thinking_visibility = normalize_thinking_visibility(options.thinking_visibility)
    if options.temperature is not None:
        config.temperature = min(2.0, max(0.0, options.temperature))
    if options.feature_flags is not None:
        config.feature_flags = options.feature_flags


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
