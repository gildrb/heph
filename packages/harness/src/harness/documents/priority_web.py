from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from collections.abc import Iterable, Iterator
from dataclasses import replace

from harness.documents.priority_types import (
    PriorityTopic,
    PriorityWebPrerequisite,
    PriorityWebSearcher,
    PriorityWebSearchResult,
)

_LETTER_RE = r"[^\W\d_]"
_WORD_BODY_RE = r"[\w+-]"
_WORD_SPLIT_RE = re.compile(rf"{_LETTER_RE}{_WORD_BODY_RE}*")
_WHITESPACE_RE = re.compile(r"\s+")
_WEB_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>'
    r".{0,1800}?"
    r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_WEB_PREREQ_TOPICS = 6
_WEB_PREREQ_RESULTS = 4
_WEB_PREREQ_TIMEOUT = 8
_WEB_PREREQ_USER_AGENT = "Heph/0.1 priority prerequisites"
_WEB_PREREQ_SEARCH_URL = "https://duckduckgo.com/html/"


def with_web_prerequisites(
    topics: list[PriorityTopic],
    web_searcher: PriorityWebSearcher | None,
) -> list[PriorityTopic]:
    if web_searcher is None:
        return topics
    enriched: list[PriorityTopic] = []
    for index, topic in enumerate(topics):
        if index >= _WEB_PREREQ_TOPICS or topic.prerequisites:
            enriched.append(topic)
            continue
        web_prerequisites = _web_prerequisites_for(topic.topic, web_searcher)
        enriched.append(replace(topic, web_prerequisites=web_prerequisites))
    return enriched


def _web_prerequisites_for(
    topic: str,
    web_searcher: PriorityWebSearcher,
) -> tuple[PriorityWebPrerequisite, ...]:
    prerequisites: list[PriorityWebPrerequisite] = []
    seen: set[str] = set()
    for result in tuple(web_searcher(f"{topic} prerequisites"))[:_WEB_PREREQ_RESULTS]:
        for term in _explicit_prerequisite_phrases(result.snippet):
            if term in seen:
                continue
            seen.add(term)
            prerequisites.append(
                PriorityWebPrerequisite(
                    term=term,
                    source_title=result.title,
                    source_url=result.url,
                )
            )
    return tuple(prerequisites)


def _explicit_prerequisite_phrases(text: str) -> list[str]:
    prerequisites: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"\bprerequisites?\s*:\s*([^.\n]+)", text, flags=re.IGNORECASE):
        for raw_part in re.split(r",|\band\b", match.group(1), flags=re.IGNORECASE):
            tokens = [
                token.lower()
                for token in _WORD_SPLIT_RE.findall(raw_part)
                if len(token) >= 3 and not token.isdigit()
            ]
            if not tokens:
                continue
            phrase = " ".join(tokens[:3])
            if phrase in seen:
                continue
            seen.add(phrase)
            prerequisites.append(phrase)
    return prerequisites


def duckduckgo_search(query: str) -> Iterable[PriorityWebSearchResult]:
    params = urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        f"{_WEB_PREREQ_SEARCH_URL}?{params}",
        headers={"User-Agent": _WEB_PREREQ_USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=_WEB_PREREQ_TIMEOUT) as response:  # nosec B310
        raw_html = response.read().decode("utf-8", errors="replace")
    return tuple(_parse_duckduckgo_results(raw_html))


_duckduckgo_search = duckduckgo_search


def _parse_duckduckgo_results(raw_html: str) -> Iterator[PriorityWebSearchResult]:
    for match in _WEB_RESULT_RE.finditer(raw_html):
        url = html.unescape(match.group("url"))
        title = _clean_web_text(match.group("title"))
        snippet = _clean_web_text(match.group("snippet"))
        if title and url and snippet:
            yield PriorityWebSearchResult(title=title, url=url, snippet=snippet)


def _clean_web_text(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value)
    return _WHITESPACE_RE.sub(" ", html.unescape(no_tags)).strip()
