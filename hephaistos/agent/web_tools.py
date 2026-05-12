"""Network-facing tool handlers for the agent harness."""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

_WEB_FETCH_TIMEOUT = 15
_WEB_FETCH_MAX_CHARS = 20_000
_WEB_USER_AGENT = "Hephaistos/0.1 (study agent)"


def run_web_fetch(url: str, timeout: int | None = None, **_kwargs: object) -> str:
    """Fetch a URL and return the text content with source attribution."""
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    parsed = urlparse(url)
    hostname = parsed.hostname
    if hostname:
        resolved_ips = _resolve_hostname_ips(hostname)
        if not resolved_ips:
            return f"Error: could not resolve host ({hostname})"
        for ip_str in resolved_ips:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return f"Error: blocked private/internal host ({hostname})"
        first_ip = resolved_ips[0]
        ip_host = f"[{first_ip}]" if ":" in first_ip else first_ip
        netloc = parsed.netloc.replace(hostname, ip_host, 1)
        safe_url = parsed._replace(netloc=netloc).geturl()
        host_header = hostname if not parsed.port else f"{hostname}:{parsed.port}"
    else:
        safe_url = url
        host_header = None

    req = urllib.request.Request(safe_url, headers={"User-Agent": _WEB_USER_AGENT})
    if host_header:
        req.add_header("Host", host_header)
    try:
        with urllib.request.urlopen(req, timeout=timeout or _WEB_FETCH_TIMEOUT) as resp:  # nosec B310
            content_type = resp.headers.get("Content-Type", "")
            if not any(ct in content_type for ct in ("text", "json", "xml")):
                return f"Error: non-text content type ({content_type}). URL: {url}"
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return f"Error: HTTP {exc.code} fetching {url}"
    except urllib.error.URLError as exc:
        return f"Error: could not reach {url} - {exc.reason}"
    except Exception as exc:
        return f"Error fetching {url}: {exc}"
    if len(raw) > _WEB_FETCH_MAX_CHARS:
        raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"
    if "<html" in raw.lower() or "<body" in raw.lower():
        raw = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        if len(raw) > _WEB_FETCH_MAX_CHARS:
            raw = raw[:_WEB_FETCH_MAX_CHARS] + "\n... [truncated]"

    return f"--- Source: {url} ---\n{raw}\n--- End of fetched content ---"


def _resolve_hostname_ips(hostname: str) -> list[str]:
    """Resolve a hostname to its IP addresses to prevent DNS rebinding."""
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return [str(sockaddr[0]) for _, _, _, _, sockaddr in addr_info]
