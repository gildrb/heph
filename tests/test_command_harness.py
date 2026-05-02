from __future__ import annotations

from hephaistos.app.command_harness import parse_slash_command


def test_parse_slash_command_defaults_bare_slash_to_help() -> None:
    invocation = parse_slash_command("/")

    assert invocation.raw == "/"
    assert invocation.name == "help"
    assert invocation.args == ""


def test_parse_slash_command_splits_name_and_args() -> None:
    invocation = parse_slash_command("/resume abc123")

    assert invocation.raw == "/resume abc123"
    assert invocation.name == "resume"
    assert invocation.args == "abc123"


def test_parse_slash_command_normalizes_name_only() -> None:
    invocation = parse_slash_command("/MODELS gpt")

    assert invocation.name == "models"
    assert invocation.args == "gpt"
