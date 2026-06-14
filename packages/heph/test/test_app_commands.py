from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import ai.providers.model_choices as _model_choices
import heph.commands.display as _commands_display
import heph.commands.local as _commands_local
import heph.commands.model as _commands_model
import heph.commands.study as _learning_commands
import pytest
from ai.providers import catalog
from ai.providers.catalog import LiveProviderCatalog
from ai.providers.config import Provider, ProviderConfig, default_config
from ai.providers.llama_cpp import (
    LLAMA_CPP_PROVIDER_SLUG,
    LlamaCppCandidate,
    LlamaCppInstallResult,
    LlamaCppModelRecord,
    LlamaCppServerState,
    ToolCapabilityResult,
)
from ai.providers.registry import ModelInfo
from ai.runtime import ChatConfig, Conversation
from heph import commands
from hephaion.armory.storage import initialize
from hephaion.chat.session import ChatSession, create_plain_session
from hephaion.rag.chunker import Chunk
from hephaion.rag.context import EvidenceChunk, TurnEvidence
from hephaion.study.priority import PriorityAnalysis, PriorityPdfCompiler, PriorityReport
from hephaion.study.schedule import load_recall_schedule
from interfaces.terminal import MenuOption
from interfaces.terminal.source_open import SourceOpenResult

from hephaion.chat import model_selection as _model_selection
from hephaion.memory import MemoryStore
from hephaion.parameters import settings as settings_store
from hephaion.study import LearningFeedbackType, LearningPhase, RecallRating


class _FakePriorityPdfCompiler:
    def compile(self, tex_path: Path, pdf_path: Path) -> None:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% hephaion fake test pdf\n")


def test_command_registry_has_unique_names_and_aliases() -> None:
    registry = commands.get_registry()
    names = [cmd.name for cmd in registry.commands]
    aliases = [alias for cmd in registry.commands for alias in cmd.aliases]
    command_tokens = names + aliases

    assert all(name for name in names)
    assert len(names) == len(set(names))
    assert len(command_tokens) == len(set(command_tokens))
    assert not any(alias.startswith("/") for alias in aliases)


def test_command_registry_suggestions_include_commands() -> None:
    registry = commands.get_registry()
    suggested_names = {suggestion.name for suggestion in registry.suggestions()}
    command_names = {cmd.name for cmd in registry.commands}

    assert suggested_names == command_names
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


def test_command_registry_includes_local() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("local") is not None
    assert "local" in names


def test_detach_command_returns_plain_session(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = create_plain_session(ChatConfig(base_url="https://example.test", model="test-model"))
    session.armory_path = tmp_path / "module"

    result = commands.DetachCommand().handle(session, "")

    assert result.new_session is not None
    assert result.new_session.armory_path is None
    assert "Armory detached" in capsys.readouterr().out


def test_detach_command_without_armory_leaves_session_plain(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(base_url="https://example.test", model="test-model"))

    result = commands.DetachCommand().handle(session, "")

    assert result.new_session is None
    assert "No armory attached" in capsys.readouterr().out


def test_settings_command_prints_summary(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.SettingsCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Settings are managed in the TUI with /settings." in out
    assert "Theme:" in out
    assert "Activity trace:" in out
    assert "Model thinking:" in out
    assert "Live cost:" in out
    assert "Provider:" in out


def test_command_registry_includes_exam_and_priority() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("exam") is not None
    assert registry.find("priority") is not None
    assert registry.find("mode") is None
    assert registry.find("autopilot") is None
    assert "exam" in names
    assert "priority" in names


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


def test_export_command_writes_session_markdown(tmp_path: Path) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.title = "Lesson notes"
    session.conversation.add("system", "private setup")
    session.conversation.add("user", "What matters here?")
    session.conversation.add("assistant", "The cited material.")
    export_path = tmp_path / "session.md"

    commands.ExportCommand().handle(session, str(export_path))

    assert export_path.read_text(encoding="utf-8") == "\n".join(
        [
            "# Lesson notes",
            "",
            "## You",
            "",
            "What matters here?",
            "",
            "## Heph",
            "",
            "The cited material.",
            "",
        ]
    )


def test_export_command_skips_empty_sessions(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("system", "private setup")
    export_path = tmp_path / "session.md"

    commands.ExportCommand().handle(session, str(export_path))

    assert not export_path.exists()
    assert "Nothing to export" in capsys.readouterr().out


def test_exam_command_without_bank_does_not_resend(
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
    assert result.output is None
    assert "No structured exam bank found" in out
    assert "without filling the chat context" in out


def test_exam_build_command_resends_structured_bank_program(
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

    result = commands.ExamCommand().handle(session, "build")

    out = capsys.readouterr().out
    assert result.output is not None
    assert result.output.startswith("__RESEND__:Execute EXAM_BANK_BUILD.")
    assert "structured JSON state file" in result.output
    assert "fixed label words" in result.output
    assert "Building a structured exam bank" in out


def test_exam_command_starts_from_structured_bank(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "exam-bank-armory"
    initialize(armory)
    material = armory / "materials" / "sheet.md"
    material.write_text(
        "1. Explain the invariant.\n\nThe invariant is preserved by each transition.\n",
        encoding="utf-8",
    )
    bank_dir = armory / ".hephaion"
    bank_dir.mkdir(exist_ok=True)
    (bank_dir / "exam_bank.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "id": "item-1",
                        "question": "Explain the invariant.",
                        "question_source_refs": ["materials/sheet.md#chunk=0"],
                        "result_source_refs": ["materials/sheet.md#chunk=0"],
                        "support_source_refs": [],
                        "topics": ["invariants"],
                        "time_limit_minutes": 4,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="exam-bank-session",
        armory_path=armory,
    )

    result = commands.ExamCommand().handle(session, "")

    out = capsys.readouterr().out
    assert result.output is None
    assert "Exam question" in out
    assert "Time limit: 4 minutes" in out
    assert "Explain the invariant." in out
    assert "tell Heph what your result was" in out
    assert session.learning_state.phase is LearningPhase.RECALL
    assert session.learning_state.current_item == "Explain the invariant."
    assert session.learning_state.expected_source_refs == ["materials/sheet.md#chunk=0"]
    assert session.learning_state.practice_session_type == "exam"


def test_exam_command_refuses_empty_structured_bank(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "empty-exam-bank-armory"
    initialize(armory)
    bank_dir = armory / ".hephaion"
    bank_dir.mkdir(exist_ok=True)
    (bank_dir / "exam_bank.json").write_text(
        '{"version": 1, "items": []}\n',
        encoding="utf-8",
    )
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="empty-exam-bank-session",
        armory_path=armory,
    )

    result = commands.ExamCommand().handle(session, "")

    out = capsys.readouterr().out
    assert result.output is None
    assert "No eligible exam-bank items" in out


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
    monkeypatch.setattr(_learning_commands, "_priority_output_dir", lambda: tmp_path / "Downloads")
    original_generate_priority_report = _learning_commands.generate_priority_report

    def generate_test_priority_report(
        analysis: PriorityAnalysis,
        output_dir: Path,
        *,
        config: ChatConfig | None = None,
        focus: str = "",
        compiler: PriorityPdfCompiler | None = None,
        keep_tex: bool = False,
        progress: Callable[[str], None] | None = None,
    ) -> PriorityReport:
        return original_generate_priority_report(
            analysis,
            output_dir,
            config=config,
            focus=focus,
            compiler=compiler or _FakePriorityPdfCompiler(),
            keep_tex=keep_tex,
            progress=progress,
        )

    monkeypatch.setattr(
        _learning_commands,
        "generate_priority_report",
        generate_test_priority_report,
    )
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="priority-session",
        armory_path=armory,
    )

    result = commands.PriorityCommand().handle(session, "graphs")
    out = capsys.readouterr().out

    assert result.output is None
    assert "Preparing indexed materials for priority analysis" in out
    assert "Read material source @past-exams/2024.md." in out
    assert "Indexed @past-exams/2024.md (1 chunks)." in out
    assert "Wrote index cache" in out
    assert "Indexed 1 enabled source(s) across 1 chunk(s)." in out
    assert "Analyzing recurring topics from enabled materials" in out
    assert "Ran priority.scan --sources 1 --chunks 1." in out
    assert "Read source 1/1: @past-exams/2024.md (1 chunk(s))." in out
    assert "Read @past-exams/2024.md chunk 1/1" in out
    assert "Generating printable priority sheet" in out
    assert "Ran priority.report --topics" in out
    assert "Using deterministic local output (no model configured)." in out
    assert "Wrote temporary LaTeX" in out
    assert "Ran _FakePriorityPdfCompiler.compile" in out
    assert "Wrote PDF" in out
    assert "Wrote verification sidecar" in out
    assert "Priority report verified in" in out
    assert "Local priority scan" in out
    assert "graphs" in out
    assert "High-yield" in out
    assert "exam marks" not in out
    assert "Priority sheet saved" in out
    assert "Downloads" in out
    assert list((tmp_path / "Downloads").glob("hephaion-priority-*.pdf"))


def test_command_registry_includes_memory() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("memory") is not None
    assert "memory" in names


def test_memory_status_reports_saved_memory(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    memory = MemoryStore(tmp_path)
    memory.add(
        "citation style",
        "User prefers compact cited answers.",
        source="conversation",
        confidence="verified",
    )
    session.configure_armory_context(memory=memory)

    result = commands.MemoryCommand().handle(session, "status")

    out = capsys.readouterr().out
    assert result.output is None
    assert "Saved memory:" in out
    assert "- [verified] citation style: User prefers compact cited answers. (conversation)" in out
    assert "Entries:" not in out


def test_memory_status_escapes_terminal_controls(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    memory = MemoryStore(tmp_path)
    memory.add(
        "topic\x1b[31m",
        "content\x07",
        source="source\x1b[0m",
        confidence="verified",
    )
    session.configure_armory_context(memory=memory)

    commands.MemoryCommand().handle(session, "status")

    out = capsys.readouterr().out
    assert "\x1b" not in out
    assert "\x07" not in out
    assert "topic\\x1b[31m" in out
    assert "content\\x07" in out
    assert "source\\x1b[0m" in out


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

    for name in ("evidence", "cost", "stats"):
        assert registry.find(name) is not None
        assert name in names
    assert registry.find("tokens") is None
    assert registry.find("thinking") is None
    assert registry.find("reasoning") is None
    assert "tokens" not in names
    assert "thinking" not in names


def test_cost_command_toggles_live_toolbar() -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CostCommand().handle(session, "show")

    assert session.live_cost_visible is True

    commands.CostCommand().handle(session, "hide")

    assert session.live_cost_visible is False


def test_cost_command_persists_live_toolbar_state() -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CostCommand().handle(session, "hide")

    saved = settings_store.load_raw_settings()
    assert saved["live_cost_visible"] is False


def test_stats_command_reports_current_session(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    session.conversation.add("user", "hello")
    session.conversation.add("assistant", "hi")

    commands.StatsCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Current session:" in out
    assert "Turns:     1" in out
    assert "Assistant: 1 messages" in out


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
    session.learning_state.phase = LearningPhase.RECALL
    session.learning_state.current_item = "Q1"
    session.learning_state.attempt_count = 2
    session.learning_state.last_feedback_type = LearningFeedbackType.PARTIAL
    session.learning_state.last_recall_seconds = 75
    session.learning_state.last_recall_rating = RecallRating.HARD
    store = load_recall_schedule(armory)
    store.record_review(
        "Q1",
        retrieval_query="Q1",
        source_refs=["materials/exam.md#chunk=0"],
        rating=RecallRating.HARD,
        elapsed_seconds=75,
    )
    store.save()

    commands.StatsCommand().handle(session, "")

    out = capsys.readouterr().out
    assert "Learning state:" in out
    assert "Recall:    1m 15s" in out
    assert "Effort:    hard" in out
    assert "Scheduled: 1 item(s)" in out


def test_terminal_study_rating_menu_uses_label_value_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    visible_options: list[MenuOption] = []

    def capture_options(_title: str, options: list[MenuOption]) -> int:
        visible_options.extend(options)
        return 0

    monkeypatch.setattr(_learning_commands, "select_option", capture_options)

    rating = _learning_commands.TerminalDrillUi().prompt_rating()

    assert rating is _learning_commands.Rating.HARD
    assert [option.label for option in visible_options] == ["HARD", "GOOD", "EASY"]
    assert [option.description for option in visible_options] == [
        "EFFORT had to think",
        "EFFORT knew it",
        "EFFORT instant recall",
    ]


def test_command_registry_uses_models_not_model() -> None:
    registry = commands.get_registry()
    suggestions = registry.suggestions()
    names = {suggestion.name for suggestion in suggestions}

    assert registry.find("remind") is None
    assert "remind" not in names
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
    monkeypatch.delenv("HEPHAION_DISABLE_LIVE_MODELS", raising=False)
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
                "google/gemini-3-flash-preview",
                "poolside/laguna-m.1:free",
            ],
            metadata=[
                ModelInfo(
                    "google/gemini-3-flash-preview",
                    "openrouter",
                    "Google Gemini 3 Flash Preview",
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
        "google/gemini-3-flash-preview",
    ]
    assert (
        visible_options[0].description == "PROVIDER openrouter  COST free  AUTH api key required"
    )


def test_model_choices_hide_active_openai_codex_without_oauth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pc = default_config()
    pc.set_active("openai-codex")
    pc.providers["openai-codex"].current_model = "gpt-5.5"

    def accessible(provider: Provider, **_kwargs: object) -> bool:
        return provider.slug != "openai-codex"

    monkeypatch.setattr(_model_choices, "provider_is_accessible", accessible)

    choices = _model_choices.configured_model_choices(pc)

    assert all(slug != "openai-codex" for slug, _model, _display, _free in choices)
    assert any(slug == "pollinations" for slug, _model, _display, _free in choices)


def test_switch_model_rejects_inaccessible_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pc = default_config()
    pc.set_active("openai-codex")
    pc.providers["openai-codex"].current_model = "gpt-5.5"
    session = ChatSession(
        config=ChatConfig(base_url="https://api.openai.com/v1", model="openai"),
        conversation=Conversation(),
        session_id="session-1",
    )

    monkeypatch.setattr(
        _model_selection.ProviderConfig,
        "load",
        classmethod(lambda _cls: pc),
    )
    monkeypatch.setattr(
        _model_selection,
        "provider_is_accessible",
        lambda _provider, **_kwargs: False,
    )

    assert not _model_selection.switch_model(session, "openai-codex", "gpt-5.5")
    assert session.config.model == "openai"


def test_switch_model_starts_local_llama_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = LlamaCppModelRecord(
        model_id="llama-cpp/acme/model:Q4_K_M",
        repo_id="acme/model",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )
    server = LlamaCppServerState(
        pid=123,
        endpoint="http://127.0.0.1:18124/v1",
        model_id=record.model_id,
        started_at=1.0,
    )
    pc = default_config()
    provider = pc.providers[LLAMA_CPP_PROVIDER_SLUG]
    provider.models = [record.model_id]
    provider.endpoint = record.endpoint
    session = ChatSession(
        config=ChatConfig(base_url="", model=""),
        conversation=Conversation(),
        session_id="session-1",
    )

    monkeypatch.setattr(
        _model_selection.ProviderConfig,
        "load",
        classmethod(lambda _cls: pc),
    )
    monkeypatch.setattr(_model_selection.ProviderConfig, "save", lambda _self: None)
    monkeypatch.setattr(
        _model_selection,
        "hydrate_provider_models",
        lambda _pc, *, provider_slugs: None,
    )
    monkeypatch.setattr(
        _model_selection.llama_cpp,
        "model_record",
        lambda model: record if model == record.model_id else None,
    )
    monkeypatch.setattr(_model_selection.llama_cpp, "start_record", lambda _record: server)

    assert _model_selection.switch_model(session, LLAMA_CPP_PROVIDER_SLUG, record.model_id)
    assert provider.endpoint == server.endpoint
    assert provider.current_model == record.model_id
    assert session.config.base_url == server.endpoint
    assert session.config.model == record.model_id
    assert session.config.provider_slug == LLAMA_CPP_PROVIDER_SLUG


def test_switch_model_hydrates_local_llama_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = LlamaCppModelRecord(
        model_id="llama-cpp/acme/model:Q4_K_M",
        repo_id="acme/model",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )
    server = LlamaCppServerState(
        pid=123,
        endpoint="http://127.0.0.1:18124/v1",
        model_id=record.model_id,
        started_at=1.0,
    )
    pc = default_config()
    provider = pc.providers[LLAMA_CPP_PROVIDER_SLUG]
    session = ChatSession(
        config=ChatConfig(base_url="", model=""),
        conversation=Conversation(),
        session_id="session-1",
    )
    hydrated_slugs: list[set[str]] = []

    def fake_hydrate_provider_models(
        config: ProviderConfig,
        *,
        provider_slugs: set[str] | None = None,
    ) -> None:
        hydrated_slugs.append(set(provider_slugs or ()))
        config.providers[LLAMA_CPP_PROVIDER_SLUG].models = [record.model_id]

    monkeypatch.setattr(
        _model_selection.ProviderConfig,
        "load",
        classmethod(lambda _cls: pc),
    )
    monkeypatch.setattr(_model_selection.ProviderConfig, "save", lambda _self: None)
    monkeypatch.setattr(
        _model_selection,
        "hydrate_provider_models",
        fake_hydrate_provider_models,
    )
    monkeypatch.setattr(
        _model_selection.llama_cpp,
        "model_record",
        lambda model: record if model == record.model_id else None,
    )
    monkeypatch.setattr(_model_selection.llama_cpp, "start_record", lambda _record: server)

    assert _model_selection.switch_model(session, LLAMA_CPP_PROVIDER_SLUG, record.model_id)
    assert hydrated_slugs == [{LLAMA_CPP_PROVIDER_SLUG}]
    assert provider.endpoint == server.endpoint
    assert provider.current_model == record.model_id
    assert session.config.base_url == server.endpoint
    assert session.config.model == record.model_id
    assert session.config.provider_slug == LLAMA_CPP_PROVIDER_SLUG


def test_ensure_session_model_ready_starts_saved_local_llama_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = LlamaCppModelRecord(
        model_id="llama-cpp/acme/model:Q4_K_M",
        repo_id="acme/model",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )
    server = LlamaCppServerState(
        pid=123,
        endpoint="http://127.0.0.1:18124/v1",
        model_id=record.model_id,
        started_at=1.0,
    )
    pc = default_config()
    provider = pc.providers[LLAMA_CPP_PROVIDER_SLUG]
    provider.models = [record.model_id]
    provider.current_model = record.model_id
    provider.endpoint = record.endpoint
    pc.set_active(LLAMA_CPP_PROVIDER_SLUG)
    session = ChatSession(
        config=ChatConfig(base_url=record.endpoint, model=record.model_id),
        conversation=Conversation(),
        session_id="session-1",
    )

    monkeypatch.setattr(
        _model_selection.ProviderConfig,
        "load",
        classmethod(lambda _cls: pc),
    )
    monkeypatch.setattr(_model_selection.ProviderConfig, "save", lambda _self: None)
    monkeypatch.setattr(
        _model_selection,
        "hydrate_provider_models",
        lambda _pc, *, provider_slugs: None,
    )
    monkeypatch.setattr(
        _model_selection.llama_cpp,
        "model_record",
        lambda model: record if model == record.model_id else None,
    )
    monkeypatch.setattr(_model_selection.llama_cpp, "start_record", lambda _record: server)

    assert _model_selection.ensure_session_model_ready(session)
    assert provider.endpoint == server.endpoint
    assert session.config.base_url == server.endpoint
    assert session.config.model == record.model_id
    assert session.config.provider_slug == LLAMA_CPP_PROVIDER_SLUG


def test_ensure_session_model_ready_ignores_remote_session_with_active_local_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pc = default_config()
    provider = pc.providers[LLAMA_CPP_PROVIDER_SLUG]
    provider.models = ["llama-cpp/acme/model:Q4_K_M"]
    provider.current_model = "llama-cpp/acme/model:Q4_K_M"
    pc.set_active(LLAMA_CPP_PROVIDER_SLUG)
    config = ChatConfig(base_url="https://api.openai.com/v1", model="gpt-5.5")
    config.apply_provider_reference("openai", "OPENAI_API_KEY")
    session = ChatSession(
        config=config,
        conversation=Conversation(),
        session_id="session-1",
    )

    monkeypatch.setattr(
        _model_selection.ProviderConfig,
        "load",
        classmethod(lambda _cls: pc),
    )
    monkeypatch.setattr(
        _model_selection,
        "hydrate_provider_models",
        lambda _pc, *, provider_slugs: pytest.fail(
            "remote sessions must not hydrate local models"
        ),
    )
    monkeypatch.setattr(
        _model_selection.llama_cpp,
        "start_record",
        lambda _record: pytest.fail("remote sessions must not start llama.cpp"),
    )

    assert _model_selection.ensure_session_model_ready(session)
    assert session.config.base_url == "https://api.openai.com/v1"
    assert session.config.model == "gpt-5.5"
    assert session.config.provider_slug == "openai"


def test_ensure_session_model_ready_ignores_remote_override_after_local_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = ChatConfig(base_url="https://example.test/v1", model="custom-model")
    config.apply_provider_reference(LLAMA_CPP_PROVIDER_SLUG, "")
    session = ChatSession(
        config=config,
        conversation=Conversation(),
        session_id="session-1",
    )

    monkeypatch.setattr(
        _model_selection.ProviderConfig,
        "load",
        classmethod(lambda _cls: pytest.fail("remote overrides must not load provider config")),
    )

    assert _model_selection.ensure_session_model_ready(session)
    assert session.config.base_url == "https://example.test/v1"
    assert session.config.model == "custom-model"
    assert session.config.provider_slug == LLAMA_CPP_PROVIDER_SLUG


def test_local_command_activates_tool_capable_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(ChatConfig(base_url="", model=""))
    candidate = LlamaCppCandidate(
        repo_id="acme/model",
        filename="model-Q4_K_M.gguf",
        quant="Q4_K_M",
        downloads=0,
        likes=0,
        size_bytes=2_497_280_256,
        display_name="Acme Model",
        recommended_ram_gb=8,
    )
    record = LlamaCppModelRecord(
        model_id="llama-cpp/acme/model:Q4_K_M",
        repo_id="acme/model",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )
    result = LlamaCppInstallResult(
        record=record,
        capability=ToolCapabilityResult(True),
        server=LlamaCppServerState(
            pid=123,
            endpoint=record.endpoint,
            model_id=record.model_id,
            started_at=1.0,
        ),
    )
    activated: list[tuple[str, str]] = []

    monkeypatch.setattr(_commands_local, "find_hf_candidate", lambda _target: candidate)
    monkeypatch.setattr(_commands_local, "confirm", lambda _title, default=False: True)
    monkeypatch.setattr(_commands_local, "install_local_target", lambda _target: result)
    monkeypatch.setattr(
        _commands_local,
        "activate_local_record",
        lambda installed, active_session: activated.append(
            (installed.model_id, active_session.session_id)
        ),
    )

    commands.LocalCommand().handle(session, "install acme/model:Q4_K_M")

    assert activated == [(record.model_id, session.session_id)]


def test_local_command_search_descriptions_use_label_value_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(ChatConfig(base_url="", model=""))
    candidate = LlamaCppCandidate(
        repo_id="acme/model",
        filename="model-Q4_K_M.gguf",
        quant="Q4_K_M",
        downloads=0,
        likes=0,
        size_bytes=2_497_280_256,
        display_name="Acme Model",
        recommended_ram_gb=8,
    )
    visible_options: list[MenuOption] = []

    def capture_options(_title: str, options: list[MenuOption]) -> None:
        visible_options.extend(options)

    monkeypatch.setattr(_commands_local, "search_gguf_models", lambda _query, limit: [candidate])
    monkeypatch.setattr(_commands_local, "select_option", capture_options)
    monkeypatch.setattr(_commands_local, "print_info", lambda _message: None)

    commands.LocalCommand().handle(session, "qwen")

    assert visible_options[0].description == "QUANT q4_k_m  SIZE 2.3 gb  RAM 8 gb"


def test_local_command_keeps_failed_probe_unselectable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(ChatConfig(base_url="", model=""))
    candidate = LlamaCppCandidate(
        repo_id="acme/model",
        filename="model-Q4_K_M.gguf",
        quant="Q4_K_M",
        downloads=0,
        likes=0,
        size_bytes=2_497_280_256,
        display_name="Acme Model",
        recommended_ram_gb=8,
    )
    record = LlamaCppModelRecord(
        model_id="llama-cpp/acme/model:Q4_K_M",
        repo_id="acme/model",
        quant="Q4_K_M",
        tool_capable=False,
        endpoint="http://127.0.0.1:18123/v1",
    )
    result = LlamaCppInstallResult(
        record=record,
        capability=ToolCapabilityResult(False, "model did not return a tool call"),
        server=LlamaCppServerState(
            pid=123,
            endpoint=record.endpoint,
            model_id=record.model_id,
            started_at=1.0,
        ),
    )
    messages: list[str] = []

    monkeypatch.setattr(_commands_local, "find_hf_candidate", lambda _target: candidate)
    monkeypatch.setattr(_commands_local, "confirm", lambda _title, default=False: True)
    monkeypatch.setattr(_commands_local, "install_local_target", lambda _target: result)
    monkeypatch.setattr(
        _commands_local,
        "activate_local_record",
        lambda _record, _session: messages.append("activated"),
    )
    monkeypatch.setattr(_commands_local, "print_error", messages.append)

    commands.LocalCommand().handle(session, "install acme/model:Q4_K_M")

    assert messages == [
        "Local model installed but not activated because the tool-call probe failed: "
        "model did not return a tool call"
    ]


def test_local_command_cancel_does_not_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_plain_session(ChatConfig(base_url="", model=""))
    candidate = LlamaCppCandidate(
        repo_id="acme/model",
        filename="model-Q4_K_M.gguf",
        quant="Q4_K_M",
        downloads=0,
        likes=0,
        size_bytes=2_497_280_256,
        display_name="Acme Model",
        recommended_ram_gb=8,
    )
    messages: list[str] = []
    installs: list[str] = []

    monkeypatch.setattr(_commands_local, "find_hf_candidate", lambda _target: candidate)
    monkeypatch.setattr(_commands_local, "confirm", lambda _title, default=False: False)
    monkeypatch.setattr(_commands_local, "install_local_target", installs.append)
    monkeypatch.setattr(_commands_local, "print_info", messages.append)

    commands.LocalCommand().handle(session, "install acme/model:Q4_K_M")

    assert installs == []
    assert messages == ["Cancelled."]


def test_local_command_status_prints_revalidatable_model_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(base_url="", model=""))
    record = LlamaCppModelRecord(
        model_id="llama-cpp/Qwen/Qwen3-4B-GGUF:Q4_K_M",
        repo_id="Qwen/Qwen3-4B-GGUF",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )

    monkeypatch.setattr(_commands_local, "current_server_state", lambda: None)
    monkeypatch.setattr(_commands_local, "installed_records", lambda: [record])

    commands.LocalCommand().handle(session, "status")

    out = capsys.readouterr().out
    assert "Qwen3 4B" in out
    assert "MODEL llama-cpp/Qwen/Qwen3-4B-GGUF:Q4_K_M" in out


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


def test_evidence_command_escapes_terminal_controls(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    armory = tmp_path / "evidence-armory"
    initialize(armory)
    source = armory / "materials" / "notes.md"
    text = "Safe text \x1b[31mnot a terminal command.\n"
    source.write_text(text, encoding="utf-8")
    chunk = Chunk(
        text=text.strip(),
        source="materials/notes.md",
        index=0,
        char_start=0,
        char_end=len(text),
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

    commands.EvidenceCommand().handle(session, "E1")

    out = capsys.readouterr().out
    assert "\x1b" not in out
    assert "\\x1b[31mnot a terminal command" in out


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


def test_compact_command_empty_session(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))

    commands.CompactCommand().handle(session, "")
    out = capsys.readouterr().out
    assert "Nothing to compact" in out


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
