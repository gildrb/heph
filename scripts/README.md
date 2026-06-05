# Repository Scripts

This directory contains project automation that is useful to the shared Hephaion
codebase. Keep personal, vendor-specific, or maintainer-only one-off helpers in
ignored local paths such as `benchmarks/`, `.artifacts/`, or personal agent
directories instead of tracked `scripts/`.

## CI And Policy Gates

- `sync_docs.py` keeps generated README and docs surfaces aligned.
- `check_repo_policies.py`, `check_architecture_guardrails.py`, `check_tech_debt.py`,
  and `validate_agents_md.py` enforce repository-specific quality rules.
- `check_lockfile_change.py`, `check_dependency_pinning.py`, and
  `check_dependency_sdist_allowlist.py` guard dependency and lockfile changes.
- `check_feature_flags.py` catches stale feature-flag wiring.

## Release And Build Helpers

- `release_stress_test.py` validates built release artifacts in isolation.
- `record_metrics.py` records CI timing/test metrics.
- `sync_labels.py` syncs GitHub labels from `.github/labels.yml`.

## Benchmark And Evaluation Tooling

- `run_benchmark_suite.py` runs the deterministic local Heph benchmark suite.
- `run_external_benchmarks.py`, `run_model_eval_matrix.py`, and
  `run_retrieval_ablation_matrix.py` exercise public or permissioned evaluation suites.
- `benchmark_*.py`, `compare_benchmark_reports.py`, `generate_benchmark_summary.py`,
  and `claim_report_envelope.py` score, compare, summarize, and package benchmark results.

## Corpus And Reproducibility Helpers

- `materialize_public_corpus.py`, `generate_public_academic_benchmark_cases.py`,
  `create_benchmark_manifest.py`, and `build_permissioned_corpus_armory.py` prepare
  benchmark-ready armories and manifests.
- `prepare_real_corpus_evidence.py`, `run_real_corpus_preflight.py`,
  `discover_real_corpus_candidates.py`, `trace_to_answer_benchmark.py`,
  `replay_answer_benchmark.py`, `run_replay_answer_eval.py`, `sample_benchmark_cases.py`,
  and `repro_bundle.py` turn local evidence into repeatable private checks.

## Local Diagnostics And Stress Tools

- `run_chat_reliability_gauntlet.py`, `create_chat_reliability_fixture.py`,
  `extract_chat_event_expectation.py`, and `tui_resize_stress.py` support targeted
  diagnostics for chat/event/TUI behavior.
- `export_enterprise_rag_answers.py` and `build_ms_marco_manifest.py` adapt external
  benchmark data without making those datasets part of the product.
