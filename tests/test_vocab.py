"""Tests for vocabulary drill system: parser, scheduler, state, and integration."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hephaion.parameters.settings import VOCAB_STRICTNESS_LENIENT, AppSettings
from hephaion.vocab import drill
from hephaion.vocab.parser import (
    VocabCard,
    parse_vocab_file,
    scan_armory,
)
from hephaion.vocab.scheduler import (
    Rating,
    schedule_card,
    select_due_cards,
)
from hephaion.vocab.state import (
    VocabCardState,
    VocabScheduleStore,
    load_schedule,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vocab_armory(tmp_path: Path) -> Path:
    """Create an armory with vocabulary markdown files."""
    arm = tmp_path / "vocab-armory"
    (arm / "materials").mkdir(parents=True)
    (arm / ".hephaion").mkdir(parents=True)

    (arm / "materials" / "french.md").write_text(
        "# French Vocabulary\n\n"
        "| word | translation |\n"
        "|------|-------------|\n"
        "| Bonjour | Hello |\n"
        "| Merci | Thank you |\n"
        "| Au revoir | Goodbye |\n"
        "| Oui | Yes |\n",
        encoding="utf-8",
    )

    (arm / "materials" / "german.md").write_text(
        "# German Words\n\n"
        "| front | back |\n"
        "|-------|------|\n"
        "| Hallo | Hello |\n"
        "| Danke | Thanks |\n",
        encoding="utf-8",
    )

    # A non-vocab file (no matching table headers).
    (arm / "materials" / "notes.md").write_text(
        "# Notes\n\n| topic | detail |\n|-------|--------|\n| Math | Algebra |\n",
        encoding="utf-8",
    )

    return arm


@pytest.fixture
def empty_armory(tmp_path: Path) -> Path:
    """Create an armory with no vocab files."""
    arm = tmp_path / "empty-armory"
    (arm / "materials").mkdir(parents=True)
    (arm / ".hephaion").mkdir(parents=True)
    (arm / "materials" / "notes.md").write_text("# Just notes\n\nNo tables here.\n")
    return arm


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestVocabParser:
    def test_parse_vocab_file_word_translation(self, vocab_armory: Path) -> None:
        cards = parse_vocab_file(vocab_armory / "materials" / "french.md", vocab_armory)
        assert len(cards) == 4
        assert cards[0].front == "Bonjour"
        assert cards[0].back == "Hello"
        assert cards[0].source_file == "materials/french.md"

    def test_parse_vocab_file_front_back(self, vocab_armory: Path) -> None:
        cards = parse_vocab_file(vocab_armory / "materials" / "german.md", vocab_armory)
        assert len(cards) == 2
        assert cards[0].front == "Hallo"
        assert cards[0].back == "Hello"

    def test_non_vocab_file_not_parsed(self, vocab_armory: Path) -> None:
        cards = parse_vocab_file(vocab_armory / "materials" / "notes.md", vocab_armory)
        assert len(cards) == 0

    def test_scan_armory_finds_all_vocab(self, vocab_armory: Path) -> None:
        deck = scan_armory(vocab_armory)
        assert deck.size == 6  # 4 French + 2 German
        assert len(deck.source_files) == 2

    def test_scan_armory_empty(self, empty_armory: Path) -> None:
        deck = scan_armory(empty_armory)
        assert deck.size == 0

    def test_scan_armory_no_dirs(self, tmp_path: Path) -> None:
        arm = tmp_path / "bare-armory"
        arm.mkdir()
        (arm / ".hephaion").mkdir()
        deck = scan_armory(arm)
        assert deck.size == 0

    def test_term_definition_columns(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaion").mkdir()
        (arm / "materials" / "glossary.md").write_text(
            "| term | definition |\n"
            "|------|------------|\n"
            "| API | Application Programming Interface |\n"
            "| SDK | Software Development Kit |\n",
        )
        cards = parse_vocab_file(arm / "materials" / "glossary.md", arm)
        assert len(cards) == 2
        assert cards[0].front == "API"

    def test_source_target_columns(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaion").mkdir()
        (arm / "materials" / "spanish.md").write_text(
            "| source | target |\n|--------|--------|\n| Hola | Hello |\n",
        )
        cards = parse_vocab_file(arm / "materials" / "spanish.md", arm)
        assert len(cards) == 1
        assert cards[0].front == "Hola"

    def test_skips_empty_cells(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaion").mkdir()
        (arm / "materials" / "sparse.md").write_text(
            "| word | translation |\n"
            "|------|-------------|\n"
            "| Hello |  |\n"
            "|  | World |\n"
            "| Foo | Bar |\n",
        )
        cards = parse_vocab_file(arm / "materials" / "sparse.md", arm)
        assert len(cards) == 1
        assert cards[0].front == "Foo"

    def test_multiple_tables_in_one_file(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaion").mkdir()
        (arm / "materials" / "multi.md").write_text(
            "# Part 1\n\n"
            "| word | translation |\n"
            "|------|-------------|\n"
            "| One | Eins |\n\n"
            "# Part 2\n\n"
            "| front | back |\n"
            "|-------|------|\n"
            "| Two | Zwei |\n",
        )
        cards = parse_vocab_file(arm / "materials" / "multi.md", arm)
        assert len(cards) == 2


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------


class TestScheduler:
    def _make_card(self, **overrides: object) -> VocabCardState:
        defaults: dict[str, object] = {
            "front": "test",
            "back": "answer",
            "source_file": "materials/test.md",
            "repetitions": 0,
            "easiness": 2.5,
            "interval": 0,
        }
        defaults.update(overrides)
        return VocabCardState(**defaults)  # ty:ignore[invalid-argument-type]

    def test_new_card_good_first_review(self) -> None:
        card = self._make_card()
        result = schedule_card(card, Rating.GOOD)
        # First review with GOOD: repetitions -> 1, interval = 1 day
        assert result.repetitions == 1
        assert result.interval_days == 1
        assert abs(result.easiness - 2.5) <= 0.01

    def test_new_card_easy_first_review(self) -> None:
        card = self._make_card()
        result = schedule_card(card, Rating.EASY)
        # First review with EASY: repetitions -> 1, interval = 1 day, ease up
        assert result.repetitions == 1
        assert result.interval_days == 1
        assert result.easiness > 2.5

    def test_second_review_good(self) -> None:
        card = self._make_card(repetitions=1, interval=1)
        result = schedule_card(card, Rating.GOOD)
        # Second review: repetitions -> 2, interval = 6 days
        assert result.repetitions == 2
        assert result.interval_days == 6

    def test_third_review_good(self) -> None:
        card = self._make_card(repetitions=2, interval=6, easiness=2.5)
        result = schedule_card(card, Rating.GOOD)
        # Third review: repetitions -> 3, interval = round(6 * 2.5) = 15
        assert result.repetitions == 3
        assert result.interval_days == 15

    def test_hard_decreases_easiness(self) -> None:
        card = self._make_card(repetitions=2, interval=6, easiness=2.5)
        result = schedule_card(card, Rating.HARD)
        assert result.easiness < 2.5
        assert result.easiness >= 1.3

    def test_easy_increases_easiness(self) -> None:
        card = self._make_card(repetitions=2, interval=6, easiness=2.5)
        result = schedule_card(card, Rating.EASY)
        assert result.easiness > 2.5

    def test_easiness_floor_at_1_3(self) -> None:
        card = self._make_card(repetitions=5, interval=100, easiness=1.3)
        result = schedule_card(card, Rating.HARD)
        assert result.easiness >= 1.3

    def test_max_interval_capped(self) -> None:
        card = self._make_card(repetitions=10, interval=300, easiness=2.5)
        result = schedule_card(card, Rating.GOOD)
        assert result.interval_days <= 365

    def test_interval_at_least_one_day(self) -> None:
        card = self._make_card(repetitions=1, interval=1, easiness=1.3)
        result = schedule_card(card, Rating.HARD)
        assert result.interval_days >= 1

    def test_sm2_easiness_formula(self) -> None:
        """Verify the exact SM-2 easiness formula for quality=3 (Hard)."""
        card = self._make_card(easiness=2.5)
        result = schedule_card(card, Rating.HARD)  # quality=3
        # EF' = 2.5 + 0.1 - (5-3)*(0.08 + (5-3)*0.02) = 2.5 + 0.1 - 2*(0.08+0.04)
        # = 2.5 + 0.1 - 0.24 = 2.36
        assert abs(result.easiness - 2.36) <= 0.01

    def test_sm2_easiness_formula_easy(self) -> None:
        """Verify the exact SM-2 easiness formula for quality=5 (Easy)."""
        card = self._make_card(easiness=2.5)
        result = schedule_card(card, Rating.EASY)  # quality=5
        # EF' = 2.5 + 0.1 - (5-5)*(0.08 + (5-5)*0.02) = 2.5 + 0.1 - 0 = 2.6
        assert abs(result.easiness - 2.6) <= 0.01


class TestSelectDueCards:
    def test_new_cards_are_due(self) -> None:
        cards = [
            VocabCardState(front="a", back="b", source_file="test.md"),
            VocabCardState(front="c", back="d", source_file="test.md"),
        ]
        due = select_due_cards(cards)
        assert len(due) == 2

    def test_future_cards_not_due(self) -> None:
        future = datetime.now(UTC) + timedelta(days=5)
        cards = [
            VocabCardState(front="a", back="b", source_file="test.md", next_review=future),
        ]
        due = select_due_cards(cards)
        assert len(due) == 0

    def test_overdue_cards_are_due(self) -> None:
        past = datetime.now(UTC) - timedelta(days=2)
        cards = [
            VocabCardState(front="a", back="b", source_file="test.md", next_review=past),
        ]
        due = select_due_cards(cards)
        assert len(due) == 1

    def test_overdue_before_new(self) -> None:
        past = datetime.now(UTC) - timedelta(days=2)
        cards = [
            VocabCardState(front="new", back="n", source_file="test.md"),
            VocabCardState(front="old", back="o", source_file="test.md", next_review=past),
        ]
        due = select_due_cards(cards)
        assert len(due) == 2
        assert due[0].front == "old"  # Overdue first.

    def test_limit(self) -> None:
        cards = [VocabCardState(front=f"w{i}", back="b", source_file="test.md") for i in range(10)]
        due = select_due_cards(cards, limit=3)
        assert len(due) == 3

    def test_empty_list(self) -> None:
        assert select_due_cards([]) == []


# ---------------------------------------------------------------------------
# State persistence tests
# ---------------------------------------------------------------------------


class TestVocabCardState:
    def test_key_generation(self) -> None:
        state = VocabCardState(front="Hello", back="Bonjour", source_file="materials/vocab.md")
        assert state.key == "materials/vocab.md:Hello"

    def test_is_new(self) -> None:
        new = VocabCardState(front="a", back="b", source_file="test.md")
        assert new.is_new
        reviewed = VocabCardState(front="a", back="b", source_file="test.md", repetitions=1)
        assert not reviewed.is_new

    def test_round_trip_serialization(self) -> None:
        original = VocabCardState(
            front="Bonjour",
            back="Hello",
            source_file="materials/vocab.md",
            repetitions=3,
            easiness=2.36,
            interval=15,
            last_review=datetime(2026, 4, 22, 10, 0, 0, tzinfo=UTC),
            next_review=datetime(2026, 5, 7, 10, 0, 0, tzinfo=UTC),
        )
        d = original.to_dict()
        restored = VocabCardState.from_dict(d)
        assert restored.front == original.front
        assert restored.back == original.back
        assert restored.repetitions == original.repetitions
        assert restored.easiness == original.easiness
        assert restored.interval == original.interval

    def test_from_card(self) -> None:
        card = VocabCard(front="Hello", back="Bonjour", source_file="materials/v.md")
        state = VocabCardState.from_card(card)
        assert state.front == "Hello"
        assert state.back == "Bonjour"
        assert state.is_new


class TestVocabScheduleStore:
    def test_save_and_load(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / ".hephaion").mkdir(parents=True)

        store = VocabScheduleStore(arm)
        store.cards["test.md:Hello"] = VocabCardState(
            front="Hello", back="World", source_file="test.md", repetitions=2
        )
        store.save()

        loaded = VocabScheduleStore(arm)
        assert loaded.load()
        assert len(loaded.cards) == 1
        assert loaded.cards["test.md:Hello"].repetitions == 2

    def test_sync_with_deck(self, vocab_armory: Path) -> None:
        deck = scan_armory(vocab_armory)
        store = VocabScheduleStore(vocab_armory)
        added = store.sync_with_deck(deck)
        assert added == 6
        assert len(store.cards) == 6

        # Syncing again doesn't add duplicates.
        added2 = store.sync_with_deck(deck)
        assert added2 == 0

    def test_sync_with_deck_updates_and_removes_stale_cards(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaion").mkdir(parents=True)

        vocab_file = arm / "materials" / "vocab.md"
        vocab_file.write_text(
            "| word | translation |\n"
            "|------|-------------|\n"
            "| Hello | Bonjour |\n"
            "| Goodbye | Au revoir |\n",
            encoding="utf-8",
        )

        store = VocabScheduleStore(arm)
        assert store.sync_with_deck(scan_armory(arm)) == 2

        hello = store.cards["materials/vocab.md:Hello"]
        hello.repetitions = 3
        hello.easiness = 2.7
        hello.interval = 12
        store.update_card(hello)

        vocab_file.write_text(
            "| word | translation |\n"
            "|------|-------------|\n"
            "| Hello | Salut |\n"
            "| Thanks | Merci |\n",
            encoding="utf-8",
        )

        added = store.sync_with_deck(scan_armory(arm))
        assert added == 1
        assert set(store.cards) == {"materials/vocab.md:Hello", "materials/vocab.md:Thanks"}

        updated_hello = store.cards["materials/vocab.md:Hello"]
        assert updated_hello.back == "Salut"
        assert updated_hello.repetitions == 3
        assert updated_hello.easiness == 2.7
        assert updated_hello.interval == 12

    def test_update_card(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / ".hephaion").mkdir(parents=True)

        store = VocabScheduleStore(arm)
        state = VocabCardState(front="Hello", back="World", source_file="test.md")
        store.update_card(state)

        updated = VocabCardState(
            front="Hello",
            back="World",
            source_file="test.md",
            repetitions=3,
            easiness=2.5,
            interval=15,
        )
        store.update_card(updated)
        assert store.cards["test.md:Hello"].repetitions == 3

    def test_reset_all(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / ".hephaion").mkdir(parents=True)

        store = VocabScheduleStore(arm)
        state = VocabCardState(
            front="Hello",
            back="World",
            source_file="test.md",
            repetitions=5,
            easiness=2.0,
            interval=30,
            last_review=datetime.now(UTC),
            next_review=datetime.now(UTC) + timedelta(days=30),
        )
        store.cards["test.md:Hello"] = state
        store.reset_all()

        reset = store.cards["test.md:Hello"]
        assert reset.repetitions == 0
        assert reset.easiness == 2.5
        assert reset.interval == 0
        assert reset.last_review is None
        assert reset.next_review is None

    def test_stats(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / ".hephaion").mkdir(parents=True)

        store = VocabScheduleStore(arm)
        store.cards["a"] = VocabCardState(front="a", back="b", source_file="t.md")
        store.cards["b"] = VocabCardState(
            front="b",
            back="c",
            source_file="t.md",
            repetitions=3,
            next_review=datetime.now(UTC) - timedelta(hours=1),
        )
        store.cards["c"] = VocabCardState(
            front="c",
            back="d",
            source_file="t.md",
            repetitions=7,
            next_review=datetime.now(UTC) + timedelta(days=30),
        )
        stats = store.stats()
        assert stats["total"] == 3
        assert stats["new"] == 1  # Only "a" (rep=0)
        assert stats["due"] == 2  # "a" (new) + "b" (overdue)
        assert stats["mastered"] == 1  # "c" with rep >= 5

    def test_load_schedule_helper(self, tmp_path: Path) -> None:
        arm = tmp_path / "arm"
        (arm / ".hephaion").mkdir(parents=True)
        store = load_schedule(arm)
        assert len(store.cards) == 0


# ---------------------------------------------------------------------------
# Integration: full drill scheduling flow
# ---------------------------------------------------------------------------


class TestAnswerMatching:
    def test_strict_matching_rejects_missing_punctuation(self) -> None:
        assert not drill._answer_matches("dont", "don't")

    def test_lenient_matching_accepts_missing_punctuation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            drill,
            "load_app_settings",
            lambda: AppSettings(vocab_strictness=VOCAB_STRICTNESS_LENIENT),
        )

        assert drill._answer_matches("dont", "don't")


class TestDrillIntegration:
    def test_full_scheduling_cycle(self, vocab_armory: Path) -> None:
        """Simulate a full scheduling cycle without the interactive TUI."""
        deck = scan_armory(vocab_armory)
        assert deck.size == 6

        store = VocabScheduleStore(vocab_armory)
        added = store.sync_with_deck(deck)
        assert added == 6

        # All cards should be due (new).
        due = select_due_cards(store.card_list)
        assert len(due) == 6

        # Drill a few cards.
        card = due[0]
        result = schedule_card(card, Rating.GOOD)
        card.repetitions = result.repetitions
        card.easiness = result.easiness
        card.interval = result.interval_days
        card.last_review = datetime.now(UTC)
        card.next_review = datetime.now(UTC) + timedelta(days=result.interval_days)
        store.update_card(card)

        assert card.repetitions == 1
        assert card.interval >= 1

        # Save and reload.
        store.save()
        loaded = VocabScheduleStore(vocab_armory)
        loaded.load()
        assert len(loaded.cards) == 6

        # The drilled card should now have a future review date.
        reloaded_card = loaded.cards[card.key]
        assert reloaded_card.repetitions == 1
        assert reloaded_card.next_review is not None

        # Remaining due count should have decreased.
        remaining = select_due_cards(loaded.card_list)
        assert len(remaining) == 5

    def test_spaced_repetition_progression(self) -> None:
        """Verify interval growth over successive GOOD reviews."""
        card = VocabCardState(front="test", back="answer", source_file="test.md")
        intervals: list[int] = []

        for _ in range(5):
            result = schedule_card(card, Rating.GOOD)
            card.repetitions = result.repetitions
            card.easiness = result.easiness
            card.interval = result.interval_days
            intervals.append(result.interval_days)

        # Expected intervals: 1, 6, 15, 37, 93 (approx, with EF=2.5)
        assert intervals[0] == 1
        assert intervals[1] == 6
        assert intervals[2] == 15
        assert intervals[3] > 15
        assert intervals[4] > intervals[3]

    def test_hard_resets_to_short_interval(self) -> None:
        """After several reviews, a Hard rating should give a short interval."""
        card = VocabCardState(
            front="test",
            back="answer",
            source_file="test.md",
            repetitions=5,
            easiness=2.5,
            interval=50,
        )
        result = schedule_card(card, Rating.HARD)
        # Hard still increments repetitions (quality=3 >= 3).
        assert result.repetitions == 6
        # But interval should be modest (50 * updated_ease ~= 50 * 2.36 = 118).
        # Actually it's just interval * new_ease, so it's still long.
        # Hard doesn't reset like "Again" would.
        assert result.easiness < 2.5

    def test_json_file_structure(self, tmp_path: Path) -> None:
        """Verify the saved JSON file has the expected structure."""
        arm = tmp_path / "arm"
        (arm / "materials").mkdir(parents=True)
        (arm / ".hephaion").mkdir(parents=True)

        (arm / "materials" / "vocab.md").write_text(
            "| word | translation |\n"
            "|------|-------------|\n"
            "| Hello | Bonjour |\n"
            "| Goodbye | Au revoir |\n",
        )

        deck = scan_armory(arm)
        store = VocabScheduleStore(arm)
        store.sync_with_deck(deck)
        assert len(store.cards) == 2

        card = next(iter(store.cards.values()))
        result = schedule_card(card, Rating.GOOD)
        card.repetitions = result.repetitions
        card.easiness = result.easiness
        card.interval = result.interval_days
        card.last_review = datetime.now(UTC)
        card.next_review = datetime.now(UTC) + timedelta(days=result.interval_days)
        store.update_card(card)
        store.save()

        data = json.loads((arm / ".hephaion" / "vocab_schedule.json").read_text())
        assert data["version"] == 1
        assert "updated_at" in data
        assert len(data["cards"]) == 2

        # Check one card's structure.
        first_card = next(iter(data["cards"].values()))
        assert "front" in first_card
        assert "back" in first_card
        assert "repetitions" in first_card
        assert "easiness" in first_card
        assert "interval" in first_card
