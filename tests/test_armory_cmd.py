from __future__ import annotations

from pathlib import Path

import pytest

from hephaistos.armory.service import init_armory, open_armory
from hephaistos.armory.storage import ArmoryValidationError


def test_init_armory_returns_success_message(tmp_path: Path) -> None:
    armory_path = tmp_path / "study-armory"

    message = init_armory(str(armory_path))

    assert "Initialized armory at" in message
    assert str(armory_path.resolve()) in message


def test_open_armory_returns_success_message(tmp_path: Path) -> None:
    armory_path = tmp_path / "study-armory"
    init_armory(str(armory_path))

    message = open_armory(str(armory_path))

    assert "Opened armory" in message
    assert str(armory_path.resolve()) in message


def test_open_armory_fails_for_uninitialized_path(tmp_path: Path) -> None:
    uninitialized = tmp_path / "not-initialized"
    uninitialized.mkdir(parents=True)

    with pytest.raises(ArmoryValidationError):
        open_armory(str(uninitialized))
