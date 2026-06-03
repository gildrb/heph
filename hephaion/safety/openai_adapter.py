"""Official OpenAI Guardrails adapter for Heph safety checkpoints."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from guardrails import GuardrailsOpenAI
from guardrails.types import GuardrailResult as SdkGuardrailResult

from hephaion.safety.contracts import (
    GUARDRAIL_STAGE_INPUT,
    GUARDRAIL_STAGE_OUTPUT,
    GUARDRAIL_STAGE_TOOL_CALL,
    GUARDRAIL_STAGE_TOOL_RESULT,
    GuardrailDecision,
    GuardrailMessage,
    GuardrailStage,
    GuardrailToolCall,
    allow_guardrail,
    block_guardrail,
    warn_guardrail,
)

_OFFICIAL_OPENAI_ENDPOINT = "https://api.openai.com/v1"
_OPENAI_PROVIDER_SLUGS = frozenset({"openai", "openai-codex"})
_GUARDRAIL_MODEL = "gpt-4o-mini"
_INPUT_SCOPE = (
    "Hephaion is a local document and learning harness. On-topic requests ask Heph to "
    "work with the active armory/materials, answer grounded questions, cite evidence, "
    "manage recall practice, explain retrieved source material, or help operate the app safely."
)
_PII_ENTITIES = (
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "CRYPTO",
    "IBAN_CODE",
    "IP_ADDRESS",
    "MEDICAL_LICENSE",
    "CVV",
    "BIC_SWIFT",
    "US_BANK_NUMBER",
    "US_DRIVER_LICENSE",
    "US_ITIN",
    "US_PASSPORT",
    "US_SSN",
    "UK_NHS",
    "UK_NINO",
    "ES_NIF",
    "ES_NIE",
    "IT_FISCAL_CODE",
    "IT_DRIVER_LICENSE",
    "IT_VAT_CODE",
    "IT_PASSPORT",
    "IT_IDENTITY_CARD",
    "PL_PESEL",
    "SG_NRIC_FIN",
    "SG_UEN",
    "AU_ABN",
    "AU_ACN",
    "AU_TFN",
    "AU_MEDICARE",
    "IN_PAN",
    "IN_AADHAAR",
    "IN_VEHICLE_REGISTRATION",
    "IN_VOTER",
    "IN_PASSPORT",
    "FI_PERSONAL_IDENTITY_CODE",
    "KR_RRN",
)


class GuardrailConfigProtocol(Protocol):
    base_url: str
    model: str

    @property
    def provider_slug(self) -> str: ...

    @property
    def resolved_api_key(self) -> str: ...


@dataclass(frozen=True, slots=True)
class OpenAIGuardrailResult:
    tripwire_triggered: bool
    execution_failed: bool
    info: dict[str, object]


class OpenAIGuardrailsRunner(Protocol):
    def run(
        self,
        stage_name: str,
        text: str,
        *,
        conversation_history: Sequence[Mapping[str, object]],
    ) -> tuple[OpenAIGuardrailResult, ...]: ...


RunnerFactory = Callable[[GuardrailConfigProtocol], OpenAIGuardrailsRunner]


def check_openai_input(
    user_input: str,
    *,
    conversation: Sequence[GuardrailMessage],
    config: GuardrailConfigProtocol,
) -> GuardrailDecision:
    runner = _runner_for_config(config)
    if runner is None:
        return allow_guardrail(GUARDRAIL_STAGE_INPUT)

    history = _conversation_history(conversation, latest_user_input=user_input)
    preflight_results = runner.run("pre_flight", user_input, conversation_history=history)
    if failed_decision := _execution_failure_decision(GUARDRAIL_STAGE_INPUT, preflight_results):
        return failed_decision

    masked_input = _masked_text(user_input, preflight_results)
    input_history = _conversation_history(conversation, latest_user_input=masked_input)
    input_results = runner.run("input", masked_input, conversation_history=input_history)
    if blocked_decision := _blocked_decision(
        GUARDRAIL_STAGE_INPUT,
        input_results,
        "Blocked because the request is outside Heph's document-learning scope or safety bounds.",
    ):
        return blocked_decision
    if failed_decision := _execution_failure_decision(GUARDRAIL_STAGE_INPUT, input_results):
        return failed_decision
    if masked_input != user_input:
        return GuardrailDecision(
            stage=GUARDRAIL_STAGE_INPUT,
            action="warn",
            message="Masked personal data before sending the request to the model.",
            replacement_text=masked_input,
            metadata=_metadata_for_results(preflight_results, code="openai_pii_masked"),
        )
    return allow_guardrail(GUARDRAIL_STAGE_INPUT)


def check_openai_tool_calls(
    tool_calls: Sequence[GuardrailToolCall],
    *,
    conversation: Sequence[GuardrailMessage],
    config: GuardrailConfigProtocol,
) -> GuardrailDecision:
    runner = _runner_for_config(config)
    if runner is None or not tool_calls:
        return allow_guardrail(GUARDRAIL_STAGE_TOOL_CALL)

    history = _conversation_history(conversation)
    history.append(_assistant_tool_call_message(tool_calls))
    results = runner.run("output", _tool_call_text(tool_calls), conversation_history=history)
    if blocked_decision := _blocked_decision(
        GUARDRAIL_STAGE_TOOL_CALL,
        results,
        "Blocked a tool call that did not align with the user's request.",
    ):
        return blocked_decision
    if failed_decision := _execution_failure_decision(GUARDRAIL_STAGE_TOOL_CALL, results):
        return failed_decision
    return allow_guardrail(GUARDRAIL_STAGE_TOOL_CALL)


def check_openai_tool_results(
    tool_results: Sequence[GuardrailMessage],
    *,
    conversation: Sequence[GuardrailMessage],
    tool_calls: Sequence[GuardrailToolCall],
    config: GuardrailConfigProtocol,
) -> GuardrailDecision:
    runner = _runner_for_config(config)
    if runner is None or not tool_results:
        return allow_guardrail(GUARDRAIL_STAGE_TOOL_RESULT)

    history = _conversation_history(conversation)
    if tool_calls:
        history.append(_assistant_tool_call_message(tool_calls))
    history.extend(_message_history(tool_results))
    results = runner.run("output", _message_text(tool_results), conversation_history=history)
    if blocked_decision := _blocked_decision(
        GUARDRAIL_STAGE_TOOL_RESULT,
        results,
        "Blocked a tool result that could redirect the model away from the user's request.",
    ):
        return blocked_decision
    if failed_decision := _execution_failure_decision(GUARDRAIL_STAGE_TOOL_RESULT, results):
        return failed_decision
    return allow_guardrail(GUARDRAIL_STAGE_TOOL_RESULT)


def check_openai_output(
    reply: str,
    *,
    conversation: Sequence[GuardrailMessage],
    config: GuardrailConfigProtocol,
) -> GuardrailDecision:
    runner = _runner_for_config(config)
    if runner is None or not reply.strip():
        return allow_guardrail(GUARDRAIL_STAGE_OUTPUT)

    history = _conversation_history(conversation)
    history.append({"role": "assistant", "content": reply})
    results = runner.run("output", reply, conversation_history=history)
    if blocked_decision := _blocked_decision(
        GUARDRAIL_STAGE_OUTPUT,
        results,
        "Blocked an assistant reply because it contained sensitive personal data.",
    ):
        return blocked_decision
    if failed_decision := _execution_failure_decision(GUARDRAIL_STAGE_OUTPUT, results):
        return failed_decision
    return allow_guardrail(GUARDRAIL_STAGE_OUTPUT)


def should_buffer_openai_output(config: GuardrailConfigProtocol) -> bool:
    return _runner_for_config(config) is not None


def set_openai_guardrails_runner_factory(factory: RunnerFactory) -> None:
    _runner_factory_state.factory = factory
    _runner_cache.clear()


def reset_openai_guardrails_runner_factory() -> None:
    _runner_factory_state.factory = _SdkOpenAIGuardrailsRunner
    _runner_cache.clear()


class _SdkOpenAIGuardrailsRunner:
    def __init__(self, config: GuardrailConfigProtocol) -> None:
        self._config = config
        self._client = None

    def run(
        self,
        stage_name: str,
        text: str,
        *,
        conversation_history: Sequence[Mapping[str, object]],
    ) -> tuple[OpenAIGuardrailResult, ...]:
        client = self._guardrails_client()
        results = client._run_stage_guardrails(
            stage_name,
            text,
            conversation_history=[dict(message) for message in conversation_history],
            suppress_tripwire=True,
        )
        return tuple(_sdk_result(result) for result in results)

    def _guardrails_client(self):
        if self._client is not None:
            return self._client

        self._client = GuardrailsOpenAI(
            config=_pipeline_config(),
            api_key=self._config.resolved_api_key,
            base_url=self._config.base_url,
            raise_guardrail_errors=False,
        )
        return self._client


@dataclass(slots=True)
class _RunnerFactoryState:
    factory: RunnerFactory


_runner_factory_state = _RunnerFactoryState(_SdkOpenAIGuardrailsRunner)
_runner_cache: dict[tuple[str, str, str], OpenAIGuardrailsRunner] = {}


def _runner_for_config(config: GuardrailConfigProtocol) -> OpenAIGuardrailsRunner | None:
    if not _is_official_openai_config(config):
        return None
    key = (config.provider_slug, _normalized_endpoint(config.base_url), config.resolved_api_key)
    runner = _runner_cache.get(key)
    if runner is None:
        runner = _runner_factory_state.factory(config)
        _runner_cache[key] = runner
    return runner


def _is_official_openai_config(config: GuardrailConfigProtocol) -> bool:
    if not config.resolved_api_key:
        return False
    if config.provider_slug in _OPENAI_PROVIDER_SLUGS:
        return True
    return _normalized_endpoint(config.base_url) == _OFFICIAL_OPENAI_ENDPOINT


def _normalized_endpoint(base_url: str) -> str:
    return base_url.strip().rstrip("/")


def _pipeline_config() -> dict[str, object]:
    pii_mask = {
        "name": "Contains PII",
        "config": {
            "entities": list(_PII_ENTITIES),
            "block": False,
            "detect_encoded_pii": True,
        },
    }
    pii_block = {
        "name": "Contains PII",
        "config": {
            "entities": list(_PII_ENTITIES),
            "block": True,
            "detect_encoded_pii": True,
        },
    }
    llm_config = {
        "model": _GUARDRAIL_MODEL,
        "confidence_threshold": 0.7,
        "max_turns": 10,
        "include_reasoning": False,
    }
    prompt_injection = {
        "name": "Prompt Injection Detection",
        "config": dict(llm_config),
    }
    return {
        "version": 1,
        "pre_flight": {"version": 1, "guardrails": [pii_mask]},
        "input": {
            "version": 1,
            "guardrails": [
                {"name": "Jailbreak", "config": dict(llm_config)},
                {
                    "name": "Off Topic Prompts",
                    "config": {**llm_config, "system_prompt_details": _INPUT_SCOPE},
                },
            ],
        },
        "output": {"version": 1, "guardrails": [prompt_injection, pii_block]},
    }


def _conversation_history(
    conversation: Sequence[GuardrailMessage],
    *,
    latest_user_input: str | None = None,
) -> list[dict[str, object]]:
    history = _message_history(conversation)
    if latest_user_input is not None:
        history.append({"role": "user", "content": latest_user_input})
    return history


def _message_history(messages: Sequence[GuardrailMessage]) -> list[dict[str, object]]:
    return [{"role": message.role, "content": message.content} for message in messages]


def _assistant_tool_call_message(
    tool_calls: Sequence[GuardrailToolCall],
) -> dict[str, object]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": tool_call.call_id,
                "type": "function",
                "function": {
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                },
            }
            for tool_call in tool_calls
        ],
    }


def _tool_call_text(tool_calls: Sequence[GuardrailToolCall]) -> str:
    return "\n".join(f"{tool_call.name}({tool_call.arguments})" for tool_call in tool_calls)


def _message_text(messages: Sequence[GuardrailMessage]) -> str:
    return "\n".join(message.content for message in messages if message.content)


def _sdk_result(result: SdkGuardrailResult) -> OpenAIGuardrailResult:
    return OpenAIGuardrailResult(
        tripwire_triggered=result.tripwire_triggered,
        execution_failed=result.execution_failed,
        info=dict(result.info),
    )


def _masked_text(original_text: str, results: Sequence[OpenAIGuardrailResult]) -> str:
    for result in results:
        if result.info.get("guardrail_name") != "Contains PII":
            continue
        if result.info.get("pii_detected") is not True:
            continue
        checked_text = result.info.get("checked_text")
        if isinstance(checked_text, str):
            return checked_text
    return original_text


def _blocked_decision(
    stage: GuardrailStage,
    results: Sequence[OpenAIGuardrailResult],
    message: str,
) -> GuardrailDecision | None:
    triggered_results = tuple(result for result in results if result.tripwire_triggered)
    if not triggered_results:
        return None
    return block_guardrail(
        stage,
        message,
        metadata=_metadata_for_results(triggered_results, code="openai_guardrail_block"),
    )


def _execution_failure_decision(
    stage: GuardrailStage,
    results: Sequence[OpenAIGuardrailResult],
) -> GuardrailDecision | None:
    failed_results = tuple(result for result in results if result.execution_failed)
    if not failed_results:
        return None
    return warn_guardrail(
        stage,
        "OpenAI Guardrails could not complete a safety check; continuing with local guardrails.",
        metadata=_metadata_for_results(
            failed_results,
            code="openai_guardrail_execution_failed",
            silent=True,
        ),
    )


def _metadata_for_results(
    results: Sequence[OpenAIGuardrailResult],
    *,
    code: str,
    silent: bool = False,
) -> dict[str, object]:
    entries = [_metadata_entry(result) for result in results]
    metadata: dict[str, object] = {"code": code, "openai_guardrails": entries}
    if silent:
        metadata["silent"] = True
    return metadata


def _metadata_entry(result: OpenAIGuardrailResult) -> dict[str, object]:
    info = result.info
    entry: dict[str, object] = {
        "name": _string_info(info, "guardrail_name"),
        "triggered": result.tripwire_triggered,
        "execution_failed": result.execution_failed,
    }
    _copy_number_info(info, entry, "confidence")
    _copy_number_info(info, entry, "threshold")
    if entity_types := _detected_entity_types(info):
        entry["detected_entity_types"] = entity_types
    if token_usage := _token_usage(info):
        entry["token_usage"] = token_usage
    return entry


def _string_info(info: Mapping[str, object], key: str) -> str:
    value = info.get(key)
    return value if isinstance(value, str) else ""


def _copy_number_info(
    source: Mapping[str, object],
    destination: dict[str, object],
    key: str,
) -> None:
    value = source.get(key)
    if isinstance(value, int | float):
        destination[key] = value


def _detected_entity_types(info: Mapping[str, object]) -> list[str]:
    detected_entities = info.get("detected_entities")
    if not isinstance(detected_entities, Mapping):
        return []
    return sorted(str(entity_type) for entity_type in detected_entities)


def _token_usage(info: Mapping[str, object]) -> dict[str, object]:
    token_usage = info.get("token_usage")
    if not isinstance(token_usage, Mapping):
        return {}
    safe_usage: dict[str, object] = {}
    allowed_keys = frozenset(
        {"prompt_tokens", "completion_tokens", "total_tokens", "unavailable_reason"}
    )
    for key, value in token_usage.items():
        if key in allowed_keys and (isinstance(value, str | int) or value is None):
            safe_usage[str(key)] = value
    return safe_usage
