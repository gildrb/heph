from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hephaion.study.artifacts import (
    LearningArtifact,
    LearningArtifactDifficulty,
    LearningArtifactKind,
    LearningArtifactReviewState,
    LearningArtifactSourceSpan,
    learning_artifacts_to_anki_tsv,
    next_learning_artifact_review_state,
    record_learning_artifact_review,
    validate_learning_artifact,
    validate_learning_artifacts,
)
from hephaion.study.state import RecallRating

SOURCE_REF = "materials/lecture.md#chunk=2"
SOURCE_TEXT = (
    "Long-term potentiation is persistent strengthening of synapses after "
    "high-frequency stimulation. NMDA receptor coincidence detection triggers "
    "calcium influx. Common misconception: LTP is only a structural change. "
    "Prerequisite: synaptic transmission."
)
SOURCE_MAP = {SOURCE_REF: SOURCE_TEXT}


def _span() -> LearningArtifactSourceSpan:
    return LearningArtifactSourceSpan(
        source_ref=SOURCE_REF,
        text=(
            "Long-term potentiation is persistent strengthening of synapses after "
            "high-frequency stimulation."
        ),
    )


def test_validate_flashcard_accepts_source_supported_artifact() -> None:
    artifact = LearningArtifact(
        artifact_id="ltp-card",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        difficulty=LearningArtifactDifficulty.CORE,
        source_spans=(_span(),),
    )

    result = validate_learning_artifact(artifact, SOURCE_MAP)

    assert result.accepted is True
    assert result.issues == ()


def test_validate_artifacts_rejects_unsupported_source_mismatched_vague_and_duplicates() -> None:
    good = LearningArtifact(
        artifact_id="supported",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(_span(),),
    )
    duplicate = LearningArtifact(
        artifact_id="duplicate",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(_span(),),
    )
    unsupported = LearningArtifact(
        artifact_id="unsupported",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="Explain this",
        answer="Astrocytes directly store the memory trace.",
        source_spans=(_span(),),
    )
    mismatched = LearningArtifact(
        artifact_id="mismatched",
        kind=LearningArtifactKind.SUMMARY,
        prompt="",
        content="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(LearningArtifactSourceSpan(source_ref=SOURCE_REF, text="not in source"),),
    )
    broad = LearningArtifact(
        artifact_id="broad",
        kind=LearningArtifactKind.QUIZ,
        prompt="Explain the entire course?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(_span(),),
    )

    report = validate_learning_artifacts(
        [good, duplicate, unsupported, mismatched, broad],
        SOURCE_MAP,
    )

    issue_codes = {
        result.artifact.artifact_id: {issue.code for issue in result.issues}
        for result in report.results
    }
    assert report.accepted == (good,)
    assert issue_codes["duplicate"] == {"duplicate_artifact"}
    assert {"vague_artifact", "unsupported_content"} <= issue_codes["unsupported"]
    assert "source_mismatch" in issue_codes["mismatched"]
    assert issue_codes["broad"] == {"overly_broad_artifact"}


def test_validate_artifacts_rejects_invalid_runtime_kind_without_crashing() -> None:
    invalid_kind = LearningArtifact(
        artifact_id="invalid-kind",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(_span(),),
    )
    object.__setattr__(invalid_kind, "kind", "flashcard")

    report = validate_learning_artifacts([invalid_kind], SOURCE_MAP)

    assert report.passed is False
    assert {issue.code for issue in report.rejected[0].issues} == {"invalid_kind"}


def test_validate_artifact_rejects_out_of_range_source_span_offsets() -> None:
    artifact = LearningArtifact(
        artifact_id="bad-offsets",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(
            LearningArtifactSourceSpan(
                source_ref=SOURCE_REF,
                text=(
                    "Long-term potentiation is persistent strengthening of synapses after "
                    "high-frequency stimulation."
                ),
                start=0,
                end=len(SOURCE_TEXT) + 20,
            ),
        ),
    )

    result = validate_learning_artifact(artifact, SOURCE_MAP)

    assert {issue.code for issue in result.issues} == {"invalid_source_span"}


def test_validate_artifacts_covers_all_supported_study_artifact_kinds() -> None:
    source_span = LearningArtifactSourceSpan(source_ref=SOURCE_REF, text=SOURCE_TEXT)
    artifacts = [
        LearningArtifact(
            artifact_id="cloze",
            kind=LearningArtifactKind.CLOZE_CARD,
            prompt="",
            content="Long-term potentiation is {{c1::persistent strengthening}} of synapses.",
            concept_tags=("Long-term potentiation",),
            source_spans=(source_span,),
        ),
        LearningArtifact(
            artifact_id="quiz",
            kind=LearningArtifactKind.QUIZ,
            prompt="What triggers calcium influx?",
            answer="NMDA receptor coincidence detection triggers calcium influx.",
            source_spans=(source_span,),
        ),
        LearningArtifact(
            artifact_id="summary",
            kind=LearningArtifactKind.SUMMARY,
            prompt="",
            content=(
                "Long-term potentiation is persistent strengthening of synapses after "
                "high-frequency stimulation."
            ),
            source_spans=(source_span,),
        ),
        LearningArtifact(
            artifact_id="misconception",
            kind=LearningArtifactKind.MISCONCEPTION,
            prompt="Correct the LTP misconception.",
            answer="LTP is not only structural; it includes persistent synaptic strengthening.",
            concept_tags=("Long-term potentiation",),
            source_spans=(source_span,),
        ),
        LearningArtifact(
            artifact_id="concept",
            kind=LearningArtifactKind.CONCEPT_TAG,
            prompt="",
            concept_tags=("Long-term potentiation",),
            source_spans=(source_span,),
        ),
        LearningArtifact(
            artifact_id="prerequisite",
            kind=LearningArtifactKind.PREREQUISITE,
            prompt="",
            content="Synaptic transmission is a prerequisite.",
            prerequisite_tags=("synaptic transmission",),
            source_spans=(source_span,),
        ),
    ]

    report = validate_learning_artifacts(artifacts, SOURCE_MAP)

    assert report.passed is True
    assert report.accepted == tuple(artifacts)


def test_validate_artifact_rejects_invalid_review_state() -> None:
    naive_last_reviewed_at = datetime(2026, 1, 1, tzinfo=UTC).replace(tzinfo=None)
    artifact = LearningArtifact(
        artifact_id="review",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(_span(),),
        review_state=LearningArtifactReviewState(
            reviews=1,
            lapses=2,
            mastery=1.5,
            last_reviewed_at=naive_last_reviewed_at,
            due_at=datetime(2026, 1, 2, tzinfo=UTC),
        ),
    )

    result = validate_learning_artifact(artifact, SOURCE_MAP)

    assert {issue.code for issue in result.issues} == {"invalid_review_state"}
    assert any("lapses cannot exceed reviews" in issue.message for issue in result.issues)
    assert any("mastery must be within" in issue.message for issue in result.issues)
    assert any("timezone-aware" in issue.message for issue in result.issues)


def test_record_learning_artifact_review_advances_due_date_without_mutating_original() -> None:
    artifact = LearningArtifact(
        artifact_id="ltp-card",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(_span(),),
    )
    reviewed_at = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)

    reviewed = record_learning_artifact_review(
        artifact,
        RecallRating.EASY,
        reviewed_at=reviewed_at,
    )

    assert artifact.review_state == LearningArtifactReviewState()
    assert reviewed.review_state.reviews == 1
    assert reviewed.review_state.lapses == 0
    assert reviewed.review_state.mastery == 1.0
    assert reviewed.review_state.last_reviewed_at == reviewed_at
    assert reviewed.review_state.due_at == datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    assert validate_learning_artifact(reviewed, SOURCE_MAP).accepted is True


def test_next_learning_artifact_review_state_tracks_lapses_and_hint_penalties() -> None:
    previous = LearningArtifactReviewState(
        reviews=1,
        lapses=0,
        mastery=1.0,
        last_reviewed_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        due_at=datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
    )
    reviewed_at = datetime(2026, 6, 1, 9, 30, tzinfo=UTC)

    state = next_learning_artifact_review_state(
        previous,
        RecallRating.HARD,
        reviewed_at=reviewed_at,
        hint_level_needed=2,
    )

    assert state.reviews == 2
    assert state.lapses == 1
    assert state.mastery == 0.678
    assert state.last_reviewed_at == reviewed_at
    assert state.due_at == datetime(2026, 6, 2, 9, 30, tzinfo=UTC)


def test_next_learning_artifact_review_state_reschedules_missed_reviews_immediately() -> None:
    reviewed_at = datetime(2026, 6, 1, 9, 30, tzinfo=UTC)

    state = next_learning_artifact_review_state(
        LearningArtifactReviewState(mastery=0.4),
        RecallRating.NONE,
        reviewed_at=reviewed_at,
    )

    assert state.reviews == 1
    assert state.lapses == 1
    assert state.mastery == 0.26
    assert state.due_at == reviewed_at


def test_next_learning_artifact_review_state_rejects_invalid_review_inputs() -> None:
    naive_reviewed_at = datetime(2026, 5, 19, 12, 0, tzinfo=UTC).replace(tzinfo=None)

    with pytest.raises(ValueError, match="timezone-aware"):
        next_learning_artifact_review_state(
            LearningArtifactReviewState(),
            RecallRating.GOOD,
            reviewed_at=naive_reviewed_at,
        )
    with pytest.raises(ValueError, match="hint_level_needed"):
        next_learning_artifact_review_state(
            LearningArtifactReviewState(),
            RecallRating.GOOD,
            reviewed_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
            hint_level_needed=-1,
        )


def test_anki_export_requires_validated_card_artifacts() -> None:
    accepted = LearningArtifact(
        artifact_id="ltp-card",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        difficulty=LearningArtifactDifficulty.INTRO,
        source_spans=(_span(),),
    )

    tsv = learning_artifacts_to_anki_tsv([accepted], SOURCE_MAP)

    assert tsv == (
        "What is long-term potentiation?\t"
        "Long-term potentiation is persistent strengthening of synapses.\t"
        "materials/lecture.md#chunk=2\t"
        "long_term_potentiation materials_lecture_md\tintro\n"
    )

    rejected = LearningArtifact(
        artifact_id="bad",
        kind=LearningArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Astrocytes directly store the memory trace.",
        source_spans=(_span(),),
    )
    with pytest.raises(ValueError, match="unsupported_content"):
        learning_artifacts_to_anki_tsv([rejected], SOURCE_MAP)
