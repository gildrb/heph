"""Stress-test built release artifacts in an isolated environment."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from collections.abc import Collection, Mapping
from pathlib import Path

from hephaion._types import is_string_mapping

from scripts.check_dependency_sdist_allowlist import allowed_source_only_package_names

EXPECTED_DISTRIBUTIONS = frozenset({"heph"})
EXPECTED_PACKAGE_NAMES = ("heph",)
DEFAULT_WORK_ROOT = Path(".artifacts") / "release-stress"
SUPPORTED_RELEASE_PLATFORMS = (
    "x86_64-pc-windows-msvc",
    "x86_64-manylinux_2_28",
    "aarch64-apple-darwin",
)
_SDK_IMPORT_SMOKE = """
from __future__ import annotations

from importlib import resources

import heph.sdk as sdk

capabilities = sdk.get_sdk_capabilities()
assert capabilities.version == sdk.SDK_CAPABILITIES_VERSION
assert sdk.validate_sdk_capabilities(capabilities) == ()
assert resources.files("heph").joinpath("py.typed").is_file()
assert resources.files("heph").joinpath("state", "release.toml").is_file()
assert resources.files("hephaion").joinpath("parameters", "default.toml").is_file()
assert resources.files("ai").joinpath("py.typed").is_file()
assert resources.files("extensions").joinpath("py.typed").is_file()
assert resources.files("interfaces").joinpath("py.typed").is_file()
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
    version = _artifact_version(wheels["heph"], suffix=".whl")
    scratch_root = args.work_root
    scratch_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-", dir=scratch_root) as temp_dir:
        work_dir = Path(temp_dir)
        venv = work_dir / "venv"
        _run(["uv", "venv", str(venv), "--python", args.python], cwd=work_dir)
        python = _venv_python(venv)
        _run(_wheel_install_command(python, wheels.values()), cwd=work_dir)
        heph = _venv_executable(venv, "heph")
        _stress_heph_executable(
            heph,
            expected_version=version,
            expected_runtime_channel=args.expect_runtime_channel,
            expected_runtime_version=args.expect_runtime_version,
            cwd=work_dir,
        )
        _stress_installed_sdk(python, heph, cwd=work_dir)
        _stress_uv_tool_install(
            args.dist.resolve(),
            version,
            args.python,
            work_dir,
            expected_runtime_channel=args.expect_runtime_channel,
            expected_runtime_version=args.expect_runtime_version,
        )
        _stress_cross_platform_resolution(args.dist.resolve(), version, work_dir)
        _stress_pip_install(
            args.dist.resolve(),
            version,
            args.python,
            work_dir,
            expected_runtime_channel=args.expect_runtime_channel,
            expected_runtime_version=args.expect_runtime_version,
        )
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
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    parser.add_argument("--expect-runtime-channel")
    parser.add_argument("--expect-runtime-version")
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


def _uv_tool_install_command(dist: Path, version: str, python: str) -> list[str]:
    return [
        "uv",
        "tool",
        "install",
        "--force",
        "--python",
        python,
        "--find-links",
        str(dist),
        "--no-sources",
        *_refresh_package_args(),
        f"heph=={version}",
    ]


def _pip_install_command(python: Path, dist: Path, version: str) -> list[str]:
    return [
        str(python),
        "-m",
        "pip",
        "install",
        "--find-links",
        str(dist),
        f"heph=={version}",
    ]


def _pip_compile_command(
    requirements: Path,
    dist: Path,
    platform: str,
    output_file: Path,
) -> list[str]:
    return [
        "uv",
        "--quiet",
        "pip",
        "compile",
        str(requirements),
        "--find-links",
        str(dist),
        "--no-sources",
        "--python-platform",
        platform,
        "--output-file",
        str(output_file),
    ]


def _refresh_package_args() -> list[str]:
    args: list[str] = []
    for package in EXPECTED_PACKAGE_NAMES:
        args.extend(("--refresh-package", package))
    return args


def _stress_uv_tool_install(
    dist: Path,
    version: str,
    python: str,
    work_dir: Path,
    *,
    expected_runtime_channel: str | None = None,
    expected_runtime_version: str | None = None,
) -> None:
    tool_dir = work_dir / "uv-tools"
    tool_bin = work_dir / "uv-tool-bin"
    tool_bin.mkdir()
    env = _isolated_uv_tool_env(tool_dir, tool_bin)
    _run(_uv_tool_install_command(dist, version, python), cwd=work_dir, env=env)
    heph = _tool_executable(tool_bin, "heph")
    _stress_heph_executable(
        heph,
        expected_version=version,
        expected_runtime_channel=expected_runtime_channel,
        expected_runtime_version=expected_runtime_version,
        cwd=work_dir,
        env=env,
    )


def _stress_cross_platform_resolution(dist: Path, version: str, work_dir: Path) -> None:
    requirements = work_dir / "heph-release.in"
    requirements.write_text(f"heph=={version}\n", encoding="utf-8")
    for platform in SUPPORTED_RELEASE_PLATFORMS:
        _run(
            _pip_compile_command(
                requirements,
                dist,
                platform,
                work_dir / f"heph-release-{platform}.txt",
            ),
            cwd=work_dir,
        )


def _stress_pip_install(
    dist: Path,
    version: str,
    python: str,
    work_dir: Path,
    *,
    expected_runtime_channel: str | None = None,
    expected_runtime_version: str | None = None,
) -> None:
    venv = work_dir / "pip-venv"
    _run(["uv", "venv", str(venv), "--python", python, "--seed"], cwd=work_dir)
    venv_python = _venv_python(venv)
    _run(_pip_install_command(venv_python, dist, version), cwd=work_dir)
    _run([str(venv_python), "-m", "pip", "check"], cwd=work_dir)
    heph = _venv_executable(venv, "heph")
    _stress_heph_executable(
        heph,
        expected_version=version,
        expected_runtime_channel=expected_runtime_channel,
        expected_runtime_version=expected_runtime_version,
        cwd=work_dir,
    )


def _stress_installed_sdk(python: Path, heph: Path, *, cwd: Path) -> None:
    _run([str(python), "-c", _SDK_IMPORT_SMOKE], cwd=cwd)
    raw_capabilities = _run_output([str(heph), "sdk", "capabilities"], cwd=cwd)
    try:
        payload: object = json.loads(raw_capabilities)
    except json.JSONDecodeError as exc:
        raise SystemExit("heph sdk capabilities did not emit valid JSON") from exc
    _validate_sdk_capability_payload(payload)


def _stress_heph_executable(
    heph: Path,
    *,
    expected_version: str,
    expected_runtime_channel: str | None = None,
    expected_runtime_version: str | None = None,
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> None:
    version_output = _run_output([str(heph), "--version"], cwd=cwd, env=env).strip()
    if version_output != f"heph {expected_version}":
        raise SystemExit(f"heph --version returned {version_output!r}")
    raw_release_state = _run_output([str(heph), "release", "status", "--json"], cwd=cwd, env=env)
    try:
        payload: object = json.loads(raw_release_state)
    except json.JSONDecodeError as exc:
        raise SystemExit("heph release status --json did not emit valid JSON") from exc
    _validate_release_state_payload(
        payload,
        expected_version=expected_version,
        expected_runtime_channel=expected_runtime_channel,
        expected_runtime_version=expected_runtime_version,
    )


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


def _validate_release_state_payload(
    payload: object,
    *,
    expected_version: str,
    expected_runtime_channel: str | None = None,
    expected_runtime_version: str | None = None,
) -> None:
    if not is_string_mapping(payload):
        raise SystemExit("heph release status did not return a JSON object")
    if payload.get("package_version") != expected_version:
        raise SystemExit("heph release status returned the wrong package version")
    official = payload.get("official")
    if not is_string_mapping(official):
        raise SystemExit("heph release status returned no official release object")
    if official.get("package") != "heph":
        raise SystemExit("heph release status returned the wrong package name")
    if official.get("command") != "heph":
        raise SystemExit("heph release status returned the wrong command name")
    if official.get("version") != expected_version:
        raise SystemExit("heph release status returned the wrong official version")
    if official.get("tag") != f"v{expected_version}":
        raise SystemExit("heph release status returned the wrong official tag")
    runtime = payload.get("runtime")
    if not is_string_mapping(runtime):
        raise SystemExit("heph release status returned no runtime object")
    if expected_runtime_channel is not None and runtime.get("channel") != expected_runtime_channel:
        raise SystemExit("heph release status returned the wrong runtime channel")
    if expected_runtime_version is not None and runtime.get("version") != expected_runtime_version:
        raise SystemExit("heph release status returned the wrong runtime version")
    if not runtime.get("python"):
        raise SystemExit("heph release status returned no Python executable")


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


def _artifact_version(path: Path, *, suffix: str) -> str:
    stem = path.name.removesuffix(suffix)
    if suffix == ".whl":
        parts = stem.split("-")
        if len(parts) < 2:
            raise SystemExit(f"cannot parse wheel version from {path.name}")
        return parts[1]
    parts = stem.rsplit("-", maxsplit=1)
    if len(parts) != 2:
        raise SystemExit(f"cannot parse sdist version from {path.name}")
    return parts[1]


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


def _tool_executable(tool_bin: Path, name: str) -> Path:
    posix = tool_bin / name
    if posix.exists():
        return posix
    windows = tool_bin / f"{name}.exe"
    if windows.exists():
        return windows
    raise SystemExit(f"{name} not found in {tool_bin}")


def _isolated_uv_tool_env(tool_dir: Path, tool_bin: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["UV_TOOL_DIR"] = str(tool_dir)
    env["UV_TOOL_BIN_DIR"] = str(tool_bin)
    return env


def _run(command: list[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _run_output(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


if __name__ == "__main__":
    raise SystemExit(main())
