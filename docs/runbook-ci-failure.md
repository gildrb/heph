# CI Failure Response

When the CI pipeline fails on the `main` branch, an issue is automatically
created or updated by the `ci-failure-issue.yml` workflow.

## Triage Steps

1. **Check the auto-created issue** - it contains the failed job name and
   a link to the failing workflow run. Start there.

2. **Identify the failing job** from the workflow run:
   - `lint` - ruff lint violations
   - `format` - ruff format differences
   - `typecheck` - ty type errors
   - `security` - Bandit or Gitleaks findings
   - `test` - pytest failures
   - `dead-code` - vulture findings
   - `duplicate-code` - pylint similarity
   - `docs-sync` - generated README/docs drift
   - `architecture` - import-linter violations
   - `build` - packaging errors

3. **Reproduce locally** using the matching command:
   ```bash
   uv run ruff check .          # lint
   uv run ruff format --check . # format
   uv run ty check    # typecheck
   uv run python -m scripts.sync_docs --check  # docs drift
   uv run python -m scripts.check_repo_policies  # repo policy drift
   uv run pytest                # tests
   ```

4. **Fix the issue** on a new branch and open a PR.

5. **Verify** - the CI must pass on the PR before merging. The auto-created
   issue is closed automatically when CI passes on `main`.

## Common Failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ruff check` fails | New lint rule violation | `uv run ruff check --fix .` |
| `repo policy check` fails | New `Any`, local import, or forbidden dynamic import | Replace `Any` with concrete types and move imports to module scope |
| `ty` fails | Type incompatibility | Add type annotations or narrow types |
| `vulture` fails | Unused code detected | Remove dead code or add to `vulture-whitelist.py` |
| `lint-imports` fails | Import boundary violation | Move import to `app` package or refactor |
| `pytest` fails | Test regression | Check if test is flaky (`@pytest.mark.flaky`) |

## Flaky Tests

If a test is intermittently failing, mark it with:
```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_something(): ...
```
The CI config reruns flaky-marked tests automatically.
