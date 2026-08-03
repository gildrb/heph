"""Tests for the retriever protocol, embedding retriever, and hybrid retriever."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import harness.rag.sparse as sparse_module
import pytest
from harness.rag.chunker import Chunk, ChunkedDocument
from harness.rag.index import ArmoryIndex
from harness.rag.retrieve import (
    Bm25Retriever,
    DocumentBm25Retriever,
    RetrievalMode,
    ScoredChunk,
    TfidfRetriever,
    _apply_negation_precision_penalty,
    _compound_query_variants,
    _expand_query_with_corpus_token_variants,
    _normalize_query_for_retrieval,
    retrieve,
)
from harness.rag.scoring import (
    cosine_similarity,
    reciprocal_rank_fusion,
    tokenize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(text: str, source: str = "test.md", index: int = 0) -> Chunk:
    return Chunk(text=text, source=source, index=index, char_start=0, char_end=len(text))


def _make_index_with_chunks(chunks: list[Chunk]) -> ArmoryIndex:
    """Build a minimal ArmoryIndex with the given chunks."""
    return _make_index_with_chunks_at(Path("/fake"), chunks)


def _make_index_with_chunks_at(armory_path: Path, chunks: list[Chunk]) -> ArmoryIndex:
    by_source: dict[str, list[Chunk]] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c)

    index = ArmoryIndex(armory_path)
    for source, source_chunks in by_source.items():
        index.documents.append(
            ChunkedDocument(
                source=source,
                chunks=source_chunks,
                content_hash="fake",
            )
        )
    return index


class _VariantRetriever:
    def __init__(self, ranked_by_query: dict[str, list[ScoredChunk]]) -> None:
        self._ranked_by_query = ranked_by_query

    def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        return self._ranked_by_query.get(query, [])[:top_k]


def test_normalize_query_for_retrieval_preserves_long_prompt_tail_signal() -> None:
    query = "intro " + "filler " * 400 + "final question exact sentinel phrase amber forge"

    normalized = _normalize_query_for_retrieval(query)

    assert len(tokenize(normalized)) <= 180
    assert "exact sentinel phrase amber forge" in normalized
    assert normalized.count("filler") <= 2


def test_tokenize_folds_lhopital_diacritic_and_spelling_variants() -> None:
    assert "hopital" in tokenize("L'Hôpital")
    assert "hospital" in tokenize("L'Hospital")


def test_retrieve_matches_lhopital_without_accents_to_lhospital_source() -> None:
    index = _make_index_with_chunks(
        [
            _make_chunk(
                "Die Folien nennen die Regel von L'Hospital für Grenzwertaufgaben.",
                "analysis.md",
            ),
            _make_chunk("Zahlensysteme und elementare Funktionen.", "basics.md"),
        ]
    )

    results = retrieve("was ist l hopital?", index, top_k=2, min_score=0.1)

    assert results
    assert results[0].chunk.source == "analysis.md"


def test_query_expansion_uses_near_matches_from_current_corpus() -> None:
    index = _make_index_with_chunks(
        [
            _make_chunk("The frobnicate marker controls the example system.", "target.md"),
            _make_chunk("A separate baseline note.", "other.md"),
        ]
    )

    expanded = _expand_query_with_corpus_token_variants("frobncate marker", index)

    assert "frobnicate" in expanded


def test_retrieve_uses_near_corpus_token_match_without_static_synonyms() -> None:
    index = _make_index_with_chunks(
        [
            _make_chunk("The frobnicate marker controls the example system.", "target.md"),
            _make_chunk("A separate baseline note.", "other.md"),
        ]
    )

    results = retrieve("frobncate marker", index, top_k=2, min_score=0.1)

    assert results
    assert results[0].chunk.source == "target.md"


def test_retrieve_long_noisy_query_still_finds_tail_match() -> None:
    index = _make_index_with_chunks(
        [
            _make_chunk("Only this file contains the exact phrase amber forge.", "target.md"),
            _make_chunk("Binary search trees allow logarithmic lookup.", "other.md"),
        ]
    )
    query = "Please ignore filler. " + "filler " * 500 + "What exact phrase is amber forge?"

    results = retrieve(query, index, top_k=2, min_score=0.1)

    assert results
    assert results[0].chunk.source == "target.md"


def test_retrieve_downranks_negative_contrast_for_affirmative_query() -> None:
    index = _make_index_with_chunks(
        [
            _make_chunk(
                "Dijkstra chooses the next frontier node with a priority queue.",
                "dijkstra.md",
            ),
            _make_chunk(
                "Bellman-Ford handles negative weights. This is not the standard choice "
                "when the question asks for Dijkstra's frontier data structure.",
                "bellman-ford.md",
            ),
        ]
    )

    results = retrieve(
        "For Dijkstra with non-negative edge weights, which data structure chooses "
        "the next frontier node?",
        index,
        top_k=2,
        min_score=0.0,
    )

    assert [result.chunk.source for result in results] == ["dijkstra.md", "bellman-ford.md"]


def test_negation_precision_penalty_keeps_negated_queries_in_order() -> None:
    results = [
        ScoredChunk(
            chunk=_make_chunk("This is not the standard method.", "negative.md"),
            score=0.9,
        ),
        ScoredChunk(chunk=_make_chunk("This is the standard method.", "positive.md"), score=0.8),
    ]

    reranked = _apply_negation_precision_penalty("Which method is not standard?", results)

    assert [result.chunk.source for result in reranked] == ["negative.md", "positive.md"]


def test_negation_precision_penalty_ignores_unrelated_negated_sentence() -> None:
    results = [
        ScoredChunk(
            chunk=_make_chunk(
                "Active recall is useful after an explanation. "
                "If the source material does not contain the answer, the tutor abstains.",
                "harness.documents.md",
            ),
            score=0.9,
        ),
        ScoredChunk(
            chunk=_make_chunk(
                "An active site can be explained through enzyme kinetics.",
                "biochem.md",
            ),
            score=0.88,
        ),
    ]

    reranked = _apply_negation_precision_penalty(
        "Why use active recall after an explanation?",
        results,
    )

    assert [result.chunk.source for result in reranked] == ["harness.documents.md", "biochem.md"]
    assert reranked[0].score == 0.9


def test_negation_precision_penalty_preserves_explicit_negation_queries() -> None:
    results = [
        ScoredChunk(
            chunk=_make_chunk(
                "If the source material does not contain the answer, the tutor abstains.",
                "abstention.md",
            ),
            score=0.9,
        ),
        ScoredChunk(chunk=_make_chunk("The tutor answers from memory.", "memory.md"), score=0.8),
    ]

    reranked = _apply_negation_precision_penalty(
        "What should a grounded tutor do when the source does not contain the answer?",
        results,
    )

    assert [result.chunk.source for result in reranked] == ["abstention.md", "memory.md"]
    assert reranked[0].score == 0.9


def test_retrieve_can_diversify_duplicate_source_chunks() -> None:
    chunks = [
        _make_chunk("alpha topic repeated", "same.md", 0),
        _make_chunk("alpha topic repeated again", "same.md", 1),
        _make_chunk("alpha topic target", "other.md", 0),
    ]
    index = _make_index_with_chunks(chunks)

    results = retrieve(
        "alpha topic",
        index,
        top_k=2,
        candidate_multiplier=3,
        diversify_sources=True,
    )

    assert {result.chunk.source for result in results} == {"same.md", "other.md"}


def test_compound_query_variants_extracts_both_clauses() -> None:
    variants = _compound_query_variants(
        "Using the sources, answer both: what rule does integration by parts follow from, "
        "and what do Fourier transforms decompose periodic signals into?"
    )

    assert variants[1:] == [
        "what rule does integration by parts follow from",
        "what do Fourier transforms decompose periodic signals into",
    ]


def test_retrieve_promotes_each_compound_clause_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = (
        "answer both: what rule does integration by parts follow from, "
        "and what do Fourier transforms decompose periodic signals into?"
    )
    normalized_query = " ".join(query.split())
    calculus_query = "what rule does integration by parts follow from"
    physics_query = "what do Fourier transforms decompose periodic signals into"
    calculus = ScoredChunk(
        chunk=_make_chunk(
            "Integration by parts follows from the product rule for derivatives.",
            "calculus.md",
            0,
        ),
        score=10.0,
    )
    calculus_neighbor = ScoredChunk(
        chunk=_make_chunk("Integration examples and extra calculus notes.", "calculus.md", 1),
        score=9.0,
    )
    physics = ScoredChunk(
        chunk=_make_chunk(
            "Fourier transforms decompose periodic signals into frequency components.",
            "physics.md",
            0,
        ),
        score=7.0,
    )
    retriever = _VariantRetriever(
        {
            normalized_query: [calculus, calculus_neighbor],
            calculus_query: [calculus],
            physics_query: [physics],
        }
    )
    retrieve_module = import_module("harness.rag.retrieve")
    monkeypatch.setattr(retrieve_module, "_create_retriever", lambda *_args, **_kwargs: retriever)

    results = retrieve(
        query,
        _make_index_with_chunks([calculus.chunk, calculus_neighbor.chunk, physics.chunk]),
        top_k=2,
    )

    assert [result.chunk.source for result in results] == ["calculus.md", "physics.md"]


# ---------------------------------------------------------------------------
# RetrieverProtocol
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TF-IDF retriever (sklearn + stdlib fallback)
# ---------------------------------------------------------------------------


class TestTfidfRetriever:
    def test_empty_index_returns_nothing(self) -> None:
        index = ArmoryIndex(Path("/fake"))
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("python")
        assert results == []

    def test_exact_keyword_match(self) -> None:
        chunks = [
            _make_chunk("Python is a programming language with dynamic typing.", "python.md", 0),
            _make_chunk("Rust is a systems programming language with ownership.", "rust.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("python programming")

        assert len(results) > 0
        assert results[0].chunk.source == "python.md"

    def test_top_k_limit(self) -> None:
        chunks = [
            _make_chunk(f"Document about topic number {i}.", f"doc{i}.md", 0) for i in range(10)
        ]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("topic number", top_k=3)
        assert len(results) == 3

    def test_scores_are_positive(self) -> None:
        chunks = [
            _make_chunk("Machine learning uses neural networks.", "ml.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("machine learning")
        for r in results:
            assert r.score > 0

    def test_results_sorted_by_score(self) -> None:
        chunks = [
            _make_chunk("Python Python Python programming language", "a.md", 0),
            _make_chunk("Python is mentioned once here.", "b.md", 0),
            _make_chunk("Completely unrelated content about cooking.", "c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("python")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_query_returns_nothing(self) -> None:
        chunks = [_make_chunk("Some content", "a.md", 0)]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("")
        assert results == []

    def test_stop_words_only_query(self) -> None:
        chunks = [_make_chunk("Some content about things", "a.md", 0)]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("the is a")
        assert results == []

    def test_no_match_returns_empty(self) -> None:
        chunks = [
            _make_chunk("Cooking recipes and baking tips.", "cooking.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("quantum physics astronomy")
        assert results == []

    def test_query_can_match_source_filename(self) -> None:
        chunks = [
            _make_chunk(
                "The main theorem connects differentiation with integration.",
                "materials/L7_WorkspaceFixture-1_Fundamentalsatz.pdf",
                0,
            ),
            _make_chunk(
                "<!-- image -->", "materials/L7_WorkspaceFixture-1_Fundamentalsatz.pdf", 1
            ),
            _make_chunk(
                "Linear algebra introduces vector spaces and matrices.",
                "materials/linear-algebra.md",
                0,
            ),
        ]
        index = _make_index_with_chunks(chunks)
        retriever = TfidfRetriever(index)
        results = retriever.retrieve("how does the fundamentalsatz work")

        assert len(results) > 0
        assert results[0].chunk.source == "materials/L7_WorkspaceFixture-1_Fundamentalsatz.pdf"


class TestBm25Retriever:
    def test_empty_token_corpus_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class ExplodingBm25:
            def index(self, _corpus_tokens: list[list[str]], *, _show_progress: bool) -> object:
                raise AssertionError("empty token corpus should not be indexed")

        index = _make_index_with_chunks([_make_chunk("a I to the", "empty.md", 0)])
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", ExplodingBm25)

        retriever = Bm25Retriever(index)

        assert not retriever.available
        assert retriever.retrieve("anything") == []

    def test_stdlib_bm25_available_without_optional_backend(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chunks = [
            _make_chunk("alpha receptor binding", "alpha.md", 0),
            _make_chunk("beta cache invalidation", "beta.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        retriever = Bm25Retriever(index)
        results = retriever.retrieve("receptor binding", top_k=2)

        assert retriever.available
        assert results[0].chunk.source == "alpha.md"

    def test_build_failure_falls_back_to_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class FailingBm25:
            def index(self, _corpus_tokens: list[list[str]], *, _show_progress: bool) -> object:
                raise ValueError("max() iterable argument is empty")

        index = _make_index_with_chunks([_make_chunk("python", "python.md", 0)])
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", FailingBm25)

        retriever = Bm25Retriever(index)

        assert retriever.available

    def test_corpus_tokens_state_saved_and_reused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class FakeBm25:
            def index(self, _corpus_tokens: list[list[str]], *, show_progress: bool) -> object:
                assert show_progress is False
                return None

            def retrieve(
                self,
                _query_tokens: list[list[str]],
                *,
                k: int,
                show_progress: bool,
            ) -> tuple[object, object]:
                return [[0]], [[1.0]]

        chunks = [_make_chunk("Python is a programming language.", "python.md", 0)]
        index = _make_index_with_chunks_at(tmp_path, chunks)
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", FakeBm25)

        Bm25Retriever(index)
        state_path = tmp_path / ".harness" / f"retriever_{index.content_hash}_bm25_tokens_v8.json"

        assert state_path.is_file()

        def failtokenize(_text: str) -> list[str]:
            raise AssertionError("cached corpus tokens should be reused")

        monkeypatch.setattr(sparse_module, "tokenize", failtokenize)
        retriever = Bm25Retriever(index)

        assert retriever.available

    def test_source_section_query_can_break_repeated_title_tie(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chunks = [
            _make_chunk(
                "CS231n Deep Learning for Computer Vision Course Website",
                "materials/public-academic/stanford-cs231n/classification/index.html",
                0,
            ),
            _make_chunk(
                "CS231n Deep Learning for Computer Vision Course Website",
                "materials/public-academic/stanford-cs231n/neural-networks-1/index.html",
                0,
            ),
        ]
        index = _make_index_with_chunks(chunks)
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        retriever = Bm25Retriever(index)
        results = retriever.retrieve(
            "CS231n Deep Learning for Computer Vision at source section "
            '"stanford-cs231n/neural-networks-1"',
            top_k=2,
        )

        assert results[0].chunk.source.endswith("neural-networks-1/index.html")


class TestLeanRetrievalContract:
    def test_dense_mode_fails_clearly(self) -> None:
        with pytest.raises(RuntimeError, match="Dense retrieval requires"):
            retrieve(
                "query",
                _make_index_with_chunks([_make_chunk("query")]),
                retrieval_mode=RetrievalMode.DENSE,
            )

    def test_rerank_mode_fails_clearly(self) -> None:
        with pytest.raises(RuntimeError, match="Reranking is unavailable"):
            retrieve(
                "query",
                _make_index_with_chunks([_make_chunk("query")]),
                retrieval_mode=RetrievalMode.HYBRID_RERANK,
            )

    def test_auto_mode_uses_lexical_retrieval(self) -> None:
        results = retrieve(
            "query",
            _make_index_with_chunks([_make_chunk("query text")]),
        )
        assert results


class TestDocumentBm25Retriever:
    def test_ranks_whole_documents_not_individual_chunks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chunks = [
            _make_chunk("alpha project overview", "target.md", 0),
            _make_chunk("beta release details", "target.md", 1),
            _make_chunk("alpha only", "other.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        retriever = DocumentBm25Retriever(index)
        results = retriever.retrieve("alpha beta", top_k=2)

        assert retriever.available
        assert results[0].chunk.source == "target.md"
        assert [result.chunk.source for result in results].count("target.md") == 1

    def test_reads_material_file_text_when_available(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        material = tmp_path / "materials" / "doc.md"
        material.parent.mkdir(parents=True)
        material.write_text(
            "# Official title\n\nfull document sentinel phrase\n",
            encoding="utf-8",
        )
        chunk = _make_chunk("chunk text without sentinel", "materials/doc.md", 0)
        index = _make_index_with_chunks_at(tmp_path, [chunk])
        retrieve_module = import_module("harness.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        retriever = DocumentBm25Retriever(index)

        assert retriever.retrieve("sentinel phrase")[0].chunk.source == "materials/doc.md"


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


class TestTokenize:
    def test_splits_on_non_alnum(self) -> None:
        assert "python" in tokenize("Python, is; great!")

    def test_removes_stop_words(self) -> None:
        tokens = tokenize("the cat is on the mat")
        assert "the" not in tokens
        assert "cat" in tokens
        assert "mat" in tokens

    def test_removes_single_chars(self) -> None:
        tokens = tokenize("a big c")
        assert "a" not in tokens
        assert "c" not in tokens
        assert "big" in tokens

    def test_keeps_single_digit_section_tokens(self) -> None:
        tokens = tokenize("neural-networks-1 neural-networks-3")
        assert "1" in tokens
        assert "3" in tokens

    def test_lowercase(self) -> None:
        tokens = tokenize("Python PYTHON python")
        assert tokens == ["python", "python", "python"]

    def test_adds_conservative_plural_variants(self) -> None:
        tokens = tokenize("therapies receptors")
        assert "therapy" in tokens
        assert "receptor" in tokens


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        assert abs(cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9

    def test_orthogonal_vectors(self) -> None:
        assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9

    def test_opposite_vectors(self) -> None:
        assert abs(cosine_similarity([1, 0], [-1, 0]) - (-1.0)) < 1e-9

    def test_zero_vector(self) -> None:
        assert cosine_similarity([0, 0], [1, 1]) == 0.0

    def test_arbitrary_vectors(self) -> None:
        # [1,2,3] · [4,5,6] = 32, |a|=√14, |b|=√77
        sim = cosine_similarity([1, 2, 3], [4, 5, 6])
        expected = 32.0 / (14.0**0.5 * 77.0**0.5)
        assert abs(sim - expected) < 1e-6


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------


class TestReciprocalRankFusion:
    def test_single_list_preserves_order(self) -> None:
        chunks = [
            _make_chunk("alpha", "a.md", 0),
            _make_chunk("beta", "b.md", 0),
        ]
        ranked = [
            ScoredChunk(chunk=chunks[0], score=0.9),
            ScoredChunk(chunk=chunks[1], score=0.5),
        ]
        result = reciprocal_rank_fusion([ranked])
        assert len(result) == 2
        assert result[0].chunk.source == "a.md"

    def test_two_lists_agree_on_top(self) -> None:
        """When both lists rank the same item first, it should win."""
        c_a = _make_chunk("best match", "a.md", 0)
        c_b = _make_chunk("decent match", "b.md", 0)
        c_c = _make_chunk("okay match", "c.md", 0)

        list1 = [
            ScoredChunk(chunk=c_a, score=0.9),
            ScoredChunk(chunk=c_b, score=0.5),
            ScoredChunk(chunk=c_c, score=0.3),
        ]
        list2 = [
            ScoredChunk(chunk=c_a, score=0.8),
            ScoredChunk(chunk=c_c, score=0.6),
            ScoredChunk(chunk=c_b, score=0.4),
        ]
        result = reciprocal_rank_fusion([list1, list2])
        # c_a is rank 0 in both lists → highest RRF score
        assert result[0].chunk.source == "a.md"

    def test_disjoint_lists_merge(self) -> None:
        """Non-overlapping lists should both contribute results."""
        c_a = _make_chunk("only in list1", "a.md", 0)
        c_b = _make_chunk("only in list2", "b.md", 0)

        list1 = [ScoredChunk(chunk=c_a, score=0.9)]
        list2 = [ScoredChunk(chunk=c_b, score=0.9)]

        result = reciprocal_rank_fusion([list1, list2])
        assert len(result) == 2

    def test_empty_lists_return_empty(self) -> None:
        result = reciprocal_rank_fusion([[], []])
        assert result == []

    def test_one_empty_one_nonempty(self) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        result = reciprocal_rank_fusion(
            [
                [ScoredChunk(chunk=c_a, score=0.5)],
                [],
            ]
        )
        assert len(result) == 1
        assert result[0].chunk.source == "a.md"

    def test_rrf_scores_are_positive(self) -> None:
        c_a = _make_chunk("alpha", "a.md", 0)
        ranked = [ScoredChunk(chunk=c_a, score=0.9)]
        result = reciprocal_rank_fusion([ranked])
        assert result[0].score > 0
        assert result[0].score == pytest.approx(1.0)

    def test_k_parameter_affects_scores(self) -> None:
        c_a = _make_chunk("alpha", "a.md", 0)
        c_b = _make_chunk("beta", "b.md", 0)
        ranked = [
            ScoredChunk(chunk=c_a, score=0.9),
            ScoredChunk(chunk=c_b, score=0.5),
        ]
        r1 = reciprocal_rank_fusion([ranked], k=1)
        r2 = reciprocal_rank_fusion([ranked], k=100)
        # Higher k flattens scores - gap should be smaller
        gap1 = r1[0].score - r1[1].score
        gap2 = r2[0].score - r2[1].score
        assert gap1 > gap2

    def test_weights_change_fusion_order(self) -> None:
        c_sparse = _make_chunk("sparse top", "sparse.md", 0)
        c_dense = _make_chunk("dense top", "dense.md", 0)
        sparse = [ScoredChunk(chunk=c_sparse, score=1.0)]
        dense = [ScoredChunk(chunk=c_dense, score=1.0)]

        result = reciprocal_rank_fusion([sparse, dense], weights=[1.0, 2.0])

        assert result[0].chunk.source == "dense.md"

    def test_weights_must_match_ranked_lists(self) -> None:
        with pytest.raises(ValueError, match="weights"):
            reciprocal_rank_fusion([[]], weights=[1.0, 1.0])


# ---------------------------------------------------------------------------
# Embedding retriever (mocked - no real model download)
# ---------------------------------------------------------------------------


class _MockArray:
    """Minimal mock that supports ``tolist()`` and indexing, simulating a numpy array.

    ``tolist()`` on the outer array returns the raw rows (list of list[float]).
    ``tolist()`` on an element (after __getitem__) returns the flat float list.
    This mirrors numpy behaviour where ``arr.tolist()`` gives ``[[...], ...]``
    but ``arr[0].tolist()`` gives ``[...]``.
    """

    def __init__(self, rows: list[list[float]] | list[float]) -> None:
        self._rows = rows

    def tolist(self):
        return self._rows

    def __getitem__(self, idx: int) -> _MockArray:
        return _MockArray(self._rows[idx])  # ty:ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# Hybrid retriever
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cross-encoder re-ranker (mocked - no real model download)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Hybrid retriever with re-ranker
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Auto-selection factory
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# min_score threshold filtering
# ---------------------------------------------------------------------------


class TestMinScoreThreshold:
    def test_filters_below_threshold(self) -> None:
        chunks = [
            _make_chunk("Python programming language basics.", "py.md", 0),
            _make_chunk("Cooking recipes for beginners.", "cook.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        # TF-IDF: "python" only matches the first chunk, second scores 0
        all_results = retrieve("python", index, min_score=0.0)
        assert len(all_results) == 1  # only py.md matches at all
        # Now use a threshold that filters it
        high_threshold = retrieve("python", index, min_score=1.0)
        assert high_threshold == []

    def test_all_below_threshold_returns_empty(self) -> None:
        chunks = [
            _make_chunk("Cooking recipes.", "cook.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        # "quantum" shares no tokens with "cooking" - scores will be ~0
        results = retrieve("quantum physics", index, min_score=0.5)
        assert results == []

    def test_zero_threshold_is_no_op(self) -> None:
        chunks = [
            _make_chunk("Python programming.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        results = retrieve("python", index, min_score=0.0)
        assert len(results) > 0

    def test_default_threshold_is_zero(self) -> None:
        chunks = [
            _make_chunk("Python programming.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        # Default min_score=0.0 - all results returned
        results = retrieve("python", index)
        assert len(results) > 0

    def test_threshold_keeps_exact_match(self) -> None:
        chunks = [
            _make_chunk("Python programming language.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        results = retrieve("python programming", index, min_score=0.05)
        assert len(results) > 0

    def test_source_path_match_can_rescue_material_named_query(self) -> None:
        chunks = [
            _make_chunk(
                "Clock distribution and timing diagrams help practical debugging.",
                "materials/mit-ocw-digital-systems-project-howto.pdf",
                0,
            ),
            _make_chunk(
                "A Java method overloading example with recursion.",
                "materials/java-repetitorium.pdf",
                0,
            ),
        ]
        index = _make_index_with_chunks(chunks)
        results = retrieve("digital systems project how-to", index, min_score=0.1)

        assert results
        assert results[0].chunk.source == "materials/mit-ocw-digital-systems-project-howto.pdf"

    def test_quoted_title_hint_breaks_repeated_navigation_tie(self) -> None:
        chunks = [
            _make_chunk(
                "1.5 Local Search | Introduction to Artificial Intelligence",
                "materials/public-academic/uc-berkeley-cs188/search/local.html",
                0,
            ),
            _make_chunk(
                "2.5 Local Search | Introduction to Artificial Intelligence",
                "materials/public-academic/uc-berkeley-cs188/csp/local-search.html",
                0,
            ),
        ]
        index = _make_index_with_chunks(chunks)
        results = retrieve(
            'Which material titled "2.5 Local Search | Introduction to Artificial '
            'Intelligence" covers constraint satisfaction?',
            index,
            top_k=2,
        )

        assert results[0].chunk.source.endswith("csp/local-search.html")

    def test_source_section_hint_breaks_repeated_title_tie(self) -> None:
        chunks = [
            _make_chunk(
                "CS231n Deep Learning for Computer Vision Course Website",
                "materials/public-academic/stanford-cs231n/neural-networks-2/index.html",
                0,
            ),
            _make_chunk(
                "CS231n Deep Learning for Computer Vision Course Website",
                "materials/public-academic/stanford-cs231n/neural-networks-1/index.html",
                0,
            ),
        ]
        index = _make_index_with_chunks(chunks)
        results = retrieve(
            'Which material titled "CS231n Deep Learning for Computer Vision" '
            'at source section "stanford-cs231n/neural-networks-1" covers computer vision?',
            index,
            top_k=2,
        )

        assert results[0].chunk.source.endswith("neural-networks-1/index.html")
