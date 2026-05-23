from __future__ import annotations

import json
from pathlib import Path

from hephaistos.rag import Chunk, EvidenceChunk, TurnEvidence
from scripts import benchmark_answers


def _evidence() -> list[benchmark_answers.RawEvidence]:
    return [
        {
            "id": "E1",
            "source": "materials/graphs.md",
            "chunk": 0,
            "text": "Dijkstra shortest paths use a priority queue.",
            "score": 0.9,
        }
    ]


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


def test_load_cases_supports_jsonl_and_defaults_citation_requirement(tmp_path: Path) -> None:
    dataset = tmp_path / "answers.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "grounded",
                        "domain": "computer-science",
                        "query": "How does Dijkstra work?",
                        "task": "grounded-explanation",
                        "answer": "It uses a priority queue [E1].",
                        "evidence": _evidence(),
                        "expected_citations": ["E1"],
                        "must_include": ["priority queue"],
                        "max_explicit_date_lines": 1,
                        "supported_claims": [
                            {"text": "priority queue", "evidence_id": "E1"},
                        ],
                    }
                ),
                "# comment",
                json.dumps(
                    {
                        "answer": "The sources do not contain that answer.",
                        "require_citations": False,
                        "require_abstention": True,
                        "required_label": "PARTIAL",
                        "must_not_include": ["outside knowledge"],
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = benchmark_answers.load_cases(dataset)

    assert [case.case_id for case in cases] == ["grounded", "case-2"]
    assert cases[0].domain == "computer-science"
    assert cases[0].task == "grounded-explanation"
    assert cases[0].require_citations is True
    assert cases[0].expected_citations == ("E1",)
    assert cases[0].evidence_kinds == (("E1", "source"),)
    assert cases[0].allowed_citation_kinds == ("source",)
    assert cases[0].supported_claims == (
        benchmark_answers.SupportedClaim(text="priority queue", evidence_id="E1"),
    )
    assert cases[0].max_explicit_date_lines == 1
    assert cases[1].require_citations is False
    assert cases[1].require_abstention is True
    assert cases[1].required_label == "PARTIAL"


def test_load_cases_parses_citation_evidence_kind_scope(tmp_path: Path) -> None:
    dataset = tmp_path / "answers.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "tool-cited",
                        "answer": "The calculator result is 42 [E2].",
                        "evidence": [
                            {
                                "id": "E2",
                                "source": "tool://calculator",
                                "chunk": 0,
                                "text": "The calculator result is 42.",
                                "kind": "Tool Result",
                            }
                        ],
                        "allowed_citation_kinds": ["source", "tool_result"],
                        "contradicted_claims": [
                            {"text": "result is 41", "evidence_id": "E2"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cases = benchmark_answers.load_cases(dataset)

    assert cases[0].evidence_kinds == (("E2", "tool_result"),)
    assert cases[0].allowed_citation_kinds == ("source", "tool_result")
    assert cases[0].contradicted_claims == (
        benchmark_answers.SupportedClaim(text="result is 41", evidence_id="E2"),
    )


def test_run_benchmark_scores_grounding_failures() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="pass",
            domain="computer-science",
            query="How does Dijkstra work?",
            task="grounded-explanation",
            answer="Dijkstra uses a priority queue [E1].",
            evidence=_turn_evidence(),
            expected_citations=("E1",),
            must_include=("priority queue",),
            must_not_include=("negative weights",),
            supported_claims=(
                benchmark_answers.SupportedClaim(text="priority queue", evidence_id="E1"),
            ),
        ),
        benchmark_answers.AnswerCase(
            case_id="fail",
            domain="computer-science",
            query="How does Dijkstra work?",
            task="grounded-explanation",
            answer="Dijkstra supports negative weights [E9].",
            evidence=_turn_evidence(),
            expected_citations=("E1",),
            must_include=("priority queue",),
            must_not_include=("negative weights",),
            supported_claims=(
                benchmark_answers.SupportedClaim(text="priority queue", evidence_id="E1"),
            ),
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.cases == 2
    assert report.domains == ("computer-science",)
    assert report.tasks == ("grounded-explanation",)
    assert report.pass_rate == 0.5
    assert report.citation_validity_rate == 0.5
    assert report.expected_citation_rate == 0.5
    assert report.citation_source_rate == 1.0
    assert report.required_text_rate == 0.5
    assert report.forbidden_text_rate == 0.5
    assert report.supported_claim_rate == 0.5
    assert report.contradiction_rate == 1.0
    assert report.answer_shape_rate == 1.0
    assert report.required_label_rate == 1.0
    assert report.failures == ("fail",)
    assert report.results[1].answer_excerpt == "Dijkstra supports negative weights [E9]."
    assert report.results[1].evidence_refs == ("E1:materials/graphs.md#chunk=0",)
    assert report.results[1].word_count == 5
    assert report.results[1].citation_count == 1
    assert report.results[1].distinct_cited_sources == 0
    assert report.results[1].bullet_count == 0
    assert report.results[1].cited_bullet_count == 0


def test_answer_benchmark_rejects_memory_or_tool_citations_by_default() -> None:
    memory_chunk = Chunk(
        text="The learner recently practiced Bellman-Ford.",
        source="memory://study-state",
        index=0,
        char_start=0,
        char_end=45,
    )
    evidence = TurnEvidence(
        (
            _turn_evidence().items[0],
            EvidenceChunk(
                evidence_id="E2",
                chunk=memory_chunk,
                score=1.0,
                content=memory_chunk.text,
            ),
        )
    )
    case = benchmark_answers.AnswerCase(
        case_id="memory-citation",
        answer="The learner recently practiced Bellman-Ford [E2].",
        evidence=evidence,
        expected_citations=("E2",),
        evidence_kinds=(("E1", "source"), ("E2", "memory")),
    )

    report = benchmark_answers.run_benchmark([case])

    assert report.pass_rate == 0.0
    assert report.citation_validity_rate == 1.0
    assert report.citation_source_rate == 0.0
    assert report.results[0].invalid_citation_kinds == ("E2:memory",)


def test_answer_benchmark_allows_explicit_tool_citation_scope() -> None:
    tool_chunk = Chunk(
        text="The calculator result is 42.",
        source="tool://calculator",
        index=0,
        char_start=0,
        char_end=28,
    )
    evidence = TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E1",
                chunk=tool_chunk,
                score=1.0,
                content=tool_chunk.text,
            ),
        )
    )
    case = benchmark_answers.AnswerCase(
        case_id="tool-citation",
        answer="The calculator result is 42 [E1].",
        evidence=evidence,
        expected_citations=("E1",),
        evidence_kinds=(("E1", "tool"),),
        allowed_citation_kinds=("source", "tool"),
    )

    result = benchmark_answers.evaluate_case(case)

    assert result.passed
    assert result.invalid_citation_kinds == ()


def test_answer_benchmark_rejects_contradicted_claims() -> None:
    case = benchmark_answers.AnswerCase(
        case_id="contradicted",
        answer="Dijkstra supports negative weights [E1].",
        evidence=_turn_evidence(),
        expected_citations=("E1",),
        contradicted_claims=(
            benchmark_answers.SupportedClaim(text="supports negative weights", evidence_id="E1"),
        ),
    )

    report = benchmark_answers.run_benchmark([case])

    assert report.pass_rate == 0.0
    assert report.contradiction_rate == 0.0
    assert report.results[0].contradicted_claims == ("supports negative weights [E1]",)


def test_answer_shape_constraints_catch_vague_or_narrow_answers() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="too-vague",
            answer="The material covers maths [E1].",
            evidence=_turn_evidence(),
            min_words=10,
            min_citation_count=2,
            min_distinct_sources=2,
        ),
        benchmark_answers.AnswerCase(
            case_id="shaped",
            answer=(
                "The retrieved sample includes graph algorithms [E1] and a separate "
                "calculus source [E2]."
            ),
            evidence=TurnEvidence(
                (
                    EvidenceChunk(
                        evidence_id="E1",
                        chunk=Chunk(
                            text="Dijkstra shortest paths use a priority queue.",
                            source="materials/graphs.md",
                            index=0,
                            char_start=0,
                            char_end=45,
                        ),
                        score=0.9,
                        content="Dijkstra shortest paths use a priority queue.",
                    ),
                    EvidenceChunk(
                        evidence_id="E2",
                        chunk=Chunk(
                            text="Integration by parts follows from the product rule.",
                            source="materials/calculus.md",
                            index=0,
                            char_start=0,
                            char_end=52,
                        ),
                        score=0.8,
                        content="Integration by parts follows from the product rule.",
                    ),
                )
            ),
            min_words=10,
            max_words=30,
            min_citation_count=2,
            min_distinct_sources=2,
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.pass_rate == 0.5
    assert report.answer_shape_rate == 0.5
    assert report.results[0].shape_failures == (
        "words 5 below 10",
        "citations 1 below 2",
        "distinct sources 1 below 2",
    )
    assert report.results[0].word_count == 5
    assert report.results[0].distinct_cited_sources == 1
    assert report.results[1].shape_failures == ()
    assert report.results[1].word_count == 13
    assert report.results[1].distinct_cited_sources == 2


def test_distinct_source_shape_counts_cited_sources_not_retrieved_sources() -> None:
    evidence = TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E1",
                chunk=Chunk(
                    text="The lecture defines a graph traversal invariant.",
                    source="materials/lecture.md",
                    index=0,
                    char_start=0,
                    char_end=47,
                ),
                score=0.9,
                content="The lecture defines a graph traversal invariant.",
            ),
            EvidenceChunk(
                evidence_id="E2",
                chunk=Chunk(
                    text="The exercise sheet asks users to apply the invariant.",
                    source="materials/exercise.md",
                    index=0,
                    char_start=0,
                    char_end=58,
                ),
                score=0.8,
                content="The exercise sheet asks users to apply the invariant.",
            ),
        )
    )
    case = benchmark_answers.AnswerCase(
        case_id="single-cited-source",
        answer=(
            "The material explains a graph traversal invariant and gives users "
            "practice applying it in exercises [E1]."
        ),
        evidence=evidence,
        min_words=10,
        min_citation_count=1,
        min_distinct_sources=2,
    )

    report = benchmark_answers.run_benchmark([case])

    assert report.answer_shape_rate == 0.0
    assert report.results[0].shape_failures == ("distinct sources 1 below 2",)


def test_answer_shape_constraints_can_require_bulleted_structure() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="paragraph",
            answer=(
                "The retrieved overview sample includes a lecture [E1] and an exam [E1]. "
                "It is not an exhaustive summary."
            ),
            evidence=_turn_evidence(),
            min_bullet_count=2,
        ),
        benchmark_answers.AnswerCase(
            case_id="bulleted",
            answer=(
                "Retrieved overview sample [E1]\n"
                "- Document signals: lecture [E1]\n"
                "- Scope: not an exhaustive summary [E1]"
            ),
            evidence=_turn_evidence(),
            min_bullet_count=2,
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.answer_shape_rate == 0.5
    assert report.results[0].shape_failures == ("bullets 0 below 2",)
    assert report.results[0].bullet_count == 0
    assert report.results[1].shape_failures == ()
    assert report.results[1].bullet_count == 2


def test_answer_shape_constraints_can_require_cited_bullets() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="uncited-bullets",
            answer=(
                "Retrieved overview sample [E1]\n"
                "- Document signals: lecture material\n"
                "- Scope: not an exhaustive summary"
            ),
            evidence=_turn_evidence(),
            min_bullet_count=2,
            min_cited_bullet_count=2,
        ),
        benchmark_answers.AnswerCase(
            case_id="cited-bullets",
            answer=(
                "Retrieved overview sample [E1]\n"
                "- Document signals: lecture material [E1]\n"
                "- Scope: not an exhaustive summary [E1]"
            ),
            evidence=_turn_evidence(),
            min_bullet_count=2,
            min_cited_bullet_count=2,
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.answer_shape_rate == 0.5
    assert report.results[0].shape_failures == ("cited bullets 0 below 2",)
    assert report.results[0].cited_bullet_count == 0
    assert report.results[1].shape_failures == ()
    assert report.results[1].cited_bullet_count == 2


def test_answer_shape_constraints_can_require_named_sections() -> None:
    case = benchmark_answers.AnswerCase(
        case_id="assessment-shape",
        answer=(
            "PARTIAL: Score: 1/2.\n"
            "Got: active recall uses memory.\n"
            "Missing: why unsupported recall matters."
        ),
        evidence=None,
        require_citations=False,
        required_sections=("Score", "Got", "Missing", "Misconception"),
    )

    result = benchmark_answers.evaluate_case(case)

    assert result.passed is False
    assert result.shape_failures == ("missing sections: Misconception",)


def test_material_overview_rejects_boilerplate_topic_phrases() -> None:
    case = benchmark_answers.AnswerCase(
        case_id="overview-boilerplate-topics",
        answer=(
            "Retrieved overview sample: two indexed sources were sampled [E1] [E2].\n"
            "- Document signals: the sample includes lecture and exam material [E1].\n"
            "- Visible topics: definition [E1], today speaking [E1], last time [E2].\n"
            "- Scope: this is not an exhaustive summary [E2].\n"
            "Next action: Review the smallest source-backed piece, then ask for recall."
        ),
        evidence=TurnEvidence(
            (
                EvidenceChunk(
                    evidence_id="E1",
                    chunk=Chunk(
                        text="Lecture material with useful calculus topics.",
                        source="materials/lecture.md",
                        index=0,
                        char_start=0,
                        char_end=44,
                    ),
                    score=0.9,
                    content="Lecture material with useful calculus topics.",
                ),
                EvidenceChunk(
                    evidence_id="E2",
                    chunk=Chunk(
                        text="Exam material with calculus tasks.",
                        source="materials/exam.md",
                        index=0,
                        char_start=0,
                        char_end=34,
                    ),
                    score=0.9,
                    content="Exam material with calculus tasks.",
                ),
            )
        ),
        expected_citations=("E1", "E2"),
        must_include=("Retrieved overview sample", "not an exhaustive summary"),
        must_not_include=(
            "Visible topics: definition",
            "next action",
            "source-backed",
        ),
        min_words=24,
        min_citation_count=2,
        min_distinct_sources=2,
        min_bullet_count=3,
        min_cited_bullet_count=3,
    )

    result = benchmark_answers.evaluate_case(case)

    assert not result.passed
    assert result.forbidden_text_present == (
        "Visible topics: definition",
        "next action",
        "source-backed",
    )


def test_material_overview_rejects_date_by_date_document_walkthrough() -> None:
    case = benchmark_answers.AnswerCase(
        case_id="overview-date-walkthrough",
        answer=(
            "Der Korpus behandelt Analysis und Modellierung [E1][E2].\n"
            "- In den Folien vom 22. April geht es um Reihen und Potenzreihen [E1].\n"
            "- In den Folien vom 15. April geht es um Folgen und Grenzwerte [E2].\n"
            "- In den Folien vom 4. Mai geht es um Taylor-Polynome [E1]."
        ),
        evidence=_turn_evidence(),
        expected_citations=("E1",),
        min_words=24,
        min_citation_count=2,
        min_bullet_count=3,
        min_cited_bullet_count=3,
        max_explicit_date_lines=1,
    )

    result = benchmark_answers.evaluate_case(case)

    assert not result.passed
    assert result.shape_failures == ("explicit date lines 2 above 1",)


def test_material_overview_rejects_chronological_walkthrough_without_dates() -> None:
    case = benchmark_answers.AnswerCase(
        case_id="overview-chronological-walkthrough",
        answer=(
            "The corpus is about applied mathematics and exam preparation [E1][E2].\n"
            "- First, the material introduces sequences and limits [E1].\n"
            "- Then, the material moves to series and convergence criteria [E2].\n"
            "- Later, it covers Taylor polynomials and approximation [E1]."
        ),
        evidence=_turn_evidence(),
        expected_citations=("E1",),
        task="material-overview",
        min_words=24,
        min_citation_count=2,
        min_bullet_count=3,
        min_cited_bullet_count=3,
        max_explicit_date_lines=1,
    )

    result = benchmark_answers.evaluate_case(case)

    assert not result.passed
    assert "chronological overview lines 3 above 1" in result.shape_failures


def test_explicit_date_counter_ignores_numbered_concepts() -> None:
    answer = (
        "- 1. Definitionen und Grundbegriffe bilden den Einstieg [E1].\n"
        "- Unit 2. Trade-offs bleiben trotzdem ein normales Thema [E2]."
    )

    assert benchmark_answers._explicit_date_line_count(answer) == 0


def test_evidence_coverage_constraints_can_require_sampled_sources() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="narrow",
            answer=(
                "Retrieved overview sample [E1]\n"
                "- Document signals: lecture material [E1]\n"
                "- Scope: not an exhaustive summary [E1]"
            ),
            evidence=_turn_evidence(),
            evidence_coverage={
                "evidence_blocks": 1,
                "sampled_sources": 1,
                "total_sources": 9,
            },
            min_sampled_sources=2,
        ),
        benchmark_answers.AnswerCase(
            case_id="broad",
            answer=(
                "Retrieved overview sample [E1]\n"
                "- Document signals: lecture material [E1]\n"
                "- Scope: not an exhaustive summary [E1]"
            ),
            evidence=_turn_evidence(),
            evidence_coverage={
                "evidence_blocks": 2,
                "sampled_sources": 2,
                "total_sources": 9,
            },
            min_sampled_sources=2,
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.pass_rate == 0.5
    assert report.evidence_coverage_rate == 0.5
    assert report.results[0].coverage_failures == ("sampled sources 1 below 2",)
    assert report.results[1].coverage_failures == ()


def test_supported_claim_must_appear_in_answer_and_cited_evidence() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="unsupported",
            answer="Dijkstra uses a Fibonacci heap [E1].",
            evidence=_turn_evidence(),
            expected_citations=("E1",),
            supported_claims=(
                benchmark_answers.SupportedClaim(text="Fibonacci heap", evidence_id="E1"),
            ),
        )
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.pass_rate == 0.0
    assert report.supported_claim_rate == 0.0
    assert report.results[0].unsupported_claims == ("Fibonacci heap [E1]",)


def test_required_abstention_must_say_sources_are_insufficient() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="hallucinated-no-evidence",
            answer="The answer is probably a geometric series.",
            evidence=None,
            require_citations=False,
            require_abstention=True,
            must_not_include=("probably",),
        ),
        benchmark_answers.AnswerCase(
            case_id="abstained",
            answer="The enabled sources do not contain that answer.",
            evidence=None,
            require_citations=False,
            require_abstention=True,
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.pass_rate == 0.5
    assert report.failures == ("hallucinated-no-evidence",)
    assert report.results[0].missing_abstention is True
    assert report.results[1].missing_abstention is False


def test_required_label_must_start_answer() -> None:
    cases = [
        benchmark_answers.AnswerCase(
            case_id="bad-label",
            answer="You are partly right: add the missing condition.",
            evidence=None,
            require_citations=False,
            required_label="PARTIAL",
        ),
        benchmark_answers.AnswerCase(
            case_id="good-label",
            answer="PARTIAL: Add the missing condition.",
            evidence=None,
            require_citations=False,
            required_label="PARTIAL",
        ),
    ]

    report = benchmark_answers.run_benchmark(cases)

    assert report.pass_rate == 0.5
    assert report.required_label_rate == 0.5
    assert report.failures == ("bad-label",)
    assert report.results[0].missing_required_label is True
    assert report.results[1].missing_required_label is False


def test_main_fails_below_threshold(tmp_path: Path, capsys) -> None:
    dataset = tmp_path / "answers.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "missing-citation",
                        "answer": "Dijkstra uses a priority queue.",
                        "evidence": _evidence(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_answers.main([str(dataset), "--min-pass-rate", "1.0"])

    captured = capsys.readouterr()
    assert status == 1
    assert "pass_rate=0.0%" in captured.out
    assert "failures=missing-citation" in captured.out
    assert "missing-citation: missing citations" in captured.out


def test_main_gates_expected_required_and_forbidden_rates(
    tmp_path: Path,
    capsys,
) -> None:
    dataset = tmp_path / "answers.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "bad-shape",
                        "answer": "Dijkstra supports negative weights [E1].",
                        "evidence": _evidence(),
                        "expected_citations": ["E2"],
                        "must_include": ["priority queue"],
                        "must_not_include": ["negative weights"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_answers.main(
        [
            str(dataset),
            "--min-expected-citations",
            "1.0",
            "--min-required-text",
            "1.0",
            "--min-forbidden-text",
            "1.0",
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "expected_citations=0.0%" in captured.out
    assert "required_text=0.0%" in captured.out
    assert "forbidden_text=0.0%" in captured.out
    assert (
        "bad-shape: missing expected citations: E2; missing required text: priority queue; "
        "forbidden text: negative weights" in captured.out
    )


def test_main_gates_citation_source_rate(tmp_path: Path, capsys) -> None:
    dataset = tmp_path / "answers.json"
    memory_evidence = _evidence()
    memory_evidence[0]["source"] = "memory://study-state"
    memory_evidence[0]["kind"] = "memory"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "memory-cited",
                        "answer": "Dijkstra shortest paths use a priority queue [E1].",
                        "evidence": memory_evidence,
                        "expected_citations": ["E1"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_answers.main([str(dataset), "--min-citation-sources", "1.0"])

    captured = capsys.readouterr()
    assert status == 1
    assert "citation_sources=0.0%" in captured.out
    assert "memory-cited: invalid citation kinds: E1:memory" in captured.out


def test_main_gates_contradiction_rate(tmp_path: Path, capsys) -> None:
    dataset = tmp_path / "answers.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "contradicted",
                        "answer": "Dijkstra supports negative weights [E1].",
                        "evidence": _evidence(),
                        "expected_citations": ["E1"],
                        "contradicted_claims": [
                            {"text": "supports negative weights", "evidence_id": "E1"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_answers.main([str(dataset), "--min-contradiction-rate", "1.0"])

    captured = capsys.readouterr()
    assert status == 1
    assert "contradictions=0.0%" in captured.out
    assert "contradicted: contradicted claims: supports negative weights [E1]" in captured.out


def test_main_gates_required_label_rate(tmp_path: Path, capsys) -> None:
    dataset = tmp_path / "answers.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "bad-label",
                        "answer": "Almost right, but incomplete.",
                        "require_citations": False,
                        "required_label": "PARTIAL",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_answers.main([str(dataset), "--min-required-label", "1.0"])

    captured = capsys.readouterr()
    assert status == 1
    assert "required_label=0.0%" in captured.out


def test_main_gates_answer_shape_rate(tmp_path: Path, capsys) -> None:
    dataset = tmp_path / "answers.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "vague",
                        "answer": "The material covers maths [E1].",
                        "evidence": _evidence(),
                        "min_words": 10,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    status = benchmark_answers.main([str(dataset), "--min-answer-shape", "1.0"])

    captured = capsys.readouterr()
    assert status == 1
    assert "answer_shape=0.0%" in captured.out
    assert "vague: answer shape: words 5 below 10" in captured.out
