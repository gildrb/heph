from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hephaion.chat.events import AssistantDeltaEvent
from hephaion.chat.session import ChatSession
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaion.runtime import ChatConfig, Conversation
from scripts import replay_answer_benchmark


def _turn_evidence() -> TurnEvidence:
    chunk = Chunk(
        text="Dijkstra shortest paths use a priority queue.",
        source="materials/graphs.md",
        index=0,
        char_start=0,
        char_end=45,
    )
    return TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E1",
                chunk=chunk,
                score=0.9,
                content=chunk.text,
            ),
        )
    )


def _session_with_evidence() -> ChatSession:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="bench-session",
        armory_path=Path("/tmp/armory"),
    )
    object.__setattr__(session, "trace", MagicMock())
    session.last_turn_evidence = _turn_evidence()
    return session


def test_load_cases_supports_jsonl(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "dijkstra",
                        "domain": "computer-science",
                        "task": "grounded-explanation",
                        "prompt": "How does Dijkstra choose nodes?",
                        "expected_citations": ["E1"],
                        "must_include": ["priority queue"],
                        "min_words": 5,
                        "min_citation_count": 1,
                        "min_distinct_sources": 1,
                        "min_bullet_count": 2,
                        "min_cited_bullet_count": 2,
                        "max_explicit_date_lines": 1,
                        "supported_claims": [
                            {"text": "priority queue", "evidence_id": "E1"},
                        ],
                    }
                ),
                "# comment",
                json.dumps(
                    {
                        "prompt": "What is absent?",
                        "require_citations": False,
                        "require_abstention": True,
                        "required_label": "PARTIAL",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = replay_answer_benchmark.load_cases(dataset)

    assert [case.case_id for case in cases] == ["dijkstra", "case-2"]
    assert cases[0].domain == "computer-science"
    assert cases[0].task == "grounded-explanation"
    assert cases[0].expected_citations == ("E1",)
    assert cases[0].must_include == ("priority queue",)
    assert cases[0].min_words == 5
    assert cases[0].min_bullet_count == 2
    assert cases[0].min_cited_bullet_count == 2
    assert cases[0].max_explicit_date_lines == 1
    assert cases[0].min_citation_count == 1
    assert cases[0].min_distinct_sources == 1
    assert cases[0].supported_claims == ({"text": "priority queue", "evidence_id": "E1"},)
    assert cases[1].require_citations is False
    assert cases[1].require_abstention is True
    assert cases[1].required_label == "PARTIAL"


def test_load_cases_rejects_unscored_replay_prompt(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    dataset.write_text(
        json.dumps({"id": "loose", "prompt": "Tell me something useful."}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="answer-contract check"):
        replay_answer_benchmark.load_cases(dataset)


def test_load_cases_rejects_empty_replay_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "replay.jsonl"
    dataset.write_text("# comments only\n\n", encoding="utf-8")

    with pytest.raises(ValueError, match="does not contain any cases"):
        replay_answer_benchmark.load_cases(dataset)


def test_replay_cases_captures_answer_and_turn_evidence() -> None:
    session = _session_with_evidence()
    cases = [
        replay_answer_benchmark.ReplayCase(
            case_id="dijkstra",
            prompt="How does Dijkstra choose nodes?",
            domain="computer-science",
            task="grounded-explanation",
            expected_citations=("E1",),
            must_include=("priority queue",),
            min_words=4,
            min_citation_count=1,
            min_distinct_sources=1,
            min_bullet_count=2,
            min_cited_bullet_count=2,
            max_explicit_date_lines=1,
            required_label="CORRECT",
            supported_claims=({"text": "priority queue", "evidence_id": "E1"},),
        )
    ]

    with (
        patch("scripts.replay_answer_benchmark.create_session", return_value=session),
        patch(
            "scripts.replay_answer_benchmark.iter_chat_events",
            return_value=[
                AssistantDeltaEvent("Dijkstra uses "),
                AssistantDeltaEvent("a priority queue [E1]."),
            ],
        ),
    ):
        fixtures = replay_answer_benchmark.replay_cases(Path("/tmp/armory"), cases, ChatConfig())

    assert fixtures == [
        {
            "id": "dijkstra",
            "query": "How does Dijkstra choose nodes?",
            "answer": "Dijkstra uses a priority queue [E1].",
            "evidence": [
                {
                    "id": "E1",
                    "source": "materials/graphs.md",
                    "chunk": 0,
                    "text": "Dijkstra shortest paths use a priority queue.",
                    "score": 0.9,
                }
            ],
            "domain": "computer-science",
            "task": "grounded-explanation",
            "expected_citations": ["E1"],
            "must_include": ["priority queue"],
            "min_words": 4,
            "min_citation_count": 1,
            "min_distinct_sources": 1,
            "min_bullet_count": 2,
            "min_cited_bullet_count": 2,
            "max_explicit_date_lines": 1,
            "required_label": "CORRECT",
            "supported_claims": [{"text": "priority queue", "evidence_id": "E1"}],
        }
    ]


def test_write_jsonl_round_trips_fixture(tmp_path: Path) -> None:
    output = tmp_path / "out" / "answers.jsonl"
    fixture: replay_answer_benchmark.AnswerFixture = {
        "id": "case",
        "query": "question",
        "answer": "answer",
        "evidence": [],
        "require_citations": False,
    }

    replay_answer_benchmark.write_jsonl(output, [fixture])

    assert output.read_text(encoding="utf-8") == (
        '{"id": "case", "query": "question", "answer": "answer", '
        '"evidence": [], "require_citations": false}\n'
    )


def test_shaped_material_overview_requires_bullet_shape() -> None:
    unstructured = replay_answer_benchmark.ReplayCase(
        case_id="overview",
        prompt="Summarize the material.",
        task="material-overview",
        min_words=24,
        max_words=120,
        min_citation_count=2,
        min_distinct_sources=2,
    )
    structured = replay_answer_benchmark.ReplayCase(
        case_id="overview",
        prompt="Summarize the material.",
        task="material-overview",
        min_words=24,
        max_words=120,
        min_citation_count=2,
        min_distinct_sources=2,
        min_bullet_count=2,
        min_cited_bullet_count=2,
        max_explicit_date_lines=1,
    )

    assert not replay_answer_benchmark.has_shaped_material_overview_case([unstructured])
    assert replay_answer_benchmark.has_shaped_material_overview_case([structured])
