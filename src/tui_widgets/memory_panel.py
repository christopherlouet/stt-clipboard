"""Memory usage panel widget for TUI."""

from typing import Any

import psutil
from textual.widgets import Static


class MemoryPanel(Static):
    """Widget that displays current process memory usage."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _get_memory_mb(self) -> float:
        """Get current process RSS memory in MB.

        Returns:
            Memory in MB, or -1.0 if unavailable.
        """
        try:
            process = psutil.Process()
            rss_bytes: int = process.memory_info().rss
            return float(rss_bytes / (1024 * 1024))
        except Exception:
            return -1.0

    def on_mount(self) -> None:
        """Start periodic refresh on mount."""
        self._refresh_display()
        self.set_interval(5, self._refresh_display)

    def _refresh_display(self) -> None:
        """Update the displayed memory value."""
        mb = self._get_memory_mb()
        if mb < 0:
            self.update("RSS: N/A")
        else:
            self.update(f"RSS: {mb:.1f} MB")
