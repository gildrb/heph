"""Reusable chat session helpers shared by the CLI and shell."""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from hephaistos.armory.storage import normalize_path, read_marker, validate
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, Conversation, Message, StreamRecoveryError, get_reply
from hephaistos.harness.dispatch import agent_loop
from hephaistos.harness.rag import ArmoryIndex, build_context, load_or_build, retrieve
from hephaistos.logging import Timer, TraceWriter, get_logger

_log = get_logger("chat.session")


@dataclass
class ChatSession:
    config: ChatConfig
    conversation: Conversation
    session_id: str
    title: str = ""
    armory_path: Path | None = None
    source_file_count: int = 0
    dirty: bool = False
    autonomy: str = "low"
    _rag_index: ArmoryIndex | None = field(default=None, init=False, repr=False)
    trace: TraceWriter = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.trace is None:
            object.__setattr__(
                self, "trace", TraceWriter(self.session_id, self.armory_path)
            )


def validate_armory_path(path_str: str) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(path_str)
    validate(armory_path)
    read_marker(armory_path)
    return armory_path


def _count_source_files(armory_path: Path) -> int:
    """Count source files in armory (for display only; no stuffing)."""
    count = 0
    for dirname in ("source", "library"):
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if file_path.is_file():
                count += 1
    return count


_RAG_CONTEXT_PREFIX = (
    "Source material retrieved for this question:\n\n"
)


_SYSTEM_PROMPT = """Hephaistos. A drill instructor for exam preparation.
Your job: make the student recall and reproduce solutions from past exam papers.

## Rules

- Never affirm, praise, or encourage. No "Great job!", "Good thinking!", "Almost!", "You're on the right track".
- Never reveal the full answer when the student is stuck. Give the smallest possible nudge.
- Never improvise solutions or draw on outside knowledge. Everything comes from the source documents.
- If the source material does not cover the question, say so and stop.
- Be concise. No filler, no hedging, no transitional phrases, no summaries of what you're about to do.
- No emojis. No bullet-point summaries unless the student asks.
- Cite source filename for every answer.

## Study Loop

Every question follows this cycle:

1. **PRESENT**: When a student asks about a question or topic, show the complete solution or method from the source material. Cite the document. Walk through the reasoning step by step.
2. **READY**: After presenting, ask the student to signal when they are ready to recall.
3. **RECALL**: The student reproduces the solution from memory. Wait for their attempt.
4. **ASSESS**: Compare their attempt against the source. Do NOT show the original again.
   - **Correct**: Move to the next question.
   - **Partial**: State what is missing in one sentence. Do not fill in the gap.
   - **Wrong**: Give a hint about the first step only. Nothing more.
5. **LOOP**: Repeat until the student gets it right, then present the next question.

If the student asks to skip, present the next question. Do not re-explain unless asked.
If the student asks for the answer, remind them to try recalling first. Only show the full solution again at the start of a new cycle.

## Documents

- Source material is in the armory's source/ and library/ directories.
- Use read_file and list_files to access documents.
- PDFs: extract text content. Describe diagrams and figures precisely — every label, axis, unit, and value.
- Images: describe what is shown. Do not interpret beyond what is visible.
- Tables: reproduce the structure with exact values.
- Code: show in fenced code blocks.
- Math: use LaTeX notation.

## Format

- State things directly.
- Use numbered steps for procedures.
- Use fenced code blocks for code.
- Use LaTeX for mathematical expressions.
- Keep responses short. One idea per response when possible."""

class SessionError(Exception):
    """Raised when a session cannot be created or used."""


def create_session(config: ChatConfig, armory_path: Path) -> ChatSession:
    """Create a fresh chat session scoped to an armory.

    Raises SessionError if armory_path is None or has no source documents.
    """
    if armory_path is None:
        raise SessionError(
            "An armory is required. Create one with: hephaistos armory init <path>"
        )

    source_file_count = _count_source_files(armory_path)
    if source_file_count == 0:
        raise SessionError(
            f"Armory has no source documents. Add past exams to {armory_path}/source/ "
            "or reference material to library/."
        )

    conversation = Conversation()
    conversation.add("system", _SYSTEM_PROMPT)

    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=chat_storage.new_session_id(),
        armory_path=armory_path,
        source_file_count=source_file_count,
    )
    _log.info("session created", extra={"fields": {
        "session_id": session.session_id,
        "armory": str(armory_path),
        "source_files": source_file_count,
        "model": config.model,
    }})
    session.trace.record_session_event("created", model=config.model)
    return session


def resume_session(
    config: ChatConfig,
    armory_path: Path,
    session_id: str,
) -> ChatSession:
    """Load a saved session from an armory."""
    conversation, title = chat_storage.load(armory_path, session_id)
    source_file_count = _count_source_files(armory_path)
    session = ChatSession(
        config=config,
        conversation=conversation,
        session_id=session_id,
        title=title,
        armory_path=armory_path,
        source_file_count=source_file_count,
    )
    _log.info("session resumed", extra={"fields": {
        "session_id": session_id,
        "armory": str(armory_path),
        "message_count": len(conversation.messages),
    }})
    session.trace.record_session_event("resumed", title=title)
    return session


def session_has_messages(session: ChatSession) -> bool:
    """Return ``True`` when the session contains user or assistant messages."""
    return any(message.role != "system" for message in session.conversation.messages)


def _derive_title(conversation: Conversation) -> str:
    first_user_content = ""
    for message in conversation.messages:
        if message.role == "user":
            first_user_content = message.content
            break
    if not first_user_content:
        return ""
    prefix = first_user_content[:60]
    count = sum(
        1
        for msg in conversation.messages
        if msg.role == "user" and msg.content.startswith(first_user_content[:20])
    )
    if count > 1:
        return f"{prefix} ({count})"
    return prefix


def send_user_message(
    session: ChatSession,
    user_input: str,
    *,
    abort: threading.Event | None = None,
) -> str:
    """Append a user message, run the agent loop, stream output, return reply."""
    length_before = len(session.conversation.messages)
    session.conversation.add("user", user_input)
    session.trace.record_user_message(user_input)

    _log.info("user message", extra={"fields": {
        "session_id": session.session_id,
        "input_len": len(user_input),
        "message_count": len(session.conversation.messages),
    }})

    # RAG context injection: retrieve and stuff before the user message
    if session.armory_path is not None:
        _inject_rag_context(session, user_input)

    timer = Timer()
    try:
        if session.armory_path is not None:
            # Agent loop with tools — workspace is the armory
            parts: list[str] = []
            for chunk in agent_loop(
                session.config,
                session.conversation,
                session.armory_path,
                abort=abort,
            ):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                parts.append(chunk)
            sys.stdout.write("\n")
            sys.stdout.flush()
            reply = "".join(parts)
        else:
            # Fallback: plain streaming without tools
            reply = get_reply(session.config, session.conversation, abort=abort)
    except StreamRecoveryError as rec:
        # Partial content was streamed before the connection dropped.
        # Roll back the conversation to keep it consistent, but preserve
        # the partial reply in the exception for the caller to inspect.
        _log.warning("stream interrupted, rolling back", extra={"fields": {
            "session_id": session.session_id,
            "partial_len": len(rec.partial_content),
            "latency_ms": timer.ms,
        }})
        del session.conversation.messages[length_before:]
        session.dirty = True
        raise
    except Exception:
        _log.error("send_user_message failed", extra={"fields": {
            "session_id": session.session_id,
            "latency_ms": timer.ms,
        }}, exc_info=True)
        del session.conversation.messages[length_before:]
        raise

    # The agent_loop already adds the assistant message to conversation,
    # but for the plain get_reply path we need to add it here.
    if session.conversation.messages and session.conversation.messages[-1].role != "assistant":
        session.conversation.add("assistant", reply)

    if not session.title:
        session.title = _derive_title(session.conversation)
    session.dirty = True

    _log.info("reply complete", extra={"fields": {
        "session_id": session.session_id,
        "reply_len": len(reply),
        "latency_ms": timer.ms,
    }})
    session.trace.record_session_event("reply", latency_ms=round(timer.ms, 1), reply_len=len(reply))

    return reply


def _inject_rag_context(session: ChatSession, user_input: str) -> int:
    """Build/load the RAG index, retrieve relevant chunks, and inject context.

    Inserts a system message with retrieved context just before the last
    user message. Returns the number of messages inserted (0 or 1).
    """
    try:
        timer = Timer()
        if session._rag_index is None:
            session._rag_index = load_or_build(session.armory_path)  # type: ignore[arg-type]

        with timer:
            scored = retrieve(user_input, session._rag_index, top_k=5)
        if not scored:
            _log.info("rag retrieve: no results", extra={"fields": {
                "query_len": len(user_input),
                "latency_ms": timer.ms,
            }})
            return 0

        scores = [sc.score for sc in scored]
        _log.info("rag retrieve", extra={"fields": {
            "query_len": len(user_input),
            "retrieved": len(scored),
            "top_score": round(scores[0], 4) if scores else 0,
            "latency_ms": round(timer.ms, 1),
        }})
        session.trace.record_rag_retrieve(
            query=user_input,
            top_k=5,
            retrieved=len(scored),
            scores=scores,
            latency_ms=timer.ms,
        )

        context_text = build_context(scored, max_tokens=2000)
        if not context_text:
            return 0

        full_context = _RAG_CONTEXT_PREFIX + context_text

        # Insert just before the last message (which is the user message)
        last_idx = len(session.conversation.messages) - 1
        session.conversation.messages.insert(
            last_idx,
            Message(role="system", content=full_context),
        )
        return 1
    except Exception:
        # RAG failure should never block the conversation
        _log.warning("rag context injection failed", exc_info=True)
        return 0


def save_session(session: ChatSession) -> Path:
    """Persist the session to the active armory."""
    if session.armory_path is None:
        raise chat_storage.ChatStorageError(
            "cannot save chat without an active armory; use /armory first"
        )
    title = session.title or _derive_title(session.conversation)
    path = chat_storage.save(
        session.armory_path,
        session.session_id,
        session.conversation,
        title=title,
    )
    session.dirty = False
    _log.info("session saved", extra={"fields": {
        "session_id": session.session_id,
        "path": str(path),
        "message_count": len(session.conversation.messages),
    }})
    session.trace.record_session_event("saved", path=str(path))
    return path


def list_armory_sessions(armory_path: Path) -> list[dict[str, str]]:
    """Return saved sessions for the given armory."""
    return chat_storage.list_sessions(armory_path)
