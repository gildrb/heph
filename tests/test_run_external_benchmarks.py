from __future__ import annotations

import json
import socket
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from hephaistos.armory.storage import initialize
from scripts import benchmark_rag, claim_report_envelope, run_external_benchmarks

ORACLE_KEYS_TO_REJECT = (
    "expected",
    "expected_past_exam_sources",
    "expected_role",
    "expected_text",
    "expected_topics",
    "forbidden_before_expected",
    "forbidden_topics",
    "must_include",
    "must_not_include",
    "relevance_grades",
)


def _write_jsonl(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_report(path: Path) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _as_str(value: object) -> str:
    assert isinstance(value, str)
    return value


def _has_exact_key(value: object, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(
            _has_exact_key(child, key_name) for child in value.values()
        )
    if isinstance(value, list):
        return any(_has_exact_key(item, key_name) for item in value)
    return False


def _make_armory(root: Path) -> Path:
    armory = root / "armory"
    initialize(armory)
    (armory / "materials" / "alpha.md").write_text(
        "Alpha receptor signaling material explains ligand binding and clinical retrieval.\n",
        encoding="utf-8",
    )
    (armory / "materials" / "beta.md").write_text(
        "Beta cache invalidation material is a plausible systems distractor.\n",
        encoding="utf-8",
    )
    return armory


def _make_external_suite(root: Path, cases: Sequence[dict[str, object]]) -> Path:
    suite = root / "suite"
    _make_armory(suite)
    _write_jsonl(suite / "rag.jsonl", cases)
    return suite


def _passing_cases() -> list[dict[str, object]]:
    return [
        {
            "id": "alpha",
            "domain": "fixture",
            "task": "single-source-retrieval",
            "query": "alpha receptor signaling ligand binding",
            "expected": ["materials/alpha.md"],
            "forbidden_before_expected": ["materials/beta.md"],
            "top_k": 9,
        }
    ]


def _case_result(
    *,
    case_id: str,
    query: str,
    retrieved: tuple[str, ...],
    hit: bool,
    rank: int | None,
    forbidden_rank: int | None = None,
    forbidden_ok: bool = True,
    chunk_scores: tuple[float, ...] | None = None,
) -> benchmark_rag.CaseResult:
    recall = 1.0 if hit else 0.0
    precision = recall / max(len(retrieved), 1)
    retrieved_chunks: tuple[benchmark_rag.RetrievedChunkResult, ...] = ()
    if chunk_scores is not None:
        assert len(chunk_scores) == len(retrieved)
        retrieved_chunks = tuple(
            benchmark_rag.RetrievedChunkResult(
                ref=ref,
                score=score,
                text_excerpt=f"excerpt for {ref}",
            )
            for ref, score in zip(retrieved, chunk_scores, strict=True)
        )
    return benchmark_rag.CaseResult(
        case_id=case_id,
        query=query,
        expected=("materials/alpha.md",),
        relevance_grades={},
        forbidden_before_expected=("materials/beta.md",),
        retrieved=retrieved,
        retrieved_chunks=retrieved_chunks,
        hit=hit,
        rank=rank,
        first_forbidden_rank=forbidden_rank,
        forbidden_before_expected_ok=forbidden_ok,
        recall=recall,
        precision_at_k=precision,
        average_precision_at_k=recall,
        ndcg_at_k=recall,
        graded_ndcg_at_k=recall,
        elapsed_ms=1.0,
    )


def _benchmark_report(
    *,
    retrieval_mode: str,
    top_k: int,
    results: tuple[benchmark_rag.CaseResult, ...],
    rerank_model: str | None = None,
) -> benchmark_rag.BenchmarkReport:
    total = len(results)
    hits = sum(1 for result in results if result.hit)
    recall_sum = sum(result.recall for result in results)
    reciprocal_rank_sum = sum(
        0.0 if result.rank is None else 1 / result.rank for result in results
    )
    precision_sum = sum(result.precision_at_k for result in results)
    average_precision_sum = sum(result.average_precision_at_k for result in results)
    ndcg_sum = sum(result.ndcg_at_k for result in results)
    graded_ndcg_sum = sum(result.graded_ndcg_at_k for result in results)
    forbidden_ok_count = sum(1 for result in results if result.forbidden_before_expected_ok)
    return benchmark_rag.BenchmarkReport(
        armory_path="/tmp/armory",
        cases=total,
        domains=("fixture",),
        tasks=("rerank",),
        top_k=top_k,
        min_score=0.0,
        retrieval_mode=retrieval_mode,
        candidate_multiplier=2,
        hybrid_sparse_weight=1.0,
        hybrid_dense_weight=1.0,
        pseudo_feedback_docs=3,
        pseudo_feedback_terms=6,
        pseudo_feedback_weight=0.1,
        retriever_backends=("FixtureRetriever",),
        transform_strategy="identity",
        embedding_model="fixture-embed",
        embedding_query_prefix="",
        embedding_document_prefix="",
        rerank_model=rerank_model,
        hit_rate=hits / total,
        mean_reciprocal_rank=reciprocal_rank_sum / total,
        mean_expected_recall=recall_sum / total,
        mean_precision_at_k=precision_sum / total,
        mean_average_precision_at_k=average_precision_sum / total,
        mean_ndcg_at_k=ndcg_sum / total,
        mean_graded_ndcg_at_k=graded_ndcg_sum / total,
        forbidden_before_expected_avoidance=forbidden_ok_count / total,
        mean_latency_ms=1.0,
        misses=tuple(result.case_id for result in results if not result.hit),
        forbidden_before_expected_failures=tuple(
            result.case_id for result in results if not result.forbidden_before_expected_ok
        ),
        results=results,
    )


def test_report_id_records_hybrid_prf_parameters() -> None:
    report_id = run_external_benchmarks._report_id(
        {
            "benchmark_type": "beir",
            "dataset": "beir/fixture",
            "fixed_parameters": {
                "retrieval_mode": "hybrid-prf",
                "transform_strategy": "identity",
                "top_k": 5,
                "min_score": 0.0,
                "candidate_multiplier": 2,
                "embedding_model": "BAAI/bge-large-en-v1.5",
                "embedding_query_prefix": (
                    "Represent this sentence for searching relevant passages: "
                ),
                "embedding_document_prefix": "",
                "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "hybrid_sparse_weight": 1.0,
                "hybrid_dense_weight": 1.5,
                "pseudo_feedback_docs": 3,
                "pseudo_feedback_terms": 6,
                "pseudo_feedback_weight": 0.1,
            },
        }
    )

    assert ":prf_docs=3:prf_terms=6:prf_weight=0.1" in report_id


def test_runner_executes_materialized_beir_suite_with_required_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "reports" / "external.json"
    monkeypatch.setenv("HEPHAISTOS_TEST_SECRET", "sentinel-secret-value")

    status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(suite),
            "--top-k",
            "9",
            "--min-score",
            "0.0",
            "--embedding-model",
            "fixture-embed-model",
            "--embedding-document-prefix",
            "passage: ",
            "--rerank-model",
            "fixture-rerank-model",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])
    metrics = _as_dict(report["aggregate_metrics"])
    formulas = _as_dict(metadata["metric_formulas"])
    parameters = _as_dict(metadata["fixed_parameters"])
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    warnings = _as_list(report["warnings"])
    envelope = _as_dict(report["claim_envelope"])
    determinism = _as_dict(envelope["determinism"])
    claim_policy = _as_dict(report["claim_policy"])
    leakage = _as_dict(claim_policy["leakage"])
    privacy = _as_dict(claim_policy["privacy"])

    assert status == 0
    assert report["schema_version"] == "external-runner-report-v1"
    assert report["report_id"] == (
        "beir:beir/fixture:mode=bm25:strategy=identity:top_k=9:"
        "min_score=0.0:candidate_multiplier=2:"
        "embedding_model=fixture-embed-model:embedding_document_prefix=passage--:"
        "rerank_model=fixture-rerank-model"
    )
    assert report["status"] == "success"
    assert metadata["benchmark_type"] == "beir"
    assert metadata["dataset"] == "beir/fixture"
    assert parameters["top_k"] == 9
    assert parameters["min_score"] == 0.0
    assert parameters["retrieval_mode"] == "bm25"
    assert parameters["candidate_multiplier"] == 2
    assert parameters["embedding_model"] == "fixture-embed-model"
    assert parameters["embedding_document_prefix"] == "passage: "
    assert parameters["rerank_model"] == "fixture-rerank-model"
    assert "cases_sha256" in metadata
    assert "corpus_sha256" in metadata
    assert "manifest_sha256" in metadata
    assert "qrels_sha256" in metadata
    assert metadata["dependency_lock_sha256"] == claim_report_envelope.sha256_file(
        claim_report_envelope.repo_root() / "uv.lock"
    )
    assert metadata["scoring_protocol_version"] == (claim_report_envelope.SCORING_PROTOCOL_VERSION)
    assert metadata["latency_scope"] == claim_report_envelope.LATENCY_SCOPE_RETRIEVAL_ONLY
    assert metadata["network_state"] == "disabled-after-materialization"
    assert metadata["cache_state"] == "local-cache-allowed"
    assert envelope["schema_version"] == claim_report_envelope.CLAIM_REPORT_ENVELOPE_SCHEMA_VERSION
    assert envelope["claim_eligible"] is False
    assert "reproducibility validation was not enabled and passed" in _as_list(
        envelope["ineligibility_reasons"]
    )
    observed_projection_sha256 = claim_report_envelope.deterministic_projection_sha256(report)
    assert determinism["projection_sha256"] == observed_projection_sha256
    assert parameters["query_order"] == "case-file-order"
    assert _as_str(formulas["hit_rate"]).startswith("fraction of queries")
    assert _as_str(formulas["mrr"]).startswith("mean reciprocal rank")
    assert _as_str(formulas["expected_recall"]).startswith("average retrieved expected references")
    assert _as_str(formulas["ndcg_at_k"]).startswith("mean normalized")
    assert _as_str(formulas["graded_ndcg_at_k"]).startswith("mean normalized")
    assert metrics["hit_rate"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["expected_recall"] == 1.0
    assert metrics["recall_at_k"] == 1.0
    assert metrics["precision_at_k"] == 1 / 9
    assert metrics["map_at_k"] == 1.0
    assert metrics["ndcg_at_k"] == 1.0
    assert metrics["graded_ndcg_at_k"] == 1.0
    assert isinstance(metrics["mean_latency_ms"], float)
    assert benchmark["status"] == "success"
    assert "miss_diagnostics" in benchmark
    for oracle_key in ORACLE_KEYS_TO_REJECT:
        assert not _has_exact_key(report, oracle_key)
    assert leakage["status"] == "passed"
    assert privacy["analytics_enabled_by_default"] is False
    assert privacy["crash_reports_enabled_by_default"] is False
    assert any("top_k=9" in str(warning) for warning in warnings)
    assert "sentinel-secret-value" not in json.dumps(report)


def test_runner_accepts_materialized_mteb_suite_with_dynamic_dataset(
    tmp_path: Path,
) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "reports" / "mteb.json"

    status = run_external_benchmarks.main(
        [
            "mteb",
            "mteb/SciFact",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])

    assert status == 0
    assert report["status"] == "success"
    assert metadata["benchmark_type"] == "mteb"
    assert metadata["dataset"] == "mteb/SciFact"
    assert benchmark["id"] == "mteb:mteb/SciFact"


def test_runner_executes_materialized_enterprise_rag_suite(tmp_path: Path) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "reports" / "enterprise-rag.json"

    status = run_external_benchmarks.main(
        [
            "enterprise-rag",
            "enterprise-rag-bench",
            "--suite",
            str(suite),
            "--top-k",
            "3",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])

    assert status == 0
    assert report["status"] == "success"
    assert metadata["benchmark_type"] == "enterprise-rag"
    assert metadata["dataset"] == "enterprise-rag-bench"
    assert benchmark["id"] == "enterprise-rag:enterprise-rag-bench"
    assert _as_dict(report["aggregate_metrics"])["hit_rate"] == 1.0


def test_enterprise_rag_reports_query_classification_for_neutral_renamed_cases(
    tmp_path: Path,
) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "neutral-alpha",
                "query": "Which source document explains alpha receptor signaling?",
                "expected": ["materials/alpha.md"],
            },
            {
                "id": "neutral-beta",
                "query": "Which source document explains beta cache invalidation?",
                "expected": ["materials/beta.md"],
            },
        ],
    )
    report_path = tmp_path / "reports" / "classification.json"

    status = run_external_benchmarks.main(
        [
            "enterprise-rag",
            "enterprise-rag-bench",
            "--suite",
            str(suite),
            "--top-k",
            "2",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    summary = _as_dict(benchmark["query_classification"])
    per_query = [_as_dict(row) for row in _as_list(benchmark["per_query_results"])]
    classifications = [_as_dict(row["query_classification"])["query_class"] for row in per_query]

    assert status == 0
    assert summary["decision_basis"] == "query-text-and-fixed-retrieval-parameters"
    assert _as_dict(summary["query_class_counts"]) == {"source_lookup": 2}
    assert classifications == ["source_lookup", "source_lookup"]
    assert _as_dict(per_query[0]["retrieval_trace"])["candidate_budget"] == 4


def test_enterprise_rag_hybrid_rerank_reports_candidate_and_harm_analysis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "win",
                "query": "alpha should rerank ahead of beta",
                "expected": ["materials/alpha.md"],
                "forbidden_before_expected": ["materials/beta.md"],
            },
            {
                "id": "harm",
                "query": "alpha should not be dropped behind beta",
                "expected": ["materials/alpha.md"],
                "forbidden_before_expected": ["materials/beta.md"],
            },
        ],
    )
    candidate_report = _benchmark_report(
        retrieval_mode="hybrid",
        top_k=2,
        results=(
            _case_result(
                case_id="win",
                query="alpha should rerank ahead of beta",
                retrieved=("materials/beta.md", "materials/alpha.md"),
                hit=True,
                rank=2,
                forbidden_rank=1,
                forbidden_ok=False,
                chunk_scores=(0.8, 0.4),
            ),
            _case_result(
                case_id="harm",
                query="alpha should not be dropped behind beta",
                retrieved=("materials/alpha.md", "materials/beta.md"),
                hit=True,
                rank=1,
                forbidden_rank=2,
                chunk_scores=(0.9, 0.3),
            ),
        ),
    )
    post_report = _benchmark_report(
        retrieval_mode="hybrid-rerank",
        top_k=1,
        rerank_model="fixture-reranker",
        results=(
            _case_result(
                case_id="win",
                query="alpha should rerank ahead of beta",
                retrieved=("materials/alpha.md",),
                hit=True,
                rank=1,
                chunk_scores=(0.95,),
            ),
            _case_result(
                case_id="harm",
                query="alpha should not be dropped behind beta",
                retrieved=("materials/beta.md",),
                hit=False,
                rank=None,
                forbidden_rank=1,
                forbidden_ok=False,
                chunk_scores=(0.96,),
            ),
        ),
    )

    def fake_run_benchmark(
        _armory_path: Path,
        _cases: Sequence[benchmark_rag.BenchmarkCase],
        **kwargs: object,
    ) -> benchmark_rag.BenchmarkReport:
        retrieval_mode = kwargs["retrieval_mode"]
        if retrieval_mode == run_external_benchmarks.RetrievalMode.HYBRID:
            return candidate_report
        if retrieval_mode == run_external_benchmarks.RetrievalMode.HYBRID_RERANK:
            return post_report
        raise AssertionError(f"unexpected retrieval mode: {retrieval_mode}")

    monkeypatch.setattr(
        run_external_benchmarks.benchmark_rag,
        "run_benchmark",
        fake_run_benchmark,
    )
    report_path = tmp_path / "reports" / "rerank.json"

    status = run_external_benchmarks.main(
        [
            "enterprise-rag",
            "enterprise-rag-bench",
            "--suite",
            str(suite),
            "--retrieval-mode",
            "hybrid-rerank",
            "--top-k",
            "1",
            "--candidate-multiplier",
            "2",
            "--rerank-model",
            "fixture-reranker",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    analysis = _as_dict(benchmark["rerank_analysis"])
    per_query = _as_list(analysis["per_query"])
    first_query = _as_dict(per_query[0])
    second_query = _as_dict(per_query[1])
    boost_diagnostics = _as_dict(analysis["boost_diagnostics"])
    selection = _as_dict(analysis["configuration_selection"])
    first_score_comparison = _as_dict(first_query["score_comparison"])

    assert status == 0
    assert analysis["top_k"] == 1
    assert analysis["candidate_multiplier"] == 2
    assert analysis["candidate_budget"] == 2
    assert analysis["recall_at_candidate_budget"] == 1.0
    assert _as_dict(analysis["post_rerank_metrics"])["recall_at_k"] == 0.5
    assert analysis["win_loss_tie"] == {"win": 1, "loss": 1, "tie": 0}
    assert _as_dict(analysis["harm"])["case_count"] == 1
    assert first_query["candidate_count"] == 2
    assert first_query["pre_rerank_rank"] == 2
    assert first_query["post_rerank_rank"] == 1
    assert first_query["rerank_outcome"] == "win"
    assert second_query["rerank_outcome"] == "loss"
    assert second_query["harm_bucket"] == "forbidden_moved_before_expected"
    assert second_query["bottleneck_bucket"] == "candidate_found_but_ranked_outside_final_top_k"
    assert first_score_comparison["first_relevant_score_delta"] == 0.55
    assert boost_diagnostics["score_delta_available"] is True
    assert boost_diagnostics["shared_ref_score_delta_count"] == 2
    assert selection["primary_metric"] == "expected_recall"
    assert selection["safe_improvement"] is False
    assert selection["selected_configuration"] == "pre_rerank_baseline"
    assert selection["harm_case_count"] == 1
    assert _as_dict(analysis["reranker_state"])["claim_eligible"] is True


def test_enterprise_rag_hybrid_rerank_selects_claim_eligible_improvement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "win",
                "query": "alpha should rerank ahead of beta",
                "expected": ["materials/alpha.md"],
                "forbidden_before_expected": ["materials/beta.md"],
            },
        ],
    )
    candidate_report = _benchmark_report(
        retrieval_mode="hybrid",
        top_k=2,
        results=(
            _case_result(
                case_id="win",
                query="alpha should rerank ahead of beta",
                retrieved=("materials/beta.md", "materials/alpha.md"),
                hit=True,
                rank=2,
                forbidden_rank=1,
                forbidden_ok=False,
                chunk_scores=(0.8, 0.4),
            ),
        ),
    )
    post_report = _benchmark_report(
        retrieval_mode="hybrid-rerank",
        top_k=1,
        rerank_model="fixture-reranker",
        results=(
            _case_result(
                case_id="win",
                query="alpha should rerank ahead of beta",
                retrieved=("materials/alpha.md",),
                hit=True,
                rank=1,
                chunk_scores=(0.95,),
            ),
        ),
    )

    def fake_run_benchmark(
        _armory_path: Path,
        _cases: Sequence[benchmark_rag.BenchmarkCase],
        **kwargs: object,
    ) -> benchmark_rag.BenchmarkReport:
        retrieval_mode = kwargs["retrieval_mode"]
        if retrieval_mode == run_external_benchmarks.RetrievalMode.HYBRID:
            return candidate_report
        if retrieval_mode == run_external_benchmarks.RetrievalMode.HYBRID_RERANK:
            return post_report
        raise AssertionError(f"unexpected retrieval mode: {retrieval_mode}")

    monkeypatch.setattr(
        run_external_benchmarks.benchmark_rag,
        "run_benchmark",
        fake_run_benchmark,
    )
    report_path = tmp_path / "reports" / "rerank-selection.json"

    status = run_external_benchmarks.main(
        [
            "enterprise-rag",
            "enterprise-rag-bench",
            "--suite",
            str(suite),
            "--retrieval-mode",
            "hybrid-rerank",
            "--top-k",
            "1",
            "--candidate-multiplier",
            "2",
            "--rerank-model",
            "fixture-reranker",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    analysis = _as_dict(benchmark["rerank_analysis"])
    selection = _as_dict(analysis["configuration_selection"])
    metric_deltas = _as_dict(selection["metric_deltas"])

    assert status == 0
    assert selection["safe_improvement"] is True
    assert selection["selected_configuration"] == "hybrid-rerank"
    assert selection["harm_case_count"] == 0
    assert metric_deltas["expected_recall"] == 1.0


def test_enterprise_rag_hybrid_rerank_blocks_claims_when_reranker_falls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "fallback",
                "query": "alpha rerank fallback control",
                "expected": ["materials/alpha.md"],
                "forbidden_before_expected": ["materials/beta.md"],
            },
        ],
    )
    candidate_report = _benchmark_report(
        retrieval_mode="hybrid",
        top_k=2,
        results=(
            _case_result(
                case_id="fallback",
                query="alpha rerank fallback control",
                retrieved=("materials/beta.md", "materials/alpha.md"),
                hit=True,
                rank=2,
                forbidden_rank=1,
                forbidden_ok=False,
            ),
        ),
    )
    post_report = _benchmark_report(
        retrieval_mode="hybrid",
        top_k=1,
        rerank_model=None,
        results=(
            _case_result(
                case_id="fallback",
                query="alpha rerank fallback control",
                retrieved=("materials/alpha.md",),
                hit=True,
                rank=1,
            ),
        ),
    )

    def fake_run_benchmark(
        _armory_path: Path,
        _cases: Sequence[benchmark_rag.BenchmarkCase],
        **kwargs: object,
    ) -> benchmark_rag.BenchmarkReport:
        retrieval_mode = kwargs["retrieval_mode"]
        if retrieval_mode == run_external_benchmarks.RetrievalMode.HYBRID:
            return candidate_report
        if retrieval_mode == run_external_benchmarks.RetrievalMode.HYBRID_RERANK:
            return post_report
        raise AssertionError(f"unexpected retrieval mode: {retrieval_mode}")

    monkeypatch.setattr(
        run_external_benchmarks.benchmark_rag,
        "run_benchmark",
        fake_run_benchmark,
    )
    report_path = tmp_path / "reports" / "rerank-fallback.json"

    status = run_external_benchmarks.main(
        [
            "enterprise-rag",
            "enterprise-rag-bench",
            "--suite",
            str(suite),
            "--retrieval-mode",
            "hybrid-rerank",
            "--top-k",
            "1",
            "--candidate-multiplier",
            "2",
            "--rerank-model",
            "fixture-reranker",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    analysis = _as_dict(benchmark["rerank_analysis"])
    reranker_state = _as_dict(analysis["reranker_state"])
    selection = _as_dict(analysis["configuration_selection"])
    reasons = _as_list(reranker_state["ineligibility_reasons"])

    assert status == 0
    assert reranker_state["claim_eligible"] is False
    assert reranker_state["claim_blocking"] is True
    assert reranker_state["fallback_status"] == "non_reranked_fallback"
    assert reranker_state["dependency_state"] == "unavailable_or_fallback"
    assert any("retrieval mode reported as 'hybrid'" in str(reason) for reason in reasons)
    assert any("active reranker model" in str(reason) for reason in reasons)
    assert selection["safe_improvement"] is False
    assert selection["selected_configuration"] == "no_claim_eligible_rerank"


def test_enterprise_rag_repair_pass_reports_trace_and_effective_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "repairable",
                "query": "distractor alpha receptor repair target",
                "expected": ["materials/alpha.md"],
                "forbidden_before_expected": ["materials/beta.md"],
            },
            {
                "id": "failed",
                "query": "irrelevant beta distractor target",
                "expected": ["materials/alpha.md"],
                "forbidden_before_expected": ["materials/beta.md"],
            },
        ],
    )

    def fake_run_benchmark(
        _armory_path: Path,
        cases: Sequence[benchmark_rag.BenchmarkCase],
        **kwargs: object,
    ) -> benchmark_rag.BenchmarkReport:
        results: list[benchmark_rag.CaseResult] = []
        for case in cases:
            repaired_query = "distractor" not in case.query.casefold()
            if case.case_id == "repairable" and repaired_query:
                results.append(
                    _case_result(
                        case_id=case.case_id,
                        query=case.query,
                        retrieved=("materials/alpha.md",),
                        hit=True,
                        rank=1,
                    )
                )
                continue
            results.append(
                _case_result(
                    case_id=case.case_id,
                    query=case.query,
                    retrieved=("materials/beta.md",),
                    hit=False,
                    rank=None,
                    forbidden_rank=1,
                    forbidden_ok=False,
                )
            )
        retrieval_mode = cast(
            "run_external_benchmarks.RetrievalMode",
            kwargs["retrieval_mode"],
        )
        top_k = cast("int", kwargs["top_k"])
        return _benchmark_report(
            retrieval_mode=retrieval_mode.value,
            top_k=top_k,
            results=tuple(results),
        )

    monkeypatch.setattr(
        run_external_benchmarks.benchmark_rag,
        "run_benchmark",
        fake_run_benchmark,
    )
    report_path = tmp_path / "reports" / "repair.json"

    status = run_external_benchmarks.main(
        [
            "enterprise-rag",
            "enterprise-rag-bench",
            "--suite",
            str(suite),
            "--top-k",
            "1",
            "--repair-max-passes",
            "2",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])
    parameters = _as_dict(metadata["fixed_parameters"])
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    analysis = _as_dict(benchmark["repair_analysis"])
    per_query = [_as_dict(row) for row in _as_list(analysis["per_query"])]
    repairable = next(row for row in per_query if row["case_id"] == "repairable")
    failed = next(row for row in per_query if row["case_id"] == "failed")
    repair_passes = [_as_dict(row) for row in _as_list(repairable["passes"])]
    failed_passes = [_as_dict(row) for row in _as_list(failed["passes"])]
    result_rows = [_as_dict(row) for row in _as_list(benchmark["per_query_results"])]
    repaired_result = next(row for row in result_rows if row["case_id"] == "repairable")

    assert status == 0
    assert parameters["repair_max_passes"] == 2
    assert ":repair_max_passes=2" in str(report["report_id"])
    assert _as_dict(benchmark["initial_metrics"])["hit_rate"] == 0.0
    assert _as_dict(benchmark["metrics"])["hit_rate"] == 0.5
    assert analysis["attempted_count"] == 2
    assert analysis["success_count"] == 1
    assert analysis["failed_count"] == 1
    assert analysis["improved_count"] == 1
    assert analysis["abstain_or_clarify_count"] == 1
    assert analysis["fabricated_evidence_ids"] == []
    assert repairable["used_repair"] is True
    assert repairable["successful"] is True
    assert repairable["final_cited_evidence_subset_of_retrieved"] is True
    assert repair_passes[0]["stop_reason"] == "retry_with_cleaned_query"
    assert repair_passes[1]["stop_reason"] == "sufficient_evidence_after_repair"
    assert repair_passes[1]["query_excerpt"] == "alpha receptor repair target"
    assert failed["abstain_or_clarify"] is True
    assert failed_passes[1]["stop_reason"] == "abstain_or_clarify"
    assert repaired_result["query"] == "distractor alpha receptor repair target"
    assert repaired_result["retrieved"] == ["materials/alpha.md"]


def test_runner_cli_top_k_overrides_case_top_k(tmp_path: Path) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "alpha",
                "domain": "fixture",
                "task": "single-source-retrieval",
                "query": "alpha beta material",
                "expected": ["materials/alpha.md"],
                "top_k": 1,
            }
        ],
    )
    report_path = tmp_path / "reports" / "external.json"

    status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(suite),
            "--top-k",
            "2",
            "--retrieval-mode",
            "bm25",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    result = _as_dict(_as_list(benchmark["per_query_results"])[0])
    rag_report = _as_dict(benchmark["rag_report"])
    assert status == 0
    assert rag_report["top_k"] == 2
    assert len(_as_list(result["retrieved"])) == 2


def test_runner_report_projection_is_deterministic_across_runtime_paths(
    tmp_path: Path,
) -> None:
    first_suite = _make_external_suite(tmp_path / "first", _passing_cases())
    second_suite = _make_external_suite(tmp_path / "second", _passing_cases())
    first_report_path = tmp_path / "reports" / "first.json"
    second_report_path = tmp_path / "reports" / "second.json"

    first_status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(first_suite),
            "--top-k",
            "9",
            "--min-score",
            "0.0",
            "--json-report",
            str(first_report_path),
        ]
    )
    second_status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(second_suite),
            "--top-k",
            "9",
            "--min-score",
            "0.0",
            "--json-report",
            str(second_report_path),
        ]
    )

    first_report = _read_report(first_report_path)
    second_report = _read_report(second_report_path)
    metadata = _as_dict(first_report["metadata"])
    reproducibility = _as_dict(first_report["reproducibility"])
    runtime_only_fields = _as_list(metadata["runtime_only_fields"])

    assert first_status == 0
    assert second_status == 0
    assert "metadata.suite_path" in runtime_only_fields
    assert "metadata.armory_path" in runtime_only_fields
    assert "metadata.cases_path" in runtime_only_fields
    assert reproducibility["runtime_only_fields"] == runtime_only_fields
    assert run_external_benchmarks.deterministic_report_projection(
        first_report
    ) == run_external_benchmarks.deterministic_report_projection(second_report)


def test_runner_validates_reproducibility_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "repro.json"
    argv = [
        "standard-rag",
        "ms-marco",
        "--suite",
        str(suite),
        "--validate-reproducibility",
        "--json-report",
        str(report_path),
    ]

    def fail_network(*_args: object, **_kwargs: object) -> socket.socket:
        raise AssertionError("runner must not open network sockets after materialization")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    status = run_external_benchmarks.main(argv)

    report = _read_report(report_path)
    reproducibility = _as_dict(report["reproducibility"])
    envelope = _as_dict(report["claim_envelope"])
    runtime_only_fields = _as_list(reproducibility["runtime_only_fields"])
    validation = claim_report_envelope.validate_claim_report_envelope(
        report,
        expected_command=claim_report_envelope.command_invocation(
            run_external_benchmarks.RUNNER_ID,
            argv,
        ),
    )

    assert status == 0
    assert report["status"] == "success"
    assert reproducibility["enabled"] is True
    assert reproducibility["status"] == "passed"
    assert envelope["claim_eligible"] is True
    for oracle_key in ORACLE_KEYS_TO_REJECT:
        assert not _has_exact_key(report, oracle_key)
    assert "benchmarks[].metrics.mean_latency_ms" in runtime_only_fields
    assert reproducibility["mismatches"] == []
    assert validation.status == "passed"
    assert validation.errors == ()


def test_runner_fails_threshold_gates_with_metric_details(tmp_path: Path) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "miss",
                "query": "unrelated astronomy vocabulary with no shared retrieval tokens",
                "expected": ["materials/alpha.md"],
            }
        ],
    )
    report_path = tmp_path / "threshold.json"

    status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(suite),
            "--min-score",
            "0.75",
            "--min-hit-rate",
            "1.0",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    failures = _as_list(report["threshold_failures"])
    first_failure = _as_dict(failures[0])

    assert status == 1
    assert report["status"] == "threshold_failed"
    assert first_failure["metric"] == "hit_rate"
    assert first_failure["minimum"] == 1.0
    assert first_failure["actual"] == 0.0


def test_runner_reports_structured_error_for_invalid_dataset(tmp_path: Path) -> None:
    suite = _make_external_suite(tmp_path, _passing_cases())
    report_path = tmp_path / "invalid.json"

    status = run_external_benchmarks.main(
        [
            "beir",
            "unsupported",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(_as_list(report["errors"])[0])

    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == "unsupported_dataset"
    assert "beir/nfcorpus" in str(error["remediation"])


def test_runner_rejects_degenerate_duplicate_expected_references(tmp_path: Path) -> None:
    suite = _make_external_suite(
        tmp_path,
        [
            {
                "id": "duplicate",
                "query": "alpha receptor signaling",
                "expected": ["materials/alpha.md", "materials/alpha.md"],
            }
        ],
    )
    report_path = tmp_path / "duplicate.json"

    status = run_external_benchmarks.main(
        [
            "standard-rag",
            "ms-marco",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(_as_list(report["errors"])[0])

    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == "duplicate_expected_references"


@pytest.mark.parametrize(
    ("case_payload", "expected_code"),
    [
        (
            {
                "id": "bad-top-k",
                "query": "alpha receptor signaling",
                "expected": ["materials/alpha.md"],
                "top_k": "many",
            },
            "invalid_top_k",
        ),
        (
            {
                "id": "missing-material",
                "query": "alpha receptor signaling",
                "expected": ["materials/missing.md"],
            },
            "missing_material_file",
        ),
        (
            {
                "id": "no-positive",
                "query": "alpha receptor signaling",
                "expected": [],
            },
            "no_positive_references",
        ),
    ],
)
def test_runner_rejects_other_degenerate_cases(
    tmp_path: Path,
    case_payload: dict[str, object],
    expected_code: str,
) -> None:
    suite = _make_external_suite(tmp_path, [case_payload])
    report_path = tmp_path / "degenerate.json"

    status = run_external_benchmarks.main(
        [
            "standard-rag",
            "ms-marco",
            "--suite",
            str(suite),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    error = _as_dict(_as_list(report["errors"])[0])

    assert status == 2
    assert report["status"] == "error"
    assert error["code"] == expected_code


def test_runner_resolves_public_academic_readiness_report(tmp_path: Path) -> None:
    armory = _make_armory(tmp_path / "materialized")
    cases_dir = tmp_path / "public-cases"
    _write_jsonl(cases_dir / "rag.jsonl", _passing_cases())
    (cases_dir / "readiness_report.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "benchmark_ready": True,
                "armory_path": str(armory),
                "generated_files": {"rag": str(cases_dir / "rag.jsonl")},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "public-academic.json"

    status = run_external_benchmarks.main(
        [
            "public-academic",
            "public-academic",
            "--suite",
            str(cases_dir),
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    metadata = _as_dict(report["metadata"])

    assert status == 0
    assert report["status"] == "success"
    assert metadata["benchmark_type"] == "public-academic"
    assert metadata["dataset"] == "public-academic"
    assert metadata["readiness_report_path"] == str(
        (cases_dir / "readiness_report.json").resolve()
    )


def test_heph_native_runner_wraps_existing_suite_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite = tmp_path / "native-suite"
    suite.mkdir()
    report_path = tmp_path / "native-wrapper.json"
    observed: dict[str, object] = {}

    def fake_run_suite(
        suite_path: Path,
        *,
        rag_hit_rate: float,
        rag_mrr: float,
        rag_expected_recall: float,
        report_path: Path | None,
    ) -> int:
        observed["suite_path"] = str(suite_path)
        observed["rag_hit_rate"] = rag_hit_rate
        observed["rag_mrr"] = rag_mrr
        observed["rag_expected_recall"] = rag_expected_recall
        assert report_path is not None
        report_path.write_text(
            json.dumps(
                {
                    "suite": str(suite_path),
                    "status": 0,
                    "thresholds": {
                        "rag_hit_rate": rag_hit_rate,
                        "rag_mrr": rag_mrr,
                        "rag_expected_recall": rag_expected_recall,
                    },
                    "rag": {
                        "hit_rate": 1.0,
                        "mean_reciprocal_rank": 0.9,
                        "mean_expected_recall": 1.0,
                        "mean_latency_ms": 3.0,
                    },
                    "material_roles": {"pass_rate": 1.0},
                    "document_understanding": {"passed": True},
                    "answers": {"pass_rate": 1.0},
                    "priority": {
                        "cases": [
                            {
                                "case_id": "priority-1",
                                "expected_topics": ["hidden topic"],
                                "expected_past_exam_sources": ["materials/exam.md"],
                                "forbidden_topics": ["private distractor"],
                            }
                        ]
                    },
                    "roles": [{"case_id": "role-1", "expected_role": "lecture"}],
                    "answers_detail": [
                        {
                            "case_id": "answer-1",
                            "expected_text": "hidden answer",
                            "must_include": ["hidden answer"],
                            "must_not_include": ["private distractor"],
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(run_external_benchmarks.run_benchmark_suite, "run_suite", fake_run_suite)

    status = run_external_benchmarks.main(
        [
            "heph-native",
            "academic",
            "--suite",
            str(suite),
            "--min-hit-rate",
            "0.8",
            "--min-mrr",
            "0.7",
            "--min-expected-recall",
            "0.9",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    benchmark = _as_dict(_as_list(report["benchmarks"])[0])
    native_report = _as_dict(benchmark["native_suite_report"])

    assert status == 0
    assert observed == {
        "suite_path": str(suite.resolve()),
        "rag_hit_rate": 0.8,
        "rag_mrr": 0.7,
        "rag_expected_recall": 0.9,
    }
    assert benchmark["benchmark_type"] == "heph-native"
    assert _as_dict(native_report["rag"])["hit_rate"] == 1.0
    assert "material_roles" in native_report
    for oracle_key in ORACLE_KEYS_TO_REJECT:
        assert not _has_exact_key(report, oracle_key)
