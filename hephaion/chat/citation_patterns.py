"""Compiled citation and quote patterns shared by chat reply processing."""

from __future__ import annotations

import re

_EVIDENCE_CITATION_TEXT_RE = re.compile(
    r"\s*(?:\[|【)(?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*(?:\]|】)"
)
_ESCAPED_EVIDENCE_CITATION_RE = re.compile(r"\\\[((?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*)\\\]")
_PRIVATE_USE_EVIDENCE_CITATION_RE = re.compile(
    r"\ue200cite(?::|\ue202)((?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*)\ue201"
)
_INLINE_QUOTED_TEXT_RE = re.compile(r"[\"“”'](?P<text>[^\"“”']{2,80})[\"“”']")
_OVERVIEW_CITATION_ID_RE = re.compile(r"\[(?:e|E)(?P<id>\d+)\]")
_OVERVIEW_CITATION_BRACKET_RE = re.compile(
    r"\[(?P<body>\s*(?:e|E)\d+(?:\s*[,;]\s*(?:e|E)\d+)*\s*)\]"
)
_OVERVIEW_CITATION_TOKEN_RE = re.compile(r"(?:e|E)(?P<id>\d+)")
_OVERVIEW_CITATION_GROUP_RE = re.compile(r"\[(?:e|E)\d+\](?:(?:\s|,\s*)*\[(?:e|E)\d+\])+")
_TRAILING_EVIDENCE_CITATION_GROUP_RE = re.compile(r"(?:\s*\[(?:e|E)\d+\])+\s*$")
_CITATION_ONLY_REPLY_RE = re.compile(r"^\s*(?:\[(?:e|E)\d+\]\s*)+(?:[.,;:])?\s*$")
