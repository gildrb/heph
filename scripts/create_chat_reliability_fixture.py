"""Create generic armories for the chat reliability gauntlet.

The generated materials are intentionally public and generic. They cover the
source areas used by ``scripts.run_chat_reliability_gauntlet`` without relying
on a private corpus, course vocabulary, or local paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from armory import storage

FIXTURE_MATERIALS_DIR = "chat-reliability-fixture"
DEFAULT_SEED_PREFIX = "fixture-seed"


class FixtureArmoryReport(TypedDict):
    armory: str
    files: list[str]


class FixtureSuiteReport(TypedDict):
    root: str
    count: int
    armories: list[FixtureArmoryReport]


@dataclass(frozen=True, slots=True)
class FixtureMaterial:
    filename: str
    title: str
    body: str


FIXTURE_MATERIALS: tuple[FixtureMaterial, ...] = (
    FixtureMaterial(
        filename="algorithms.md",
        title="Algorithms Source",
        body=(
            "Selection sort repeatedly chooses the smallest remaining item and places it "
            "next in the output position.\n\n"
            "The procedure separates the input into a sorted prefix and an unsorted suffix. "
            "A learner should track which comparison justifies each selected item.\n\n"
            "A useful limitation is that the simple version keeps scanning the unsorted suffix, "
            "so it is clear but not the fastest choice for large lists."
        ),
    ),
    FixtureMaterial(
        filename="calculus.md",
        title="Calculus Source",
        body=(
            "The product rule says that the derivative of a product depends on both factors: "
            "hold one factor steady, differentiate the other, and add the mirrored term.\n\n"
            "The rule follows from comparing the change in each factor separately. Practice "
            "requires naming which factor is being differentiated in each term.\n\n"
            "A common mistake is to differentiate both factors at once and forget the original "
            "factor that remains in each term."
        ),
    ),
    FixtureMaterial(
        filename="physics.md",
        title="Physics Source",
        body=(
            "A force vector can be decomposed into perpendicular components. The horizontal "
            "and vertical parts can then be reasoned about independently.\n\n"
            "The main concept is that the components are not extra forces; they are a more "
            "convenient representation of the same vector.\n\n"
            "In a diagram, label the angle before choosing sine or cosine so the formula "
            "matches the component being described."
        ),
    ),
    FixtureMaterial(
        filename="study-methods.md",
        title="Study Methods Source",
        body=(
            "Retrieval practice asks the learner to recall an answer before rereading the "
            "source. The point is to expose what can be remembered unaided.\n\n"
            "Good practice requires a feedback step: compare the recalled answer with the "
            "material, correct errors, and try again later.\n\n"
            "Spacing matters because a little forgetting makes the next recall attempt more "
            "diagnostic than immediate repetition."
        ),
    ),
    FixtureMaterial(
        filename="history.md",
        title="History Source",
        body=(
            "The public library example describes a city choosing longer opening hours after "
            "community groups asked for evening access.\n\n"
            "The supported claim is modest: the decision followed documented requests and a "
            "budget review, not a single dramatic event.\n\n"
            "The source distinguishes direct evidence from interpretation by naming meeting "
            "minutes as evidence and calling broader cultural impact an inference."
        ),
    ),
    FixtureMaterial(
        filename="exercises.md",
        title="Exercises Source",
        body=(
            "The exercise set asks learners to annotate each answer with the source sentence "
            "that supports it.\n\n"
            "One task asks for a two-step checklist: identify the claim, then match it to a "
            "specific evidence phrase.\n\n"
            "Another task asks the learner to write a counterexample or limitation when the "
            "material provides one."
        ),
    ),
    FixtureMaterial(
        filename="exams.md",
        title="Exam Source",
        body=(
            "The exam-style material expects short answers with citations. A complete answer "
            "names the source, states the claim, and explains the evidence in one sentence.\n\n"
            "One expected task is to compare two source areas without inventing facts that are "
            "not present in the materials.\n\n"
            "A second expected task is to mark unsupported claims as not found instead of "
            "guessing."
        ),
    ),
    FixtureMaterial(
        filename="formula-sheet.md",
        title="Formula Sheet Source",
        body=(
            "The slope formula measures change in output divided by change in input. Its role "
            "is to turn two points into a rate of change.\n\n"
            "The area formula for a rectangle multiplies base by height. Its role is to count "
            "equal rows of equal length.\n\n"
            "A formula should be explained by what each symbol represents before numbers are "
            "substituted."
        ),
    ),
    FixtureMaterial(
        filename="procedure.md",
        title="Procedure Source",
        body=(
            "The clearest procedure has three steps: read the source claim, locate the smallest "
            "supporting phrase, and cite that phrase.\n\n"
            "If no supporting phrase appears, the procedure says to report that the material "
            "does not contain the answer.\n\n"
            "This procedure is meant for grounded answers, not for open-ended speculation."
        ),
    ),
)


def create_fixture_armory(
    armory_path: Path,
    *,
    variant: str = "base",
    force: bool = False,
) -> tuple[Path, ...]:
    """Create or update one generic fixture armory and return written material paths."""
    resolved_armory = armory_path.expanduser().resolve()
    storage.initialize(resolved_armory)
    materials_dir = resolved_armory / storage.MATERIALS_DIR / FIXTURE_MATERIALS_DIR
    if materials_dir.exists() and not force:
        existing_files = [path for path in materials_dir.iterdir() if path.is_file()]
        if existing_files:
            message = (
                f"fixture materials already exist in {materials_dir}; "
                "pass force=True or --force to overwrite them"
            )
            raise FileExistsError(message)
    materials_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for material in FIXTURE_MATERIALS:
        target = materials_dir / material.filename
        target.write_text(_render_material(material, variant), encoding="utf-8")
        written.append(target)
    manifest = materials_dir / "fixture-manifest.md"
    manifest.write_text(_render_manifest(variant), encoding="utf-8")
    written.append(manifest)
    return tuple(written)


def create_fixture_armories(
    output_path: Path,
    *,
    count: int = 1,
    seed_prefix: str = DEFAULT_SEED_PREFIX,
    force: bool = False,
) -> FixtureSuiteReport:
    if count <= 0:
        raise ValueError("count must be positive")
    resolved_output = output_path.expanduser().resolve()
    armory_paths = _armory_paths(resolved_output, count=count, seed_prefix=seed_prefix)
    reports: list[FixtureArmoryReport] = []
    for index, armory_path in enumerate(armory_paths, start=1):
        variant = seed_prefix if count == 1 else f"{seed_prefix}-{index:02d}"
        files = create_fixture_armory(armory_path, variant=variant, force=force)
        reports.append(
            {
                "armory": str(armory_path),
                "files": [str(path.relative_to(armory_path)) for path in files],
            }
        )
    return {
        "root": str(resolved_output),
        "count": count,
        "armories": reports,
    }


def _armory_paths(output_path: Path, *, count: int, seed_prefix: str) -> tuple[Path, ...]:
    if count == 1:
        return (output_path,)
    return tuple(output_path / f"{seed_prefix}-{index:02d}" for index in range(1, count + 1))


def _render_material(material: FixtureMaterial, variant: str) -> str:
    return (
        f"# {material.title}\n\n"
        f"{material.body}\n\n"
        f"Fixture variant: {variant}. This line makes seeded armories distinct while keeping "
        "the corpus generic and public.\n"
    )


def _render_manifest(variant: str) -> str:
    filenames = "\n".join(f"- {material.filename}" for material in FIXTURE_MATERIALS)
    return (
        "# Chat Reliability Fixture Manifest\n\n"
        "This generated armory is for multi-turn chat reliability testing. It contains "
        "generic public materials for algorithms, calculus, physics, learning methods, "
        "history, exercises, exams, formulas, and grounded-answer procedure checks.\n\n"
        f"Variant: {variant}\n\n"
        "Materials:\n"
        f"{filenames}\n"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output armory path, or parent dir with --count")
    parser.add_argument("--count", type=int, default=1, help="Number of armories to create")
    parser.add_argument(
        "--seed-prefix",
        default=DEFAULT_SEED_PREFIX,
        help="Name prefix for seeded armories when --count is greater than 1",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite generated fixture materials if they already exist",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON creation report")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        report = create_fixture_armories(
            cast("Path", args.output),
            count=cast("int", args.count),
            seed_prefix=cast("str", args.seed_prefix),
            force=cast("bool", args.force),
        )
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"fixture creation error: {exc}", file=sys.stderr)
        return 2
    if cast("bool", args.json):
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)
    return 0


def _print_report(report: FixtureSuiteReport) -> None:
    print(f"created={report['count']}")
    for armory in report["armories"]:
        print(f"armory={armory['armory']} files={len(armory['files'])}")


if __name__ == "__main__":
    raise SystemExit(main())
