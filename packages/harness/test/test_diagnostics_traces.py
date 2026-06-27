"""Tests for armory-scoped trace writing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from harness.diagnostics.traces import TraceWriter


@pytest.fixture
def trace_dir(tmp_path: Path) -> Path:
    armory = tmp_path / "armory"
    armory.mkdir()
    (armory / ".harness").mkdir()
    return armory


class TestTraceWriter:
    def test_no_armory_no_file(self) -> None:
        writer = TraceWriter("sess1", armory_path=None)

        assert writer.path is None
        writer.record_user_message("hello")

    def test_creates_trace_file(self, trace_dir: Path) -> None:
        writer = TraceWriter("sess1", armory_path=trace_dir)
        writer.record_user_message("hello world")
        writer.close()

        trace_path = trace_dir / ".harness" / "traces" / "sess1.jsonl"
        assert trace_path.exists()
        lines = trace_path.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["type"] == "user_message"
        assert data["content"] == "hello world"
        assert "ts" in data

    def test_record_rag_retrieve(self, trace_dir: Path) -> None:
        writer = TraceWriter("sess6", armory_path=trace_dir)
        writer.record_rag_retrieve(
            query="what is async await?",
            top_k=5,
            retrieved=3,
            scores=[0.95, 0.82, 0.71],
            latency_ms=120.3,
            chunks=[
                {
                    "ref": "materials/notes.md#chunk=0",
                    "score": 0.95,
                    "text_excerpt": "async await suspends work without blocking the thread",
                }
            ],
        )
        writer.close()

        data = json.loads((trace_dir / ".harness" / "traces" / "sess6.jsonl").read_text().strip())
        assert data["type"] == "rag_retrieve"
        assert data["retrieved"] == 3
        assert data["scores"] == [0.95, 0.82, 0.71]
        assert data["chunks"][0]["ref"] == "materials/notes.md#chunk=0"
        assert "async await" in data["chunks"][0]["text_excerpt"]

    def test_record_rag_retrieve_redacts_nested_chunk_secrets(self, trace_dir: Path) -> None:
        writer = TraceWriter("sess6-secret", armory_path=trace_dir)
        writer.record_rag_retrieve(
            query="secret",
            top_k=1,
            retrieved=1,
            scores=[1.0],
            latency_ms=1.0,
            chunks=[
                {
                    "ref": "materials/secrets.md#chunk=0",
                    "text_excerpt": "AWS key AKIAIOSFODNN7EXAMPLE should not persist",
                }
            ],
        )
        writer.close()

        raw = (trace_dir / ".harness" / "traces" / "sess6-secret.jsonl").read_text()
        assert "AKIAIOSFODNN7EXAMPLE" not in raw
        assert "***REDACTED***" in raw

    def test_record_session_event(self, trace_dir: Path) -> None:
        writer = TraceWriter("sess7", armory_path=trace_dir)
        writer.record_session_event("created", model="glm-5")
        writer.record_session_event("saved", path="/tmp/save.json")
        writer.close()

        lines = (trace_dir / ".harness" / "traces" / "sess7.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["event"] == "created"
        assert json.loads(lines[1])["event"] == "saved"

    def test_append_mode(self, trace_dir: Path) -> None:
        writer = TraceWriter("sess8", armory_path=trace_dir)
        writer.record_user_message("first")
        writer.close()

        next_writer = TraceWriter("sess8", armory_path=trace_dir)
        next_writer.record_user_message("second")
        next_writer.close()

        lines = (trace_dir / ".harness" / "traces" / "sess8.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["content"] == "first"
        assert json.loads(lines[1])["content"] == "second"

    def test_close_idempotent(self, trace_dir: Path) -> None:
        writer = TraceWriter("sess9", armory_path=trace_dir)
        writer.record_user_message("hello")
        writer.close()
        writer.close()

    def test_trace_write_rejects_symlinked_trace_file(self, trace_dir: Path) -> None:
        outside = trace_dir.parent / "outside.jsonl"
        outside.write_text("unchanged", encoding="utf-8")
        trace_path = trace_dir / ".harness" / "traces" / "sess-link.jsonl"
        trace_path.parent.mkdir(parents=True)
        trace_path.symlink_to(outside)

        writer = TraceWriter("sess-link", armory_path=trace_dir)
        writer.record_user_message("hello")

        assert outside.read_text(encoding="utf-8") == "unchanged"
