"""Status rendering for chat sessions."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.terminal.display import STYLE_DIM, styled


def session_status_lines(session: ChatSession) -> list[str]:
    armory = str(session.armory_path) if session.armory_path else styled("none", STYLE_DIM)
    title = session.title or styled("(untitled)", STYLE_DIM)
    msg_count = sum(1 for message in session.conversation.messages if message.role != "system")
    tool_count = 7 if session.armory_path else 0
    mode = "agent (tools)" if session.armory_path else "plain chat"
    usage_summary = session.usage.summary()
    mem_count = len(session.memory.entries) if session.memory else 0
    key_status = (
        "not needed (free provider)"
        if is_keyless_endpoint(session.config.base_url)
        else "configured"
        if session.config.resolved_api_key
        else styled("not set", STYLE_DIM)
    )
    return [
        f"  Armory:    {armory}",
        f"  Session:   {session.session_id}",
        f"  Title:     {title}",
        f"  Model:     {session.config.model}",
        f"  Persona:   {session.persona.display_name}",
        f"  API:       {session.config.base_url}",
        f"  Key:       {key_status}",
        f"  Mode:      {mode}",
        f"  Tools:     {tool_count}",
        f"  Messages:  {msg_count}",
        f"  Memory:    {mem_count} concepts",
        f"  API calls: {usage_summary['api_calls']}",
        (
            f"  Tokens:    {usage_summary['total_tokens']}"
            f" (prompt: {usage_summary['prompt_tokens']},"
            f" completion: {usage_summary['completion_tokens']})"
        ),
        f"  Cost:      ${usage_summary['cost_usd']:.4f}",
        f"  Dirty:     {'yes' if session.dirty else 'no'}",
    ]


def render_session_status(session: ChatSession) -> str:
    return "\n".join(session_status_lines(session))
