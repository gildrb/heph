"""Reply text localization, cleanup, and normalization helpers."""

from __future__ import annotations

import json
import re

import unicodeit
from ai.runtime.engine import (
    ChatConfig,
    Conversation,
    EngineError,
    RetryConfig,
    build_client,
    stream_completion,
)

from hephaion._types import is_string_mapping
from hephaion.chat.citation_patterns import _OVERVIEW_CITATION_ID_RE

_LATEX_INLINE_MATH_RE = re.compile(r"\\\((?P<expr>.+?)\\\)")
_LATEX_DISPLAY_MATH_RE = re.compile(r"\\\[(?P<expr>.+?)\\\]", re.DOTALL)
_LATEX_BARE_MATHBB_RE = re.compile(r"\\mathbb\s+(?P<symbol>[A-Za-z])")
_TOOL_CALL_BLOCK_RE = re.compile(r"<tool_call\b[^>]*>.*?</tool_call>", re.IGNORECASE | re.DOTALL)
_TOOL_CALL_OPEN_RE = re.compile(r"<tool_call\b[^>]*>", re.IGNORECASE)
_TOOL_CALL_CLOSE_RE = re.compile(r"</tool_call>", re.IGNORECASE)
_DETERMINISTIC_REPLY_LITERAL_RE = re.compile(r"`[^`]+`|/[\w-]+|\"[^\"]+\"")
_ASSESSMENT_LABEL_RE = re.compile(r"^(?:CORRECT|PARTIAL|WRONG):")
_LEADING_CONTROL_JSON_KEYS = frozenset(
    {
        "canonical_english_request",
        "confidence",
        "intent",
        "query",
        "retrieval_query",
        "topic",
    }
)
_MALFORMED_LEADING_CONTROL_JSON_RE = re.compile(
    r"(?is)^\s*\{\s*\"(?:"
    + "|".join(re.escape(key) for key in sorted(_LEADING_CONTROL_JSON_KEYS))
    + r")\"\s*:\s*.*?\}\s*(?=[A-ZÄÖÜ])"
)
_DETERMINISTIC_FALLBACK_LOCALIZATION_PROMPT = """
Rewrite an internal English fallback message for the user. Use the same language as the user's
request when clear. If the request is English or the language is unclear, return the original
English message. Preserve command literals, slash commands, paths, and quoted phrases exactly.
Preserve any leading CORRECT:, PARTIAL:, or WRONG: assessment label exactly.
Do not add facts, citations, source claims, apologies, or next actions.
Return plain text only.
""".strip()


def _localize_deterministic_reply(
    reply: str,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> str:
    if not _should_localize_deterministic_reply(reply, user_input=user_input, config=config):
        return reply

    localized = _localized_deterministic_reply(reply, user_input=user_input, config=config)
    return localized if _valid_localized_deterministic_reply(localized, original=reply) else reply


def _should_localize_deterministic_reply(
    reply: str,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> bool:
    return (
        bool(reply.strip())
        and bool(user_input.strip())
        and config is not None
        and bool(config.base_url)
        and bool(config.model)
    )


def _localized_deterministic_reply(
    reply: str,
    *,
    user_input: str,
    config: ChatConfig | None,
) -> str:
    if config is None:
        return ""
    conversation = Conversation()
    conversation.add("system", _DETERMINISTIC_FALLBACK_LOCALIZATION_PROMPT)
    conversation.add(
        "user",
        f"User request:\n{user_input.strip()}\n\nFallback message:\n{reply.strip()}",
    )
    parts: list[str] = []
    try:
        parts.extend(
            delta.content
            for delta in stream_completion(
                config,
                conversation,
                retry=RetryConfig(max_retries=1),
                client_factory=build_client,
            )
            if delta.content
        )
    except EngineError:
        return ""
    return _strip_tool_call_markup("".join(parts)).strip()


def _valid_localized_deterministic_reply(localized: str, *, original: str) -> bool:
    return (
        bool(localized)
        and not _localized_reply_too_long(localized, original)
        and not _localized_reply_adds_citations(localized, original)
        and _localized_reply_preserves_assessment_label(localized, original)
        and _localized_reply_preserves_literals(localized, original)
    )


def _localized_reply_too_long(localized: str, original: str) -> bool:
    return len(localized) > max(len(original) * 3, len(original) + 600)


def _localized_reply_adds_citations(localized: str, original: str) -> bool:
    return bool(_OVERVIEW_CITATION_ID_RE.search(localized)) and not bool(
        _OVERVIEW_CITATION_ID_RE.search(original)
    )


def _localized_reply_preserves_assessment_label(localized: str, original: str) -> bool:
    assessment_label = _ASSESSMENT_LABEL_RE.match(original.strip())
    return assessment_label is None or localized.startswith(assessment_label.group(0))


def _localized_reply_preserves_literals(localized: str, original: str) -> bool:
    literals = _DETERMINISTIC_REPLY_LITERAL_RE.findall(original)
    return all(literal in localized for literal in literals)


def _unicode_math_reply(reply: str) -> str:
    converted = _LATEX_DISPLAY_MATH_RE.sub(_unicode_math_match, reply)
    converted = _LATEX_INLINE_MATH_RE.sub(_unicode_math_match, converted)
    return _LATEX_BARE_MATHBB_RE.sub(_unicode_bare_mathbb_match, converted)


def _unicode_math_match(match: re.Match[str]) -> str:
    expression = match.group("expr").strip()
    converted = unicodeit.replace(expression)
    if _unicode_math_conversion_is_suspicious(converted):
        return expression
    return converted


def _unicode_bare_mathbb_match(match: re.Match[str]) -> str:
    expression = rf"\mathbb{{{match.group('symbol')}}}"
    converted = unicodeit.replace(expression)
    if _unicode_math_conversion_is_suspicious(converted):
        return match.group(0)
    return converted


def _unicode_math_conversion_is_suspicious(converted: str) -> bool:
    return "ł" in converted or "Ł" in converted


def _strip_leading_control_json(reply: str) -> str:
    if not reply.startswith("{"):
        return reply
    try:
        payload, end = json.JSONDecoder().raw_decode(reply)
    except json.JSONDecodeError:
        return _strip_malformed_leading_control_json(reply)
    tail = reply[end:].lstrip()
    if not tail or not is_string_mapping(payload):
        return reply
    if _LEADING_CONTROL_JSON_KEYS.isdisjoint(payload):
        return reply
    return tail


def _strip_malformed_leading_control_json(reply: str) -> str:
    match = _MALFORMED_LEADING_CONTROL_JSON_RE.match(reply)
    return reply[match.end() :].lstrip() if match else reply


def _strip_unsolicited_learning_followup(reply: str) -> str:
    if not reply.strip():
        return reply
    return _strip_uncited_tail_after_last_citation(reply)


def _strip_uncited_tail_after_last_citation(reply: str) -> str:
    citation_end = _last_citation_end(reply)
    if citation_end is None:
        return reply.strip()
    keep_end = _citation_tail_keep_end(reply, citation_end)
    if not reply[keep_end:].strip():
        return reply.strip()
    return reply[:keep_end].rstrip()


def _has_uncited_tail_after_last_citation(reply: str) -> bool:
    citation_end = _last_citation_end(reply)
    if citation_end is None:
        return False
    keep_end = _citation_tail_keep_end(reply, citation_end)
    return bool(reply[keep_end:].strip())


def _last_citation_end(reply: str) -> int | None:
    matches = tuple(_OVERVIEW_CITATION_ID_RE.finditer(reply))
    if not matches:
        return None
    return matches[-1].end()


def _citation_tail_keep_end(reply: str, citation_end: int) -> int:
    keep_end = citation_end
    while keep_end < len(reply) and reply[keep_end] in " \t.,;:)]}":
        keep_end += 1
    return keep_end


def _strip_tool_call_markup(reply: str) -> str:
    cleaned = _TOOL_CALL_BLOCK_RE.sub("", reply)
    cleaned = _TOOL_CALL_OPEN_RE.sub("", cleaned)
    cleaned = _TOOL_CALL_CLOSE_RE.sub("", cleaned)
    kept_lines = [line for line in cleaned.splitlines() if "<tool_call" not in line.casefold()]
    return "\n".join(kept_lines)
