# Repository Scripts

This directory contains project automation that is useful to the shared Hephaion
codebase. Keep personal, vendor-specific, or maintainer-only one-off helpers in
ignored local paths such as `benchmarks/`, `.artifacts/`, or personal agent
directories instead of tracked `scripts/`.

`scripts/` should stay boring: repository policy, documentation sync, dependency
checks, release sanity checks, and small CI helpers. Benchmark suites, corpus
preparation, replay harnesses, stress tests, model matrices, and private proof
runs do not belong here.

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
