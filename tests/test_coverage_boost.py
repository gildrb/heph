"""Targeted tests to cover low-coverage modules.

These modules have straightforward logic paths that are easy to exercise
without complex TUI or LLM integration.
"""

from __future__ import annotations

import importlib.util
import time
from threading import Event
from unittest.mock import MagicMock, patch

import heph.cli.main as _main_mod
from ai.providers.config import ProviderConfig
from ai.runtime import Conversation, EngineError
from harness.chat.compaction import compact_session
from harness.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
)
from harness.chat.model_selection import switch_model
from harness.chat.titles import derive_title
from harness.memory.workflow import schedule_memory_extraction
from harness.parameters import settings as settings_store
from interfaces.tui.routing import pending_input_requires_terminal
from interfaces.tui.streaming import run_tui_turn

# ---------------------------------------------------------------------------
# CLI entry point ownership
# ---------------------------------------------------------------------------


class TestMainModule:
    def test_main_entry_point_importable(self) -> None:
        assert _main_mod is not None

    def test_old_flat_cli_module_is_not_a_shim(self) -> None:
        assert importlib.util.find_spec("cli") is None


# ---------------------------------------------------------------------------
# chat/titles.py - derive_title
# ---------------------------------------------------------------------------


class TestDeriveTitle:
    def test_empty_conversation(self) -> None:
        conv = Conversation()
        assert derive_title(conv) == ""

    def test_single_user_message(self) -> None:
        conv = Conversation()
        conv.add("user", "What is Python?")
        title = derive_title(conv)
        assert title == "What is Python?"

    def test_whitespace_spam_collapses_to_first_request(self) -> None:
        conv = Conversation()
        conv.add("user", "\n\n \t What   do\n\nyou think about the material?\x1b[31m")
        title = derive_title(conv)
        assert title == "What do you think about the material?"

    def test_long_message_truncated(self) -> None:
        conv = Conversation()
        long_msg = "x" * 100
        conv.add("user", long_msg)
        title = derive_title(conv)
        assert len(title) == 60
        assert title == long_msg[:60]

    def test_duplicate_user_messages_get_count(self) -> None:
        conv = Conversation()
        conv.add("user", "Hello")
        conv.add("assistant", "Hi there")
        conv.add("user", "Hello")
        title = derive_title(conv)
        assert "(2)" in title

    def test_different_user_messages_no_count(self) -> None:
        conv = Conversation()
        conv.add("user", "First question")
        conv.add("assistant", "Answer")
        conv.add("user", "Second question")
        title = derive_title(conv)
        assert "(" not in title
        assert title == "First question"


# ---------------------------------------------------------------------------
# chat/model_selection.py - switch_model
# ---------------------------------------------------------------------------


class TestSwitchModel:
    def test_switch_to_unknown_provider_returns_false(self, chat_session) -> None:
        result = switch_model(chat_session, "nonexistent", "gpt-4")
        assert result is False

    def test_switch_to_unknown_model_returns_false(self, chat_session, providers_toml) -> None:
        _providers = providers_toml  # fixture creates file that ProviderConfig.load() reads
        pc = ProviderConfig.load()
        pc.apply_to_config(chat_session.config)

        result = switch_model(chat_session, "zai", "nonexistent-model")
        assert result is False

    def test_switch_to_valid_model(self, chat_session, providers_toml, monkeypatch) -> None:
        _providers = providers_toml  # fixture creates file that ProviderConfig.load() reads
        monkeypatch.setenv("ZAI_API_KEY", "test-key")
        pc = ProviderConfig.load()
        pc.apply_to_config(chat_session.config)

        result = switch_model(chat_session, "zai", "glm-5")
        assert result is True


# ---------------------------------------------------------------------------
# tui/streaming.py - run_tui_turn
# ---------------------------------------------------------------------------


class TestRunTuiTurn:
    def test_successful_turn_calls_callbacks(self, chat_session) -> None:
        replies: list[str] = []
        notices: list[str] = []
        errors: list[str] = []
        finishes: list[bool] = []

        def fake_iter(session, user_input, *, abort):
            yield AssistantDeltaEvent(delta="Hello ")
            yield AssistantDeltaEvent(delta="world")

        with patch("interfaces.tui.streaming.iter_chat_events", fake_iter):
            run_tui_turn(
                chat_session,
                "hi",
                Event(),
                on_reply=replies.append,
                on_notice=notices.append,
                on_error=errors.append,
                on_finish=lambda: finishes.append(True),
            )

        assert replies == ["Hello world"]
        assert errors == []
        assert finishes == [True]

    def test_empty_reply_not_emitted(self, chat_session) -> None:
        replies: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield NoticeEvent(message="Thinking...")

        with patch("interfaces.tui.streaming.iter_chat_events", fake_iter):
            run_tui_turn(
                chat_session,
                "hi",
                Event(),
                on_reply=replies.append,
                on_notice=lambda _: None,
                on_error=lambda _: None,
                on_finish=lambda: None,
            )

        assert replies == []

    def test_turn_complete_reply_overrides_streamed_raw_deltas(self, chat_session) -> None:
        replies: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield AssistantDeltaEvent(
                delta=(
                    '<tool_call name="search_materials">{"query":"what can i use this for"}'
                    "</tool_call>"
                )
            )
            yield AssistantDeltaEvent(delta="No searchable armory evidence was found.")
            yield TurnCompleteEvent(
                full_text=(
                    "No searchable armory evidence was found for this item. "
                    "Ask a more specific material-backed prompt."
                ),
                turn_index=0,
                latency_ms=0.0,
                finish_reason="stop",
                tokens_remaining=0,
            )

        with patch("interfaces.tui.streaming.iter_chat_events", fake_iter):
            run_tui_turn(
                chat_session,
                "what can i use this for",
                Event(),
                on_reply=replies.append,
                on_notice=lambda _: None,
                on_error=lambda _: None,
                on_finish=lambda: None,
            )

        assert replies == [
            (
                "No searchable armory evidence was found for this item. "
                "Ask a more specific material-backed prompt."
            )
        ]

    def test_material_operation_events_produce_ordered_notices(self, chat_session) -> None:
        replies: list[str] = []
        notices: list[str] = []
        progress: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield MaterialOperationEvent(
                operation="search_index",
                message="Searching indexed materials for: integration by parts",
                metadata={"query": "integration by parts"},
            )
            yield AssistantDeltaEvent(delta="Grounded answer [E1].")

        with patch("interfaces.tui.streaming.iter_chat_events", fake_iter):
            run_tui_turn(
                chat_session,
                "explain integration by parts",
                Event(),
                on_reply=replies.append,
                on_notice=notices.append,
                on_error=lambda _: None,
                on_finish=lambda: None,
                on_progress=progress.append,
            )

        assert progress == ["searching materials"]
        assert notices == ["materials: searched `integration by parts`."]
        assert replies == ["Grounded answer [E1]."]

    def test_tool_events_produce_notices(self, chat_session) -> None:
        notices: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield ToolCallEvent(
                call_id="call_1",
                name="bash",
                arguments={},
                display="Running: ls",
            )
            yield ToolResultEvent(
                call_id="call_1",
                name="bash",
                content="out",
                summary="file1.py\nfile2.py",
            )

        with patch("interfaces.tui.streaming.iter_chat_events", fake_iter):
            run_tui_turn(
                chat_session,
                "list files",
                Event(),
                on_reply=lambda _: None,
                on_notice=notices.append,
                on_error=lambda _: None,
                on_finish=lambda: None,
            )

        assert notices == ["tool: bash; results summarized."]

    def test_activity_callback_streams_live_tool_and_material_lines(self, chat_session) -> None:
        activity_lines: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield MaterialOperationEvent(
                operation="search_index",
                message="Searching indexed materials for: integration by parts",
                metadata={"query": "integration by parts"},
            )
            yield NoticeEvent(
                message=(
                    "Read complete model response from gpt-5.4-mini: "
                    "172 character(s), 1 tool call(s) in 1.4s."
                ),
                code="model_complete",
            )
            yield ToolCallEvent(
                call_id="call_1",
                name="bash",
                arguments={"command": "rtk rg -n integration materials"},
                display="    Running: rtk rg -n integration materials",
            )
            yield ToolResultEvent(
                call_id="call_1",
                name="bash",
                content="materials/week-3.md:42:integration by parts",
                summary="materials/week-3.md:42:integration by parts",
            )
            yield AssistantDeltaEvent(delta="Grounded answer [E1].")

        with (
            patch("interfaces.tui.streaming.iter_chat_events", fake_iter),
            patch(
                "interfaces.tui.streaming.load_app_settings",
                lambda: settings_store.AppSettings(
                    activity_trace_mode=settings_store.ACTIVITY_TRACE_TOOL_CALLS
                ),
            ),
        ):
            run_tui_turn(
                chat_session,
                "explain integration by parts",
                Event(),
                on_reply=lambda _: None,
                on_notice=lambda _: None,
                on_error=lambda _: None,
                on_finish=lambda: None,
                on_activity=activity_lines.append,
            )

        assert activity_lines == [
            "    Searching indexed materials for: integration by parts",
            (
                "    Read complete model response from gpt-5.4-mini: "
                "172 character(s), 1 tool call(s) in 1.4s."
            ),
            "    Ran bash `rtk rg -n integration materials`",
            "    -> materials/week-3.md:42:integration by parts",
        ]

    def test_hidden_activity_trace_suppresses_progress_and_summary(self, chat_session) -> None:
        notices: list[str] = []
        progress: list[str] = []
        activity_lines: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield MaterialOperationEvent(
                operation="search_index",
                message="Searching indexed materials for: integration by parts",
                metadata={"query": "integration by parts"},
            )
            yield AssistantDeltaEvent(delta="Grounded answer [E1].")

        with (
            patch("interfaces.tui.streaming.iter_chat_events", fake_iter),
            patch(
                "interfaces.tui.streaming.load_app_settings",
                lambda: settings_store.AppSettings(
                    activity_trace_mode=settings_store.ACTIVITY_TRACE_HIDDEN_TOOL_CALLS
                ),
            ),
        ):
            run_tui_turn(
                chat_session,
                "explain integration by parts",
                Event(),
                on_reply=lambda _: None,
                on_notice=notices.append,
                on_error=lambda _: None,
                on_finish=lambda: None,
                on_progress=progress.append,
                on_activity=activity_lines.append,
            )

        assert notices == []
        assert progress == []
        assert activity_lines == []

    def test_minimal_activity_trace_reports_summary_without_live_lines(self, chat_session) -> None:
        notices: list[str] = []
        progress: list[str] = []
        activity_lines: list[str] = []

        def fake_iter(session, user_input, *, abort):
            yield MaterialOperationEvent(
                operation="search_index",
                message="Searching indexed materials for: integration by parts",
                metadata={"query": "integration by parts"},
            )
            yield AssistantDeltaEvent(delta="Grounded answer [E1].")

        with (
            patch("interfaces.tui.streaming.iter_chat_events", fake_iter),
            patch(
                "interfaces.tui.streaming.load_app_settings",
                lambda: settings_store.AppSettings(
                    activity_trace_mode=settings_store.ACTIVITY_TRACE_MINIMAL_TOOL_CALLS
                ),
            ),
        ):
            run_tui_turn(
                chat_session,
                "explain integration by parts",
                Event(),
                on_reply=lambda _: None,
                on_notice=notices.append,
                on_error=lambda _: None,
                on_finish=lambda: None,
                on_progress=progress.append,
                on_activity=activity_lines.append,
            )

        assert notices == ["materials: searched `integration by parts`."]
        assert progress == ["searching materials"]
        assert activity_lines == []

    def test_engine_error_reports_error(self, chat_session) -> None:
        errors: list[str] = []

        def fake_iter(session, user_input, *, abort):
            raise EngineError("model overloaded")

        with patch("interfaces.tui.streaming.iter_chat_events", fake_iter):
            run_tui_turn(
                chat_session,
                "hi",
                Event(),
                on_reply=lambda _: None,
                on_notice=lambda _: None,
                on_error=errors.append,
                on_finish=lambda: None,
            )

        assert any("model overloaded" in e for e in errors)

    def test_network_error_reports_offline_notice(self, chat_session) -> None:
        notices: list[str] = []

        def fake_iter(session, user_input, *, abort):
            raise EngineError("ConnectionError: network unreachable")

        with (
            patch("interfaces.tui.streaming.iter_chat_events", fake_iter),
            patch("interfaces.tui.streaming.is_network_error", return_value=True),
        ):
            run_tui_turn(
                chat_session,
                "hi",
                Event(),
                on_reply=lambda _: None,
                on_notice=notices.append,
                on_error=lambda _: None,
                on_finish=lambda: None,
            )

        assert len(notices) == 1
        assert "offline" in notices[0].lower()


# ---------------------------------------------------------------------------
# tui/routing.py - pending_input_requires_terminal edge cases
# ---------------------------------------------------------------------------


class TestPendingInputRequiresTerminal:
    def test_history_browse(self) -> None:
        assert pending_input_requires_terminal("/sessions browse") is False

    def test_history_menu(self) -> None:
        assert pending_input_requires_terminal("/sessions menu") is False

    def test_history_other(self) -> None:
        assert pending_input_requires_terminal("/sessions 5") is False

    def test_vocabulary_defaults_to_drill(self) -> None:
        assert pending_input_requires_terminal("/vocabulary") is True

    def test_vocabulary_status(self) -> None:
        assert pending_input_requires_terminal("/vocabulary status") is False

    def test_non_command(self) -> None:
        assert pending_input_requires_terminal("just chatting") is False

    def test_login_not_terminal(self) -> None:
        assert pending_input_requires_terminal("/login") is False


# ---------------------------------------------------------------------------
# chat/compaction.py - compact_session
# ---------------------------------------------------------------------------


class TestCompactSession:
    def test_compact_replaces_messages_with_summary(self, chat_session) -> None:
        # The fixture adds a default system prompt; clear it for a clean test
        chat_session.conversation.messages.clear()
        chat_session.conversation.add("system", "You are a tutor.")
        chat_session.conversation.add("user", "What is Python?")
        chat_session.conversation.add("assistant", "Python is a programming language.")

        with (
            patch(
                "harness.chat.compaction.stream_reply",
                return_value=iter(["A summary."]),
            ),
            patch("harness.chat.compaction.sys"),
        ):
            compact_session(chat_session)

        msgs = chat_session.conversation.messages
        assert len(msgs) == 2
        assert msgs[0].role == "system"
        assert msgs[0].content == "You are a tutor."
        assert "[Conversation summary]" in msgs[1].content
        assert "A summary." in msgs[1].content
        assert chat_session.dirty is True

    def test_compact_preserves_system_messages(self, chat_session) -> None:
        chat_session.conversation.messages.clear()
        chat_session.conversation.add("system", "System prompt 1")
        chat_session.conversation.add("system", "System prompt 2")
        chat_session.conversation.add("user", "Hello")

        with (
            patch(
                "harness.chat.compaction.stream_reply",
                return_value=iter(["Brief summary"]),
            ),
            patch("harness.chat.compaction.sys"),
        ):
            compact_session(chat_session)

        system_msgs = [m for m in chat_session.conversation.messages if m.role == "system"]
        non_summary = [m for m in system_msgs if "[Conversation summary]" not in m.content]
        assert len(non_summary) == 2


# ---------------------------------------------------------------------------
# memory/workflow.py - schedule_memory_extraction
# ---------------------------------------------------------------------------


class TestMemoryWorkflow:
    def test_skips_when_no_memory(self) -> None:
        # Should not raise even with no memory store
        schedule_memory_extraction(
            config=MagicMock(),
            memory=None,
            user_input="question",
            reply="a" * 200,
            evidence="",
        )

    def test_skips_empty_exchange(self) -> None:
        memory = MagicMock()
        schedule_memory_extraction(
            config=MagicMock(),
            memory=memory,
            user_input="",
            reply="",
            evidence="",
        )
        # No thread should be started for empty exchanges

    def test_launches_extraction_for_non_empty_exchange(self) -> None:
        memory = MagicMock()
        with patch("harness.memory.workflow.extract_and_store", return_value=3) as mock_extract:
            schedule_memory_extraction(
                config=MagicMock(),
                memory=memory,
                user_input="question",
                reply="short",
                evidence="some evidence",
            )
            # Give the daemon thread time to run
            time.sleep(0.3)
            mock_extract.assert_called_once()
