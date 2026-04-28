# Features

Active contributors: Gil

Hephaistos is a local-first study CLI with an interactive Textual TUI. It combines RAG-based retrieval, LLM-powered chat, citation verification, structured study loops, spaced-repetition vocabulary drills, persistent memory, and automatic context compaction into a single agent workflow.

## Feature overview

| Feature | Summary | Details |
|---|---|---|
| [RAG retrieval](rag-retrieval.md) | Markdown-aware chunking, BM25/hybrid retrieval, cross-encoder re-ranking, and query transformation | Full pipeline from source files to scored chunks |
| [Citation verification](citation-verification.md) | Assigns stable evidence IDs to retrieved chunks and verifies model citations against them | Prevents fabricated or mismatched references |
| [Study loop](study-loop.md) | Deterministic state machine that drives present → recall → assess cycles | Recall-first philosophy with hints and source grounding |
| [Vocabulary drill](vocabulary-drill.md) | Anki-style spaced repetition over vocabulary tables embedded in armory Markdown files | SM-2 scheduling with interactive TUI drill sessions |
| [Memory system](memory-system.md) | Extracts and persists learned concepts per armory to avoid repeating material | Local JSON store with optional Supermemory cloud backend |
| [Context compaction](compact.md) | Three-layer compression keeps sessions running indefinitely within token budgets | Micro-compaction, LLM summarisation, and explicit `/compact` command |

## Architecture in brief

All features live under `hephaistos/`. The `app` package owns the CLI/TUI layer and is the only package allowed to import from others (enforced by `lint-imports`). The `harness` package holds the agent loop, RAG pipeline, citation logic, and compaction. Business-logic packages (`study`, `vocab`, `memory`, `providers`, `armory`, `parameters`) are independent leaves that `app` and `harness` coordinate.

See the individual feature pages for source-level details, key abstractions, and integration points.
