from __future__ import annotations

from hephaistos.agent.persona import DEFAULT, TUTOR, get_persona, list_personas, resolve_persona


def test_get_persona_returns_registered_persona_or_none() -> None:
    assert get_persona("drill") is DEFAULT
    assert get_persona("missing") is None


def test_list_personas_keeps_default_first() -> None:
    personas = list_personas()

    assert personas[0] is DEFAULT
    assert {persona.slug for persona in personas} >= {
        "drill",
        "tutor",
        "examiner",
        "summarizer",
        "debater",
    }


def test_resolve_persona_falls_back_to_default() -> None:
    assert resolve_persona(None) is DEFAULT
    assert resolve_persona("missing") is DEFAULT
    assert resolve_persona("tutor") is TUTOR
