"""Tests for query transformation strategies: HyDE, Multi-Query, Query Expansion."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from rag.chunker import Chunk, ChunkedDocument
from rag.index import ArmoryIndex
from rag.query_transform import (
    _SYNONYM_MAP,
    CompositeTransformer,
    HyDETransformer,
    IdentityTransformer,
    MultiQueryTransformer,
    QueryExpander,
    QueryTransformerProtocol,
    TransformStrategy,
    _expand_with_wordnet,
    create_transformer,
    transform_query,
)
from rag.retrieve import (
    CrossEncoderReranker,
    EmbeddingRetriever,
    HybridRetriever,
    ScoredChunk,
    retrieve,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(text: str, source: str = "test.md", index: int = 0) -> Chunk:
    return Chunk(text=text, source=source, index=index, char_start=0, char_end=len(text))


def _make_index_with_chunks(chunks: list[Chunk]) -> ArmoryIndex:
    by_source: dict[str, list[Chunk]] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c)

    index = ArmoryIndex(Path("/fake"))
    for source, source_chunks in by_source.items():
        index.documents.append(
            ChunkedDocument(
                source=source,
                chunks=source_chunks,
                content_hash="fake",
            )
        )
    return index


# ---------------------------------------------------------------------------
# QueryTransformerProtocol
# ---------------------------------------------------------------------------


class TestQueryTransformerProtocol:
    def test_identity_satisfies_protocol(self) -> None:
        assert isinstance(IdentityTransformer(), QueryTransformerProtocol)

    def test_expander_satisfies_protocol(self) -> None:
        assert isinstance(QueryExpander(), QueryTransformerProtocol)

    def test_hyde_satisfies_protocol(self) -> None:
        assert isinstance(HyDETransformer(), QueryTransformerProtocol)

    def test_multi_query_satisfies_protocol(self) -> None:
        assert isinstance(MultiQueryTransformer(), QueryTransformerProtocol)

    def test_composite_satisfies_protocol(self) -> None:
        assert isinstance(CompositeTransformer([]), QueryTransformerProtocol)

    def test_plain_object_does_not_satisfy(self) -> None:
        assert not isinstance(object(), QueryTransformerProtocol)


# ---------------------------------------------------------------------------
# IdentityTransformer
# ---------------------------------------------------------------------------


class TestIdentityTransformer:
    def test_returns_query_in_list(self) -> None:
        t = IdentityTransformer()
        result = t.transform("What is Python?")
        assert result == ["What is Python?"]

    def test_returns_exactly_one_query(self) -> None:
        t = IdentityTransformer()
        result = t.transform("hello")
        assert len(result) == 1

    def test_empty_query(self) -> None:
        t = IdentityTransformer()
        result = t.transform("")
        assert result == [""]

    def test_preserves_query_exactly(self) -> None:
        t = IdentityTransformer()
        query = "  complex   query  with  spaces  "
        assert t.transform(query) == [query]


# ---------------------------------------------------------------------------
# QueryExpander
# ---------------------------------------------------------------------------


class TestQueryExpander:
    def test_expandable_words_produce_expanded_query(self) -> None:
        """Words in the synonym map should produce an expanded query."""
        expander = QueryExpander(use_wordnet=False)
        result = expander.transform("how to learn Python")
        assert len(result) == 2
        assert result[0] == "how to learn Python"  # original
        assert "train" in result[1] or "study" in result[1]  # expanded

    def test_no_expandable_words_returns_original_only(self) -> None:
        """Words not in any synonym map should return only the original."""
        expander = QueryExpander(use_wordnet=False)
        result = expander.transform("xylophone zephyr quantum")
        assert len(result) == 1
        assert result[0] == "xylophone zephyr quantum"

    def test_original_query_always_first(self) -> None:
        expander = QueryExpander(use_wordnet=False)
        result = expander.transform("create a new system")
        assert result[0] == "create a new system"

    def test_expanded_query_contains_original(self) -> None:
        expander = QueryExpander(use_wordnet=False)
        result = expander.transform("find the error")
        assert len(result) == 2
        # Expanded query should contain the original words
        assert "find" in result[1]
        assert "error" in result[1]

    def test_empty_query_returns_original(self) -> None:
        expander = QueryExpander(use_wordnet=False)
        result = expander.transform("")
        assert result == [""]

    def test_multiple_synonym_words(self) -> None:
        """Multiple words with synonyms should produce multiple expansions."""
        expander = QueryExpander(use_wordnet=False)
        result = expander.transform("learn and create")
        assert len(result) == 2
        expanded = result[1]
        # Should contain expansions from both "learn" and "create"
        learn_synonyms = _SYNONYM_MAP["learn"][:3]
        create_synonyms = _SYNONYM_MAP["create"][:3]
        has_learn = any(s in expanded for s in learn_synonyms)
        has_create = any(s in expanded for s in create_synonyms)
        assert has_learn or has_create

    def test_wordnet_integration_flag(self) -> None:
        """With use_wordnet=False, only built-in synonyms are used."""
        expander = QueryExpander(use_wordnet=False)
        # This should work even if nltk is not installed
        result = expander.transform("test the method")
        assert len(result) >= 1


class TestQueryExpanderWordNet:
    def test_wordnet_graceful_when_not_installed(self) -> None:
        """WordNet expansion should not crash if nltk is unavailable."""
        result = _expand_with_wordnet("test")
        # Should return a list (possibly empty) without raising
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# HyDETransformer
# ---------------------------------------------------------------------------


class TestHyDETransformer:
    def test_no_prompt_fn_returns_original(self) -> None:
        t = HyDETransformer()
        result = t.transform("What is machine learning?")
        assert result == ["What is machine learning?"]

    def test_with_prompt_fn_returns_hypothetical_and_original(self) -> None:
        mock_fn = MagicMock(
            return_value=(
                "Machine learning is a subset of artificial intelligence "
                "that enables systems to learn from data. It encompasses "
                "supervised, unsupervised, and reinforcement learning paradigms."
            )
        )
        t = HyDETransformer(prompt_fn=mock_fn)
        result = t.transform("What is machine learning?")

        assert len(result) == 2
        # First result is the hypothetical document
        assert "artificial intelligence" in result[0] or "Machine learning" in result[0]
        # Second result is the original query
        assert result[1] == "What is machine learning?"

    def test_prompt_fn_called_with_correct_format(self) -> None:
        mock_fn = MagicMock(return_value="Some hypothetical answer.")
        t = HyDETransformer(prompt_fn=mock_fn)
        t.transform("How does RAG work?")

        mock_fn.assert_called_once()
        prompt_arg = mock_fn.call_args[0][0]
        assert "How does RAG work?" in prompt_arg
        assert "informative answer" in prompt_arg.lower() or "textbook" in prompt_arg.lower()

    def test_empty_llm_response_falls_back(self) -> None:
        mock_fn = MagicMock(return_value="   \n  ")
        t = HyDETransformer(prompt_fn=mock_fn)
        result = t.transform("test query")
        assert result == ["test query"]

    def test_llm_exception_falls_back(self) -> None:
        mock_fn = MagicMock(side_effect=RuntimeError("API error"))
        t = HyDETransformer(prompt_fn=mock_fn)
        result = t.transform("test query")
        assert result == ["test query"]

    def test_hypothetical_doc_stripped(self) -> None:
        mock_fn = MagicMock(return_value="  \n  A good answer about Python.  \n  ")
        t = HyDETransformer(prompt_fn=mock_fn)
        result = t.transform("What is Python?")
        assert result[0] == "A good answer about Python."

    def test_hypothetical_doc_used_as_primary_query(self) -> None:
        """The hypothetical document should be the first (primary) result."""
        mock_fn = MagicMock(
            return_value="Python is an interpreted high-level programming language.",
        )
        t = HyDETransformer(prompt_fn=mock_fn)
        result = t.transform("What is Python?")
        assert "interpreted" in result[0] or "programming" in result[0]


# ---------------------------------------------------------------------------
# MultiQueryTransformer
# ---------------------------------------------------------------------------


class TestMultiQueryTransformer:
    def test_no_prompt_fn_returns_original(self) -> None:
        t = MultiQueryTransformer()
        result = t.transform("What is deep learning?")
        assert result == ["What is deep learning?"]

    def test_with_prompt_fn_returns_original_plus_alternatives(self) -> None:
        mock_fn = MagicMock(
            return_value=(
                "How does deep learning work?\n"
                "Explain neural networks and deep learning\n"
                "What are the applications of deep learning?"
            )
        )
        t = MultiQueryTransformer(prompt_fn=mock_fn)
        result = t.transform("What is deep learning?")

        assert len(result) == 4  # original + 3 alternatives
        assert result[0] == "What is deep learning?"  # original first
        assert "neural networks" in result[1] or "neural networks" in result[2]

    def test_respects_max_alternatives(self) -> None:
        mock_fn = MagicMock(
            return_value=(
                "Alt one about topic\n"
                "Alt two about topic\n"
                "Alt three about topic\n"
                "Alt four about topic\n"
                "Alt five about topic"
            )
        )
        t = MultiQueryTransformer(prompt_fn=mock_fn, max_alternatives=2)
        result = t.transform("test query")

        # original + max 2 alternatives
        assert len(result) == 3

    def test_strips_numbering_from_alternatives(self) -> None:
        mock_fn = MagicMock(
            return_value=(
                "1. First alternative query\n"
                "2. Second alternative query\n"
                "3. Third alternative query"
            )
        )
        t = MultiQueryTransformer(prompt_fn=mock_fn, max_alternatives=5)
        result = t.transform("test")

        # Should not contain numbered prefixes
        for alt in result[1:]:
            assert not alt.startswith("1.")
            assert not alt.startswith("2.")

    def test_empty_llm_response_falls_back(self) -> None:
        mock_fn = MagicMock(return_value="   \n  ")
        t = MultiQueryTransformer(prompt_fn=mock_fn)
        result = t.transform("test query")
        assert result == ["test query"]

    def test_llm_exception_falls_back(self) -> None:
        mock_fn = MagicMock(side_effect=RuntimeError("timeout"))
        t = MultiQueryTransformer(prompt_fn=mock_fn)
        result = t.transform("test query")
        assert result == ["test query"]

    def test_filters_very_short_alternatives(self) -> None:
        """Very short fragments (< 5 chars) should be filtered out."""
        mock_fn = MagicMock(
            return_value=(
                "How does neural network architecture work?\n"
                "ok\n"
                "What are the fundamentals of deep learning?"
            )
        )
        t = MultiQueryTransformer(prompt_fn=mock_fn)
        result = t.transform("deep learning")

        # "ok" should be filtered (only 2 chars)
        for alt in result[1:]:
            assert len(alt) > 5

    def test_default_max_alternatives(self) -> None:
        t = MultiQueryTransformer()
        assert t._max_alternatives == 3


# ---------------------------------------------------------------------------
# CompositeTransformer
# ---------------------------------------------------------------------------


class TestCompositeTransformer:
    def test_empty_transformers_returns_original(self) -> None:
        ct = CompositeTransformer([])
        result = ct.transform("hello")
        assert result == ["hello"]

    def test_single_identity_transformer(self) -> None:
        ct = CompositeTransformer([IdentityTransformer()])
        result = ct.transform("hello")
        assert result == ["hello"]

    def test_chains_two_transformers(self) -> None:
        """Two transformers should be applied sequentially."""
        mock1 = MagicMock()
        mock1.transform.return_value = ["query A", "query B"]

        mock2 = MagicMock()
        mock2.transform.side_effect = lambda q: [f"expanded: {q}"]

        ct = CompositeTransformer([mock1, mock2])
        ct.transform("original")

        # First transformer called with "original"
        mock1.transform.assert_called_once_with("original")
        # Second transformer called with each output of the first
        assert mock2.transform.call_count == 2

    def test_deduplicates_queries(self) -> None:
        """Duplicate queries should be deduplicated."""
        mock1 = MagicMock()
        mock1.transform.return_value = ["test query", "test query"]

        ct = CompositeTransformer([mock1])
        result = ct.transform("test query")
        assert len(result) == 1
        assert result[0] == "test query"

    def test_ensures_original_in_result(self) -> None:
        """Even if no transformer outputs the original, it should be present."""
        mock1 = MagicMock()
        mock1.transform.return_value = ["something different"]

        ct = CompositeTransformer([mock1])
        result = ct.transform("original query")
        assert "original query" in result

    def test_expansion_then_hyde(self) -> None:
        """Test chaining QueryExpander with HyDE-like transformer."""
        # Expander produces [original, expanded]
        expander = QueryExpander(use_wordnet=False)

        # HyDE-like: just prefix each query
        class PrefixTransformer:
            def transform(self, query: str) -> list[str]:
                return [f"HYPOTHETICAL: {query}"]

        ct = CompositeTransformer([expander, PrefixTransformer()])
        result = ct.transform("learn Python")

        # Should have original + hypothetical variants of expanded queries
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


class TestCreateTransformer:
    def test_identity_strategy(self) -> None:
        t = create_transformer(TransformStrategy.IDENTITY)
        assert isinstance(t, IdentityTransformer)

    def test_expansion_strategy(self) -> None:
        t = create_transformer(TransformStrategy.EXPANSION)
        assert isinstance(t, QueryExpander)

    def test_hyde_strategy(self) -> None:
        t = create_transformer(TransformStrategy.HYDE)
        assert isinstance(t, HyDETransformer)

    def test_hyde_with_prompt_fn(self) -> None:
        mock_fn = MagicMock(return_value="answer")
        t = create_transformer(TransformStrategy.HYDE, prompt_fn=mock_fn)
        assert isinstance(t, HyDETransformer)
        assert t._prompt_fn is mock_fn

    def test_multi_query_strategy(self) -> None:
        t = create_transformer(TransformStrategy.MULTI_QUERY)
        assert isinstance(t, MultiQueryTransformer)

    def test_multi_query_with_prompt_fn(self) -> None:
        mock_fn = MagicMock(return_value="alt query")
        t = create_transformer(TransformStrategy.MULTI_QUERY, prompt_fn=mock_fn)
        assert isinstance(t, MultiQueryTransformer)
        assert t._prompt_fn is mock_fn

    def test_unknown_strategy_falls_back_to_identity(self) -> None:
        # This shouldn't happen in practice but the factory should be safe
        t = create_transformer("not_a_real_strategy")  # ty:ignore[invalid-argument-type]
        assert isinstance(t, IdentityTransformer)


# ---------------------------------------------------------------------------
# transform_query convenience function
# ---------------------------------------------------------------------------


class TestTransformQueryConvenience:
    def test_identity_returns_original(self) -> None:
        result = transform_query("test query", TransformStrategy.IDENTITY)
        assert result == ["test query"]

    def test_expansion_with_no_expandable_words(self) -> None:
        result = transform_query("xylophone", TransformStrategy.EXPANSION)
        assert len(result) >= 1
        assert "xylophone" in result[0]

    def test_expansion_produces_expanded(self) -> None:
        result = transform_query("learn to code", TransformStrategy.EXPANSION)
        assert len(result) >= 1

    def test_hyde_without_prompt_fn_returns_original(self) -> None:
        result = transform_query("What is RAG?", TransformStrategy.HYDE)
        assert result == ["What is RAG?"]

    def test_hyde_with_prompt_fn(self) -> None:
        mock_fn = MagicMock(return_value="RAG stands for Retrieval-Augmented Generation.")
        result = transform_query("What is RAG?", TransformStrategy.HYDE, prompt_fn=mock_fn)
        assert len(result) == 2
        assert "Retrieval-Augmented Generation" in result[0]

    def test_multi_query_without_prompt_fn(self) -> None:
        result = transform_query("test", TransformStrategy.MULTI_QUERY)
        assert result == ["test"]


# ---------------------------------------------------------------------------
# Integration: HybridRetriever with query transformation
# ---------------------------------------------------------------------------


class TestHybridRetrieverWithTransformation:
    def test_single_transformed_query(self) -> None:
        """When transformer returns one query, standard path is used."""
        chunks = [
            _make_chunk("Python programming language", "a.md", 0),
            _make_chunk("Rust systems programming", "b.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_transformer = MagicMock()
        mock_transformer.transform.return_value = ["python programming"]

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, query_transformer=mock_transformer)
            results = hybrid.retrieve("anything", top_k=2)

            mock_transformer.transform.assert_called_once_with("anything")
            assert len(results) > 0

    def test_multi_query_retrieval_fuses_results(self) -> None:
        """When transformer returns multiple queries, results are fused via RRF."""
        chunks = [
            _make_chunk("Python is great for data science", "a.md", 0),
            _make_chunk("Machine learning uses Python extensively", "b.md", 0),
            _make_chunk("Rust is fast and safe", "c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_transformer = MagicMock()
        mock_transformer.transform.return_value = [
            "Python data science",
            "machine learning Python",
            "programming for data analysis",
        ]

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, query_transformer=mock_transformer)
            results = hybrid.retrieve("Python ML", top_k=2)

            # Should have results (fused from multiple queries)
            assert len(results) > 0
            # Python-related chunks should rank highest
            assert results[0].chunk.source in ("a.md", "b.md")

    def test_multi_query_with_embeddings(self) -> None:
        """Full pipeline: multi-query + embeddings + RRF."""
        chunks = [
            _make_chunk("Python programming", "a.md", 0),
            _make_chunk("Rust systems", "b.md", 0),
            _make_chunk("Cooking recipes", "c.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_embed = MagicMock(spec=EmbeddingRetriever)
        mock_embed.retrieve.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.95),
            ScoredChunk(chunk=chunks[1], score=0.5),
        ]

        mock_transformer = MagicMock()
        mock_transformer.transform.return_value = [
            "python programming",
            "how to code in python",
        ]

        with (
            patch(
                "rag.retrieve._is_sentence_transformers_available",
                return_value=True,
            ),
            patch(
                "rag.retrieve.EmbeddingRetriever",
                return_value=mock_embed,
            ),
        ):
            hybrid = HybridRetriever(index, query_transformer=mock_transformer)
            results = hybrid.retrieve("python", top_k=2)

            # Both queries should have been sent to embedding retriever
            assert mock_embed.retrieve.call_count >= 2
            assert len(results) > 0

    def test_multi_query_all_empty_results(self) -> None:
        """When all transformed queries return nothing, result is empty."""
        chunks = [_make_chunk("unrelated content", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        mock_transformer = MagicMock()
        mock_transformer.transform.return_value = [
            "zzzzz quantum",
            "yyyyyy astronomy",
        ]

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, query_transformer=mock_transformer)
            results = hybrid.retrieve("zzzzz", top_k=5)
            assert results == []

    def test_multi_query_with_reranker(self) -> None:
        """Multi-query + RRF + cross-encoder re-ranking."""
        chunks = [
            _make_chunk("Python programming", "a.md", 0),
            _make_chunk("Rust systems", "b.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_transformer = MagicMock()
        mock_transformer.transform.return_value = [
            "python",
            "programming language",
        ]

        mock_reranker = MagicMock(spec=CrossEncoderReranker)
        mock_reranker.rerank.return_value = [
            ScoredChunk(chunk=chunks[0], score=0.99),
        ]

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(
                index,
                reranker=mock_reranker,
                query_transformer=mock_transformer,
            )
            results = hybrid.retrieve("python", top_k=1)

            mock_reranker.rerank.assert_called_once()
            assert len(results) == 1
            assert results[0].chunk.source == "a.md"

    def test_hyde_integration(self) -> None:
        """HyDE: LLM generates hypothetical doc, retriever uses it."""
        chunks = [
            _make_chunk(
                "Machine learning is a field of artificial intelligence that "
                "uses statistical techniques to give computer systems the ability "
                "to learn from data.",
                "ml.md",
                0,
            ),
            _make_chunk("Cooking with garlic and olive oil.", "cook.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_fn = MagicMock(
            return_value=(
                "Machine learning is an AI discipline focused on building systems "
                "that learn from data using statistical methods."
            )
        )
        hyde = HyDETransformer(prompt_fn=mock_fn)

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, query_transformer=hyde)
            results = hybrid.retrieve("What is ML?", top_k=2)

            # The hypothetical doc should match the ML chunk
            assert len(results) > 0
            assert results[0].chunk.source == "ml.md"

    def test_expansion_integration(self) -> None:
        """Query expansion with real TF-IDF retrieval."""
        chunks = [
            _make_chunk("How to train a machine learning model with Python.", "ml.md", 0),
            _make_chunk("Cooking pasta with tomato sauce.", "cook.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        expander = QueryExpander(use_wordnet=False)

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            hybrid = HybridRetriever(index, query_transformer=expander)
            results = hybrid.retrieve("learn machine learning", top_k=2)

            assert len(results) > 0
            # ML chunk should rank higher than cooking
            assert results[0].chunk.source == "ml.md"

    def test_backward_compatible_no_transformer(self) -> None:
        """Without a transformer, behavior is identical to before."""
        chunks = [
            _make_chunk("Python is a programming language.", "py.md", 0),
            _make_chunk("Rust is a systems language.", "rs.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            # No query_transformer argument — backward compatible
            hybrid = HybridRetriever(index)
            results = hybrid.retrieve("python programming")
            assert len(results) > 0
            assert results[0].chunk.source == "py.md"


# ---------------------------------------------------------------------------
# Integration: retrieve() convenience function with transformation
# ---------------------------------------------------------------------------


class TestRetrieveWithTransformation:
    def test_identity_strategy_default(self) -> None:
        """Default behavior (no transformation) unchanged."""
        chunks = [
            _make_chunk("Python is a programming language.", "py.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve("python", index)
            assert len(results) > 0

    def test_expansion_strategy_no_llm(self) -> None:
        """Expansion strategy works without any LLM."""
        chunks = [
            _make_chunk("How to learn Python programming.", "learn.md", 0),
            _make_chunk("Cooking Italian food.", "cook.md", 0),
        ]
        index = _make_index_with_chunks(chunks)
        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve(
                "learn Python",
                index,
                transform_strategy=TransformStrategy.EXPANSION,
            )
            assert len(results) > 0
            assert results[0].chunk.source == "learn.md"

    def test_hyde_strategy_with_prompt_fn(self) -> None:
        """HyDE strategy with a mock prompt function."""
        chunks = [
            _make_chunk(
                "RAG combines retrieval and generation for better LLM outputs.",
                "rag.md",
                0,
            ),
            _make_chunk("The weather is sunny today.", "weather.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_fn = MagicMock(
            return_value=(
                "Retrieval-Augmented Generation (RAG) is a technique that combines "
                "information retrieval with text generation."
            )
        )

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve(
                "What is RAG?",
                index,
                transform_strategy=TransformStrategy.HYDE,
                prompt_fn=mock_fn,
            )
            assert len(results) > 0

    def test_multi_query_strategy_with_prompt_fn(self) -> None:
        """Multi-query strategy with a mock prompt function."""
        chunks = [
            _make_chunk("Vector databases store embeddings for similarity search.", "vec.md", 0),
            _make_chunk("TF-IDF is a classic information retrieval technique.", "tfidf.md", 0),
        ]
        index = _make_index_with_chunks(chunks)

        mock_fn = MagicMock(
            return_value=(
                "How do vector stores work?\n"
                "What is similarity search in databases?\n"
                "Explain embedding-based retrieval systems"
            )
        )

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve(
                "vector search",
                index,
                transform_strategy=TransformStrategy.MULTI_QUERY,
                prompt_fn=mock_fn,
            )
            assert len(results) > 0

    def test_hyde_without_prompt_fn_graceful(self) -> None:
        """HyDE without prompt_fn degrades to identity gracefully."""
        chunks = [_make_chunk("Python programming", "a.md", 0)]
        index = _make_index_with_chunks(chunks)

        with patch(
            "rag.retrieve._is_sentence_transformers_available",
            return_value=False,
        ):
            results = retrieve(
                "python",
                index,
                transform_strategy=TransformStrategy.HYDE,
            )
            assert len(results) > 0


# ---------------------------------------------------------------------------
# Synonym map coverage
# ---------------------------------------------------------------------------


class TestSynonymMap:
    def test_all_synonyms_are_lowercase(self) -> None:
        for word, synonyms in _SYNONYM_MAP.items():
            assert word == word.lower(), f"Key '{word}' is not lowercase"
            for syn in synonyms:
                assert syn == syn.lower(), f"Synonym '{syn}' for '{word}' is not lowercase"

    def test_no_self_references(self) -> None:
        for word, synonyms in _SYNONYM_MAP.items():
            assert word not in synonyms, f"'{word}' appears in its own synonym list"

    def test_all_synonyms_are_strings(self) -> None:
        for word, synonyms in _SYNONYM_MAP.items():
            for syn in synonyms:
                assert isinstance(syn, str), f"Synonym for '{word}' is not a string"

    def test_reasonable_number_of_synonyms(self) -> None:
        for word, synonyms in _SYNONYM_MAP.items():
            assert len(synonyms) <= 5, f"'{word}' has too many synonyms ({len(synonyms)})"
            assert len(synonyms) >= 1, f"'{word}' has no synonyms"
