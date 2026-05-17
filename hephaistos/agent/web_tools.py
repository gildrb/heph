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
from urllib.parse import urljoin, urlparse

_WEB_FETCH_TIMEOUT = 15
_WEB_FETCH_MAX_CHARS = 20_000
_WEB_FETCH_MAX_REDIRECTS = 5
_WEB_USER_AGENT = "Hephaistos/0.1 (document workspace)"
_REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True, slots=True)
class FetchTarget:
    safe_url: str
    host_header: str | None


class FetchResponse(Protocol):
    headers: Message

    def read(self) -> bytes: ...

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
        del fp, newurl


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def _open_without_redirect(
    req: urllib.request.Request,
    *,
    timeout: int,
) -> FetchResponse:
    return cast("FetchResponse", _NO_REDIRECT_OPENER.open(req, timeout=timeout))


def run_web_fetch(url: str, timeout: int | None = None, **_kwargs: object) -> str:
    """Fetch a URL and return the text content with source attribution."""
    original_url = url
    current_url = url
    redirects = 0
    actual_timeout = timeout or _WEB_FETCH_TIMEOUT

    while True:
        target = _prepare_fetch_target(current_url)
        if isinstance(target, str):
            return target

        req = urllib.request.Request(
            target.safe_url,
            headers={"User-Agent": _WEB_USER_AGENT},
        )
        if target.host_header:
            req.add_header("Host", target.host_header)
        try:
            with _open_without_redirect(req, timeout=actual_timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if not any(ct in content_type for ct in ("text", "json", "xml")):
                    return f"Error: non-text content type ({content_type}). URL: {original_url}"
                raw = resp.read().decode("utf-8", errors="replace")
                break
        except urllib.error.HTTPError as exc:
            if exc.code in _REDIRECT_STATUS_CODES:
                location = exc.headers.get("Location", "") if exc.headers else ""
                if not location:
                    return f"Error: HTTP {exc.code} redirect missing Location for {current_url}"
                if redirects >= _WEB_FETCH_MAX_REDIRECTS:
                    return f"Error: too many redirects fetching {original_url}"
                current_url = urljoin(current_url, location)
                redirects += 1
                continue
            return f"Error: HTTP {exc.code} fetching {current_url}"
        except urllib.error.URLError as exc:
            return f"Error: could not reach {current_url} - {exc.reason}"
        except Exception as exc:
            return f"Error fetching {current_url}: {exc}"

    if len(raw) > _WEB_FETCH_MAX_CHARS:
        raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"
    if "<html" in raw.lower() or "<body" in raw.lower():
        raw = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        if len(raw) > _WEB_FETCH_MAX_CHARS:
            raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"

    header = f"--- Source: {original_url} ---"
    if current_url != original_url:
        header += f"\n--- Final URL: {current_url} ---"
    return f"{header}\n{raw}\n--- End of fetched content ---"


def _prepare_fetch_target(url: str) -> FetchTarget | str:
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return "Error: URL must include a host"
    if parsed.username is not None or parsed.password is not None:
        return "Error: URL must not include credentials"
    try:
        port = parsed.port
    except ValueError:
        return "Error: URL has invalid port"

    resolved_ips = _resolve_hostname_ips(hostname)
    if not resolved_ips:
        return f"Error: could not resolve host ({hostname})"
    for ip_str in resolved_ips:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return f"Error: blocked private/internal host ({hostname})"
    first_ip = resolved_ips[0]
    ip_host = f"[{first_ip}]" if ":" in first_ip else first_ip
    netloc = ip_host if port is None else f"{ip_host}:{port}"
    safe_url = parsed._replace(netloc=netloc).geturl()
    host = f"[{hostname}]" if ":" in hostname else hostname
    host_header = host if port is None else f"{host}:{port}"
    return FetchTarget(safe_url=safe_url, host_header=host_header)


def _resolve_hostname_ips(hostname: str) -> list[str]:
    """Resolve a hostname to its IP addresses to prevent DNS rebinding."""
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return [str(sockaddr[0]) for _, _, _, _, sockaddr in addr_info]
