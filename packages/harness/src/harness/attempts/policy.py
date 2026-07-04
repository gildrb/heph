"""Static policy for structural answer-attempt guards."""

from __future__ import annotations

from harness.attempts.actions import FALLBACK_ACTION_ORDER, AttemptAction
from harness.attempts.observation import AttemptObservation


class StaticAttemptPolicy:
    """Dependency-free policy for deciding whether an answer attempt is acceptable."""

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
    if _has_acceptance_blocker(observation):
        return False
    if observation.citation_required and not observation.has_citations:
        return False
    return _citations_valid(observation) and (
        observation.evidence_sufficient or not observation.citation_required
    )


def _has_acceptance_blocker(observation: AttemptObservation) -> bool:
    return bool(
        observation.off_topic_answer
        or observation.unsupported_claim_count
        or observation.answer_shape_failed
        or observation.evidence_recommended_action == "abstain"
        or (observation.evidence_count > 0 and not observation.evidence_sufficient)
    )


def _should_abstain(observation: AttemptObservation) -> bool:
    return bool(
        observation.off_topic_answer
        or (
            observation.evidence_recommended_action == "abstain"
            and not observation.grounded_partial_progress
        )
    )


def _citations_valid(observation: AttemptObservation) -> bool:
    return bool(observation.all_citations_verified and not observation.unverified_citation_count)


def _needs_grounded_answer_retry(observation: AttemptObservation) -> bool:
    return bool(
        not observation.off_topic_answer
        and observation.citation_required
        and observation.evidence_count > 0
        and (
            observation.answer_shape_failed
            or not observation.has_citations
            or not observation.all_citations_verified
            or observation.unsupported_claim_count
            or observation.missing_required_citation_count
        )
    )


def _action_allowed(action: AttemptAction, observation: AttemptObservation) -> bool:
    if action is AttemptAction.RETRY_DIVERSIFY_SOURCES:
        return observation.distinct_source_count < 2 and observation.evidence_count > 0
    if action is AttemptAction.RETRY_SHORTER_ANSWER:
        return observation.reply_chars > 1200
    if action is AttemptAction.RETRY_OVERVIEW_SAMPLING:
        return observation.retrieval_strategy != "overview"
    if action is AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER:
        return observation.citation_required and bool(
            observation.answer_shape_failed
            or not observation.all_citations_verified
            or observation.unsupported_claim_count
            or observation.missing_required_citation_count
        )
    return action not in {AttemptAction.ACCEPT, AttemptAction.ABSTAIN}
