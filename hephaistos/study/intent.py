"""Shared deterministic intent helpers for study turn routing."""

from __future__ import annotations

import re

_MATERIAL_REFERENCE_RE = (
    r"(?:"
    r"source(?: files?| materials?)?|sources?|indexed "
    r"(?:source|sources|materials?|documents?)|"
    r"materials?|source materials?|course materials?|documents?|docs?|files?|"
    r"notes?|lecture notes?|course notes?|class notes?|"
    r"lectures?|slides?|slide decks?|handouts?|pdfs?|ppts?|readings?|textbooks?|"
    r"books?|workbooks?|worksheets?|exercise sheets?|assignments?|homework|"
    r"problem sets?|labs?|lab manuals?|syllabus|syllabi|rubrics?|mark schemes?|"
    r"solution sheets?|answer keys?|papers?|articles?|chapters?|study guides?|"
    r"course packs?|packets?|uploaded (?:files?|materials?|documents?)|"
    r"attached (?:files?|materials?|documents?)|provided (?:files?|materials?|documents?)"
    r")"
)
_MATERIAL_REFERENCE_OWNER_RE = r"(?:the\s+|my\s+|your\s+|our\s+)?"
_MATERIAL_SOURCE_REQUEST_RE = re.compile(
    rf"\b(?:using|use|from|based on|according to)\s+(?:only\s+)?"
    rf"{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\b|"
    rf"\bbase\s+(?:it|this|that|your\s+answer|the\s+answer)\s+on\s+"
    rf"(?:only\s+)?{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\b|"
    rf"\b(?:rely\s+(?:only\s+)?on|stick\s+to)\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\b|"
    rf"\b(?:cite|quote)\s+{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\b|"
    rf"\b(?:cite|quote)\s+.{{0,80}}?\b(?:from|in)\s+"
    rf"{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\b|"
    rf"\b(?:show|tell)\s+me\s+where\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\s+"
    r"(?:says?|states?|mentions?|covers?|contains?|includes?|defines?|describes?|"
    r"explains?|shows?)\b|"
    rf"\b(?:point|direct)\s+me\s+to\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\b|"
    rf"\bwhich\s+{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\s+"
    r"(?:says?|states?|mentions?|covers?|contains?|includes?|defines?|describes?|"
    r"explains?|shows?)\b|"
    rf"\bwhat\s+(?:does|do|did)\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\s+"
    r"(?:say|state|mention|call|define|describe|cover|include|ask|require|expect|"
    r"explain|show|prove|derive|solve|discuss)\b|"
    rf"\b(?:does|do|did)\s+{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\s+"
    r"(?:say|state|mention|call|define|describe|cover|include|ask|require|expect|"
    r"explain|show|prove|derive|solve|discuss)\b|"
    rf"\b(?:find|search|look\s+up|look\s+for|check)\s+.{{0,80}}?"
    rf"\b(?:in|through|within|from)\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\b|"
    rf"\b(?:find|search|look\s+through|check)\s+"
    rf"{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\s+"
    r"(?:for|about|on)\b|"
    rf"\b(?:summari[sz]e|outline)\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\b|"
    rf"\b(?:summari[sz]e|outline|list)\s+.{{0,80}}?"
    rf"\b(?:in|from|using|based\s+on|according\s+to)\s+"
    rf"{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\b|"
    r"\b(?:which|what)\s+(?:page|pages|slide|slides|section|chapter)\s+"
    r"(?:mentions?|covers?|explains?|defines?|describes?|contains?|includes?)\b|"
    rf"\bin\s+{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\b|"
    r"\banswer with (?:just )?(?:the )?exact\b|"
    r"\bexact (?:phrase|wording)\b",
    re.IGNORECASE,
)
_MATERIAL_SOURCE_ONLY_SAFETY_RE = re.compile(
    rf"\b(?:if|when)\s+{_MATERIAL_REFERENCE_OWNER_RE}{_MATERIAL_REFERENCE_RE}\s+"
    r"(?:(?:does|do)\s+not|doesn'?t|don'?t)\s+"
    r"(?:contain|cover|include|mention|say|state|define|describe|explain|show)\b|"
    rf"\b(?:if|when)\s+(?:it|this|that|the\s+answer)\s+(?:is\s+)?"
    rf"(?:not|isn'?t)\s+(?:in|from)\s+{_MATERIAL_REFERENCE_OWNER_RE}"
    rf"{_MATERIAL_REFERENCE_RE}\b",
    re.IGNORECASE,
)
_SOURCE_ONLY_POLICY_FRAGMENT = (
    r"(?:"
    r"(?:do\s+not|don'?t)\s+(?:guess|hallucinate|invent|use\s+outside\s+knowledge)|"
    r"(?:do\s+not|don'?t)\s+make\s+(?:it|things|stuff|anything)?\s*up|"
    r"no\s+outside\s+knowledge|"
    r"(?:say|tell\s+me)\s+(?:if\s+)?(?:you\s+)?(?:do\s+not|don'?t)\s+know"
    r")"
)
_SOURCE_ONLY_POLICY_RE = re.compile(
    rf"\b{_SOURCE_ONLY_POLICY_FRAGMENT}\b",
    re.IGNORECASE,
)
_STANDALONE_SOURCE_ONLY_POLICY_RE = re.compile(
    rf"^(?:please\s+)?{_SOURCE_ONLY_POLICY_FRAGMENT}[.!?]?$",
    re.IGNORECASE,
)
_NEW_TOPIC_REQUEST_RE = re.compile(
    r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
    r"(?:"
    r"explain|teach(?:\s+me)?|walk\s+me\s+through|go\s+over|review|study|"
    r"help\s+me\s+(?:study|understand)|tell\s+me\s+about|compare|"
    r"(?:can|could|would)\s+we\s+do|do|work\s+on|move(?:\s+on)?\s+to|"
    r"switch(?:\s+over)?\s+to|start|next\s+topic:?|"
    r"let'?s\s+(?:do|study|work\s+on|start|move(?:\s+on)?\s+to|switch(?:\s+over)?\s+to)|"
    r"i\s+(?:want|would\s+like)\s+to\s+(?:study|do|work\s+on|start)|"
    r"give\s+me\s+(?:an?\s+)?example\s+of|show\s+me\s+(?:an?\s+)?example\s+of|"
    r"what\s+(?:is|are)\s+the\s+differences?\s+between"
    r")\s+(?P<topic>[^.?!]{3,180}?)(?:\s+with\s+me)?[.?!]?\s*$",
    re.IGNORECASE,
)
_MATERIAL_DRILL_REQUEST_RE = (
    re.compile(
        r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
        r"(?:quiz|test|drill)\s+me\s+(?:on|about|with)\s+"
        r"(?P<topic>[^.?!]{3,180})[.?!]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
        r"ask\s+me\s+(?:a|one|some)?\s*"
        r"(?:active[-\s]?recall\s+|practice\s+|exam[-\s]?style\s+)?"
        r"questions?\s+(?:on|about|from)\s+"
        r"(?P<topic>[^.?!]{3,180})[.?!]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
        r"(?:practice|practise)\s+(?P<topic>[^.?!]{3,180}?)\s+with\s+me[.?!]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?"
        r"give\s+me\s+(?:an?\s+)?"
        r"(?:active[-\s]?recall\s+|practice\s+|exam[-\s]?style\s+)?"
        r"questions?\s+(?:on|about|from)\s+"
        r"(?P<topic>[^.?!]{3,180})[.?!]?\s*$",
        re.IGNORECASE,
    ),
)
_FOLLOWUP_TOPIC_REFERENTS = frozenset(
    {
        "again",
        "answer",
        "current item",
        "it",
        "material",
        "more",
        "prompt",
        "question",
        "solution",
        "that",
        "the answer",
        "the current item",
        "the material",
        "the prompt",
        "the question",
        "the solution",
        "this",
        "why",
    }
)
_FOLLOWUP_TOPIC_REFERENT_RE = re.compile(
    r"^(?:"
    r"(?:the\s+)?(?:answer|current\s+item|material|prompt|question|solution)|"
    r"(?:it|this|that)(?:\s+(?:concept|item|one|prompt|question|topic))?|"
    r"why"
    r")(?:\s+(?:again|once\s+more|one\s+more\s+time))?$",
    re.IGNORECASE,
)
_REFERENT_ONLY_WORDS = frozenset(
    {
        "about",
        "again",
        "an",
        "and",
        "answer",
        "between",
        "concept",
        "current",
        "example",
        "it",
        "item",
        "material",
        "of",
        "one",
        "prompt",
        "question",
        "solution",
        "that",
        "the",
        "this",
        "topic",
        "why",
        "with",
    }
)
_TOPIC_WORD_RE = re.compile(r"[^\W\d_][\w+-]{1,}")


def is_material_source_request(text: str) -> bool:
    normalized = _normalize(text)
    return bool(
        _MATERIAL_SOURCE_REQUEST_RE.search(normalized)
        or _MATERIAL_SOURCE_ONLY_SAFETY_RE.search(normalized)
    )


def is_source_only_query(text: str) -> bool:
    normalized = _normalize(text)
    return bool(
        _MATERIAL_SOURCE_REQUEST_RE.search(normalized)
        or _MATERIAL_SOURCE_ONLY_SAFETY_RE.search(normalized)
        or _SOURCE_ONLY_POLICY_RE.search(normalized)
    )


def is_source_only_policy(text: str) -> bool:
    return bool(_SOURCE_ONLY_POLICY_RE.search(_normalize(text)))


def is_standalone_source_only_policy(text: str) -> bool:
    return bool(_STANDALONE_SOURCE_ONLY_POLICY_RE.fullmatch(_normalize(text)))


def material_drill_query(text: str) -> str | None:
    normalized = _normalize(text)
    for pattern in _MATERIAL_DRILL_REQUEST_RE:
        match = pattern.search(normalized)
        if match is None:
            continue
        topic = _normalize(match.group("topic").strip(" .?!:;"))
        words = [word.casefold() for word in _TOPIC_WORD_RE.findall(topic)]
        if any(word not in _REFERENT_ONLY_WORDS for word in words):
            return topic
    return None


def is_new_material_topic_request(text: str) -> bool:
    normalized = _normalize(text)
    if _SOURCE_ONLY_POLICY_RE.search(normalized):
        return False
    match = _NEW_TOPIC_REQUEST_RE.search(normalized)
    if match is None:
        return False
    topic = _normalize(match.group("topic").strip(" .?!:;"))
    words = [word.casefold() for word in _TOPIC_WORD_RE.findall(topic)]
    return (
        bool(topic)
        and topic.casefold() not in _FOLLOWUP_TOPIC_REFERENTS
        and not (_FOLLOWUP_TOPIC_REFERENT_RE.search(topic))
        and any(word not in _REFERENT_ONLY_WORDS for word in words)
    )


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())
