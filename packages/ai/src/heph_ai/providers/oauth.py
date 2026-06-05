"""OAuth authentication for subscription-based LLM providers."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import html
import json
import os
import re
import secrets
import ssl
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import NamedTuple
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

import certifi

from heph_ai._types import is_string_mapping
from heph_ai.logging import get_logger
from heph_ai.palette import LIGHT_THEME
from heph_ai.providers.volatile_keys import clear_volatile_key

_log = get_logger("providers.oauth")

_AUTH_DIR = Path.home() / ".config" / "hephaion"
_AUTH_FILE = _AUTH_DIR / "auth.json"

_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
_AUTHORIZE_URL = "https://auth.openai.com/oauth/authorize"
_TOKEN_URL = "https://auth.openai.com/oauth/token"
_REDIRECT_URI = "http://localhost:1455/auth/callback"
_SCOPE = "openid profile email offline_access"
_CALLBACK_PORT = 1455
_CALLBACK_TIMEOUT_SECONDS = 120
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)")

_SUCCESS_HTML = (
    "<!DOCTYPE html><html><body"
    " style='font-family:sans-serif;text-align:center;padding:2em'>"
    "<h2>Authentication successful!</h2>"
    "<p>You can close this window.</p></body></html>"
)

_ERROR_HTML_TEMPLATE = (
    "<!DOCTYPE html><html><body"
    " style='font-family:sans-serif;text-align:center;padding:2em'>"
    f"<h2 style='color:{LIGHT_THEME.status_error_text}'>Authentication failed</h2>"
    "<p>{error}</p></body></html>"
)


@dataclass
class _CallbackState:
    expected_state: str
    code: str | None = None
    error: str | None = None
    received_state: str | None = None


class _OAuthCallbackServer(HTTPServer):
    callback_state: _CallbackState

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        callback_state: _CallbackState,
    ) -> None:
        self.callback_state = callback_state
        super().__init__(server_address, handler_class)


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


class _CredentialEntry(NamedTuple):
    access_token: str
    refresh_token: str
    expires_at: float
    account_id: str | None


class _TokenResponse(NamedTuple):
    access_token: str
    refresh_token: str
    expires_in_seconds: float


def generate_pkce() -> tuple[str, str]:
    """Return ``(verifier, challenge)`` for PKCE S256."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _decode_jwt_payload(token: str) -> dict[str, object]:
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding
    try:
        decoded: object = json.loads(base64.urlsafe_b64decode(payload))
        if is_string_mapping(decoded):
            return decoded
        return {}
    except Exception:
        return {}


def _extract_account_id(access_token: str) -> str | None:
    payload = _decode_jwt_payload(access_token)
    auth_info = payload.get("https://api.openai.com/auth", {})
    if not is_string_mapping(auth_info):
        return None
    account_id = auth_info.get("chatgpt_account_id")
    return account_id if isinstance(account_id, str) and account_id else None


class _CallbackHandler(BaseHTTPRequestHandler):
    """Receives the OAuth redirect on localhost."""

    def _callback_state(self) -> _CallbackState:
        state = getattr(self.server, "callback_state", None)
        if not isinstance(state, _CallbackState):
            raise TypeError("OAuth callback state is unavailable.")
        return state

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        callback_state = self._callback_state()

        if parsed.path != "/auth/callback":
            self._respond(404, "Callback route not found.")
            return

        state = params.get("state", [None])[0]
        if not state or state != callback_state.expected_state:
            self._respond(400, "OAuth state mismatch.")
            return

        err = params.get("error", [None])[0]
        if err:
            safe_error = _sanitize_callback_error(err)
            callback_state.error = safe_error
            callback_state.received_state = state
            self._respond(400, safe_error)
            return

        code = params.get("code", [None])[0]

        if not code:
            callback_state.error = "Missing code or state"
            self._respond(400, "Missing code or state")
            return

        callback_state.code = code
        callback_state.received_state = state
        self._respond(200, "")

    def _respond(self, status: int, error: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if status >= 400:
            escaped_error = html.escape(error, quote=True)
            self.wfile.write(_ERROR_HTML_TEMPLATE.format(error=escaped_error).encode())
        else:
            self.wfile.write(_SUCCESS_HTML.encode())

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def _start_callback_server(state: str) -> _OAuthCallbackServer | None:
    """Start the local callback server.  Returns ``None`` on bind failure."""
    try:
        server = _OAuthCallbackServer(
            ("127.0.0.1", _CALLBACK_PORT),
            _CallbackHandler,
            _CallbackState(expected_state=state),
        )
        server.timeout = 120
        return server
    except OSError:
        return None


def _sanitize_callback_error(error: str) -> str:
    collapsed = " ".join(_strip_control_chars(_ANSI_ESCAPE_RE.sub("", error)).split())
    return collapsed[:500] or "OAuth provider returned an error."


def _strip_control_chars(value: str) -> str:
    return "".join(char if _is_displayable_callback_char(char) else " " for char in value)


def _is_displayable_callback_char(char: str) -> bool:
    return char == "\t" or (ord(char) >= 32 and ord(char) != 127)


def _wait_for_callback(server: _OAuthCallbackServer) -> None:
    deadline = time.monotonic() + _CALLBACK_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if server.callback_state.code or server.callback_state.error:
            return
        remaining = deadline - time.monotonic()
        server.timeout = max(0.1, min(1.0, remaining))
        server.handle_request()


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
        return ssl.create_default_context(cafile=certifi.where())
    # Last resort: default context without certifi (will likely fail, but
    # avoids crashing before the actual network call).
    return ssl.create_default_context()


def _post_form(url: str, data: dict[str, str]) -> dict[str, object]:
    body = urlencode(data).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=30, context=_ssl_context()) as resp:  # nosec B310
        payload: object = json.loads(resp.read())
        if is_string_mapping(payload):
            return payload
        return {}


def _post_json(url: str, data: dict[str, str]) -> dict[str, object]:
    body = json.dumps(data).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30, context=_ssl_context()) as resp:  # nosec B310
        payload: object = json.loads(resp.read())
        if is_string_mapping(payload):
            return payload
        return {}


def _parse_token_response(
    token_data: dict[str, object],
    provider: str,
    old_account_id: str | None = None,
) -> OAuthCredentials:
    token_response = _validated_token_response(token_data)
    account_id = _extract_account_id(token_response.access_token) or old_account_id
    return OAuthCredentials(
        provider=provider,
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        expires_at=time.time() * 1000 + token_response.expires_in_seconds * 1000,
        account_id=account_id,
    )


def _validated_token_response(token_data: dict[str, object]) -> _TokenResponse:
    access_token = _string_entry_value(token_data, "access_token") or ""
    refresh_token = _string_entry_value(token_data, "refresh_token") or ""
    expires_in = token_data.get("expires_in", 0)
    expires_in_seconds = float(expires_in) if isinstance(expires_in, int | float) else 0.0
    if not access_token or not refresh_token:
        raise RuntimeError("Token response missing required fields.")
    return _TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=expires_in_seconds,
    )


def login_openai_codex() -> OAuthCredentials:
    """Run the OpenAI Codex OAuth login flow."""
    verifier, challenge = generate_pkce()
    state = secrets.token_hex(16)
    auth_url = _authorization_url(challenge, state)
    code = _authorization_code(auth_url, state)

    print("  Exchanging authorization code for tokens...")
    token_data = _post_form(
        _TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": _CLIENT_ID,
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": _REDIRECT_URI,
        },
    )
    creds = _parse_token_response(token_data, provider="openai-codex")

    save_credentials(creds)
    return creds


def _authorization_url(challenge: str, state: str) -> str:
    return f"{_AUTHORIZE_URL}?" + urlencode(
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
            "originator": "hephaion",
        }
    )


def _authorization_code(auth_url: str, state: str) -> str:
    server = _start_callback_server(state)
    if server is None:
        return _manual_authorization_code(auth_url, state)
    return _callback_authorization_code(server, auth_url, state)


def _manual_authorization_code(auth_url: str, state: str) -> str:
    print("  Could not start local callback server.")
    print(f"  Open this URL in your browser:\n\n    {auth_url}\n")
    redirect = input("  Paste the full redirect URL: ").strip()
    parsed = urlparse(redirect)
    qs = parse_qs(parsed.query)
    received_state = qs.get("state", [None])[0]
    if received_state != state:
        raise RuntimeError("OAuth state mismatch.")
    code = qs.get("code", [None])[0]
    if not code:
        raise RuntimeError("No authorization code received.")
    return code


def _callback_authorization_code(server: _OAuthCallbackServer, auth_url: str, state: str) -> str:
    print("  Opening browser for OpenAI authentication...")
    webbrowser.open(auth_url)
    print(f"  Waiting for callback on port {_CALLBACK_PORT}...")

    _wait_for_callback(server)
    server.server_close()

    callback_state = server.callback_state
    if callback_state.error:
        raise RuntimeError(f"OAuth error: {callback_state.error}")
    if callback_state.received_state != state:
        raise RuntimeError("OAuth state mismatch.")
    code = callback_state.code
    if not code:
        raise RuntimeError("No authorization code received.")
    return code


def refresh_credentials(creds: OAuthCredentials) -> OAuthCredentials:
    """Refresh an expired token and persist the new credentials."""
    token_data = _post_json(
        _TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token,
            "client_id": _CLIENT_ID,
        },
    )
    new_creds = _parse_token_response(
        token_data,
        provider=creds.provider,
        old_account_id=creds.account_id,
    )
    save_credentials(new_creds)
    return new_creds


def _load_all() -> dict[str, dict[str, object]]:
    if not _AUTH_FILE.is_file():
        return {}
    try:
        return _auth_entries_from_json(json.loads(_AUTH_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return {}


def _auth_entries_from_json(data: object) -> dict[str, dict[str, object]]:
    if not is_string_mapping(data):
        return {}
    return {key: value for key, value in data.items() if is_string_mapping(value)}


def _write_all(data: dict[str, dict[str, object]]) -> None:
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_DIR.chmod(0o700)
    raw = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    fd = os.open(str(_AUTH_FILE), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(raw)


def save_credentials(creds: OAuthCredentials) -> None:
    data = _load_all()
    data[creds.provider] = {
        "type": "oauth",
        "access_token": creds.access_token,
        "refresh_token": creds.refresh_token,
        "expires_at": creds.expires_at,
        "account_id": creds.account_id,
    }
    _write_all(data)


_creds_cache: dict[str, OAuthCredentials] = {}


def _credentials_from_entry(
    provider: str,
    entry: dict[str, object] | None,
) -> OAuthCredentials | None:
    credential_entry = _parse_credential_entry(entry)
    if credential_entry is None:
        return None
    return OAuthCredentials(
        provider=provider,
        access_token=credential_entry.access_token,
        refresh_token=credential_entry.refresh_token,
        expires_at=credential_entry.expires_at,
        account_id=credential_entry.account_id,
    )


def _parse_credential_entry(entry: dict[str, object] | None) -> _CredentialEntry | None:
    if entry is None or entry.get("type") != "oauth":
        return None
    access_token = _string_entry_value(entry, "access_token")
    refresh_token = _string_entry_value(entry, "refresh_token")
    expires_at = entry.get("expires_at", 0.0)
    if access_token is None or refresh_token is None or not isinstance(expires_at, int | float):
        return None
    return _CredentialEntry(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=float(expires_at),
        account_id=_string_entry_value(entry, "account_id"),
    )


def _string_entry_value(entry: dict[str, object], key: str) -> str | None:
    value = entry.get(key)
    return value if isinstance(value, str) else None


def _refresh_loaded_credentials(creds: OAuthCredentials) -> OAuthCredentials | None:
    try:
        return refresh_credentials(creds)
    except Exception as exc:
        _log.warning(
            "OAuth auto-refresh failed",
            extra={"fields": {"provider": creds.provider, "error": str(exc)}},
        )
        return None


def load_credentials(
    provider: str,
    *,
    refresh_expired: bool = True,
) -> OAuthCredentials | None:
    """Load credentials, auto-refreshing if expired unless disabled.

    Results are cached in-process to avoid repeated disk reads.
    """
    cached = _creds_cache.get(provider)
    if cached is not None:
        return _usable_loaded_credentials(provider, cached, refresh_expired=refresh_expired)

    data = _load_all()
    creds = _credentials_from_entry(provider, data.get(provider))
    if creds is None:
        return None
    return _usable_loaded_credentials(provider, creds, refresh_expired=refresh_expired)


def _usable_loaded_credentials(
    provider: str,
    creds: OAuthCredentials,
    *,
    refresh_expired: bool,
) -> OAuthCredentials | None:
    if creds.is_expired:
        if not refresh_expired:
            return None
        refreshed = _refresh_loaded_credentials(creds)
        if refreshed is None:
            return None
        creds = refreshed
    _creds_cache[provider] = creds
    return creds


def clear_credentials(provider: str) -> bool:
    """Remove stored credentials.  Returns ``True`` if anything was removed."""
    removed_volatile = clear_volatile_key(provider)
    removed_cached = _creds_cache.pop(provider, None) is not None
    data = _load_all()
    if provider not in data:
        return removed_volatile or removed_cached
    del data[provider]
    _write_all(data)
    return True


def list_providers() -> list[str]:
    """Return slugs with stored OAuth credentials."""
    data = _load_all()
    return [provider for provider, entry in data.items() if entry.get("type") == "oauth"]


def resolve_oauth_key(slug: str, *, refresh_expired: bool = True) -> str:
    """Resolve a fresh access token for *slug*, or ``""`` if unavailable."""
    creds = load_credentials(slug, refresh_expired=refresh_expired)
    if creds is None:
        return ""
    return creds.access_token
