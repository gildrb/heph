"""Source-grounded learning artifact models and validators."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum

from hephaistos.study.mastery import next_recall_mastery
from hephaistos.study.state import RecallRating


class LearningArtifactKind(StrEnum):
    FLASHCARD = "flashcard"
    CLOZE_CARD = "cloze_card"
    QUIZ = "quiz"
    SUMMARY = "summary"
    MISCONCEPTION = "misconception"
    CONCEPT_TAG = "concept_tag"
    PREREQUISITE = "prerequisite"


class LearningArtifactDifficulty(StrEnum):
    INTRO = "intro"
    CORE = "core"
    ADVANCED = "advanced"


@dataclass(frozen=True, slots=True)
class LearningArtifactSourceSpan:
    source_ref: str
    text: str
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True, slots=True)
class LearningArtifactReviewState:
    reviews: int = 0
    lapses: int = 0
    mastery: float = 0.0
    last_reviewed_at: datetime | None = None
    due_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LearningArtifact:
    artifact_id: str
    kind: LearningArtifactKind
    prompt: str
    answer: str = ""
    content: str = ""
    concept_tags: tuple[str, ...] = ()
    prerequisite_tags: tuple[str, ...] = ()
    difficulty: LearningArtifactDifficulty = LearningArtifactDifficulty.CORE
    source_spans: tuple[LearningArtifactSourceSpan, ...] = ()
    review_state: LearningArtifactReviewState = field(default_factory=LearningArtifactReviewState)


@dataclass(frozen=True, slots=True)
class LearningArtifactIssue:
    artifact_id: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class LearningArtifactValidationResult:
    artifact: LearningArtifact
    issues: tuple[LearningArtifactIssue, ...] = ()

    @property
    def accepted(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class LearningArtifactValidationReport:
    results: tuple[LearningArtifactValidationResult, ...]

    @property
    def accepted(self) -> tuple[LearningArtifact, ...]:
        return tuple(result.artifact for result in self.results if result.accepted)

    @property
    def rejected(self) -> tuple[LearningArtifactValidationResult, ...]:
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
type _ArtifactRule = tuple[str, str, Callable[[LearningArtifact], bool]]


def _valid_flashcard(artifact: LearningArtifact) -> bool:
    return bool(_clean(artifact.prompt) and _clean(artifact.answer))


def _valid_cloze_card(artifact: LearningArtifact) -> bool:
    return bool(_CLOZE_RE.search(_clean(artifact.content) or _clean(artifact.prompt)))


def _valid_quiz(artifact: LearningArtifact) -> bool:
    return "?" in _clean(artifact.prompt) and bool(_clean(artifact.answer))


def _valid_summary(artifact: LearningArtifact) -> bool:
    return len(_TOKEN_RE.findall(_clean(artifact.content) or _clean(artifact.answer))) >= 8


def _valid_misconception(artifact: LearningArtifact) -> bool:
    return bool(_clean(artifact.content) or _clean(artifact.answer))


def _valid_concept_tag(artifact: LearningArtifact) -> bool:
    return bool(artifact.concept_tags)


def _valid_prerequisite(artifact: LearningArtifact) -> bool:
    return bool(artifact.prerequisite_tags)


_ARTIFACT_KIND_RULES: dict[LearningArtifactKind, _ArtifactRule] = {
    LearningArtifactKind.FLASHCARD: (
        "invalid_flashcard",
        "flashcards need prompt and answer",
        _valid_flashcard,
    ),
    LearningArtifactKind.CLOZE_CARD: (
        "invalid_cloze",
        "cloze cards need {{c1::...}} text",
        _valid_cloze_card,
    ),
    LearningArtifactKind.QUIZ: (
        "invalid_quiz",
        "quizzes need a question and answer",
        _valid_quiz,
    ),
    LearningArtifactKind.SUMMARY: (
        "invalid_summary",
        "summaries need supported content",
        _valid_summary,
    ),
    LearningArtifactKind.MISCONCEPTION: (
        "invalid_misconception",
        "misconceptions need a correction",
        _valid_misconception,
    ),
    LearningArtifactKind.CONCEPT_TAG: (
        "invalid_concept_tag",
        "concept tags are required",
        _valid_concept_tag,
    ),
    LearningArtifactKind.PREREQUISITE: (
        "invalid_prerequisite",
        "prerequisite tags are required",
        _valid_prerequisite,
    ),
}


def validate_learning_artifact(
    artifact: LearningArtifact,
    source_text_by_ref: Mapping[str, str] | None = None,
) -> LearningArtifactValidationResult:
    source_map = source_text_by_ref or {}
    return LearningArtifactValidationResult(artifact, _artifact_issues(artifact, source_map))


def validate_learning_artifacts(
    artifacts: Sequence[LearningArtifact],
    source_text_by_ref: Mapping[str, str] | None = None,
) -> LearningArtifactValidationReport:
    seen: dict[str, str] = {}
    results: list[LearningArtifactValidationResult] = []
    source_map = source_text_by_ref or {}
    for artifact in artifacts:
        issues = list(_artifact_issues(artifact, source_map))
        fingerprint = _artifact_fingerprint(artifact)
        if fingerprint in seen:
            issues.append(
                LearningArtifactIssue(
                    artifact_id=artifact.artifact_id,
                    code="duplicate_artifact",
                    message=f"duplicates artifact {seen[fingerprint]}",
                )
            )
        else:
            seen[fingerprint] = artifact.artifact_id
        results.append(LearningArtifactValidationResult(artifact=artifact, issues=tuple(issues)))
    return LearningArtifactValidationReport(results=tuple(results))


def learning_artifacts_to_anki_tsv(
    artifacts: Sequence[LearningArtifact],
    source_text_by_ref: Mapping[str, str] | None = None,
) -> str:
    report = validate_learning_artifacts(artifacts, source_text_by_ref)
    if report.rejected:
        raise ValueError(_rejected_artifact_export_message(report.rejected))

    rows = [row for artifact in report.accepted if (row := _anki_row_for_artifact(artifact))]
    if not rows:
        raise ValueError("no flashcard, cloze, or quiz artifacts available for Anki export")

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def _rejected_artifact_export_message(
    rejected: Sequence[LearningArtifactValidationResult],
) -> str:
    failures = [
        f"{result.artifact.artifact_id}: {', '.join(issue.code for issue in result.issues)}"
        for result in rejected
    ]
    return "cannot export rejected learning artifacts: " + "; ".join(failures)


def _anki_row_for_artifact(artifact: LearningArtifact) -> tuple[str, str, str, str, str] | None:
    front_back = _anki_front_back(artifact)
    if front_back is None:
        return None
    front, back = front_back
    if not front:
        return None
    return (
        front,
        back,
        ", ".join(span.source_ref for span in artifact.source_spans),
        " ".join(_anki_tag_value(tag) for tag in _anki_tags(artifact)),
        artifact.difficulty.value,
    )


def _anki_front_back(artifact: LearningArtifact) -> tuple[str, str] | None:
    if artifact.kind is LearningArtifactKind.CLOZE_CARD:
        return artifact.content or artifact.prompt, artifact.answer
    if artifact.kind in {LearningArtifactKind.FLASHCARD, LearningArtifactKind.QUIZ}:
        return artifact.prompt, artifact.answer or artifact.content
    return None


def _anki_tag_value(tag: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", tag.strip().casefold()).strip("_") or "source"


def next_learning_artifact_review_state(
    state: LearningArtifactReviewState,
    rating: RecallRating,
    *,
    reviewed_at: datetime,
    hint_level_needed: int | None = None,
) -> LearningArtifactReviewState:
    _validate_review_input(rating, reviewed_at, hint_level_needed)
    reviews = state.reviews + 1
    lapse = rating in {RecallRating.HARD, RecallRating.NONE}
    lapses = state.lapses + (1 if lapse else 0)
    mastery = next_recall_mastery(state.mastery, rating, hint_level_needed)
    interval = _next_artifact_review_interval(rating, reviews=reviews, mastery=mastery)
    return LearningArtifactReviewState(
        reviews=reviews,
        lapses=lapses,
        mastery=mastery,
        last_reviewed_at=reviewed_at,
        due_at=reviewed_at + interval,
    )


def _validate_review_input(
    rating: RecallRating,
    reviewed_at: datetime,
    hint_level_needed: int | None,
) -> None:
    if not isinstance(rating, RecallRating):
        raise TypeError("rating must be a RecallRating")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ValueError("reviewed_at must be timezone-aware")
    if hint_level_needed is not None and hint_level_needed < 0:
        raise ValueError("hint_level_needed cannot be negative")


def _next_artifact_review_interval(
    rating: RecallRating,
    *,
    reviews: int,
    mastery: float,
) -> timedelta:
    if rating is RecallRating.NONE:
        return timedelta(0)
    if rating is RecallRating.HARD:
        return timedelta(days=1)
    base_days = 7 if rating is RecallRating.EASY else 3
    review_multiplier = 1.0 + (min(max(reviews - 1, 0), 8) * 0.35)
    mastery_multiplier = 1.0 + (mastery * (0.65 if rating is RecallRating.EASY else 0.35))
    days = round(base_days * review_multiplier * mastery_multiplier)
    return timedelta(days=min(_MAX_ARTIFACT_REVIEW_INTERVAL_DAYS, max(1, days)))


def record_learning_artifact_review(
    artifact: LearningArtifact,
    rating: RecallRating,
    *,
    reviewed_at: datetime,
    hint_level_needed: int | None = None,
) -> LearningArtifact:
    return replace(
        artifact,
        review_state=next_learning_artifact_review_state(
            artifact.review_state,
            rating,
            reviewed_at=reviewed_at,
            hint_level_needed=hint_level_needed,
        ),
    )


def _artifact_issues(
    artifact: LearningArtifact,
    source_text_by_ref: Mapping[str, str],
) -> tuple[LearningArtifactIssue, ...]:
    issues: list[LearningArtifactIssue] = []
    issues.extend(_shape_issues(artifact))
    issues.extend(_source_span_issues(artifact, source_text_by_ref))
    issues.extend(_review_state_issues(artifact))
    source_tokens = {
        token for span in artifact.source_spans for token in _significant_tokens(span.text)
    }
    issues.extend(_support_issues(artifact, source_tokens))
    return tuple(issues)


def _shape_issues(artifact: LearningArtifact) -> tuple[LearningArtifactIssue, ...]:
    issues: list[LearningArtifactIssue] = []
    if not artifact.artifact_id.strip():
        issues.append(_issue(artifact, "missing_id", "artifact_id is required"))
    valid_kind = isinstance(artifact.kind, LearningArtifactKind)
    if not valid_kind:
        issues.append(_issue(artifact, "invalid_kind", "kind must be a LearningArtifactKind"))
    if not isinstance(artifact.difficulty, LearningArtifactDifficulty):
        issues.append(
            _issue(
                artifact,
                "invalid_difficulty",
                "difficulty must be a LearningArtifactDifficulty",
            )
        )
    prompt = _clean(artifact.prompt)
    answer = _clean(artifact.answer)
    content = _clean(artifact.content)
    issues.extend(_text_shape_issues(artifact, (prompt, answer, content)))

    if valid_kind:
        code, message, is_valid = _ARTIFACT_KIND_RULES[artifact.kind]
        if not is_valid(artifact):
            issues.append(_issue(artifact, code, message))
    return tuple(issues)


def _text_shape_issues(
    artifact: LearningArtifact,
    texts: tuple[str, str, str],
) -> tuple[LearningArtifactIssue, ...]:
    issues: list[LearningArtifactIssue] = []
    if any(_is_vague(text) for text in texts):
        issues.append(_issue(artifact, "vague_artifact", "artifact text is too vague"))
    if any(_is_overly_broad_text(text) for text in texts):
        issues.append(
            _issue(artifact, "overly_broad_artifact", "artifact asks for too broad a scope")
        )
    return tuple(issues)


def _is_overly_broad_text(text: str) -> bool:
    return bool(_BROAD_RE.search(text)) or len(_TOKEN_RE.findall(text)) > 180


def _source_span_issues(
    artifact: LearningArtifact,
    source_text_by_ref: Mapping[str, str],
) -> tuple[LearningArtifactIssue, ...]:
    if not artifact.source_spans:
        return (_issue(artifact, "missing_source_span", "at least one source span is required"),)
    issues: list[LearningArtifactIssue] = []
    for span in artifact.source_spans:
        issues.extend(_single_source_span_issues(artifact, span, source_text_by_ref))
    return tuple(issues)


def _single_source_span_issues(
    artifact: LearningArtifact,
    span: LearningArtifactSourceSpan,
    source_text_by_ref: Mapping[str, str],
) -> tuple[LearningArtifactIssue, ...]:
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
    artifact: LearningArtifact,
    span: LearningArtifactSourceSpan,
) -> LearningArtifactIssue | None:
    if (span.start is None) != (span.end is None):
        return _issue(artifact, "invalid_source_span", "span offsets must be paired")
    if span.start is None or span.end is None:
        return None
    if span.start < 0 or span.end <= span.start:
        return _issue(artifact, "invalid_source_span", "span offsets are invalid")
    return None


def _source_span_bounds_issue(
    artifact: LearningArtifact,
    span: LearningArtifactSourceSpan,
    source_text: str,
) -> LearningArtifactIssue | None:
    if span.end is not None and span.end > len(source_text):
        return _issue(artifact, "invalid_source_span", "span offsets are invalid")
    return None


def _review_state_issues(artifact: LearningArtifact) -> tuple[LearningArtifactIssue, ...]:
    state = artifact.review_state
    issues: list[LearningArtifactIssue] = []
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
    artifact: LearningArtifact,
    source_tokens: set[str],
) -> tuple[LearningArtifactIssue, ...]:
    if not source_tokens:
        return ()
    issues: list[LearningArtifactIssue] = []
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


def _span_matches_source(span: LearningArtifactSourceSpan, source_text: str) -> bool:
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


def _artifact_fingerprint(artifact: LearningArtifact) -> str:
    kind = artifact.kind
    kind_value = kind.value if isinstance(kind, LearningArtifactKind) else str(kind)
    parts = (
        kind_value,
        _normalized_for_match(artifact.prompt),
        _normalized_for_match(artifact.answer),
        _normalized_for_match(artifact.content),
        "|".join(span.source_ref for span in artifact.source_spans),
    )
    return "\n".join(parts)


def _anki_tags(artifact: LearningArtifact) -> tuple[str, ...]:
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


def _issue(artifact: LearningArtifact, code: str, message: str) -> LearningArtifactIssue:
    return LearningArtifactIssue(artifact_id=artifact.artifact_id, code=code, message=message)
