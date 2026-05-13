from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import hephaistos.commands.display as _commands_display
import hephaistos.commands.memory as _commands_memory
import hephaistos.commands.model as _commands_model
import hephaistos.commands.persona as _commands_persona
import hephaistos.commands.session as _commands_session
import hephaistos.commands.study as _commands_study
from hephaistos import commands
from hephaistos.armory.storage import initialize
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession, create_plain_session
from hephaistos.providers import catalog
from hephaistos.providers.catalog import LiveProviderCatalog
from hephaistos.providers.config import default_config
from hephaistos.providers.registry import ModelInfo
from hephaistos.rag.chunker import Chunk
from hephaistos.rag.context import EvidenceChunk, TurnEvidence
from hephaistos.study import StudyAutonomyMode, StudyFeedbackType, StudyPhase, StudyRecallRating
from hephaistos.study.schedule import load_study_schedule
from hephaistos.terminal import MenuOption
from hephaistos.terminal.source_open import SourceOpenResult


def test_command_registry_has_unique_names_and_aliases() -> None:
    registry = commands.get_registry()
    names = [cmd.name for cmd in registry.commands]
    aliases = [alias for cmd in registry.commands for alias in cmd.aliases]
    command_tokens = names + aliases

    assert all(name for name in names)
    assert len(names) == len(set(names))
    assert len(command_tokens) == len(set(command_tokens))
    assert not any(alias.startswith("/") for alias in aliases)


def test_command_registry_suggestions_include_only_visible_commands() -> None:
    registry = commands.get_registry()
    suggested_names = {suggestion.name for suggestion in registry.suggestions()}
    visible_names = {cmd.name for cmd in registry.commands if not cmd.hidden}
    hidden_names = {cmd.name for cmd in registry.commands if cmd.hidden}

    assert suggested_names == visible_names
    assert suggested_names.isdisjoint(hidden_names)
    assert all(suggestion.description for suggestion in registry.suggestions())


def test_command_registry_includes_login_logout() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("login") is not None
    assert registry.find("logout") is not None
    assert "login" in names
    assert "logout" in names


def test_command_registry_includes_settings() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("settings") is not None
    assert "settings" in names


def test_command_registry_includes_exam_and_priority() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("exam") is not None
    assert registry.find("priority") is not None
    assert registry.find("mode") is not None
    assert registry.find("autopilot") is not None
    assert "exam" in names
    assert "priority" in names
    assert "mode" in names
    assert "autopilot" in names


def test_mode_command_updates_study_autonomy(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.ModeCommand().handle(session, "manual")

    out = capsys.readouterr().out
    assert result.output is None
    assert session.study_state.autonomy_mode is StudyAutonomyMode.MANUAL
    assert session.dirty is True
    assert "manual" in out


def test_autopilot_exam_command_sets_bounded_session(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.AutopilotCommand().handle(session, "exam 45m")

    out = capsys.readouterr().out
    assert session.study_state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
    assert session.study_state.autopilot_session_type == "exam"
    assert session.study_state.time_budget_minutes == 45
    assert session.study_state.session_goal == "exam preparation"
    assert result.output is not None
    assert result.output.startswith("__RESEND__:Autopilot exam mode.")
    assert "confidence from 0-100%" in result.output
    assert "45 minute" in out


def test_autopilot_without_args_starts_general_session(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.AutopilotCommand().handle(session, "")

    out = capsys.readouterr().out
    assert session.study_state.autonomy_mode is StudyAutonomyMode.AUTOPILOT
    assert session.study_state.autopilot_session_type == "general"
    assert session.study_state.session_goal == "autonomous guided study"
    assert result.output is not None
    assert result.output.startswith("__RESEND__:Autopilot general mode.")
    assert "confidence from 0-100%" in result.output
    assert "Autopilot general session started" in out


def test_autopilot_off_returns_to_manual(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    commands.AutopilotCommand().handle(session, "exam 30m")

    result = commands.AutopilotCommand().handle(session, "off")

    out = capsys.readouterr().out
    assert result.output is None
    assert session.study_state.autonomy_mode is StudyAutonomyMode.MANUAL
    assert session.study_state.autopilot_session_type == ""
    assert session.study_state.time_budget_minutes is None
    assert "Autopilot off" in out


def test_import_command_refreshes_running_session_sources(tmp_path: Path) -> None:
    armory = tmp_path / "import-armory"
    initialize(armory)
    first = armory / "materials" / "first.md"
    first.write_text("# First\n", encoding="utf-8")
    imported = tmp_path / "imported.md"
    imported.write_text("# Imported\n", encoding="utf-8")
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="import-session",
        armory_path=armory,
        source_file_count=1,
        source_files=("materials/first.md",),
    )

    commands.ImportCommand().handle(session, str(imported))

    assert session.source_file_count == 2
    assert "materials/imported.md" in session.source_files
    assert session.rag_index is None


def test_exam_command_warns_and_resends_active_recall_prompt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "exam-armory"
    initialize(armory)
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="exam-session",
        armory_path=armory,
    )

    result = commands.ExamCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "materials aside" in out
    assert "time limit" in out
    assert result.output is not None
    assert result.output.startswith("__RESEND__:Ask me one random exam-style question")
    assert "concrete time limit" in result.output
    assert "reason from memory" in result.output
    assert "do not show the result" in result.output
    assert "source IDs" in result.output
    assert "citations" in result.output


def test_priority_command_prints_local_priority_scan(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    armory = tmp_path / "priority-armory"
    initialize(armory)
    exam = armory / "materials" / "past-exams"
    exam.mkdir(parents=True)
    (exam / "2024.md").write_text(
        "Explain Dijkstra shortest paths. [10 marks]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_commands_study, "_priority_output_dir", lambda: tmp_path / "Downloads")
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="priority-session",
        armory_path=armory,
    )

    result = commands.PriorityCommand().handle(session, "graphs")
    out = capsys.readouterr().out

    assert result.output is None
    assert "Local priority scan" in out
    assert "graphs" in out
    assert "exam marks 10" in out
    assert "Priority report saved" in out
    assert "Downloads" in out
    assert list((tmp_path / "Downloads").glob("hephaistos-priority-*.html"))


def test_command_registry_includes_memory_and_recommend() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("memory") is not None
    assert registry.find("recommend") is not None
    assert "memory" in names
    assert "recommend" in names


def test_memory_status_reports_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    monkeypatch.setattr(_commands_memory, "resolve_supermemory_key", lambda: "")

    result = commands.MemoryCommand().handle(session, "status")

    out = capsys.readouterr().out
    assert result.output is None
    assert "Supermemory: disabled" in out
    assert "Run /memory setup" in out


def test_memory_disable_updates_settings(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.MemoryCommand().handle(session, "disable")

    out = capsys.readouterr().out
    assert "Supermemory disabled" in out


def test_recommend_command_lists_study_models(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.RecommendCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Study picks" in out
    assert "study" in out


def test_command_registry_uses_sessions_for_saved_chat_switching() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("chats") is None
    assert registry.find("sessions") is not None
    assert registry.find("resume") is None
    assert registry.find("history") is None
    assert "chats" not in names
    assert "sessions" in names
    assert "resume" not in names
    assert "history" not in names


def test_command_registry_includes_session_utility_commands() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    for name in ("evidence", "tokens", "cost", "stats"):
        assert registry.find(name) is not None
        assert name in names


def test_tokens_and_cost_commands_toggle_live_toolbar() -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.TokensCommand().handle(session, "show")
    commands.CostCommand().handle(session, "show")

    assert session.live_tokens_visible is True
    assert session.live_cost_visible is True

    commands.TokensCommand().handle(session, "hide")
    commands.CostCommand().handle(session, "hide")

    assert session.live_tokens_visible is False
    assert session.live_cost_visible is False


def test_stats_command_reports_current_session(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("user", "hello")
    session.conversation.add("assistant", "hi")

    commands.StatsCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Current session:" in out
    assert "Turns:      1" in out
    assert "Assistant:  1 messages" in out


def test_stats_command_reports_study_recall_timing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "study-stats"
    initialize(armory)
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="study-stats",
        armory_path=armory,
    )
    session.study_state.phase = StudyPhase.RECALL
    session.study_state.current_item = "Q1"
    session.study_state.attempt_count = 2
    session.study_state.last_feedback_type = StudyFeedbackType.PARTIAL
    session.study_state.last_recall_seconds = 75
    session.study_state.last_recall_rating = StudyRecallRating.HARD
    store = load_study_schedule(armory)
    store.record_review(
        "Q1",
        retrieval_query="Q1",
        source_refs=["materials/exam.md#chunk=0"],
        rating=StudyRecallRating.HARD,
        elapsed_seconds=75,
    )
    store.save()

    commands.StatsCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Study mode:" in out
    assert "Recall:    1m 15s" in out
    assert "Effort:    hard" in out
    assert "Scheduled: 1 item(s)" in out


def test_remind_command_reports_due_study_items_without_vocab(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "remind-study"
    initialize(armory)
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="remind-study",
        armory_path=armory,
    )
    store = load_study_schedule(armory)
    store.record_review(
        "Explain Dijkstra",
        retrieval_query="dijkstra",
        source_refs=["materials/exam.md#chunk=0"],
        rating=StudyRecallRating.HARD,
        elapsed_seconds=160,
        concept="Dijkstra shortest paths",
        error_type="misconception",
        exam_importance=0.75,
        now=datetime.now(UTC) - timedelta(days=2),
    )
    store.save()

    commands.RemindCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "study item" in out
    assert "due for active recall" in out
    assert "Explain Dijkstra" in out
    assert "concept: Dijkstra shortest paths" in out
    assert "last: misconception" in out
    assert "failures: 1" in out
    assert "exam priority: 75%" in out
    assert "/exam" in out


def test_command_registry_uses_models_not_model() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("model") is None
    assert registry.find("models") is not None
    assert "model" not in names
    assert "models" in names


def test_models_command_switches_selected_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    cfg = ChatConfig(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-5.4",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="session-1",
    )
    messages: list[tuple[str, str]] = []

    monkeypatch.setattr(
        _commands_model.ProviderConfig,
        "load",
        classmethod(lambda _cls: default_config()),
    )

    def select_gpt_55(_title: str, options: list[MenuOption]) -> int:
        return next(index for index, option in enumerate(options) if option.label == "gpt-5.5")

    monkeypatch.setattr(_commands_model, "select_option", select_gpt_55)

    def switch(session: ChatSession, slug: str, model: str) -> bool:
        session.config.model = model
        session.config.apply_provider_reference(slug, "")
        return True

    monkeypatch.setattr(_commands_model, "switch_model", switch)
    monkeypatch.setattr(
        _commands_model,
        "print_success",
        lambda msg: messages.append(("success", msg)),
    )
    monkeypatch.setattr(
        _commands_model,
        "print_error",
        lambda msg: messages.append(("error", msg)),
    )

    result = commands.ModelsCommand().handle(session, "gpt-5.5")

    assert result.output is None
    assert session.config.model == "gpt-5.5"
    assert messages == [("success", "Switched to OpenAI API / gpt-5.5")]


def test_models_command_shows_live_openrouter_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAISTOS_DISABLE_LIVE_MODELS", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    catalog.invalidate_catalog_cache()
    pc = default_config()
    pc.set_active("openrouter")
    pc.providers["openrouter"].current_model = "openai/gpt-5.4"
    session = ChatSession(
        config=ChatConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-5.4",
        ),
        conversation=Conversation(),
        session_id="session-1",
    )

    def fake_fetch(_endpoint: str) -> LiveProviderCatalog:
        return LiveProviderCatalog(
            models=[
                "anthropic/claude-sonnet-latest",
                "poolside/laguna-m.1:free",
            ],
            metadata=[
                ModelInfo(
                    "anthropic/claude-sonnet-latest",
                    "openrouter",
                    "Anthropic Claude Sonnet Latest",
                    1_000_000,
                    128_000,
                    0.003,
                    0.015,
                ),
                ModelInfo(
                    "poolside/laguna-m.1:free",
                    "openrouter",
                    "Poolside Laguna M.1 (free)",
                    131_072,
                    8_192,
                    0.0,
                    0.0,
                    tags=("free",),
                ),
            ],
        )

    visible_options: list[MenuOption] = []

    def capture_options(_title: str, options: list[MenuOption]) -> None:
        visible_options.extend(options)

    monkeypatch.setattr(catalog, "_fetch_openrouter_catalog", fake_fetch)
    catalog.hydrate_provider_models(
        pc,
        allow_network=True,
        provider_slugs={"openrouter"},
    )
    monkeypatch.setattr(
        _commands_model.ProviderConfig,
        "load",
        classmethod(lambda _cls: pc),
    )
    monkeypatch.setattr(_commands_model, "select_option", capture_options)

    commands.ModelsCommand().handle(session, "")

    labels = [option.label for option in visible_options]
    assert labels[:2] == [
        "poolside/laguna-m.1:free",
        "anthropic/claude-sonnet-latest",
    ]
    assert visible_options[0].description == "via OpenRouter  free, API key required"


def test_clear_command_supports_plain_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("user", "hello")

    monkeypatch.setattr(
        _commands_session,
        "confirm",
        lambda *_args, **_kwargs: True,
    )

    result = commands.ClearCommand().handle(session, "")

    assert result.new_session is not None
    assert result.new_session.armory_path is None
    assert result.new_session.conversation.messages[0].role == "system"
    assert len(result.new_session.conversation.messages) == 1


def test_persona_command_updates_plain_chat_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    before = session.conversation.messages[0].content

    monkeypatch.setattr(
        _commands_persona,
        "print_success",
        lambda _msg: None,
    )

    result = commands.PersonaCommand().handle(session, "tutor")

    after = session.conversation.messages[0].content
    assert result.output is None
    assert session.persona.slug == "tutor"
    assert after != before
    assert "patient tutor" in after
    assert "No armory or study materials are attached" in after


def test_models_command_reports_no_matching_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = ChatConfig(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-5.4",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="session-1",
    )
    messages: list[tuple[str, str]] = []

    monkeypatch.setattr(
        _commands_model.ProviderConfig,
        "load",
        classmethod(lambda _cls: default_config()),
    )
    monkeypatch.setattr(
        _commands_model,
        "print_success",
        lambda msg: messages.append(("success", msg)),
    )
    monkeypatch.setattr(
        _commands_model,
        "print_error",
        lambda msg: messages.append(("error", msg)),
    )

    result = commands.ModelsCommand().handle(session, "does-not-exist")

    assert result.output is None
    assert session.config.model == "gpt-5.4"
    assert messages == []


# ---------------------------------------------------------------------------
# Coverage-boosting tests for command handlers
# ---------------------------------------------------------------------------


def test_exit_command_returns_quit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.ExitCommand().handle(session, "")

    assert result.should_exit is True


def test_quit_command_returns_quit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.QuitCommand().handle(session, "")

    assert result.should_exit is True


def test_status_command_reports_model(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    result = commands.StatusCommand().handle(session, "")

    assert result.output is not None
    assert "Model:" in result.output


def test_evidence_command_no_armory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.EvidenceCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "evidence" in out.lower()


def _session_with_line_mapped_evidence(tmp_path: Path) -> ChatSession:
    armory = tmp_path / "evidence-armory"
    initialize(armory)
    source = armory / "materials" / "notes.md"
    text = "Intro\n\n## Target\nExact sentinel phrase amber forge.\nMore context.\n"
    source.write_text(text, encoding="utf-8")
    start = text.index("Exact sentinel")
    content = "Exact sentinel phrase amber forge."
    chunk = Chunk(
        text=content,
        source="materials/notes.md",
        index=0,
        char_start=start,
        char_end=start + len(content),
        heading="Target",
        heading_level=2,
    )
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="evidence-session",
        armory_path=armory,
    )
    session.last_turn_evidence = TurnEvidence(
        (EvidenceChunk(evidence_id="E1", chunk=chunk, score=0.91, content=content),)
    )
    return session


def test_evidence_command_lists_exact_source_location(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _session_with_line_mapped_evidence(tmp_path)

    commands.EvidenceCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "E1" in out
    assert "materials/notes.md" in out
    assert "#chunk=0" not in out
    assert "line 4" in out
    assert "heading: Target" in out
    assert "expand: /evidence E1" in out
    assert "open:   /evidence E1 open" in out
    assert "Expand exact source text: /evidence E1" in out
    assert "Open source at line:      /evidence E1 open" in out


def test_evidence_command_uses_reader_friendly_label_when_lines_unknown(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "evidence-armory"
    initialize(armory)
    chunk = Chunk(
        text="Slide text extracted by a converter.",
        source="materials/week-02-slides.pdf",
        index=2,
        char_start=0,
        char_end=35,
    )
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="evidence-session",
        armory_path=armory,
    )
    session.last_turn_evidence = TurnEvidence(
        (EvidenceChunk(evidence_id="E1", chunk=chunk, score=0.91, content=chunk.text),)
    )

    commands.EvidenceCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "slide/deck excerpt 3" in out
    assert "line unknown" not in out
    assert "chunk" not in out.lower()


def test_evidence_command_groups_multiple_items_by_source(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _session_with_line_mapped_evidence(tmp_path)
    armory = session.armory_path
    assert armory is not None
    other = armory / "materials" / "other.md"
    other.write_text("Alpha\nBeta evidence line.\n", encoding="utf-8")
    text = other.read_text(encoding="utf-8")
    start = text.index("Beta")
    chunk = Chunk(
        text="Beta evidence line.",
        source="materials/other.md",
        index=0,
        char_start=start,
        char_end=start + len("Beta evidence line."),
    )
    assert session.last_turn_evidence is not None
    session.last_turn_evidence = TurnEvidence(
        (
            *session.last_turn_evidence.items,
            EvidenceChunk(evidence_id="E2", chunk=chunk, score=0.82, content=chunk.text),
        )
    )

    commands.EvidenceCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Last turn sources:" in out
    assert "materials/notes.md" in out
    assert "materials/other.md" in out
    assert "E1  line 4; score=0.910" in out
    assert "E2  line 2; score=0.820" in out


def test_evidence_command_shows_numbered_excerpt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _session_with_line_mapped_evidence(tmp_path)

    commands.EvidenceCommand().handle(session, "E1")

    out = capsys.readouterr().out
    assert "line 4; score=0.910" in out
    assert "chars " not in out
    assert "heading: Target" in out
    assert "Source text:" in out
    assert "> 4 │ Exact sentinel phrase amber forge." in out
    assert "Open source: /evidence E1 open" in out


def test_evidence_command_opens_source_at_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _session_with_line_mapped_evidence(tmp_path)
    opened: list[tuple[Path, int | None]] = []

    def fake_open(path: Path, line: int | None = None) -> SourceOpenResult:
        opened.append((path, line))
        return SourceOpenResult(path=path, line=line, used_line=True)

    monkeypatch.setattr(_commands_display, "open_source_file", fake_open)

    commands.EvidenceCommand().handle(session, "E1 open")

    out = capsys.readouterr().out
    assert session.armory_path is not None
    assert "Opened" in out
    assert opened == [((session.armory_path / "materials" / "notes.md").resolve(), 4)]


def test_evidence_command_handles_deleted_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = _session_with_line_mapped_evidence(tmp_path)
    assert session.armory_path is not None
    (session.armory_path / "materials" / "notes.md").unlink()
    monkeypatch.setattr(
        _commands_display,
        "open_source_file",
        lambda _path, _line=None: pytest.fail("deleted source should not be opened"),
    )

    commands.EvidenceCommand().handle(session, "E1 open")

    out = capsys.readouterr().out
    assert "Evidence source not found" in out


def test_save_command_plain_session(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    monkeypatch.setattr(
        _commands_session,
        "save_session",
        lambda _s: Path("/fake/saved.json"),
    )

    result = commands.SaveCommand().handle(session, "")
    assert result.output is not None
    assert "Saved" in result.output


def test_compact_command_empty_session(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CompactCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "Nothing to compact" in out


def test_edit_command_no_messages(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.EditCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "No user messages" in out


def test_tokens_command_invalid_arg(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.TokensCommand().handle(session, "bogus")
    out = capsys.readouterr().out
    assert "Usage:" in out or "toggle" in out.lower()


def test_tokens_command_toggle(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.TokensCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "tokens" in out.lower()


def test_cost_command_invalid_arg(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CostCommand().handle(session, "bogus")
    out = capsys.readouterr().out
    assert "Usage:" in out or "toggle" in out.lower()


def test_cost_command_toggle(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CostCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "cost" in out.lower()
