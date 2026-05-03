"""Session status helpers for app adapters.

Matches Codex's separate status modules: compute status/config state outside the
TUI renderer so adapters only format it for their surface.
"""

from __future__ import annotations

from hephaistos import __version__
from hephaistos.chat.session import ChatSession
from hephaistos.memory.supermemory import supermemory_configured
from hephaistos.runtime import is_keyless_endpoint, missing_api_key_message


def status_lines(session: ChatSession, state: str = "ready") -> str:
    armory = str(session.armory_path) if session.armory_path is not None else "none"
    model = session.config.model or "none"
    keyless = is_keyless_endpoint(session.config.base_url)
    key_ok = keyless or bool(session.config.resolved_api_key)
    if keyless:
        api = "free"
    elif key_ok:
        api = "configured"
    else:
        api = "missing"
    mem_status = "on" if supermemory_configured() else "/memory"
    sources = session.source_file_count or 0
    source_str = str(sources) if sources else "none"
    state_tag = f" [{state}]" if state != "ready" else ""
    return (
        f"Hephaistos v{__version__}{state_tag}"
        f"  armory {armory}"
        f"  model {model}"
        f"  api {api}"
        f"  memory {mem_status}"
        f"  materials {source_str}"
    )


def config_error(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not session.config.resolved_api_key and not is_keyless_endpoint(session.config.base_url):
        return missing_api_key_message(session.config)
    return None
