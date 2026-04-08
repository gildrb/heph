"""Tests for memory extraction from conversation exchanges."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from hephaistos.chat.engine import ChatConfig
from hephaistos.memory import MemoryStore
from hephaistos.memory.extract import extract_and_store, extract_from_exchange


def _make_config() -> ChatConfig:
    return ChatConfig(
        api_key="test-key",
        base_url="http://localhost/v1",
        model="test-model",
    )


def _mock_llm_response(content: str | None) -> MagicMock:
    """Build a mock OpenAI response object."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# extract_from_exchange
# ---------------------------------------------------------------------------


class TestExtractFromExchange:
    def test_short_content_returns_empty(self) -> None:
        config = _make_config()
        result = extract_from_exchange(config, "hi", "short reply")
        assert result == []

    def test_extracts_valid_json(self) -> None:
        config = _make_config()
        entries = [
            {"topic": "TCP handshake", "content": "3-way: SYN, SYN-ACK, ACK", "source": "notes"},
        ]
        mock_response = _mock_llm_response(json.dumps(entries))

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(
                config,
                "What is TCP?",
                "TCP uses a 3-way handshake: SYN, SYN-ACK, ACK. "
                "This is a fundamental concept in computer networking.",
            )

        assert len(result) == 1
        assert result[0]["topic"] == "TCP handshake"
        assert "SYN" in result[0]["content"]
        assert result[0]["source"] == "notes"

    def test_strips_markdown_code_fences(self) -> None:
        config = _make_config()
        entries = [{"topic": "DNS", "content": "Domain name system", "source": "networking"}]
        fenced = f"```json\n{json.dumps(entries)}\n```"
        mock_response = _mock_llm_response(fenced)

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(
                config,
                "What is DNS?",
                "DNS resolves domain names to IP addresses. "
                "It is a foundational part of how the internet works, "
                "translating human-readable names into routable addresses.",
            )

        assert len(result) == 1
        assert result[0]["topic"] == "DNS"

    def test_empty_array_returns_empty(self) -> None:
        config = _make_config()
        mock_response = _mock_llm_response("[]")

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(
                config,
                "hello",
                "a" * 200,  # long enough to pass min length
            )

        assert result == []

    def test_invalid_json_returns_empty(self) -> None:
        config = _make_config()
        mock_response = _mock_llm_response("not valid json {{{")

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert result == []

    def test_non_list_json_returns_empty(self) -> None:
        config = _make_config()
        mock_response = _mock_llm_response('{"topic": "not a list"}')

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert result == []

    def test_skips_entries_without_topic_or_content(self) -> None:
        config = _make_config()
        entries = [
            {"topic": "", "content": "has content but no topic"},
            {"topic": "has topic", "content": ""},
            {"topic": "valid", "content": "both present"},
        ]
        mock_response = _mock_llm_response(json.dumps(entries))

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert len(result) == 1
        assert result[0]["topic"] == "valid"

    def test_skips_non_dict_entries(self) -> None:
        config = _make_config()
        entries = ["not a dict", 42, {"topic": "ok", "content": "fine"}]
        mock_response = _mock_llm_response(json.dumps(entries))

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert len(result) == 1

    def test_truncates_long_topic_and_content(self) -> None:
        config = _make_config()
        entries = [{"topic": "x" * 200, "content": "y" * 1000, "source": "test"}]
        mock_response = _mock_llm_response(json.dumps(entries))

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert len(result[0]["topic"]) == 100
        assert len(result[0]["content"]) == 500

    def test_llm_exception_returns_empty(self) -> None:
        config = _make_config()

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API error")
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert result == []

    def test_null_content_in_response(self) -> None:
        config = _make_config()
        mock_response = _mock_llm_response(None)

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            result = extract_from_exchange(config, "question", "a" * 200)

        assert result == []

    def test_uses_deterministic_temperature(self) -> None:
        config = _make_config()
        mock_response = _mock_llm_response("[]")

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            extract_from_exchange(config, "question", "a" * 200)

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["temperature"] == 0.1
        assert call_kwargs.kwargs["stream"] is False


# ---------------------------------------------------------------------------
# extract_and_store
# ---------------------------------------------------------------------------


class TestExtractAndStore:
    def test_stores_entries_and_returns_count(self, tmp_path) -> None:
        config = _make_config()
        memory = MemoryStore(tmp_path)
        entries = [{"topic": "HTTP", "content": "HyperText Transfer Protocol", "source": "web"}]
        mock_response = _mock_llm_response(json.dumps(entries))

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            added = extract_and_store(config, memory, "What is HTTP?", "a" * 200)

        assert added == 1
        assert len(memory.entries) == 1
        assert memory.entries[0].topic == "HTTP"

    def test_returns_zero_when_nothing_extracted(self, tmp_path) -> None:
        config = _make_config()
        memory = MemoryStore(tmp_path)

        # Short content triggers early return
        added = extract_and_store(config, memory, "hi", "short")
        assert added == 0
        assert len(memory.entries) == 0

    def test_does_not_save_when_no_entries(self, tmp_path) -> None:
        config = _make_config()
        memory = MemoryStore(tmp_path)
        mock_response = _mock_llm_response("[]")

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("hephaistos.memory.extract.save_memory") as mock_save:
                added = extract_and_store(config, memory, "q", "a" * 200)

        assert added == 0
        mock_save.assert_not_called()

    def test_saves_memory_when_entries_added(self, tmp_path) -> None:
        config = _make_config()
        memory = MemoryStore(tmp_path)
        entries = [{"topic": "TLS", "content": "Transport Layer Security", "source": "crypto"}]
        mock_response = _mock_llm_response(json.dumps(entries))

        with patch("hephaistos.memory.extract._build_client") as mock_build:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("hephaistos.memory.extract.save_memory") as mock_save:
                added = extract_and_store(config, memory, "q", "a" * 200)

        assert added == 1
        mock_save.assert_called_once_with(memory)
