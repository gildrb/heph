"""Session status helpers for app adapters.

Matches Codex's separate status modules: compute status/config state outside the
TUI renderer so adapters only format it for their surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from heph_ai.runtime import has_configured_access

if TYPE_CHECKING:
    from chat.session import ChatSession

STATUS_FIELD_GAP = "  "


def status_lines(session: ChatSession) -> str:
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
    return (
        f"Heph{STATUS_FIELD_GAP}armory {armory}"
        f"{STATUS_FIELD_GAP}model {model}"
        f"{STATUS_FIELD_GAP}reasoning {session.config.reasoning_level}"
    )


def config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not has_configured_access(session.config):
        from heph_ai.runtime import missing_api_key_message

        return missing_api_key_message(session.config)
    return None
