"""Tests for the retriever protocol, embedding retriever, and hybrid retriever."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hephaistos.harness.rag.chunker import Chunk, ChunkedDocument
from hephaistos.harness.rag.index import ArmoryIndex
from hephaistos.harness.rag.retrieve import (
    CrossEncoderReranker,
    EmbeddingRetriever,
    HybridRetriever,
    RerankerProtocol,
    RetrieverProtocol,
    ScoredChunk,
    TfidfRetriever,
    _cosine_similarity,
    _create_retriever,
    _reciprocal_rank_fusion,
    _tokenize,
    retrieve,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(text: str, source: str = "test.md", index: int = 0) -> Chunk:
    return Chunk(text=text, source=source, index=index, char_start=0, char_end=len(text))


def _make_index_with_chunks(chunks: list[Chunk]) -> ArmoryIndex:
    """Build a minimal ArmoryIndex with the given chunks."""
    by_source: dict[str, list[Chunk]] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c)

    index = ArmoryIndex(Path("/fake"))
    for source, source_chunks in by_source.items():
        index.documents.append(ChunkedDocument(
            source=source,
            chunks=source_chunks,
            content_hash="fake",
        ))
    return index


# ---------------------------------------------------------------------------
# RetrieverProtocol
# ---------------------------------------------------------------------------


class TestRetrieverProtocol:
    def test_tfidf_satisfies_protocol(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello world")])
        assert isinstance(TfidfRetriever(index), RetrieverProtocol)

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
            _make_chunk(f"Document about topic number {i}.", f"doc{i}.md", 0)
            for i in range(10)
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


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


class TestTokenize:
    def test_splits_on_non_alnum(self) -> None:
        assert "python" in _tokenize("Python, is; great!")

    def test_removes_stop_words(self) -> None:
        tokens = _tokenize("the cat is on the mat")
        assert "the" not in tokens
        assert "cat" in tokens
        assert "mat" in tokens

    def test_removes_single_chars(self) -> None:
        tokens = _tokenize("a big c")
        assert "a" not in tokens
        assert "c" not in tokens
        assert "big" in tokens

    def test_lowercase(self) -> None:
        tokens = _tokenize("Python PYTHON python")
        assert tokens == ["python", "python", "python"]


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        assert abs(_cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9

    def test_orthogonal_vectors(self) -> None:
        assert abs(_cosine_similarity([1, 0], [0, 1])) < 1e-9

    def test_opposite_vectors(self) -> None:
        assert abs(_cosine_similarity([1, 0], [-1, 0]) - (-1.0)) < 1e-9

    def test_zero_vector(self) -> None:
        assert _cosine_similarity([0, 0], [1, 1]) == 0.0

    def test_arbitrary_vectors(self) -> None:
        # [1,2,3] · [4,5,6] = 32, |a|=√14, |b|=√77
        sim = _cosine_similarity([1, 2, 3], [4, 5, 6])
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
        result = _reciprocal_rank_fusion([ranked])
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
        result = _reciprocal_rank_fusion([list1, list2])
        # c_a is rank 0 in both lists → highest RRF score
        assert result[0].chunk.source == "a.md"

    def test_disjoint_lists_merge(self) -> None:
        """Non-overlapping lists should both contribute results."""
        c_a = _make_chunk("only in list1", "a.md", 0)
        c_b = _make_chunk("only in list2", "b.md", 0)

        list1 = [ScoredChunk(chunk=c_a, score=0.9)]
        list2 = [ScoredChunk(chunk=c_b, score=0.9)]

        result = _reciprocal_rank_fusion([list1, list2])
        assert len(result) == 2

    def test_empty_lists_return_empty(self) -> None:
        result = _reciprocal_rank_fusion([[], []])
        assert result == []

    def test_one_empty_one_nonempty(self) -> None:
        c_a = _make_chunk("hello", "a.md", 0)
        result = _reciprocal_rank_fusion([
            [ScoredChunk(chunk=c_a, score=0.5)],
            [],
        ])
        assert len(result) == 1
        assert result[0].chunk.source == "a.md"

    def test_rrf_scores_are_positive(self) -> None:
        c_a = _make_chunk("alpha", "a.md", 0)
        ranked = [ScoredChunk(chunk=c_a, score=0.9)]
        result = _reciprocal_rank_fusion([ranked])
        assert result[0].score > 0

    def test_k_parameter_affects_scores(self) -> None:
        c_a = _make_chunk("alpha", "a.md", 0)
        c_b = _make_chunk("beta", "b.md", 0)
        ranked = [
            ScoredChunk(chunk=c_a, score=0.9),
            ScoredChunk(chunk=c_b, score=0.5),
        ]
        r1 = _reciprocal_rank_fusion([ranked], k=1)
        r2 = _reciprocal_rank_fusion([ranked], k=100)
        # Higher k flattens scores — gap should be smaller
        gap1 = r1[0].score - r1[1].score
        gap2 = r2[0].score - r2[1].score
        assert gap1 > gap2


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
        monkeypatch.setenv("HEPHAISTOS_EMBED_MODEL", "custom-model-v2")
        index = ArmoryIndex(Path("/fake"))
        retriever = EmbeddingRetriever(index)
        assert retriever._model_name == "custom-model-v2"

    def test_model_name_from_constructor(self) -> None:
        index = ArmoryIndex(Path("/fake"))
        retriever = EmbeddingRetriever(index, model_name="my-model")
        assert retriever._model_name == "my-model"

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

    def __getitem__(self, idx: int) -> "_MockArray":
        return _MockArray(self._rows[idx])  # type: ignore[index]


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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
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

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            side_effect=ImportError("no torch"),
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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
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

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            return_value=mock_embed,
        ):
            hybrid = HybridRetriever(index)
            assert hybrid._embedding is mock_embed

            results = hybrid.retrieve("python")
            assert len(results) > 0
            # a.md should rank highest (it's top in both TF-IDF and embeddings)
            assert results[0].chunk.source == "a.md"

    def test_empty_results_from_both(self) -> None:
        chunks = [_make_chunk("unrelated", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = []

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            return_value=mock_embed,
        ):
            hybrid = HybridRetriever(index)
            # Query has zero TF-IDF overlap, embeddings also return nothing
            results = hybrid.retrieve("zzzzzzzz quantum xyz")
            assert results == []

    def test_respects_top_k(self) -> None:
        chunks = [
            _make_chunk(f"doc {i}", f"d{i}.md", 0) for i in range(10)
        ]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[i], score=float(10 - i) / 10)
            for i in range(10)
        ]

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            return_value=mock_embed,
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
        assert results[0].score == 0.95
        assert results[1].chunk.source == "a.md"
        assert results[1].score == 0.6
        assert results[2].chunk.source == "b.md"
        assert results[2].score == 0.1

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
        # b (0.8) > c (0.6)
        assert results[0].chunk.source == "b.md"
        assert results[1].chunk.source == "c.md"

    def test_scores_are_cross_encoder_scores(self) -> None:
        """Original retrieval scores are fully replaced by cross-encoder scores."""
        c_a = _make_chunk("hello", "a.md", 0)
        candidates = [ScoredChunk(chunk=c_a, score=0.1)]

        reranker = self._make_reranker_with_mock([0.99])
        results = reranker.rerank("test", candidates, top_k=5)
        assert results[0].score == 0.99

    def test_model_name_default(self) -> None:
        reranker = CrossEncoderReranker()
        assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def test_model_name_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HEPHAISTOS_RERANK_MODEL", "my-custom-reranker")
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
            ("programming", "Python code"),
            ("programming", "Rust code"),
        ]


# ---------------------------------------------------------------------------
# Hybrid retriever with re-ranker
# ---------------------------------------------------------------------------


class TestHybridRetrieverWithReranker:
    def test_reranker_property(self) -> None:
        chunks = [_make_chunk("hello", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        hybrid = HybridRetriever(index, reranker=mock_reranker)
        assert hybrid.has_reranker

    def test_no_reranker_property(self) -> None:
        chunks = [_make_chunk("hello", "a.md", 0)]
        index = _make_index_with_chunks(chunks)
        hybrid = HybridRetriever(index)
        assert not hybrid.has_reranker

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
        mock_reranker.rerank.side_effect = (
            lambda query, candidates, top_k=5: [
                ScoredChunk(chunk=chunks[1], score=0.99),
                ScoredChunk(chunk=chunks[0], score=0.7),
            ][:top_k]
        )

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            return_value=mock_embed,
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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index)
            results = hybrid.retrieve("python programming")
            assert len(results) > 0
            assert results[0].chunk.source == "py.md"

    def test_reranker_over_fetch_respects_top_k(self) -> None:
        """Reranker receives full candidate pool but returns exactly top_k."""
        chunks = [
            _make_chunk(f"doc {i}", f"d{i}.md", 0) for i in range(10)
        ]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[i], score=float(10 - i) / 10)
            for i in range(10)
        ]

        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        mock_reranker.rerank.return_value = [
            ScoredChunk(chunk=chunks[i], score=float(i) / 10)
            for i in range(3)
        ]

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            return_value=mock_embed,
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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            r = _create_retriever(index)
            assert isinstance(r, TfidfRetriever)

    def test_returns_hybrid_when_embeddings_available(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ):
            r = _create_retriever(index)
            assert isinstance(r, HybridRetriever)
            assert r.has_embeddings

    def test_hybrid_has_reranker_when_st_available(self) -> None:
        """Factory auto-creates a CrossEncoderReranker alongside the hybrid retriever."""
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ):
            r = _create_retriever(index)
            assert isinstance(r, HybridRetriever)
            assert r.has_reranker

    def test_reranker_creation_failure_still_returns_hybrid(self) -> None:
        """If CrossEncoderReranker fails, hybrid still works without it."""
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.CrossEncoderReranker",
            side_effect=ImportError("no cross-encoder"),
        ):
            r = _create_retriever(index)
            assert isinstance(r, HybridRetriever)
            assert r.has_embeddings
            assert not r.has_reranker

    def test_falls_back_to_tfidf_if_hybrid_init_fails(self) -> None:
        index = _make_index_with_chunks([_make_chunk("hello")])
        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            side_effect=ImportError("nope"),
        ):
            r = _create_retriever(index)
            assert isinstance(r, TfidfRetriever)


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
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
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

        with patch(
            "hephaistos.harness.rag.retrieve._is_sentence_transformers_available",
            return_value=True,
        ), patch(
            "hephaistos.harness.rag.retrieve.EmbeddingRetriever",
            return_value=mock_embed,
        ), patch(
            "hephaistos.harness.rag.retrieve.CrossEncoderReranker",
            return_value=mock_reranker,
        ):
            results = retrieve("binary search", index)
            assert len(results) > 0
