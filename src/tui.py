"""Text User Interface for STT Clipboard."""

from datetime import datetime

from rich.text import Text
from textual import events, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, RichLog, Static

from src.audio_capture import AudioRecorder
from src.clipboard import copy_to_clipboard
from src.config import Config
from src.history import TranscriptionHistory
from src.notifications import notify_text_copied
from src.punctuation import PunctuationProcessor
from src.transcription import WhisperTranscriber
from src.tui_settings import SettingsScreen

# Responsive breakpoints
BREAKPOINT_COMPACT = 80
BREAKPOINT_VERY_COMPACT = 60
BREAKPOINT_WIDE = 120


class StatusIndicator(Static):
    """Status indicator widget."""

    status = reactive("idle")

    def watch_status(self, status: str) -> None:
        """Update display when status changes."""
        status_styles = {
            "idle": ("IDLE", "white", "darkblue"),
            "recording": ("RECORDING", "white", "red"),
            "transcribing": ("TRANSCRIBING", "black", "yellow"),
            "copying": ("COPYING", "white", "green"),
            "ready": ("READY", "white", "darkgreen"),
            "error": ("ERROR", "white", "darkred"),
        }
        text, color, background = status_styles.get(status, ("UNKNOWN", "white", "grey"))
        self.update(f" {text} ")
        self.styles.background = background
        self.styles.color = color


class StatsPanel(Static):
    """Statistics panel widget with grid layout."""

    DEFAULT_CSS = """
    StatsPanel {
        layout: horizontal;
        height: 3;
        padding: 1;
        background: $surface-darken-1;
    }

    StatsPanel .stat-item {
        width: auto;
        margin-right: 2;
    }

    StatsPanel .stat-value {
        text-style: bold;
    }

    StatsPanel .stat-success {
        color: $success;
    }

    StatsPanel .stat-error {
        color: $error;
    }

    StatsPanel .stat-muted {
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.total_requests: int = 0
        self.successful: int = 0
        self.failed: int = 0
        self.total_audio: float = 0.0
        self.total_transcription: float = 0.0

    def update_stats(
        self,
        total: int,
        successful: int,
        failed: int,
        audio_duration: float,
        transcription_time: float,
    ) -> None:
        """Update statistics display."""
        self.total_requests = total
        self.successful = successful
        self.failed = failed
        self.total_audio = audio_duration
        self.total_transcription = transcription_time
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the statistics display with improved formatting."""
        rtf = self.total_transcription / self.total_audio if self.total_audio > 0 else 0.0
        # Compact, readable format with visual hierarchy
        self.update(
            f"[bold]{self.total_requests}[/] req  "
            f"[green]{self.successful}[/] ok  "
            f"[red]{self.failed}[/] err  "
            f"[dim]{self.total_audio:.1f}s audio[/]  "
            f"[dim]RTF {rtf:.2f}x[/]"
        )


class TranscriptionLog(RichLog):
    """Log widget for transcriptions."""

    def add_transcription(self, text: str, language: str | None = None) -> None:
        """Add a transcription entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        lang_str = f"[{language}]" if language else ""
        self.write(Text(f"[{timestamp}] {lang_str} {text}"))


class STTApp(App):
    """STT Clipboard TUI Application."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    /* Status bar - clean and compact */
    #status-bar {
        height: 3;
        padding: 0 1;
        background: $surface;
        align: left middle;
    }

    #status-indicator {
        width: auto;
        min-width: 14;
        padding: 0 2;
        text-style: bold;
        text-align: center;
        margin-right: 2;
        transition: background 150ms;
    }

    #config-info {
        color: $text-muted;
        padding-left: 1;
    }

    /* Main content area */
    #main-container {
        padding: 1;
    }

    #transcription-log {
        border: round $primary-darken-2;
        background: $surface-darken-1;
        height: 100%;
        scrollbar-gutter: stable;
    }

    /* Control buttons */
    #controls {
        height: auto;
        padding: 1;
        align: center middle;
        background: $surface;
    }

    #controls Button {
        margin: 0 1;
        min-width: 16;
    }

    #btn-record {
        background: $primary;
    }

    #btn-record:hover {
        background: $primary-lighten-1;
    }

    #btn-continuous {
        background: $warning-darken-1;
    }

    #btn-stop {
        background: $error-darken-1;
    }

    #btn-stop:disabled {
        opacity: 0.5;
    }

    /* Recording state animation */
    .recording #status-indicator {
        background: $error;
        text-style: bold;
    }

    /* ===== RESPONSIVE: Small screens (< 80 cols) ===== */
    .-compact #status-bar {
        height: 2;
        padding: 0;
    }

    .-compact #status-indicator {
        min-width: 10;
        padding: 0 1;
    }

    .-compact #config-info {
        display: none;
    }

    .-compact #controls Button {
        min-width: 10;
        margin: 0;
    }

    .-compact #btn-history {
        display: none;
    }

    .-compact #main-container {
        padding: 0;
    }

    .-compact #transcription-log {
        border: none;
    }

    .-compact #stats-bar {
        height: 2;
        padding: 0 1;
    }

    /* ===== RESPONSIVE: Very small screens (< 60 cols) ===== */
    .-very-compact #status-bar {
        display: none;
    }

    .-very-compact #controls {
        padding: 0;
    }

    .-very-compact #controls Button {
        min-width: 8;
    }

    .-very-compact #btn-continuous {
        display: none;
    }

    .-very-compact #stats-bar {
        display: none;
    }

    /* ===== RESPONSIVE: Wide screens (> 120 cols) ===== */
    .-wide #controls Button {
        min-width: 20;
        margin: 0 2;
    }

    .-wide #main-container {
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("r", "record", "Record"),
        ("c", "continuous", "Continuous"),
        ("s", "stop", "Stop"),
        ("h", "history", "History"),
        ("o", "settings", "Options"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, config: Config, config_path: str = "config/config.yaml") -> None:
        super().__init__()
        self.config = config
        self.config_path = config_path

        # Initialize components
        self.transcriber = WhisperTranscriber(config.transcription)
        self.audio_recorder = AudioRecorder(config.audio, config.vad)
        self.punctuation_processor = PunctuationProcessor(
            enable_french_spacing=config.punctuation.french_spacing,
            clean_artifacts=True,
            capitalize=True,
        )

        # History
        self.history: TranscriptionHistory | None = None
        if config.history.enabled:
            self.history = TranscriptionHistory(
                history_file=config.history.file,
                max_entries=config.history.max_entries,
                auto_save=config.history.auto_save,
            )

        # State
        self._is_recording = False
        self._is_continuous = False
        self._stop_requested = False

        # Stats - using typed attributes for clarity
        self._total_requests: int = 0
        self._successful: int = 0
        self._failed: int = 0
        self._total_audio: float = 0.0
        self._total_transcription: float = 0.0

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        # Simplified status bar
        lang = self.config.transcription.language or "auto"
        model = self.config.transcription.model_size
        with Horizontal(id="status-bar"):
            yield StatusIndicator(id="status-indicator")
            yield Static(f"[dim]Model:[/] {model}  [dim]Lang:[/] {lang}", id="config-info")

        with Container(id="main-container"):
            yield TranscriptionLog(id="transcription-log", highlight=True, markup=True)

        with Horizontal(id="controls"):
            yield Button("Record", id="btn-record", variant="primary")
            yield Button("Continuous", id="btn-continuous", variant="warning")
            yield Button("Stop", id="btn-stop", variant="error", disabled=True)
            yield Button("History", id="btn-history", variant="default")

        yield StatsPanel(id="stats-bar")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize on mount."""
        log = self.query_one("#transcription-log", TranscriptionLog)
        log.write("[bold green]STT Clipboard Ready[/]")
        log.write(
            "[dim]Shortcuts: R=Record  C=Continuous  S=Stop  H=History  O=Settings  Q=Quit[/]"
        )
        log.write("")

        # Apply responsive layout based on initial size
        self._apply_responsive_layout(self.size.width)

        # Load models
        self.set_status("idle")
        self._load_models()

    def on_resize(self, event: events.Resize) -> None:
        """Handle terminal resize for responsive layout."""
        self._apply_responsive_layout(event.size.width)

    def _apply_responsive_layout(self, width: int) -> None:
        """Apply responsive CSS classes based on terminal width."""
        # Remove all responsive classes first
        self.remove_class("-compact", "-very-compact", "-wide")

        # Apply appropriate class based on width
        if width < BREAKPOINT_VERY_COMPACT:
            self.add_class("-very-compact", "-compact")
        elif width < BREAKPOINT_COMPACT:
            self.add_class("-compact")
        elif width >= BREAKPOINT_WIDE:
            self.add_class("-wide")

    @work(thread=True)
    async def _load_models(self) -> None:
        """Load models in background."""
        log = self.query_one("#transcription-log", TranscriptionLog)
        log.write("[dim]Loading models...[/]")
        self.transcriber.load_model()
        self.audio_recorder._load_vad_model()
        log.write("[green]Models loaded[/]")
        self.set_status("ready")

    def set_status(self, status: str) -> None:
        """Set the status indicator."""
        indicator = self.query_one("#status-indicator", StatusIndicator)
        indicator.status = status

    def update_stats(self) -> None:
        """Update the stats panel."""
        stats_panel = self.query_one("#stats-bar", StatsPanel)
        stats_panel.update_stats(
            self._total_requests,
            self._successful,
            self._failed,
            self._total_audio,
            self._total_transcription,
        )

    def action_record(self) -> None:
        """Start single recording."""
        if self._is_recording:
            return
        self._record_single()

    def action_continuous(self) -> None:
        """Start continuous recording."""
        if self._is_recording:
            return
        self._record_continuous()

    def action_stop(self) -> None:
        """Stop recording."""
        self._stop_requested = True
        if self._is_continuous:
            self.audio_recorder.stop_continuous()
        self._is_recording = False

    def action_history(self) -> None:
        """Show history."""
        log = self.query_one("#transcription-log", TranscriptionLog)
        log.write("-" * 50)
        log.write("[bold]Recent History:[/]")

        if self.history is not None:
            entries = self.history.get_recent(10)
            if entries:
                for entry in entries:
                    lang = f"[{entry.language}]" if entry.language else ""
                    log.write(f"  {entry.timestamp[:19]} {lang} {entry.text[:50]}...")
            else:
                log.write("  No history entries")
        else:
            log.write("  History disabled")
        log.write("-" * 50)

    def reload_config(self, new_config: Config) -> None:
        """Reload configuration and update components that can be hot-reloaded.

        Args:
            new_config: The new configuration to apply
        """
        old_config = self.config
        self.config = new_config

        # Hot-reload history if settings changed
        if (
            new_config.history.enabled != old_config.history.enabled
            or new_config.history.file != old_config.history.file
            or new_config.history.max_entries != old_config.history.max_entries
        ):
            if new_config.history.enabled:
                self.history = TranscriptionHistory(
                    history_file=new_config.history.file,
                    max_entries=new_config.history.max_entries,
                    auto_save=new_config.history.auto_save,
                )
            else:
                self.history = None

        # Hot-reload punctuation settings
        if new_config.punctuation.french_spacing != old_config.punctuation.french_spacing:
            self.punctuation_processor = PunctuationProcessor(
                enable_french_spacing=new_config.punctuation.french_spacing,
                clean_artifacts=True,
                capitalize=True,
            )

    def action_settings(self) -> None:
        """Open settings screen."""
        self.push_screen(SettingsScreen(self.config, self.config_path))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-record":
            self.action_record()
        elif event.button.id == "btn-continuous":
            self.action_continuous()
        elif event.button.id == "btn-stop":
            self.action_stop()
        elif event.button.id == "btn-history":
            self.action_history()

    @work(thread=True)
    async def _record_single(self) -> None:
        """Record single transcription."""
        self._is_recording = True
        self._stop_requested = False

        log = self.query_one("#transcription-log", TranscriptionLog)
        btn_stop = self.query_one("#btn-stop", Button)
        btn_record = self.query_one("#btn-record", Button)
        btn_continuous = self.query_one("#btn-continuous", Button)

        try:
            btn_stop.disabled = False
            btn_record.disabled = True
            btn_continuous.disabled = True

            # Record
            self.set_status("recording")
            log.write("[yellow]Recording... speak now[/]")

            audio = self.audio_recorder.record_until_silence()

            if audio is None or self._stop_requested:
                log.write("[red]Recording cancelled or failed[/]")
                self._failed += 1
                return

            audio_duration = len(audio) / self.config.audio.sample_rate
            self._total_audio += audio_duration

            # Transcribe
            self.set_status("transcribing")
            log.write("[yellow]Transcribing...[/]")

            import time

            start = time.time()
            text = self.transcriber.transcribe(audio)
            transcription_time = time.time() - start
            self._total_transcription += transcription_time

            if not text or not text.strip():
                log.write("[red]Empty transcription[/]")
                self._failed += 1
                return

            # Post-process
            if self.config.punctuation.enabled:
                text = self.punctuation_processor.process(
                    text, detected_language=self.transcriber.detected_language
                )

            # Copy to clipboard
            self.set_status("copying")
            if self.config.clipboard.enabled:
                success = copy_to_clipboard(text, self.config.clipboard.timeout)
                if success:
                    notify_text_copied(text)

            # Log result
            log.add_transcription(text, self.transcriber.detected_language)

            # Update stats
            self._total_requests += 1
            self._successful += 1
            self.update_stats()

            # Add to history
            if self.history is not None:
                self.history.add(
                    text=text,
                    language=self.transcriber.detected_language,
                    audio_duration=audio_duration,
                    transcription_time=transcription_time,
                )

        except Exception as e:
            log.write(f"[red]Error: {e}[/]")
            self._failed += 1

        finally:
            self._is_recording = False
            self.set_status("ready")
            btn_stop.disabled = True
            btn_record.disabled = False
            btn_continuous.disabled = False
            self.update_stats()

    @work(thread=True)
    async def _record_continuous(self) -> None:
        """Record continuously."""
        self._is_recording = True
        self._is_continuous = True
        self._stop_requested = False

        log = self.query_one("#transcription-log", TranscriptionLog)
        btn_stop = self.query_one("#btn-stop", Button)
        btn_record = self.query_one("#btn-record", Button)
        btn_continuous = self.query_one("#btn-continuous", Button)

        try:
            btn_stop.disabled = False
            btn_record.disabled = True
            btn_continuous.disabled = True

            log.write("[bold yellow]Continuous mode started[/]")
            log.write("Speak... pause... text copied. Press [S] to stop.")

            segment_count = 0

            for audio in self.audio_recorder.record_continuous():
                if self._stop_requested:
                    break

                segment_count += 1
                self.set_status("recording")

                audio_duration = len(audio) / self.config.audio.sample_rate
                self._total_audio += audio_duration

                # Transcribe
                self.set_status("transcribing")

                import time

                start = time.time()
                text = self.transcriber.transcribe(audio)
                transcription_time = time.time() - start
                self._total_transcription += transcription_time

                if not text or not text.strip():
                    self._failed += 1
                    continue

                # Post-process
                if self.config.punctuation.enabled:
                    text = self.punctuation_processor.process(
                        text, detected_language=self.transcriber.detected_language
                    )

                # Copy to clipboard
                self.set_status("copying")
                if self.config.clipboard.enabled:
                    success = copy_to_clipboard(text, self.config.clipboard.timeout)
                    if success:
                        notify_text_copied(text)

                # Log result
                log.add_transcription(text, self.transcriber.detected_language)

                # Update stats
                self._total_requests += 1
                self._successful += 1
                self.update_stats()

                # Add to history
                if self.history is not None:
                    self.history.add(
                        text=text,
                        language=self.transcriber.detected_language,
                        audio_duration=audio_duration,
                        transcription_time=transcription_time,
                    )

            log.write(f"[bold green]Continuous mode stopped ({segment_count} segments)[/]")

        except Exception as e:
            log.write(f"[red]Error: {e}[/]")

        finally:
            self._is_recording = False
            self._is_continuous = False
            self.set_status("ready")
            btn_stop.disabled = True
            btn_record.disabled = False
            btn_continuous.disabled = False
            self.update_stats()


def run_tui(config: Config, config_path: str = "config/config.yaml") -> None:
    """Run the TUI application.

    Args:
        config: Application configuration
        config_path: Path to configuration file
    """
    app = STTApp(config, config_path)
    app.run()


if __name__ == "__main__":
    # Test run
    config = Config()
    run_tui(config)
