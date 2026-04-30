from __future__ import annotations

from pathlib import Path

from scripts import sync_docs


def test_replace_managed_block_updates_named_section() -> None:
    text = "\n".join(
        [
            "before",
            "<!-- sync-docs:demo:start -->",
            "old content",
            "<!-- sync-docs:demo:end -->",
            "after",
        ]
    )

    updated = sync_docs.replace_managed_block(text, "demo", "new content")

    assert updated == "\n".join(
        [
            "before",
            "<!-- sync-docs:demo:start -->",
            "new content",
            "<!-- sync-docs:demo:end -->",
            "after",
        ]
    )


def test_lint_legacy_commands_flags_stale_refs(tmp_path: Path) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text(
        "Use `heph start` if you want to launch the shell.\nThen run `heph source reindex`.\n",
        encoding="utf-8",
    )

    errors = sync_docs.lint_legacy_commands(tmp_path)

    assert any("heph` or `heph <path>`" in error for error in errors)
    assert any("materials index" in error for error in errors)


def test_collect_docs_model_reads_live_surfaces() -> None:
    model = sync_docs.collect_docs_model(sync_docs.ROOT)

    assert model.short_command == "heph"
    assert any(
        command.command == "heph materials index <path>"
        for command in model.cli_reference_commands
    )
    assert any(
        command.command == "heph source index <path>" for command in model.cli_reference_commands
    )
    assert not any("reindex" in command.command for command in model.cli_reference_commands)
    assert any(command.command == "/vocab" for command in model.slash_commands)
    assert any(env.name == "HEPHAISTOS_POSTHOG_PROJECT_TOKEN" for env in model.env_vars)


def test_repository_docs_are_synced() -> None:
    targets = sync_docs.render_targets(sync_docs.ROOT)

    for target in targets:
        assert target.path.read_text(encoding="utf-8") == target.content
