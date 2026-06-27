<coding_guidelines>
# Heph — Agent Guide

NEVER create regex label lists / phrase-catching architecture and ALWAYS solve the problem structurally with this mindset: https://mariozechner.at/posts/2025-06-02-prompts-are-code/.

## Core Shape

Protect this shape in every change:

- Heph answers from local armory materials with accurate, cited responses.
- Armories stay portable normal directories.
- Answers are grounded in user materials and citations remain verifiable.
- Memory is scoped to the armory unless the user explicitly opts into a shared service.
- Provider and model choices stay swappable; vendor-specific behavior remains optional.
- `ai.*` stays provider/model API substrate and should almost never change for
  Heph-specific behavior.
- The harness owns correctness guardrails, validation, armory state, retrieval,
  citation checks, memory, and diagnostics. It is not a second agent brain.
- Heph owns agent identity, conversational strategy, research orchestration, and
  user-facing composition. Move new brain behavior toward Heph-facing modules,
  while calling the harness for correctness.
- Never hardcode user-private corpus details: university names, course titles, lecturer names,
  campus platforms, armory names, local paths, or one-off source-file vocabulary. Retrieval and
  overview fixes must use provider-swappable prompts, semantic evidence handling, and generic
  fixtures instead of private keyword lists. Add local private terms to
  `.git/info/heph-private-corpus-terms` and run
  `uv run python -m scripts.check_repo_policies` before handing off.

## Setup
```bash
uv sync --frozen           # install all dependencies
uv sync --frozen --group dev        # install dev tools (lint, type-check, test)
```

## Run
```bash
uv run heph                # launch the TUI
uv run heph PATH           # launch Heph for an armory
uv run heph armory init NAME    # create a new armory in ~/.armories
```

## Development Workflow

1. Make focused changes from current `main`.
2. Follow existing package boundaries and local helper APIs.
3. Add or update tests for behavior that could break.
4. Update user-facing docs when commands, armory behavior, retrieval, citation checks,
   memory, provider setup, privacy, or diagnostics behavior changes.
5. Run the narrowest useful checks before handing off.
6. Use short conventional-style commit subjects when asked to commit:
   `fix: ...`, `core: ...`, `tui: ...`, `docs: ...`, `test: ...`,
   `refactor: ...`, or `chore: ...`.

## Docs Sync
<!-- sync-docs:privacy-diagnostics-docs-contract:start -->
- Privacy and diagnostics rule: PostHog is anonymous opt-in maintainer visibility only; Sentry
  is redacted opt-in crash reporting only.
- Preserve the public safe-stub split in `packages/hephaion/src/hephaion/privacy/release.py`.
  Official release builds inject privacy and diagnostics backend values in CI; source, editable, and
  Git installs must stay bare by default.
- When CLI commands, privacy or diagnostics surfaces, or README-adjacent docs change, run
  `uv run python -m scripts.sync_docs` and keep `README.md`, `docs/index.md`,
  `docs/cli-reference.md`, `AGENTS.md`, and the architecture privacy and diagnostics section
  aligned.
<!-- sync-docs:privacy-diagnostics-docs-contract:end -->

## Core Code Style

- Python ≥3.13 only.
- Every Python module starts with `from __future__ import annotations`.
- Line length: 99 characters. Quotes: double. Line endings: LF.
- Naming is enforced by Ruff N rules:
  - Classes: `PascalCase`
  - Functions and variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private implementation helpers: leading underscore
- Prefer clear, readable code over clever abstractions or micro-optimizations.
- Never write one-line function wrappers.
- Keep comments sparse and useful; explain why a non-obvious block exists.

## Type Checking Policy

- Use `ty` strict mode. `pyproject.toml` targets Python 3.13 and includes
  `hephaion` and `tests`; all rules are errors except configured import handling.
- Explicit `Any` is forbidden, including imports from `typing` or `typing_extensions`,
  bare `Any`, attribute references (`typing.Any`, `typing_extensions.Any`), and
  `cast()` string arguments that mention `Any`.
- Use concrete SDK types, `TypedDict`, dataclasses, protocols, or narrow unions instead.
- Prefer fixing the type issue. Suppressions are last resort only for small,
  provably safe abstractions the checker cannot recognize.
- Ty suppressions must use exact diagnostics: `# ty:ignore[exact-diagnostic]`.
- Ruff suppressions must use exact rules: `# noqa: RULE`.
- Do not use `# type: ignore[...]` or legacy `# ty: ignore`.
- Do not suppress private-usage diagnostics with broad type ignores.
- Type-only imports belong in `if TYPE_CHECKING:` blocks when runtime imports are undesirable.

## Import Architecture

- Protected core packages:
  - `ai.*`: provider/model API substrate only.
  - `hephaion.*`: harness implementation namespace: guardrails, armories, retrieval,
    citations, memory, diagnostics, and session state.
  - `heph.*`: agent identity, brain/composition, CLI entrypoint, and
    slash-command coordination.
- Adapter surface: `heph.cli`, `heph.commands`, `interfaces.tui`, and most
  `interfaces.terminal` modules.
  Adapters may depend broadly, but reusable decisions should move into services or domains.
- AI reusable packages: `ai.runtime`, `ai.providers`, `ai.logging`,
  `ai.diagnostics`, `ai.types`.
- Harness reusable packages: `hephaion.matching`, `hephaion._types`,
  `hephaion.materials`, `hephaion.rag`, `hephaion.memory`, `hephaion.armory`,
  `hephaion.vocab`, `hephaion.learning`, `hephaion.study`, `hephaion.chat`,
  and focused workflow modules.
- Reusable packages, including `hephaion.privacy` and `hephaion.diagnostics`, must not
  import adapters (`heph.cli`, `heph.commands`, `interfaces.tui`,
  `interfaces.terminal.history`, `interfaces.terminal.input`).
- `ai.logging` and `hephaion.diagnostics` must not import adapters.
- `hephaion.materials` owns discovery/ignore policy and must not import
  `hephaion.chat`, `hephaion.agent`, `hephaion.rag`, or `hephaion.study`.
- `hephaion.rag` may import `hephaion.materials`; it must not import
  `hephaion.agent`, `hephaion.chat`, `interfaces.tui`, or `hephaion.study`.
- `ai.runtime` stays below product workflows and must not import adapters,
  `hephaion.chat`, `hephaion.agent`, `hephaion.rag`, `hephaion.study`,
  `hephaion.materials`, `hephaion.memory`, or `hephaion.armory`.
- `providers` owns model/provider config and auth; it must not import adapters,
  `ai.runtime`, `hephaion.chat`, `hephaion.agent`, `hephaion.rag`,
  `hephaion.study`, or `hephaion.materials`.
- `hephaion.memory` may use `ai.runtime`, but must not import adapters,
  `hephaion.chat`, or `hephaion.agent`.
- `hephaion.study` remains a controller/state layer and must not import adapters,
  `hephaion.chat`, `hephaion.agent`, or `hephaion.rag`.
- `hephaion.agent` must not import `hephaion.chat`.
- Keep `hephaion.chat.session` and `hephaion.chat.orchestrator` independent at runtime.
- `heph.commands` must not import `interfaces.tui`.
- Standard top-level imports are the default.
- Deferred imports are allowed only for optional extras, plugin loading, or measured
  startup-critical paths allowlisted in `scripts/check_repo_policies.py`.
- Imports inside `TYPE_CHECKING` guards or optional-dependency `try` blocks are policy-allowed.
- Dynamic import helpers are file-allowlisted by `scripts/check_repo_policies.py`;
  `__import__` is forbidden.

## Tooling Configuration

- Use `uv` for dependency management and command execution.
- Use `ruff` for linting and formatting.
- Use `ty` for type checking.
- Ruff selected rule families include: `E`, `W`, `F`, `I`, `UP`, `B`, `SIM`, `RUF`,
  `A`, `C4`, `DTZ`, `EM`, `EXE`, `ISC`, `ICN`, `LOG`, `G`, `PIE`, `PYI`, `PT`,
  `Q`, `R`, `RET`, `SLOT`, `T10`, `TCH`, `INT`, `ARG`, `PTH`, `TD`, `FIX`,
  `ERA`, `PGH`, `PL`, `TRY`, `FURB`, `PERF`, and `N`.
- Notable Ruff ignores are intentional for data/config shapes, test magic numbers,
  TODO usage, protocol-required unused arguments, complexity thresholds, and deferred imports
  controlled by the custom policy checker.

## Lint & Format
```bash
uv run ruff check .        # lint
uv run ruff check --fix .  # lint with auto-fix
uv run ruff format .       # format
uv run ruff format --check .  # format check (CI mode)
uv run python -m scripts.check_repo_policies  # no Any / unapproved deferred imports
```

## Type Check
```bash
uv run ty check  # type-check the project
```

## Dead Code / Architecture / Quality Gates
```bash
uv run vulture packages/ai/src packages/extensions/src packages/heph/src packages/hephaion/src packages/interfaces/src packages/ai/test packages/extensions/test packages/heph/test packages/hephaion/test packages/interfaces/test vulture-whitelist.py  # dead-code detection
uv run pylint --persistent=no --score=no --disable=all --enable=duplicate-code packages/ai/src packages/extensions/src packages/heph/src packages/hephaion/src packages/interfaces/src  # duplicate code
uv run lint-imports        # verify import boundaries
uv run python scripts/check_architecture_guardrails.py  # guard architecture debt baselines
uv run python scripts/check_tech_debt.py --strict  # TODO/FIXME issue links
uv run python scripts/validate_agents_md.py --strict  # AGENTS.md command validation
```

Additional configured gates:

- Vulture scans all workspace package source/test trees and `vulture-whitelist.py` at 80%
  confidence.
- Pylint duplicate-code uses an 8-line similarity threshold and ignores comments,
  docstrings, and imports.
- Architecture guardrails enforce no regression against current module size, function size,
  class size, complexity, and package-facade import baselines.
- Pre-commit also runs check-large-files, gitleaks, docs sync, ty via
  `astral-sh/ty-pre-commit`, deptry, and radon.
- Bandit is configured in `pyproject.toml`; run it when touching security-sensitive code.

## Test
```bash
uv run pytest                              # run all tests
uv run pytest --cov --cov-fail-under=46    # run with current coverage baseline
uv run pytest packages/ai/test/test_chat_engine.py    # single file
uv run pytest packages/interfaces/test/test_app_tui.py -x      # stop on first failure
uv run pytest -k "test_stream_recovery"    # by keyword
uv run pytest -m flaky                     # flaky-marked tests only
```

Testing rules:

- Pytest uses strict markers, short tracebacks, top-10 duration reporting,
  xdist auto/worksteal, and a 46% coverage baseline on `hephaion`; raise it toward
  the long-term 75% target as characterization coverage improves.
- Test files: `test_<module>.py` or `*_test.py`; test classes: `Test<Feature>`;
  test functions: `test_<verb>_<object>_<condition_or_expectation>`.
- Parametrize with tuple names, list values, and tuple rows.
- `pytest.raises()` for broad exceptions (`Exception`, `ValueError`, `TypeError`,
  `RuntimeError`, `OSError`) must include `match=`.
- Use `tmp_path`, `monkeypatch`, and shared fixtures from `tests/conftest.py`.
  Do not touch real user config, auth, network, or armory state unless the test is
  explicitly integration-level.
- Mark flaky tests with `@pytest.mark.flaky(reruns=2, reruns_delay=1)`.
- Focus coverage on citation parsing/verification, armory-scoped memory, retrieval
  and stale indexes, provider/model switching, and learning-loop state transitions
  implemented by `hephaion.learning` and the `study` controller.

## Security and Repository Policy

- Do not commit secrets. Gitleaks runs in pre-commit; `.env.example`, tests, and
  `vulture-whitelist.py` are allowlisted for known false positives.
- Added files over 500KB are blocked by pre-commit. Keep large binary artifacts out of
  the repository unless a future Git LFS policy is added intentionally.
- API keys must not be written to config files; resolve them from OS keyring,
  environment variables, or the in-memory test store.
- Logs, diagnostics, traces, and crash reports must redact secrets before writing.
- Treat dependency updates as reviewed code changes.
- Direct external dependency declarations must be exact `==` pins; `uv.lock` remains the
  dependency ground truth.
- Set `HEPH_ALLOW_LOCKFILE_CHANGE=1` only after reviewing lockfile changes.
- Run `uv lock --check`, `uv run python -m scripts.check_dependency_pinning`,
  `uv run python -m scripts.check_dependency_sdist_allowlist`, and `uv audit --frozen`
  when dependencies change.

## Documentation and Naming Style

- Voice: practical, private, verification-first, and grounded in user files.
- Naming: use `Heph` for the public Python package, command, SDK surface, and
  user-facing app. Use `the harness` for the correctness layer. Use
  implementation identifiers such as `hephaion.*`, `.hephaion/`, and
  `HEPHAION_*` only when the exact namespace, state path, or environment
  variable is actionable.
- README and `docs/index.md` stay short and link-forward. Preserve the clickable
  Docs map. They cover what Heph does, armory structure, one start path, core
  commands, safety, and where to read next. Keep provider/model setup inside the
  command flow and linked docs, not as a standalone README section.
- User docs belong in `docs/`: armory workflows, materials/source files,
  provider and model setup, CLI and slash commands, privacy/network behavior,
  troubleshooting, and verifiable operational examples.
- Developer docs belong in `docs/developers/`, package READMEs, and `AGENTS.md`:
  package boundaries, import rules, policy gates, release/runbook steps, and
  agent instructions.
- Keep descriptions deterministic: say what exists, what command to run, what
  state is written, and what the user should expect. Prefer concrete examples
  over abstract claims.
- Name dependencies only in install, config, release, security, or debugging
  contexts where the exact package is actionable.
- Keep roadmap, marketing claims, maintainer-only operations, and optional
  alternatives out of user-facing docs unless a current command, config, release
  contract, or security contract requires them.
- Use learning-oriented copy (`learn`, `learning`, `recall`, `practice`) when
  the feature is actually about learning.
- Emphasize armories, materials/source files, retrieval, citation verification,
  learning memory, recall practice, provider/model choice, and local/private
  behavior.
- When docs or wiki conflict with code or `docs/`, prefer code and repo docs.

## Diagnostics

- Structured logging: `HEPHAION_LOG_LEVEL`, `HEPHAION_LOG_FILE`, `HEPHAION_LOG_FORMAT`
- Session traces: per-armory JSONL files under `.hephaion/traces/`
- Profiling: `--profile` (CPU) or `--profile-memory` (memory) CLI flags

## Build & Release
```bash
uv run python -m scripts.check_release_state --current-version-must-match-stable  # verify stable release metadata
uv run python -m scripts.build_release_artifacts                # build official sdists + wheels for the stable tag
uv run python -m scripts.release_stress_test --expect-runtime-channel pypi --expect-runtime-version v0.0.50
uv publish --dry-run dist/*                                     # validate upload payloads before publishing
uv run python -m scripts.check_public_install --expect-runtime-version v0.0.50
```
Publish PyPI releases manually from a reviewed `v*` tag with `UV_PUBLISH_TOKEN`
set in the environment, then verify `uv tool install heph@latest` and
`pip install heph` from a clean environment.
Edge deploys are published manually via `.github/workflows/deploy.yml`.

## Runbooks

Operational playbooks for incident response:

- `docs/runbooks/ci-failure.md` — CI failure triage
- `docs/runbooks/slow-llm-response.md` — Debug slow LLM responses
- `docs/runbooks/deployment-rollback.md` — Revert bad releases
- `docs/runbooks/rag-retrieval-issues.md` — Debug RAG quality

## Pre-commit Hooks

Configured hooks: ruff, ruff-format, check-large-files, gitleaks, sync-docs,
check-repo-policies, lockfile change review gate, dependency pinning,
source-only sdist allowlist, ty, vulture, pylint duplicate-code, lint-imports,
architecture guardrails, deptry, radon complexity, check-tech-debt, and validate-agents-md.
</coding_guidelines>
