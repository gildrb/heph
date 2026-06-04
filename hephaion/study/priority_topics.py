"""Topic validity helpers for priority analysis."""

from __future__ import annotations

import re


def valid_priority_topic(candidate: str, symbolic_token_re: re.Pattern[str]) -> bool:
    words = candidate.split()
    return bool(words and not _invalid_topic_words(words, symbolic_token_re) and len(words) <= 5)


def _invalid_topic_words(words: list[str], symbolic_token_re: re.Pattern[str]) -> bool:
    return any(_invalid_topic_word(word, symbolic_token_re) for word in words) or (
        len(words) == 1 and len(words[0]) < 4
    )


def _invalid_topic_word(word: str, symbolic_token_re: re.Pattern[str]) -> bool:
    return (
        word in {"administrative", "footer", "header"}
        or len(word) <= 1
        or (symbolic_token_re.fullmatch(word) is not None)
    )
