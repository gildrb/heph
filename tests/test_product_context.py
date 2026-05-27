from __future__ import annotations

from hephaion.product.context import heph_product_context


def test_heph_product_context_includes_operational_docs() -> None:
    heph_product_context.cache_clear()

    context = heph_product_context()

    assert "Heph Assistant Atlas" in context
    assert "heph armory init" in context
    assert "/armory" in context
    assert "/models" in context
    assert "/evidence" in context
    assert "materials/" in context
    assert "Docs map" in context


def test_heph_product_context_stays_compact() -> None:
    heph_product_context.cache_clear()

    context = heph_product_context()

    assert len(context) <= 4000
    assert "Environment variables" not in context
