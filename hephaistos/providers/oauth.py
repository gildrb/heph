"""OAuth login flows for subscription-based LLM providers.

Supports browser-based OAuth2 PKCE flows for:
- Anthropic (Claude Pro/Max subscription)
- OpenAI (ChatGPT Plus/Pro subscription)

The flow:
1. Generate PKCE code verifier + challenge
2. Start a local HTTP server to receive the callback
3. Open the browser to the provider's authorize URL
4. Exchange the auth code for access + refresh tokens
5. Store tokens in the OS keychain

Token refresh happens automatically when the access token expires.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from hephaistos.logging import get_logger

_log = get_logger("providers.oauth")


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code verifier and S256 challenge."""
    verifier_bytes = secrets.token_bytes(32)
    verifier = _base64url_encode(verifier_bytes)
    challenge_bytes = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = _base64url_encode(challenge_bytes)
    return verifier, challenge


# ---------------------------------------------------------------------------
# OAuth callback server
# ---------------------------------------------------------------------------


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that captures the OAuth callback code."""

    code: str | None = None
    state: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "error" in params:
            self.error = params["error"][0]
            self._respond("Authentication failed. You can close this tab.")
            return

        _OAuthCallbackHandler.code = params.get("code", [None])[0]
        _OAuthCallbackHandler.state = params.get("state", [None])[0]
        self._respond("Authentication successful! You can close this tab and return to Hephaistos.")

    def _respond(self, message: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"<html><body style='font-family:sans-serif;padding:40px'><h2>{message}</h2></body></html>"
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        pass  # suppress HTTP server logs


# ---------------------------------------------------------------------------
# Token storage
# ---------------------------------------------------------------------------

_OAUTH_KEY_PREFIX = "oauth:"


def _store_oauth_token(provider_slug: str, token_data: dict) -> None:
    """Store OAuth tokens in the keychain as JSON."""
    key = f"{_OAUTH_KEY_PREFIX}{provider_slug}"
    try:
        import keyring
        keyring.set_password("hephaistos", key, json.dumps(token_data))
    except Exception:
        # Fallback: store in volatile memory
        from hephaistos.providers.keyring_store import set_volatile
        set_volatile(key, json.dumps(token_data))


def _load_oauth_token(provider_slug: str) -> dict | None:
    """Load OAuth tokens from the keychain."""
    key = f"{_OAUTH_KEY_PREFIX}{provider_slug}"
    try:
        import keyring
        raw = keyring.get_password("hephaistos", key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    # Try volatile
    from hephaistos.providers.keyring_store import get_volatile
    raw = get_volatile(key)
    if raw:
        return json.loads(raw)
    return None


# ---------------------------------------------------------------------------
# Provider configs
# ---------------------------------------------------------------------------


@dataclass
class OAuthProvider:
    slug: str
    display_name: str
    authorize_url: str
    token_url: str
    client_id: str
    scopes: str
    callback_port: int
    callback_path: str


_PROVIDERS = {
    "anthropic": OAuthProvider(
        slug="anthropic",
        display_name="Anthropic (Claude Pro/Max)",
        authorize_url="https://claude.ai/oauth/authorize",
        token_url="https://platform.claude.com/v1/oauth/token",
        client_id="9d1c250a-e61b-44d9-88ed-5944d1962f5e",
        scopes="org:create_api_key user:profile user:inference user:sessions:claude_code",
        callback_port=53692,
        callback_path="/callback",
    ),
    "openai": OAuthProvider(
        slug="openai",
        display_name="OpenAI (ChatGPT Plus/Pro)",
        authorize_url="https://auth.openai.com/oauth/authorize",
        token_url="https://auth.openai.com/oauth/token",
        client_id="app_EMoamEEZ73f0CkXaXp7hrann",
        scopes="openid profile email offline_access",
        callback_port=1455,
        callback_path="/auth/callback",
    ),
}


# Need dataclass import


# ---------------------------------------------------------------------------
# Login flow
# ---------------------------------------------------------------------------


def login(provider_slug: str) -> dict | None:
    """Run the OAuth login flow for a provider.

    Opens a browser, waits for callback, exchanges tokens.
    Returns token data dict or None on failure.
    """

    provider = _PROVIDERS.get(provider_slug)
    if provider is None:
        _log.error("unknown oauth provider", extra={"fields": {"slug": provider_slug}})
        return None

    verifier, challenge = _generate_pkce()
    state = secrets.token_hex(16)

    redirect_uri = f"http://localhost:{provider.callback_port}{provider.callback_path}"

    # Build authorize URL
    params = {
        "response_type": "code",
        "client_id": provider.client_id,
        "redirect_uri": redirect_uri,
        "scope": provider.scopes,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    auth_url = f"{provider.authorize_url}?{urlencode(params)}"

    # Reset handler state
    _OAuthCallbackHandler.code = None
    _OAuthCallbackHandler.state = None
    _OAuthCallbackHandler.error = None

    # Start callback server
    server = HTTPServer(("127.0.0.1", provider.callback_port), _OAuthCallbackHandler)
    server.timeout = 120  # 2 minute timeout

    _log.info("oauth: starting callback server", extra={"fields": {
        "provider": provider_slug,
        "port": provider.callback_port,
    }})

    print(f"\n  Opening browser for {provider.display_name}...")
    print(f"  If the browser doesn't open, visit:\n  {auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    # Wait for callback
    result: dict | None = None
    try:
        server.handle_request()  # handles one request then returns

        if _OAuthCallbackHandler.error:
            print(f"  Authentication failed: {_OAuthCallbackHandler.error}")
            return None

        code = _OAuthCallbackHandler.code
        received_state = _OAuthCallbackHandler.state

        if not code:
            print("  No authorization code received.")
            return None

        if received_state != state:
            print("  State mismatch — possible CSRF attack. Aborting.")
            return None

        # Exchange code for tokens
        print("  Exchanging authorization code...")
        token_data = _exchange_code(provider, code, verifier, redirect_uri)

        if token_data is None:
            return None

        # Store tokens
        _store_oauth_token(provider_slug, token_data)
        print(f"  Successfully authenticated with {provider.display_name}!")
        result = token_data

    except Exception as exc:
        _log.error("oauth login failed", extra={"fields": {
            "provider": provider_slug,
            "error": str(exc),
        }})
        print(f"  Login failed: {exc}")
    finally:
        server.server_close()

    return result


def _exchange_code(
    provider: OAuthProvider,
    code: str,
    verifier: str,
    redirect_uri: str,
) -> dict | None:
    """Exchange authorization code for access + refresh tokens."""
    import urllib.request

    data = urlencode({
        "grant_type": "authorization_code",
        "client_id": provider.client_id,
        "code": code,
        "code_verifier": verifier,
        "redirect_uri": redirect_uri,
    }).encode("utf-8")

    req = urllib.request.Request(
        provider.token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        _log.error("token exchange failed", extra={"fields": {
            "provider": provider.slug,
            "error": str(exc),
        }})
        print(f"  Token exchange failed: {exc}")
        return None

    if "access_token" not in body or "refresh_token" not in body:
        _log.error("token exchange returned incomplete data", extra={"fields": {
            "keys": list(body.keys()),
        }})
        print("  Token exchange returned incomplete data.")
        return None

    return {
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "expires_at": time.time() + body.get("expires_in", 3600) - 300,
        "provider": provider.slug,
    }


def refresh(provider_slug: str) -> dict | None:
    """Refresh an expired OAuth token.

    Returns updated token data or None on failure.
    """
    token_data = _load_oauth_token(provider_slug)
    if token_data is None:
        return None

    # Check if still valid
    if token_data.get("expires_at", 0) > time.time():
        return token_data

    provider = _PROVIDERS.get(provider_slug)
    if provider is None:
        return None

    refresh_token = token_data.get("refresh_token", "")
    if not refresh_token:
        return None

    import urllib.request

    data = urlencode({
        "grant_type": "refresh_token",
        "client_id": provider.client_id,
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = urllib.request.Request(
        provider.token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        _log.error("token refresh failed", extra={"fields": {
            "provider": provider_slug,
            "error": str(exc),
        }})
        return None

    updated = {
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token", refresh_token),
        "expires_at": time.time() + body.get("expires_in", 3600) - 300,
        "provider": provider_slug,
    }

    _store_oauth_token(provider_slug, updated)
    return updated


def get_access_token(provider_slug: str) -> str | None:
    """Get a valid access token for a provider.

    Automatically refreshes if expired. Returns None if no credentials.
    """
    token_data = refresh(provider_slug)
    if token_data is None:
        return None
    return token_data.get("access_token")


def is_logged_in(provider_slug: str) -> bool:
    """Check if OAuth credentials exist for a provider."""
    return _load_oauth_token(provider_slug) is not None


def logout(provider_slug: str) -> bool:
    """Remove OAuth credentials for a provider."""
    key = f"{_OAUTH_KEY_PREFIX}{provider_slug}"
    try:
        import keyring
        keyring.delete_password("hephaistos", key)
    except Exception:
        pass
    from hephaistos.providers.keyring_store import clear_volatile
    clear_volatile(key)
    return True


def available_providers() -> list[dict[str, str]]:
    """List available OAuth providers and their login status."""
    result = []
    for slug, provider in _PROVIDERS.items():
        result.append({
            "slug": slug,
            "display_name": provider.display_name,
            "logged_in": is_logged_in(slug),
        })
    return result
