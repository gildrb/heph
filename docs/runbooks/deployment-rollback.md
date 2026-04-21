# Deployment Rollback

When a release or edge deploy causes problems, follow these steps to
revert and restore service.

## Edge Deploy (main branch)

Edge deploys run on every push to `main` via `.github/workflows/deploy.yml`.

### Rollback Steps

1. **Identify the bad commit** — check the [edge release](https://github.com/gildrb/hephaistos/releases/tag/edge)
   for the commit SHA.

2. **Revert the commit** on `main`:
   ```bash
   git revert <sha>
   git push origin main
   ```
   The revert push triggers a new edge deploy automatically.

3. **Verify** — check the new edge release and confirm the app works.

4. **Monitor** — watch the follow-up GitHub Actions run and do a quick smoke test
   with `heph --version` plus a basic armory command.

## PyPI Release (version tags)

Stable releases are published to PyPI on `v*` tags via `.github/workflows/release.yml`.

### Rollback Steps

1. **Yank the release from PyPI** (prevents new installs):
   ```bash
   pip install twine
   twine register --repository pypi "hephaistos==0.1.0"  # if not registered
   # Yank:
   pip run twine yank hephaistos 0.1.0 --repository pypi
   ```

2. **Delete the GitHub Release** (if needed):
   ```bash
   gh release delete v0.1.0 --yes
   ```

3. **Fix forward** — create a new version with the fix and tag it:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

4. **Communicate** — note the rollback in the release discussion or issue tracker.

## Where to Check Deploy Impact

- **GitHub Deployments** — https://github.com/gildrb/hephaistos/deployments
- **GitHub Actions** — check the latest deploy/release workflow run
- **Published package** — verify the expected wheel and sdist exist on the GitHub release and PyPI

## Prevention

- Always test on edge before cutting a stable release
- Use `--profile` and `--profile-memory` flags during QA
- Keep a small smoke-test checklist for install, armory init, and chat startup
