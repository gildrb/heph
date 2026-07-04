from __future__ import annotations

from datetime import UTC, datetime, timedelta

from harness.documents.schedule import load_recall_schedule
from harness.documents.state import RecallRating


def test_recall_schedule_records_fast_easy_review(tmp_path) -> None:
    store = load_recall_schedule(tmp_path)
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)

    state = store.record_review(
        "What is Dijkstra's algorithm?",
        concept="Dijkstra",
        retrieval_query="dijkstra",
        source_refs=["materials/exam.md#chunk=0"],
        rating=RecallRating.EASY,
        elapsed_seconds=18,
        confidence=0.8,
        error_type="correct",
        exam_importance=0.8,
        now=now,
    )

    assert state.reviews == 1
    assert state.failures == 0
    assert state.concept == "Dijkstra"
    assert state.error_type == "correct"
    assert state.last_correct is True
    assert state.last_retrieval_success is True
    assert state.last_transfer_success is False
    assert state.exam_importance == 0.8
    assert state.difficulty < 5.0
    assert state.stability > 1.0
    assert state.last_recall_seconds == 18
    assert state.last_confidence == 0.8
    assert state.next_review is not None
    assert state.next_review > now
    assert state.retrievability(now=now) == 1.0
    assert state.mastery == 1.0
    assert state.calibration_gap == 0.2
    assert state.next_best_action == "move_to_harder_question"


def test_recall_schedule_persists_reviews(tmp_path) -> None:
    store = load_recall_schedule(tmp_path)
    store.record_review(
        "Explain recurrence relations",
        concept="Recurrence relations",
        retrieval_query="recurrence",
        source_refs=["materials/exam.md#chunk=1"],
        rating=RecallRating.HARD,
        elapsed_seconds=180,
        confidence=0.9,
        hint_level_needed=3,
        error_type="wrong",
        intervention="give_hint",
        exam_importance=2.0,
        now=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
    )
    store.record_policy_outcome(
        "give_hint",
        success=False,
        mastery_delta=-0.1,
        confidence_delta=0.0,
        time_cost_seconds=180,
        frustration_signal=True,
    )
    store.save()

    loaded = load_recall_schedule(tmp_path)

    assert (tmp_path / ".harness" / "recall_schedule.json").is_file()
    assert len(loaded.item_list) == 1
    item = loaded.item_list[0]
    assert item.item == "Explain recurrence relations"
    assert item.concept == "Recurrence relations"
    assert item.error_type == "wrong"
    assert item.exam_importance == 1.0
    assert item.last_rating is RecallRating.HARD
    assert item.last_correct is False
    assert item.last_retrieval_success is True
    assert item.last_transfer_success is False
    assert item.failures == 1
    assert item.last_recall_seconds == 180
    assert item.last_confidence == 0.9
    assert item.hint_level_needed == 3
    assert item.solved_after_hint is False
    assert item.common_errors == ["wrong"]
    assert item.failed_interventions == ["give_hint"]
    assert item.mastery < 0.1
    assert item.next_best_action == "contrastive_question"
    assert loaded.policy_stats["give_hint"].uses == 1
    assert loaded.policy_stats["give_hint"].frustration_count == 1


def test_recall_schedule_loads_legacy_reviews_without_mastery_fields(tmp_path) -> None:
    schedule_path = tmp_path / ".harness" / "study_schedule.json"
    schedule_path.parent.mkdir()
    schedule_path.write_text(
        (
            "{\n"
            '  "version": 1,\n'
            '  "items": {\n'
            '    "legacy:materials/a.md#chunk=0": {\n'
            '      "item": "legacy",\n'
            '      "retrieval_query": "legacy",\n'
            '      "source_refs": ["materials/a.md#chunk=0"],\n'
            '      "reviews": 1,\n'
            '      "difficulty": 5.0,\n'
            '      "stability": 1.0,\n'
            '      "last_rating": "hard"\n'
            "    }\n"
            "  }\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    store = load_recall_schedule(tmp_path)

    assert len(store.item_list) == 1
    item = store.item_list[0]
    assert item.concept == ""
    assert item.error_type == ""
    assert item.exam_importance == 0.0
    assert item.failures == 0
    assert item.last_correct is False
    assert item.last_retrieval_success is True
    assert item.last_transfer_success is False
    assert item.mastery == 0.0
    assert item.common_errors == []
    assert item.successful_interventions == []
    assert item.failed_interventions == []


def test_recall_schedule_tracks_transfer_success_for_application_items(tmp_path) -> None:
    store = load_recall_schedule(tmp_path)

    state = store.record_review(
        "Apply convexity to a new scenario",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=RecallRating.GOOD,
        elapsed_seconds=45,
    )

    assert state.last_correct is True
    assert state.last_retrieval_success is True
    assert state.last_transfer_success is True


def test_recall_schedule_accumulates_failures_for_weak_concepts(tmp_path) -> None:
    store = load_recall_schedule(tmp_path)
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)

    first = store.record_review(
        "Explain convexity",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=RecallRating.HARD,
        elapsed_seconds=120,
        now=now,
    )
    second = store.record_review(
        "Explain convexity",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=RecallRating.GOOD,
        elapsed_seconds=45,
        now=now + timedelta(days=1),
    )

    assert first is second
    assert second.reviews == 2
    assert second.failures == 1
    assert second.last_correct is True


def test_slow_recall_reduces_next_stability_more_than_fast_recall(tmp_path) -> None:
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    fast_store = load_recall_schedule(tmp_path / "fast")
    slow_store = load_recall_schedule(tmp_path / "slow")

    fast = fast_store.record_review(
        "Explain convexity",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=RecallRating.GOOD,
        elapsed_seconds=20,
        now=now,
    )
    slow = slow_store.record_review(
        "Explain convexity",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=RecallRating.GOOD,
        elapsed_seconds=180,
        now=now,
    )

    assert fast.stability > slow.stability
    assert fast.difficulty < slow.difficulty
    assert fast.next_review is not None
    assert slow.next_review is not None
    assert fast.next_review > slow.next_review


def test_retrievability_decays_toward_target_by_next_review(tmp_path) -> None:
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    store = load_recall_schedule(tmp_path)

    state = store.record_review(
        "Explain amortized analysis",
        retrieval_query="amortized analysis",
        source_refs=["materials/exam.md#chunk=2"],
        rating=RecallRating.EASY,
        elapsed_seconds=15,
        now=now,
    )

    assert state.next_review is not None
    assert 0.86 <= state.retrievability(now=state.next_review) <= 0.94


def test_due_items_prioritize_exam_importance_before_difficulty(tmp_path) -> None:
    store = load_recall_schedule(tmp_path)
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)

    low_importance = store.record_review(
        "Low importance but hard",
        concept="Low",
        retrieval_query="low",
        source_refs=["materials/notes.md#chunk=0"],
        rating=RecallRating.HARD,
        elapsed_seconds=180,
        exam_importance=0.1,
        now=now,
    )
    high_importance = store.record_review(
        "High importance",
        concept="High",
        retrieval_query="high",
        source_refs=["materials/exam.md#chunk=0"],
        rating=RecallRating.HARD,
        elapsed_seconds=20,
        exam_importance=0.9,
        now=now,
    )
    assert low_importance.next_review is not None
    assert high_importance.next_review is not None
    high_importance.next_review = low_importance.next_review
    low_importance.difficulty = 10.0
    high_importance.difficulty = 1.0

    due = store.due_items(now=now + timedelta(days=1))

    assert [item.concept for item in due] == ["High", "Low"]


def test_due_items_prioritize_repeated_failures_before_difficulty(tmp_path) -> None:
    store = load_recall_schedule(tmp_path)
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)

    difficult_once = store.record_review(
        "Difficult once",
        concept="Difficult once",
        retrieval_query="difficult",
        source_refs=["materials/notes.md#chunk=0"],
        rating=RecallRating.HARD,
        elapsed_seconds=180,
        exam_importance=0.5,
        now=now,
    )
    repeated_failure = store.record_review(
        "Repeated failure",
        concept="Repeated failure",
        retrieval_query="repeated",
        source_refs=["materials/notes.md#chunk=1"],
        rating=RecallRating.HARD,
        elapsed_seconds=90,
        exam_importance=0.5,
        now=now,
    )
    repeated_failure.failures = 3
    repeated_failure.next_review = difficult_once.next_review
    difficult_once.difficulty = 10.0
    repeated_failure.difficulty = 1.0

    due = store.due_items(now=now + timedelta(days=1))

    assert [item.concept for item in due] == ["Repeated failure", "Difficult once"]
