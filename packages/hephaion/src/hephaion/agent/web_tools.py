"""Network-facing tool handlers for the agent harness."""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import Message
from typing import Protocol, Self, cast
from urllib.parse import ParseResult, urljoin, urlparse

_WEB_FETCH_TIMEOUT = 15
_WEB_FETCH_MAX_CHARS = 20_000
_WEB_FETCH_MAX_BYTES = _WEB_FETCH_MAX_CHARS * 4
_WEB_FETCH_MAX_REDIRECTS = 5
_WEB_USER_AGENT = "Heph/0.1 (document workspace)"
_REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True, slots=True)
class FetchTarget:
    safe_url: str
    host_header: str | None


type FetchTargetResult = FetchTarget | str


@dataclass(frozen=True, slots=True)
class FetchSuccess:
    url: str
    content: str


class FetchResponse(Protocol):
    headers: Message

    def read(self, _amt: int = -1) -> bytes: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> bool | None: ...


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def _open_without_redirect(
    req: urllib.request.Request,
    *,
    timeout: int,
) -> FetchResponse:
    return cast("FetchResponse", _NO_REDIRECT_OPENER.open(req, timeout=timeout))


def run_web_fetch(url: str, **_kwargs: object) -> str:
    """Fetch a URL and return the text content with source attribution."""
    original_url = url
    current_url = url
    redirects = 0

    while True:
        target = _fetch_target(current_url)
        if isinstance(target, str):
            return target

        try:
            success = _fetch_once(target, current_url, timeout=_WEB_FETCH_TIMEOUT)
        except urllib.error.HTTPError as exc:
            redirect = _redirect_result(current_url, original_url, redirects, exc)
            if redirect.startswith("Error:"):
                return redirect
            current_url = redirect
            redirects += 1
            continue
        except urllib.error.URLError as exc:
            return f"Error: could not reach {current_url} - {exc.reason}"
        except Exception as exc:
            return f"Error fetching {current_url}: {exc}"

        if isinstance(success, str):
            return success
        return _fetched_content(original_url, success)


def _fetch_once(
    target: FetchTarget,
    current_url: str,
    *,
    timeout: int,
) -> FetchSuccess | str:
    request = _fetch_request(target)
    with _open_without_redirect(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if not _is_text_content_type(content_type):
            return f"Error: non-text content type ({content_type}). URL: {current_url}"
        raw_bytes = response.read(_WEB_FETCH_MAX_BYTES + 1)
        raw = raw_bytes[:_WEB_FETCH_MAX_BYTES].decode("utf-8", errors="replace")
    return FetchSuccess(url=current_url, content=_normalize_fetched_text(raw))


def _fetch_request(target: FetchTarget) -> urllib.request.Request:
    request = urllib.request.Request(
        target.safe_url,
        headers={"User-Agent": _WEB_USER_AGENT},
    )
    if target.host_header:
        request.add_header("Host", target.host_header)
    return request


def _is_text_content_type(content_type: str) -> bool:
    return any(kind in content_type for kind in ("text", "json", "xml"))


def _redirect_url(current_url: str, exc: urllib.error.HTTPError) -> str | None:
    if exc.code not in _REDIRECT_STATUS_CODES:
        return None
    location = exc.headers.get("Location", "") if exc.headers else ""
    return urljoin(current_url, location) if location else ""


def _redirect_result(
    current_url: str,
    original_url: str,
    redirects: int,
    exc: urllib.error.HTTPError,
) -> str:
    redirect_url = _redirect_url(current_url, exc)
    if redirect_url is None:
        return f"Error: HTTP {exc.code} fetching {current_url}"
    if not redirect_url:
        return f"Error: HTTP {exc.code} redirect missing Location for {current_url}"
    if redirects >= _WEB_FETCH_MAX_REDIRECTS:
        return f"Error: too many redirects fetching {original_url}"
    return redirect_url


def _normalize_fetched_text(raw: str) -> str:
    text = _trim_fetched_text(raw)
    if not _looks_like_html(text):
        return text
    return _trim_fetched_text(_html_to_text(text))


def _looks_like_html(text: str) -> bool:
    lowered = text.lower()
    return "<html" in lowered or "<body" in lowered


def _html_to_text(raw: str) -> str:
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", raw, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _trim_fetched_text(text: str) -> str:
    if len(text) <= _WEB_FETCH_MAX_CHARS:
        return text
    return text[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"


def _fetched_content(original_url: str, success: FetchSuccess) -> str:
    header = f"--- Source: {original_url} ---"
    if success.url != original_url:
        header += f"\n--- Final URL: {success.url} ---"
    return f"{header}\n{success.content}\n--- End of fetched content ---"


def _fetch_target(url: str) -> FetchTargetResult:
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    parsed = urlparse(url)
    validation_error = _target_validation_error(parsed)
    if validation_error:
        return validation_error
    hostname = parsed.hostname or ""
    port = parsed.port
    resolved_ips = _resolve_hostname_ips(hostname)
    if not resolved_ips:
        return f"Error: could not resolve host ({hostname})"
    if _has_blocked_ip(resolved_ips):
        return f"Error: blocked private/internal host ({hostname})"
    netloc = _netloc(resolved_ips[0], port)
    safe_url = parsed._replace(netloc=netloc).geturl()
    host_header = _netloc(hostname, port)
    return FetchTarget(safe_url=safe_url, host_header=host_header)


def _target_validation_error(parsed: ParseResult) -> str:
    hostname = parsed.hostname
    if not hostname:
        return "Error: URL must include a host"
    if parsed.username is not None or parsed.password is not None:
        return "Error: URL must not include credentials"
    try:
        _port = parsed.port
    except ValueError:
        return "Error: URL has invalid port"
    return ""


def _has_blocked_ip(resolved_ips: list[str]) -> bool:
    for ip_str in resolved_ips:
        ip = ipaddress.ip_address(ip_str)
        if not ip.is_global:
            return True
    return False


def _netloc(host: str, port: int | None) -> str:
    wrapped_host = f"[{host}]" if ":" in host else host
    return wrapped_host if port is None else f"{wrapped_host}:{port}"


def _resolve_hostname_ips(hostname: str) -> list[str]:
    """Resolve a hostname to its IP addresses to prevent DNS rebinding."""
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return [str(sockaddr[0]) for _, _, _, _, sockaddr in addr_info]
