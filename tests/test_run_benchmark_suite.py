from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts import run_benchmark_suite


def test_default_suite_passes_and_does_not_write_index_to_fixture() -> None:
    status = run_benchmark_suite.run_suite()

    assert status == 0
    assert not (
        run_benchmark_suite.DEFAULT_SUITE / "armory" / ".hephaistos" / "rag_index.json"
    ).exists()


def test_suite_fails_when_threshold_is_too_high() -> None:
    status = run_benchmark_suite.run_suite(rag_mrr=1.01)

    assert status == 1


def test_suite_writes_machine_readable_report(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "suite.json"

    status = run_benchmark_suite.run_suite(report_path=report_path)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 0
    assert report["status"] == 0
    assert report["suite"] == str(run_benchmark_suite.DEFAULT_SUITE)
    assert report["thresholds"]["rag_hit_rate"] == 1.0
    assert report["thresholds"]["rag_forbidden_before_expected_avoidance"] == 1.0
    assert report["thresholds"]["answer_shape"] == 1.0
    assert report["thresholds"]["evidence_coverage"] == 1.0
    assert report["thresholds"]["required_label"] == 1.0
    assert report["thresholds"]["document_understanding_min_documents"] == 10
    assert report["thresholds"]["document_understanding_required_roles"] == [
        "assignment",
        "lecture",
        "past_exam",
    ]
    assert report["thresholds"]["document_understanding_overview_coverage"] == 1.0
    assert report["thresholds"]["index_integrity_pass_rate"] == 1.0
    assert report["thresholds"]["index_integrity_required_text"] == 1.0
    assert report["thresholds"]["index_integrity_forbidden_text"] == 1.0
    assert report["thresholds"]["index_integrity_corpus_forbidden_text"] == 1.0
    assert report["thresholds"]["study_state_pass_rate"] == 1.0
    assert report["rag"]["hit_rate"] == 1.0
    assert report["rag"]["forbidden_before_expected_avoidance"] == 1.0
    assert report["material_roles"]["pass_rate"] == 1.0
    assert report["document_understanding"]["indexed_documents"] == 14
    assert report["document_understanding"]["extraction_health_passed"] is True
    assert report["document_understanding"]["role_counts"]["assignment"] == 1
    assert report["document_understanding"]["overview_source_coverage_rate"] == 1.0
    assert report["index_integrity"]["pass_rate"] == 1.0
    assert report["index_integrity"]["required_text_rate"] == 1.0
    assert report["index_integrity"]["forbidden_text_rate"] == 1.0
    assert report["index_integrity"]["corpus_forbidden_text_rate"] == 1.0
    assert report["priority"]["pass_rate"] == 1.0
    assert report["prompt_cache"]["pass_rate"] == 1.0
    assert report["prompt_cache"]["stable_hash_reuse_rate"] == 1.0
    assert report["prompt_cache"]["dynamic_tail_preservation_rate"] == 1.0
    assert report["replay"]["cases"] == 7
    assert report["chat_events"]["has_reading"] is True
    assert report["chat_events"]["has_evidence"] is True
    assert report["chat_events"]["has_writing"] is True
    assert report["chat_events"]["has_material_operation"] is True
    assert report["chat_events"]["material_operation_metadata_rate"] == 1.0
    assert report["chat_events"]["has_turn_complete"] is True
    assert report["chat_events"]["has_consistent_completion"] is True
    assert report["chat_events"]["has_evidence_metadata"] is True
    assert report["chat_events"]["evidence_metadata_rate"] == 1.0
    assert report["chat_events"]["tool_runtime_metadata_rate"] == 1.0
    assert report["chat_events"]["answer_pass_rate"] == 1.0
    assert report["chat_runtime_events"]["has_tool_runtime"] is True
    assert report["chat_runtime_events"]["has_material_operation"] is True
    assert report["chat_runtime_events"]["material_operation_metadata_rate"] == 1.0
    assert report["chat_runtime_events"]["tool_runtime_metadata_rate"] == 1.0
    assert report["chat_runtime_events"]["has_acceptance_criteria"] is True
    assert report["chat_runtime_events"]["acceptance_criteria_metadata_rate"] == 1.0
    assert report["chat_runtime_events"]["answer_pass_rate"] == 1.0
    assert report["answers"]["pass_rate"] == 1.0
    assert report["answers"]["answer_shape_rate"] == 1.0
    assert report["answers"]["evidence_coverage_rate"] == 1.0
    assert report["study_state"]["pass_rate"] == 1.0
    assert report["study_state"]["scheduling_pass_rate"] == 1.0
    assert report["study_state"]["mastery_metadata_rate"] == 1.0
    assert report["academic_items"]["pass_rate"] == 1.0
    assert report["academic_items"]["question_type_count"] >= 3
    assert report["academic_items"]["grounded_question_rate"] == 1.0
    assert report["report_path"] == str(report_path)


def test_suite_can_compare_current_report_to_baseline(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    assert run_benchmark_suite.run_suite(report_path=baseline_path) == 0

    status = run_benchmark_suite.run_suite(
        report_path=current_path,
        compare_to=baseline_path,
    )

    assert status == 0


def test_suite_rejects_compare_without_current_report(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text('{"rag":{"hit_rate":1.0}}\n', encoding="utf-8")

    status = run_benchmark_suite.main(["--compare-to", str(baseline_path)])

    assert status == 2


def test_suite_gates_rag_expected_recall() -> None:
    assert run_benchmark_suite.run_suite(rag_expected_recall=1.01) == 1


def test_suite_gates_rag_forbidden_before_expected_avoidance() -> None:
    assert run_benchmark_suite.run_suite(rag_forbidden_before_expected_avoidance=1.01) == 1


def test_suite_gates_answer_shape_thresholds() -> None:
    assert run_benchmark_suite.run_suite(expected_citations=1.01) == 1
    assert run_benchmark_suite.run_suite(required_text=1.01) == 1
    assert run_benchmark_suite.run_suite(forbidden_text=1.01) == 1
    assert run_benchmark_suite.run_suite(required_label=1.01) == 1
    assert run_benchmark_suite.run_suite(answer_shape=1.01) == 1
    assert run_benchmark_suite.run_suite(evidence_coverage=1.01) == 1
    assert run_benchmark_suite.run_suite(index_integrity_pass_rate=1.01) == 1
    assert run_benchmark_suite.run_suite(index_integrity_required_text=1.01) == 1
    assert run_benchmark_suite.run_suite(index_integrity_forbidden_text=1.01) == 1
    assert run_benchmark_suite.run_suite(index_integrity_corpus_forbidden_text=1.01) == 1
    assert run_benchmark_suite.run_suite(study_state_pass_rate=1.01) == 1
    assert run_benchmark_suite.run_suite(study_state_scheduling_pass_rate=1.01) == 1
    assert run_benchmark_suite.run_suite(document_understanding_overview_coverage=1.01) == 1


def test_missing_suite_returns_error(tmp_path: Path, capsys) -> None:
    status = run_benchmark_suite.main(["--suite", str(tmp_path / "missing")])

    captured = capsys.readouterr()
    assert status == 2
    assert "benchmark suite error:" in captured.err


def test_suite_rejects_empty_replay_dataset(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "replay.jsonl").write_text("# empty replay dataset\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "replay dataset does not contain any cases" in captured.err


def test_suite_rejects_missing_chat_event_dataset(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "chat_events.jsonl").unlink()

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "benchmark suite is missing chat event dataset" in captured.err


def test_suite_rejects_chat_event_stream_without_evidence_notice(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    lines = [
        line
        for line in (suite / "chat_events.jsonl").read_text(encoding="utf-8").splitlines()
        if '"code":"evidence"' not in line
    ]
    (suite / "chat_events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 1
    assert "missing evidence notice" in captured.out


def test_suite_rejects_narrow_replay_tasks(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "replay.jsonl").write_text(
        "\n".join(
            (
                (
                    '{"id":"one","domain":"computer-science","task":"grounded-explanation",'
                    '"prompt":"Explain Dijkstra.","must_include":["priority queue"]}'
                ),
                (
                    '{"id":"two","domain":"mathematics","task":"grounded-explanation",'
                    '"prompt":"Explain integration by parts.","must_include":["product rule"]}'
                ),
            )
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "replay benchmark must cover at least" in captured.err


def test_suite_rejects_replay_without_shaped_material_overview(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    lines = [
        line
        for line in (suite / "replay.jsonl").read_text(encoding="utf-8").splitlines()
        if "material-overview-replay" not in line
    ]
    (suite / "replay.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "replay benchmark must include a material-overview case" in captured.err


def test_suite_rejects_replay_material_overview_without_shape_contract(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    lines = []
    for line in (suite / "replay.jsonl").read_text(encoding="utf-8").splitlines():
        if "material-overview-replay" in line:
            payload = json.loads(line)
            for field in (
                "min_words",
                "max_words",
                "min_citation_count",
                "min_distinct_sources",
                "min_bullet_count",
                "min_cited_bullet_count",
            ):
                payload.pop(field, None)
            lines.append(json.dumps(payload))
            continue
        lines.append(line)
    (suite / "replay.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "replay material-overview case must include" in captured.err


def test_suite_rejects_narrow_answer_tasks(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "answers.jsonl").write_text(
        "\n".join(
            (
                (
                    '{"id":"one","domain":"computer-science","task":"grounded-explanation",'
                    '"answer":"Dijkstra uses a priority queue [E1].",'
                    '"evidence":[{"id":"E1","source":"materials/algorithms.md",'
                    '"chunk":0,"text":"Dijkstra uses a priority queue."}]}'
                ),
                (
                    '{"id":"two","domain":"computer-science","task":"grounded-explanation",'
                    '"answer":"Integration by parts follows from product rule [E1].",'
                    '"evidence":[{"id":"E1","source":"materials/calculus.md",'
                    '"chunk":0,"text":"Integration by parts follows from product rule."}]}'
                ),
            )
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "answer benchmark must cover at least" in captured.err


def test_suite_rejects_narrow_material_role_domains(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "material_roles.jsonl").write_text(
        "\n".join(
            (
                (
                    '{"id":"lecture","domain":"mathematics",'
                    '"source":"materials/mfi-lecture.md","expected_role":"lecture"}'
                ),
                (
                    '{"id":"exam","domain":"mathematics",'
                    '"source":"materials/mfi-past-exam.md","expected_role":"past_exam"}'
                ),
            )
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "material role benchmark must cover at least" in captured.err


def test_suite_rejects_narrow_rag_tasks(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "rag.jsonl").write_text(
        "\n".join(
            (
                (
                    '{"id":"one","domain":"mathematics","task":"single-source-fact",'
                    '"query":"Integration by parts follows from which derivative rule?",'
                    '"expected":["materials/calculus.md"]}'
                ),
                (
                    '{"id":"two","domain":"mathematics","task":"single-source-fact",'
                    '"query":"What data structure does Dijkstra use?",'
                    '"expected":["materials/algorithms.md"]}'
                ),
            )
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "RAG benchmark must cover at least" in captured.err


def test_suite_rejects_rag_without_multi_source_case(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    cases = [
        line
        for line in (suite / "rag.jsonl").read_text(encoding="utf-8").splitlines()
        if "multi-source-synthesis" not in line
    ]
    (suite / "rag.jsonl").write_text("\n".join(cases) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "multi-source synthesis" in captured.err


def test_suite_rejects_answers_without_multi_evidence_case(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    cases = [
        line
        for line in (suite / "answers.jsonl").read_text(encoding="utf-8").splitlines()
        if "multi-source-synthesis" not in line
    ]
    (suite / "answers.jsonl").write_text("\n".join(cases) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "multi-evidence synthesis" in captured.err


def test_suite_rejects_answers_without_active_recall_case(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    cases = [
        line
        for line in (suite / "answers.jsonl").read_text(encoding="utf-8").splitlines()
        if "active-recall" not in line
    ]
    (suite / "answers.jsonl").write_text("\n".join(cases) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "active-recall assessment" in captured.err


def test_suite_rejects_answers_without_hint_case(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    cases = [
        line
        for line in (suite / "answers.jsonl").read_text(encoding="utf-8").splitlines()
        if '"task": "hint"' not in line
    ]
    (suite / "answers.jsonl").write_text("\n".join(cases) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "hint case" in captured.err


def test_suite_rejects_overview_answers_without_boilerplate_forbidden_terms(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    lines = []
    for line in (suite / "answers.jsonl").read_text(encoding="utf-8").splitlines():
        if "material-overview-grounded-sample" in line:
            payload = json.loads(line)
            payload["must_not_include"] = [
                phrase for phrase in payload["must_not_include"] if phrase != "Document signals"
            ]
            lines.append(json.dumps(payload))
            continue
        lines.append(line)
    (suite / "answers.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "answer material-overview case must forbid" in captured.err
    assert "Document signals" in captured.err


def test_suite_rejects_chat_expectation_without_boilerplate_forbidden_terms(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    payload = json.loads((suite / "chat_event_expectation.json").read_text(encoding="utf-8"))
    payload[0]["must_not_include"] = [
        phrase for phrase in payload[0]["must_not_include"] if phrase != "heute sprechen"
    ]
    (suite / "chat_event_expectation.json").write_text(
        json.dumps(payload) + "\n",
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "chat-event expectation material-overview case must forbid" in captured.err
    assert "heute sprechen" in captured.err


def test_suite_rejects_narrow_priority_domains(tmp_path: Path, capsys) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "priority.jsonl").write_text(
        (
            '{"id":"mfi","domain":"mathematics","limit":30,'
            '"expected_topics":["geometrische reihe"],'
            '"expected_past_exam_sources":["materials/mfi-past-exam.md"]}\n'
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "priority benchmark must cover at least" in captured.err


def test_suite_rejects_narrow_index_integrity_tasks(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "index_integrity.jsonl").write_text(
        (
            '{"id":"unicode","domain":"mathematics","task":"unicode-extraction",'
            '"source":"materials/mfi-lecture.md",'
            '"must_include":["Universität Würzburg"]}\n'
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "index integrity benchmark must cover at least" in captured.err


def test_suite_rejects_narrow_index_integrity_domains(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "index_integrity.jsonl").write_text(
        "\n".join(
            (
                (
                    '{"id":"unicode","domain":"mathematics","task":"unicode-extraction",'
                    '"source":"materials/mfi-lecture.md",'
                    '"must_include":["Universität Würzburg"]}'
                ),
                (
                    '{"id":"formula","domain":"mathematics","task":"formula-language-extraction",'
                    '"source":"materials/calculus.md",'
                    '"must_include":["Integration by parts"]}'
                ),
                (
                    '{"id":"exam","domain":"mathematics","task":"exam-format-extraction",'
                    '"source":"materials/mfi-past-exam.md",'
                    '"must_include":["Aufgabe 1 [8 Punkte]"]}'
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "index integrity benchmark must cover at least" in captured.err
    assert "labelled domains" in captured.err


def test_suite_rejects_narrow_study_state_domains(
    tmp_path: Path,
    capsys,
) -> None:
    suite = tmp_path / "suite"
    shutil.copytree(run_benchmark_suite.DEFAULT_SUITE, suite)
    (suite / "study_state.jsonl").write_text(
        (
            '{"id":"one-domain","domain":"mathematics","expected_final_phase":"presenting",'
            '"expected_scheduled_reviews":1,"turns":['
            '{"user":"Explain integration by parts","reply":"Use product rule.",'
            '"source_refs":["materials/calculus.md#chunk=0"]},'
            '{"user":"ready","reply":"State it from memory."},'
            '{"user":"attempt","reply":"CORRECT: Correct.",'
            '"source_refs":["materials/calculus.md#chunk=0"],'
            '"advance_seconds":18,"record_schedule":true}'
            "]}\n"
        ),
        encoding="utf-8",
    )

    status = run_benchmark_suite.main(["--suite", str(suite)])

    captured = capsys.readouterr()
    assert status == 2
    assert "study-state benchmark must cover at least" in captured.err
