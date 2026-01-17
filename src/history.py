"""Transcription history management."""

import json
from dataclasses import asdict, dataclass, field
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


@dataclass
class TranscriptionHistory:
    """Manages transcription history with persistence."""

    history_file: str | Path | None = None
    max_entries: int = 100
    auto_save: bool = True
    entries: list[TranscriptionEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize history and load from file if exists."""
        if self.history_file:
            self.history_file = Path(self.history_file)
            self._load()

    def _load(self) -> None:
        """Load history from JSON file."""
        if not self.history_file:
            return

        # history_file is converted to Path in __post_init__
        path = self.history_file if isinstance(self.history_file, Path) else Path(self.history_file)
        if not path.exists():
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            self.entries = [TranscriptionEntry(**entry) for entry in data.get("entries", [])]
            logger.debug(f"Loaded {len(self.entries)} history entries from {self.history_file}")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse history file: {e}")
            self.entries = []
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
            self.entries = []

    def save(self) -> None:
        """Save history to JSON file."""
        if not self.history_file:
            return

        # history_file is converted to Path in __post_init__
        path = self.history_file if isinstance(self.history_file, Path) else Path(self.history_file)

        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {"entries": [asdict(entry) for entry in self.entries]}

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(self.entries)} history entries to {self.history_file}")

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

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
            language: Detected language
            audio_duration: Audio duration in seconds
            transcription_time: Transcription time in seconds

        Returns:
            The created TranscriptionEntry
        """
        entry = TranscriptionEntry(
            text=text,
            timestamp=datetime.now().isoformat(),
            language=language,
            audio_duration=audio_duration,
            transcription_time=transcription_time,
        )

        self.entries.append(entry)

        # Trim to max_entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

        # Auto-save if enabled
        if self.auto_save:
            self.save()

        logger.debug(f"Added history entry: {text[:50]}...")
        return entry

    def get_recent(self, count: int = 10) -> list[TranscriptionEntry]:
        """Get recent transcription entries.

        Args:
            count: Number of entries to return

        Returns:
            List of recent entries (newest first)
        """
        return list(reversed(self.entries[-count:]))

    def search(self, query: str, limit: int = 10) -> list[TranscriptionEntry]:
        """Search history for entries containing query.

        Args:
            query: Search query (case-insensitive)
            limit: Maximum number of results

        Returns:
            List of matching entries (newest first)
        """
        query_lower = query.lower()
        matches = [entry for entry in self.entries if query_lower in entry.text.lower()]
        return list(reversed(matches[-limit:]))

    def clear(self) -> None:
        """Clear all history entries."""
        self.entries = []
        if self.auto_save:
            self.save()
        logger.info("History cleared")

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)
