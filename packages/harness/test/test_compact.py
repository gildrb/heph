"""Tests for three-layer context compaction (s06)."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from unittest.mock import MagicMock

import harness.rag.context as rag_context_module
import pytest
from ai.runtime import ApiMessage, Conversation, ToolCallDelta
from harness.agent.compact import (
    KEEP_RECENT,
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
from harness.agent.dispatch import _sync_conversation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _message_text(message: ApiMessage) -> str:
    content = message["content"]
    return content if isinstance(content, str) else ""


def _tool_result(content: str, call_id: str = "call_1") -> ApiMessage:
    return {"role": "tool", "tool_call_id": call_id, "content": content}


def _assistant_with_tools(*tool_names: str) -> ApiMessage:
    """Build an assistant message with tool_calls (call_id = call_N)."""
    calls: list[ToolCallDelta] = []
    for i, name in enumerate(tool_names):
        calls.append(
            {
                "id": f"call_{i + 1}",
                "type": "function",
                "function": {"name": name, "arguments": "{}"},
            }
        )
    return {"role": "assistant", "content": None, "tool_calls": calls}


def _build_messages(n_tool_results: int, result_size: int = 500) -> list[ApiMessage]:
    """Build a message list with *n_tool_results* tool result entries."""
    messages: list[ApiMessage] = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Do stuff"},
    ]
    for _i in range(n_tool_results):
        messages.append(_assistant_with_tools("bash"))
        messages.append(_tool_result("x" * result_size, call_id="call_1"))
    return messages


def _build_multi_exchange(n_exchanges: int = 5) -> list[ApiMessage]:
    """Build a message list with multiple user/assistant exchanges."""
    messages: list[ApiMessage] = [
        {"role": "system", "content": "You are helpful."},
    ]
    for i in range(n_exchanges):
        messages.append({"role": "user", "content": f"exchange_{i}"})
        messages.append({"role": "assistant", "content": f"response_{i}"})
    return messages


# ---------------------------------------------------------------------------
# estimate_messages_tokens
# ---------------------------------------------------------------------------


class TestEstimateMessagesTokens:
    def test_empty(self) -> None:
        assert estimate_messages_tokens([]) == 0

    def test_text_messages(self, monkeypatch) -> None:
        monkeypatch.setattr(rag_context_module, "_encoder", None)

        msgs: list[ApiMessage] = [
            {"role": "user", "content": "a" * 400},
            {"role": "assistant", "content": "b" * 400},
        ]
        tokens = estimate_messages_tokens(msgs)
        # 800 chars / 4 chars-per-token = 200
        assert tokens == 200

    def test_includes_tool_calls(self) -> None:
        msgs: list[ApiMessage] = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": '{"command": "ls"}',
                        },
                    }
                ],
            },
        ]
        tokens = estimate_messages_tokens(msgs)
        assert tokens > 0


# ---------------------------------------------------------------------------
# micro_compact (Layer 1)
# ---------------------------------------------------------------------------


class TestMicroCompact:
    def test_no_tool_results(self) -> None:
        messages: list[ApiMessage] = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
        ]
        assert micro_compact(messages) == 0
        assert messages[1]["content"] == "hi"

    def test_few_results_unchanged(self) -> None:
        """If tool results <= KEEP_RECENT, nothing is replaced."""
        messages = _build_messages(KEEP_RECENT, result_size=500)
        replaced = micro_compact(messages)
        assert replaced == 0

    def test_replaces_old_results(self) -> None:
        """Old tool results (beyond KEEP_RECENT) are replaced."""
        messages = _build_messages(KEEP_RECENT + 3, result_size=500)
        replaced = micro_compact(messages)
        assert replaced == 3

        # The last KEEP_RECENT tool results should be untouched
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        for msg in tool_msgs[-KEEP_RECENT:]:
            assert len(str(msg["content"])) == 500

        # The older ones should be placeholders
        for msg in tool_msgs[:-KEEP_RECENT]:
            assert str(msg["content"]).startswith("[Previous: used")

    def test_preserves_short_results(self) -> None:
        """Results shorter than PLACEHOLDER_THRESHOLD are left alone."""
        messages = _build_messages(KEEP_RECENT + 2, result_size=10)
        replaced = micro_compact(messages)
        assert replaced == 0

    def test_finds_tool_name(self) -> None:
        """Placeholder references the correct tool name."""
        messages: list[ApiMessage] = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "go"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_99",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": "{}"},
                    }
                ],
            },
            _tool_result("x" * 500, call_id="call_99"),
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "bash", "arguments": "{}"},
                    }
                ],
            },
            _tool_result("y" * 500, call_id="call_1"),
            _tool_result("z" * 500, call_id="call_1"),
            _tool_result("w" * 500, call_id="call_1"),
        ]
        replaced = micro_compact(messages, keep_recent=3)
        assert replaced == 1
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        assert "read_file" in str(tool_msgs[0]["content"])

    def test_custom_keep_recent(self) -> None:
        messages = _build_messages(5, result_size=500)
        replaced = micro_compact(messages, keep_recent=1)
        assert replaced == 4


# ---------------------------------------------------------------------------
# auto_compact (Layer 2 / Layer 3)
# ---------------------------------------------------------------------------


class TestAutoCompact:
    @staticmethod
    def _mock_config_and_client(summary: str = "Summary of conversation."):
        """Return (config, mock_client) for testing auto_compact."""
        config = MagicMock()
        config.model = "gpt-4o-mini"

        mock_message = MagicMock()
        mock_message.content = summary
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        return config, mock_client

    def test_saves_transcript(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A JSONL transcript file is created under .harness/transcripts/."""
        messages = _build_messages(3)
        config, mock_client = self._mock_config_and_client()
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        auto_compact(messages, config, tmp_path)

        transcript_dir = tmp_path / ".harness" / "transcripts"
        assert transcript_dir.is_dir()
        files = list(transcript_dir.glob("transcript_*.jsonl"))
        assert len(files) == 1

        # Transcript should contain original messages
        lines = files[0].read_text().strip().splitlines()
        assert len(lines) == len(messages)
        for line in lines:
            parsed = json.loads(line)
            assert "role" in parsed

    @pytest.mark.skipif(
        os.name == "nt", reason="POSIX permission bits are not portable on Windows"
    )
    def test_transcript_uses_private_permissions_and_redacts_secrets(
        self,
        tmp_path: Path,
    ) -> None:
        messages: list[ApiMessage] = [
            {"role": "system", "content": "You are helpful."},
            {
                "role": "user",
                "content": "run with token=compact-secret",
                "tool_metadata": {"api_key": "compact-secret"},
            },
        ]

        auto_compact(messages, MagicMock(), tmp_path)

        transcript_dir = tmp_path / ".harness" / "transcripts"
        transcript_path = next(transcript_dir.glob("transcript_*.jsonl"))
        serialized = transcript_path.read_text(encoding="utf-8")
        assert stat.S_IMODE(transcript_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE(transcript_path.stat().st_mode) == 0o600
        assert "compact-secret" not in serialized
        assert "***REDACTED***" in serialized

    def test_transcript_rejects_symlinked_state_dir(self, tmp_path: Path) -> None:
        messages = _build_messages(3)
        outside = tmp_path / "outside"
        outside.mkdir()
        internal = tmp_path / ".harness"
        internal.mkdir()
        try:
            (internal / "transcripts").symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks are not supported on this filesystem")

        with pytest.raises(OSError, match="must not be a symlink"):
            auto_compact(messages, MagicMock(), tmp_path)

        assert list(outside.iterdir()) == []

    def test_returns_compressed_messages(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Result has system messages + a summary + recent exchanges."""
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client()
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        compressed = auto_compact(messages, config, tmp_path)

        system_msgs = [m for m in compressed if m["role"] == "system"]
        assert len(system_msgs) == 2

        summary_msgs = [
            m
            for m in compressed
            if m["role"] == "system" and "[Earlier conversation summary]" in _message_text(m)
        ]
        assert len(summary_msgs) == 1
        assert "untrusted historical context" in _message_text(summary_msgs[0])

    def test_preserves_recent_exchanges(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Recent exchanges are kept verbatim, not summarized."""
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client()
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        compressed = auto_compact(messages, config, tmp_path, keep_recent_exchanges=2)

        user_msgs = [m for m in compressed if m["role"] == "user"]
        recent_user_contents = [
            _message_text(m)
            for m in user_msgs
            if "[Earlier conversation summary]" not in _message_text(m)
        ]
        assert any("exchange_4" in c for c in recent_user_contents)
        assert any("exchange_3" in c for c in recent_user_contents)

    def test_summary_content(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The mock LLM summary appears in the compressed output."""
        messages = _build_multi_exchange(n_exchanges=4)
        config, mock_client = self._mock_config_and_client(summary="Key fact: the answer is 42.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        compressed = auto_compact(messages, config, tmp_path)
        summary_msgs = [
            m
            for m in compressed
            if m["role"] == "system" and "[Earlier conversation summary]" in _message_text(m)
        ]
        assert any("42" in _message_text(message) for message in summary_msgs)

    def test_first_compaction_saves_summary_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client(summary="Cached summary.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        compressed = auto_compact(messages, config, tmp_path)

        cache_files = list((tmp_path / ".harness" / "compaction_cache").glob("*.txt"))
        assert len(cache_files) == 1
        assert cache_files[0].read_text(encoding="utf-8") == "Cached summary."
        assert any("Cached summary." in _message_text(message) for message in compressed)

    @pytest.mark.skipif(
        os.name == "nt", reason="POSIX permission bits are not portable on Windows"
    )
    def test_summary_cache_uses_private_permissions_and_redacts_secrets(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client(summary="summary token=compact-secret")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        auto_compact(messages, config, tmp_path)

        cache_dir = tmp_path / ".harness" / "compaction_cache"
        cache_path = next(cache_dir.glob("*.txt"))
        serialized = cache_path.read_text(encoding="utf-8")
        assert stat.S_IMODE(cache_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE(cache_path.stat().st_mode) == 0o600
        assert "compact-secret" not in serialized
        assert "***REDACTED***" in serialized

    def test_summary_request_uses_sanitized_history(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        messages: list[ApiMessage] = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "old token=compact-secret"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": "password=compact-secret",
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "secret=compact-secret",
                "tool_metadata": {"api_key": "compact-secret"},
                "tool_error": "token=compact-secret",
            },
            {"role": "user", "content": "current request"},
            {"role": "assistant", "content": "current answer"},
        ]
        config, mock_client = self._mock_config_and_client(summary="Safe summary.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        auto_compact(messages, config, tmp_path, keep_recent_exchanges=1)

        request_messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        serialized_request = json.dumps(request_messages, default=str)
        assert "compact-secret" not in serialized_request
        assert "tool_metadata" not in serialized_request
        assert "tool_error" not in serialized_request
        assert "password=compact-secret" not in serialized_request
        assert "***REDACTED***" in serialized_request

    def test_unavailable_summary_is_not_cached(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        messages = _build_multi_exchange(n_exchanges=5)
        config, empty_client = self._mock_config_and_client(summary="")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: empty_client,
        )

        compressed = auto_compact(messages, config, tmp_path)

        assert any("(summary unavailable)" in _message_text(message) for message in compressed)
        cache_dir = tmp_path / ".harness" / "compaction_cache"
        assert not list(cache_dir.glob("*.txt"))

        _config, retry_client = self._mock_config_and_client(summary="Recovered summary.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: retry_client,
        )

        retried = auto_compact(messages, config, tmp_path)

        retry_client.chat.completions.create.assert_called_once()
        assert any("Recovered summary." in _message_text(message) for message in retried)
        cache_files = list(cache_dir.glob("*.txt"))
        assert len(cache_files) == 1
        assert cache_files[0].read_text(encoding="utf-8") == "Recovered summary."

    def test_identical_compaction_reuses_summary_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client(summary="Cached summary.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )
        auto_compact(messages, config, tmp_path)

        failing_client = MagicMock()
        failing_client.chat.completions.create.side_effect = AssertionError("unexpected LLM call")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: failing_client,
        )

        compressed = auto_compact(messages, config, tmp_path)

        failing_client.chat.completions.create.assert_not_called()
        assert any("Cached summary." in _message_text(message) for message in compressed)

    def test_changed_compaction_messages_use_new_summary_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        messages = _build_multi_exchange(n_exchanges=5)
        config, first_client = self._mock_config_and_client(summary="First summary.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: first_client,
        )
        auto_compact(messages, config, tmp_path)

        changed = _build_multi_exchange(n_exchanges=5)
        changed[1]["content"] = "changed_exchange_0"
        _config, second_client = self._mock_config_and_client(summary="Second summary.")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: second_client,
        )

        compressed = auto_compact(changed, config, tmp_path)

        second_client.chat.completions.create.assert_called_once()
        cache_files = list((tmp_path / ".harness" / "compaction_cache").glob("*.txt"))
        assert len(cache_files) == 2
        assert any("Second summary." in _message_text(message) for message in compressed)

    def test_returns_original_on_llm_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If the summarisation LLM call fails, original messages are returned."""
        messages = _build_messages(3)
        config = MagicMock()
        config.model = "gpt-4o-mini"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("no API key")
        monkeypatch.setattr(
            "harness.agent.compact.build_client",
            lambda _c: mock_client,
        )

        result = auto_compact(messages, config, tmp_path)
        # Same list returned - no crash, no compression
        assert result is messages
        assert len(result) == len(messages)

        # Transcript still saved even though summarisation failed
        transcript_dir = tmp_path / ".harness" / "transcripts"
        assert transcript_dir.is_dir()
        assert len(list(transcript_dir.glob("transcript_*.jsonl"))) == 1


# ---------------------------------------------------------------------------
# _sync_conversation
# ---------------------------------------------------------------------------


class TestSyncConversation:
    def test_rebuilds_from_api_messages(self) -> None:
        conv = Conversation()
        conv.add("system", "old system")
        conv.add("user", "old user")

        api_messages: list[ApiMessage] = [
            {"role": "system", "content": "new system"},
            {"role": "system", "content": "[Earlier conversation summary]\n\nSummary here"},
        ]
        _sync_conversation(conv, api_messages)

        assert len(conv.messages) == 2
        assert conv.messages[0].content == "new system"
        assert "Summary here" in conv.messages[1].content

    def test_skips_tool_messages(self) -> None:
        conv = Conversation()
        api_messages: list[ApiMessage] = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "tool", "tool_call_id": "c1", "content": "output"},
        ]
        _sync_conversation(conv, api_messages)
        assert len(conv.messages) == 2

    def test_skips_none_content(self) -> None:
        conv = Conversation()
        api_messages: list[ApiMessage] = [
            {"role": "assistant", "content": None, "tool_calls": []},
            {"role": "assistant", "content": "text reply"},
        ]
        _sync_conversation(conv, api_messages)
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "text reply"
