from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.armory.state_files import (
    ArmoryStateError,
    read_armory_state_text,
    write_armory_state_text,
)
from harness.chat.automation import iter_chat_events
from harness.chat.session import SessionBusyError, create_plain_session, create_session
from harness.chat.orchestrator import TurnOrchestrator
from harness.chat.turn_contract import TurnIntentResolution
from harness.rag.index import build_index
from harness.agent import model_stream
from harness.chat.storage import _conversation_from_data, save, load
from harness.agent.dispatch import iter_agent_events
from harness.agent.tool_execution import execute_tool_calls
from ai.runtime import CompletionDelta
from harness.documents import RecallState
from heph.cli.main import build_parser
from ai.runtime import ChatConfig, Conversation

def armory(tmp_path: Path) -> Path:
    root = tmp_path / "armory"
    (root / "materials").mkdir(parents=True)
    (root / ".harness").mkdir()
    return root

def test_state_write_replaces_atomically_and_rejects_escape(tmp_path: Path) -> None:
    root = armory(tmp_path)
    write_armory_state_text(root, ".harness/state.json", "{\"v\": 1}\n")
    write_armory_state_text(root, ".harness/state.json", "{\"v\": 2}\n")
    assert json.loads(read_armory_state_text(root, ".harness/state.json"))["v"] == 2
    with pytest.raises(ArmoryStateError):
        write_armory_state_text(root, ".harness/../escape", "bad")

def test_session_decode_ignores_invalid_messages() -> None:
    conversation = _conversation_from_data({"messages": [
        {"role": "user", "content": "ok"},
        {"role": "root", "content": "fake"},
        {"role": "assistant", "content": 4},
    ]})
    assert [(m.role, m.content) for m in conversation.messages] == [("user", "ok")]

def test_documents_exports_only_core_turn_types() -> None:
    assert RecallState().to_dict()["phase"]

def test_sdk_surface_is_not_a_cli_dependency() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["sdk", "serve"])


def test_session_rejects_concurrent_turns() -> None:
    session = create_plain_session(ChatConfig())
    assert session._turn_lock.acquire(blocking=False)
    try:
        with pytest.raises(SessionBusyError):
            next(iter_chat_events(session, "second"))
    finally:
        session._turn_lock.release()


def test_session_persists_tool_calls_and_results(tmp_path: Path) -> None:
    root = armory(tmp_path)
    conversation = Conversation()
    conversation.add("system", "system")
    conversation.add_api_message({
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": "read_file", "arguments": "{}"}}],
    })
    conversation.add_api_message({
        "role": "tool",
        "tool_call_id": "call-1",
        "content": "result",
        "tool_success": True,
    })
    save(root, "session", conversation)
    loaded, _ = load(root, "session")
    messages = loaded.to_api_messages()
    assert messages[1]["tool_calls"][0]["id"] == "call-1"
    assert messages[2]["role"] == "tool"
    assert messages[2]["tool_call_id"] == "call-1"



def test_agent_reports_malformed_tool_arguments_and_types(tmp_path: Path) -> None:
    malformed = execute_tool_calls(
        [{"id": "call-1", "type": "function", "function": {"name": "read_file", "arguments": "{"}}],
        tmp_path,
    )
    assert malformed[0]["tool_success"] is False
    assert "invalid JSON" in str(malformed[0]["content"])

    wrong_type = execute_tool_calls(
        [{"id": "call-2", "type": "function", "function": {"name": "read_file", "arguments": '{"path": 3}'}}],
        tmp_path,
    )
    assert wrong_type[0]["tool_success"] is False
    assert "must be string" in str(wrong_type[0]["content"])

def test_agent_blocks_unknown_tools(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_stream(*_args: object, **_kwargs: object):
        yield CompletionDelta(
            tool_calls=[{
                "id": "call-unknown",
                "type": "function",
                "function": {"name": "delete_everything", "arguments": "{}"},
            }],
            finish_reason="tool_calls",
        )

    monkeypatch.setattr(model_stream, "stream_completion", fake_stream)
    events = list(iter_agent_events(ChatConfig(model="fake"), Conversation(), tmp_path))
    assert any(getattr(event, "kind", "") == "guardrail" for event in events)
    assert events[-1].finish_reason == "guardrail"


def test_agent_can_disable_tools_for_non_tool_calling_models(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_stream(*_args: object, **kwargs: object):
        captured["tools"] = kwargs.get("tools")
        yield CompletionDelta(content="answer", finish_reason="stop")

    monkeypatch.setattr(model_stream, "stream_completion", fake_stream)
    config = ChatConfig(model="math", feature_flags=frozenset({"disable_tools"}))
    events = list(
        iter_agent_events(
            config,
            Conversation(),
            tmp_path,
            allowed_tool_names=("read_file",),
        )
    )
    assert events[-1].finish_reason == "stop"
    assert captured["tools"] is None


def test_agent_persists_allowed_tool_messages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("grounded fact", encoding="utf-8")
    calls = 0

    def fake_stream(*_args: object, **_kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 1:
            yield CompletionDelta(
                tool_calls=[{
                    "id": "call-read",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path":"note.md"}'},
                }],
                finish_reason="tool_calls",
            )
        else:
            yield CompletionDelta(content="The note says grounded fact [E1].", finish_reason="stop")

    monkeypatch.setattr(model_stream, "stream_completion", fake_stream)
    conversation = Conversation()
    events = list(iter_agent_events(ChatConfig(model="fake"), conversation, tmp_path))
    assert events[-1].finish_reason == "stop"
    assert [message.role for message in conversation.messages] == ["assistant", "tool", "assistant"]
    assert conversation.messages[0].metadata["tool_calls"][0]["id"] == "call-read"
    assert conversation.messages[1].metadata["tool_call_id"] == "call-read"



def test_armory_tool_history_survives_document_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = armory(tmp_path)
    (root / "materials" / "facts.md").write_text("Ada Lovelace wrote the first algorithm.", encoding="utf-8")
    build_index(root)
    session = create_session(ChatConfig(base_url="https://fake.local/v1", model="fake"), root)
    calls = 0

    def fake_stream(*_args: object, **_kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 1:
            yield CompletionDelta(
                tool_calls=[{"id": "call-open", "type": "function", "function": {"name": "open_material", "arguments": '{"source":"materials/facts.md"}'}}],
                finish_reason="tool_calls",
            )
        else:
            yield CompletionDelta(content="Ada Lovelace wrote the first algorithm [E1].", finish_reason="stop")

    monkeypatch.setattr(model_stream, "stream_completion", fake_stream)
    monkeypatch.setattr(
        "harness.chat.intent_resolution._resolved_user_intent",
        lambda *_args, **_kwargs: TurnIntentResolution(
            intent="topic_presentation", retrieval_query="Ada Lovelace"
        ),
    )
    orchestrator = TurnOrchestrator(session)
    events = list(orchestrator.iter_events("Explain the fact."))
    assert events[-1].finish_reason == "stop"
    api_messages = session.conversation.to_api_messages()
    assert any(message.get("tool_calls") for message in api_messages)
    assert any(message.get("role") == "tool" for message in api_messages)

def test_agent_abort_and_length_are_not_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def truncated(*_args: object, **_kwargs: object):
        yield CompletionDelta(content="partial", finish_reason="length")

    monkeypatch.setattr(model_stream, "stream_completion", truncated)
    truncated_events = list(iter_agent_events(ChatConfig(model="fake"), Conversation(), tmp_path))
    assert truncated_events[-1].finish_reason == "length"

    abort = __import__("threading").Event()
    abort.set()
    aborted_events = list(iter_agent_events(
        ChatConfig(model="fake"), Conversation(), tmp_path, abort=abort
    ))
    assert aborted_events[-1].finish_reason == "aborted"


def test_armory_answer_is_grounded_and_cited(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = armory(tmp_path)
    (root / "materials" / "facts.md").write_text(
        "Ada Lovelace wrote the first algorithm intended for a machine.\n",
        encoding="utf-8",
    )
    build_index(root)
    config = ChatConfig(base_url="https://fake.local/v1", model="fake")
    session = create_session(config, root)

    def fake_stream(*_args: object, **_kwargs: object):
        yield CompletionDelta(
            content="Ada Lovelace wrote the first algorithm intended for a machine [E1].",
            finish_reason="stop",
        )

    monkeypatch.setattr(model_stream, "stream_completion", fake_stream)
    monkeypatch.setattr(
        "harness.chat.intent_resolution._resolved_user_intent",
        lambda *_args, **_kwargs: TurnIntentResolution(
            intent="source_qa",
            canonical_request="Who wrote the first algorithm?",
            retrieval_query="Who wrote the first algorithm?",
            confidence=1.0,
            direct_evidence_required=True,
        ),
    )
    orchestrator = TurnOrchestrator(session)
    events = list(orchestrator.iter_events("Who wrote the first algorithm?"))
    assert orchestrator.turn_status == "success"
    assert orchestrator.last_reply.endswith("[E1].")
    assert events[-1].finish_reason == "stop"


def test_plain_length_is_failed_and_persists_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    from harness.chat import turn_execution

    def truncated(*_args: object, **_kwargs: object):
        yield CompletionDelta(content="partial", finish_reason="length")

    monkeypatch.setattr(turn_execution, "stream_completion", truncated)
    session = create_plain_session(ChatConfig(base_url="https://fake.local/v1", model="fake"))
    orchestrator = TurnOrchestrator(session)
    events = list(orchestrator.iter_events("hello"))
    assert events[-1].finish_reason == "length"
    assert orchestrator.turn_status == "failed"
    assert session.conversation.messages[-1].content == "partial"
