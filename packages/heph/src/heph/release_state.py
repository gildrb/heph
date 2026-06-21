from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata, resources
from pathlib import Path
from typing import TypedDict, cast

from hephaion.privacy import release as privacy_release


class OfficialReleasePayload(TypedDict):
    package: str
    command: str
    channel: str
    version: str
    tag: str
    release_workflow: str
    edge_workflow: str


class RuntimeReleaseState(TypedDict):
    channel: str
    version: str
    python: str
    module: str


class CurrentReleaseState(TypedDict):
    package_version: str
    official: OfficialReleasePayload
    runtime: RuntimeReleaseState


@dataclass(frozen=True, slots=True)
class OfficialRelease:
    package: str
    command: str
    channel: str
    version: str
    tag: str
    release_workflow: str
    edge_workflow: str

    def to_dict(self) -> OfficialReleasePayload:
        return {
            "package": self.package,
            "command": self.command,
            "channel": self.channel,
            "version": self.version,
            "tag": self.tag,
            "release_workflow": self.release_workflow,
            "edge_workflow": self.edge_workflow,
        }


def official_release() -> OfficialRelease:
    data = cast("dict[str, object]", tomllib.loads(_release_manifest_text()))
    return OfficialRelease(
        package=_required_string(data, "package"),
        command=_required_string(data, "command"),
        channel=_required_string(data, "channel"),
        version=_required_string(data, "version"),
        tag=_required_string(data, "tag"),
        release_workflow=_required_string(data, "release_workflow"),
        edge_workflow=_required_string(data, "edge_workflow"),
    )


def current_release_state() -> CurrentReleaseState:
    official = official_release()
    release_config = _release_config()
    return {
        "package_version": _metadata_version(official.package),
        "official": official.to_dict(),
        "runtime": {
            "channel": _release_config_value(release_config, "RELEASE_CHANNEL") or "source",
            "version": _release_config_value(release_config, "RELEASE_VERSION") or "",
            "python": sys.executable,
            "module": str(Path(__file__).resolve()),
        },
    }


def format_current_release_state() -> str:
    state = current_release_state()
    official = official_release()
    runtime = state["runtime"]
    runtime_version = runtime["version"] or "(not injected)"
    lines = [
        "Heph release state",
        f"  package version: {state['package_version']}",
        f"  official stable: {official.tag} ({official.version})",
        f"  release channel: {runtime['channel']}",
        f"  release version: {runtime_version}",
        f"  python: {runtime['python']}",
        f"  module: {runtime['module']}",
        f"  release workflow: {official.release_workflow}",
        f"  edge workflow: {official.edge_workflow}",
    ]
    return "\n".join(lines)


def _release_manifest_text() -> str:
    manifest = resources.files("heph").joinpath("state", "release.toml")
    return manifest.read_text(encoding="utf-8")


def _required_string(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"release manifest field {key!r} must be a non-empty string")
    return value


def _metadata_version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "0.0.50"


def _release_config() -> object:
    return privacy_release


def _release_config_value(release_config: object, name: str) -> str:
    value = getattr(release_config, name, None)
    return value if isinstance(value, str) else ""
