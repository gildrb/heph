"""No-armory local replies for the Textual shell."""

from __future__ import annotations

from hephaistos.chat.session import ChatSession, no_armory_guidance_reply
from hephaistos.study import plan_turn


def record_no_armory_turn(session: ChatSession, user_input: str) -> str:
    """Record and return the local no-armory reply for one TUI input."""
    plan = plan_turn(session.study_state, user_input)
    reply = plan.direct_reply or no_armory_guidance_reply()
    session.conversation.add("user", user_input)
    session.conversation.add("assistant", reply)
    return reply
