from __future__ import annotations

from extension_contracts import heph_product_routing_context


def test_extension_contracts_routing_context_is_available() -> None:
    context = heph_product_routing_context()

    assert "Heph" in context
    assert "Product intents use no retrieval" in context
