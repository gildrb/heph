"""Secure API key storage via the OS keychain.

Keys are stored in the system keychain (macOS Keychain, Linux Secret Service,
Windows Credential Manager) using the ``keyring`` library.  This avoids
keeping raw API keys in process memory, session objects, or config files.

Storage convention::

    Service:  harness:<provider_slug>
    Username: api_key
    Password: <the actual key>

Fallback order for key resolution:

1. OS keychain (keyring)
2. Environment variable (the ``api_key_env`` field in provider config)
3. In-memory override from interactive login flows (volatile, session-scoped)
"""

from __future__ import annotations

import os
from typing import Final

import keyring
from keyring.errors import KeyringError

from ai.providers import volatile_keys as _volatile_keys
from ai.providers.oauth import resolve_oauth_key

_SERVICE_PREFIX = "harness"
_USERNAME = "api_key"
GLOBAL_API_KEY_ENV: Final[str] = "HARNESS_API_KEY"

# In-process cache for keychain lookups (avoids OS keychain round-trip per API call).
_keychain_cache: dict[str, str | None] = {}

# Backwards-compatible test hook for clearing session-scoped keys.
_volatile = _volatile_keys._volatile


def _service_name(slug: str) -> str:
    return f"{_SERVICE_PREFIX}:{slug}"


def store_key(slug: str, api_key: str) -> None:
    keyring.set_password(_service_name(slug), _USERNAME, api_key)
    _keychain_cache[slug] = api_key


def retrieve_key(slug: str) -> str | None:
    if slug in _keychain_cache:
        return _keychain_cache[slug]
    try:
        result = keyring.get_password(_service_name(slug), _USERNAME)
    except KeyringError:
        return None
    _keychain_cache[slug] = result
    return result


def clear_key(slug: str) -> bool:
    removed = _volatile_keys.clear_volatile_key(slug)
    cached = _keychain_cache.pop(slug, None)
    if cached is not None:
        removed = True
    try:
        keyring.delete_password(_service_name(slug), _USERNAME)
    except KeyringError:
        return removed
    except Exception:
        return removed
    return True


def set_volatile(slug: str, api_key: str) -> None:
    _volatile_keys.set_volatile_key(slug, api_key)
    _keychain_cache.pop(slug, None)


def get_volatile(slug: str) -> str | None:
    return _volatile_keys.get_volatile_key(slug)


def resolve_key(slug: str, env_var: str = "", *, refresh_oauth: bool = True) -> str:
    """Resolve an API key using the full fallback chain.

    Priority:
    0. HARNESS_API_KEY environment variable (global override)
    1. OS keychain
    2. OAuth credentials (auto-refreshed access token unless disabled)
    3. Provider-specific environment variable (if ``env_var`` is provided)
    4. Volatile in-memory store

    Returns the key string, or ``""`` if none found.
    """
    # 0. Global override - takes precedence over everything
    override = os.environ.get(GLOBAL_API_KEY_ENV, "").strip()
    if override:
        return override

    # 1. Keychain
    key = retrieve_key(slug)
    if key:
        return key

    # 2. OAuth
    oauth_key = resolve_oauth_key(slug, refresh_expired=refresh_oauth)
    if oauth_key:
        return oauth_key

    # 3. Provider-specific environment variable
    if env_var:
        env_val = os.environ.get(env_var, "").strip()
        if env_val:
            return env_val

    # 4. Volatile
    vol = get_volatile(slug)
    if vol:
        return vol

    return ""


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 12:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"
