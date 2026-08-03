"""Verify that the default workspace environment stays lean and usable."""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

_MAX_DISTRIBUTIONS = 45
_DENYLIST = (
    "torch",
    "torchvision",
    "triton",
    "nvidia-",
    "cuda-",
    "transformers",
    "accelerate",
    "opencv-python",
    "rapidocr",
    "scipy",
    "pandas",
    "scikit-learn",
    "sentence-transformers",
    "docling",
    "tree-sitter",
    "numpy",
    "pillow",
    "lxml",
    "python-docx",
    "python-pptx",
    "openpyxl",
    "huggingface-hub",
    "safetensors",
    "tokenizers",
    "regex",
    "sympy",
    "networkx",
    "jinja2",
    "requests",
    "urllib3",
)
_UV = shlex.split(os.environ.get("HEPH_UV", "uv"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="heph-lean-profile-") as temporary:
        environment = Path(temporary) / "venv"
        env = os.environ.copy()
        env["UV_PROJECT_ENVIRONMENT"] = str(environment)
        _run([*_UV, "venv", "--python", "3.13", str(environment)], env=env)
        _run(
            [
                *_UV,
                "sync",
                "--frozen",
                "--no-dev",
            ],
            env=env,
        )
        python = environment / "bin" / "python"
        _run([str(environment / "bin" / "heph"), "--version"], env=env)
        _run([str(environment / "bin" / "heph"), "--help"], env=env)
        _check_distributions(python)
        _run_smoke_check(python, temporary)
    return 0


def _check_distributions(python: Path) -> None:
    code = (
        "import importlib.metadata as m; "
        "print('\\n'.join(sorted(d.metadata['Name'] for d in m.distributions() "
        "if d.metadata.get('Name'))))"
    )
    result = subprocess.run([str(python), "-c", code], check=True, text=True, capture_output=True)
    names = [line.strip().lower() for line in result.stdout.splitlines() if line.strip()]
    offending = [
        name
        for name in names
        if any(name == denied or name.startswith(denied) for denied in _DENYLIST)
    ]
    if offending:
        raise RuntimeError(
            "Lean profile contains denied distributions: "
            + ", ".join(offending)
            + ". Inspect uv.lock dependency paths and move the responsible requirement "
            "from the default dependency graph."
        )
    if len(names) > _MAX_DISTRIBUTIONS:
        raise RuntimeError(
            f"Lean profile contains {len(names)} distributions; cap is {_MAX_DISTRIBUTIONS}. "
            "Inspect uv.lock dependency paths for new default dependencies."
        )
    print(f"Lean profile: {len(names)} distributions (cap {_MAX_DISTRIBUTIONS})")


def _run_smoke_check(python: Path, temporary: str) -> None:
    armory = Path(temporary) / "armory" / "materials"
    armory.mkdir(parents=True)
    (armory / "alpha.md").write_text(
        "# Alpha\n\nThe amber comet protocol uses a green battery.\n",
        encoding="utf-8",
    )
    (armory / "beta.md").write_text(
        "# Beta\n\nThis unrelated note discusses cooking.\n",
        encoding="utf-8",
    )
    code = """
from pathlib import Path
from harness.rag.index import ArmoryIndex
from harness.rag.retrieve import retrieve

root = Path(__import__("sys").argv[1])
index = ArmoryIndex(root)
index.build()
results = retrieve("amber comet protocol", index, top_k=1)
assert index.documents and results and results[0].chunk.source.endswith("alpha.md")
"""
    _run([str(python), "-c", code, str(armory.parent)])
    print("Lean profile smoke check: passed")


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("$", " ".join(command))
    subprocess.run(command, check=True, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
