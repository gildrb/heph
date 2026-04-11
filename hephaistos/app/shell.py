"""Chat-first interactive shell with rich terminal UX.

Features:
- Slash commands with tab-autocomplete
- Shell mode via ! prefix
- Arrow-key history navigation
- Multi-line input with backslash continuation
- Streaming interrupt via Ctrl+C

All keybindings are configurable via ``DEFAULT_SHELL_KEYBINDINGS``.
"""

from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style as PtStyle

from hephaistos import __version__
from hephaistos.app.commands import get_registry
from hephaistos.app.display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    direct_input,
    print_error,
    print_info,
    print_shell_intro,
    print_success,
    styled,
)
from hephaistos.app.input_history import InputHistory
from hephaistos.app.keybindings import DEFAULT_SHELL_KEYBINDINGS
from hephaistos.app.menu import MenuOption, select_option
from hephaistos.app.palette import FORGE_ASH, FORGE_EMBER, FORGE_IRON, FORGE_PANEL, FORGE_SMOKE
from hephaistos.armory.storage import ArmoryError, initialize, normalize_path
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import ChatConfig, EngineError, StreamRecoveryError
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    list_armory_sessions,
    resume_session,
    save_session,
    send_user_message,
    session_has_messages,
    validate_armory_path,
)
from hephaistos.chat.usage import ContextBudget
from hephaistos.parameters.cli import load_config
from hephaistos.providers.config import ProviderConfig

ARMORY_MENU_OPTIONS = [
    MenuOption("Open existing armory", "Attach a workspace and load its study context."),
    MenuOption("Create new armory", "Initialize a new workspace and start chatting in it."),
    MenuOption("Detach armory", "Switch to plain chat without workspace tools."),
    MenuOption("Resume saved chat", "Pick a saved conversation from an armory."),
    MenuOption("List saved chats", "Show the saved sessions for an armory."),
    MenuOption("Cancel", "Return to the chat prompt."),
]

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"

_PT_STYLE = PtStyle.from_dict(
    {
        "armory": FORGE_ASH,
        "prompt-mark": f"bold {FORGE_EMBER}",
        "composer": f"bg:{FORGE_PANEL} fg:{FORGE_ASH}",
        "bottom-toolbar": f"noreverse fg:{FORGE_SMOKE}",
        "bottom-toolbar.text": f"noreverse fg:{FORGE_SMOKE}",
        "toolbar-location": f"noreverse fg:{FORGE_ASH}",
        "toolbar-accent": f"noreverse bold fg:{FORGE_ASH}",
        "toolbar-error": f"noreverse bold fg:{FORGE_IRON}",
        "completion-menu.completion.current": f"bg:{FORGE_EMBER} fg:{FORGE_ASH} bold",
        "completion-menu.completion": f"bg:{FORGE_PANEL} fg:{FORGE_ASH}",
        "completion-menu.meta.completion.current": f"bg:{FORGE_EMBER} fg:{FORGE_ASH}",
        "completion-menu.meta.completion": f"bg:{FORGE_PANEL} fg:{FORGE_SMOKE}",
        "scrollbar.background": f"bg:{FORGE_PANEL}",
        "scrollbar.button": f"bg:{FORGE_EMBER}",
    }
)


@dataclass
class ShellRuntime:
    busy: bool = False
    steering_count: int = 0
    abort_event: threading.Event = field(default_factory=threading.Event)
    worker: threading.Thread | None = None


class SlashCommandCompleter(Completer):
    """Context-aware completion for slash commands and their common arguments."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()

        if not stripped.startswith("/") or "\n" in stripped:
            return

        body = stripped[1:]
        registry = get_registry()

        if not body or " " not in body:
            prefix = body.lower()
            seen: set[str] = set()
            for cmd in registry.commands:
                if cmd.hidden:
                    continue
                matches_name = cmd.name.lower().startswith(prefix)
                matches_alias = any(alias.lower().startswith(prefix) for alias in cmd.aliases)
                if not (matches_name or matches_alias) or cmd.name in seen:
                    continue
                seen.add(cmd.name)
                yield Completion(
                    text=cmd.name + " ",
                    start_position=-len(body),
                    display_meta=cmd.description,
                )
            return

        parts = body.split()
        if not parts:
            return

        ends_with_space = stripped.endswith(" ")
        cmd_name = parts[0].lower()
        arg_parts = parts[1:]
        if ends_with_space:
            arg_parts.append("")

        for suggestion, description in self._argument_suggestions(cmd_name, arg_parts):
            current = arg_parts[-1] if arg_parts else ""
            if current and not suggestion.lower().startswith(current.lower()):
                continue
            suffix = "" if suggestion.endswith(" ") else " "
            yield Completion(
                text=suggestion + suffix,
                start_position=-len(current),
                display_meta=description,
            )

    def _argument_suggestions(
        self,
        cmd_name: str,
        arg_parts: list[str],
    ) -> list[tuple[str, str]]:
        if cmd_name == "api":
            if len(arg_parts) <= 1:
                return [
                    ("key", "Store an API key for the active provider"),
                    ("url", "Override the provider base URL"),
                ]
            return []

        if cmd_name == "provider":
            return self._provider_suggestions(arg_parts)

        if cmd_name == "model":
            return [(model, f"via {slug}") for slug, model in self._all_models()]

        if cmd_name == "persona":
            return self._persona_suggestions(arg_parts)

        return []

    def _provider_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) <= 1:
            return [
                ("use", "Switch active provider (and optional model)"),
                ("model", "Switch model within the active provider"),
            ]

        subcmd = arg_parts[0].lower()
        providers = ProviderConfig.load().providers

        if subcmd == "use":
            if len(arg_parts) == 2:
                return [(slug, provider.display_name) for slug, provider in providers.items()]
            if len(arg_parts) == 3:
                provider = providers.get(arg_parts[1].lower())
                if provider is None:
                    return []
                return [(model, provider.display_name) for model in provider.models]

        if subcmd == "model":
            active = ProviderConfig.load().get_active()
            if active is None:
                return []
            return [(model, active.display_name) for model in active.models]

        return []

    def _all_models(self) -> list[tuple[str, str]]:
        providers = ProviderConfig.load().providers
        models: list[tuple[str, str]] = []
        for slug, provider in providers.items():
            models.extend((slug, model) for model in provider.models)
        return models

    def _persona_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) > 1:
            return []
        from hephaistos.harness.persona import list_personas

        return [(p.slug, p.description) for p in list_personas()]


def _build_keybindings(
    keybindings: dict[str, str | list[str]],
) -> KeyBindings:
    """Build prompt_toolkit key bindings from a config dict."""
    kb = KeyBindings()
    submit_keys = keybindings["submit"]
    newline_keys = keybindings["newline"]

    submit_key_list = (
        [k.strip() for k in submit_keys.split(",")]
        if isinstance(submit_keys, str)
        else submit_keys
    )

    @kb.add(*submit_key_list)
    def _(event):
        buf = event.current_buffer
        line = buf.document.current_line_before_cursor
        if line.rstrip().endswith("\\"):
            stripped = line.rstrip()
            buf.delete_before_cursor(count=len(line) - len(stripped) + 1)
            buf.insert_text("\n")
            return
        if not buf.text.strip():
            return

        buf.validate_and_handle()

    newline_key_list = (
        [k.strip() for k in newline_keys.split(",")]
        if isinstance(newline_keys, str)
        else newline_keys
    )

    @kb.add(*newline_key_list)
    def _(event):
        """Insert a newline (e.g. Alt+Enter)."""
        event.current_buffer.insert_text("\n")

    return kb


def _get_prompt_message(runtime: ShellRuntime | None = None):
    """Return the compact composer prefix used for every prompt line."""

    def message():
        marker = "+ " if runtime is not None and runtime.busy else "> "
        return FormattedText([("class:prompt-mark", marker)])

    return message


def _get_prompt_continuation(width: int, line_number: int, wrap_count: int):
    """Indent wrapped and multi-line composer rows under the prompt mark."""
    _ = line_number, wrap_count
    return FormattedText([("class:bottom-toolbar", " " * width)])


def _display_path(path: Path) -> str:
    """Render a path relative to the user's home directory when possible."""
    resolved = path.expanduser().resolve()
    try:
        rel = resolved.relative_to(Path.home())
        return "~" if str(rel) == "." else f"~/{rel}"
    except ValueError:
        return str(resolved)


def _context_left(session: ChatSession) -> int:
    """Return the estimated prompt-budget percentage left for the session."""
    budget = ContextBudget(model=session.config.model, max_tokens=session.config.max_tokens)
    prompt_budget = max(1, budget.prompt_budget)
    remaining = budget.tokens_remaining(session.conversation.to_api_messages())  # type: ignore[arg-type]
    return max(0, min(100, round((remaining / prompt_budget) * 100)))


def _source_label(session: ChatSession) -> str:
    count = session.source_file_count
    if count <= 0:
        return "none"
    return f"{count} file{'s' if count != 1 else ''}"


def _build_bottom_toolbar_status(
    session: ChatSession,
    runtime: ShellRuntime | None = None,
) -> str:
    """Build the multi-line status block shown below the composer."""
    location = session.armory_path or Path.cwd()
    mode = "armory attached" if session.armory_path is not None else "plain chat"
    api_state = "configured" if session.config.resolved_api_key else "missing"
    persona_tag = session.persona.display_name if session.persona.slug != "drill" else ""
    if runtime is not None and runtime.busy:
        steering_suffix = f" · queued {runtime.steering_count}" if runtime.steering_count else ""
        input_hint = (
            f"assistant working · enter queues follow-up · ctrl+c interrupt{steering_suffix}"
        )
    else:
        input_hint = "enter send · alt+enter newline · / commands · ! shell"
    return (
        f"{_display_path(location)} · {mode}\n"
        f"model {session.config.model}"
        f" · context {_context_left(session)}% left"
        f" · api {api_state} · source {_source_label(session)}"
        f"{f' · persona {persona_tag}' if persona_tag else ''}\n"
        f"{input_hint}"
    )


def _refresh_bottom_toolbar(
    session: ChatSession,
    toolbar_ref: list[str],
    runtime: ShellRuntime | None = None,
) -> None:
    """Refresh the cached prompt_toolkit toolbar text for the active session."""
    toolbar_ref[0] = _build_bottom_toolbar_status(session, runtime)


def _get_bottom_toolbar(toolbar_ref: list[str]):
    """Return the cached metadata shown below the composer."""
    status = toolbar_ref[0]
    lines = status.splitlines()
    fragments: list[tuple[str, str]] = []
    if not lines:
        return FormattedText([])
    fragments.append(("class:toolbar-location", lines[0]))
    for line in lines[1:]:
        fragments.append(("", "\n"))
        if "api missing" in line:
            prefix, suffix = line.split("api missing", 1)
            fragments.append(("class:bottom-toolbar", prefix))
            fragments.append(("class:toolbar-error", "api missing"))
            fragments.append(("class:bottom-toolbar", suffix))
            continue
        if line.startswith("assistant working"):
            prefix, suffix = line.split("assistant working", 1)
            fragments.append(("class:bottom-toolbar", prefix))
            fragments.append(("class:toolbar-accent", "assistant working"))
            fragments.append(("class:bottom-toolbar", suffix))
            continue
        fragments.append(("class:bottom-toolbar", line))
    return FormattedText(fragments)


def _discover_startup_armory() -> Path | None:
    candidates = [Path.cwd(), Path.cwd() / "armory"]
    for candidate in candidates:
        try:
            return validate_armory_path(str(candidate))
        except ArmoryError:
            continue
    return None


def _default_armory_input(session: ChatSession) -> str:
    return str(session.armory_path or Path.cwd())


def _prompt_path(label: str, default: str) -> str | None:
    """Prompt the user for a path.  Returns *None* on cancel (empty or 'q')."""
    try:
        raw = direct_input(f"{label} [{default}] (q to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        return None
    if raw.lower() in ("q", "quit", "cancel", "back"):
        return None
    return raw or default


def _save_before_switch(session: ChatSession) -> None:
    if not session.dirty or session.armory_path is None:
        return
    try:
        path = save_session(session)
        print_success(f"Saved chat to {path}")
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))


def _start_fresh_session(
    session: ChatSession,
    armory_path: Path | None,
) -> ChatSession:
    if armory_path is None and session.armory_path is None:
        print_info("Already in plain chat mode.")
        return session
    _save_before_switch(session)
    try:
        if armory_path is None:
            new_session = create_plain_session(session.config)
        else:
            new_session = create_session(session.config, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        return session
    if armory_path is None:
        print_success("Detached armory. Plain chat mode.")
        return new_session
    print_success(f"Using armory {armory_path}")
    if new_session.source_file_count:
        print_info(f"Loaded {new_session.source_file_count} file(s).")
    return new_session


def _detach_armory(session: ChatSession) -> ChatSession:
    return _start_fresh_session(session, None)


def _open_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return session
    try:
        armory_path = validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    return _start_fresh_session(session, armory_path)


def _create_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("New armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return session
    armory_path = normalize_path(raw_path)
    try:
        initialize(armory_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    print_success(f"Initialized armory at {armory_path}")
    try:
        return _start_fresh_session(session, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        print_info("Add source files and use /armory to attach it.")
        return session


def _prompt_armory_for_sessions(session: ChatSession) -> Path | None:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)
    if raw_path is None:
        print_info("Cancelled.")
        return None
    try:
        return validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return None


def _resume_saved_chat(session: ChatSession) -> ChatSession:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return session
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print_info("No saved chats found.")
        return session
    options = [
        MenuOption(
            entry["title"] or entry["session_id"],
            f"{entry['session_id']}  {entry['updated_at']}",
        )
        for entry in sessions
    ]
    selected = select_option("Resume Saved Chat", options)
    if selected is None:
        return session
    entry = sessions[selected]
    _save_before_switch(session)
    try:
        resumed = resume_session(session.config, armory_path, entry["session_id"])
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))
        return session
    print_success(f"Resumed session {resumed.session_id}")
    if resumed.title:
        print_info(f"Title: {resumed.title}")
    return resumed


def _list_saved_chats(session: ChatSession) -> None:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print_info("No saved chats found.")
        return
    print(f"Saved chats for {armory_path}:")
    for entry in sessions:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")


def _handle_armory_command(session: ChatSession) -> ChatSession:
    selected = select_option("Armory", ARMORY_MENU_OPTIONS)
    handlers = [
        _open_armory,
        _create_armory,
        _detach_armory,
        _resume_saved_chat,
        _list_saved_chats,
    ]
    if selected is None or selected < 0 or selected >= len(handlers):
        return session
    result = handlers[selected](session)
    if result is None:
        return session
    return result


def _run_shell_command(cmd: str) -> None:
    """Execute a shell command and display output."""
    print(styled(f"$ {cmd}", STYLE_DIM))
    try:
        subprocess.run(cmd, shell=True, capture_output=False, text=True, check=False)
    except Exception as exc:
        print_error(str(exc))


def _invalidate_prompt(pt_session: PromptSession | None) -> None:
    if pt_session is None:
        return
    try:
        pt_session.app.invalidate()
    except Exception:
        return


def _start_background_reply(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    runtime: ShellRuntime,
    toolbar_ref: list[str],
    pt_session: PromptSession,
) -> None:
    history.add(user_input)
    runtime.busy = True
    runtime.steering_count = 0
    runtime.abort_event.clear()
    _refresh_bottom_toolbar(session, toolbar_ref, runtime)
    _invalidate_prompt(pt_session)

    print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)

    def _worker() -> None:
        try:
            send_user_message(session, user_input, abort=runtime.abort_event)
        except StreamRecoveryError as rec:
            msg = (
                f"{styled('warning:', STYLE_ERROR)} "
                f"Stream interrupted — connection lost after partial reply."
            )
            if rec.partial_content:
                msg += f" ({len(rec.partial_content)} chars received)"
            print(msg)
        except EngineError as exc:
            print_error(str(exc))
        finally:
            runtime.worker = None
            runtime.abort_event.clear()
            runtime.busy = False
            _refresh_bottom_toolbar(session, toolbar_ref, runtime)
            _invalidate_prompt(pt_session)

    runtime.worker = threading.Thread(target=_worker, name="hephaistos-shell-reply", daemon=True)
    runtime.worker.start()


def _handle_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    streaming: bool = False,
) -> tuple[ChatSession, bool]:
    """Process a single input. Returns (session, should_continue).

    If *streaming* is True, the agent is currently running. The input is
    enqueued as a steering message instead of being processed normally.
    """
    if not user_input or not user_input.strip():
        return session, True
    if streaming:
        from hephaistos.harness.dispatch import SteeringQueue

        if isinstance(session.steering, SteeringQueue):
            session.steering.enqueue(user_input)
        return session, True
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            _run_shell_command(cmd)
        return session, True
    if user_input.startswith("/"):
        history.add(user_input)
        stripped = user_input.strip()
        if stripped == "/":
            registry = get_registry()
            cmd = registry.find("help")
            if cmd:
                cmd.handle(session, "")
            return session, True
        space_idx = stripped.find(" ")
        if space_idx == -1:
            cmd_name = stripped[1:].lower()
            cmd_args = ""
        else:
            cmd_name = stripped[1:space_idx].lower()
            cmd_args = stripped[space_idx + 1 :].strip()

        registry = get_registry()
        cmd = registry.find(cmd_name)
        if cmd is None:
            print_error(f"Unknown command: {stripped}")
            print_info("Type /help for available commands.")
            return session, True

        result = cmd.handle(session, cmd_args)

        if result.should_exit:
            return session, False

        if result.new_session is not None:
            session = result.new_session  # type: ignore[assignment]
        if result.output and result.output.startswith("__RESEND__:"):
            new_input = result.output[len("__RESEND__:") :]
            history.add(new_input)
            print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)
            abort = threading.Event()
            try:
                send_user_message(session, new_input, abort=abort)
            except StreamRecoveryError as rec:
                msg = (
                    f"{styled('warning:', STYLE_ERROR)} "
                    f"Stream interrupted — connection lost after partial reply."
                )
                if rec.partial_content:
                    msg += f" ({len(rec.partial_content)} chars received)"
                print(msg)
            except EngineError as exc:
                print_error(str(exc))
        return session, True
    history.add(user_input)
    print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)
    abort = threading.Event()
    try:
        send_user_message(session, user_input, abort=abort)
    except StreamRecoveryError as rec:
        msg = (
            f"{styled('warning:', STYLE_ERROR)} "
            f"Stream interrupted — connection lost after partial reply."
        )
        if rec.partial_content:
            msg += f" ({len(rec.partial_content)} chars received)"
        print(msg)
    except EngineError as exc:
        print_error(str(exc))
    return session, True


def _print_shell_intro(session: ChatSession) -> None:
    print_shell_intro(
        version=__version__,
        armory_path=str(session.armory_path or "none"),
        source_file_count=session.source_file_count or 0,
        model=session.config.model,
        has_api_key=bool(session.config.resolved_api_key),
    )


def _get_history_path(session: ChatSession) -> Path:
    if session.armory_path is None:
        return _HISTORY_DIR / "plain-history"
    return session.armory_path / ".hephaistos" / "history"


def _save_on_exit(session: ChatSession) -> None:
    if session.dirty and session_has_messages(session) and session.armory_path is not None:
        try:
            path = save_session(session)
            print_success(f"Saved chat to {path}")
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
    session.trace.close()


def _create_startup_session(config: ChatConfig) -> ChatSession:
    """Try to create a session with the auto-discovered armory, fall back to plain."""
    armory = _discover_startup_armory()
    if armory is None:
        return create_plain_session(config)
    try:
        return create_session(config, armory)
    except SessionError as exc:
        print_error(f"Auto-discovered armory unusable: {exc}")
        print_info("Falling back to plain chat mode.")
        return create_plain_session(config)


def run_chat_shell(
    session: ChatSession | None = None,
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> None:
    """Run the interactive chat shell with rich terminal UX."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _run_fallback_shell(session)
        return

    if session is None:
        session = _create_startup_session(load_config())

    _print_shell_intro(session)

    kb = keybindings or DEFAULT_SHELL_KEYBINDINGS

    runtime = ShellRuntime()
    toolbar_ref = [_build_bottom_toolbar_status(session, runtime)]
    history_path = _get_history_path(session)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    pt_session = PromptSession(
        message=_get_prompt_message(runtime),
        style=_PT_STYLE,
        history=FileHistory(str(history_path)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=SlashCommandCompleter(),
        key_bindings=_build_keybindings(kb),
        bottom_toolbar=lambda: _get_bottom_toolbar(toolbar_ref),
        multiline=True,
        complete_while_typing=True,
        show_frame=False,
    )

    history = InputHistory()

    with patch_stdout(raw=True):
        while True:
            try:
                user_input = pt_session.prompt(prompt_continuation=_get_prompt_continuation)
            except KeyboardInterrupt:
                if runtime.busy:
                    runtime.abort_event.set()
                    print_info("Interrupt requested.")
                continue
            except EOFError:
                if runtime.busy:
                    runtime.abort_event.set()
                    if runtime.worker is not None:
                        runtime.worker.join(timeout=5.0)
                break

            if not user_input or not user_input.strip():
                continue

            stripped = user_input.strip().lower()
            if runtime.busy and stripped in {"/exit", "/quit", "/q"}:
                runtime.abort_event.set()
                if runtime.worker is not None:
                    runtime.worker.join(timeout=5.0)
                break

            if runtime.busy:
                if user_input.startswith("/"):
                    session, _ = _handle_input(session, user_input, history)
                    _refresh_bottom_toolbar(session, toolbar_ref, runtime)
                    _invalidate_prompt(pt_session)
                    continue
                session, _ = _handle_input(session, user_input, history, streaming=True)
                runtime.steering_count += 1
                _refresh_bottom_toolbar(session, toolbar_ref, runtime)
                _invalidate_prompt(pt_session)
                continue

            try:
                if user_input.startswith(("/", "!")):
                    session, should_continue = _handle_input(session, user_input, history)
                    _refresh_bottom_toolbar(session, toolbar_ref, runtime)
                    if not should_continue:
                        break
                    continue

                _start_background_reply(
                    session, user_input, history, runtime, toolbar_ref, pt_session
                )
            except KeyboardInterrupt:
                print_info("Cancelled.")
                continue

    _save_on_exit(session)


def _run_fallback_shell(session: ChatSession | None = None) -> None:
    """Simple fallback shell when the terminal is not a TTY."""
    if session is None:
        session = _create_startup_session(load_config())

    print("Hephaistos (basic mode)")
    history = InputHistory()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        session, should_continue = _handle_input(session, user_input, history)
        if not should_continue:
            break

    _save_on_exit(session)
