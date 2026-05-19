from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hephaistos.study.artifacts import (
    StudyArtifact,
    StudyArtifactDifficulty,
    StudyArtifactKind,
    StudyArtifactReviewState,
    StudyArtifactSourceSpan,
    next_study_artifact_review_state,
    record_study_artifact_review,
    study_artifacts_to_anki_tsv,
    validate_study_artifact,
    validate_study_artifacts,
)
from hephaistos.study.state import StudyRecallRating

SOURCE_REF = "materials/lecture.md#chunk=2"
SOURCE_TEXT = (
    "Long-term potentiation is persistent strengthening of synapses after "
    "high-frequency stimulation. NMDA receptor coincidence detection triggers "
    "calcium influx. Common misconception: LTP is only a structural change. "
    "Prerequisite: synaptic transmission."
)
SOURCE_MAP = {SOURCE_REF: SOURCE_TEXT}


def _span() -> StudyArtifactSourceSpan:
    return StudyArtifactSourceSpan(
        source_ref=SOURCE_REF,
        text=(
            "Long-term potentiation is persistent strengthening of synapses after "
            "high-frequency stimulation."
        ),
    )


def test_validate_flashcard_accepts_source_supported_artifact() -> None:
    artifact = StudyArtifact(
        artifact_id="ltp-card",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        difficulty=StudyArtifactDifficulty.CORE,
        source_spans=(_span(),),
    )

    result = validate_study_artifact(artifact, SOURCE_MAP)

    assert result.accepted is True
    assert result.issues == ()


def test_validate_artifacts_rejects_unsupported_source_mismatched_vague_and_duplicates() -> None:
    good = StudyArtifact(
        artifact_id="supported",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(_span(),),
    )
    duplicate = StudyArtifact(
        artifact_id="duplicate",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(_span(),),
    )
    unsupported = StudyArtifact(
        artifact_id="unsupported",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="Explain this",
        answer="Astrocytes directly store the memory trace.",
        source_spans=(_span(),),
    )
    mismatched = StudyArtifact(
        artifact_id="mismatched",
        kind=StudyArtifactKind.SUMMARY,
        prompt="",
        content="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(StudyArtifactSourceSpan(source_ref=SOURCE_REF, text="not in source"),),
    )
    broad = StudyArtifact(
        artifact_id="broad",
        kind=StudyArtifactKind.QUIZ,
        prompt="Explain the entire course?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(_span(),),
    )

    report = validate_study_artifacts(
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
    invalid_kind = StudyArtifact(
        artifact_id="invalid-kind",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(_span(),),
    )
    object.__setattr__(invalid_kind, "kind", "flashcard")

    report = validate_study_artifacts([invalid_kind], SOURCE_MAP)

    assert report.passed is False
    assert {issue.code for issue in report.rejected[0].issues} == {"invalid_kind"}


def test_validate_artifact_rejects_out_of_range_source_span_offsets() -> None:
    artifact = StudyArtifact(
        artifact_id="bad-offsets",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        source_spans=(
            StudyArtifactSourceSpan(
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

    result = validate_study_artifact(artifact, SOURCE_MAP)

    assert {issue.code for issue in result.issues} == {"invalid_source_span"}


def test_validate_artifacts_covers_all_supported_study_artifact_kinds() -> None:
    source_span = StudyArtifactSourceSpan(source_ref=SOURCE_REF, text=SOURCE_TEXT)
    artifacts = [
        StudyArtifact(
            artifact_id="cloze",
            kind=StudyArtifactKind.CLOZE_CARD,
            prompt="",
            content="Long-term potentiation is {{c1::persistent strengthening}} of synapses.",
            concept_tags=("Long-term potentiation",),
            source_spans=(source_span,),
        ),
        StudyArtifact(
            artifact_id="quiz",
            kind=StudyArtifactKind.QUIZ,
            prompt="What triggers calcium influx?",
            answer="NMDA receptor coincidence detection triggers calcium influx.",
            source_spans=(source_span,),
        ),
        StudyArtifact(
            artifact_id="summary",
            kind=StudyArtifactKind.SUMMARY,
            prompt="",
            content=(
                "Long-term potentiation is persistent strengthening of synapses after "
                "high-frequency stimulation."
            ),
            source_spans=(source_span,),
        ),
        StudyArtifact(
            artifact_id="misconception",
            kind=StudyArtifactKind.MISCONCEPTION,
            prompt="Correct the LTP misconception.",
            answer="LTP is not only structural; it includes persistent synaptic strengthening.",
            concept_tags=("Long-term potentiation",),
            source_spans=(source_span,),
        ),
        StudyArtifact(
            artifact_id="concept",
            kind=StudyArtifactKind.CONCEPT_TAG,
            prompt="",
            concept_tags=("Long-term potentiation",),
            source_spans=(source_span,),
        ),
        StudyArtifact(
            artifact_id="prerequisite",
            kind=StudyArtifactKind.PREREQUISITE,
            prompt="",
            content="Synaptic transmission is a prerequisite.",
            prerequisite_tags=("synaptic transmission",),
            source_spans=(source_span,),
        ),
    ]

    report = validate_study_artifacts(artifacts, SOURCE_MAP)

    assert report.passed is True
    assert report.accepted == tuple(artifacts)


def test_validate_artifact_rejects_invalid_review_state() -> None:
    naive_last_reviewed_at = datetime(2026, 1, 1, tzinfo=UTC).replace(tzinfo=None)
    artifact = StudyArtifact(
        artifact_id="review",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(_span(),),
        review_state=StudyArtifactReviewState(
            reviews=1,
            lapses=2,
            mastery=1.5,
            last_reviewed_at=naive_last_reviewed_at,
            due_at=datetime(2026, 1, 2, tzinfo=UTC),
        ),
    )

    result = validate_study_artifact(artifact, SOURCE_MAP)

    assert {issue.code for issue in result.issues} == {"invalid_review_state"}
    assert any("lapses cannot exceed reviews" in issue.message for issue in result.issues)
    assert any("mastery must be within" in issue.message for issue in result.issues)
    assert any("timezone-aware" in issue.message for issue in result.issues)


def test_record_study_artifact_review_advances_due_date_without_mutating_original() -> None:
    artifact = StudyArtifact(
        artifact_id="ltp-card",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        source_spans=(_span(),),
    )
    reviewed_at = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)

    reviewed = record_study_artifact_review(
        artifact,
        StudyRecallRating.EASY,
        reviewed_at=reviewed_at,
    )

    assert artifact.review_state == StudyArtifactReviewState()
    assert reviewed.review_state.reviews == 1
    assert reviewed.review_state.lapses == 0
    assert reviewed.review_state.mastery == 1.0
    assert reviewed.review_state.last_reviewed_at == reviewed_at
    assert reviewed.review_state.due_at == datetime(2026, 5, 31, 12, 0, tzinfo=UTC)
    assert validate_study_artifact(reviewed, SOURCE_MAP).accepted is True


def test_next_study_artifact_review_state_tracks_lapses_and_hint_penalties() -> None:
    previous = StudyArtifactReviewState(
        reviews=1,
        lapses=0,
        mastery=1.0,
        last_reviewed_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        due_at=datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
    )
    reviewed_at = datetime(2026, 6, 1, 9, 30, tzinfo=UTC)

    state = next_study_artifact_review_state(
        previous,
        StudyRecallRating.HARD,
        reviewed_at=reviewed_at,
        hint_level_needed=2,
    )

    assert state.reviews == 2
    assert state.lapses == 1
    assert state.mastery == 0.678
    assert state.last_reviewed_at == reviewed_at
    assert state.due_at == datetime(2026, 6, 2, 9, 30, tzinfo=UTC)


def test_next_study_artifact_review_state_reschedules_missed_reviews_immediately() -> None:
    reviewed_at = datetime(2026, 6, 1, 9, 30, tzinfo=UTC)

    state = next_study_artifact_review_state(
        StudyArtifactReviewState(mastery=0.4),
        StudyRecallRating.NONE,
        reviewed_at=reviewed_at,
    )

    assert state.reviews == 1
    assert state.lapses == 1
    assert state.mastery == 0.26
    assert state.due_at == reviewed_at


def test_next_study_artifact_review_state_rejects_invalid_review_inputs() -> None:
    naive_reviewed_at = datetime(2026, 5, 19, 12, 0, tzinfo=UTC).replace(tzinfo=None)

    with pytest.raises(ValueError, match="timezone-aware"):
        next_study_artifact_review_state(
            StudyArtifactReviewState(),
            StudyRecallRating.GOOD,
            reviewed_at=naive_reviewed_at,
        )
    with pytest.raises(ValueError, match="hint_level_needed"):
        next_study_artifact_review_state(
            StudyArtifactReviewState(),
            StudyRecallRating.GOOD,
            reviewed_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
            hint_level_needed=-1,
        )


def test_anki_export_requires_validated_card_artifacts() -> None:
    accepted = StudyArtifact(
        artifact_id="ltp-card",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Long-term potentiation is persistent strengthening of synapses.",
        concept_tags=("Long-term potentiation",),
        difficulty=StudyArtifactDifficulty.INTRO,
        source_spans=(_span(),),
    )

    tsv = study_artifacts_to_anki_tsv([accepted], SOURCE_MAP)

    assert tsv == (
        "What is long-term potentiation?\t"
        "Long-term potentiation is persistent strengthening of synapses.\t"
        "materials/lecture.md#chunk=2\t"
        "long_term_potentiation materials_lecture_md\tintro\n"
    )

    rejected = StudyArtifact(
        artifact_id="bad",
        kind=StudyArtifactKind.FLASHCARD,
        prompt="What is long-term potentiation?",
        answer="Astrocytes directly store the memory trace.",
        source_spans=(_span(),),
    )
    with pytest.raises(ValueError, match="unsupported_content"):
        study_artifacts_to_anki_tsv([rejected], SOURCE_MAP)
