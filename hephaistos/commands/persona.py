"""Persona management command."""

from __future__ import annotations

from hephaistos.agent.persona import get_persona, list_personas
from hephaistos.chat.session import replace_system_prompt
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.terminal import MenuOption, select_option
from hephaistos.terminal_display import print_error, print_info, print_success


class PersonaCommand(Command):
    name = "persona"
    description = "Show or switch the agent persona"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        slug = args.strip().lower()

        if slug:
            persona = get_persona(slug)
            if persona is None:
                available = ", ".join(p.slug for p in list_personas())
                print_error(f"Unknown persona: {slug}")
                print_info(f"Available: {available}")
                return CommandResult()
            old_name = s.persona.display_name
            s.persona = persona
            replace_system_prompt(s)
            s.dirty = True
            print_success(f"Persona: {old_name} -> {persona.display_name}")
            return CommandResult()

        personas = list_personas()
        options = [
            MenuOption(
                p.display_name,
                f"{p.description} {'← current' if p.slug == s.persona.slug else ''}".strip(),
                is_current=(p.slug == s.persona.slug),
            )
            for p in personas
        ]

        selected = select_option("Persona", options)
        if selected is None:
            return CommandResult()

        persona = personas[selected]
        old_name = s.persona.display_name
        s.persona = persona
        replace_system_prompt(s)
        s.dirty = True
        print_success(f"Persona: {old_name} -> {persona.display_name}")
        return CommandResult()
