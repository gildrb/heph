from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path
from re import escape

import pytest

from scripts import check_release_artifacts


def test_check_release_artifacts_accepts_expected_wheel_and_sdist(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _write_wheel(dist / "heph-0.0.58-py3-none-any.whl")
    _write_sdist(dist / "heph-0.0.58.tar.gz")

    assert check_release_artifacts.main_with_args(["--dist", str(dist)]) == 0


def test_check_release_artifacts_rejects_internal_workspace_dependency(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _write_wheel(
        dist / "heph-0.0.58-py3-none-any.whl",
        requires_dist=("harness==0.0.58",),
    )
    _write_sdist(dist / "heph-0.0.58.tar.gz")

    with pytest.raises(SystemExit, match="internal distribution"):
        check_release_artifacts.main_with_args(["--dist", str(dist)])


def test_check_release_artifacts_rejects_missing_package_data(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _write_wheel(
        dist / "heph-0.0.58-py3-none-any.whl",
        members=check_release_artifacts.EXPECTED_WHEEL_MEMBERS
        - {"harness/parameters/default.toml"},
    )
    _write_sdist(dist / "heph-0.0.58.tar.gz")

    with pytest.raises(SystemExit, match=escape("harness/parameters/default.toml")):
        check_release_artifacts.main_with_args(["--dist", str(dist)])


def _write_wheel(
    path: Path,
    *,
    members: frozenset[str] = check_release_artifacts.EXPECTED_WHEEL_MEMBERS,
    requires_dist: tuple[str, ...] = ("rich==14.3.3",),
) -> None:
    metadata_lines = ["Name: heph", "Version: 0.0.58"]
    metadata_lines.extend(f"Requires-Dist: {requirement}" for requirement in requires_dist)
    metadata = "\n".join(metadata_lines) + "\n"
    with zipfile.ZipFile(path, "w") as wheel:
        for member in members:
            wheel.writestr(member, "")
        wheel.writestr("heph-0.0.58.dist-info/METADATA", metadata)
        wheel.writestr(
            "heph-0.0.58.dist-info/entry_points.txt",
            "[console_scripts]\nheph = heph.cli.main:main\n",
        )


def _write_sdist(path: Path) -> None:
    with tarfile.open(path, "w:gz") as sdist:
        for suffix in (
            "LICENSE",
            "pyproject.toml",
            "src/ai/py.typed",
            "src/extensions/py.typed",
            "src/heph/__init__.py",
            "src/heph/py.typed",
            "src/heph/state/release.toml",
            "src/harness/parameters/default.toml",
            "src/harness/py.typed",
            "src/interfaces/py.typed",
        ):
            source = path.parent / suffix.replace("/", "_")
            source.write_text("", encoding="utf-8")
            sdist.add(source, arcname=f"heph-0.0.58/{suffix}")
