"""Source-grounded study artifact models and validators."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class StudyArtifactKind(StrEnum):
    """Source-grounded study artifact families."""

    FLASHCARD = "flashcard"
    CLOZE_CARD = "cloze_card"
    QUIZ = "quiz"
    SUMMARY = "summary"
    MISCONCEPTION = "misconception"
    CONCEPT_TAG = "concept_tag"
    PREREQUISITE = "prerequisite"


class StudyArtifactDifficulty(StrEnum):
    """Human-readable study difficulty labels."""

    INTRO = "intro"
    CORE = "core"
    ADVANCED = "advanced"


@dataclass(frozen=True, slots=True)
class StudyArtifactSourceSpan:
    """A source excerpt that supports a study artifact."""

    source_ref: str
    text: str
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True, slots=True)
class StudyArtifactReviewState:
    """Deterministic review metadata for a study artifact."""

    reviews: int = 0
    lapses: int = 0
    mastery: float = 0.0
    last_reviewed_at: datetime | None = None
    due_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class StudyArtifact:
    """A source-grounded artifact that can enter a study workflow."""

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
    """A validation issue attached to one artifact."""

    artifact_id: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class StudyArtifactValidationResult:
    """Validation result for one study artifact."""

    artifact: StudyArtifact
    issues: tuple[StudyArtifactIssue, ...] = ()

    @property
    def accepted(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class StudyArtifactValidationReport:
    """Batch validation result for source-grounded study artifacts."""

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


def validate_study_artifact(
    artifact: StudyArtifact,
    source_text_by_ref: Mapping[str, str] | None = None,
) -> StudyArtifactValidationResult:
    """Validate one artifact against declared source text."""
    issues = list(_artifact_issues(artifact, source_text_by_ref or {}))
    return StudyArtifactValidationResult(artifact=artifact, issues=tuple(issues))


def validate_study_artifacts(
    artifacts: Sequence[StudyArtifact],
    source_text_by_ref: Mapping[str, str] | None = None,
) -> StudyArtifactValidationReport:
    """Validate artifacts and reject duplicates inside the batch."""
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
    """Return Anki-compatible TSV rows for validated flashcard-like artifacts."""
    report = validate_study_artifacts(artifacts, source_text_by_ref)
    if report.rejected:
        failures = [
            f"{result.artifact.artifact_id}: {', '.join(issue.code for issue in result.issues)}"
            for result in report.rejected
        ]
        raise ValueError("cannot export rejected study artifacts: " + "; ".join(failures))

    rows: list[tuple[str, str, str, str, str]] = []
    for artifact in report.accepted:
        front, back = _anki_card_fields(artifact)
        if not front:
            continue
        rows.append(
            (
                front,
                back,
                ", ".join(span.source_ref for span in artifact.source_spans),
                " ".join(_anki_tag(tag) for tag in _anki_tags(artifact)),
                artifact.difficulty.value,
            )
        )
    if not rows:
        raise ValueError("no flashcard, cloze, or quiz artifacts available for Anki export")

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def _artifact_issues(
    artifact: StudyArtifact,
    source_text_by_ref: Mapping[str, str],
) -> tuple[StudyArtifactIssue, ...]:
    issues: list[StudyArtifactIssue] = []
    issues.extend(_shape_issues(artifact))
    issues.extend(_source_span_issues(artifact, source_text_by_ref))
    issues.extend(_review_state_issues(artifact))
    source_tokens = _source_tokens(artifact)
    issues.extend(_support_issues(artifact, source_tokens))
    return tuple(issues)


def _shape_issues(artifact: StudyArtifact) -> tuple[StudyArtifactIssue, ...]:
    issues: list[StudyArtifactIssue] = []
    if not artifact.artifact_id.strip():
        issues.append(_issue(artifact, "missing_id", "artifact_id is required"))
    if not isinstance(artifact.kind, StudyArtifactKind):
        issues.append(_issue(artifact, "invalid_kind", "kind must be a StudyArtifactKind"))
    if not isinstance(artifact.difficulty, StudyArtifactDifficulty):
        issues.append(
            _issue(artifact, "invalid_difficulty", "difficulty must be a StudyArtifactDifficulty")
        )
    prompt = _clean(artifact.prompt)
    answer = _clean(artifact.answer)
    content = _clean(artifact.content)
    if _is_vague(prompt) or _is_vague(answer) or _is_vague(content):
        issues.append(_issue(artifact, "vague_artifact", "artifact text is too vague"))
    if _is_overly_broad(prompt) or _is_overly_broad(answer) or _is_overly_broad(content):
        issues.append(
            _issue(artifact, "overly_broad_artifact", "artifact asks for too broad a scope")
        )

    if artifact.kind is StudyArtifactKind.FLASHCARD and (not prompt or not answer):
        issues.append(_issue(artifact, "invalid_flashcard", "flashcards need prompt and answer"))
    elif artifact.kind is StudyArtifactKind.CLOZE_CARD:
        cloze_text = content or prompt
        if not _CLOZE_RE.search(cloze_text):
            issues.append(_issue(artifact, "invalid_cloze", "cloze cards need {{c1::...}} text"))
    elif artifact.kind is StudyArtifactKind.QUIZ and ("?" not in prompt or not answer):
        issues.append(_issue(artifact, "invalid_quiz", "quizzes need a question and answer"))
    elif artifact.kind is StudyArtifactKind.SUMMARY and _word_count(content or answer) < 8:
        issues.append(_issue(artifact, "invalid_summary", "summaries need supported content"))
    elif artifact.kind is StudyArtifactKind.MISCONCEPTION and not (content or answer):
        issues.append(
            _issue(artifact, "invalid_misconception", "misconceptions need a correction")
        )
    elif artifact.kind is StudyArtifactKind.CONCEPT_TAG and not artifact.concept_tags:
        issues.append(_issue(artifact, "invalid_concept_tag", "concept tags are required"))
    elif artifact.kind is StudyArtifactKind.PREREQUISITE and not artifact.prerequisite_tags:
        issues.append(_issue(artifact, "invalid_prerequisite", "prerequisite tags are required"))
    return tuple(issues)


def _source_span_issues(
    artifact: StudyArtifact,
    source_text_by_ref: Mapping[str, str],
) -> tuple[StudyArtifactIssue, ...]:
    if not artifact.source_spans:
        return (_issue(artifact, "missing_source_span", "at least one source span is required"),)
    issues: list[StudyArtifactIssue] = []
    for span in artifact.source_spans:
        if not span.source_ref.strip() or not span.text.strip():
            issues.append(_issue(artifact, "invalid_source_span", "source ref and text required"))
            continue
        offsets_invalid = False
        if (span.start is None) != (span.end is None):
            issues.append(_issue(artifact, "invalid_source_span", "span offsets must be paired"))
            offsets_invalid = True
        elif span.start is not None and span.end is not None:
            if span.start < 0 or span.end <= span.start:
                issues.append(_issue(artifact, "invalid_source_span", "span offsets are invalid"))
                offsets_invalid = True
        source_text = source_text_by_ref.get(span.source_ref)
        if source_text is None:
            if source_text_by_ref:
                issues.append(
                    _issue(
                        artifact,
                        "source_mismatch",
                        f"source ref is not available: {span.source_ref}",
                    )
                )
            continue
        if span.start is not None and span.end is not None and span.end > len(source_text):
            issues.append(_issue(artifact, "invalid_source_span", "span offsets are invalid"))
            offsets_invalid = True
        if offsets_invalid:
            continue
        if not _span_matches_source(span, source_text):
            issues.append(
                _issue(
                    artifact,
                    "source_mismatch",
                    f"source span text is not present in {span.source_ref}",
                )
            )
    return tuple(issues)


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
        tokens = _significant_tokens(_plain_study_text(text))
        if tokens and _support_rate(tokens, source_tokens) < 0.55:
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


def _source_tokens(artifact: StudyArtifact) -> set[str]:
    return {token for span in artifact.source_spans for token in _significant_tokens(span.text)}


def _significant_tokens(text: str) -> set[str]:
    return {
        token.casefold() for token in _TOKEN_RE.findall(text) if token.casefold() not in _STOPWORDS
    }


def _support_rate(tokens: set[str], source_tokens: set[str]) -> float:
    if not tokens:
        return 1.0
    return len(tokens & source_tokens) / len(tokens)


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


def _anki_card_fields(artifact: StudyArtifact) -> tuple[str, str]:
    if artifact.kind is StudyArtifactKind.CLOZE_CARD:
        return artifact.content or artifact.prompt, artifact.answer
    if artifact.kind in {StudyArtifactKind.FLASHCARD, StudyArtifactKind.QUIZ}:
        return artifact.prompt, artifact.answer or artifact.content
    return "", ""


def _anki_tags(artifact: StudyArtifact) -> tuple[str, ...]:
    source_tags = tuple(
        span.source_ref.split("#", maxsplit=1)[0] for span in artifact.source_spans
    )
    return artifact.concept_tags + artifact.prerequisite_tags + source_tags


def _anki_tag(text: str) -> str:
    tag = re.sub(r"[^A-Za-z0-9_]+", "_", text.strip().casefold()).strip("_")
    return tag or "source"


def _plain_study_text(text: str) -> str:
    return _CLOZE_RE.sub(lambda match: match.group("text"), text)


def _is_vague(text: str) -> bool:
    normalized = _normalized_for_match(text)
    if not normalized:
        return False
    if normalized in _VAGUE_PHRASES:
        return True
    tokens = _significant_tokens(text)
    return len(tokens) <= 1 and any(word in normalized for word in ("concept", "topic", "this"))


def _is_overly_broad(text: str) -> bool:
    return bool(_BROAD_RE.search(text)) or _word_count(text) > 180


def _word_count(text: str) -> int:
    return len(_TOKEN_RE.findall(text))


def _clean(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalized_for_match(text: str) -> str:
    return _clean(text).casefold()


def _issue(artifact: StudyArtifact, code: str, message: str) -> StudyArtifactIssue:
    return StudyArtifactIssue(artifact_id=artifact.artifact_id, code=code, message=message)
