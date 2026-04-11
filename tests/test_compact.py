"""Tests for three-layer context compaction (s06)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hephaistos.chat.engine import Conversation
from hephaistos.harness.compact import (
    KEEP_RECENT,
    auto_compact,
    estimate_messages_tokens,
    micro_compact,
)
from hephaistos.harness.dispatch import _sync_conversation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_result(content: str, call_id: str = "call_1") -> dict:
    return {"role": "tool", "tool_call_id": call_id, "content": content}


def _assistant_with_tools(*tool_names: str) -> dict:
    """Build an assistant message with tool_calls (call_id = call_N)."""
    calls = []
    for i, name in enumerate(tool_names):
        calls.append(
            {
                "id": f"call_{i + 1}",
                "type": "function",
                "function": {"name": name, "arguments": "{}"},
            }
        )
    return {"role": "assistant", "content": None, "tool_calls": calls}


def _build_messages(n_tool_results: int, result_size: int = 500) -> list[dict]:
    """Build a message list with *n_tool_results* tool result entries."""
    messages: list[dict] = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Do stuff"},
    ]
    for _i in range(n_tool_results):
        messages.append(_assistant_with_tools("bash"))
        messages.append(_tool_result("x" * result_size, call_id="call_1"))
    return messages


def _build_multi_exchange(n_exchanges: int = 5) -> list[dict]:
    """Build a message list with multiple user/assistant exchanges."""
    messages: list[dict] = [
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

    def test_text_messages(self) -> None:
        msgs = [
            {"role": "user", "content": "a" * 400},
            {"role": "assistant", "content": "b" * 400},
        ]
        tokens = estimate_messages_tokens(msgs)
        # 800 chars / 4 chars-per-token = 200
        assert tokens == 200

    def test_includes_tool_calls(self) -> None:
        msgs = [
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
        messages = [
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
            assert len(msg["content"]) == 500

        # The older ones should be placeholders
        for msg in tool_msgs[:-KEEP_RECENT]:
            assert msg["content"].startswith("[Previous: used")

    def test_preserves_short_results(self) -> None:
        """Results shorter than PLACEHOLDER_THRESHOLD are left alone."""
        messages = _build_messages(KEEP_RECENT + 2, result_size=10)
        replaced = micro_compact(messages)
        assert replaced == 0

    def test_finds_tool_name(self) -> None:
        """Placeholder references the correct tool name."""
        messages: list[dict] = [
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
        assert "read_file" in tool_msgs[0]["content"]

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
        """A JSONL transcript file is created under .hephaistos/transcripts/."""
        messages = _build_messages(3)
        config, mock_client = self._mock_config_and_client()
        monkeypatch.setattr("hephaistos.harness.compact._build_client", lambda c: mock_client)

        auto_compact(messages, config, tmp_path)

        transcript_dir = tmp_path / ".hephaistos" / "transcripts"
        assert transcript_dir.is_dir()
        files = list(transcript_dir.glob("transcript_*.jsonl"))
        assert len(files) == 1

        # Transcript should contain original messages
        lines = files[0].read_text().strip().splitlines()
        assert len(lines) == len(messages)
        for line in lines:
            parsed = json.loads(line)
            assert "role" in parsed

    def test_returns_compressed_messages(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Result has system messages + a summary + recent exchanges."""
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client()
        monkeypatch.setattr("hephaistos.harness.compact._build_client", lambda c: mock_client)

        compressed = auto_compact(messages, config, tmp_path)

        system_msgs = [m for m in compressed if m["role"] == "system"]
        assert len(system_msgs) == 1

        summary_msgs = [
            m
            for m in compressed
            if m["role"] == "user" and "[Earlier conversation summary]" in m["content"]
        ]
        assert len(summary_msgs) == 1

    def test_preserves_recent_exchanges(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Recent exchanges are kept verbatim, not summarized."""
        messages = _build_multi_exchange(n_exchanges=5)
        config, mock_client = self._mock_config_and_client()
        monkeypatch.setattr("hephaistos.harness.compact._build_client", lambda c: mock_client)

        compressed = auto_compact(messages, config, tmp_path, keep_recent_exchanges=2)

        user_msgs = [m for m in compressed if m["role"] == "user"]
        recent_user_contents = [
            m["content"] for m in user_msgs if "[Earlier conversation summary]" not in m["content"]
        ]
        assert any("exchange_4" in c for c in recent_user_contents)
        assert any("exchange_3" in c for c in recent_user_contents)

    def test_summary_content(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The mock LLM summary appears in the compressed output."""
        messages = _build_multi_exchange(n_exchanges=4)
        config, mock_client = self._mock_config_and_client(summary="Key fact: the answer is 42.")
        monkeypatch.setattr("hephaistos.harness.compact._build_client", lambda c: mock_client)

        compressed = auto_compact(messages, config, tmp_path)
        summary_msgs = [m for m in compressed if m["role"] == "user"]
        assert any("42" in m["content"] for m in summary_msgs)

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
        monkeypatch.setattr("hephaistos.harness.compact._build_client", lambda c: mock_client)

        result = auto_compact(messages, config, tmp_path)
        # Same list returned — no crash, no compression
        assert result is messages
        assert len(result) == len(messages)

        # Transcript still saved even though summarisation failed
        transcript_dir = tmp_path / ".hephaistos" / "transcripts"
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

        api_messages = [
            {"role": "system", "content": "new system"},
            {"role": "user", "content": "[Earlier conversation summary]\n\nSummary here"},
        ]
        _sync_conversation(conv, api_messages)

        assert len(conv.messages) == 2
        assert conv.messages[0].content == "new system"
        assert "Summary here" in conv.messages[1].content

    def test_skips_tool_messages(self) -> None:
        conv = Conversation()
        api_messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "tool", "tool_call_id": "c1", "content": "output"},
        ]
        _sync_conversation(conv, api_messages)
        assert len(conv.messages) == 2

    def test_skips_none_content(self) -> None:
        conv = Conversation()
        api_messages = [
            {"role": "assistant", "content": None, "tool_calls": []},
            {"role": "assistant", "content": "text reply"},
        ]
        _sync_conversation(conv, api_messages)
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "text reply"
