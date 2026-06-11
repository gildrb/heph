"""Session status helpers for app adapters.

Matches Codex's separate status modules: compute status/config state outside the
TUI renderer so adapters only format it for their surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ai.runtime import has_configured_access

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession

STATUS_FIELD_GAP = "  "
_BASE_STATUS_FIELDS = ("armory", "model", "reasoning")
_DEFAULT_STATUS_TITLE = "Heph"


def status_lines(
    session: ChatSession, *, draft: str = "", title: str = _DEFAULT_STATUS_TITLE
) -> str:
    # Draft text is not usage until a provider records the turn.
    _ = draft
    display_title = title.strip() or _DEFAULT_STATUS_TITLE
    armory = "none"
    if session.armory_path is not None:
        try:
            path = session.armory_path.expanduser().resolve(strict=False)
            armory = f"~/{path.relative_to(Path.home())}"
        except ValueError:
            armory = str(session.armory_path)
        if len(armory) > 48:
            armory = f"...{armory[-45:]}"
    model = session.config.model or "none"
    fields = [
        ("armory", armory),
        ("model", model),
        ("reasoning", session.config.reasoning_level),
        *_live_usage_fields(session),
    ]
    return STATUS_FIELD_GAP.join(
        (display_title, *(f"{label.upper()} {value.lower()}" for label, value in fields))
    )


def status_labels(session: ChatSession) -> tuple[str, ...]:
    labels = [*_BASE_STATUS_FIELDS]
    if session.live_tokens_visible:
        labels.append("tokens")
    if session.live_cost_visible:
        labels.append("cost")
    return tuple(label.upper() for label in labels)


def _live_usage_fields(session: ChatSession) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    if session.live_tokens_visible:
        fields.append(("tokens", _token_status_value(session)))
    if session.live_cost_visible:
        fields.append(("cost", _cost_status_value(session)))
    return fields


def _token_status_value(session: ChatSession) -> str:
    summary = session.usage.summary()
    prompt_tokens = int(summary["prompt_tokens"])
    completion_tokens = int(summary["completion_tokens"])
    total_tokens = int(summary["total_tokens"])
    if total_tokens <= 0:
        return "0"

    parts: list[str] = []
    if prompt_tokens:
        parts.append(f"↑{_format_tokens(prompt_tokens)}")
    if completion_tokens:
        parts.append(f"↓{_format_tokens(completion_tokens)}")
    return " ".join(parts) or _format_tokens(total_tokens)


def _cost_status_value(session: ChatSession) -> str:
    summary = session.usage.summary()
    value = f"${float(summary['cost_usd']):.3f}"
    if _uses_subscription_billing(session):
        return f"{value} (sub)"
    return value


def _uses_subscription_billing(session: ChatSession) -> bool:
    return session.config.provider_slug == "openai-codex"


def _format_tokens(count: int) -> str:
    if count < 1_000:
        return str(count)
    if count < 10_000:
        return f"{count / 1_000:.1f}k"
    if count < 1_000_000:
        return f"{round(count / 1_000)}k"
    if count < 10_000_000:
        return f"{count / 1_000_000:.1f}M"
    return f"{round(count / 1_000_000)}M"


def config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not has_configured_access(session.config):
        from ai.runtime import missing_api_key_message

        return missing_api_key_message(session.config)
    return None
