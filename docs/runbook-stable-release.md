# Stable Release

Use this runbook to publish a reviewed `heph` release to PyPI and GitHub.

## One-Time Trusted Publishing Setup

Stable releases are uploaded by GitHub Actions using PyPI Trusted Publishing.
This avoids storing long-lived PyPI tokens in GitHub or uploading from a local
maintainer shell.

The GitHub environment is `pypi`. If it needs to be recreated, create it in
GitHub repository settings or with:

```bash
gh api --method PUT repos/gildrb/heph/environments/pypi --input - <<'JSON'
{}
JSON
```

Configure PyPI once for the existing `heph` project:

1. Open `https://pypi.org/manage/project/heph/settings/publishing/`.
2. Add a GitHub Actions trusted publisher.
3. Use these values:
   - Owner: `gildrb`
   - Repository name: `heph`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
4. Revoke any manual upload tokens that are no longer needed.

GitHub Actions billing must allow workflow runs. If a release run fails before
starting with a billing or spending-limit message, fix billing before retrying
the run.

## Release Flow

The release workflow runs on `v*.*.*` tags and also supports manual dispatch
from `main` with a tag input.

Before tagging, make sure the stable pointer and package versions agree:

```bash
uv run python -m scripts.check_release_state --current-version-must-match-stable
```

Create and push the reviewed release commit on `main`, then push the tag:

```bash
git tag v0.0.59
git push origin main
git push origin v0.0.59
```

The workflow then:

1. Checks that the tag is reachable from `main`.
2. Runs repo policy, lint, type, security, dead-code, duplicate-code, and pytest gates.
3. Builds the bundled public `heph` wheel and sdist with release metadata.
4. Stress-tests the artifacts before upload.
5. Publishes to PyPI through the `pypi` GitHub environment and PyPI OIDC.
6. Installs the published version back from PyPI through `uv tool install` and
   plain `pip install`.
7. Creates the GitHub Release with the wheel, sdist, and release assets.

## Troubleshooting

- `pypi-publish` cannot mint a token: verify the PyPI trusted publisher values
  match `gildrb/heph`, `.github/workflows/release.yml`, and environment `pypi`.
- Release run never starts: check GitHub Actions billing or spending limits.
- Public install check cannot see the new version immediately: rerun the failed
  job after the PyPI simple index catches up.
- If a release must be uploaded manually as an emergency fallback, use a fresh
  project-scoped PyPI token, publish with `uv publish dist/*`, then revoke the
  token immediately.
