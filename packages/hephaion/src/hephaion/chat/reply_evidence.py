"""Reply citation evidence state."""

from __future__ import annotations

from dataclasses import replace

from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.prior_answer import _evidence_item_ref
from hephaion.chat.reply_repair import _reply_evidence_ids
from hephaion.rag.context import TurnEvidence


def _resolved_with_visible_evidence_refs(
    resolved: ResolvedTurnPlan,
    reply: str,
    visible_evidence: TurnEvidence | None,
) -> ResolvedTurnPlan:
    contract = resolved.turn_contract
    if contract is None:
        return resolved
    return replace(
        resolved,
        turn_contract=replace(
            contract,
            evidence_refs=tuple(_reply_cited_evidence_refs(reply, visible_evidence)),
        ),
    )


def _reply_cited_evidence_refs(
    reply: str,
    evidence: TurnEvidence | None,
) -> list[str]:
    if evidence is None or not evidence.items:
        return []
    return _deduplicated_cited_refs(
        _reply_evidence_ids(reply),
        _evidence_ref_by_id(evidence),
    )


def _evidence_ref_by_id(evidence: TurnEvidence) -> dict[str, str]:
    return {item.evidence_id.casefold(): _evidence_item_ref(item) for item in evidence.items}


def _deduplicated_cited_refs(
    evidence_ids: tuple[str, ...],
    ref_by_id: dict[str, str],
) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for evidence_id in evidence_ids:
        ref = ref_by_id.get(evidence_id.casefold())
        if ref is None or ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)
    return refs
