"""Session status helpers for app adapters.

Matches Codex's separate status modules: compute status/config state outside the
TUI renderer so adapters only format it for their surface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos.runtime import has_configured_access

if TYPE_CHECKING:
    from pathlib import Path

    from hephaistos.chat.session import ChatSession


def _armory_status_label(path: Path | None, *, max_length: int = 24) -> str:
    if path is None:
        return "none"
    label = path.name or str(path)
    if len(label) <= max_length:
        return label
    return f"...{label[-(max_length - 3) :]}"


def status_lines(session: ChatSession, state: str = "ready") -> str:
    _ = state
    armory = _armory_status_label(session.armory_path)
    model = session.config.model or "none"
    study_mode = session.study_state.autonomy_mode.value
    return f"Heph armory {armory} model {model} mode {study_mode}"


def config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not has_configured_access(session.config):
        from hephaistos.runtime import missing_api_key_message

        return missing_api_key_message(session.config)
    return None
