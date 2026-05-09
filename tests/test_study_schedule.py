from __future__ import annotations

from datetime import UTC, datetime

from hephaistos.study.schedule import load_study_schedule
from hephaistos.study.state import StudyRecallRating


def test_study_schedule_records_fast_easy_review(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = load_study_schedule(tmp_path)
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)

    state = store.record_review(
        "What is Dijkstra's algorithm?",
        retrieval_query="dijkstra",
        source_refs=["materials/exam.md#chunk=0"],
        rating=StudyRecallRating.EASY,
        elapsed_seconds=18,
        now=now,
    )

    assert state.reviews == 1
    assert state.difficulty < 5.0
    assert state.stability > 1.0
    assert state.last_recall_seconds == 18
    assert state.next_review is not None
    assert state.next_review > now
    assert state.retrievability(now=now) == 1.0


def test_study_schedule_persists_reviews(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = load_study_schedule(tmp_path)
    store.record_review(
        "Explain recurrence relations",
        retrieval_query="recurrence",
        source_refs=["materials/exam.md#chunk=1"],
        rating=StudyRecallRating.HARD,
        elapsed_seconds=180,
        now=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
    )
    store.save()

    loaded = load_study_schedule(tmp_path)

    assert len(loaded.item_list) == 1
    item = loaded.item_list[0]
    assert item.item == "Explain recurrence relations"
    assert item.last_rating is StudyRecallRating.HARD
    assert item.last_recall_seconds == 180


def test_slow_recall_reduces_next_stability_more_than_fast_recall(tmp_path) -> None:  # type: ignore[no-untyped-def]
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    fast_store = load_study_schedule(tmp_path / "fast")
    slow_store = load_study_schedule(tmp_path / "slow")

    fast = fast_store.record_review(
        "Explain convexity",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=StudyRecallRating.GOOD,
        elapsed_seconds=20,
        now=now,
    )
    slow = slow_store.record_review(
        "Explain convexity",
        retrieval_query="convexity",
        source_refs=["materials/lecture.md#chunk=0"],
        rating=StudyRecallRating.GOOD,
        elapsed_seconds=180,
        now=now,
    )

    assert fast.stability > slow.stability
    assert fast.difficulty < slow.difficulty
    assert fast.next_review is not None
    assert slow.next_review is not None
    assert fast.next_review > slow.next_review


def test_retrievability_decays_toward_target_by_next_review(tmp_path) -> None:  # type: ignore[no-untyped-def]
    now = datetime(2026, 5, 9, 12, 0, tzinfo=UTC)
    store = load_study_schedule(tmp_path)

    state = store.record_review(
        "Explain amortized analysis",
        retrieval_query="amortized analysis",
        source_refs=["materials/exam.md#chunk=2"],
        rating=StudyRecallRating.EASY,
        elapsed_seconds=15,
        now=now,
    )

    assert state.next_review is not None
    assert 0.86 <= state.retrievability(now=state.next_review) <= 0.94
