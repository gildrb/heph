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

4. **Monitor** — watch Sentry for new errors and the deploy webhook for
   confirmation.

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

4. **Notify** — post to the deploy webhook channel about the rollback.

## Where to Check Deploy Impact

- **Sentry Releases** — filter errors by `hephaistos@{version}` release tag
- **GitHub Deployments** — https://github.com/gildrb/hephaistos/deployments
- **GitHub Actions** — check the latest deploy/release workflow run
- **Deploy webhook** — if `DEPLOY_WEBHOOK_URL` is configured, deploy notifications include version and commit SHA

## Prevention

- Always test on edge before cutting a stable release
- Use `--profile` and `--profile-memory` flags during QA
- Monitor Sentry error rate after each deploy
