# Hephaistos Benchmarks

This directory holds benchmark scripts, schemas, and tiny example shapes for
measuring whether the agent harness is improving academic RAG quality. Real
benchmark suites, corpora, qrels, snapshots, and generated reports are private
local artifacts: keep them in ignored paths such as `benchmarks/academic/`,
`benchmarks/public-academic/`, or `.artifacts/benchmarks/...`.

Run a local deterministic suite after provisioning the ignored suite directory:

```bash
uv run python -m scripts.run_benchmark_suite \
  --json-report .artifacts/benchmark-suite.json \
  --min-evidence-coverage 1.0
```

The suite copies `benchmarks/academic/armory` into a temporary directory before
building a RAG index, then scores retrieval, material-role inference, priority,
document-understanding preflight, index integrity, academic-item extraction,
study-state, scheduling, and grounded-answer datasets from the ignored local
suite. It also validates the model replay prompt dataset so
replay cases cannot silently drift away from the answer benchmark contract.
Answer quality gates include citation validity, answer shape, and evidence
coverage; `--min-evidence-coverage` fails the suite when answer fixtures
under-sample required source coverage.

The suite also prints and writes a `study_intent` contract report. This guards
the English-first intent-normalizer surface: the schema must keep the full set
of control labels, the prompt must say it interprets requests in whatever
language into an English-first control signal, the runtime parser must accept
those labels, and the contract must not grow language-specific examples that
would turn multilingual routing into a phrase list. The same report scans the
main study/chat prompt source files so language-specific examples do not creep
back into adjacent routing or fallback prompts.

The suite also validates `benchmarks/academic/manifest.json`, which declares
the domains, material roles, document types, stressors, datasets, and known
limits covered by the corpus. This keeps breadth visible and machine-checkable:

```bash
uv run python -m scripts.validate_benchmark_manifest \
  benchmarks/academic/manifest.json
```

For a larger public or permissioned corpus, use stricter gates that prove the
manifest is no longer just a synthetic smoke set:

```bash
uv run python -m scripts.validate_benchmark_manifest \
  path/to/real-corpus/manifest.json \
  --require-corpus-kind public-pdfs \
  --min-documents 40 \
  --min-domains 5 \
  --min-roles 4 \
  --min-document-types 8 \
  --min-stressors 16 \
  --require-document-type pdf \
  --require-document-type scanned-pdf \
  --require-document-type exercise-sheet \
  --require-document-type past-exam \
  --require-stressor real-pdf \
  --require-stressor ocr-noise \
  --require-stressor table-heavy \
  --require-stressor multi-column \
  --require-stressor multilingual \
  --forbid-known-limit "Synthetic snippets" \
  --forbid-known-limit "No real scanned PDFs" \
  --forbid-known-limit "No table-heavy"
```

To create a first manifest scaffold from an existing armory:

```bash
uv run python -m scripts.create_benchmark_manifest \
  path/to/armory \
  path/to/corpus/manifest.json \
  --corpus-kind permissioned-materials \
  --domain unlabelled \
  --infer-roles-from-index
```

The generator infers visible material paths, coarse roles, document types, and
file-shape stressors from the armory. With `--infer-roles-from-index`, it also
uses indexed document text to infer roles such as slides, assignments, and past
exams when filenames are generic. Treat the output as a review scaffold: replace
`unlabelled` domains, correct any roles, add real corpus-specific stressors, and
remove unresolved scaffold `known_limits` only after review. Strict real-corpus
preflight and completion audit gates reject generated-scaffold, human-review,
and no-model-proof `known_limits` so a large unreviewed scaffold cannot be
mistaken for completed evidence.

To discover whether a local armory root already contains a broad enough
candidate for real-corpus proof, run:

```bash
uv run python -m scripts.discover_real_corpus_candidates \
  ~/.armories \
  --min-documents 40 \
  --require-candidate
```

This command only reports corpus-readiness signals such as visible material
count, inferred roles, and file extensions. It does not label the corpus and it
does not replace the strict preflight or model-backed evals.

To create the manifest scaffold and strict preflight report in one repeatable
step, use the evidence-preparation wrapper. It writes a benchmark-suite-shaped
directory containing a manifest, dataset placeholders, an `armory` link, and a
preflight JSON report:

```bash
uv run python -m scripts.prepare_real_corpus_evidence \
  path/to/real-armory \
  .artifacts/real-corpus-evidence
```

If the corpus is too small, narrow, synthetic, missing required stressors, or
fails extraction/role checks, this command exits non-zero and prints the exact
failures. Fresh scaffold manifests are also expected to fail until their
domains, roles, document types, stressors, and unresolved `known_limits` have
been reviewed. Strict real-corpus gates also require every document to include
provenance, either `source_url` for public materials or `permission_note` for
permissioned materials. A passing reviewed report is suitable for the
`--real-manifest` and `--real-preflight-report` inputs to
`scripts.audit_agent_harness_completion`; it still does not replace the
model-backed local/frontier replay matrix.

For public corpora with public HTTPS `source_url` provenance, rebuild the armory
from the reviewed manifest instead of committing documents:

```bash
uv run python -m scripts.materialize_public_corpus \
  path/to/reviewed-public-manifest.json \
  path/to/real-armory
```

This writes only under the declared `materials/...` paths, refuses local or
private-network URLs, and refuses to overwrite existing files unless
`--overwrite` is supplied.

For permissioned local folders, copy the documents into a benchmark armory and
write `file://` provenance in one step:

```bash
uv run python -m scripts.build_permissioned_corpus_armory \
  path/to/real-armory \
  path/to/real-corpus-manifest.json \
  path/to/permissioned-materials \
  --domain-from-parent \
  --balance-domains \
  --infer-roles-from-index \
  --overwrite
```

The generated manifest is still a scaffold until a human reviews domains,
stressors, roles, document types, and unresolved `known_limits`; after that
review, rerun with `--reviewed` to omit scaffold known limits. The
`--domain-from-parent` flag preserves coarse folder-based domains when copying
multiple course folders, `--balance-domains` keeps any optional `--limit` from
taking every document from the first large folder, and `--infer-roles-from-index`
uses copied document text to improve role labels when filenames are generic.

After capturing `heph chat ask --jsonl`, use
`scripts.extract_chat_event_expectation` to draft the chat-event expectation
from evidence-notice metadata. The extractor writes `known_limits` deliberately;
`scripts.benchmark_chat_events` rejects the expectation until those limits are
removed after review.

For overview prompts, add `required_material_operations: ["sample_overview"]`
and `forbidden_material_operations: ["search_index"]` to the expectation. That
guards broad corpus-orientation requests against regressing into narrow query
retrieval while still using the normal answer-shape and citation checks.

Before labelled cases exist for a real armory, run a generic document
understanding smoke check. This checks extraction health, indexed coverage, and
content-based role inference without assuming a specific subject, lecturer,
university, language, or filename convention:

```bash
uv run python -m scripts.benchmark_document_understanding path/to/armory \
  --min-documents 5 \
  --require-role slides \
  --require-role past_exam \
  --require-role assignment \
  --min-role-confidence 0.75 \
  --json-report .artifacts/document-understanding.json
```

Use this as a preflight for arbitrary user material. It does not replace
labelled benchmarks, but it catches the common "the corpus indexed as vague
references" failure before RAG answers or priority reports are trusted.
Required roles are checked against indexed documents, so an unreadable file or
filename-only guess cannot satisfy the preflight role gate.

The JSON report includes per-case results, not only aggregate scores. Retrieval
cases include expected references, retrieved references, scores, and compact
chunk excerpts. Index-integrity cases include source paths, chunk counts,
missing required text, and forbidden extraction noise. Answer cases include the
answer excerpt, evidence references, verified and unverified citations, missing
required text, forbidden text, unsupported claims, answer-shape failures, and
evidence-coverage failures. Document-understanding reports include overview
source coverage so broad-summary regressions are visible in saved artifacts.
This makes failed artifacts inspectable from CI output or a local `.artifacts/`
directory.

Compare two saved benchmark reports:

```bash
uv run python -m scripts.compare_benchmark_reports \
  .artifacts/benchmark-suite.baseline.json \
  .artifacts/benchmark-suite.current.json \
  --tolerance 0.001
```

Or make the suite fail on a regression while it runs:

```bash
uv run python -m scripts.run_benchmark_suite \
  --json-report .artifacts/benchmark-suite.current.json \
  --compare-to .artifacts/benchmark-suite.baseline.json \
  --compare-tolerance 0.001
```

Run the strict completion audit after deterministic suite, real-corpus manifest,
and model-matrix reports exist:

```bash
uv run python -m scripts.audit_agent_harness_completion \
  --real-manifest path/to/real-corpus/manifest.json \
  --real-preflight-report .artifacts/real-corpus-preflight.json \
  --model-matrix-report .artifacts/model-eval/matrix.report.json \
  --json-report .artifacts/harness-completion-audit.json
```

This command is expected to fail until all external proof points are present:
the real-corpus manifest, the matching real-corpus preflight report, and the
model-backed local/frontier matrix. It exists to keep synthetic fixtures and
local smoke checks from being mistaken for full academic competitiveness.

Before running a model-backed matrix, validate the matrix, armory path, and
replay dataset breadth without model calls. For completion evidence, the replay
dataset path must be declared by the real-corpus manifest with
`kind: "model-replay-prompts"`. The real-corpus manifest must also declare
`kind: "chat-events"` and `kind: "chat-event-answer-expectation"` datasets so
the proof package includes the public harness stream that shows reading,
evidence use, writing, turn completion, and any runtime execution notes emitted
while tools recover from failures or oversized results:

```bash
uv run python -m scripts.run_model_eval_matrix \
  path/to/real-armory \
  path/to/replay.jsonl \
  benchmarks/model-matrix.example.json \
  .artifacts/model-eval \
  --validate-inputs \
  --json-report .artifacts/model-eval/matrix.inputs.json
```

Then run the actual local/frontier replay matrix and save the report used by
the completion audit:

```bash
uv run python -m scripts.run_model_eval_matrix \
  path/to/real-armory \
  path/to/replay.jsonl \
  path/to/model-matrix.json \
  .artifacts/model-eval \
  --min-evidence-coverage 1.0 \
  --json-report .artifacts/model-eval/matrix.report.json
```

Both validate-input and full matrix reports record replay case count, labelled
domains, and labelled tasks. The full run must score exactly the replay dataset
it was given, so stale or partial child reports cannot masquerade as passing
model evidence. The completion audit also checks that the matrix armory matches
the real-corpus preflight armory and that the matrix replay dataset is declared
by the real-corpus manifest, alongside real-corpus chat-event and answer
expectation datasets. During audit, each saved answer fixture is rescored with
`scripts.benchmark_answers`; claimed child-report metrics must match the
rescored fixture metrics.

For a real or permissioned corpus that is not fully labelled yet, run the
preflight wrapper first. It validates the manifest breadth and runs the generic
document-understanding smoke benchmark in one report:

```bash
uv run python -m scripts.run_real_corpus_preflight \
  path/to/real-armory \
  path/to/real-corpus/manifest.json \
  --json-report .artifacts/real-corpus-preflight.json
```

The preflight report is not a replacement for labelled RAG/answer/model evals;
it is the gate that says the corpus is broad enough and extraction/role
understanding is healthy enough to justify investing in labels.

## Retrieval Datasets

Use retrieval datasets to answer: "Did the retriever find the evidence a correct
answer would need, and did it avoid ranking plausible wrong evidence first?"

```json
{"id": "dijkstra-source", "domain": "computer-science", "task": "single-source-fact", "query": "How does Dijkstra choose the next node?", "expected": ["materials/graphs.md"]}
{"id": "dijkstra-near-miss", "domain": "computer-science", "task": "near-miss-negative", "query": "Which data structure chooses Dijkstra's frontier node?", "expected": ["materials/graphs.md"], "forbidden_before_expected": ["materials/bellman-ford.md"]}
{"id": "calculus-physics-synthesis", "domain": "cross-domain", "task": "multi-source-synthesis", "query": "Which sources answer both integration by parts and Fourier transforms?", "expected": ["materials/calculus.md", "materials/physics.md"], "top_k": 4}
{"id": "abstention-policy", "domain": "study-methods", "task": "abstention-policy", "query": "What should the tutor do without source evidence?", "expected": ["materials/grounding.md#chunk=0"]}
```

Run:

```bash
uv run python -m scripts.benchmark_rag path/to/armory benchmarks/rag.example.jsonl \
  --min-hit-rate 0.85 \
  --min-mrr 0.70 \
  --min-expected-recall 1.0 \
  --min-forbidden-before-expected-avoidance 1.0
```

The committed suite must label enough domains and retrieval tasks to catch
subject-specific, query-shape-specific, and near-miss evidence-ranking
regressions. It must also contain at least one multi-source case so expected
recall proves synthesis evidence was retrieved from more than one source.

## Material Role Datasets

Use material role datasets to answer: "Did Hephaistos identify lectures,
exercise sheets, past exams, and other material roles from paths plus extracted
text?"

```json
{"id": "lecture-role", "domain": "biology", "source": "materials/lecture.md", "expected_role": "lecture"}
{"id": "exercise-role", "domain": "mathematics", "source": "materials/sheet.md", "expected_role": "assignment"}
{"id": "exam-role", "domain": "history", "source": "materials/past-exam.md", "expected_role": "past_exam"}
```

Run:

```bash
uv run python -m scripts.benchmark_material_roles path/to/armory \
  benchmarks/academic/material_roles.jsonl \
  --min-pass-rate 1.0
```

The committed suite must cover multiple labelled domains and multiple material
role types. This is intentional: a benchmark that only contains one lecturer,
one language, or one subject cannot prove that document understanding is
general.

## Document Understanding Smoke

Use document-understanding smoke checks before labelled eval cases exist. They
answer: "Can Hephaistos see, index, classify, and overview the enabled
materials without course-specific assumptions?"

```bash
uv run python -m scripts.benchmark_document_understanding path/to/armory \
  --min-documents 9 \
  --require-role slides \
  --require-role past_exam \
  --min-overview-source-coverage 1.0
```

This reports visible materials, indexed documents, inferred visible and indexed
roles, extraction health, and `overview_source_coverage`. The overview coverage
metric is deliberately simple: for a broad "what is this material about?"
request, the harness should sample across indexed sources instead of letting a
few long chunks from early documents crowd out the rest of the corpus. For very
large corpora, the smoke check treats reaching the overview sample cap as
healthy even when the sampled/total percentage is low.
For large real-corpus proof, `scripts.run_real_corpus_preflight` applies a
bounded overview-coverage floor by default; raise
`--min-overview-source-coverage` when validating smaller corpora where full
source coverage should fit in one overview turn.

## Index Integrity Datasets

Use index integrity datasets to answer: "Did extraction, normalization, and
chunking preserve source text before retrieval or model answering starts?"

```json
{"id": "lecture-topic-text", "domain": "mathematics", "task": "topic-extraction", "source": "materials/lecture.md", "must_include": ["Administrative header", "Matrix multiplication"], "must_not_include": ["Formula-not-decoded"]}
{"id": "exam-format-text", "domain": "mathematics", "task": "exam-format-preservation", "source": "materials/past-exam.md", "must_include": ["Aufgabe 1 [8 Punkte]"], "must_not_include": ["Matrikelnummcr"]}
```

Run:

```bash
uv run python -m scripts.benchmark_index_integrity path/to/armory \
  benchmarks/academic/index_integrity.jsonl \
  --min-pass-rate 1.0 \
  --min-required-text 1.0 \
  --min-forbidden-text 1.0 \
  --min-corpus-forbidden-text 1.0
```

For a new arbitrary armory before labelled cases exist, run the corpus-wide
extraction health scan alone:

```bash
uv run python -m scripts.benchmark_index_integrity path/to/armory --scan-only \
  --min-corpus-forbidden-text 1.0
```

The same generic extraction health check is available as a product command:

```bash
uv run heph health path/to/armory
```

This gate is deliberately subject-neutral. Cases should name observable source
properties: preserved Unicode, domain terminology, formulas rendered as usable
text, tables not collapsed into garbage, exam point formats retained, exercise
numbering retained, and extraction placeholders removed. In addition to labelled
cases, the benchmark scans every indexed document for generic extraction poison
such as undecoded formulas/images/tables and Docling image/table comments. The
suite rejects narrow index-integrity coverage across both tasks and domains so
it cannot pass by only proving a single language, lecturer, subject, or file
shape.

## Priority Datasets

Use priority datasets to answer: "Did the deterministic study-priority scanner
rank real academic topics and reject boilerplate/OCR noise?"

```json
{
  "id": "mathematics-priority",
  "domain": "mathematics",
  "expected_topics": ["matrix multiplication"],
  "expected_ordered_topics": ["matrix multiplication", "eigenvalues"],
  "expected_mark_totals": {"matrix multiplication": 8},
  "expected_tiers": {"matrix multiplication": "High-yield"},
  "forbidden_topics": ["administrative line", "administrative header"],
  "expected_past_exam_sources": ["materials/past-exam-a.md"],
  "limit": 6
}
```

Use `expected_ordered_topics`, `expected_mark_totals`, and `expected_tiers`
when a case needs to prove exam weighting rather than only topic presence.

Run:

```bash
uv run python -m scripts.benchmark_priority path/to/armory benchmarks/academic/priority.jsonl \
  --min-pass-rate 1.0 \
  --min-topic-recall 1.0 \
  --min-forbidden-avoidance 1.0 \
  --min-past-exam-source-recall 1.0
```

## Grounded Answer Datasets

Use answer datasets to answer: "Did a saved model output obey the grounding
contract and any task-specific response shape?"

```json
{
  "id": "dijkstra-cited",
  "domain": "computer-science",
  "task": "grounded-explanation",
  "answer": "Dijkstra uses a priority queue to choose the next node [E1].",
  "evidence": [
    {
      "id": "E1",
      "source": "materials/graphs.md",
      "chunk": 0,
      "text": "Dijkstra shortest paths use a priority queue."
    }
  ],
  "expected_citations": ["E1"],
  "must_include": ["priority queue"],
  "must_not_include": ["negative weights"],
  "supported_claims": [
    {"text": "priority queue", "evidence_id": "E1"}
  ]
}
```

For active-recall assessment cases, use `required_label` to enforce the study
controller contract that feedback starts with exactly one assessment label. Add
`required_sections` when the case should also enforce rubric-style feedback
fields such as score, missing points, misconception correction, and the next
retrieval prompt:

```json
{
  "id": "active-recall-partial",
  "task": "active-recall-assessment",
  "answer": "PARTIAL: You recalled the definition but missed why it matters.",
  "require_citations": false,
  "required_label": "PARTIAL",
  "required_sections": ["Score", "Got", "Missing", "Misconception", "Correction", "Try again"],
  "must_not_include": ["[E1]", "The full answer is"]
}
```

For hint cases, make the first-step nudge explicit and forbid answer reveals,
citations, and source labels:

```json
{
  "id": "active-recall-hint",
  "task": "hint",
  "answer": "Start by naming the rule before applying the formula.",
  "require_citations": false,
  "must_include": ["Start by"],
  "must_not_include": ["The full answer is", "[E1]", "Source:"]
}
```

For no-evidence cases, set `require_abstention` so the answer must explicitly
say that the indexed sources are insufficient:

```json
{
  "id": "unknown-topic",
  "answer": "The enabled sources do not contain that answer.",
  "require_citations": false,
  "require_abstention": true,
  "must_not_include": ["probably"]
}
```

Run:

```bash
uv run python -m scripts.benchmark_answers benchmarks/answers.example.jsonl \
  --min-pass-rate 0.90 \
  --min-citation-validity 1.0 \
  --min-citation-presence 0.95 \
  --min-expected-citations 1.0 \
  --min-required-text 1.0 \
  --min-forbidden-text 1.0 \
  --min-supported-claims 1.0 \
  --min-answer-shape 1.0 \
  --min-evidence-coverage 1.0 \
  --min-required-label 1.0
```

The committed answer fixture suite must also label multiple domains and answer
tasks so saved model outputs cannot pass by only proving one response shape. It
must include at least one multi-evidence synthesis answer with citations to more
than one source and at least one active-recall assessment with a required
feedback label. It must also include at least one hint case that proves the
harness can nudge without revealing the answer. When a case sets
`min_distinct_sources`, the benchmark counts distinct sources from verified
citations in the answer, not merely from retrieved evidence. When a case sets
`min_bullet_count`, the answer must include that many markdown-style bullet
lines, which lets overview cases reject dense paragraph output even if citations
are syntactically valid. `min_cited_bullet_count` further requires that many
bullet lines to contain evidence citations. `max_explicit_date_lines` lets
overview cases reject chronological document walk-throughs that mention several
lecture/file dates instead of synthesizing the big picture. Material-overview
cases also fail when multiple bullet or numbered lines are shaped as a
chronological walkthrough, even if they avoid explicit dates.

## Study-State Datasets

Use study-state datasets to answer: "Did the harness move through the active
recall state machine correctly, and did a completed recall attempt create a
review schedule item?"

```json
{
  "id": "fast-correct-review",
  "domain": "mathematics",
  "expected_final_phase": "presenting",
  "expected_scheduled_reviews": 1,
  "expected_scheduled_concepts": ["Explain integration by parts"],
  "expected_schedule_error_types": ["correct"],
  "expected_schedule_failures": [0],
  "turns": [
    {
      "user": "Explain integration by parts",
      "reply": "Use the product-rule rearrangement.",
      "source_refs": ["materials/calculus.md#chunk=0"],
      "expected_action": "present",
      "expected_phase": "waiting_for_ready",
      "expected_feedback": "presented"
    },
    {
      "user": "ready",
      "reply": "State it from memory.",
      "expected_action": "prompt_recall",
      "expected_phase": "recall",
      "expected_feedback": "ready",
      "prompt_must_include": ["same language as the current item"],
      "prompt_must_not_include": ["End with exactly: Answer from memory"]
    },
    {
      "user": "Integral of u dv equals uv minus integral v du. Confidence 4/5.",
      "reply": "CORRECT: Correct.",
      "source_refs": ["materials/calculus.md#chunk=0"],
      "advance_seconds": 18,
      "expected_action": "assess",
      "expected_rating": "easy",
      "expected_confidence": 0.8,
      "record_schedule": true
    }
  ]
}
```

Run:

```bash
uv run python -m scripts.benchmark_study_state benchmarks/academic/study_state.jsonl \
  --armory benchmarks/academic/armory \
  --min-pass-rate 1.0 \
  --min-transition-pass-rate 1.0 \
  --min-scheduling-pass-rate 1.0
```

The committed suite must include multiple labelled domains and at least one
scheduling case with concept, error type, failure count, latency, and confidence
metadata plus retrieval-success and transfer-success signals. At least one turn
must also include prompt contract checks with `prompt_must_include` or
`prompt_must_not_include`, so the state harness can protect language,
instruction-shape, and no-boilerplate prompt requirements instead of only
checking state transitions. Corpus material-overview turns must remain normal
answers in the `presenting` phase, not arm the ready/recall loop; separate
topic-presentation cases cover that loop. The suite report exposes
`study_state.mastery_metadata_rate` and `study_state.prompt_contract_rate`, and
the default comparator tracks both so scheduled-review metadata and prompt
contract regressions are caught without hand-inspecting JSON. This keeps the
active-recall harness honest without binding it to a specific lecturer,
language, or subject.

## Academic Item Datasets

Use academic item datasets to answer: "Did deterministic extraction preserve
traceable concepts, definitions, formulas, figures, tables, exam questions,
answers, rubric points, and exam-skill cues for later course graph work?"

```json
{
  "id": "hamiltonian-definition",
  "domain": "physics",
  "source_ref": "materials/physics-lecture.md#chunk=1",
  "kind": "definition",
  "concept": "Hamiltonian mechanics",
  "text": "generalized coordinates, canonical momentum"
}
```

Run:

```bash
uv run python -m scripts.benchmark_academic_items \
  benchmarks/academic/armory \
  benchmarks/academic/academic_items.jsonl \
  --min-pass-rate 1.0 \
  --min-grounded-question-rate 1.0 \
  --min-canonical-source-label-rate 1.0 \
  --min-question-quality-rate 1.0 \
  --min-question-types 6
```

The committed suite should cover at least definitions, formula-like source
spans, figure/table captions, exam questions, answers, rubric points, and
exam-skill cues. It should also generate several grounded question styles so
active recall does not collapse to one prompt template, and the generated
questions should avoid metadata trivia, filenames, chunk IDs, and internal
source-control wording. Each generated question also carries a canonical
human-facing `source_label` separated from internal chunk refs; labels are
expected to be exact source names such as `3 Requirements Engineering`, not
filenames, dates, or `#chunk` locators.

## Replay Datasets

Use replay datasets to answer: "What does the current harness/model produce for
these prompts?"

```json
{"id": "dijkstra-replay", "domain": "computer-science", "task": "grounded-explanation", "prompt": "Using the sources, explain how Dijkstra chooses the next node.", "must_include": ["priority queue"], "supported_claims": [{"text": "priority queue", "evidence_id": "E1"}]}
```

Run the prompts through the real chat harness:

```bash
uv run python -m scripts.replay_answer_benchmark path/to/armory \
  benchmarks/replay.example.jsonl \
  .artifacts/answers.current.jsonl \
  --model gpt-4.1
```

Then score the generated answer fixtures:

```bash
uv run python -m scripts.benchmark_answers .artifacts/answers.current.jsonl \
  --min-pass-rate 0.90 \
  --min-citation-validity 1.0 \
  --min-citation-presence 0.95 \
  --min-expected-citations 1.0 \
  --min-required-text 1.0 \
  --min-forbidden-text 1.0 \
  --min-supported-claims 1.0 \
  --min-answer-shape 1.0 \
  --min-evidence-coverage 1.0 \
  --min-required-label 1.0
```

Or run the model-backed replay and scoring gates in one command:

```bash
uv run python -m scripts.run_replay_answer_eval path/to/armory \
  benchmarks/academic/replay.jsonl \
  .artifacts/answers.current.jsonl \
  --json-report .artifacts/answers.current.report.json \
  --model gpt-4.1 \
  --min-answer-pass-rate 1.0 \
  --min-citation-validity 1.0 \
  --min-citation-presence 1.0 \
  --min-expected-citations 1.0 \
  --min-required-text 1.0 \
  --min-forbidden-text 1.0 \
  --min-supported-claims 1.0 \
  --min-answer-shape 1.0 \
  --min-evidence-coverage 1.0 \
  --min-required-label 1.0
```

The default replay suite must include multiple labelled answer tasks, including
grounded citation behavior and abstention behavior.

You can compare replay-eval reports with the same report comparator:

```bash
uv run python -m scripts.compare_benchmark_reports \
  .artifacts/answers.baseline.report.json \
  .artifacts/answers.current.report.json \
  --metric report.pass_rate \
  --metric report.supported_claim_rate \
  --metric report.answer_shape_rate \
  --metric report.evidence_coverage_rate
```

The replay runner can also compare directly against a saved baseline report by
adding `--compare-to .artifacts/answers.baseline.report.json` to the replay
command above.

For full-suite reports, the default comparator also tracks public chat-event
health metrics, including `chat_events.material_operation_metadata_rate`,
`chat_events.evidence_metadata_rate`,
`chat_runtime_events.material_operation_metadata_rate`,
`chat_runtime_events.tool_runtime_metadata_rate`, and
`chat_runtime_events.acceptance_criteria_metadata_rate`, so visible harness
metadata regressions are caught without scraping terminal output. The default
academic suite includes both a normal public chat stream and a small
runtime-note stream that exercises `acceptance_criteria` and `tool_runtime`
metadata, including failed-call and repeated-call execution notes.

## Model Eval Matrix

Use the model eval matrix to answer: "Do the same replay prompts pass on both a
small/local model and a frontier hosted model?"

Create a JSON matrix. A starter file is available at
`benchmarks/model-matrix.example.json`:

```json
{
  "candidates": [
    {
      "id": "local-small",
      "group": "local",
      "model": "llama-3.1-8b",
      "base_url": "http://localhost:11434/v1",
      "api_key_env": "LOCAL_OPENAI_API_KEY",
      "responsibilities": ["chunk labeling", "question formatting"]
    },
    {
      "id": "frontier-hosted",
      "group": "frontier",
      "model": "gpt-4.1",
      "api_key_env": "OPENAI_API_KEY",
      "responsibilities": ["complex explanation", "misconception correction"]
    }
  ]
}
```

`responsibilities` is descriptive metadata that travels into matrix result
reports. Use it to document the intended harness split between smaller local
models and frontier tutoring/evaluation models; the replay gates still decide
whether each candidate actually passes.

Then run:

```bash
uv run python -m scripts.run_model_eval_matrix \
  path/to/armory \
  benchmarks/academic/replay.jsonl \
  benchmarks/model-matrix.example.json \
  .artifacts/model-eval \
  --min-evidence-coverage 1.0 \
  --json-report .artifacts/model-eval/matrix.report.json
```

To validate the candidate groups and report shape without calling any models:

```bash
uv run python -m scripts.run_model_eval_matrix \
  path/to/armory \
  benchmarks/academic/replay.jsonl \
  benchmarks/model-matrix.example.json \
  .artifacts/model-eval \
  --validate-only \
  --json-report .artifacts/model-eval/matrix.validate.json
```

By default the matrix requires at least one `local` candidate and one
`frontier` candidate. It writes one answer fixture and one scored report per
candidate, then writes a combined report with pass/fail status and answer
quality metrics including `evidence_coverage_rate`. API keys may come from
`api_key_env`; they are used for the run but are not written to reports.

## Trace Replay

Use trace replay to answer: "Can I turn a bad live session into a scored,
repeatable benchmark case?"

```bash
uv run python -m scripts.trace_to_answer_benchmark \
  path/to/armory/.hephaistos/traces/session-id.jsonl \
  .artifacts/answers.from-trace.jsonl \
  --expectations .artifacts/trace-expectations.json \
  --expect-all-citations \
  --score
```

The converter uses `reply` trace events and their recorded `evidence_items` and
`evidence_coverage`.
Generated fixtures can be checked with `scripts.benchmark_answers` or edited
into a committed benchmark dataset after removing private or copyrighted text.
The optional expectations file may be a JSON list or `{"cases": [...]}` with
entries keyed by either `turn` or generated fixture `id`; supported fields are
`domain`, `task`, `require_citations`, `require_abstention`,
`required_label`, `expected_citations`, `must_include`, `must_not_include`, and
`supported_claims`. Answer fixtures may also set `min_words`, `max_words`,
`min_citation_count`, `min_distinct_sources`, `min_sampled_sources`,
`min_bullet_count`, `min_cited_bullet_count`, and `max_explicit_date_lines` so
vague, narrow, under-sampled, hard-to-read, chronological, or uncited structured
responses fail even when they contain syntactically valid citations somewhere.
Material-overview cases are additionally checked for repeated chronology-shaped
lines such as first/then/later document walkthroughs.
Material-overview trace replay adds a default `min_sampled_sources=2` gate.

## What To Add

Prefer small, labelled cases that catch real failures:

- Exact phrase lookup from source materials.
- Single-source concept questions.
- Multi-document synthesis questions.
- Past-exam priority and prerequisite questions.
- No-evidence questions where the correct behavior is abstention.
- Active-recall assessment answers with required labels such as `CORRECT:`,
  `PARTIAL:`, or `WRONG:`.

Benchmarks should stay local-first. Do not commit private study material,
user data, API responses with secrets, or copyrighted source text beyond
short fair-use snippets needed to validate behavior.
