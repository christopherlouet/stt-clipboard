"""Transcription history management for STT Clipboard."""

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger


@dataclass
class TranscriptionEntry:
    """A single transcription history entry."""

    text: str
    timestamp: str
    language: str | None = None
    audio_duration: float | None = None
    transcription_time: float | None = None

    @classmethod
    def create(
        cls,
        text: str,
        language: str | None = None,
        audio_duration: float | None = None,
        transcription_time: float | None = None,
    ) -> "TranscriptionEntry":
        """Create a new entry with current timestamp.

        Args:
            text: Transcribed text
            language: Detected language code
            audio_duration: Duration of audio in seconds
            transcription_time: Time taken to transcribe in seconds

        Returns:
            New TranscriptionEntry instance
        """
        return cls(
            text=text,
            timestamp=datetime.now().isoformat(),
            language=language,
            audio_duration=audio_duration,
            transcription_time=transcription_time,
        )

    def to_dict(self) -> dict:
        """Convert entry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TranscriptionEntry":
        """Create entry from dictionary.

        Args:
            data: Dictionary with entry fields

        Returns:
            TranscriptionEntry instance
        """
        return cls(
            text=data["text"],
            timestamp=data["timestamp"],
            language=data.get("language"),
            audio_duration=data.get("audio_duration"),
            transcription_time=data.get("transcription_time"),
        )


class TranscriptionHistory:
    """Manages transcription history with persistence."""

    def __init__(
        self,
        history_file: str | Path | None = None,
        max_entries: int = 100,
        auto_save: bool = True,
    ):
        """Initialize transcription history.

        Args:
            history_file: Path to history file. None disables persistence.
            max_entries: Maximum number of entries to keep (FIFO)
            auto_save: Whether to save after each add
        """
        self.history_file = Path(history_file) if history_file else None
        self.max_entries = max_entries
        self.auto_save = auto_save
        self._entries: list[TranscriptionEntry] = []
        self._lock = threading.Lock()

        # Load existing history
        if self.history_file and self.history_file.exists():
            self._load()

        logger.debug(
            f"TranscriptionHistory initialized: "
            f"file={self.history_file}, max={max_entries}, entries={len(self._entries)}"
        )

    def add(
        self,
        text: str,
        language: str | None = None,
        audio_duration: float | None = None,
        transcription_time: float | None = None,
    ) -> TranscriptionEntry:
        """Add a new transcription to history.

        Args:
            text: Transcribed text
            language: Detected language code
            audio_duration: Duration of audio in seconds
            transcription_time: Time taken to transcribe in seconds

        Returns:
            The created TranscriptionEntry
        """
        entry = TranscriptionEntry.create(
            text=text,
            language=language,
            audio_duration=audio_duration,
            transcription_time=transcription_time,
        )

        with self._lock:
            self._entries.append(entry)

            # Trim to max entries (FIFO)
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries :]

            if self.auto_save and self.history_file:
                self._save_unlocked()

        logger.debug(f"Added to history: '{text[:50]}...' ({len(self._entries)} total)")
        return entry

    def get_recent(self, count: int = 10) -> list[TranscriptionEntry]:
        """Get most recent transcriptions.

        Args:
            count: Number of entries to return

        Returns:
            List of most recent entries (newest first)
        """
        with self._lock:
            return list(reversed(self._entries[-count:]))

    def get_all(self) -> list[TranscriptionEntry]:
        """Get all transcriptions.

        Returns:
            List of all entries (oldest first)
        """
        with self._lock:
            return list(self._entries)

    def search(self, query: str, limit: int = 10) -> list[TranscriptionEntry]:
        """Search transcriptions containing query text.

        Args:
            query: Text to search for (case-insensitive)
            limit: Maximum results to return

        Returns:
            List of matching entries (newest first)
        """
        query_lower = query.lower()
        with self._lock:
            results = [e for e in reversed(self._entries) if query_lower in e.text.lower()]
            return results[:limit]

    def clear(self) -> int:
        """Clear all history entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            if self.auto_save and self.history_file:
                self._save_unlocked()
        logger.info(f"Cleared {count} history entries")
        return count

    def __len__(self) -> int:
        """Return number of entries in history."""
        with self._lock:
            return len(self._entries)

    def _load(self) -> None:
        """Load history from file."""
        if not self.history_file or not self.history_file.exists():
            return

        try:
            with open(self.history_file, encoding="utf-8") as f:
                data = json.load(f)

            self._entries = [TranscriptionEntry.from_dict(e) for e in data.get("entries", [])]

            # Trim if needed
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries :]

            logger.info(f"Loaded {len(self._entries)} history entries from {self.history_file}")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse history file: {e}")
            self._entries = []
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self._entries = []

    def _save_unlocked(self) -> None:
        """Save history to file (caller must hold lock)."""
        if not self.history_file:
            return

        try:
            # Ensure directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": 1,
                "entries": [e.to_dict() for e in self._entries],
            }

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(self._entries)} entries to {self.history_file}")

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def save(self) -> None:
        """Manually save history to file."""
        with self._lock:
            self._save_unlocked()


# Global history instance
_history: TranscriptionHistory | None = None


def get_history(
    history_file: str | Path | None = None,
    max_entries: int = 100,
) -> TranscriptionHistory:
    """Get or create the global history instance.

    Args:
        history_file: Path to history file
        max_entries: Maximum entries to keep

    Returns:
        TranscriptionHistory instance
    """
    global _history
    if _history is None:
        _history = TranscriptionHistory(
            history_file=history_file,
            max_entries=max_entries,
        )
    return _history
