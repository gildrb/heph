from __future__ import annotations

from pathlib import Path

from scripts import benchmark_study_state


def test_load_study_state_cases(tmp_path: Path) -> None:
    dataset = tmp_path / "study_state.jsonl"
    dataset.write_text(
        (
            '{"id":"case-1","domain":"mathematics","expected_final_phase":"presenting",'
            '"expected_scheduled_reviews":1,"turns":['
            '{"user":"Explain integration by parts","reply":"Use product rule.",'
            '"source_refs":["materials/calculus.md#chunk=0"],"expected_action":"present",'
            '"prompt_must_include":["Execute the PRESENT phase"],'
            '"prompt_must_not_include":["Execute ASSESS"]}'
            "]}\n"
        ),
        encoding="utf-8",
    )

    cases = benchmark_study_state.load_cases(dataset)

    assert len(cases) == 1
    assert cases[0].case_id == "case-1"
    assert cases[0].turns[0].source_refs == ("materials/calculus.md#chunk=0",)
    assert cases[0].turns[0].prompt_must_include == ("Execute the PRESENT phase",)
    assert cases[0].turns[0].prompt_must_not_include == ("Execute ASSESS",)


def test_study_state_benchmark_scores_transitions_and_schedule(tmp_path: Path) -> None:
    cases = [
        benchmark_study_state.StudyStateCase(
            case_id="fast-correct",
            domain="mathematics",
            expected_final_phase="presenting",
            expected_scheduled_reviews=1,
            expected_due_reviews=0,
            expected_scheduled_concepts=("Explain integration by parts",),
            expected_schedule_error_types=("correct",),
            expected_schedule_failures=(0,),
            turns=(
                benchmark_study_state.StudyTurnCase(
                    user="Explain integration by parts",
                    reply="Use the product-rule rearrangement.",
                    source_refs=("materials/calculus.md#chunk=0",),
                    expected_action="present",
                    expected_phase="waiting_for_ready",
                    expected_feedback="presented",
                    prompt_must_include=("same language as the student's request",),
                ),
                benchmark_study_state.StudyTurnCase(
                    user="ready",
                    reply="State it from memory.",
                    expected_action="prompt_recall",
                    expected_phase="recall",
                    expected_feedback="ready",
                    prompt_must_include=("same language as the current item",),
                    prompt_must_not_include=("End with exactly: Answer from memory",),
                ),
                benchmark_study_state.StudyTurnCase(
                    user="Integral of u dv equals uv minus integral v du. confidence 4/5",
                    reply="CORRECT: Correct.",
                    source_refs=("materials/calculus.md#chunk=0",),
                    advance_seconds=18,
                    expected_action="assess",
                    expected_phase="presenting",
                    expected_feedback="correct",
                    expected_rating="easy",
                    expected_confidence=0.8,
                    record_schedule=True,
                ),
            ),
        )
    ]

    report = benchmark_study_state.run_benchmark(cases, armory_path=tmp_path)

    assert report.pass_rate == 1.0
    assert report.transition_pass_rate == 1.0
    assert report.scheduling_pass_rate == 1.0
    assert report.mastery_metadata_rate == 1.0
    assert report.prompt_contract_rate == 1.0
    assert report.results[0].scheduled_reviews == 1
    assert report.results[0].turns[0].prompt_contract_checked is True
    assert report.results[0].turns[0].prompt_contract_passed is True
    assert report.results[0].turns[2].confidence == 0.8
    assert report.results[0].scheduled_concepts == ("Explain integration by parts",)
    assert report.results[0].schedule_error_types == ("correct",)
    assert report.results[0].schedule_failures == (0,)
    assert report.results[0].schedule_confidences == (0.8,)
    assert report.results[0].schedule_retrieval_successes == (True,)
    assert report.results[0].schedule_transfer_successes == (False,)


def test_study_state_benchmark_reports_failures(tmp_path: Path) -> None:
    case = benchmark_study_state.StudyStateCase(
        case_id="wrong-expectation",
        turns=(
            benchmark_study_state.StudyTurnCase(
                user="hey",
                reply="Hey.",
                expected_action="present",
            ),
        ),
    )

    report = benchmark_study_state.run_benchmark([case], armory_path=tmp_path)

    assert report.pass_rate == 0.0
    assert "action expected 'present', got 'chat'" in report.failures[0]


def test_study_state_benchmark_reports_prompt_contract_failures(tmp_path: Path) -> None:
    case = benchmark_study_state.StudyStateCase(
        case_id="prompt-contract",
        turns=(
            benchmark_study_state.StudyTurnCase(
                user="Explain Bayes theorem",
                reply="Bayes theorem relates conditional probabilities.",
                expected_action="present",
                prompt_must_include=("missing phrase",),
                prompt_must_not_include=("Execute the PRESENT phase",),
            ),
        ),
    )

    report = benchmark_study_state.run_benchmark([case], armory_path=tmp_path)

    assert report.pass_rate == 0.0
    assert report.prompt_contract_rate == 0.0
    assert report.results[0].turns[0].prompt_contract_checked is True
    assert report.results[0].turns[0].prompt_contract_passed is False
    assert "prompt missing required phrase 'missing phrase'" in report.failures[0]
    assert "prompt includes forbidden phrase 'Execute the PRESENT phase'" in report.failures[1]
