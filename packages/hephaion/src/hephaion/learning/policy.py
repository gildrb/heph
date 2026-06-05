"""Policy fallback for local harness-attempt actions."""

from __future__ import annotations

from hephaion.learning.actions import FALLBACK_ACTION_ORDER, AttemptAction
from hephaion.learning.observation import AttemptObservation


class StaticAttemptPolicy:
    """Dependency-free fallback policy used when no trained policy is available."""

    def choose(self, observation: AttemptObservation) -> AttemptAction:
        if _can_accept(observation):
            return AttemptAction.ACCEPT
        if _should_abstain(observation):
            return AttemptAction.ABSTAIN
        if _needs_grounded_answer_retry(observation):
            return AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER
        for action in FALLBACK_ACTION_ORDER:
            if _action_allowed(action, observation):
                return action
        return AttemptAction.ABSTAIN


def _can_accept(observation: AttemptObservation) -> bool:
    if observation.reply_chars <= 0:
        return False
    if observation.citation_required and not observation.has_citations:
        return False
    return observation.all_citations_verified and (
        observation.evidence_sufficient or not observation.citation_required
    )


def _should_abstain(observation: AttemptObservation) -> bool:
    return bool(
        observation.evidence_recommended_action == "abstain" and observation.attempt_index >= 2
    )


def _needs_grounded_answer_retry(observation: AttemptObservation) -> bool:
    return bool(
        observation.citation_required
        and observation.evidence_count > 0
        and (not observation.has_citations or not observation.all_citations_verified)
    )


def _action_allowed(action: AttemptAction, observation: AttemptObservation) -> bool:
    if action is AttemptAction.RETRY_DIVERSIFY_SOURCES:
        return observation.distinct_source_count < 2 and observation.evidence_count > 0
    if action is AttemptAction.RETRY_SHORTER_ANSWER:
        return observation.reply_chars > 1200
    if action is AttemptAction.RETRY_OVERVIEW_SAMPLING:
        return observation.retrieval_strategy != "overview"
    if action is AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER:
        return observation.citation_required and not observation.all_citations_verified
    return action not in {AttemptAction.ACCEPT, AttemptAction.ABSTAIN}
