"""Tests for the secure API key store (keyring + volatile fallback)."""

from __future__ import annotations

import contextlib

import keyring
import pytest

from hephaistos.providers.keyring_store import (
    _SERVICE_PREFIX,
    _USERNAME,
    get_volatile,
    mask_key,
    resolve_key,
    retrieve_key,
    set_volatile,
    store_key,
)

# Use a unique test prefix to avoid colliding with real keys
_TEST_SLUG = "__test_hephaistos_unit__"


@pytest.fixture(autouse=True)
def _clean_test_key():  # pyright: ignore[reportUnusedFunction]
    """Ensure no leftover test key in system keyring."""
    with contextlib.suppress(Exception):
        keyring.delete_password(f"{_SERVICE_PREFIX}:{_TEST_SLUG}", _USERNAME)
    yield
    with contextlib.suppress(Exception):
        keyring.delete_password(f"{_SERVICE_PREFIX}:{_TEST_SLUG}", _USERNAME)


# ---------------------------------------------------------------------------
# mask_key
# ---------------------------------------------------------------------------


class TestMaskKey:
    def test_empty_key(self) -> None:
        assert mask_key("") == ""

    def test_short_key_fully_masked(self) -> None:
        assert mask_key("abc") == "***"

    def test_exactly_12_chars_fully_masked(self) -> None:
        assert mask_key("123456789012") == "************"

    def test_long_key_partial_mask(self) -> None:
        assert mask_key("sk-abcdefghijklmnop1234567890") == "sk-a...7890"

    def test_13_chars_shows_ends(self) -> None:
        assert mask_key("1234567890123") == "1234...0123"


# ---------------------------------------------------------------------------
# Volatile store
# ---------------------------------------------------------------------------


class TestVolatileStore:
    def test_set_and_get(self) -> None:
        set_volatile(_TEST_SLUG, "volatile-key")
        assert get_volatile(_TEST_SLUG) == "volatile-key"

    def test_get_missing_returns_none(self) -> None:
        assert get_volatile("nonexistent-slug") is None


# ---------------------------------------------------------------------------
# Keychain round-trip (may fail gracefully if keychain is locked)
# ---------------------------------------------------------------------------


class TestKeychainRoundTrip:
    def test_store_and_retrieve(self) -> None:
        try:
            store_key(_TEST_SLUG, "test-secret-key")
        except Exception:
            pytest.skip("keychain not available in this environment")
        assert retrieve_key(_TEST_SLUG) == "test-secret-key"


# ---------------------------------------------------------------------------
# resolve_key fallback chain
# ---------------------------------------------------------------------------


class TestResolveKey:
    def test_resolves_from_keychain(self, monkeypatch) -> None:
        # Remove env var interference
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        try:
            store_key(_TEST_SLUG, "keychain-key")
        except Exception:
            pytest.skip("keychain not available")
        assert resolve_key(_TEST_SLUG, "TEST_API_KEY") == "keychain-key"

    def test_falls_back_to_env_var(self, monkeypatch) -> None:
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        # No keychain entry (deleted by fixture)
        assert retrieve_key(_TEST_SLUG) is None
        monkeypatch.setenv("TEST_API_KEY", "env-key")
        assert resolve_key(_TEST_SLUG, "TEST_API_KEY") == "env-key"

    def test_falls_back_to_volatile(self, monkeypatch) -> None:
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        # No keychain, no env
        set_volatile(_TEST_SLUG, "volatile-key")
        assert resolve_key(_TEST_SLUG, "TEST_API_KEY") == "volatile-key"

    def test_returns_empty_when_nothing_set(self, monkeypatch) -> None:
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        assert resolve_key(_TEST_SLUG, "TEST_API_KEY") == ""

    def test_keychain_takes_priority_over_env(self, monkeypatch) -> None:
        monkeypatch.setenv("TEST_API_KEY", "env-key")
        try:
            store_key(_TEST_SLUG, "keychain-key")
        except Exception:
            pytest.skip("keychain not available")
        assert resolve_key(_TEST_SLUG, "TEST_API_KEY") == "keychain-key"

    def test_env_takes_priority_over_volatile(self, monkeypatch) -> None:
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        monkeypatch.setenv("TEST_API_KEY", "env-key")
        set_volatile(_TEST_SLUG, "volatile-key")
        # Keychain not set (fixture cleanup), so env wins over volatile
        assert resolve_key(_TEST_SLUG, "TEST_API_KEY") == "env-key"
