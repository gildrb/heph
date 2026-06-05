"""Discrete harness actions for local attempt-policy learning."""

from __future__ import annotations

from enum import StrEnum


class AttemptAction(StrEnum):
    ACCEPT = "accept"
    ABSTAIN = "abstain"
    RETRY_REWRITE_QUERY = "retry_rewrite_query"
    RETRY_EXPAND_EVIDENCE = "retry_expand_evidence"
    RETRY_DIVERSIFY_SOURCES = "retry_diversify_sources"
    RETRY_NEIGHBOR_CHUNKS = "retry_neighbor_chunks"
    RETRY_STRICTER_GROUNDED_ANSWER = "retry_stricter_grounded_answer"
    RETRY_SHORTER_ANSWER = "retry_shorter_answer"
    RETRY_OVERVIEW_SAMPLING = "retry_overview_sampling"


FALLBACK_ACTION_ORDER: tuple[AttemptAction, ...] = (
    AttemptAction.RETRY_EXPAND_EVIDENCE,
    AttemptAction.RETRY_DIVERSIFY_SOURCES,
    AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER,
    AttemptAction.RETRY_REWRITE_QUERY,
    AttemptAction.RETRY_NEIGHBOR_CHUNKS,
    AttemptAction.RETRY_SHORTER_ANSWER,
    AttemptAction.RETRY_OVERVIEW_SAMPLING,
    AttemptAction.ABSTAIN,
)


def parse_attempt_action(value: object) -> AttemptAction:
    if isinstance(value, AttemptAction):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        for action in AttemptAction:
            if action.value == normalized:
                return action
    return AttemptAction.ACCEPT
