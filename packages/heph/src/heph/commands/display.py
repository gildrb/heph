from __future__ import annotations

from pathlib import Path

from hephaion.chat.session import ChatSession
from hephaion.rag.context import EvidenceChunk, TurnEvidence
from hephaion.rag.source_mapping import (
    SourceLineSpan,
    SourceMappingError,
    chunk_line_span,
    evidence_location_label,
    resolve_source_path,
    source_excerpt,
)
from interfaces.terminal import print_error, print_info, print_success
from interfaces.terminal.source_open import open_source_file

from heph.commands._base import (
    Command,
    CommandResult,
    ensure_session,
)

_VISIBILITY_ON = ("show", "on", "yes", "true", "1")
_VISIBILITY_OFF = ("hide", "off", "no", "false", "0")


def _evidence_request(args: str) -> tuple[str | None, bool]:
    tokens = args.strip().split()
    open_requested = any(token.lower() in {"open", "source"} for token in tokens)
    evidence_id = next(
        (evidence_id for token in tokens if (evidence_id := _evidence_id_from_token(token))),
        None,
    )
    return evidence_id, open_requested


def _evidence_id_from_token(token: str) -> str | None:
    cleaned = token.strip("[](),;:").upper()
    if cleaned.startswith("E") and cleaned[1:].isdigit():
        return cleaned
    if cleaned.isdigit():
        return f"E{cleaned}"
    return None


def _item_path_and_span(
    session: ChatSession,
    item: EvidenceChunk,
) -> tuple[Path | None, SourceLineSpan | None]:
    if session.armory_path is None:
        return None, None
    try:
        path = resolve_source_path(session.armory_path, item.source)
    except SourceMappingError:
        return None, None
    return path, chunk_line_span(path, item.chunk)


def _format_evidence_overview(session: ChatSession, items: tuple[EvidenceChunk, ...]) -> str:
    lines = ["Last turn sources:"]
    previous_source: str | None = None
    for item in items:
        if item.source != previous_source:
            lines.append(f"  {item.source}")
            previous_source = item.source
        lines.extend(_format_evidence_overview_item(session, item))
    lines += [
        "",
        "Expand exact source text: /evidence E1",
        "Open source at line:      /evidence E1 open",
    ]
    return "\n".join(lines)


def _format_evidence_overview_item(session: ChatSession, item: EvidenceChunk) -> list[str]:
    _, span = _item_path_and_span(session, item)
    location = evidence_location_label(item.source, item.chunk, span)
    lines = [f"    {item.evidence_id}  {location}; score={item.score:.3f}"]
    if item.chunk.heading:
        lines.append(f"      heading: {item.chunk.heading}")
    lines += [
        f"      expand: /evidence {item.evidence_id}",
        f"      open:   /evidence {item.evidence_id} open",
    ]
    return lines


def _format_evidence_detail(session: ChatSession, item: EvidenceChunk) -> str:
    path, span = _item_path_and_span(session, item)
    source = item.source if path is None else str(path)
    location = evidence_location_label(item.source, item.chunk, span)
    lines = [
        f"{item.evidence_id}  {source}",
        f"{location}; score={item.score:.3f}",
    ]
    if item.chunk.heading:
        lines.append(f"heading: {item.chunk.heading}")
    lines += ["", "Source text:"]
    excerpt = source_excerpt(path, item.chunk) if path is not None else ""
    lines.append(excerpt or item.content)
    lines += ["", f"Open source: /evidence {item.evidence_id} open"]
    return "\n".join(lines)


def _open_evidence_item(session: ChatSession, item: EvidenceChunk) -> None:
    if session.armory_path is None:
        print_error("No armory attached; cannot open evidence source.")
        return
    try:
        path = resolve_source_path(session.armory_path, item.source)
    except SourceMappingError as exc:
        print_error(str(exc))
        return
    if not path.exists():
        print_error(f"Evidence source not found: {path}")
        return
    span = chunk_line_span(path, item.chunk)
    line = span.start_line if span is not None else None
    try:
        result = open_source_file(path, line)
    except OSError as exc:
        print_error(str(exc))
        return
    print_success(result.message)


def _update_visibility(session: ChatSession, args: str, attr: str, label: str, usage: str) -> None:
    value = args.strip().lower()
    if value in _VISIBILITY_ON:
        visible = True
    elif value in _VISIBILITY_OFF:
        visible = False
    elif value:
        print_error(usage)
        return
    else:
        visible = not bool(getattr(session, attr))
    setattr(session, attr, visible)
    state = "shown" if visible else "hidden"
    print_success(f"{label} {state}.")


class EvidenceCommand(Command):
    name = "evidence"
    description = "Show retrieved evidence for the last turn"
    aliases = ("sources",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        evidence = s.last_turn_evidence
        if evidence is None or not evidence.items:
            print_info("No evidence was retrieved for the last turn.")
            return CommandResult()

        evidence_id, open_requested = _evidence_request(args)
        if evidence_id is not None:
            return _handle_evidence_item(s, evidence, evidence_id, open_requested)

        if open_requested:
            print_error("Usage: /evidence <EID> open")
            return CommandResult()

        print(_format_evidence_overview(s, evidence.items))
        return CommandResult()


def _handle_evidence_item(
    session: ChatSession,
    evidence: TurnEvidence,
    evidence_id: str,
    open_requested: bool,
) -> CommandResult:
    item = evidence.get(evidence_id)
    if item is None:
        print_error(f"Unknown evidence ID: {evidence_id}")
        return CommandResult()
    if open_requested:
        _open_evidence_item(session, item)
    else:
        print(_format_evidence_detail(session, item))
    return CommandResult()


class TokensCommand(Command):
    name = "tokens"
    description = "Show or hide live token estimates"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        _update_visibility(
            s, args, "live_tokens_visible", "Live tokens", "Usage: /tokens [show|hide]"
        )
        return CommandResult()


class CostCommand(Command):
    name = "cost"
    description = "Show or hide live cost estimates"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        _update_visibility(s, args, "live_cost_visible", "Live cost", "Usage: /cost [show|hide]")
        return CommandResult()
