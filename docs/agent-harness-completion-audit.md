# Agent Harness Completion Audit

This audit maps the user-facing objective to concrete artifacts and remaining
gaps. It is intentionally stricter than a normal changelog: the goal is not
"tests are green", but "Hephaistos can prove academic RAG quality across
subjects, document roles, and answer behaviors."

The machine-readable completion gate is:

```bash
uv run python -m scripts.audit_agent_harness_completion \
  --real-manifest path/to/real-corpus/manifest.json \
  --real-preflight-report .artifacts/real-corpus-preflight.json \
  --model-matrix-report .artifacts/model-eval/matrix.report.json \
  --json-report .artifacts/harness-completion-audit.json
```

Without external real-corpus manifest evidence, a matching passing preflight
report, and a passing model-backed local / frontier replay matrix, this command
intentionally exits non-zero.

First discover whether a local armory root has a broad enough candidate:

```bash
uv run python -m scripts.discover_real_corpus_candidates \
  ~/.armories \
  --min-documents 40 \
  --min-roles 3 \
  --require-candidate
```

This is a cheap readiness check. It reports visible material counts, inferred
roles, extensions, and next-step commands for the strongest passing candidate
without making any subject-specific assumption or claiming accuracy proof.
By default it also requires coarse role variety, so a large folder of only
generic notes is not suggested as broad academic proof.

For public corpora, keep the reviewed manifest as the reproducible provenance
artifact and materialize it into an armory when needed:

```bash
uv run python -m scripts.materialize_public_corpus \
  path/to/reviewed-public-manifest.json \
  path/to/real-armory
```

This downloads or copies each document with `source_url` into its declared
`materials/...` path, refuses path traversal, and refuses to overwrite existing
files unless `--overwrite` is supplied. Permissioned corpora can still use
`permission_note` provenance. Local permissioned folders can be copied into a
benchmark armory with:

```bash
uv run python -m scripts.build_permissioned_corpus_armory \
  path/to/real-armory \
  path/to/real-corpus-manifest.json \
  path/to/permissioned-materials \
  --limit 60 \
  --overwrite
```

This writes `file://` provenance, creates placeholder dataset files, and leaves
strict preflight/audit gates to reject narrow, unreviewed, or slow-to-extract
corpora.

Real-corpus candidates should first pass:

```bash
uv run python -m scripts.run_real_corpus_preflight \
  path/to/real-armory \
  path/to/real-corpus/manifest.json \
  --json-report .artifacts/real-corpus-preflight.json
```

That preflight combines strict manifest breadth validation, manifest-to-armory
source consistency, and the generic document-understanding smoke check. The
document-understanding report distinguishes visible material roles from indexed
material roles; required preflight roles must be backed by indexed content, not
only by filenames or unindexed files. It also reports overview source coverage
so a broad corpus summary cannot pass proof gates after sampling only a tiny
slice of the indexed corpus. Strict real-corpus validation also requires every
manifest document to include provenance, either a `source_url` for public
materials or a `permission_note` for permissioned materials.

The scaffold-plus-preflight path can be produced in one command:

```bash
uv run python -m scripts.prepare_real_corpus_evidence \
  path/to/real-armory \
  .artifacts/real-corpus-evidence
```

This writes `.artifacts/real-corpus-evidence/real-corpus-manifest.json` and
`.artifacts/real-corpus-evidence/real-corpus-preflight.json`, keeps strict
failures visible, and prints the next audit command. The generated manifest is
only a review scaffold at first: strict real-corpus gates reject unresolved
`known_limits` such as generated-scaffold, provenance-review, human-review, or
missing-model-proof markers. It becomes proof evidence only after the manifest
has been reviewed, labelled broadly enough, document provenance has been filled
in, those unresolved markers have been removed, and the
preflight report status is `0`; small or narrow corpora should fail.

The real-corpus proof also needs a captured public harness stream. After
reviewing the generated manifest and expectation file, capture and verify the
chat JSONL events:

```bash
uv run heph chat ask --jsonl path/to/real-armory "what is the material about" \
  > .artifacts/real-corpus-evidence/chat_events.jsonl
uv run python -m scripts.extract_chat_event_expectation \
  .artifacts/real-corpus-evidence/chat_events.jsonl \
  --output .artifacts/real-corpus-evidence/chat_event_expectation.json
uv run python -m scripts.benchmark_chat_events \
  .artifacts/real-corpus-evidence/chat_events.jsonl \
  --answer-expectation .artifacts/real-corpus-evidence/chat_event_expectation.json
```

This must show reading, evidence, writing, completion, a passing answer
contract, and consistent streamed assistant text versus `turn_complete.full_text`.
The generated `chat_event_expectation.json` is only a scaffold; fill in the
reviewed evidence items and expected citations from the captured turn before it
can count as real proof. Each expected citation must match a reviewed evidence
object with a non-empty `id`, `source`, and `text`, and the expectation must
cover at least two distinct evidence sources. The extractor command writes
`known_limits` on purpose; remove them only after reviewing the evidence text
and expected citations against the source material. `scripts.benchmark_chat_events`
rejects expectations that still contain `known_limits`, so this verification
step should fail until the scaffold has actually been reviewed.

Before spending model calls on the local/frontier replay matrix, validate the
candidate groups, armory path, and replay dataset breadth. For completion
evidence, `path/to/replay.jsonl` must be one of the real manifest datasets with
`kind: "model-replay-prompts"`. The same real manifest must also declare a
captured `chat-events` dataset and a `chat-event-answer-expectation` dataset,
so completion proof covers the visible public harness stream as well as saved
model replay answers:

```bash
uv run python -m scripts.run_model_eval_matrix \
  path/to/real-armory \
  path/to/replay.jsonl \
  path/to/model-matrix.json \
  .artifacts/model-eval \
  --validate-inputs \
  --json-report .artifacts/model-eval/matrix.inputs.json
```

The actual proof artifact still comes from the model-backed run without
`--validate-inputs`, saved as `.artifacts/model-eval/matrix.report.json`. The
completion audit requires this matrix to use the same armory as the real-corpus
preflight and a replay dataset declared by the real-corpus manifest.

## Objective

Build a native Hephaistos function-tool harness that can be benchmarked and can
reliably compete in academic RAG, document understanding, and answer accuracy
without adopting LangGraph, LlamaIndex, or LangChain as core runtime frameworks.

## Success Criteria

| Requirement | Evidence | Status |
| --- | --- | --- |
| Do not introduce LangGraph, LlamaIndex, or LangChain as dependencies. | `tests/test_native_harness_policy.py` rejects those packages in `pyproject.toml` and `uv.lock`. | Covered |
| Do not leak fixture-specific courses into runtime harness logic. | `tests/test_native_harness_policy.py` scans `hephaistos/` runtime code for MfI/Jesse/Ratzkin and other fixture-only course tokens, and `scripts.audit_agent_harness_completion` also scans non-fixture harness scripts while benchmark fixtures remain free to use realistic examples. | Covered |
| Benchmark retrieval quality. | `scripts/benchmark_rag.py`, `benchmarks/academic/rag.jsonl`, and `scripts/run_benchmark_suite.py` score hit rate, MRR, expected-source recall, whether plausible wrong evidence outranks expected evidence, and at least one multi-source synthesis case. | Covered for deterministic fixtures |
| Completion audit must verify the deterministic suite, not only file presence. | `scripts.audit_agent_harness_completion` runs `scripts.run_benchmark_suite` and requires status `0` before marking deterministic proof artifacts covered. | Covered |
| Benchmark grounded answer quality. | `scripts/benchmark_answers.py` checks citation validity, citation presence, required text, forbidden text, expected citations, abstention, supported claims, answer-shape constraints including overview bullet structure and cited bullet lines, evidence coverage such as minimum sampled sources, active-recall labels, hint-without-reveal behavior, and at least one multi-evidence synthesis answer. | Covered for saved fixtures |
| Benchmark real harness/model answers. | `scripts/replay_answer_benchmark.py` generates answer fixtures from the chat harness; `scripts.benchmark_chat_events` verifies `heph chat ask --jsonl` streams expose reading/evidence/writing/completion and can score the final answer with `scripts.benchmark_answers`; `scripts.extract_chat_event_expectation` turns evidence-notice metadata from a captured JSONL stream into a review scaffold; `scripts/run_replay_answer_eval.py` scores one model run; `scripts/run_model_eval_matrix.py` runs the same replay set across required candidate groups such as `local` and `frontier`. | Implemented, but not yet run broadly with saved local/frontier results |
| Completion audit must verify the public chat-event fixture, not only its script. | `scripts.audit_agent_harness_completion` checks that the default benchmark manifest declares `chat-events` and `chat-event-answer-expectation`, then runs `scripts.benchmark_chat_events` against the committed fixture. The verifier requires reading/evidence/writing/completion stages, answer scoring, consistent streamed assistant text versus `turn_complete.full_text`, and evidence-notice metadata that exposes refs, coverage, text excerpts, and expected evidence IDs. | Covered |
| Compare benchmark runs against baselines. | `scripts/compare_benchmark_reports.py`, `--json-report`, `--compare-to`, and `--compare-tolerance` are wired into deterministic and replay eval runners. | Covered |
| CI must expose benchmark metrics. | `.github/workflows/ci.yml` runs `scripts.run_benchmark_suite`, writes `.artifacts/benchmark-suite.json`, uploads it, and writes a summary table including retrieval, extraction, overview source coverage, chat-event stages, evidence metadata, answer quality, and study-state metrics. | Covered |
| Material-role inference must avoid one-module hardcoding. | `benchmarks/academic/material_roles.jsonl` spans biochemistry, general, history, mathematics, and physics; `scripts/run_benchmark_suite.py` rejects narrow domain/role coverage. | Covered for deterministic fixtures |
| Extraction and chunking must preserve source text before retrieval. | `scripts/benchmark_index_integrity.py`, `benchmarks/academic/index_integrity.jsonl`, and `scripts/run_benchmark_suite.py` check required text, forbidden extraction noise, Unicode, formula language, exam format preservation, and whole-corpus generic extraction poison. | Covered for deterministic fixtures |
| Priority scanning must reject boilerplate and OCR noise. | `scripts/benchmark_priority.py` checks expected topics, forbidden topics, and past-exam source recall across multiple domains. | Covered for deterministic fixtures |
| Study-state transitions and review scheduling must be benchmarked. | `scripts/benchmark_study_state.py` drives deterministic active-recall scenarios through `plan_turn`, `apply_turn_result`, and `StudyScheduleStore`; `benchmarks/academic/study_state.jsonl` covers multiple domains and one scheduling case; the suite rejects missing scheduling coverage. | Covered for deterministic fixtures |
| German text and LaTeX extraction should not collapse retrieval. | `hephaistos/rag/chunker.py` normalizes extracted text and repairs common umlaut/OCR patterns; `scripts/benchmark_index_integrity.py` gates indexed source text before retrieval; synthetic German/LaTeX fixtures cover regression cases. | Covered for deterministic fixtures; real scanned PDFs still need broader corpus proof |
| User-visible harness events should show reading, retrieval, and writing. | `hephaistos/rag/index.py` reports index `reading`, `indexed`, `skipped`, and `writing` progress; `hephaistos/chat/orchestrator.py` emits turn-stream `reading`, `evidence`, `writing`, and `verification` notices; evidence notices carry reviewable refs, source coverage, and excerpt metadata; `heph chat ask --jsonl` exposes those events as JSON Lines for non-interactive harness audits; `tests/test_chat_orchestrator.py` and `tests/test_cli_integration.py` verify material-backed turns expose these notices while calibration evidence stays hidden. | Covered for CLI/chat stream surfaces |
| Tool and retrieval traces must reproduce bad answers. | Session traces and JSON benchmark reports exist; retrieval trace events include refs, scores, and chunk excerpts; reply trace events include answer excerpts, evidence refs, evidence item excerpts, evidence coverage, and verification notices; `scripts.trace_to_answer_benchmark` converts live traces into answer fixtures, preserves evidence coverage, and can score them with benchmark assertions such as `min_sampled_sources`. | Covered for citation/grounding trace replay |
| Broad academic accuracy must be proven across arbitrary subjects and files. | Current committed fixtures span several subjects and answer shapes; `benchmarks/academic/manifest.json` and `scripts.validate_benchmark_manifest` make domain, role, document-type, and stressor coverage explicit. The validator now supports stricter external-corpus gates for required corpus kind, minimum documents, required document types, required stressors, required document provenance, and forbidden unresolved known limits. `scripts.create_benchmark_manifest` can scaffold a manifest from any armory so real corpora can be labelled and gated without committing private files, `scripts.materialize_public_corpus` can rebuild public-corpus armories from reviewed `source_url` provenance, and `scripts.build_permissioned_corpus_armory` can copy local permissioned document pools into an armory with `file://` provenance plus placeholder datasets. Generated-scaffold/provenance-review/human-review/no-model-proof `known_limits` are rejected by strict preflight and completion audit gates. | Not complete: no larger public/permissioned corpus has passed strict preflight and model eval yet |
| Unlabelled real armories need a generic preflight before labels exist. | `scripts.benchmark_document_understanding` checks indexed document coverage, extraction health, inferred visible-role and indexed-role distributions, required broad indexed roles, low role confidence, and overview source coverage for any armory without course-specific names. | Covered as a smoke/preflight gate; does not replace labelled real-corpus evals |
| Real corpus proof should be runnable as one artifact-producing command. | `scripts.prepare_real_corpus_evidence` creates a benchmark-suite-shaped evidence directory with a manifest, dataset placeholders, an armory link/copy, and a strict preflight JSON report; `scripts.build_permissioned_corpus_armory` creates the same suite shape from local permissioned folders; `scripts.run_real_corpus_preflight` remains the direct preflight runner and supports a document-understanding timeout so slow PDF conversion is reported as a failure instead of hanging. Fresh scaffold manifests intentionally fail strict proof gates until a human-reviewed manifest removes unresolved scaffold known-limits. | Covered for preflight evidence preparation; reviewed labels/model evals still required |
| End-to-end academic evals should pass for at least one local/small model and one frontier hosted model. | `scripts/run_model_eval_matrix.py` enforces required model groups and writes per-candidate plus combined reports. The runner rejects duplicate replay case IDs and narrow replay domain/task coverage before model calls, carries each candidate's scored case count, domains, tasks, grounded-answer metrics, answer-shape metrics, and evidence-coverage metrics into the combined matrix report, and fails candidates whose reports omit required coverage fields, narrow domain/task coverage below configured minima, mismatch the replay dataset's exact case/domain/task coverage, or fall below required grounded-answer metrics. `benchmarks/model-matrix.example.json` provides a standard local/frontier template, and `--validate-only` checks matrix shape without model calls. | Not complete: no committed broad model-backed evaluation result proves this |
| Completion cannot be declared from partial proxy evidence. | `scripts.audit_agent_harness_completion` checks native harness artifacts, forbidden framework policy, real-corpus manifest evidence, required real manifest dataset kinds (`chat-events`, `chat-event-answer-expectation`, and `model-replay-prompts`), real-corpus chat-event verification with reading/evidence/writing/completion and stream-consistency checks, reviewed chat expectation evidence with matching expected citations and at least two distinct sources, matching real-corpus preflight evidence with existing armory and manifest paths, extraction health, indexed coverage, complete visible-role coverage, indexed-role coverage, required indexed roles, and overview source coverage, plus model-backed local/frontier eval evidence with existing armory, replay dataset, and output directory paths. The model matrix must use the same armory as the real preflight and a replay dataset declared by the real manifest as `model-replay-prompts`; child report and answer fixture containment inside that output directory, replay dataset answer-contract/domain/task breadth, per-candidate answer metrics including `evidence_coverage_rate`, matching matrix/child/fixture domain and task coverage, matching matrix/child replay case counts, matching child replay reports, corpus/dataset/model metadata consistency, answer fixture path consistency, preserved answer fixtures, rescored answer-fixture metrics, full replay case count and case-id coverage, and preserved scoring thresholds are all checked. | Covered as an audit gate; currently expected to fail until external proof is provided |

## Prompt-To-Artifact Checklist

| Prompt requirement | Concrete artifact | Verification command |
| --- | --- | --- |
| "Remove these frameworks from the plan." | `docs/agent-harness-roadmap.md` Native Harness Stance and `tests/test_native_harness_policy.py`. | `uv run pytest tests/test_native_harness_policy.py` |
| "Benchmarks are needed for it to be provably accurate." | `benchmarks/academic/*`, benchmark scripts, CI benchmark job. | `uv run python -m scripts.run_benchmark_suite` |
| "Make it an actual harness." | Replay runner, answer gates, report comparator, visible event labels. | `uv run python -m scripts.run_replay_answer_eval ...` with a configured model |
| "Show when it's reading, when it's writing." | RAG index progress callback, chat turn notices, `heph chat ask --jsonl`, and tool execution display labels. | CLI/TUI interaction tests plus manual `heph index` smoke test |
| "Identify lecture PDFs vs past exam by itself." | `infer_material_role_from_text` and material-role benchmark fixtures. | `uv run python -m scripts.benchmark_material_roles path/to/armory path/to/material_roles.jsonl` |
| "Arbitrary files from another uni should not break it." | Generic unlabelled armory smoke benchmark checks extraction health and role distribution without course-specific assumptions. | `uv run python -m scripts.benchmark_document_understanding path/to/armory --require-role slides --require-role past_exam` |
| "German letters and LaTeX cannot poison the index." | Chunk normalization plus index-integrity fixtures and suite gates. | `uv run python -m scripts.benchmark_index_integrity path/to/armory path/to/index_integrity.jsonl` |
| "Do not hardcode MfI-2, Jesse Ratzkin, German, or BioChem." | Multi-domain suite integrity checks reject narrow fixture sets; heuristics are role/content based, runtime-code policy tests reject fixture-specific course tokens in `hephaistos/`, and the completion audit rejects the same tokens in non-fixture harness scripts. | `uv run pytest tests/test_native_harness_policy.py && uv run python -m scripts.run_benchmark_suite` |
| "Every subject, every lecture, every exercise, every past exam." | Generalized material-role and priority APIs plus benchmark manifest breadth gates. | Not fully provable yet; requires larger public/permissioned eval corpus |
| "Bad vague output cannot happen." | Grounded answer gates catch missing citations, unsupported claims, failure to abstain, missing active-recall labels, evidence under-sampling, and answer-shape failures such as too-short overview answers, too few citations, too few distinct cited evidence sources, too few bullet lines, or too few cited bullet lines for readable overview output. | `uv run python -m scripts.benchmark_answers path/to/answers.jsonl` |
| "Objectively competitive, benchmarked, and accuracy-proven." | Machine-readable completion audit requires deterministic harness artifacts plus external real-corpus manifest, real-corpus preflight, and model-backed replay evidence. | `uv run python -m scripts.audit_agent_harness_completion --real-manifest ... --real-preflight-report ... --model-matrix-report ...` |

## Current Verified Commands

The current working tree has been checked with:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run lint-imports
uv run vulture hephaistos tests vulture-whitelist.py
uv run pylint --persistent=no --score=no --disable=all --enable=duplicate-code hephaistos
uv run pytest
uv run python -m scripts.check_repo_policies
uv run python -m scripts.sync_docs --check
uv run python -m scripts.run_benchmark_suite --min-evidence-coverage 1.0
uv run python -m scripts.discover_real_corpus_candidates ~/.armories --min-documents 40 --min-roles 3 --require-candidate
uv run python -m scripts.audit_agent_harness_completion
```

The deterministic suite can also compare against a saved baseline when one is
available:

```bash
uv run python -m scripts.run_benchmark_suite \
  --json-report .artifacts/benchmark-suite.current.json \
  --compare-to .artifacts/benchmark-suite.baseline.json
```

Completion should only be declared with real saved proof artifacts:

```bash
uv run python -m scripts.audit_agent_harness_completion \
  --real-manifest path/to/real-corpus/manifest.json \
  --real-preflight-report .artifacts/real-corpus-preflight.json \
  --model-matrix-report .artifacts/model-eval/matrix.report.json
```

Temporary smoke reports should not be committed.

## Remaining Work

The objective is not complete until these gaps are closed:

1. Add a larger non-private academic eval corpus and validate it with strict
   manifest gates. `scripts.prepare_real_corpus_evidence` can create the
   initial manifest scaffold plus preflight report from an external armory, and
   `scripts.create_benchmark_manifest` can still be used directly for manual
   manifest work. Before the manifest can count as proof, review domains, roles,
   document types, and stressors, then remove unresolved generated-scaffold /
   human-review / no-model-proof `known_limits`. The corpus should include more document types:
   scanned PDFs, slide decks, exercise sheets, solutions, past exams, formulas,
   tables, multi-column layouts, multilingual text, and OCR noise.
2. Run `scripts.benchmark_document_understanding` against candidate real
   armories before labelling them so extraction, overview source coverage, and
   broad role inference failures are caught immediately.
3. Run and save broad model-backed replay evals for at least one small/local
   model and one frontier hosted model using `scripts.run_model_eval_matrix`.
   The reviewed real-corpus manifest must declare the replay prompt dataset and
   the captured chat-event stream plus its answer expectation.
4. Expand TUI/browser-level harness event tests beyond the stream-level checks
   if UI rendering changes.
5. Build and run larger public or permissioned academic corpora with real PDFs,
   scans, formulas, tables, multilingual text, and past exams.
