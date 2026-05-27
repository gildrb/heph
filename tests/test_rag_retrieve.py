"""Tests for the retriever protocol, embedding retriever, and hybrid retriever."""

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import hephaion.rag.sparse as sparse_module
from hephaion.rag.chunker import Chunk, ChunkedDocument
from hephaion.rag.index import ArmoryIndex
from hephaion.rag.query_transform import TransformStrategy
from hephaion.rag.retrieve import (
    Bm25Retriever,
    CrossEncoderReranker,
    DocumentBm25Retriever,
    EmbeddingRetriever,
    HybridRetriever,
    RerankerProtocol,
    RetrievalMode,
    RetrieverProtocol,
    ScoredChunk,
    TfidfRetriever,
    _apply_negation_precision_penalty,
    _compound_query_variants,
    _create_retriever,
    _expand_query_with_corpus_token_variants,
    _normalize_query_for_retrieval,
    retrieve,
)
from hephaion.rag.scoring import (
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
                "study.md",
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

    assert [result.chunk.source for result in reranked] == ["study.md", "biochem.md"]
    assert reranked[0].score == 0.9


def test_negation_precision_penalty_preserves_abstention_queries() -> None:
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
        "What should a grounded tutor do when the source lacks the answer?",
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
    retrieve_module = import_module("hephaion.rag.retrieve")
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


class TestRetrieverProtocol:
    def test_tfidf_satisfies_protocol(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello world")])
        assert isinstance(TfidfRetriever(index), RetrieverProtocol)

    def test_document_bm25_satisfies_protocol(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello world")])
        assert isinstance(DocumentBm25Retriever(index), RetrieverProtocol)

    def test_embedding_satisfies_protocol(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello world")])
        assert isinstance(EmbeddingRetriever(index), RetrieverProtocol)

    def test_hybrid_satisfies_protocol(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello world")])
        assert isinstance(HybridRetriever(index), RetrieverProtocol)

    def test_plain_object_does_not_satisfy(self) -> None:
        assert not isinstance(object(), RetrieverProtocol)

    def test_cross_encoder_reranker_satisfies_reranker_protocol(self) -> None:
        reranker = CrossEncoderReranker()
        assert isinstance(reranker, RerankerProtocol)

    def test_plain_object_does_not_satisfy_reranker_protocol(self) -> None:
        assert not isinstance(object(), RerankerProtocol)


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

    def test_sklearn_token_pattern_matches_words(self) -> None:
        captured: dict[str, str] = {}

        class FakeVectorizer:
            def __init__(self, **kwargs: str) -> None:
                captured["token_pattern"] = kwargs["token_pattern"]

            def fit_transform(self, _texts: object) -> object:
                return object()

        chunks = [_make_chunk("Python programming language", "python.md", 0)]
        index = _make_index_with_chunks(chunks)

        with (
            patch("hephaion.rag.optional_backends.HAS_SKLEARN", True),
            patch("hephaion.rag.optional_backends.SKLEARN_TFIDF_VECTORIZER", FakeVectorizer),
        ):
            TfidfRetriever(index)

        assert re.findall(captured["token_pattern"], "Python programming") == [
            "Python",
            "programming",
        ]

    def test_idf_state_saved_and_reused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chunks = [
            _make_chunk("Python is a programming language.", "python.md", 0),
            _make_chunk("Rust ownership and borrowing.", "rust.md", 0),
        ]
        index = _make_index_with_chunks_at(tmp_path, chunks)
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "HAS_SKLEARN", False)

        TfidfRetriever(index)
        state_path = tmp_path / ".hephaion" / f"retriever_{index.content_hash}_tfidf_v8.json"

        assert state_path.is_file()
        with patch.object(
            TfidfRetriever,
            "_build_idf",
            side_effect=AssertionError("cached IDF state should be reused"),
        ):
            retriever = TfidfRetriever(index)

        assert retriever.retrieve("python")


class TestBm25Retriever:
    def test_uses_bm25_backend_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
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
                assert k == 2
                assert show_progress is False
                return [[1, 0]], [[3.0, 1.0]]

        chunks = [
            _make_chunk("Python is a programming language.", "python.md", 0),
            _make_chunk("Rust ownership and borrowing.", "rust.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", FakeBm25)

        retriever = Bm25Retriever(index)
        results = retriever.retrieve("ownership", top_k=2)

        assert retriever.available
        assert [result.chunk.source for result in results] == ["rust.md", "python.md"]

    def test_empty_token_corpus_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class ExplodingBm25:
            def index(self, _corpus_tokens: list[list[str]], *, _show_progress: bool) -> object:
                raise AssertionError("empty token corpus should not be indexed")

        index = _make_index_with_chunks([_make_chunk("a I to the", "empty.md", 0)])
        retrieve_module = import_module("hephaion.rag.optional_backends")
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
        retrieve_module = import_module("hephaion.rag.optional_backends")
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
        retrieve_module = import_module("hephaion.rag.optional_backends")
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
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", FakeBm25)

        Bm25Retriever(index)
        state_path = tmp_path / ".hephaion" / f"retriever_{index.content_hash}_bm25_tokens_v8.json"

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
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        retriever = Bm25Retriever(index)
        results = retriever.retrieve(
            "CS231n Deep Learning for Computer Vision at source section "
            '"stanford-cs231n/neural-networks-1"',
            top_k=2,
        )

        assert results[0].chunk.source.endswith("neural-networks-1/index.html")


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
        retrieve_module = import_module("hephaion.rag.optional_backends")
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
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        retriever = DocumentBm25Retriever(index)

        assert retriever.retrieve("sentinel phrase")[0].chunk.source == "materials/doc.md"

    def test_uses_bm25_backend_cache_without_tokenizing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class FakeBm25:
            @classmethod
            def load(cls, _cache_dir: Path, *, load_corpus: bool, mmap: bool) -> FakeBm25:
                assert load_corpus is False
                assert mmap is True
                return cls()

            def retrieve(
                self,
                _query_tokens: list[list[str]],
                *,
                k: int,
                show_progress: bool,
            ) -> tuple[object, object]:
                assert k == 1
                assert show_progress is False
                return [[0]], [[2.0]]

        chunk = _make_chunk("alpha beta", "materials/doc.md", 0)
        index = _make_index_with_chunks_at(tmp_path, [chunk])
        cache_dir = tmp_path / ".hephaion" / f"retriever_{index.content_hash}_bm25s_document_v1"
        cache_dir.mkdir(parents=True)
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", FakeBm25)
        originaltokenize = sparse_module.tokenize

        def failtokenize(_text: str) -> list[str]:
            raise AssertionError("backend cache should avoid rebuilding document tokens")

        monkeypatch.setattr(sparse_module, "tokenize", failtokenize)
        retriever = DocumentBm25Retriever(index)
        monkeypatch.setattr(sparse_module, "tokenize", originaltokenize)

        assert retriever.available
        assert retriever.retrieve("alpha")[0].chunk.source == "materials/doc.md"


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
        # Higher k flattens scores — gap should be smaller
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
# Embedding retriever (mocked — no real model download)
# ---------------------------------------------------------------------------


class TestEmbeddingRetriever:
    def _make_retriever_with_mock(
        self,
        chunks: list[Chunk],
        query_embedding: list[float],
        chunk_embeddings: list[list[float]],
    ) -> EmbeddingRetriever:
        """Create an EmbeddingRetriever with a mocked sentence-transformers model."""
        index = _make_index_with_chunks(chunks)
        retriever = EmbeddingRetriever(index)

        # Pre-set embeddings so _ensure_embeddings never calls the model
        retriever._embeddings = chunk_embeddings

        mock_model = MagicMock()
        # encode([query], ...) must return something whose [0].tolist() gives a list[float]
        mock_model.encode.return_value = _MockArray([query_embedding])

        retriever._model = mock_model
        return retriever

    def test_empty_index(self) -> None:
        index = ArmoryIndex(Path("/fake"))
        retriever = EmbeddingRetriever(index)
        retriever._model = MagicMock()
        results = retriever.retrieve("anything")
        assert results == []

    def test_retrieve_by_similarity(self) -> None:
        c_a = _make_chunk("Python programming", "a.md", 0)
        c_b = _make_chunk("Cooking recipes", "b.md", 0)

        # Chunk embeddings: a is close to query, b is far
        retriever = self._make_retriever_with_mock(
            chunks=[c_a, c_b],
            query_embedding=[1.0, 0.0, 0.0],
            chunk_embeddings=[[0.9, 0.1, 0.0], [0.0, 0.1, 0.9]],
        )
        results = retriever.retrieve("Python programming")
        assert len(results) >= 1
        # First result must be the Python chunk (highest similarity)
        assert results[0].chunk.source == "a.md"
        # Scores must be descending
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_limit(self) -> None:
        chunks = [_make_chunk(f"doc {i}", f"d{i}.md", 0) for i in range(5)]
        embeddings = [[float(i == j) for j in range(5)] for i in range(5)]

        retriever = self._make_retriever_with_mock(
            chunks=chunks,
            query_embedding=[0.5, 0.5, 0.5, 0.5, 0.5],
            chunk_embeddings=embeddings,
        )
        results = retriever.retrieve("test", top_k=2)
        assert len(results) == 2

    def test_zero_similarity_excluded(self) -> None:
        c_a = _make_chunk("orthogonal", "a.md", 0)

        retriever = self._make_retriever_with_mock(
            chunks=[c_a],
            query_embedding=[1.0, 0.0],
            chunk_embeddings=[[0.0, 1.0]],  # orthogonal → sim = 0
        )
        results = retriever.retrieve("test")
        assert results == []

    def test_model_name_default(self) -> None:
        index = ArmoryIndex(Path("/fake"))
        retriever = EmbeddingRetriever(index)
        assert retriever._model_name == "all-MiniLM-L6-v2"

    def test_model_name_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAION_EMBED_MODEL", "custom-model-v2")
        index = ArmoryIndex(Path("/fake"))
        retriever = EmbeddingRetriever(index)
        assert retriever._model_name == "custom-model-v2"

    def test_model_name_from_constructor(self) -> None:
        index = ArmoryIndex(Path("/fake"))
        retriever = EmbeddingRetriever(index, model_name="my-model")
        assert retriever._model_name == "my-model"

    def test_query_prefix_applied_to_query_embedding(self) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        index = _make_index_with_chunks([c_a])
        retriever = EmbeddingRetriever(index, query_prefix="query: ")

        mock_model = MagicMock()
        mock_model.encode.side_effect = [
            _MockArray([[1.0, 0.0]]),
            _MockArray([[1.0, 0.0]]),
        ]
        retriever._model = mock_model

        retriever.retrieve("hello")

        assert mock_model.encode.call_args_list[1].args[0] == ["query: hello"]

    def test_document_prefix_applied_to_chunk_embeddings(self) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        index = _make_index_with_chunks([c_a])
        retriever = EmbeddingRetriever(index, document_prefix="passage: ")

        mock_model = MagicMock()
        mock_model.encode.side_effect = [
            _MockArray([[1.0, 0.0]]),
            _MockArray([[1.0, 0.0]]),
        ]
        retriever._model = mock_model

        retriever.retrieve("hello")

        assert mock_model.encode.call_args_list[0].args[0] == ["passage: hello\na.md"]
        assert mock_model.encode.call_args_list[1].args[0] == ["hello"]

    def test_document_prefix_changes_embedding_cache_key(self) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        index = _make_index_with_chunks([c_a])
        retriever = EmbeddingRetriever(
            index,
            model_name="fixture-embed-model",
            document_prefix="passage: ",
        )

        mock_model = MagicMock()
        mock_model.encode.return_value = _MockArray([[0.1, 0.2, 0.3]])
        retriever._model = mock_model

        expected_cache_key = "fixture-embed-model\ndocument_prefix=passage: "
        with (
            patch.object(index, "load_embeddings", return_value=None) as load_embeddings,
            patch.object(index, "save_embeddings") as save_embeddings,
        ):
            retriever._ensure_embeddings()

        assert load_embeddings.call_args.kwargs["cache_key"] == expected_cache_key
        assert save_embeddings.call_args.kwargs["cache_key"] == expected_cache_key

    def test_embedding_cache_separates_document_prefixes(self, tmp_path: Path) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        index = _make_index_with_chunks_at(tmp_path, [c_a])

        default_path = index.save_embeddings([[1.0, 0.0]], "fixture-embed-model")
        prefixed_path = index.save_embeddings(
            [[0.0, 1.0]],
            "fixture-embed-model",
            cache_key="fixture-embed-model\ndocument_prefix=passage: ",
        )

        assert default_path is not None
        assert prefixed_path is not None
        assert default_path != prefixed_path
        assert index.load_embeddings("fixture-embed-model") == [[1.0, 0.0]]
        assert index.load_embeddings(
            "fixture-embed-model",
            cache_key="fixture-embed-model\ndocument_prefix=passage: ",
        ) == [[0.0, 1.0]]

    def test_embeddings_cached(self) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        index = _make_index_with_chunks([c_a])
        retriever = EmbeddingRetriever(index)

        mock_model = MagicMock()
        mock_model.encode.return_value = _MockArray([[0.1, 0.2, 0.3]])
        retriever._model = mock_model

        # Call twice — encode should only be called once for chunks
        retriever._ensure_embeddings()
        retriever._ensure_embeddings()
        assert mock_model.encode.call_count == 1


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


class TestHybridRetriever:
    def test_falls_back_to_tfidf_when_no_embeddings(self) -> None:
        chunks = [
            _make_chunk("Python programming language", "a.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index)
            assert hybrid._embedding is None
            assert not hybrid.has_embeddings

            results = hybrid.retrieve("python")
            assert len(results) == 1
            assert results[0].chunk.source == "a.md"

    def test_has_embeddings_when_available(self) -> None:
        chunks = [_make_chunk("hello", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=True,
        ):
            hybrid = HybridRetriever(index)
            # EmbeddingRetriever.__init__ doesn't load the model (lazy),
            # so has_embeddings should be True
            assert hybrid.has_embeddings

    def test_embedding_init_failure_graceful(self) -> None:
        """If EmbeddingRetriever raises during init, hybrid falls back."""
        chunks = [_make_chunk("hello", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                side_effect=ImportError("no torch"),
            ),
        ):
            hybrid = HybridRetriever(index)
            assert hybrid._embedding is None
            assert not hybrid.has_embeddings

    def test_tfidf_only_returns_results(self) -> None:
        chunks = [
            _make_chunk("Python is a programming language.", "py.md", 0),
            _make_chunk("Rust is a systems language.", "rs.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index)
            results = hybrid.retrieve("python programming")
            assert len(results) > 0
            assert results[0].chunk.source == "py.md"

    def test_hybrid_merges_both_retrievers(self) -> None:
        """When embedding retriever returns results, hybrid merges via RRF."""
        chunks = [
            _make_chunk("Python programming", "a.md", 0),
            _make_chunk("Rust systems", "b.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.95),
            ScoredChunk(chunk=chunks[1], score=0.3),
        ]

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
        ):
            hybrid = HybridRetriever(index)
            assert hybrid._embedding is mock_embed

            results = hybrid.retrieve("python")
            assert len(results) > 0
            # a.md should rank highest (it's top in both TF-IDF and embeddings)
            assert results[0].chunk.source == "a.md"

    def test_mode_specific_transformer_routes_sparse_and_dense_queries(self) -> None:
        chunks = [
            _make_chunk("sparse match", "sparse.md", 0),
            _make_chunk("dense match", "dense.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        class StubModeSpecificTransformer:
            def transform(self, query: str) -> list[str]:
                return [query]

            def transform_sparse(self, _query: str) -> list[str]:
                return ["keyword bag", "expanded keyword bag"]

            def transform_dense(self, _query: str) -> list[str]:
                return ["natural language description"]

        hybrid = HybridRetriever(
            index,
            candidate_multiplier=3,
            query_transformer=StubModeSpecificTransformer(),
        )
        sparse = MagicMock()
        sparse.retrieve.side_effect = [
            [ScoredChunk(chunk=chunks[0], score=1.0)],
            [ScoredChunk(chunk=chunks[1], score=0.5)],
        ]
        dense = MagicMock()
        dense.retrieve.return_value = [ScoredChunk(chunk=chunks[1], score=1.0)]
        hybrid._sparse = sparse
        hybrid._embedding = dense

        results = hybrid.retrieve("original query", top_k=2)

        assert [call.args for call in sparse.retrieve.call_args_list] == [
            ("keyword bag", 6),
            ("expanded keyword bag", 6),
        ]
        dense.retrieve.assert_called_once_with("natural language description", top_k=6)
        assert {result.chunk.source for result in results} == {"sparse.md", "dense.md"}

    def test_pseudo_feedback_adds_expanded_sparse_list(self) -> None:
        chunks = [
            _make_chunk("alpha rareterm citation clue", "seed.md", 0),
            _make_chunk("rareterm answer", "target.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        hybrid = HybridRetriever(index, pseudo_feedback=True)
        hybrid._embedding = None

        sparse = MagicMock()

        def fake_sparse_retrieve(query: str, top_k: int = 5) -> list[ScoredChunk]:
            del top_k
            if "rareterm" in query and query != "alpha":
                return [ScoredChunk(chunk=chunks[1], score=2.0)]
            return [ScoredChunk(chunk=chunks[0], score=1.0)]

        sparse.retrieve.side_effect = fake_sparse_retrieve
        hybrid._sparse = sparse

        results = hybrid.retrieve("alpha", top_k=2)

        assert {result.chunk.source for result in results} == {"seed.md", "target.md"}
        assert sparse.retrieve.call_count == 2
        feedback_query = sparse.retrieve.call_args_list[1].args[0]
        assert feedback_query.startswith("alpha ")
        assert "rareterm" in feedback_query

    def test_pseudo_feedback_prefers_distinctive_terms_over_repeated_boilerplate(
        self,
    ) -> None:
        chunks = [
            _make_chunk(
                "alpha common common common raretarget raretarget",
                "seed.md",
                0,
            ),
            _make_chunk("common filler", "common-a.md", 0),
            _make_chunk("common another", "common-b.md", 0),
            _make_chunk("common third", "common-c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        hybrid = HybridRetriever(index, pseudo_feedback=True, pseudo_feedback_terms=1)

        feedback_query = hybrid._feedback_query(
            "alpha",
            [ScoredChunk(chunk=chunks[0], score=1.0)],
        )

        assert feedback_query == "alpha raretarget"

    def test_empty_results_from_both(self) -> None:
        chunks = [_make_chunk("unrelated", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = []

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
        ):
            hybrid = HybridRetriever(index)
            # Query has zero TF-IDF overlap, embeddings also return nothing
            results = hybrid.retrieve("zzzzzzzz quantum xyz")
            assert results == []

    def test_respects_top_k(self) -> None:
        chunks = [_make_chunk(f"doc {i}", f"d{i}.md", 0) for i in range(10)]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[i], score=float(10 - i) / 10) for i in range(10)
        ]

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
        ):
            hybrid = HybridRetriever(index)
            results = hybrid.retrieve("doc", top_k=3)
            assert len(results) <= 3


# ---------------------------------------------------------------------------
# Cross-encoder re-ranker (mocked — no real model download)
# ---------------------------------------------------------------------------


class TestCrossEncoderReranker:
    def _make_reranker_with_mock(
        self,
        predict_scores: list[float],
    ) -> CrossEncoderReranker:
        """Create a CrossEncoderReranker with a mocked CrossEncoder model."""
        reranker = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = predict_scores
        reranker._model = mock_model
        return reranker

    def test_empty_candidates(self) -> None:
        reranker = self._make_reranker_with_mock([])
        results = reranker.rerank("test", [])
        assert results == []

    def test_rerank_rescores_and_sorts(self) -> None:
        """Cross-encoder scores replace original scores; results sorted desc."""
        c_a = _make_chunk("Python programming language", "a.md", 0)
        c_b = _make_chunk("Cooking recipes", "b.md", 0)
        c_c = _make_chunk("Rust systems programming", "c.md", 0)

        candidates = [
            ScoredChunk(chunk=c_a, score=0.9),  # was top by TF-IDF
            ScoredChunk(chunk=c_b, score=0.5),
            ScoredChunk(chunk=c_c, score=0.3),
        ]

        # Cross-encoder says: c (Rust) is most relevant, then a, then b
        reranker = self._make_reranker_with_mock([0.6, 0.1, 0.95])

        results = reranker.rerank("systems programming language", candidates, top_k=3)
        assert len(results) == 3
        # New ordering: c (0.95) > a (0.6) > b (0.1)
        assert results[0].chunk.source == "c.md"
        assert results[0].score == pytest.approx(1.0)
        assert results[1].chunk.source == "a.md"
        assert results[2].chunk.source == "b.md"
        assert results[0].score > results[1].score > results[2].score

    def test_rerank_respects_top_k(self) -> None:
        c_a = _make_chunk("doc a", "a.md", 0)
        c_b = _make_chunk("doc b", "b.md", 0)
        c_c = _make_chunk("doc c", "c.md", 0)
        c_d = _make_chunk("doc d", "d.md", 0)

        candidates = [
            ScoredChunk(chunk=c_a, score=0.9),
            ScoredChunk(chunk=c_b, score=0.7),
            ScoredChunk(chunk=c_c, score=0.5),
            ScoredChunk(chunk=c_d, score=0.3),
        ]

        reranker = self._make_reranker_with_mock([0.4, 0.8, 0.6, 0.2])
        results = reranker.rerank("test", candidates, top_k=2)
        assert len(results) == 2
        assert results[0].chunk.source == "b.md"
        assert results[1].chunk.source == "c.md"

    def test_scores_are_normalized_cross_encoder_scores(self) -> None:
        """Original retrieval scores are replaced by normalized cross-encoder scores."""
        c_a = _make_chunk("hello", "a.md", 0)
        candidates = [ScoredChunk(chunk=c_a, score=0.1)]

        reranker = self._make_reranker_with_mock([0.99])
        results = reranker.rerank("test", candidates, top_k=5)
        assert results[0].score == pytest.approx(1.0)

    def test_negative_model_scores_are_normalized_relative_to_best(self) -> None:
        c_a = _make_chunk("most relevant", "a.md", 0)
        c_b = _make_chunk("less relevant", "b.md", 0)
        candidates = [
            ScoredChunk(chunk=c_a, score=0.9),
            ScoredChunk(chunk=c_b, score=0.8),
        ]

        reranker = self._make_reranker_with_mock([-8.0, -9.0])
        results = reranker.rerank("test", candidates, top_k=2)

        assert [result.chunk.source for result in results] == ["a.md", "b.md"]
        assert results[0].score == pytest.approx(1.0)
        assert 0.0 < results[1].score < results[0].score

    def test_model_name_default(self) -> None:
        reranker = CrossEncoderReranker()
        assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def test_model_name_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAION_RERANK_MODEL", "my-custom-reranker")
        reranker = CrossEncoderReranker()
        assert reranker.model_name == "my-custom-reranker"

    def test_model_name_from_constructor(self) -> None:
        reranker = CrossEncoderReranker(model_name="other-model")
        assert reranker.model_name == "other-model"

    def test_model_lazy_loaded(self) -> None:
        """Model is not loaded at construction time."""
        reranker = CrossEncoderReranker()
        assert reranker._model is None

    def test_model_cached_after_first_use(self) -> None:
        reranker = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5]
        reranker._model = mock_model

        c_a = _make_chunk("hello", "a.md", 0)
        candidates = [ScoredChunk(chunk=c_a, score=0.1)]

        reranker.rerank("test", candidates)
        reranker.rerank("test", candidates)
        # predict called twice (once per rerank call), but model was set once
        assert mock_model.predict.call_count == 2

    def test_predict_receives_query_text_pairs(self) -> None:
        """Cross-encoder receives (query, chunk_text) pairs."""
        reranker = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5, 0.3]
        reranker._model = mock_model

        c_a = _make_chunk("Python code", "a.md", 0)
        c_b = _make_chunk("Rust code", "b.md", 0)
        candidates = [
            ScoredChunk(chunk=c_a, score=0.9),
            ScoredChunk(chunk=c_b, score=0.5),
        ]

        reranker.rerank("programming", candidates)
        call_args = mock_model.predict.call_args[0][0]
        assert call_args == [
            ("programming", "Python code\na.md"),
            ("programming", "Rust code\nb.md"),
        ]


# ---------------------------------------------------------------------------
# Hybrid retriever with re-ranker
# ---------------------------------------------------------------------------


class TestHybridRetrieverWithReranker:
    def test_reranker_applied_after_rrf_fusion(self) -> None:
        """Full pipeline: TF-IDF + embeddings → RRF → cross-encoder re-rank."""
        chunks = [
            _make_chunk("Python programming", "a.md", 0),
            _make_chunk("Rust systems", "b.md", 0),
            _make_chunk("Cooking recipes", "c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        # Mock embedding retriever
        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.9),
            ScoredChunk(chunk=chunks[1], score=0.5),
        ]

        # Mock cross-encoder reranker — flip the order
        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        mock_reranker.rerank.side_effect = lambda _query, _candidates, top_k=5: [
            ScoredChunk(chunk=chunks[1], score=0.99),
            ScoredChunk(chunk=chunks[0], score=0.7),
        ][:top_k]

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
        ):
            hybrid = HybridRetriever(index, reranker=mock_reranker)
            results = hybrid.retrieve("programming", top_k=3)

            # Reranker was called with the fused candidates
            mock_reranker.rerank.assert_called_once()
            call_args = mock_reranker.rerank.call_args
            assert call_args[0][0] == "programming"  # query
            assert call_args[1]["top_k"] == 3

            # Results reflect reranker's ordering
            assert results[0].chunk.source == "b.md"
            assert results[0].score == 0.99
            assert results[1].chunk.source == "a.md"
            assert results[1].score == 0.7

    def test_reranker_not_called_when_no_results(self) -> None:
        """If retrieval returns nothing, reranker is not invoked."""
        chunks = [_make_chunk("unrelated", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        mock_reranker = MagicMock(spec=CrossEncoderReranker)

        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, reranker=mock_reranker)
            results = hybrid.retrieve("zzzzzzz quantum xyz")
            assert results == []
            mock_reranker.rerank.assert_not_called()

    def test_tfidf_only_with_reranker(self) -> None:
        """When no embeddings, TF-IDF over-fetches so reranker has a pool."""
        chunks = [
            _make_chunk("Python programming language", "a.md", 0),
            _make_chunk("Python scripting automation", "b.md", 0),
            _make_chunk("Cooking with Python beans", "c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        mock_reranker.rerank.return_value = [
            ScoredChunk(chunk=chunks[1], score=0.95),
            ScoredChunk(chunk=chunks[0], score=0.8),
        ]

        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, reranker=mock_reranker)
            results = hybrid.retrieve("python scripting", top_k=2)

            # Reranker was called with over-fetched pool
            mock_reranker.rerank.assert_called_once()
            call_args = mock_reranker.rerank.call_args
            # The pool should have > top_k candidates
            candidates_arg = call_args[0][1]
            assert len(candidates_arg) > 2  # over-fetched
            assert call_args[1]["top_k"] == 2

            assert len(results) == 2
            assert results[0].chunk.source == "b.md"

    def test_tfidf_only_without_reranker_same_behavior(self) -> None:
        """Without reranker, TF-IDF-only path behaves as before."""
        chunks = [
            _make_chunk("Python is a programming language.", "py.md", 0),
            _make_chunk("Rust is a systems language.", "rs.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index)
            results = hybrid.retrieve("python programming")
            assert len(results) > 0
            assert results[0].chunk.source == "py.md"

    def test_reranker_over_fetch_respects_top_k(self) -> None:
        """Reranker receives full candidate pool but returns exactly top_k."""
        chunks = [_make_chunk(f"doc {i}", f"d{i}.md", 0) for i in range(10)]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[i], score=float(10 - i) / 10) for i in range(10)
        ]

        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        mock_reranker.rerank.return_value = [
            ScoredChunk(chunk=chunks[i], score=float(i) / 10) for i in range(3)
        ]

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
        ):
            hybrid = HybridRetriever(index, reranker=mock_reranker)
            results = hybrid.retrieve("doc", top_k=3)
            assert len(results) == 3


# ---------------------------------------------------------------------------
# Auto-selection factory
# ---------------------------------------------------------------------------


class TestCreateRetriever:
    def test_returns_tfidf_when_no_embeddings(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            r = _create_retriever(index)
            assert isinstance(r, Bm25Retriever | TfidfRetriever)

    def test_returns_hybrid_when_embeddings_available(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=True,
        ):
            r = _create_retriever(index)
            assert isinstance(r, HybridRetriever)
            assert r.has_embeddings

    def test_hybrid_prf_mode_enables_pseudo_feedback(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=True,
        ):
            r = _create_retriever(index, retrieval_mode=RetrievalMode.HYBRID_PRF)
            assert isinstance(r, HybridRetriever)
            assert r._pseudo_feedback is True

    def test_hybrid_prf_can_run_sparse_only(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=True,
        ):
            r = _create_retriever(
                index,
                retrieval_mode=RetrievalMode.HYBRID_PRF,
                hybrid_dense_weight=0.0,
            )
            assert isinstance(r, HybridRetriever)
            assert r._pseudo_feedback is True
            assert r.has_embeddings is False

    def test_returns_document_bm25_for_document_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        index = _make_index_with_chunks([_make_chunk("hello world", "doc.md", 0)])
        retrieve_module = import_module("hephaion.rag.optional_backends")
        monkeypatch.setattr(retrieve_module, "BM25_CLASS", None)

        r = _create_retriever(index, retrieval_mode=RetrievalMode.BM25_DOCUMENT)

        assert isinstance(r, DocumentBm25Retriever)

    def test_reranker_creation_failure_still_returns_hybrid(self) -> None:
        """If CrossEncoderReranker fails, hybrid still works without it."""
        index = _make_index_with_chunks([_make_chunk("hello")])
        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.retrieve.CrossEncoderReranker",
                side_effect=ImportError("no cross-encoder"),
            ),
        ):
            r = _create_retriever(index)
            assert isinstance(r, HybridRetriever)
            assert r.has_embeddings

    def test_falls_back_to_tfidf_if_hybrid_init_fails(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                side_effect=ImportError("nope"),
            ),
        ):
            r = _create_retriever(index)
            assert isinstance(r, Bm25Retriever | TfidfRetriever)


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestRetrieveConvenience:
    def test_works_with_tfidf_fallback(self) -> None:
        chunks = [
            _make_chunk("Binary search runs in O(log n) time.", "algo.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve("binary search algorithm", index)
            assert len(results) > 0
            assert isinstance(results[0], ScoredChunk)

    def test_works_with_hybrid(self) -> None:
        chunks = [
            _make_chunk("Binary search runs in O(log n) time.", "algo.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.95),
        ]

        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        mock_reranker.rerank.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.99),
        ]

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
            patch(
                "hephaion.rag.retrieve.CrossEncoderReranker",
                return_value=mock_reranker,
            ),
        ):
            results = retrieve("binary search", index)
            assert len(results) > 0

    def test_hybrid_negative_rerank_scores_survive_min_score_filter(self) -> None:
        chunks = [
            _make_chunk("Binary search runs in O(log n) time.", "algo.md", 0),
            _make_chunk("Cooking notes for soups.", "cook.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.95),
            ScoredChunk(chunk=chunks[1], score=0.2),
        ]
        reranker = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [-8.0, -9.0]
        reranker._model = mock_model

        with (
            patch(
                "hephaion.rag.optional_backends.sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.retrieve._is_sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "hephaion.rag.hybrid.EmbeddingRetriever",
                return_value=mock_embed,
            ),
            patch(
                "hephaion.rag.retrieve.CrossEncoderReranker",
                return_value=reranker,
            ),
        ):
            results = retrieve("binary search", index, min_score=0.1)

        assert results
        assert results[0].chunk.source == "algo.md"
        assert results[0].score == pytest.approx(1.0)

    def test_overfetches_before_precision_adjustments(self) -> None:
        chunks = [
            _make_chunk("This is not the standard method.", "negative.md", 0),
            _make_chunk("This is the standard method.", "positive.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        class _OrderedRetriever:
            def __init__(self) -> None:
                self.calls: list[int] = []

            def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
                del query
                self.calls.append(top_k)
                return [
                    ScoredChunk(chunk=chunks[0], score=0.9),
                    ScoredChunk(chunk=chunks[1], score=0.8),
                ][:top_k]

        ordered_retriever = _OrderedRetriever()

        def fake_create_retriever(*_args: object, **_kwargs: object) -> _OrderedRetriever:
            return ordered_retriever

        with patch(
            "hephaion.rag.retrieve._create_retriever",
            side_effect=fake_create_retriever,
        ):
            results = retrieve("Which method is standard?", index, top_k=1)

        assert ordered_retriever.calls == [2]
        assert [result.chunk.source for result in results] == ["positive.md"]

    def test_caches_retrievers_per_transform_configuration(self) -> None:
        index = _make_index_with_chunks([_make_chunk("Binary search runs in O(log n) time.")])
        transformed_queries: list[list[str]] = []

        class _StubTransformer:
            def __init__(self, label: str) -> None:
                self._label = label

            def transform(self, query: str) -> list[str]:
                return [f"{self._label}:{query}"]

        class _StubRetriever:
            def __init__(self, transformer: object | None) -> None:
                self._transformer = transformer

            def retrieve(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
                del top_k
                if self._transformer is None:
                    transformed_queries.append([query])
                else:
                    transformer = self._transformer
                    transformed_queries.append(transformer.transform(query))  # ty:ignore[unresolved-attribute]
                return [ScoredChunk(chunk=index.all_chunks[0], score=1.0)]

        def prompt_fn(prompt: str) -> str:
            return prompt

        def fake_create_retriever(
            armory_index: ArmoryIndex,
            embed_model: str | None = None,
            embed_query_prefix: str = "",
            embed_document_prefix: str = "",
            rerank_model: str | None = None,
            query_transformer: object | None = None,
            retrieval_mode: object | None = None,
            candidate_multiplier: int = 3,
            hybrid_sparse_weight: float = 1.0,
            hybrid_dense_weight: float = 1.0,
            pseudo_feedback_docs: int = 3,
            pseudo_feedback_terms: int = 6,
            pseudo_feedback_weight: float = 0.2,
        ) -> _StubRetriever:
            del (
                armory_index,
                embed_model,
                embed_query_prefix,
                embed_document_prefix,
                rerank_model,
                retrieval_mode,
                candidate_multiplier,
                hybrid_sparse_weight,
                hybrid_dense_weight,
                pseudo_feedback_docs,
                pseudo_feedback_terms,
                pseudo_feedback_weight,
            )
            return _StubRetriever(query_transformer)

        with (
            patch(
                "hephaion.rag.retrieve.create_transformer",
                return_value=_StubTransformer("hyde"),
            ),
            patch(
                "hephaion.rag.retrieve._create_retriever",
                side_effect=fake_create_retriever,
            ) as mock_create_retriever,
        ):
            retrieve("binary search", index)
            retrieve(
                "binary search",
                index,
                transform_strategy=TransformStrategy.HYDE,
                prompt_fn=prompt_fn,
            )

        assert transformed_queries == [["binary search"], ["hyde:binary search"]]
        assert mock_create_retriever.call_count == 2


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
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
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
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            # "quantum" shares no tokens with "cooking" — scores will be ~0
            results = retrieve("quantum physics", index, min_score=0.5)
            assert results == []

    def test_zero_threshold_is_no_op(self) -> None:
        chunks = [
            _make_chunk("Python programming.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve("python", index, min_score=0.0)
            assert len(results) > 0

    def test_default_threshold_is_zero(self) -> None:
        chunks = [
            _make_chunk("Python programming.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            # Default min_score=0.0 — all results returned
            results = retrieve("python", index)
            assert len(results) > 0

    def test_threshold_keeps_exact_match(self) -> None:
        chunks = [
            _make_chunk("Python programming language.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
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
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
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
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
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
        with patch(
            "hephaion.rag.optional_backends.sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve(
                'Which material titled "CS231n Deep Learning for Computer Vision" '
                'at source section "stanford-cs231n/neural-networks-1" covers computer vision?',
                index,
                top_k=2,
            )

        assert results[0].chunk.source.endswith("neural-networks-1/index.html")
