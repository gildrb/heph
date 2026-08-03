"""Test-suite defaults for optional RAG backend isolation."""

from __future__ import annotations

import subprocess
import sys

from harness.rag import optional_backends


def test_no_ml_backend_probes_or_fallbacks_are_exposed() -> None:
    """The lean install exposes no optional ML backend compatibility API."""
    assert not any(
        name.endswith(("sklearn", "transformer", "encoder", "bm25"))
        for name in dir(optional_backends)
    )


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
