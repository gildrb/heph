# Agent Harness Roadmap

Heph should treat agent quality as an evaluated product surface, not as a
side effect of adding a framework. The target is a document workspace that can prove
retrieval accuracy, grounded answering, citation faithfulness, and study-loop
control across repeatable academic tasks.

## Current Position

The project already has useful primitives:

- `agent.dispatch` owns the model/tool loop, streaming events,
  compaction, tool execution, and per-turn evidence injection.
- `chat.orchestrator` owns turn planning, rollback, learning state,
  citation verification, memory extraction, and trace/usage recording.
- `rag` owns local chunking, indexing, hybrid retrieval, query
  transformation, re-ranking, and citable evidence rendering.
- `study` owns a deterministic study-loop state machine.

The weakness is that these pieces are not yet expressed as a benchmarked agent
runtime contract. The harness can work, but it cannot yet prove that a change
improves academic RAG quality instead of merely changing behavior.

## Native Harness Stance

Heph should win with its own harness instead of outsourcing the core
runtime to an agent framework. The important pieces are already local: armory
layout, document conversion, retrieval, evidence IDs, learning state, tool events,
privacy boundaries, and benchmark gates.

Frameworks are not part of the plan. New work should improve native source
classification, retrieval quality, visible harness events, answer contracts,
traceability, and deterministic regression tests.

## Target Runtime Contract

Each agent turn should become an explicit state transition:

1. Classify user intent and study phase.
2. Resolve required evidence or produce a grounded no-evidence response.
3. Build a bounded context package with citations and memory.
4. Run the model/tool loop with tool policy and interruption points.
5. Verify citations, learning-state transition, and answer shape.
6. Persist trace, usage, retrieval metadata, and evaluation hooks.

This contract should be implemented in the existing orchestrator and agent
event stream so users can see what the harness is doing without losing the
local-first product semantics.

## Benchmark Layers

Use several small gates instead of one vague "agent quality" score:

- Retrieval: hit rate, mean reciprocal rank, expected-source recall, latency.
- Material roles: lecture, slide deck, exercise sheet, past exam, and reference
  classification from path plus extracted text.
- Index integrity: extracted chunks preserve source text, Unicode, formula
  language, and exam formats while rejecting extraction placeholders and OCR
  garbage before retrieval runs.
- Grounding: every factual answer cites retrieved evidence, and every citation
  exists in the current turn.
- Faithfulness: answers do not introduce unsupported claims when evidence is
  missing or thin.
- Study control: recall, reveal refusal, hints, simplification, review, and
  assessment transitions match the deterministic learning state; completed recall
  attempts create review schedule items.
- Tooling: tool calls are valid JSON, respect workspace policy, and recover
  cleanly from errors.
- End-to-end academic tasks: labelled source QA, exact phrase lookup, exam
  priority analysis, active recall assessment, and multi-document synthesis.

The first concrete benchmark entry point is:

```bash
uv run python -m scripts.benchmark_rag path/to/armory path/to/cases.jsonl \
  --top-k 5 \
  --min-score 0.1 \
  --min-hit-rate 0.85 \
  --min-mrr 0.70 \
  --min-expected-recall 1.0
```

Material role fixtures can be checked with:

```bash
uv run python -m scripts.benchmark_material_roles path/to/armory \
  path/to/material-roles.jsonl \
  --min-pass-rate 1.0
```

Index integrity fixtures can be checked with:

```bash
uv run python -m scripts.benchmark_index_integrity path/to/armory \
  path/to/index-integrity.jsonl \
  --min-pass-rate 1.0 \
  --min-required-text 1.0 \
  --min-forbidden-text 1.0 \
  --min-corpus-forbidden-text 1.0
```

Before labelled cases exist for a new armory, run the generic corpus health
scan:

```bash
uv run python -m scripts.benchmark_index_integrity path/to/armory --scan-only \
  --min-corpus-forbidden-text 1.0
```

Grounded answer fixtures can be checked with:

```bash
uv run python -m scripts.benchmark_answers path/to/answers.jsonl \
  --min-pass-rate 0.90 \
  --min-citation-validity 1.0 \
  --min-citation-presence 0.95 \
  --min-expected-citations 1.0 \
  --min-required-text 1.0 \
  --min-forbidden-text 1.0 \
  --min-supported-claims 1.0
```

Learning-state fixtures can be checked with:

```bash
uv run python -m scripts.benchmark_study_state path/to/learning-state.jsonl \
  --armory path/to/armory \
  --min-pass-rate 1.0 \
  --min-transition-pass-rate 1.0 \
  --min-scheduling-pass-rate 1.0
```

To generate answer fixtures from the current harness/model:

```bash
uv run python -m scripts.replay_answer_benchmark path/to/armory \
  path/to/replay-prompts.jsonl \
  .artifacts/answers.current.jsonl \
  --model gpt-4.1
```

To audit the public non-interactive CLI stream:

```bash
heph chat ask --jsonl path/to/armory "what is the material about" \
  > .artifacts/chat-events.jsonl
uv run python -m scripts.benchmark_chat_events \
  .artifacts/chat-events.jsonl \
  --answer-expectation path/to/single-answer-contract.json
```

Real-corpus proof manifests should declare both the captured chat-event stream
and its single-answer expectation with dataset kinds `chat-events` and
`chat-event-answer-expectation`. This keeps the visible harness behavior under
the same audit umbrella as model replay prompts. When the stream contains
runtime execution notes such as failed, slow, oversized, or repeated tool calls,
`scripts.benchmark_chat_events` validates that those `tool_runtime` notices
carry reviewable tool, reason, latency, result-size, error, and repeat metadata.
For generic tool-enabled agent turns, the dispatch loop also emits an
`acceptance_criteria` notice and injects the same criteria into model context,
so the first verification/tool step has visible acceptance criteria instead of
only an implied tool requirement.

To run the same replay set across local and hosted model candidates:

```bash
uv run python -m scripts.run_model_eval_matrix \
  path/to/armory \
  path/to/replay-prompts.jsonl \
  path/to/model-matrix.json \
  .artifacts/model-eval \
  --json-report .artifacts/model-eval/matrix.report.json
```

Replay prompt datasets should carry the same answer-contract fields as saved
answer fixtures where possible: expected citations, required/forbidden text,
supported claims, and no-evidence abstention requirements. The deterministic
suite validates replay prompt shape even when CI cannot call a hosted model.

The deterministic CI gate is:

```bash
uv run python -m scripts.run_benchmark_suite
```

When a saved baseline report exists, run the suite as a regression gate:

```bash
uv run python -m scripts.run_benchmark_suite \
  --json-report .artifacts/benchmark-suite.current.json \
  --compare-to .artifacts/benchmark-suite.baseline.json
```

## Recommended Sequence

1. Build labelled local benchmark sets from real armories: material roles,
   exact lookup, concept QA, multi-document synthesis, and past-exam priority
   prompts.
2. Gate retrieval, material roles, index integrity, and saved-output quality in CI with
   `scripts.run_benchmark_suite`.
3. Expand retrieval quality gates with `scripts.benchmark_rag`.
4. Gate saved model outputs with `scripts.benchmark_answers` for citation
   validity, required answer content, forbidden unsupported claims, answer
   shape, and evidence coverage.
5. Replay fixed prompts against a configured model with
   `scripts.replay_answer_benchmark`, preserving supported-claim and
   abstention requirements, then score the generated fixtures with
   `scripts.benchmark_answers`.
6. Compare current deterministic and model-backed JSON reports against saved
   baselines before accepting an accuracy change.
7. Extract the current orchestrator into explicit native harness steps while
   keeping the public event stream stable.
8. Keep user-visible harness events clear and compact, and use
   `heph chat ask --jsonl` when a non-interactive audit needs structured
   reading, retrieval, writing, verification, and answer-completion events.
9. Expand real academic benchmark sets, especially PDF-heavy modules with
   lecture decks, past exams, German text, and LaTeX.

## Success Criteria

The harness is competitive only when changes are accepted by evidence:

- Retrieval gates pass on project benchmark datasets.
- Material-role gates correctly identify lectures, exercises, and past exams
  across labelled academic fixtures.
- End-to-end academic evals pass for at least one local/small model and one
  frontier hosted model.
- Citation verification has no known false-positive path for invented evidence
  IDs.
- Supported-claim gates catch answers that cite real evidence IDs for claims not
  present in the cited evidence.
- Replay datasets remain compatible with the grounded-answer contract before
  model-backed replay output is generated.
- No-evidence and low-confidence paths are tested and user-visible.
- Tool and retrieval traces are sufficient to reproduce a bad answer.
