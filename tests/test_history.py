"""Tests for transcription history module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.history import TranscriptionEntry, TranscriptionHistory, get_history


class TestTranscriptionEntry:
    """Tests for TranscriptionEntry dataclass."""

    def test_create_entry(self):
        """Test creating an entry with current timestamp."""
        entry = TranscriptionEntry.create(
            text="Hello world",
            language="en",
            audio_duration=2.5,
            transcription_time=0.8,
        )
        assert entry.text == "Hello world"
        assert entry.language == "en"
        assert entry.audio_duration == 2.5
        assert entry.transcription_time == 0.8
        assert entry.timestamp is not None

    def test_create_entry_minimal(self):
        """Test creating entry with only text."""
        entry = TranscriptionEntry.create(text="Test")
        assert entry.text == "Test"
        assert entry.language is None
        assert entry.audio_duration is None
        assert entry.transcription_time is None

    def test_timestamp_is_iso_format(self):
        """Test timestamp is valid ISO format."""
        entry = TranscriptionEntry.create(text="Test")
        # Should not raise
        datetime.fromisoformat(entry.timestamp)

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = TranscriptionEntry(
            text="Hello",
            timestamp="2024-01-15T10:30:00",
            language="fr",
            audio_duration=1.5,
            transcription_time=0.5,
        )
        d = entry.to_dict()
        assert d["text"] == "Hello"
        assert d["timestamp"] == "2024-01-15T10:30:00"
        assert d["language"] == "fr"
        assert d["audio_duration"] == 1.5
        assert d["transcription_time"] == 0.5

    def test_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "text": "Bonjour",
            "timestamp": "2024-01-15T11:00:00",
            "language": "fr",
            "audio_duration": 2.0,
            "transcription_time": 0.6,
        }
        entry = TranscriptionEntry.from_dict(data)
        assert entry.text == "Bonjour"
        assert entry.timestamp == "2024-01-15T11:00:00"
        assert entry.language == "fr"
        assert entry.audio_duration == 2.0
        assert entry.transcription_time == 0.6

    def test_from_dict_minimal(self):
        """Test creating entry from minimal dictionary."""
        data = {
            "text": "Test",
            "timestamp": "2024-01-15T12:00:00",
        }
        entry = TranscriptionEntry.from_dict(data)
        assert entry.text == "Test"
        assert entry.language is None
        assert entry.audio_duration is None


class TestTranscriptionHistory:
    """Tests for TranscriptionHistory class."""

    def test_init_without_file(self):
        """Test initialization without persistence."""
        history = TranscriptionHistory(history_file=None)
        assert len(history) == 0
        assert history.history_file is None

    def test_init_with_nonexistent_file(self):
        """Test initialization with file that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history = TranscriptionHistory(history_file=Path(tmpdir) / "history.json")
            assert len(history) == 0

    def test_add_entry(self):
        """Test adding an entry."""
        history = TranscriptionHistory(history_file=None)
        entry = history.add(text="Hello world")
        assert entry.text == "Hello world"
        assert len(history) == 1

    def test_add_entry_with_metadata(self):
        """Test adding entry with all metadata."""
        history = TranscriptionHistory(history_file=None)
        entry = history.add(
            text="Test",
            language="en",
            audio_duration=3.0,
            transcription_time=1.0,
        )
        assert entry.language == "en"
        assert entry.audio_duration == 3.0
        assert entry.transcription_time == 1.0

    def test_add_multiple_entries(self):
        """Test adding multiple entries."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="First")
        history.add(text="Second")
        history.add(text="Third")
        assert len(history) == 3

    def test_max_entries_limit(self):
        """Test that entries are trimmed when exceeding max."""
        history = TranscriptionHistory(history_file=None, max_entries=3)
        history.add(text="One")
        history.add(text="Two")
        history.add(text="Three")
        history.add(text="Four")
        assert len(history) == 3
        entries = history.get_all()
        assert entries[0].text == "Two"
        assert entries[2].text == "Four"

    def test_get_recent(self):
        """Test getting recent entries."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="First")
        history.add(text="Second")
        history.add(text="Third")

        recent = history.get_recent(2)
        assert len(recent) == 2
        assert recent[0].text == "Third"  # Newest first
        assert recent[1].text == "Second"

    def test_get_recent_more_than_available(self):
        """Test getting more recent than available."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="Only")

        recent = history.get_recent(10)
        assert len(recent) == 1

    def test_get_all(self):
        """Test getting all entries."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="First")
        history.add(text="Second")

        all_entries = history.get_all()
        assert len(all_entries) == 2
        assert all_entries[0].text == "First"  # Oldest first
        assert all_entries[1].text == "Second"

    def test_search(self):
        """Test searching entries."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="Hello world")
        history.add(text="Goodbye world")
        history.add(text="Hello again")

        results = history.search("hello")
        assert len(results) == 2
        assert results[0].text == "Hello again"  # Newest first

    def test_search_case_insensitive(self):
        """Test search is case-insensitive."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="HELLO WORLD")
        history.add(text="hello world")

        results = history.search("Hello")
        assert len(results) == 2

    def test_search_with_limit(self):
        """Test search respects limit."""
        history = TranscriptionHistory(history_file=None)
        for i in range(10):
            history.add(text=f"Test message {i}")

        results = history.search("test", limit=3)
        assert len(results) == 3

    def test_search_no_results(self):
        """Test search with no matches."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="Hello world")

        results = history.search("xyz")
        assert len(results) == 0

    def test_clear(self):
        """Test clearing history."""
        history = TranscriptionHistory(history_file=None)
        history.add(text="One")
        history.add(text="Two")

        count = history.clear()
        assert count == 2
        assert len(history) == 0


class TestTranscriptionHistoryPersistence:
    """Tests for history file persistence."""

    def test_save_and_load(self):
        """Test saving and loading history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"

            # Create and add entries
            history1 = TranscriptionHistory(history_file=history_file)
            history1.add(text="First", language="en")
            history1.add(text="Second", language="fr")

            # Create new instance and verify loaded
            history2 = TranscriptionHistory(history_file=history_file)
            assert len(history2) == 2
            entries = history2.get_all()
            assert entries[0].text == "First"
            assert entries[0].language == "en"
            assert entries[1].text == "Second"

    def test_creates_parent_directories(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "subdir" / "history.json"

            history = TranscriptionHistory(history_file=history_file)
            history.add(text="Test")

            assert history_file.exists()

    def test_handles_corrupted_file(self):
        """Test handling of corrupted history file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            history_file.write_text("not valid json")

            # Should not raise, just start empty
            history = TranscriptionHistory(history_file=history_file)
            assert len(history) == 0

    def test_auto_save_enabled(self):
        """Test auto-save saves after each add."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"

            history = TranscriptionHistory(history_file=history_file, auto_save=True)
            history.add(text="Auto saved")

            # Read file directly
            with open(history_file) as f:
                data = json.load(f)
            assert len(data["entries"]) == 1

    def test_auto_save_disabled(self):
        """Test auto-save disabled doesn't save automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"

            history = TranscriptionHistory(history_file=history_file, auto_save=False)
            history.add(text="Not auto saved")

            # File should not exist yet
            assert not history_file.exists()

            # Manual save
            history.save()
            assert history_file.exists()

    def test_manual_save(self):
        """Test manual save method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"

            history = TranscriptionHistory(history_file=history_file, auto_save=False)
            history.add(text="Entry 1")
            history.add(text="Entry 2")
            history.save()

            with open(history_file) as f:
                data = json.load(f)
            assert len(data["entries"]) == 2

    def test_file_format_version(self):
        """Test file includes version field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"

            history = TranscriptionHistory(history_file=history_file)
            history.add(text="Test")

            with open(history_file) as f:
                data = json.load(f)
            assert data["version"] == 1


class TestGetHistory:
    """Tests for get_history function."""

    def test_creates_global_instance(self):
        """Test that get_history creates a singleton."""
        # Reset global
        import src.history

        src.history._history = None

        history1 = get_history()
        history2 = get_history()
        assert history1 is history2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
