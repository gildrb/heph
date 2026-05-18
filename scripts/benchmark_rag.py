"""Benchmark Hephaistos RAG retrieval against labelled cases.

Dataset format:

JSONL:
    {"id": "q1", "query": "What is Dijkstra?", "expected": ["materials/graphs.md#chunk=0"]}

JSON:
    {"cases": [{"id": "q1", "query": "...", "expected": ["materials/graphs.md"]}]}

Expected references may be either exact chunk references
(``materials/foo.md#chunk=2``) or source-level references (``materials/foo.md``).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from hephaistos.rag import (
    EvidenceReference,
    RetrievalMode,
    ScoredChunk,
    TransformStrategy,
    load_or_build,
    retrieve,
)
from hephaistos.rag.hybrid import (
    DEFAULT_PSEUDO_FEEDBACK_DOCS,
    DEFAULT_PSEUDO_FEEDBACK_TERMS,
    DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
)

_DEFAULT_TOP_K = 5
_DEFAULT_MIN_SCORE = 0.1


class RawCase(TypedDict):
    query: str
    expected: list[str]
    relevance_grades: NotRequired[dict[str, float]]
    forbidden_before_expected: NotRequired[list[str]]
    domain: NotRequired[str]
    task: NotRequired[str]
    id: NotRequired[str]
    top_k: NotRequired[int]


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    query: str
    expected: tuple[str, ...]
    relevance_grades: dict[str, float] = field(default_factory=dict)
    forbidden_before_expected: tuple[str, ...] = ()
    domain: str | None = None
    task: str | None = None
    top_k: int | None = None


@dataclass(frozen=True, slots=True)
class RetrievedChunkResult:
    ref: str
    score: float
    text_excerpt: str


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    query: str
    expected: tuple[str, ...]
    relevance_grades: dict[str, float]
    forbidden_before_expected: tuple[str, ...]
    retrieved: tuple[str, ...]
    retrieved_chunks: tuple[RetrievedChunkResult, ...]
    hit: bool
    rank: int | None
    first_forbidden_rank: int | None
    forbidden_before_expected_ok: bool
    recall: float
    precision_at_k: float
    average_precision_at_k: float
    ndcg_at_k: float
    graded_ndcg_at_k: float
    elapsed_ms: float


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    armory_path: str
    cases: int
    domains: tuple[str, ...]
    tasks: tuple[str, ...]
    top_k: int
    min_score: float
    retrieval_mode: str
    candidate_multiplier: int
    hybrid_sparse_weight: float
    hybrid_dense_weight: float
    pseudo_feedback_docs: int
    pseudo_feedback_terms: int
    pseudo_feedback_weight: float
    retriever_backends: tuple[str, ...]
    transform_strategy: str
    embedding_model: str | None
    embedding_query_prefix: str
    embedding_document_prefix: str
    rerank_model: str | None
    hit_rate: float
    mean_reciprocal_rank: float
    mean_expected_recall: float
    mean_precision_at_k: float
    mean_average_precision_at_k: float
    mean_ndcg_at_k: float
    mean_graded_ndcg_at_k: float
    forbidden_before_expected_avoidance: float
    mean_latency_ms: float
    misses: tuple[str, ...]
    forbidden_before_expected_failures: tuple[str, ...]
    results: tuple[CaseResult, ...]


def _as_raw_cases(payload: object) -> list[RawCase]:
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("benchmark dataset must be a JSON list or an object with a 'cases' list")

    cases: list[RawCase] = []
    for idx, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise TypeError(f"case {idx} must be an object")
        query = raw.get("query")
        expected = raw.get("expected")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"case {idx} must include a non-empty string 'query'")
        if not isinstance(expected, list) or not expected:
            raise ValueError(f"case {idx} must include a non-empty list 'expected'")
        expected_refs = [item for item in expected if isinstance(item, str) and item.strip()]
        if len(expected_refs) != len(expected):
            raise ValueError(f"case {idx} expected references must all be non-empty strings")
        raw_case: RawCase = {"query": query, "expected": expected_refs}
        forbidden = raw.get("forbidden_before_expected", [])
        if not isinstance(forbidden, list):
            raise TypeError(f"case {idx} forbidden_before_expected must be a list")
        forbidden_refs = [item for item in forbidden if isinstance(item, str) and item.strip()]
        if len(forbidden_refs) != len(forbidden):
            raise ValueError(
                f"case {idx} forbidden_before_expected references must all be non-empty strings"
            )
        if forbidden_refs:
            raw_case["forbidden_before_expected"] = forbidden_refs
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            raw_case["id"] = raw_id
        raw_domain = raw.get("domain")
        if isinstance(raw_domain, str) and raw_domain.strip():
            raw_case["domain"] = raw_domain.strip()
        raw_task = raw.get("task")
        if isinstance(raw_task, str) and raw_task.strip():
            raw_case["task"] = raw_task.strip()
        raw_top_k = raw.get("top_k")
        if isinstance(raw_top_k, int):
            raw_case["top_k"] = raw_top_k
        relevance_grades = _extract_relevance_grades(raw, expected_refs)
        if relevance_grades:
            raw_case["relevance_grades"] = relevance_grades
        cases.append(raw_case)
    return cases


def _extract_relevance_grades(
    raw: dict[object, object],
    expected_refs: Sequence[str],
) -> dict[str, float]:
    expected_set = set(expected_refs)
    grades: dict[str, float] = {}
    raw_grades = raw.get("relevance_grades")
    if isinstance(raw_grades, dict):
        for raw_ref, raw_grade in raw_grades.items():
            if not isinstance(raw_ref, str) or raw_ref not in expected_set:
                continue
            grade = _positive_float_or_none(raw_grade)
            if grade is not None:
                grades[raw_ref] = grade

    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        return grades
    judgments = metadata.get("relevance_judgments")
    if not isinstance(judgments, list):
        return grades
    for judgment in judgments:
        if not isinstance(judgment, dict):
            continue
        source_id = judgment.get("source_id")
        if not isinstance(source_id, str) or source_id not in expected_set:
            continue
        grade = _positive_float_or_none(judgment.get("grade"))
        if grade is not None:
            grades[source_id] = grade
    return grades


def _positive_float_or_none(value: object) -> float | None:
    if not isinstance(value, int | float):
        return None
    grade = float(value)
    if grade <= 0:
        return None
    return grade


def load_cases(path: Path) -> list[BenchmarkCase]:
    """Load benchmark cases from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read benchmark dataset: {path}") from exc

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
        raise ValueError(f"invalid benchmark dataset JSON: {path}") from exc

    cases: list[BenchmarkCase] = []
    for idx, raw in enumerate(_as_raw_cases(payload), start=1):
        cases.append(
            BenchmarkCase(
                case_id=raw.get("id", f"case-{idx}"),
                query=raw["query"].strip(),
                expected=tuple(ref.strip() for ref in raw["expected"]),
                relevance_grades={
                    ref.strip(): float(grade)
                    for ref, grade in raw.get("relevance_grades", {}).items()
                },
                forbidden_before_expected=tuple(
                    ref.strip() for ref in raw.get("forbidden_before_expected", [])
                ),
                domain=raw.get("domain"),
                task=raw.get("task"),
                top_k=raw.get("top_k"),
            )
        )
    return cases


def _result_ref(scored_chunk: ScoredChunk) -> str:
    return EvidenceReference(scored_chunk.chunk.source, scored_chunk.chunk.index).render()


def _excerpt(text: str, *, limit: int = 240) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _retrieved_chunk_result(scored_chunk: ScoredChunk) -> RetrievedChunkResult:
    return RetrievedChunkResult(
        ref=_result_ref(scored_chunk),
        score=scored_chunk.score,
        text_excerpt=_excerpt(scored_chunk.chunk.text),
    )


def _matches_expected(expected_ref: str, scored_chunk: ScoredChunk) -> bool:
    parsed = EvidenceReference.parse(expected_ref)
    if parsed is None:
        return scored_chunk.chunk.source == expected_ref
    return (
        scored_chunk.chunk.source == parsed.source
        and scored_chunk.chunk.index == parsed.chunk_index
    )


def _expected_was_found(expected_ref: str, scored_chunks: Sequence[ScoredChunk]) -> bool:
    return any(_matches_expected(expected_ref, scored_chunk) for scored_chunk in scored_chunks)


def _first_match_rank(
    expected: Sequence[str],
    scored_chunks: Sequence[ScoredChunk],
) -> int | None:
    for rank, scored_chunk in enumerate(scored_chunks, start=1):
        if any(_matches_expected(expected_ref, scored_chunk) for expected_ref in expected):
            return rank
    return None


def _first_forbidden_rank(
    forbidden: Sequence[str],
    scored_chunks: Sequence[ScoredChunk],
) -> int | None:
    if not forbidden:
        return None
    for rank, scored_chunk in enumerate(scored_chunks, start=1):
        if any(_matches_expected(forbidden_ref, scored_chunk) for forbidden_ref in forbidden):
            return rank
    return None


def _forbidden_before_expected_ok(
    expected_rank: int | None,
    forbidden_rank: int | None,
) -> bool:
    if forbidden_rank is None:
        return True
    if expected_rank is None:
        return False
    return expected_rank < forbidden_rank


@dataclass(frozen=True, slots=True)
class _RankMetrics:
    relevant_found: int
    precision_at_k: float
    recall_at_k: float
    average_precision_at_k: float
    ndcg_at_k: float
    graded_ndcg_at_k: float


def _rank_metrics(
    expected: Sequence[str],
    scored_chunks: Sequence[ScoredChunk],
    *,
    top_k: int,
    relevance_grades: Mapping[str, float] | None = None,
) -> _RankMetrics:
    matched_expected_indices: set[int] = set()
    relevant_by_rank: list[int] = []
    graded_relevance_by_rank: list[float] = []
    grades = relevance_grades or {}

    for scored_chunk in scored_chunks[:top_k]:
        match_index = next(
            (
                index
                for index, expected_ref in enumerate(expected)
                if index not in matched_expected_indices
                and _matches_expected(expected_ref, scored_chunk)
            ),
            None,
        )
        if match_index is None:
            relevant_by_rank.append(0)
            graded_relevance_by_rank.append(0.0)
            continue
        matched_expected_indices.add(match_index)
        relevant_by_rank.append(1)
        expected_ref = expected[match_index]
        graded_relevance_by_rank.append(float(grades.get(expected_ref, 1.0)))

    relevant_found = sum(relevant_by_rank)
    ideal_relevant_at_k = min(len(expected), top_k)
    precision_at_k = relevant_found / top_k
    recall_at_k = relevant_found / len(expected)

    precision_sum = 0.0
    cumulative_relevant = 0
    for rank, is_relevant in enumerate(relevant_by_rank, start=1):
        if not is_relevant:
            continue
        cumulative_relevant += 1
        precision_sum += cumulative_relevant / rank
    average_precision_at_k = precision_sum / ideal_relevant_at_k if ideal_relevant_at_k else 0.0

    dcg = sum(
        is_relevant / math.log2(rank + 1)
        for rank, is_relevant in enumerate(relevant_by_rank, start=1)
        if is_relevant
    )
    idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_relevant_at_k + 1))
    ndcg_at_k = dcg / idcg if idcg else 0.0
    ideal_grades = sorted(
        (float(grades.get(expected_ref, 1.0)) for expected_ref in expected),
        reverse=True,
    )[:top_k]
    graded_dcg = sum(
        grade / math.log2(rank + 1)
        for rank, grade in enumerate(graded_relevance_by_rank, start=1)
        if grade > 0
    )
    graded_idcg = sum(
        grade / math.log2(rank + 1)
        for rank, grade in enumerate(ideal_grades, start=1)
        if grade > 0
    )
    graded_ndcg_at_k = graded_dcg / graded_idcg if graded_idcg else 0.0

    return _RankMetrics(
        relevant_found=relevant_found,
        precision_at_k=precision_at_k,
        recall_at_k=recall_at_k,
        average_precision_at_k=average_precision_at_k,
        ndcg_at_k=ndcg_at_k,
        graded_ndcg_at_k=graded_ndcg_at_k,
    )


def run_benchmark(
    armory_path: Path,
    cases: Sequence[BenchmarkCase],
    *,
    top_k: int = _DEFAULT_TOP_K,
    min_score: float = _DEFAULT_MIN_SCORE,
    transform_strategy: TransformStrategy = TransformStrategy.IDENTITY,
    retrieval_mode: RetrievalMode = RetrievalMode.AUTO,
    candidate_multiplier: int = 2,
    diversify_sources: bool = True,
    use_case_top_k: bool = True,
    embed_model: str | None = None,
    embed_query_prefix: str = "",
    embed_document_prefix: str = "",
    rerank_model: str | None = None,
    hybrid_sparse_weight: float = 1.0,
    hybrid_dense_weight: float = 1.0,
    pseudo_feedback_docs: int = DEFAULT_PSEUDO_FEEDBACK_DOCS,
    pseudo_feedback_terms: int = DEFAULT_PSEUDO_FEEDBACK_TERMS,
    pseudo_feedback_weight: float = DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
) -> BenchmarkReport:
    """Run retrieval benchmark cases and return aggregate metrics."""
    if not cases:
        raise ValueError("benchmark dataset does not contain any cases")
    index = load_or_build(armory_path)
    results: list[CaseResult] = []

    for case in cases:
        case_top_k = case.top_k if use_case_top_k and case.top_k is not None else top_k
        started = time.perf_counter()
        scored_chunks = retrieve(
            case.query,
            index,
            top_k=case_top_k,
            min_score=min_score,
            transform_strategy=transform_strategy,
            retrieval_mode=retrieval_mode,
            candidate_multiplier=candidate_multiplier,
            diversify_sources=diversify_sources,
            embed_model=embed_model,
            embed_query_prefix=embed_query_prefix,
            embed_document_prefix=embed_document_prefix,
            rerank_model=rerank_model,
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
            pseudo_feedback_docs=pseudo_feedback_docs,
            pseudo_feedback_terms=pseudo_feedback_terms,
            pseudo_feedback_weight=pseudo_feedback_weight,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        rank = _first_match_rank(case.expected, scored_chunks)
        first_forbidden_rank = _first_forbidden_rank(
            case.forbidden_before_expected,
            scored_chunks,
        )
        forbidden_before_expected_ok = _forbidden_before_expected_ok(rank, first_forbidden_rank)
        rank_metrics = _rank_metrics(
            case.expected,
            scored_chunks,
            top_k=case_top_k,
            relevance_grades=case.relevance_grades,
        )
        results.append(
            CaseResult(
                case_id=case.case_id,
                query=case.query,
                expected=case.expected,
                relevance_grades=case.relevance_grades,
                forbidden_before_expected=case.forbidden_before_expected,
                retrieved=tuple(_result_ref(scored_chunk) for scored_chunk in scored_chunks),
                retrieved_chunks=tuple(
                    _retrieved_chunk_result(scored_chunk) for scored_chunk in scored_chunks
                ),
                hit=rank is not None,
                rank=rank,
                first_forbidden_rank=first_forbidden_rank,
                forbidden_before_expected_ok=forbidden_before_expected_ok,
                recall=rank_metrics.recall_at_k,
                precision_at_k=rank_metrics.precision_at_k,
                average_precision_at_k=rank_metrics.average_precision_at_k,
                ndcg_at_k=rank_metrics.ndcg_at_k,
                graded_ndcg_at_k=rank_metrics.graded_ndcg_at_k,
                elapsed_ms=elapsed_ms,
            )
        )

    hit_count = sum(1 for result in results if result.hit)
    reciprocal_rank_sum = sum(1 / result.rank for result in results if result.rank is not None)
    recall_sum = sum(result.recall for result in results)
    precision_sum = sum(result.precision_at_k for result in results)
    average_precision_sum = sum(result.average_precision_at_k for result in results)
    ndcg_sum = sum(result.ndcg_at_k for result in results)
    graded_ndcg_sum = sum(result.graded_ndcg_at_k for result in results)
    forbidden_case_count = sum(1 for result in results if result.forbidden_before_expected)
    forbidden_ok_count = sum(
        1
        for result in results
        if result.forbidden_before_expected and result.forbidden_before_expected_ok
    )
    latency_sum = sum(result.elapsed_ms for result in results)
    total = len(results)
    retriever_backends = index.retriever_backend_names
    forbidden_avoidance = (
        forbidden_ok_count / forbidden_case_count if forbidden_case_count else 1.0
    )
    return BenchmarkReport(
        armory_path=str(armory_path),
        cases=total,
        domains=tuple(sorted({case.domain for case in cases if case.domain})),
        tasks=tuple(sorted({case.task for case in cases if case.task})),
        top_k=top_k,
        min_score=min_score,
        retrieval_mode=retrieval_mode.value,
        candidate_multiplier=max(1, candidate_multiplier),
        hybrid_sparse_weight=max(0.0, hybrid_sparse_weight),
        hybrid_dense_weight=max(0.0, hybrid_dense_weight),
        pseudo_feedback_docs=max(1, pseudo_feedback_docs),
        pseudo_feedback_terms=max(1, pseudo_feedback_terms),
        pseudo_feedback_weight=max(0.0, pseudo_feedback_weight),
        retriever_backends=retriever_backends,
        transform_strategy=transform_strategy.value,
        embedding_model=embed_model,
        embedding_query_prefix=embed_query_prefix,
        embedding_document_prefix=embed_document_prefix,
        rerank_model=rerank_model,
        hit_rate=hit_count / total,
        mean_reciprocal_rank=reciprocal_rank_sum / total,
        mean_expected_recall=recall_sum / total,
        mean_precision_at_k=precision_sum / total,
        mean_average_precision_at_k=average_precision_sum / total,
        mean_ndcg_at_k=ndcg_sum / total,
        mean_graded_ndcg_at_k=graded_ndcg_sum / total,
        forbidden_before_expected_avoidance=forbidden_avoidance,
        mean_latency_ms=latency_sum / total,
        misses=tuple(result.case_id for result in results if not result.hit),
        forbidden_before_expected_failures=tuple(
            result.case_id
            for result in results
            if result.forbidden_before_expected and not result.forbidden_before_expected_ok
        ),
        results=tuple(results),
    )


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_text_report(report: BenchmarkReport) -> None:
    """Print a compact human-readable report."""
    print(f"RAG benchmark: {report.cases} cases against {report.armory_path}")
    if report.domains:
        print(f"domains={len(report.domains)} ({', '.join(report.domains)})")
    if report.tasks:
        print(f"tasks={len(report.tasks)} ({', '.join(report.tasks)})")
    print(
        f"strategy={report.transform_strategy} retrieval_mode={report.retrieval_mode} "
        f"candidate_multiplier={report.candidate_multiplier} top_k={report.top_k} "
        f"min_score={report.min_score}"
    )
    print(
        f"hybrid_sparse_weight={report.hybrid_sparse_weight:.3f} "
        f"hybrid_dense_weight={report.hybrid_dense_weight:.3f}"
    )
    if report.retrieval_mode == RetrievalMode.HYBRID_PRF.value:
        print(
            f"pseudo_feedback_docs={report.pseudo_feedback_docs} "
            f"pseudo_feedback_terms={report.pseudo_feedback_terms} "
            f"pseudo_feedback_weight={report.pseudo_feedback_weight:.3f}"
        )
    if report.embedding_model:
        print(f"embedding_model={report.embedding_model}")
    if report.embedding_query_prefix:
        print(f"embedding_query_prefix={report.embedding_query_prefix}")
    if report.embedding_document_prefix:
        print(f"embedding_document_prefix={report.embedding_document_prefix}")
    if report.rerank_model:
        print(f"rerank_model={report.rerank_model}")
    print(f"hit_rate={_format_percent(report.hit_rate)}")
    print(f"mrr={report.mean_reciprocal_rank:.3f}")
    print(f"expected_recall={_format_percent(report.mean_expected_recall)}")
    print(f"precision_at_k={_format_percent(report.mean_precision_at_k)}")
    print(f"map_at_k={report.mean_average_precision_at_k:.3f}")
    print(f"ndcg_at_k={report.mean_ndcg_at_k:.3f}")
    print(f"graded_ndcg_at_k={report.mean_graded_ndcg_at_k:.3f}")
    print(
        "forbidden_before_expected_avoidance="
        f"{_format_percent(report.forbidden_before_expected_avoidance)}"
    )
    print(f"mean_latency_ms={report.mean_latency_ms:.1f}")
    if report.misses:
        print(f"misses={', '.join(report.misses)}")
    if report.forbidden_before_expected_failures:
        print(
            "forbidden_before_expected_failures="
            f"{', '.join(report.forbidden_before_expected_failures)}"
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armory", type=Path, help="Armory path containing materials/")
    parser.add_argument("dataset", type=Path, help="JSON or JSONL labelled benchmark cases")
    parser.add_argument("--top-k", type=int, default=_DEFAULT_TOP_K)
    parser.add_argument("--min-score", type=float, default=_DEFAULT_MIN_SCORE)
    parser.add_argument(
        "--strategy",
        choices=[strategy.value for strategy in TransformStrategy],
        default=TransformStrategy.IDENTITY.value,
        help="RAG query transformation strategy",
    )
    parser.add_argument("--embedding-model", help="Sentence-transformers embedding model")
    parser.add_argument(
        "--embedding-query-prefix",
        default="",
        help="Prefix applied to embedding queries, for instruction-tuned retrievers",
    )
    parser.add_argument(
        "--embedding-document-prefix",
        default="",
        help="Prefix applied to embedded documents, for asymmetric retrievers",
    )
    parser.add_argument("--rerank-model", help="Cross-encoder reranking model")
    parser.add_argument("--hybrid-sparse-weight", type=float, default=1.0)
    parser.add_argument("--hybrid-dense-weight", type=float, default=1.0)
    parser.add_argument("--pseudo-feedback-docs", type=int, default=DEFAULT_PSEUDO_FEEDBACK_DOCS)
    parser.add_argument("--pseudo-feedback-terms", type=int, default=DEFAULT_PSEUDO_FEEDBACK_TERMS)
    parser.add_argument(
        "--pseudo-feedback-weight",
        type=float,
        default=DEFAULT_PSEUDO_FEEDBACK_WEIGHT,
    )
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    parser.add_argument("--min-hit-rate", type=float, default=0.0, help="Fail below this hit rate")
    parser.add_argument("--min-mrr", type=float, default=0.0, help="Fail below this MRR")
    parser.add_argument(
        "--min-expected-recall",
        type=float,
        default=0.0,
        help="Fail below this expected-reference recall",
    )
    parser.add_argument(
        "--min-forbidden-before-expected-avoidance",
        type=float,
        default=0.0,
        help="Fail when plausible wrong evidence outranks expected evidence too often",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    armory = cast("Path", args.armory).expanduser().resolve()
    dataset = cast("Path", args.dataset).expanduser().resolve()
    top_k = cast("int", args.top_k)
    min_score = cast("float", args.min_score)
    min_hit_rate = cast("float", args.min_hit_rate)
    min_mrr = cast("float", args.min_mrr)
    min_expected_recall = cast("float", args.min_expected_recall)
    min_forbidden_before_expected_avoidance = cast(
        "float",
        args.min_forbidden_before_expected_avoidance,
    )
    embed_model = cast("str | None", args.embedding_model)
    embed_query_prefix = cast("str", args.embedding_query_prefix)
    embed_document_prefix = cast("str", args.embedding_document_prefix)
    rerank_model = cast("str | None", args.rerank_model)
    hybrid_sparse_weight = cast("float", args.hybrid_sparse_weight)
    hybrid_dense_weight = cast("float", args.hybrid_dense_weight)
    pseudo_feedback_docs = cast("int", args.pseudo_feedback_docs)
    pseudo_feedback_terms = cast("int", args.pseudo_feedback_terms)
    pseudo_feedback_weight = cast("float", args.pseudo_feedback_weight)

    if top_k <= 0:
        parser.error("--top-k must be positive")
    if min_score < 0:
        parser.error("--min-score must be non-negative")
    if not 0 <= min_hit_rate <= 1:
        parser.error("--min-hit-rate must be between 0 and 1")
    if not 0 <= min_mrr <= 1:
        parser.error("--min-mrr must be between 0 and 1")
    if not 0 <= min_expected_recall <= 1:
        parser.error("--min-expected-recall must be between 0 and 1")
    if not 0 <= min_forbidden_before_expected_avoidance <= 1:
        parser.error("--min-forbidden-before-expected-avoidance must be between 0 and 1")
    if hybrid_sparse_weight < 0 or hybrid_dense_weight < 0:
        parser.error("--hybrid-sparse-weight and --hybrid-dense-weight must be non-negative")
    if pseudo_feedback_docs <= 0 or pseudo_feedback_terms <= 0:
        parser.error("--pseudo-feedback-docs and --pseudo-feedback-terms must be positive")
    if pseudo_feedback_weight < 0:
        parser.error("--pseudo-feedback-weight must be non-negative")

    try:
        strategy = TransformStrategy(cast("str", args.strategy))
        cases = load_cases(dataset)
        report = run_benchmark(
            armory,
            cases,
            top_k=top_k,
            min_score=min_score,
            transform_strategy=strategy,
            embed_model=embed_model,
            embed_query_prefix=embed_query_prefix,
            embed_document_prefix=embed_document_prefix,
            rerank_model=rerank_model,
            hybrid_sparse_weight=hybrid_sparse_weight,
            hybrid_dense_weight=hybrid_dense_weight,
            pseudo_feedback_docs=pseudo_feedback_docs,
            pseudo_feedback_terms=pseudo_feedback_terms,
            pseudo_feedback_weight=pseudo_feedback_weight,
        )
    except (TypeError, ValueError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2

    if cast("bool", args.json):
        print(json.dumps(asdict(report), indent=2))
    else:
        print_text_report(report)

    if (
        report.hit_rate < min_hit_rate
        or report.mean_reciprocal_rank < min_mrr
        or report.mean_expected_recall < min_expected_recall
        or report.forbidden_before_expected_avoidance < min_forbidden_before_expected_avoidance
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
