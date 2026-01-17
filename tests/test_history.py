"""Tests for transcription history module."""

import json
import tempfile
from pathlib import Path

from src.history import TranscriptionEntry, TranscriptionHistory


class TestTranscriptionEntry:
    """Tests for TranscriptionEntry dataclass."""

    def test_should_create_entry_with_required_fields(self) -> None:
        """Test entry creation with only required fields."""
        entry = TranscriptionEntry(
            text="Hello world",
            timestamp="2024-01-15T10:30:00",
        )
        assert entry.text == "Hello world"
        assert entry.timestamp == "2024-01-15T10:30:00"
        assert entry.language is None
        assert entry.audio_duration is None
        assert entry.transcription_time is None

    def test_should_create_entry_with_all_fields(self) -> None:
        """Test entry creation with all fields."""
        entry = TranscriptionEntry(
            text="Bonjour monde",
            timestamp="2024-01-15T10:30:00",
            language="fr",
            audio_duration=5.5,
            transcription_time=1.2,
        )
        assert entry.text == "Bonjour monde"
        assert entry.language == "fr"
        assert entry.audio_duration == 5.5
        assert entry.transcription_time == 1.2


class TestTranscriptionHistory:
    """Tests for TranscriptionHistory class."""

    class TestInitialization:
        """Tests for history initialization."""

        def test_should_initialize_empty_history(self) -> None:
            """Test empty history initialization."""
            history = TranscriptionHistory()
            assert len(history) == 0
            assert history.entries == []

        def test_should_initialize_with_custom_max_entries(self) -> None:
            """Test initialization with custom max entries."""
            history = TranscriptionHistory(max_entries=50)
            assert history.max_entries == 50

        def test_should_load_from_file_if_exists(self) -> None:
            """Test loading history from existing file."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(
                    {
                        "entries": [
                            {
                                "text": "Test entry",
                                "timestamp": "2024-01-15T10:30:00",
                                "language": "en",
                                "audio_duration": None,
                                "transcription_time": None,
                            }
                        ]
                    },
                    f,
                )
                temp_path = f.name

            try:
                history = TranscriptionHistory(history_file=temp_path)
                assert len(history) == 1
                assert history.entries[0].text == "Test entry"
            finally:
                Path(temp_path).unlink()

        def test_should_handle_missing_file_gracefully(self) -> None:
            """Test that missing file doesn't raise error."""
            history = TranscriptionHistory(history_file="/nonexistent/path/history.json")
            assert len(history) == 0

        def test_should_handle_invalid_json_gracefully(self) -> None:
            """Test that invalid JSON doesn't raise error."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                f.write("invalid json {{{")
                temp_path = f.name

            try:
                history = TranscriptionHistory(history_file=temp_path)
                assert len(history) == 0
            finally:
                Path(temp_path).unlink()

    class TestAddEntry:
        """Tests for adding entries."""

        def test_should_add_entry_with_text_only(self) -> None:
            """Test adding entry with just text."""
            history = TranscriptionHistory(auto_save=False)
            entry = history.add(text="Hello")
            assert len(history) == 1
            assert entry.text == "Hello"
            assert entry.timestamp is not None

        def test_should_add_entry_with_all_metadata(self) -> None:
            """Test adding entry with all metadata."""
            history = TranscriptionHistory(auto_save=False)
            entry = history.add(
                text="Bonjour",
                language="fr",
                audio_duration=3.5,
                transcription_time=0.8,
            )
            assert entry.language == "fr"
            assert entry.audio_duration == 3.5
            assert entry.transcription_time == 0.8

        def test_should_trim_to_max_entries(self) -> None:
            """Test that history is trimmed to max entries."""
            history = TranscriptionHistory(max_entries=3, auto_save=False)
            history.add("Entry 1")
            history.add("Entry 2")
            history.add("Entry 3")
            history.add("Entry 4")

            assert len(history) == 3
            assert history.entries[0].text == "Entry 2"
            assert history.entries[2].text == "Entry 4"

        def test_should_auto_save_when_enabled(self) -> None:
            """Test that auto-save saves to file."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                temp_path = f.name

            try:
                history = TranscriptionHistory(history_file=temp_path, auto_save=True)
                history.add("Test entry")

                # Verify file was updated
                with open(temp_path, encoding="utf-8") as f:
                    data = json.load(f)
                assert len(data["entries"]) == 1
                assert data["entries"][0]["text"] == "Test entry"
            finally:
                Path(temp_path).unlink()

    class TestGetRecent:
        """Tests for getting recent entries."""

        def test_should_return_recent_entries_newest_first(self) -> None:
            """Test that recent entries are returned newest first."""
            history = TranscriptionHistory(auto_save=False)
            history.add("Entry 1")
            history.add("Entry 2")
            history.add("Entry 3")

            recent = history.get_recent(2)
            assert len(recent) == 2
            assert recent[0].text == "Entry 3"
            assert recent[1].text == "Entry 2"

        def test_should_return_all_if_fewer_than_requested(self) -> None:
            """Test return all entries if fewer than requested."""
            history = TranscriptionHistory(auto_save=False)
            history.add("Entry 1")

            recent = history.get_recent(10)
            assert len(recent) == 1

        def test_should_return_empty_for_empty_history(self) -> None:
            """Test empty list for empty history."""
            history = TranscriptionHistory(auto_save=False)
            recent = history.get_recent(5)
            assert recent == []

    class TestSearch:
        """Tests for search functionality."""

        def test_should_find_entries_containing_query(self) -> None:
            """Test that search finds matching entries."""
            history = TranscriptionHistory(auto_save=False)
            history.add("Hello world")
            history.add("Bonjour monde")
            history.add("Hello there")

            results = history.search("Hello")
            assert len(results) == 2

        def test_should_be_case_insensitive(self) -> None:
            """Test that search is case insensitive."""
            history = TranscriptionHistory(auto_save=False)
            history.add("HELLO WORLD")
            history.add("hello there")

            results = history.search("hello")
            assert len(results) == 2

        def test_should_respect_limit(self) -> None:
            """Test that search respects limit."""
            history = TranscriptionHistory(auto_save=False)
            for i in range(10):
                history.add(f"Test entry {i}")

            results = history.search("Test", limit=3)
            assert len(results) == 3

        def test_should_return_empty_for_no_matches(self) -> None:
            """Test empty results for no matches."""
            history = TranscriptionHistory(auto_save=False)
            history.add("Hello world")

            results = history.search("nonexistent")
            assert results == []

    class TestClear:
        """Tests for clear functionality."""

        def test_should_clear_all_entries(self) -> None:
            """Test that clear removes all entries."""
            history = TranscriptionHistory(auto_save=False)
            history.add("Entry 1")
            history.add("Entry 2")

            history.clear()
            assert len(history) == 0

        def test_should_save_after_clear_when_auto_save_enabled(self) -> None:
            """Test that auto-save saves after clear."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                temp_path = f.name

            try:
                history = TranscriptionHistory(history_file=temp_path, auto_save=True)
                history.add("Test entry")
                history.clear()

                # Verify file was updated
                with open(temp_path, encoding="utf-8") as f:
                    data = json.load(f)
                assert len(data["entries"]) == 0
            finally:
                Path(temp_path).unlink()

    class TestSave:
        """Tests for save functionality."""

        def test_should_save_to_file(self) -> None:
            """Test saving to file."""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                temp_path = f.name

            try:
                history = TranscriptionHistory(history_file=temp_path, auto_save=False)
                history.add("Entry 1")
                history.add("Entry 2")
                history.save()

                # Verify file contents
                with open(temp_path, encoding="utf-8") as f:
                    data = json.load(f)
                assert len(data["entries"]) == 2
            finally:
                Path(temp_path).unlink()

        def test_should_create_directory_if_not_exists(self) -> None:
            """Test that save creates directory if needed."""
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_path = Path(tmpdir) / "subdir" / "history.json"

                history = TranscriptionHistory(history_file=temp_path, auto_save=False)
                history.add("Test entry")
                history.save()

                assert temp_path.exists()

        def test_should_not_save_if_no_file_specified(self) -> None:
            """Test that save does nothing without file."""
            history = TranscriptionHistory(history_file=None, auto_save=False)
            history.add("Test entry")
            history.save()  # Should not raise


class TestHistoryIntegration:
    """Integration tests for history module."""

    def test_should_persist_and_restore_history(self) -> None:
        """Test full persistence cycle."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            # Create and populate history
            history1 = TranscriptionHistory(history_file=temp_path, auto_save=True)
            history1.add("First entry", language="en")
            history1.add("Second entry", language="fr")

            # Create new history from same file
            history2 = TranscriptionHistory(history_file=temp_path)
            assert len(history2) == 2
            assert history2.entries[0].text == "First entry"
            assert history2.entries[0].language == "en"
        finally:
            Path(temp_path).unlink()
