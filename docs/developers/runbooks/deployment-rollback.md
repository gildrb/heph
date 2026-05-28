# Deployment Rollback

When a release or edge deploy causes problems, follow these steps to
revert and restore service.

## Edge Deploy (manual workflow)

Edge deploys are published only when `.github/workflows/deploy.yml` is run
manually. Routine pushes to `main` do not create a new edge deployment or
refresh the rolling edge prerelease.

### Rollback Steps

1. **Identify the bad commit** — check the [edge release](https://github.com/gildrb/heph/releases/tag/edge)
   for the commit SHA.

2. **Revert the commit** on `main`:
   ```bash
   git revert <sha>
   git push origin main
   ```
   If you want the reverted state available on edge, run the Deploy workflow
   manually and target `main` (or the specific ref you want to publish).

3. **Verify** — check the new edge release and confirm the app works.

4. **Monitor** — watch the follow-up GitHub Actions run and do a quick smoke test
   with `heph --version` plus a basic armory command.

## PyPI Release (version tags)

Stable releases are published to PyPI by manually dispatching
`.github/workflows/release.yml` from protected `main` for a reviewed `v*` tag.

### Rollback Steps

1. **Yank the release from PyPI** (prevents new installs):
   ```bash
   pip install twine
   twine register --repository pypi "heph==0.1.0"  # if not registered
   # Yank:
   pip run twine yank heph 0.1.0 --repository pypi
   ```

2. **Delete the GitHub Release** (if needed):
   ```bash
   gh release delete v0.1.0 --yes
   ```

3. **Fix forward** — create a new version with the fix, tag it, and dispatch the
   release workflow from `main` with that tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

4. **Communicate** — note the rollback in the release discussion or issue tracker.

## Where to Check Deploy Impact

- **GitHub Deployments** — https://github.com/gildrb/heph/deployments
- **GitHub Actions** — check the latest deploy/release workflow run
- **Published package** — verify the expected wheel and sdist exist on the GitHub release and PyPI

## Prevention

- Always test on edge before cutting a stable release
- Keep edge publishes explicit so routine `main` pushes do not create deployment noise
- Use `--profile` and `--profile-memory` flags during QA
- Keep a small smoke-test checklist for install, armory init, and chat startup
