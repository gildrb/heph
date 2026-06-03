"""Stress-test built release artifacts in an isolated environment."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    args = _build_parser().parse_args()
    wheel = _single_wheel(args.dist)
    sdist = _single_sdist(args.dist)
    with tempfile.TemporaryDirectory(prefix="heph-release-stress-", dir=Path.cwd()) as temp_dir:
        work_dir = Path(temp_dir)
        venv = work_dir / "venv"
        _run(["uv", "venv", str(venv), "--python", args.python], cwd=work_dir)
        python = _venv_python(venv)
        _run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--only-binary",
                ":all:",
                "--no-binary",
                "antlr4-python3-runtime,pylatexenc,unicodeit",
                str(wheel),
            ],
            cwd=work_dir,
        )
        _run([str(_venv_executable(venv, "heph")), "--version"], cwd=work_dir)
        _run(
            [
                "uv",
                "build",
                "--wheel",
                "--build-constraints",
                str(args.build_constraints.resolve()),
                "--require-hashes",
                "--out-dir",
                str(work_dir / "sdist-wheel"),
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


def _single_wheel(dist: Path) -> Path:
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one wheel in {dist}, found {len(wheels)}")
    return wheels[0].resolve()


def _single_sdist(dist: Path) -> Path:
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(sdists) != 1:
        raise SystemExit(f"expected exactly one sdist in {dist}, found {len(sdists)}")
    return sdists[0].resolve()


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
