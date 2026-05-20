"""Source-grounded study artifact models and validators."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum

from hephaistos.study.mastery import next_recall_mastery
from hephaistos.study.state import StudyRecallRating


class StudyArtifactKind(StrEnum):
    FLASHCARD = "flashcard"
    CLOZE_CARD = "cloze_card"
    QUIZ = "quiz"
    SUMMARY = "summary"
    MISCONCEPTION = "misconception"
    CONCEPT_TAG = "concept_tag"
    PREREQUISITE = "prerequisite"


class StudyArtifactDifficulty(StrEnum):
    INTRO = "intro"
    CORE = "core"
    ADVANCED = "advanced"


@dataclass(frozen=True, slots=True)
class StudyArtifactSourceSpan:
    source_ref: str
    text: str
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True, slots=True)
class StudyArtifactReviewState:
    reviews: int = 0
    lapses: int = 0
    mastery: float = 0.0
    last_reviewed_at: datetime | None = None
    due_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class StudyArtifact:
    artifact_id: str
    kind: StudyArtifactKind
    prompt: str
    answer: str = ""
    content: str = ""
    concept_tags: tuple[str, ...] = ()
    prerequisite_tags: tuple[str, ...] = ()
    difficulty: StudyArtifactDifficulty = StudyArtifactDifficulty.CORE
    source_spans: tuple[StudyArtifactSourceSpan, ...] = ()
    review_state: StudyArtifactReviewState = field(default_factory=StudyArtifactReviewState)


@dataclass(frozen=True, slots=True)
class StudyArtifactIssue:
    artifact_id: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class StudyArtifactValidationResult:
    artifact: StudyArtifact
    issues: tuple[StudyArtifactIssue, ...] = ()

    @property
    def accepted(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class StudyArtifactValidationReport:
    results: tuple[StudyArtifactValidationResult, ...]

    @property
    def accepted(self) -> tuple[StudyArtifact, ...]:
        return tuple(result.artifact for result in self.results if result.accepted)

    @property
    def rejected(self) -> tuple[StudyArtifactValidationResult, ...]:
        return tuple(result for result in self.results if not result.accepted)

    @property
    def passed(self) -> bool:
        return not self.rejected


_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_-]{2,}")
_WHITESPACE_RE = re.compile(r"\s+")
_CLOZE_RE = re.compile(r"\{\{c\d+::(?P<text>[^}]+)\}\}", re.IGNORECASE)
_BROAD_RE = re.compile(
    r"\b(?:all|everything|entire|whole)\s+"
    r"(?:course|exam|module|subject|syllabus|textbook|topic)\b",
    re.IGNORECASE,
)
_VAGUE_PHRASES = frozenset(
    {
        "explain this",
        "important concept",
        "learn this",
        "remember this",
        "study this",
        "understand this",
        "what is it?",
    }
)
_STOPWORDS = frozenset(
    {
        "about",
        "also",
        "and",
        "are",
        "because",
        "before",
        "can",
        "does",
        "for",
        "from",
        "how",
        "into",
        "its",
        "not",
        "the",
        "this",
        "what",
        "when",
        "where",
        "which",
        "why",
        "with",
    }
)
_MAX_ARTIFACT_REVIEW_INTERVAL_DAYS = 365
type _ArtifactRule = tuple[str, str, Callable[[StudyArtifact], bool]]


def _valid_flashcard(artifact: StudyArtifact) -> bool:
    return bool(_clean(artifact.prompt) and _clean(artifact.answer))


def _valid_cloze_card(artifact: StudyArtifact) -> bool:
    return bool(_CLOZE_RE.search(_clean(artifact.content) or _clean(artifact.prompt)))


def _valid_quiz(artifact: StudyArtifact) -> bool:
    return "?" in _clean(artifact.prompt) and bool(_clean(artifact.answer))


def _valid_summary(artifact: StudyArtifact) -> bool:
    return len(_TOKEN_RE.findall(_clean(artifact.content) or _clean(artifact.answer))) >= 8


def _valid_misconception(artifact: StudyArtifact) -> bool:
    return bool(_clean(artifact.content) or _clean(artifact.answer))


def _valid_concept_tag(artifact: StudyArtifact) -> bool:
    return bool(artifact.concept_tags)


def _valid_prerequisite(artifact: StudyArtifact) -> bool:
    return bool(artifact.prerequisite_tags)


_ARTIFACT_KIND_RULES: dict[StudyArtifactKind, _ArtifactRule] = {
    StudyArtifactKind.FLASHCARD: (
        "invalid_flashcard",
        "flashcards need prompt and answer",
        _valid_flashcard,
    ),
    StudyArtifactKind.CLOZE_CARD: (
        "invalid_cloze",
        "cloze cards need {{c1::...}} text",
        _valid_cloze_card,
    ),
    StudyArtifactKind.QUIZ: (
        "invalid_quiz",
        "quizzes need a question and answer",
        _valid_quiz,
    ),
    StudyArtifactKind.SUMMARY: (
        "invalid_summary",
        "summaries need supported content",
        _valid_summary,
    ),
    StudyArtifactKind.MISCONCEPTION: (
        "invalid_misconception",
        "misconceptions need a correction",
        _valid_misconception,
    ),
    StudyArtifactKind.CONCEPT_TAG: (
        "invalid_concept_tag",
        "concept tags are required",
        _valid_concept_tag,
    ),
    StudyArtifactKind.PREREQUISITE: (
        "invalid_prerequisite",
        "prerequisite tags are required",
        _valid_prerequisite,
    ),
}


def validate_study_artifact(
    artifact: StudyArtifact,
    source_text_by_ref: Mapping[str, str] | None = None,
) -> StudyArtifactValidationResult:
    source_map = source_text_by_ref or {}
    return StudyArtifactValidationResult(artifact, _artifact_issues(artifact, source_map))


def validate_study_artifacts(
    artifacts: Sequence[StudyArtifact],
    source_text_by_ref: Mapping[str, str] | None = None,
) -> StudyArtifactValidationReport:
    seen: dict[str, str] = {}
    results: list[StudyArtifactValidationResult] = []
    source_map = source_text_by_ref or {}
    for artifact in artifacts:
        issues = list(_artifact_issues(artifact, source_map))
        fingerprint = _artifact_fingerprint(artifact)
        if fingerprint in seen:
            issues.append(
                StudyArtifactIssue(
                    artifact_id=artifact.artifact_id,
                    code="duplicate_artifact",
                    message=f"duplicates artifact {seen[fingerprint]}",
                )
            )
        else:
            seen[fingerprint] = artifact.artifact_id
        results.append(StudyArtifactValidationResult(artifact=artifact, issues=tuple(issues)))
    return StudyArtifactValidationReport(results=tuple(results))


def study_artifacts_to_anki_tsv(
    artifacts: Sequence[StudyArtifact],
    source_text_by_ref: Mapping[str, str] | None = None,
) -> str:
    report = validate_study_artifacts(artifacts, source_text_by_ref)
    if report.rejected:
        failures = [
            f"{result.artifact.artifact_id}: {', '.join(issue.code for issue in result.issues)}"
            for result in report.rejected
        ]
        raise ValueError("cannot export rejected study artifacts: " + "; ".join(failures))

    rows: list[tuple[str, str, str, str, str]] = []
    for artifact in report.accepted:
        if artifact.kind is StudyArtifactKind.CLOZE_CARD:
            front, back = artifact.content or artifact.prompt, artifact.answer
        elif artifact.kind in {StudyArtifactKind.FLASHCARD, StudyArtifactKind.QUIZ}:
            front, back = artifact.prompt, artifact.answer or artifact.content
        else:
            continue
        if not front:
            continue
        rows.append(
            (
                front,
                back,
                ", ".join(span.source_ref for span in artifact.source_spans),
                " ".join(
                    re.sub(r"[^A-Za-z0-9_]+", "_", tag.strip().casefold()).strip("_") or "source"
                    for tag in _anki_tags(artifact)
                ),
                artifact.difficulty.value,
            )
        )
    if not rows:
        raise ValueError("no flashcard, cloze, or quiz artifacts available for Anki export")

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def next_study_artifact_review_state(
    state: StudyArtifactReviewState,
    rating: StudyRecallRating,
    *,
    reviewed_at: datetime,
    hint_level_needed: int | None = None,
) -> StudyArtifactReviewState:
    if not isinstance(rating, StudyRecallRating):
        raise TypeError("rating must be a StudyRecallRating")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ValueError("reviewed_at must be timezone-aware")
    if hint_level_needed is not None and hint_level_needed < 0:
        raise ValueError("hint_level_needed cannot be negative")

    reviews = state.reviews + 1
    lapse = rating in {StudyRecallRating.HARD, StudyRecallRating.NONE}
    lapses = state.lapses + (1 if lapse else 0)
    mastery = next_recall_mastery(state.mastery, rating, hint_level_needed)
    if rating is StudyRecallRating.NONE:
        interval = timedelta(0)
    elif rating is StudyRecallRating.HARD:
        interval = timedelta(days=1)
    else:
        base_days = 7 if rating is StudyRecallRating.EASY else 3
        review_multiplier = 1.0 + (min(max(reviews - 1, 0), 8) * 0.35)
        mastery_multiplier = 1.0 + (mastery * (0.65 if rating is StudyRecallRating.EASY else 0.35))
        days = round(base_days * review_multiplier * mastery_multiplier)
        interval = timedelta(days=min(_MAX_ARTIFACT_REVIEW_INTERVAL_DAYS, max(1, days)))
    return StudyArtifactReviewState(
        reviews=reviews,
        lapses=lapses,
        mastery=mastery,
        last_reviewed_at=reviewed_at,
        due_at=reviewed_at + interval,
    )


def record_study_artifact_review(
    artifact: StudyArtifact,
    rating: StudyRecallRating,
    *,
    reviewed_at: datetime,
    hint_level_needed: int | None = None,
) -> StudyArtifact:
    return replace(
        artifact,
        review_state=next_study_artifact_review_state(
            artifact.review_state,
            rating,
            reviewed_at=reviewed_at,
            hint_level_needed=hint_level_needed,
        ),
    )


def _artifact_issues(
    artifact: StudyArtifact,
    source_text_by_ref: Mapping[str, str],
) -> tuple[StudyArtifactIssue, ...]:
    issues: list[StudyArtifactIssue] = []
    issues.extend(_shape_issues(artifact))
    issues.extend(_source_span_issues(artifact, source_text_by_ref))
    issues.extend(_review_state_issues(artifact))
    source_tokens = {
        token for span in artifact.source_spans for token in _significant_tokens(span.text)
    }
    issues.extend(_support_issues(artifact, source_tokens))
    return tuple(issues)


def _shape_issues(artifact: StudyArtifact) -> tuple[StudyArtifactIssue, ...]:
    issues: list[StudyArtifactIssue] = []
    if not artifact.artifact_id.strip():
        issues.append(_issue(artifact, "missing_id", "artifact_id is required"))
    valid_kind = isinstance(artifact.kind, StudyArtifactKind)
    if not valid_kind:
        issues.append(_issue(artifact, "invalid_kind", "kind must be a StudyArtifactKind"))
    if not isinstance(artifact.difficulty, StudyArtifactDifficulty):
        issues.append(
            _issue(artifact, "invalid_difficulty", "difficulty must be a StudyArtifactDifficulty")
        )
    prompt = _clean(artifact.prompt)
    answer = _clean(artifact.answer)
    content = _clean(artifact.content)
    if any(_is_vague(text) for text in (prompt, answer, content)):
        issues.append(_issue(artifact, "vague_artifact", "artifact text is too vague"))
    if any(
        _BROAD_RE.search(text) or len(_TOKEN_RE.findall(text)) > 180
        for text in (prompt, answer, content)
    ):
        issues.append(
            _issue(artifact, "overly_broad_artifact", "artifact asks for too broad a scope")
        )

    if valid_kind:
        code, message, is_valid = _ARTIFACT_KIND_RULES[artifact.kind]
        if not is_valid(artifact):
            issues.append(_issue(artifact, code, message))
    return tuple(issues)


def _source_span_issues(
    artifact: StudyArtifact,
    source_text_by_ref: Mapping[str, str],
) -> tuple[StudyArtifactIssue, ...]:
    if not artifact.source_spans:
        return (_issue(artifact, "missing_source_span", "at least one source span is required"),)
    issues: list[StudyArtifactIssue] = []
    for span in artifact.source_spans:
        issues.extend(_single_source_span_issues(artifact, span, source_text_by_ref))
    return tuple(issues)


def _single_source_span_issues(
    artifact: StudyArtifact,
    span: StudyArtifactSourceSpan,
    source_text_by_ref: Mapping[str, str],
) -> tuple[StudyArtifactIssue, ...]:
    if not span.source_ref.strip() or not span.text.strip():
        return (_issue(artifact, "invalid_source_span", "source ref and text required"),)
    if offset_issue := _source_span_offset_issue(artifact, span):
        return (offset_issue,)

    source_text = source_text_by_ref.get(span.source_ref)
    if source_text is None:
        if not source_text_by_ref:
            return ()
        return (
            _issue(
                artifact,
                "source_mismatch",
                f"source ref is not available: {span.source_ref}",
            ),
        )
    if offset_issue := _source_span_bounds_issue(artifact, span, source_text):
        return (offset_issue,)
    if _span_matches_source(span, source_text):
        return ()
    return (
        _issue(
            artifact,
            "source_mismatch",
            f"source span text is not present in {span.source_ref}",
        ),
    )


def _source_span_offset_issue(
    artifact: StudyArtifact,
    span: StudyArtifactSourceSpan,
) -> StudyArtifactIssue | None:
    if (span.start is None) != (span.end is None):
        return _issue(artifact, "invalid_source_span", "span offsets must be paired")
    if span.start is None or span.end is None:
        return None
    if span.start < 0 or span.end <= span.start:
        return _issue(artifact, "invalid_source_span", "span offsets are invalid")
    return None


def _source_span_bounds_issue(
    artifact: StudyArtifact,
    span: StudyArtifactSourceSpan,
    source_text: str,
) -> StudyArtifactIssue | None:
    if span.end is not None and span.end > len(source_text):
        return _issue(artifact, "invalid_source_span", "span offsets are invalid")
    return None


def _review_state_issues(artifact: StudyArtifact) -> tuple[StudyArtifactIssue, ...]:
    state = artifact.review_state
    issues: list[StudyArtifactIssue] = []
    if state.reviews < 0 or state.lapses < 0:
        issues.append(
            _issue(artifact, "invalid_review_state", "reviews and lapses cannot be negative")
        )
    if state.lapses > state.reviews:
        issues.append(_issue(artifact, "invalid_review_state", "lapses cannot exceed reviews"))
    if not 0.0 <= state.mastery <= 1.0:
        issues.append(_issue(artifact, "invalid_review_state", "mastery must be within [0, 1]"))
    for label, value in (
        ("last_reviewed_at", state.last_reviewed_at),
        ("due_at", state.due_at),
    ):
        if value is not None and value.tzinfo is None:
            issues.append(
                _issue(artifact, "invalid_review_state", f"{label} must be timezone-aware")
            )
    return tuple(issues)


def _support_issues(
    artifact: StudyArtifact,
    source_tokens: set[str],
) -> tuple[StudyArtifactIssue, ...]:
    if not source_tokens:
        return ()
    issues: list[StudyArtifactIssue] = []
    for label, text in (("answer", artifact.answer), ("content", artifact.content)):
        tokens = _significant_tokens(_CLOZE_RE.sub(lambda match: match.group("text"), text))
        if tokens and len(tokens & source_tokens) / len(tokens) < 0.55:
            issues.append(
                _issue(
                    artifact,
                    "unsupported_content",
                    f"{label} is not sufficiently supported by source spans",
                )
            )
    for tag in artifact.concept_tags + artifact.prerequisite_tags:
        tokens = _significant_tokens(tag)
        if tokens and not tokens <= source_tokens:
            issues.append(
                _issue(
                    artifact,
                    "unsupported_tag",
                    f"tag is not supported by source spans: {tag}",
                )
            )
    return tuple(issues)


def _span_matches_source(span: StudyArtifactSourceSpan, source_text: str) -> bool:
    normalized_span = _normalized_for_match(span.text)
    if not normalized_span:
        return False
    if span.start is not None and span.end is not None:
        if span.start < 0 or span.end > len(source_text) or span.end <= span.start:
            return False
        selected = source_text[span.start : span.end]
        return _normalized_for_match(selected) == normalized_span
    return normalized_span in _normalized_for_match(source_text)


def _significant_tokens(text: str) -> set[str]:
    return {
        token.casefold() for token in _TOKEN_RE.findall(text) if token.casefold() not in _STOPWORDS
    }


def _artifact_fingerprint(artifact: StudyArtifact) -> str:
    kind = artifact.kind
    kind_value = kind.value if isinstance(kind, StudyArtifactKind) else str(kind)
    parts = (
        kind_value,
        _normalized_for_match(artifact.prompt),
        _normalized_for_match(artifact.answer),
        _normalized_for_match(artifact.content),
        "|".join(span.source_ref for span in artifact.source_spans),
    )
    return "\n".join(parts)


def _anki_tags(artifact: StudyArtifact) -> tuple[str, ...]:
    source_tags = tuple(
        span.source_ref.split("#", maxsplit=1)[0] for span in artifact.source_spans
    )
    return artifact.concept_tags + artifact.prerequisite_tags + source_tags


def _is_vague(text: str) -> bool:
    normalized = _normalized_for_match(text)
    if not normalized:
        return False
    if normalized in _VAGUE_PHRASES:
        return True
    tokens = _significant_tokens(text)
    return len(tokens) <= 1 and any(word in normalized for word in ("concept", "topic", "this"))


def _clean(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalized_for_match(text: str) -> str:
    return _clean(text).casefold()


def _issue(artifact: StudyArtifact, code: str, message: str) -> StudyArtifactIssue:
    return StudyArtifactIssue(artifact_id=artifact.artifact_id, code=code, message=message)
