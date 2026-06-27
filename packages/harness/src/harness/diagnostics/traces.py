"""Armory-scoped session trace writing."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from ai.logging import get_logger, redact_mapping

from harness.armory.state_files import append_armory_state_text
from harness.armory.storage import TRACES_DIR


class TraceWriter:
    def __init__(self, session_id: str, armory_path: Path | None = None) -> None:
        # Defense-in-depth: reject path traversal in session_id.
        if "/" in session_id or "\\" in session_id or ".." in session_id:
            raise ValueError(f"Invalid session_id: {session_id}")
        self.session_id = session_id
        self._armory_path = armory_path
        self._path: Path | None = None
        self._log = get_logger("trace")

    @property
    def path(self) -> Path | None:
        if self._path is None and self._armory_path is not None:
            self._path = self._armory_path / TRACES_DIR / f"{self.session_id}.jsonl"
        return self._path

    def _write(self, event: Mapping[str, object]) -> None:
        if self._armory_path is None:
            return
        line = json.dumps(redact_mapping(event), default=str, ensure_ascii=False)
        try:
            append_armory_state_text(
                self._armory_path,
                f"{TRACES_DIR}/{self.session_id}.jsonl",
                line + "\n",
            )
        except OSError as exc:
            self._log.warning("trace write failed", extra={"fields": {"error": str(exc)}})

    @staticmethod
    def _ts() -> str:
        return datetime.now(UTC).isoformat()

    def record_user_message(self, content: str) -> None:
        self._write({"type": "user_message", "ts": self._ts(), "content": content})

    def record_rag_retrieve(
        self,
        *,
        query: str,
        top_k: int,
        retrieved: int,
        scores: list[float],
        latency_ms: float,
        chunks: list[Mapping[str, object]] | None = None,
    ) -> None:
        event: dict[str, object] = {
            "type": "rag_retrieve",
            "ts": self._ts(),
            "query": query[:200],
            "top_k": top_k,
            "retrieved": retrieved,
            "scores": [round(score, 4) for score in scores],
            "latency_ms": round(latency_ms, 1),
        }
        if chunks is not None:
            event["chunks"] = chunks
        self._write(event)

    def record_material_operation(
        self,
        *,
        operation: str,
        message: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        event: dict[str, object] = {
            "type": "material_operation",
            "ts": self._ts(),
            "operation": operation,
            "message": message,
        }
        if metadata:
            event["metadata"] = dict(metadata)
        self._write(event)

    def record_session_event(self, event: str, **details: object) -> None:
        entry: dict[str, object] = {
            "type": "session",
            "ts": self._ts(),
            "event": event,
        }
        entry.update(details)
        self._write(entry)

    def close(self) -> None:
        pass
