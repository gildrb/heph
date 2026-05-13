"""Session status helpers for app adapters.

Matches Codex's separate status modules: compute status/config state outside the
TUI renderer so adapters only format it for their surface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hephaistos import __version__
from hephaistos.memory.supermemory import supermemory_configured
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.runtime import has_configured_access

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


def status_lines(session: ChatSession, state: str = "ready") -> str:
    armory = str(session.armory_path) if session.armory_path is not None else "none"
    model = session.config.model or "none"
    keyless = is_keyless_endpoint(session.config.base_url)
    key_ok = has_configured_access(session.config, refresh_oauth=False)
    if keyless:
        api = "free"
    elif key_ok:
        api = "configured"
    else:
        api = "missing"
    mem_status = "on" if supermemory_configured() else "/memory"
    study_mode = session.study_state.autonomy_mode.value
    sources = session.source_file_count or 0
    source_str = str(sources)
    state_tag = f" [{state}]" if state != "ready" else ""
    return (
        f"Hephaistos v{__version__}{state_tag}"
        f" armory {armory}"
        f" model {model}"
        f" mode {study_mode}"
        f" api {api}"
        f" memory {mem_status}"
        f" materials {source_str}"
    )


def config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not has_configured_access(session.config):
        from hephaistos.runtime import missing_api_key_message

        return missing_api_key_message(session.config)
    return None
