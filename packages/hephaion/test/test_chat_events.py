from __future__ import annotations

from hephaion.chat.automation import event_to_json_object
from hephaion.chat.events import (
    AssistantDeltaEvent,
    CompactRequestEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
    render_turn_event,
)


def test_event_defaults_expose_expected_kinds() -> None:
    assert AssistantDeltaEvent("hi").kind == "assistant_delta"
    assert ToolCallEvent("1", "bash", {}, "$ bash").kind == "tool_call"
    assert ToolResultEvent("1", "bash", "done", "summary").kind == "tool_result"
    assert MaterialOperationEvent("search_index", "Searching materials.").kind == (
        "material_operation"
    )
    assert CompactRequestEvent("1", "compact", {}).kind == "compact_request"
    assert TurnCompleteEvent("done", 0, 1.0, "stop", 100).kind == "turn_complete"
    notice = NoticeEvent("Heads up")
    assert notice.kind == "notice"
    assert notice.code == "notice"


def test_render_turn_event_handles_each_supported_event_type() -> None:
    assert render_turn_event(AssistantDeltaEvent("hello")) == "hello"
    assert render_turn_event(ToolCallEvent("1", "bash", {}, "$ bash")) == "\n$ bash\n"
    assert render_turn_event(ToolResultEvent("1", "bash", "output", "summary")) == "summary\n"
    assert render_turn_event(MaterialOperationEvent("read_excerpt", "Opened source.")) == (
        "Opened source.\n"
    )
    assert render_turn_event(CompactRequestEvent("1", "compact", {})) == ""
    assert render_turn_event(TurnCompleteEvent("done", 0, 1.0, "stop", 100)) == ""
    assert render_turn_event(NoticeEvent("Verified", code="verification")) == "\nVerified\n"
    assert render_turn_event(NoticeEvent("Working")) == "\n[Working]\n"


def test_event_to_json_object_uses_public_type_key() -> None:
    assert event_to_json_object(AssistantDeltaEvent("hello")) == {
        "type": "assistant_delta",
        "delta": "hello",
    }
    assert event_to_json_object(ToolCallEvent("1", "bash", {"command": "pwd"}, "$ bash")) == {
        "type": "tool_call",
        "call_id": "1",
        "name": "bash",
        "arguments": {"command": "pwd"},
        "display": "$ bash",
    }
    assert event_to_json_object(NoticeEvent("Working")) == {
        "type": "notice",
        "message": "Working",
        "code": "notice",
    }


def test_assistant_delta_strips_decorative_symbols() -> None:
    event = AssistantDeltaEvent("Hey! 👋 Use A→B and x².")

    assert event.delta == "Hey!  Use A→B and x²."
    assert render_turn_event(event) == event.delta


def test_turn_complete_strips_decorative_symbols() -> None:
    event = TurnCompleteEvent("Done ✅", 0, 1.0, "stop", 100)

    assert event.full_text == "Done "
