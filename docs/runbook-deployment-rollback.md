# Deployment Rollback

When a release or edge deploy causes problems, follow these steps to
revert and restore service.

## Edge Deploy (manual workflow)

Edge deploys are published only when `.github/workflows/deploy.yml` is run
manually. Routine pushes to `main` do not create a new edge deployment or
refresh the rolling edge prerelease.

### Rollback Steps

1. **Identify the bad commit** - check the [edge release](https://github.com/gildrb/heph/releases/tag/edge)
   for the commit SHA.

2. **Revert the commit** on `main`:
   ```bash
   git revert <sha>
   git push origin main
   ```
   If you want the reverted state available on edge, run the Deploy workflow
   manually and target `main` (or the specific ref you want to publish).

3. **Verify** - check the new edge release and confirm the app works.

4. **Monitor** - do a quick stress test with `heph --version` plus a basic
   armory command.

## PyPI Release (version tags)

Stable releases are published to PyPI from a reviewed `v*` tag reachable from
protected `main`. See [Stable Release](runbook-stable-release.md) for the full
trusted-publishing workflow.
The official stable pointer lives in
`packages/heph/src/heph/state/release.toml`; update it only when a reviewed
version is ready to become the public `heph@latest` release.

The public beta train starts at `v0.0.49`; `v0.0.58` supersedes that first
upload with the complete bundled package data. Keep beta fixes on `0.0.x` until
the first stable public train is ready, then move the stable pointer to
`v0.1.0`. Later `0.1.x` fixes can climb toward `0.1.49` before the next larger
`v0.2.0` train.

Before publishing, run from `main` with the release tag fetched. The release
workflow verifies package inputs still match the stable tag before it injects
runtime release metadata:

```bash
uv run python -m scripts.check_release_state --current-version-must-match-stable --require-tag
uv run python -m scripts.build_release_artifacts
uv run python -m scripts.release_stress_test --expect-runtime-channel pypi --expect-runtime-version v0.0.58
```

Publish by pushing the reviewed tag. The release workflow uploads through PyPI
Trusted Publishing, verifies the public install paths, and creates the GitHub
Release:

```bash
git push origin main
git push origin v0.0.58
```

### Rollback Steps

1. **Yank the release from PyPI** (prevents new installs):
   ```bash
   uvx twine yank heph 0.0.58 --repository pypi
   ```

2. **Delete the GitHub Release** (if needed):
   ```bash
   gh release delete v0.0.58 --yes
   ```

3. **Fix forward** - create a new version with the fix, tag it, and publish the
   new tag:
   ```bash
   git tag v0.0.58
   git push origin v0.0.58
   ```

4. **Communicate** - note the rollback in the release discussion or issue tracker.

## Where to Check Deploy Impact

- **GitHub Deployments** - https://github.com/gildrb/heph/deployments
- **Published package** - verify the expected wheel and sdist exist on the GitHub release and PyPI

## Prevention

- Always test on edge before cutting a stable release
- Keep edge publishes explicit so routine `main` pushes do not create deployment noise
- Use `--profile` and `--profile-memory` flags during QA
- Keep a small stress-test checklist for install, armory init, and chat startup
