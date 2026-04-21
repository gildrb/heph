"""OAuth authentication for subscription-based LLM providers.

Implements the Authorization Code + PKCE flow for OpenAI Codex
(ChatGPT Plus/Pro).  Tokens are stored in ``~/.config/hephaistos/auth.json``
with ``0600`` permissions and auto-refreshed when expired.

Token resolution is wired into the key resolution chain so that
``resolve_key()`` transparently returns a fresh access token when
the active provider has OAuth credentials stored.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import secrets
import ssl
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from hephaistos.logging import get_logger

_log = get_logger("providers.oauth")

_AUTH_DIR = Path.home() / ".config" / "hephaistos"
_AUTH_FILE = _AUTH_DIR / "auth.json"

# --- OpenAI Codex OAuth constants -------------------------------------------

_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
_AUTHORIZE_URL = "https://auth.openai.com/oauth/authorize"
_TOKEN_URL = "https://auth.openai.com/oauth/token"
_REDIRECT_URI = "http://localhost:1455/auth/callback"
_SCOPE = "openid profile email offline_access"
_CALLBACK_PORT = 1455

_SUCCESS_HTML = (
    "<!DOCTYPE html><html><body"
    " style='font-family:sans-serif;text-align:center;padding:2em'>"
    "<h2>Authentication successful!</h2>"
    "<p>You can close this window.</p></body></html>"
)

_ERROR_HTML_TEMPLATE = (
    "<!DOCTYPE html><html><body"
    " style='font-family:sans-serif;text-align:center;padding:2em'>"
    "<h2 style='color:red'>Authentication failed</h2>"
    "<p>{error}</p></body></html>"
)

# Shared mutable state for the OAuth callback handler.
# Using a module-level dict instead of class variables avoids
# stale state if the handler class is subclassed or if tests
# run concurrently.
_callback_state: dict[str, str | None] = {}


# --- Data classes -----------------------------------------------------------


@dataclass
class OAuthCredentials:
    """OAuth token bundle for a single provider."""

    provider: str
    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp in **milliseconds**
    account_id: str | None = None

    @property
    def is_expired(self) -> bool:
        return time.time() * 1000 >= self.expires_at


# --- PKCE helpers -----------------------------------------------------------


def generate_pkce() -> tuple[str, str]:
    """Return ``(verifier, challenge)`` for PKCE S256."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


# --- JWT helpers ------------------------------------------------------------


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding
    try:
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


def _extract_account_id(access_token: str) -> str | None:
    payload = _decode_jwt_payload(access_token)
    auth_info = payload.get("https://api.openai.com/auth", {})
    account_id = auth_info.get("chatgpt_account_id")
    return account_id if isinstance(account_id, str) and account_id else None


# --- Callback server --------------------------------------------------------


class _CallbackHandler(BaseHTTPRequestHandler):
    """Receives the OAuth redirect on localhost."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path != "/auth/callback":
            self._respond(404, "Callback route not found.")
            return

        err = params.get("error", [None])[0]
        if err:
            _callback_state["error"] = err
            self._respond(400, err)
            return

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if not code or not state:
            _callback_state["error"] = "Missing code or state"
            self._respond(400, "Missing code or state")
            return

        _callback_state["code"] = code
        _callback_state["received_state"] = state
        self._respond(200, "")

    def _respond(self, status: int, error: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if status >= 400:
            self.wfile.write(_ERROR_HTML_TEMPLATE.format(error=error).encode())
        else:
            self.wfile.write(_SUCCESS_HTML.encode())

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


def _start_callback_server() -> HTTPServer | None:
    """Start the local callback server.  Returns ``None`` on bind failure."""
    _callback_state.clear()
    try:
        server = HTTPServer(("127.0.0.1", _CALLBACK_PORT), _CallbackHandler)
        server.timeout = 120
        return server
    except OSError:
        return None


# --- Token exchange ---------------------------------------------------------


def _ssl_context() -> ssl.SSLContext:
    """Build an SSL context that can verify server certificates on macOS.

    On macOS Python often cannot locate the system certificate store, causing
    ``[SSL: CERTIFICATE_VERIFY_FAILED]``.  This helper tries the default
    context first, then falls back to the ``certifi`` CA bundle (always
    available as a transitive dependency of ``openai``/``keyring``).
    """
    with contextlib.suppress(Exception):
        ctx = ssl.create_default_context()
        if ctx.get_ca_certs():
            return ctx
    # certifi is guaranteed available (transitive dep of openai/keyring).
    with contextlib.suppress(Exception):
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    # Last resort: default context without certifi (will likely fail, but
    # avoids crashing before the actual network call).
    return ssl.create_default_context()


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urlencode(data).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=30, context=_ssl_context()) as resp:  # nosec B310
        return json.loads(resp.read())


def _exchange_code(code: str, verifier: str) -> dict[str, Any]:
    return _post_form(
        _TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": _CLIENT_ID,
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": _REDIRECT_URI,
        },
    )


def _refresh_access_token(refresh_token: str) -> dict[str, Any]:
    return _post_form(
        _TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": _CLIENT_ID,
        },
    )


# --- High-level login / refresh ---------------------------------------------


def _parse_token_response(
    token_data: dict[str, Any],
    provider: str,
    old_account_id: str | None = None,
) -> OAuthCredentials:
    access = token_data.get("access_token", "")
    refresh = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 0)

    if not access or not refresh:
        raise RuntimeError("Token response missing required fields.")

    account_id = _extract_account_id(access) or old_account_id

    return OAuthCredentials(
        provider=provider,
        access_token=access,
        refresh_token=refresh,
        expires_at=time.time() * 1000 + expires_in * 1000,
        account_id=account_id,
    )


def login_openai_codex() -> OAuthCredentials:
    """Run the OpenAI Codex (ChatGPT) OAuth login flow.

    1. Generate PKCE pair and random state.
    2. Start a local HTTP server on port 1455.
    3. Open the browser for the user to authenticate.
    4. Receive the callback, exchange code for tokens.
    5. Persist credentials to ``auth.json``.
    """
    verifier, challenge = generate_pkce()
    state = secrets.token_hex(16)

    auth_url = f"{_AUTHORIZE_URL}?" + urlencode(
        {
            "response_type": "code",
            "client_id": _CLIENT_ID,
            "redirect_uri": _REDIRECT_URI,
            "scope": _SCOPE,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "id_token_add_organizations": "true",
            "codex_cli_simplified_flow": "true",
            "originator": "hephaistos",
        }
    )

    server = _start_callback_server()

    if server is None:
        # Fallback: manual paste
        print("  Could not start local callback server.")
        print(f"  Open this URL in your browser:\n\n    {auth_url}\n")
        redirect = input("  Paste the full redirect URL: ").strip()
        parsed = urlparse(redirect)
        qs = parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        received_state = qs.get("state", [None])[0]
        if received_state != state:
            raise RuntimeError("OAuth state mismatch.")
        if not code:
            raise RuntimeError("No authorization code received.")
    else:
        print("  Opening browser for OpenAI authentication...")
        webbrowser.open(auth_url)
        print(f"  Waiting for callback on port {_CALLBACK_PORT}...")

        server.handle_request()
        server.server_close()

        if _callback_state.get("error"):
            raise RuntimeError(f"OAuth error: {_callback_state['error']}")
        if _callback_state.get("received_state") != state:
            raise RuntimeError("OAuth state mismatch.")
        code = _callback_state.get("code")
        if not code:
            raise RuntimeError("No authorization code received.")

    print("  Exchanging authorization code for tokens...")
    token_data = _exchange_code(code, verifier)
    creds = _parse_token_response(token_data, provider="openai-codex")

    save_credentials(creds)
    return creds


def refresh_credentials(creds: OAuthCredentials) -> OAuthCredentials:
    """Refresh an expired token and persist the new credentials."""
    token_data = _refresh_access_token(creds.refresh_token)
    new_creds = _parse_token_response(
        token_data,
        provider=creds.provider,
        old_account_id=creds.account_id,
    )
    save_credentials(new_creds)
    return new_creds


# --- Persistence ------------------------------------------------------------


def _load_all() -> dict[str, Any]:
    if not _AUTH_FILE.is_file():
        return {}
    try:
        return json.loads(_AUTH_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_credentials(creds: OAuthCredentials) -> None:
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_DIR.chmod(0o700)
    data = _load_all()
    data[creds.provider] = {
        "type": "oauth",
        "access_token": creds.access_token,
        "refresh_token": creds.refresh_token,
        "expires_at": creds.expires_at,
        "account_id": creds.account_id,
    }
    raw = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    fd = os.open(str(_AUTH_FILE), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)


def load_credentials(provider: str) -> OAuthCredentials | None:
    """Load credentials, auto-refreshing if expired."""
    data = _load_all()
    entry = data.get(provider)
    if not entry or entry.get("type") != "oauth":
        return None

    creds = OAuthCredentials(
        provider=provider,
        access_token=entry["access_token"],
        refresh_token=entry["refresh_token"],
        expires_at=entry["expires_at"],
        account_id=entry.get("account_id"),
    )

    if creds.is_expired:
        try:
            creds = refresh_credentials(creds)
        except Exception as exc:
            _log.warning(
                "OAuth auto-refresh failed",
                extra={"fields": {"provider": provider, "error": str(exc)}},
            )
            return None

    return creds


def clear_credentials(provider: str) -> bool:
    """Remove stored credentials.  Returns ``True`` if anything was removed."""
    data = _load_all()
    if provider not in data:
        return False
    del data[provider]
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_DIR.chmod(0o700)
    raw = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    fd = os.open(str(_AUTH_FILE), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)
    return True


def list_providers() -> list[str]:
    """Return slugs with stored OAuth credentials."""
    data = _load_all()
    return [k for k, v in data.items() if v.get("type") == "oauth"]


def resolve_oauth_key(slug: str) -> str:
    """Resolve a fresh access token for *slug*, or ``""`` if unavailable."""
    creds = load_credentials(slug)
    if creds is None:
        return ""
    return creds.access_token
