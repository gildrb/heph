"""Benchmark grounded answer fixtures for citation and answer-shape quality.

Dataset format:

JSONL:
    {"id": "q1", "answer": "Dijkstra relaxes edges [E1].", "evidence": [...]}

JSON:
    {"cases": [{"id": "q1", "answer": "...", "evidence": [...]}]}

Each evidence item uses the citable evidence shape:

    {"id": "E1", "source": "materials/graphs.md", "chunk": 0, "text": "..."}

Cases may also include supported claims:

    {"text": "priority queue", "evidence_id": "E1"}

No-evidence cases may require explicit abstention:

    {"answer": "The sources do not contain that answer.", "require_abstention": true}

This benchmark is intentionally deterministic. It checks whether saved model
answers obey the grounding contract; semantic faithfulness judges can be added
later as another score alongside these hard gates.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaion.agent.citation import verify_citations
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence


class RawEvidence(TypedDict):
    id: str
    source: str
    chunk: int
    text: str
    score: NotRequired[float]
    kind: NotRequired[str]


class RawSupportedClaim(TypedDict):
    text: str
    evidence_id: str


class RawAnswerCase(TypedDict):
    answer: str
    evidence: NotRequired[list[RawEvidence]]
    domain: NotRequired[str]
    id: NotRequired[str]
    query: NotRequired[str]
    task: NotRequired[str]
    require_citations: NotRequired[bool]
    require_abstention: NotRequired[bool]
    required_label: NotRequired[str]
    expected_citations: NotRequired[list[str]]
    must_include: NotRequired[list[str]]
    must_not_include: NotRequired[list[str]]
    min_words: NotRequired[int]
    max_words: NotRequired[int]
    min_citation_count: NotRequired[int]
    min_distinct_sources: NotRequired[int]
    min_sampled_sources: NotRequired[int]
    min_bullet_count: NotRequired[int]
    min_cited_bullet_count: NotRequired[int]
    max_explicit_date_lines: NotRequired[int]
    required_sections: NotRequired[list[str]]
    evidence_coverage: NotRequired[dict[str, int]]
    supported_claims: NotRequired[list[RawSupportedClaim]]
    contradicted_claims: NotRequired[list[RawSupportedClaim]]
    allowed_citation_kinds: NotRequired[list[str]]


@dataclass(frozen=True, slots=True)
class SupportedClaim:
    text: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class AnswerCase:
    case_id: str
    answer: str
    evidence: TurnEvidence | None
    domain: str | None = None
    query: str = ""
    task: str | None = None
    require_citations: bool = True
    require_abstention: bool = False
    required_label: str | None = None
    expected_citations: tuple[str, ...] = ()
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()
    min_words: int = 0
    max_words: int = 0
    min_citation_count: int = 0
    min_distinct_sources: int = 0
    min_sampled_sources: int = 0
    min_bullet_count: int = 0
    min_cited_bullet_count: int = 0
    max_explicit_date_lines: int = 0
    required_sections: tuple[str, ...] = ()
    evidence_coverage: dict[str, int] | None = None
    supported_claims: tuple[SupportedClaim, ...] = ()
    contradicted_claims: tuple[SupportedClaim, ...] = ()
    evidence_kinds: tuple[tuple[str, str], ...] = ()
    allowed_citation_kinds: tuple[str, ...] = ("source",)


@dataclass(frozen=True, slots=True)
class AnswerCaseResult:
    case_id: str
    query: str
    answer_excerpt: str
    evidence_refs: tuple[str, ...]
    word_count: int
    citation_count: int
    distinct_cited_sources: int
    bullet_count: int
    cited_bullet_count: int
    evidence_coverage: dict[str, int] | None
    verified_citations: tuple[str, ...]
    unverified_citations: tuple[str, ...]
    missing_expected_citations: tuple[str, ...]
    missing_required_text: tuple[str, ...]
    forbidden_text_present: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    contradicted_claims: tuple[str, ...]
    invalid_citation_kinds: tuple[str, ...]
    shape_failures: tuple[str, ...]
    coverage_failures: tuple[str, ...]
    missing_citations: bool
    missing_abstention: bool
    missing_required_label: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class AnswerBenchmarkReport:
    cases: int
    domains: tuple[str, ...]
    tasks: tuple[str, ...]
    pass_rate: float
    citation_validity_rate: float
    citation_presence_rate: float
    expected_citation_rate: float
    citation_source_rate: float
    required_text_rate: float
    forbidden_text_rate: float
    supported_claim_rate: float
    contradiction_rate: float
    answer_shape_rate: float
    evidence_coverage_rate: float
    required_label_rate: float
    failures: tuple[str, ...]
    results: tuple[AnswerCaseResult, ...]


_EXPLICIT_DATE_RE = re.compile(
    r"\b(?:"
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
    r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|"
    r"\d{1,2}\.\s*[A-ZÀ-ÖØ-Þa-zà-öø-ÿ]{3,}\s+\d{4}|"
    r"(?:1[3-9]|2\d|3[01])\.\s*[A-ZÀ-ÖØ-Þa-zà-öø-ÿ]{3,}"
    r")\b"
)
_CHRONOLOGICAL_OVERVIEW_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s*|\d+[.)]\s*)?"
    r"(?:"
    r"(?:first|second|third|next|then|afterwards?|later|finally|subsequently)\b|"
    r"in\s+(?:the\s+)?(?:first|second|third|next|following|later)\b"
    r")",
    re.IGNORECASE,
)


def _as_string_list(value: object, field_name: str, case_idx: int) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"case {case_idx} field '{field_name}' must be a list")
    items = [item for item in value if isinstance(item, str) and item.strip()]
    if len(items) != len(value):
        raise ValueError(f"case {case_idx} field '{field_name}' must contain strings only")
    return items


def _as_bool(value: object, *, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _normalize_evidence_kind(value: object, *, field_name: str, case_idx: int) -> str:
    if value is None:
        return "source"
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"case {case_idx} field '{field_name}' must be a non-empty string")
    return re.sub(r"[^a-z0-9_-]+", "_", value.strip().casefold()).strip("_")


def _as_non_negative_int(value: object, field_name: str, case_idx: int) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"case {case_idx} field '{field_name}' must be a non-negative integer")
    return value


def _parse_supported_claims(raw_claims: object, case_idx: int) -> list[RawSupportedClaim]:
    if raw_claims is None:
        return []
    if not isinstance(raw_claims, list):
        raise TypeError(f"case {case_idx} field 'supported_claims' must be a list")

    claims: list[RawSupportedClaim] = []
    for claim_idx, raw_claim in enumerate(raw_claims, start=1):
        if not isinstance(raw_claim, dict):
            raise TypeError(f"case {case_idx} supported claim {claim_idx} must be an object")
        text = raw_claim.get("text")
        evidence_id = raw_claim.get("evidence_id")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"case {case_idx} supported claim {claim_idx} must include text")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError(
                f"case {case_idx} supported claim {claim_idx} must include evidence_id"
            )
        claims.append({"text": text.strip(), "evidence_id": evidence_id.strip().upper()})
    return claims


def _parse_evidence_coverage(value: object, case_idx: int) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f"case {case_idx} field 'evidence_coverage' must be an object")
    coverage: dict[str, int] = {}
    for field_name in ("evidence_blocks", "sampled_sources", "total_sources"):
        raw_value = value.get(field_name)
        if raw_value is None:
            continue
        if isinstance(raw_value, bool) or not isinstance(raw_value, int) or raw_value < 0:
            raise ValueError(
                f"case {case_idx} evidence_coverage field '{field_name}' must be "
                "a non-negative integer"
            )
        coverage[field_name] = raw_value
    return coverage or None


def _as_raw_cases(payload: object) -> list[RawAnswerCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("answer dataset must be a JSON list or an object with a 'cases' list")

    cases: list[RawAnswerCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        answer = raw.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError(f"case {idx} must include a non-empty string 'answer'")

        raw_case: RawAnswerCase = {"answer": answer}
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            raw_case["id"] = raw_id
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            raw_case["domain"] = raw_domain.strip()
        raw_query = raw.get("query")
        if isinstance(raw_query, str) and raw_query.strip():
            raw_case["query"] = raw_query
        raw_task = raw.get("task")
        if isinstance(raw_task, str) and raw_task.strip():
            raw_case["task"] = raw_task.strip()
        raw_require_citations = raw.get("require_citations")
        if isinstance(raw_require_citations, bool):
            raw_case["require_citations"] = raw_require_citations
        raw_require_abstention = raw.get("require_abstention")
        if isinstance(raw_require_abstention, bool):
            raw_case["require_abstention"] = raw_require_abstention
        raw_required_label = raw.get("required_label")
        if isinstance(raw_required_label, str) and raw_required_label.strip():
            raw_case["required_label"] = raw_required_label.strip()

        expected_citations = _as_string_list(
            raw.get("expected_citations"),
            "expected_citations",
            idx,
        )
        if expected_citations:
            raw_case["expected_citations"] = expected_citations
        must_include = _as_string_list(raw.get("must_include"), "must_include", idx)
        if must_include:
            raw_case["must_include"] = must_include
        must_not_include = _as_string_list(raw.get("must_not_include"), "must_not_include", idx)
        if must_not_include:
            raw_case["must_not_include"] = must_not_include
        min_words = _as_non_negative_int(raw.get("min_words"), "min_words", idx)
        if min_words:
            raw_case["min_words"] = min_words
        max_words = _as_non_negative_int(raw.get("max_words"), "max_words", idx)
        if max_words:
            raw_case["max_words"] = max_words
        min_citation_count = _as_non_negative_int(
            raw.get("min_citation_count"),
            "min_citation_count",
            idx,
        )
        if min_citation_count:
            raw_case["min_citation_count"] = min_citation_count
        min_distinct_sources = _as_non_negative_int(
            raw.get("min_distinct_sources"),
            "min_distinct_sources",
            idx,
        )
        if min_distinct_sources:
            raw_case["min_distinct_sources"] = min_distinct_sources
        min_sampled_sources = _as_non_negative_int(
            raw.get("min_sampled_sources"),
            "min_sampled_sources",
            idx,
        )
        if min_sampled_sources:
            raw_case["min_sampled_sources"] = min_sampled_sources
        min_bullet_count = _as_non_negative_int(
            raw.get("min_bullet_count"),
            "min_bullet_count",
            idx,
        )
        if min_bullet_count:
            raw_case["min_bullet_count"] = min_bullet_count
        min_cited_bullet_count = _as_non_negative_int(
            raw.get("min_cited_bullet_count"),
            "min_cited_bullet_count",
            idx,
        )
        if min_cited_bullet_count:
            raw_case["min_cited_bullet_count"] = min_cited_bullet_count
        max_explicit_date_lines = _as_non_negative_int(
            raw.get("max_explicit_date_lines"),
            "max_explicit_date_lines",
            idx,
        )
        if max_explicit_date_lines:
            raw_case["max_explicit_date_lines"] = max_explicit_date_lines
        required_sections = _as_string_list(raw.get("required_sections"), "required_sections", idx)
        if required_sections:
            raw_case["required_sections"] = required_sections
        supported_claims = _parse_supported_claims(raw.get("supported_claims"), idx)
        if supported_claims:
            raw_case["supported_claims"] = supported_claims
        contradicted_claims = _parse_supported_claims(raw.get("contradicted_claims"), idx)
        if contradicted_claims:
            raw_case["contradicted_claims"] = contradicted_claims
        evidence_coverage = _parse_evidence_coverage(raw.get("evidence_coverage"), idx)
        if evidence_coverage is not None:
            raw_case["evidence_coverage"] = evidence_coverage
        allowed_citation_kinds = _as_string_list(
            raw.get("allowed_citation_kinds"),
            "allowed_citation_kinds",
            idx,
        )
        if allowed_citation_kinds:
            raw_case["allowed_citation_kinds"] = allowed_citation_kinds

        raw_evidence = raw.get("evidence")
        if raw_evidence is not None:
            raw_case["evidence"] = _parse_raw_evidence_list(raw_evidence, idx)
        cases.append(raw_case)
    return cases


def _parse_raw_evidence_list(raw_evidence: object, case_idx: int) -> list[RawEvidence]:
    if not isinstance(raw_evidence, list):
        raise TypeError(f"case {case_idx} field 'evidence' must be a list")

    items: list[RawEvidence] = []
    for evidence_idx, raw_item in enumerate(raw_evidence, start=1):
        if not isinstance(raw_item, dict):
            raise TypeError(f"case {case_idx} evidence {evidence_idx} must be an object")
        evidence_id = raw_item.get("id")
        source = raw_item.get("source")
        chunk = raw_item.get("chunk")
        text = raw_item.get("text")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError(f"case {case_idx} evidence {evidence_idx} must include string 'id'")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(
                f"case {case_idx} evidence {evidence_idx} must include string 'source'"
            )
        if not isinstance(chunk, int) or chunk < 0:
            raise ValueError(f"case {case_idx} evidence {evidence_idx} must include chunk >= 0")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"case {case_idx} evidence {evidence_idx} must include string 'text'")
        raw_score = raw_item.get("score", 1.0)
        score = raw_score if isinstance(raw_score, int | float) else 1.0
        kind = _normalize_evidence_kind(
            raw_item.get("kind"),
            field_name="evidence.kind",
            case_idx=case_idx,
        )
        items.append(
            {
                "id": evidence_id,
                "source": source,
                "chunk": chunk,
                "text": text,
                "score": float(score),
                "kind": kind,
            }
        )
    return items


def _evidence_from_raw(raw_evidence: Sequence[RawEvidence]) -> TurnEvidence | None:
    if not raw_evidence:
        return None

    items: list[EvidenceChunk] = []
    for raw_item in raw_evidence:
        chunk = Chunk(
            text=raw_item["text"],
            source=raw_item["source"],
            index=raw_item["chunk"],
            char_start=0,
            char_end=len(raw_item["text"]),
        )
        items.append(
            EvidenceChunk(
                evidence_id=raw_item["id"].strip().upper(),
                chunk=chunk,
                score=float(raw_item.get("score", 1.0)),
                content=raw_item["text"],
            )
        )
    return TurnEvidence(tuple(items))


def _supported_claims_from_raw(
    raw_claims: Sequence[RawSupportedClaim],
) -> tuple[SupportedClaim, ...]:
    return tuple(
        SupportedClaim(text=claim["text"], evidence_id=claim["evidence_id"].strip().upper())
        for claim in raw_claims
    )


def _evidence_kinds_from_raw(raw_evidence: Sequence[RawEvidence]) -> tuple[tuple[str, str], ...]:
    return tuple((item["id"].strip().upper(), item.get("kind", "source")) for item in raw_evidence)


def _allowed_citation_kinds_from_raw(raw: RawAnswerCase, case_idx: int) -> tuple[str, ...]:
    return tuple(
        _normalize_evidence_kind(item, field_name="allowed_citation_kinds", case_idx=case_idx)
        for item in raw.get("allowed_citation_kinds", ["source"])
    )


def load_cases_from_payload(payload: object) -> list[AnswerCase]:
    """Build answer benchmark cases from an already-loaded JSON payload."""
    cases: list[AnswerCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        raw_evidence = raw.get("evidence", [])
        evidence = _evidence_from_raw(raw_evidence)
        default_require_citations = evidence is not None
        cases.append(
            AnswerCase(
                case_id=raw.get("id", f"case-{idx}"),
                answer=raw["answer"].strip(),
                evidence=evidence,
                domain=raw.get("domain"),
                query=raw.get("query", ""),
                task=raw.get("task"),
                require_citations=_as_bool(
                    raw.get("require_citations"),
                    default=default_require_citations,
                ),
                require_abstention=_as_bool(
                    raw.get("require_abstention"),
                    default=False,
                ),
                required_label=raw.get("required_label"),
                expected_citations=tuple(
                    citation.strip().upper() for citation in raw.get("expected_citations", [])
                ),
                must_include=tuple(raw.get("must_include", [])),
                must_not_include=tuple(raw.get("must_not_include", [])),
                min_words=raw.get("min_words", 0),
                max_words=raw.get("max_words", 0),
                min_citation_count=raw.get("min_citation_count", 0),
                min_distinct_sources=raw.get("min_distinct_sources", 0),
                min_sampled_sources=raw.get("min_sampled_sources", 0),
                min_bullet_count=raw.get("min_bullet_count", 0),
                min_cited_bullet_count=raw.get("min_cited_bullet_count", 0),
                max_explicit_date_lines=raw.get("max_explicit_date_lines", 0),
                required_sections=tuple(raw.get("required_sections", [])),
                evidence_coverage=raw.get("evidence_coverage"),
                supported_claims=_supported_claims_from_raw(raw.get("supported_claims", [])),
                contradicted_claims=_supported_claims_from_raw(raw.get("contradicted_claims", [])),
                evidence_kinds=_evidence_kinds_from_raw(raw_evidence),
                allowed_citation_kinds=_allowed_citation_kinds_from_raw(raw, idx),
            )
        )
    return cases


def load_cases(path: Path) -> list[AnswerCase]:
    """Load answer benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read answer benchmark dataset: {path}") from exc

    try:
        if path.suffix == ".jsonl":
            payload: object = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        else:
            payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid answer benchmark dataset JSON: {path}") from exc

    return load_cases_from_payload(payload)


def _contains_text(answer: str, needle: str) -> bool:
    return needle.casefold() in answer.casefold()


def _evidence_text_by_id(turn_evidence: TurnEvidence | None) -> dict[str, str]:
    if not turn_evidence:
        return {}
    return {item.evidence_id: item.content for item in turn_evidence.items}


def _unsupported_claims(
    case: AnswerCase,
    verified_citations: Sequence[str],
) -> tuple[str, ...]:
    evidence_by_id = _evidence_text_by_id(case.evidence)
    verified = set(verified_citations)
    unsupported: list[str] = []
    for claim in case.supported_claims:
        if claim.evidence_id not in verified:
            unsupported.append(f"{claim.text} [{claim.evidence_id}]")
            continue
        evidence_text = evidence_by_id.get(claim.evidence_id, "")
        if not _contains_text(case.answer, claim.text) or not _contains_text(
            evidence_text,
            claim.text,
        ):
            unsupported.append(f"{claim.text} [{claim.evidence_id}]")
    return tuple(unsupported)


def _evidence_kind_by_id(case: AnswerCase) -> dict[str, str]:
    kinds = dict(case.evidence_kinds)
    if case.evidence is not None:
        for item in case.evidence.items:
            kinds.setdefault(item.evidence_id, "source")
    return kinds


def _invalid_citation_kinds(
    case: AnswerCase,
    verified_citations: Sequence[str],
) -> tuple[str, ...]:
    allowed = set(case.allowed_citation_kinds or ("source",))
    evidence_kind_by_id = _evidence_kind_by_id(case)
    invalid: list[str] = []
    for citation in verified_citations:
        kind = evidence_kind_by_id.get(citation, "source")
        if kind not in allowed:
            invalid.append(f"{citation}:{kind}")
    return tuple(invalid)


def _contradicted_claims_present(case: AnswerCase) -> tuple[str, ...]:
    return tuple(
        f"{claim.text} [{claim.evidence_id}]"
        for claim in case.contradicted_claims
        if _contains_text(case.answer, claim.text)
    )


def _is_abstention(answer: str) -> bool:
    normalized = answer.casefold()
    abstention_markers = (
        "do not contain",
        "does not contain",
        "not contain",
        "no evidence",
        "not enough evidence",
        "insufficient evidence",
        "not in the provided",
        "not in the sources",
        "cannot determine",
        "cannot answer from",
        "not supported by",
        "nicht in den quellen",
        "keine hinweise",
        "nicht genug",
    )
    return any(marker in normalized for marker in abstention_markers)


def _has_required_label(answer: str, label: str | None) -> bool:
    if label is None:
        return True
    normalized_label = label.strip().rstrip(":").casefold()
    if not normalized_label:
        return True
    normalized_answer = answer.lstrip().casefold()
    return normalized_answer.startswith((f"{normalized_label}:", f"{normalized_label}-"))


def _excerpt(text: str, *, limit: int = 300) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _evidence_refs(turn_evidence: TurnEvidence | None) -> tuple[str, ...]:
    if not turn_evidence:
        return ()
    return tuple(
        f"{item.evidence_id}:{item.chunk.source}#chunk={item.chunk.index}"
        for item in turn_evidence.items
    )


def _word_count(text: str) -> int:
    return sum(1 for token in text.split() if token.strip())


def _bullet_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith(("- ", "* ", "+ ")))


def _cited_bullet_count(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if line.lstrip().startswith(("- ", "* ", "+ "))
        and verify_citations(line, None).has_citations
    )


def _explicit_date_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if _EXPLICIT_DATE_RE.search(line))


def _chronological_overview_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if _CHRONOLOGICAL_OVERVIEW_LINE_RE.search(line))


def _has_required_section(answer: str, section: str) -> bool:
    normalized_section = section.strip().rstrip(":").casefold()
    if not normalized_section:
        return True
    for line in answer.splitlines():
        normalized_line = line.strip().casefold()
        for label in ("correct:", "partial:", "wrong:"):
            if normalized_line.startswith(label):
                normalized_line = normalized_line.removeprefix(label).lstrip()
                break
        if normalized_line.startswith(
            (
                f"{normalized_section}:",
                f"{normalized_section} -",
                f"{normalized_section}-",
            )
        ):
            return True
    return False


def _distinct_verified_evidence_sources(
    turn_evidence: TurnEvidence | None,
    verified_citations: Sequence[str],
) -> int:
    if not turn_evidence:
        return 0
    verified = set(verified_citations)
    return len({item.chunk.source for item in turn_evidence.items if item.evidence_id in verified})


def _shape_failures(
    case: AnswerCase,
    *,
    citation_count: int,
    verified_citations: Sequence[str],
) -> tuple[str, ...]:
    failures: list[str] = []
    word_count = _word_count(case.answer)
    if case.min_words and word_count < case.min_words:
        failures.append(f"words {word_count} below {case.min_words}")
    if case.max_words and word_count > case.max_words:
        failures.append(f"words {word_count} above {case.max_words}")
    if case.min_citation_count and citation_count < case.min_citation_count:
        failures.append(f"citations {citation_count} below {case.min_citation_count}")
    distinct_sources = _distinct_verified_evidence_sources(case.evidence, verified_citations)
    if case.min_distinct_sources and distinct_sources < case.min_distinct_sources:
        failures.append(f"distinct sources {distinct_sources} below {case.min_distinct_sources}")
    bullet_count = _bullet_count(case.answer)
    if case.min_bullet_count and bullet_count < case.min_bullet_count:
        failures.append(f"bullets {bullet_count} below {case.min_bullet_count}")
    cited_bullet_count = _cited_bullet_count(case.answer)
    if case.min_cited_bullet_count and cited_bullet_count < case.min_cited_bullet_count:
        failures.append(f"cited bullets {cited_bullet_count} below {case.min_cited_bullet_count}")
    explicit_date_lines = _explicit_date_line_count(case.answer)
    if case.max_explicit_date_lines and explicit_date_lines > case.max_explicit_date_lines:
        failures.append(
            f"explicit date lines {explicit_date_lines} above {case.max_explicit_date_lines}"
        )
    chronological_lines = _chronological_overview_line_count(case.answer)
    if case.task == "material-overview" and chronological_lines > 1:
        failures.append(f"chronological overview lines {chronological_lines} above 1")
    missing_sections = [
        section
        for section in case.required_sections
        if not _has_required_section(case.answer, section)
    ]
    if missing_sections:
        failures.append("missing sections: " + ", ".join(missing_sections))
    return tuple(failures)


def _coverage_failures(case: AnswerCase) -> tuple[str, ...]:
    if not case.min_sampled_sources:
        return ()
    sampled_sources = 0
    if case.evidence_coverage is not None:
        sampled_sources = case.evidence_coverage.get("sampled_sources", 0)
    elif case.evidence is not None:
        sampled_sources = len({item.source for item in case.evidence.items})
    if sampled_sources < case.min_sampled_sources:
        return (f"sampled sources {sampled_sources} below {case.min_sampled_sources}",)
    return ()


def evaluate_case(case: AnswerCase) -> AnswerCaseResult:
    """Evaluate one answer fixture."""
    verification = verify_citations(case.answer, case.evidence)
    verified = tuple(verification.verified)
    unverified = tuple(verification.unverified)
    missing_expected = tuple(
        citation for citation in case.expected_citations if citation not in verified
    )
    missing_required_text = tuple(
        phrase for phrase in case.must_include if not _contains_text(case.answer, phrase)
    )
    forbidden_text_present = tuple(
        phrase for phrase in case.must_not_include if _contains_text(case.answer, phrase)
    )
    unsupported_claims = _unsupported_claims(case, verified)
    contradicted_claims = _contradicted_claims_present(case)
    invalid_citation_kinds = _invalid_citation_kinds(case, verified)
    word_count = _word_count(case.answer)
    distinct_cited_sources = _distinct_verified_evidence_sources(case.evidence, verified)
    bullet_count = _bullet_count(case.answer)
    cited_bullet_count = _cited_bullet_count(case.answer)
    shape_failures = _shape_failures(
        case,
        citation_count=verification.citation_count,
        verified_citations=verified,
    )
    coverage_failures = _coverage_failures(case)
    missing_citations = (
        case.require_citations and bool(case.evidence) and not verification.has_citations
    )
    missing_abstention = case.require_abstention and not _is_abstention(case.answer)
    missing_required_label = not _has_required_label(case.answer, case.required_label)
    passed = not (
        unverified
        or missing_expected
        or missing_required_text
        or forbidden_text_present
        or unsupported_claims
        or contradicted_claims
        or invalid_citation_kinds
        or shape_failures
        or coverage_failures
        or missing_citations
        or missing_abstention
        or missing_required_label
    )
    return AnswerCaseResult(
        case_id=case.case_id,
        query=case.query,
        answer_excerpt=_excerpt(case.answer),
        evidence_refs=_evidence_refs(case.evidence),
        word_count=word_count,
        citation_count=verification.citation_count,
        distinct_cited_sources=distinct_cited_sources,
        bullet_count=bullet_count,
        cited_bullet_count=cited_bullet_count,
        evidence_coverage=case.evidence_coverage,
        verified_citations=verified,
        unverified_citations=unverified,
        missing_expected_citations=missing_expected,
        missing_required_text=missing_required_text,
        forbidden_text_present=forbidden_text_present,
        unsupported_claims=unsupported_claims,
        contradicted_claims=contradicted_claims,
        invalid_citation_kinds=invalid_citation_kinds,
        shape_failures=shape_failures,
        coverage_failures=coverage_failures,
        missing_citations=missing_citations,
        missing_abstention=missing_abstention,
        missing_required_label=missing_required_label,
        passed=passed,
    )


def _rate(total: int, passed: int) -> float:
    if total <= 0:
        return 0.0
    return passed / total


def run_benchmark(cases: Sequence[AnswerCase]) -> AnswerBenchmarkReport:
    """Run grounded answer benchmark cases and return aggregate metrics."""
    if not cases:
        raise ValueError("answer benchmark dataset does not contain any cases")

    results = tuple(evaluate_case(case) for case in cases)
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    citation_valid = sum(1 for result in results if not result.unverified_citations)
    citation_present = sum(1 for result in results if not result.missing_citations)
    expected_citations = sum(1 for result in results if not result.missing_expected_citations)
    citation_sources = sum(1 for result in results if not result.invalid_citation_kinds)
    required_text = sum(1 for result in results if not result.missing_required_text)
    forbidden_text = sum(1 for result in results if not result.forbidden_text_present)
    supported_claims = sum(1 for result in results if not result.unsupported_claims)
    contradictions = sum(1 for result in results if not result.contradicted_claims)
    answer_shape = sum(1 for result in results if not result.shape_failures)
    evidence_coverage = sum(1 for result in results if not result.coverage_failures)
    required_label = sum(1 for result in results if not result.missing_required_label)

    return AnswerBenchmarkReport(
        cases=total,
        domains=tuple(sorted({case.domain for case in cases if case.domain})),
        tasks=tuple(sorted({case.task for case in cases if case.task})),
        pass_rate=_rate(total, passed),
        citation_validity_rate=_rate(total, citation_valid),
        citation_presence_rate=_rate(total, citation_present),
        expected_citation_rate=_rate(total, expected_citations),
        citation_source_rate=_rate(total, citation_sources),
        required_text_rate=_rate(total, required_text),
        forbidden_text_rate=_rate(total, forbidden_text),
        supported_claim_rate=_rate(total, supported_claims),
        contradiction_rate=_rate(total, contradictions),
        answer_shape_rate=_rate(total, answer_shape),
        evidence_coverage_rate=_rate(total, evidence_coverage),
        required_label_rate=_rate(total, required_label),
        failures=tuple(result.case_id for result in results if not result.passed),
        results=results,
    )


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_text_report(report: AnswerBenchmarkReport) -> None:
    """Print a compact human-readable report."""
    print(f"Answer benchmark: {report.cases} cases")
    if report.domains:
        print(f"domains={len(report.domains)} ({', '.join(report.domains)})")
    if report.tasks:
        print(f"tasks={len(report.tasks)} ({', '.join(report.tasks)})")
    print(f"pass_rate={_format_percent(report.pass_rate)}")
    print(f"citation_validity={_format_percent(report.citation_validity_rate)}")
    print(f"citation_presence={_format_percent(report.citation_presence_rate)}")
    print(f"expected_citations={_format_percent(report.expected_citation_rate)}")
    print(f"citation_sources={_format_percent(report.citation_source_rate)}")
    print(f"required_text={_format_percent(report.required_text_rate)}")
    print(f"forbidden_text={_format_percent(report.forbidden_text_rate)}")
    print(f"supported_claims={_format_percent(report.supported_claim_rate)}")
    print(f"contradictions={_format_percent(report.contradiction_rate)}")
    print(f"answer_shape={_format_percent(report.answer_shape_rate)}")
    print(f"evidence_coverage={_format_percent(report.evidence_coverage_rate)}")
    print(f"required_label={_format_percent(report.required_label_rate)}")
    if report.failures:
        print(f"failures={', '.join(report.failures)}")
        for result in report.results:
            if not result.passed:
                print(f"  - {result.case_id}: {_failure_reasons(result)}")


def _failure_reasons(result: AnswerCaseResult) -> str:
    reasons: list[str] = []
    if result.unverified_citations:
        reasons.append("unverified citations: " + ", ".join(result.unverified_citations))
    if result.missing_expected_citations:
        reasons.append(
            "missing expected citations: " + ", ".join(result.missing_expected_citations)
        )
    if result.missing_required_text:
        reasons.append("missing required text: " + ", ".join(result.missing_required_text))
    if result.forbidden_text_present:
        reasons.append("forbidden text: " + ", ".join(result.forbidden_text_present))
    if result.unsupported_claims:
        reasons.append("unsupported claims: " + ", ".join(result.unsupported_claims))
    if result.contradicted_claims:
        reasons.append("contradicted claims: " + ", ".join(result.contradicted_claims))
    if result.invalid_citation_kinds:
        reasons.append("invalid citation kinds: " + ", ".join(result.invalid_citation_kinds))
    if result.shape_failures:
        reasons.append("answer shape: " + "; ".join(result.shape_failures))
    if result.coverage_failures:
        reasons.append("evidence coverage: " + "; ".join(result.coverage_failures))
    if result.missing_citations:
        reasons.append("missing citations")
    if result.missing_abstention:
        reasons.append("missing abstention")
    if result.missing_required_label:
        reasons.append("missing required label")
    return "; ".join(reasons) if reasons else "failed"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="JSON or JSONL grounded answer cases")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    parser.add_argument("--min-pass-rate", type=float, default=0.0)
    parser.add_argument("--min-citation-validity", type=float, default=0.0)
    parser.add_argument("--min-citation-presence", type=float, default=0.0)
    parser.add_argument("--min-expected-citations", type=float, default=0.0)
    parser.add_argument("--min-citation-sources", type=float, default=0.0)
    parser.add_argument("--min-required-text", type=float, default=0.0)
    parser.add_argument("--min-forbidden-text", type=float, default=0.0)
    parser.add_argument("--min-supported-claims", type=float, default=0.0)
    parser.add_argument("--min-contradiction-rate", type=float, default=0.0)
    parser.add_argument("--min-answer-shape", type=float, default=0.0)
    parser.add_argument("--min-evidence-coverage", type=float, default=0.0)
    parser.add_argument("--min-required-label", type=float, default=0.0)
    return parser


def _validate_rate(value: float, label: str, parser: argparse.ArgumentParser) -> None:
    if not 0 <= value <= 1:
        parser.error(f"{label} must be between 0 and 1")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dataset = cast("Path", args.dataset).expanduser().resolve()
    min_pass_rate = cast("float", args.min_pass_rate)
    min_citation_validity = cast("float", args.min_citation_validity)
    min_citation_presence = cast("float", args.min_citation_presence)
    min_expected_citations = cast("float", args.min_expected_citations)
    min_citation_sources = cast("float", args.min_citation_sources)
    min_required_text = cast("float", args.min_required_text)
    min_forbidden_text = cast("float", args.min_forbidden_text)
    min_supported_claims = cast("float", args.min_supported_claims)
    min_contradiction_rate = cast("float", args.min_contradiction_rate)
    min_answer_shape = cast("float", args.min_answer_shape)
    min_evidence_coverage = cast("float", args.min_evidence_coverage)
    min_required_label = cast("float", args.min_required_label)

    _validate_rate(min_pass_rate, "--min-pass-rate", parser)
    _validate_rate(min_citation_validity, "--min-citation-validity", parser)
    _validate_rate(min_citation_presence, "--min-citation-presence", parser)
    _validate_rate(min_expected_citations, "--min-expected-citations", parser)
    _validate_rate(min_citation_sources, "--min-citation-sources", parser)
    _validate_rate(min_required_text, "--min-required-text", parser)
    _validate_rate(min_forbidden_text, "--min-forbidden-text", parser)
    _validate_rate(min_supported_claims, "--min-supported-claims", parser)
    _validate_rate(min_contradiction_rate, "--min-contradiction-rate", parser)
    _validate_rate(min_answer_shape, "--min-answer-shape", parser)
    _validate_rate(min_evidence_coverage, "--min-evidence-coverage", parser)
    _validate_rate(min_required_label, "--min-required-label", parser)

    try:
        report = run_benchmark(load_cases(dataset))
    except (TypeError, ValueError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2

    if cast("bool", args.json):
        print(json.dumps(asdict(report), indent=2))
    else:
        print_text_report(report)

    if (
        report.pass_rate < min_pass_rate
        or report.citation_validity_rate < min_citation_validity
        or report.citation_presence_rate < min_citation_presence
        or report.expected_citation_rate < min_expected_citations
        or report.citation_source_rate < min_citation_sources
        or report.required_text_rate < min_required_text
        or report.forbidden_text_rate < min_forbidden_text
        or report.supported_claim_rate < min_supported_claims
        or report.contradiction_rate < min_contradiction_rate
        or report.answer_shape_rate < min_answer_shape
        or report.evidence_coverage_rate < min_evidence_coverage
        or report.required_label_rate < min_required_label
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
