"""Stress-test built release artifacts in an isolated environment."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from collections.abc import Collection
from pathlib import Path

from scripts.check_dependency_sdist_allowlist import allowed_source_only_package_names

EXPECTED_DISTRIBUTIONS = frozenset(
    {"heph", "heph_ai", "heph_extensions", "heph_interfaces", "hephaion"}
)


def main() -> int:
    args = _build_parser().parse_args()
    wheels = _release_artifacts(args.dist, suffix=".whl")
    sdists = _release_artifacts(args.dist, suffix=".tar.gz")
    with tempfile.TemporaryDirectory(prefix="heph-release-stress-", dir=Path.cwd()) as temp_dir:
        work_dir = Path(temp_dir)
        venv = work_dir / "venv"
        _run(["uv", "venv", str(venv), "--python", args.python], cwd=work_dir)
        python = _venv_python(venv)
        _run(_wheel_install_command(python, wheels.values()), cwd=work_dir)
        _run([str(_venv_executable(venv, "heph")), "--version"], cwd=work_dir)
        for name, sdist in sdists.items():
            _run(
                [
                    "uv",
                    "build",
                    "--wheel",
                    "--build-constraints",
                    str(args.build_constraints.resolve()),
                    "--require-hashes",
                    "--out-dir",
                    str(work_dir / "sdist-wheel" / name),
                    str(sdist),
                ],
                cwd=work_dir,
            )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--build-constraints", type=Path, default=Path("build-constraints.txt"))
    parser.add_argument("--python", default="3.13")
    return parser


def _wheel_install_command(python: Path, wheels: Collection[Path]) -> list[str]:
    no_binary = ",".join(allowed_source_only_package_names())
    return [
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        "--only-binary",
        ":all:",
        "--no-binary",
        no_binary,
        *(str(wheel) for wheel in wheels),
    ]


def _release_artifacts(dist: Path, *, suffix: str) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for path in sorted(dist.glob(f"*{suffix}")):
        distribution = _distribution_name(path, suffix=suffix)
        if distribution in artifacts:
            raise SystemExit(f"duplicate {distribution} artifact in {dist}")
        artifacts[distribution] = path.resolve()
    missing = sorted(EXPECTED_DISTRIBUTIONS - artifacts.keys())
    extra = sorted(artifacts.keys() - EXPECTED_DISTRIBUTIONS)
    if missing or extra:
        raise SystemExit(
            f"unexpected {suffix} artifacts in {dist}: missing={missing}, extra={extra}"
        )
    return artifacts


def _distribution_name(path: Path, *, suffix: str) -> str:
    stem = path.name.removesuffix(suffix)
    if suffix == ".whl":
        return stem.split("-", maxsplit=1)[0]
    return stem.rsplit("-", maxsplit=1)[0]


def _venv_python(venv: Path) -> Path:
    return _venv_executable(venv, "python")


def _venv_executable(venv: Path, name: str) -> Path:
    posix = venv / "bin" / name
    if posix.exists():
        return posix
    windows = venv / "Scripts" / f"{name}.exe"
    if windows.exists():
        return windows
    raise SystemExit(f"{name} not found in {venv}")


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
