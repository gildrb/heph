"""Test-suite defaults for optional RAG backend isolation."""

from __future__ import annotations

from harness.rag import chunker, optional_backends


def test_default_tests_pin_optional_rag_backends_off() -> None:
    """Benchmark/retrieval tests should not change behavior when extras are installed."""
    assert optional_backends.has_sklearn() is False
    assert optional_backends.sklearn_tfidf_vectorizer() is None
    assert optional_backends.bm25_class() is None
    assert optional_backends.sentence_transformers_available() is False
    assert optional_backends.sentence_transformer() is None
    assert optional_backends.cross_encoder() is None
    assert chunker._sentence_transformer_factory() is None
