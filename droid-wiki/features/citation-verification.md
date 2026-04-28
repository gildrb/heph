# Citation verification

Hephaistos uses a structured citation system to ensure the LLM grounds its answers in retrieved evidence rather than fabricating references. Every retrieved chunk is assigned a stable evidence ID, the model is instructed to cite those IDs, and a post-generation verification step audits the response.

## Purpose

Prevent hallucinated citations and make grounding auditable. The verification operates on the exact `TurnEvidence` objects produced by the RAG pipeline — not on filenames scraped from the prompt.

## Directory layout

```
hephaistos/harness/
├── citation.py           # extraction, verification, warning formatting
└── rag/
    └── context.py        # TurnEvidence, evidence ID assignment
```

## Key abstractions

| Abstraction | Source file | Purpose |
|---|---|---|
| `TurnEvidence` | `hephaistos/harness/rag/context.py` | Frozen tuple of `EvidenceChunk` items with stable IDs (`E1`, `E2`, …) |
| `EvidenceChunk` | `hephaistos/harness/rag/context.py` | A chunk promoted into a citable block: `evidence_id`, `Chunk`, `score`, `content` |
| `ExtractedCitation` | `hephaistos/harness/citation.py` | An evidence citation found in response text (e.g. `E1`) |
| `VerificationResult` | `hephaistos/harness/citation.py` | Outcome: verified IDs, unverified IDs, counts, `all_verified` flag |
| `build_turn_evidence()` | `hephaistos/harness/rag/context.py` | Converts `ScoredChunk` list → `TurnEvidence` with token budget |
| `verify_response()` | `hephaistos/harness/citation.py` | Full pipeline: extract citations → verify → format notice |

## How it works

### Evidence ID assignment

When the orchestrator calls `build_turn_evidence()` (in `hephaistos/harness/rag/context.py`), each scored chunk from retrieval is assigned a sequential ID: `E1`, `E2`, `E3`, etc. The evidence is rendered into a prompt block that includes:

```
[E1] networking_notes.md (chunk 0, relevance: 0.87)
TCP uses a 3-way handshake: SYN, SYN-ACK, ACK...
```

The rendered prompt explicitly instructs the model: *"Cite evidence IDs in brackets after factual claims, for example [E1] or [E1][E2]. Do not cite filenames by themselves."*

### Citation extraction

`extract_citations()` in `hephaistos/harness/citation.py` scans response text with a strict regex that matches:
- Single citations: `[E1]`
- Grouped citations: `[E1, E2]` or `[E1; E2]`

Raw filenames are intentionally **not** treated as valid citations — only bracketed evidence IDs count.

### Verification step

`verify_citations()` compares every extracted citation ID against the `TurnEvidence` items for that turn:

- **Verified**: The ID exists in the turn evidence (e.g. `E1` matches `TurnEvidence.get("E1")`).
- **Unverified**: The ID was not found in the turn evidence (potential fabrication).

The function returns a `VerificationResult` with `verified`, `unverified`, `has_citations`, and `all_verified` fields.

### Warning behavior

`format_verification_notice()` produces a human-readable notice:

| Condition | Warning |
|---|---|
| Unverified citations | *"Warning: Unverified evidence citation(s): E5. These IDs were not found in the retrieved evidence."* |
| No citations in a long response (>200 chars) with evidence present | *"⚠ No evidence citations found in this answer — verify claims against your materials."* |
| All citations verified | No warning (empty string) |

Short conversational responses (under 200 characters) are exempted from the "no citations" warning since they are typically greetings or acknowledgements.

### Integration with the orchestrator

In `hephaistos/chat/orchestrator.py`, the citation verification flow is:

1. **Before the LLM call**: `TurnEvidence` is built from retrieved chunks and injected into the system prompt via `_inject_turn_context()`.
2. **After the LLM call**: `_finalize_successful_turn()` calls `verify_response(self.last_reply, resolved.turn_evidence)`.
3. **Result**: The verification notice is either displayed to the user or logged silently.

The orchestrator also tracks `session.last_turn_evidence` so evidence references persist across the turn lifecycle.

## Integration points

- **RAG pipeline**: `TurnEvidence` is produced by `build_turn_evidence()` in [RAG retrieval](rag-retrieval.md).
- **Study loop**: Assessment replies are citation-verified when the study controller uses source-grounded context. See [study loop](study-loop.md).
- **Memory extraction**: Evidence refs are passed to `extract_and_store()` as source context. See [memory system](memory-system.md).

## Key source files

| File | Responsibility |
|---|---|
| `hephaistos/harness/citation.py` | Citation extraction, verification, warning formatting |
| `hephaistos/harness/rag/context.py` | `TurnEvidence`, `EvidenceChunk`, evidence ID assignment |
| `hephaistos/chat/orchestrator.py` | Integration point — calls `verify_response()` after each turn |

## Entry points for modification

- Change citation format: update `_EVIDENCE_CITATION_RE` and `_EVIDENCE_ID_RE` in `hephaistos/harness/citation.py`.
- Change evidence prompt instructions: update `_EVIDENCE_PROMPT_PREFIX` in `hephaistos/harness/rag/context.py`.
- Adjust the "no citation" threshold: change `_NO_CITATION_CHAR_THRESHOLD` in `hephaistos/harness/citation.py`.
