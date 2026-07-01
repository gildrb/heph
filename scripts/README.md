# Repository Scripts

This directory contains project automation for the shared Heph codebase. Keep
personal, vendor-specific, or maintainer-only one-off helpers in
ignored local paths such as `benchmarks/`, `.artifacts/`, or personal agent
directories instead of tracked `scripts/`.

`scripts/` should stay boring: repository policy, documentation sync, dependency
checks, release sanity checks, and small CI helpers. Benchmark suites, corpus
preparation, replay harnesses, stress tests, model matrices, and private proof
runs do not belong here.

## CI And Policy Gates

- `sync_docs.py` keeps generated README and docs surfaces aligned.
- `check_repo_policies.py`, `check_architecture_guardrails.py`, and
  `check_tech_debt.py` enforce repository-specific quality rules.
- `check_lockfile_change.py`, `check_dependency_pinning.py`, and
  `check_dependency_sdist_allowlist.py` guard dependency and lockfile changes.
- `check_release_state.py` verifies the official stable release pointer, package
  versions, license metadata, and optional git tag target.
- `check_dependency_vulnerability_audit.py` runs `uv audit --frozen` with reviewed,
  lockfile-scoped `--ignore-until-fixed` waivers when a temporary waiver is needed.
  PyTorch is expected only through the standard conversion runtime, not direct
  Heph source usage.
- `check_feature_flags.py` catches stale feature-flag wiring.
- `validate_agents_md.py` is a CI compatibility check that skips when the
  local-only `AGENTS.md` file is absent.

## Release And Build Helpers

- `build_release_artifacts.py` builds official release artifacts for the stable
  tag, verifies package inputs still match that tag, temporarily injects release
  channel/version metadata, and restores the tracked safe privacy stub.
- `release_stress_test.py` validates built release artifacts in isolation,
  including `uv tool install`, pip install, cross-platform dependency resolution,
  CLI startup, and SDK JSON output.
- `check_public_install.py` verifies the published PyPI package through isolated
  `uv tool install heph@latest` and `pip install heph` paths.
- `record_metrics.py` records CI timing/test metrics.
- `sync_labels.py` syncs GitHub labels from `.github/labels.yml`.
