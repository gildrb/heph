"""Stress-test built release artifacts in an isolated environment."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from collections.abc import Collection
from pathlib import Path

from hephaion._types import is_string_mapping

from scripts.check_dependency_sdist_allowlist import allowed_source_only_package_names

EXPECTED_DISTRIBUTIONS = frozenset(
    {"heph", "heph_ai", "heph_extensions", "heph_interfaces", "hephaion"}
)
_SDK_IMPORT_SMOKE = """
from __future__ import annotations

from importlib import resources

import heph.sdk as sdk

capabilities = sdk.get_sdk_capabilities()
assert capabilities.version == sdk.SDK_CAPABILITIES_VERSION
assert sdk.validate_sdk_capabilities(capabilities) == ()
assert resources.files("heph").joinpath("py.typed").is_file()
assert isinstance(sdk.__version__, str)
assert sdk.__version__
assert "HephService" in sdk.__all__
assert "JsonlSdkProcess" in sdk.__all__
ready = sdk.JsonlSdkReady(
    sdk.SDK_JSONL_PROTOCOL,
    sdk.SDK_JSONL_VERSION,
    {"version": sdk.SDK_CAPABILITIES_VERSION},
    {"service": {"is_busy": False}},
)
ready_payload = ready.to_dict()
assert ready_payload["type"] == "ready"
ready_payload["capabilities"]["version"] = 0
assert ready.to_dict()["capabilities"]["version"] == sdk.SDK_CAPABILITIES_VERSION
error_payload = sdk.JsonlSdkErrorPayload("sdk_error", "message", None).to_dict()
assert error_payload == {
    "code": "sdk_error",
    "message": "message",
    "unavailable_reason": None,
}
"""


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
        heph = _venv_executable(venv, "heph")
        _run([str(heph), "--version"], cwd=work_dir)
        _stress_installed_sdk(python, heph, cwd=work_dir)
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


def _stress_installed_sdk(python: Path, heph: Path, *, cwd: Path) -> None:
    _run([str(python), "-c", _SDK_IMPORT_SMOKE], cwd=cwd)
    raw_capabilities = _run_output([str(heph), "sdk", "capabilities"], cwd=cwd)
    try:
        payload: object = json.loads(raw_capabilities)
    except json.JSONDecodeError as exc:
        raise SystemExit("heph sdk capabilities did not emit valid JSON") from exc
    _validate_sdk_capability_payload(payload)


def _validate_sdk_capability_payload(payload: object) -> None:
    if not is_string_mapping(payload):
        raise SystemExit("heph sdk capabilities did not return a JSON object")
    version = payload.get("version")
    if not _is_json_integer(version):
        raise SystemExit("heph sdk capabilities returned a non-integer SDK version")
    jsonl = payload.get("jsonl")
    if not is_string_mapping(jsonl):
        raise SystemExit("heph sdk capabilities returned no JSONL contract")
    if jsonl.get("protocol") != "heph-sdk-jsonl":
        raise SystemExit("heph sdk capabilities returned an unexpected JSONL protocol")
    if not _is_json_integer(jsonl.get("version")):
        raise SystemExit("heph sdk capabilities returned a non-integer JSONL version")


def _is_json_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


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


def _run_output(command: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


if __name__ == "__main__":
    raise SystemExit(main())
