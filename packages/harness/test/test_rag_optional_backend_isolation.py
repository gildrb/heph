"""Test-suite defaults for optional RAG backend isolation."""

from __future__ import annotations

import subprocess
import sys

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


def test_importing_chunker_does_not_import_heavy_document_backends() -> None:
    code = """
import sys
import harness.rag.chunker

heavy = [
    name
    for name in sys.modules
    if name == "docling"
    or name.startswith("docling.")
    or name == "transformers"
    or name.startswith("transformers.")
    or name == "torch"
    or name.startswith("torch.")
]
if heavy:
    raise SystemExit(",".join(sorted(heavy)[:10]))
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def test_capabilities_report_conditional_local_backends() -> None:
    capabilities = optional_backends.capabilities()

    assert [capability.name for capability in capabilities] == [
        "pdftotext",
        "documents",
        "retrieval",
    ]
    assert all(capability.enables for capability in capabilities)
    assert all(capability.fallback for capability in capabilities)
    assert not any("pip install" in capability.fallback for capability in capabilities)
