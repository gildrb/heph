from __future__ import annotations

from hephaistos.chat.events import (
    AssistantDeltaEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    render_turn_event,
)


def test_event_defaults_expose_expected_kinds() -> None:
    assert AssistantDeltaEvent("hi").kind == "assistant_delta"
    assert ToolCallEvent("1", "bash", {}, "$ bash").kind == "tool_call"
    assert ToolResultEvent("1", "bash", "done", "summary").kind == "tool_result"
    notice = NoticeEvent("Heads up")
    assert notice.kind == "notice"
    assert notice.code == "notice"


def test_render_turn_event_handles_each_supported_event_type() -> None:
    assert render_turn_event(AssistantDeltaEvent("hello")) == "hello"
    assert render_turn_event(ToolCallEvent("1", "bash", {}, "$ bash")) == "\n$ bash\n"
    assert render_turn_event(ToolResultEvent("1", "bash", "output", "summary")) == "summary\n"
    assert render_turn_event(NoticeEvent("Verified", code="verification")) == "\nVerified\n"
    assert render_turn_event(NoticeEvent("Working")) == "\n[Working]\n"
