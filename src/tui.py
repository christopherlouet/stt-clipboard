"""Text User Interface for STT Clipboard."""

from datetime import datetime

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Label, RichLog, Static

from src.audio_capture import AudioRecorder
from src.clipboard import copy_to_clipboard
from src.config import Config
from src.history import TranscriptionHistory
from src.notifications import notify_text_copied
from src.punctuation import PunctuationProcessor
from src.transcription import WhisperTranscriber


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
    """Statistics panel widget."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.total_requests = 0
        self.successful = 0
        self.failed = 0
        self.total_audio = 0.0
        self.total_transcription = 0.0

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
        """Refresh the statistics display."""
        rtf = self.total_transcription / self.total_audio if self.total_audio > 0 else 0
        self.update(
            f"Requests: {self.total_requests} | "
            f"Success: {self.successful} | "
            f"Failed: {self.failed} | "
            f"Audio: {self.total_audio:.1f}s | "
            f"RTF: {rtf:.2f}x"
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

    #status-bar {
        height: 3;
        padding: 1;
        background: $surface;
    }

    #status-indicator {
        width: auto;
        padding: 0 2;
        text-style: bold;
    }

    #main-container {
        padding: 1;
    }

    #transcription-log {
        border: solid $primary;
        height: 100%;
    }

    #controls {
        height: 5;
        padding: 1;
        align: center middle;
    }

    #stats-bar {
        height: 3;
        padding: 1;
        background: $surface-darken-1;
    }

    Button {
        margin: 0 1;
    }

    .recording {
        background: red;
    }
    """

    BINDINGS = [
        ("r", "record", "Record"),
        ("c", "continuous", "Continuous"),
        ("s", "stop", "Stop"),
        ("h", "history", "History"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

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

        # Stats
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_audio": 0.0,
            "total_transcription": 0.0,
        }

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        with Horizontal(id="status-bar"):
            yield Label("Status: ")
            yield StatusIndicator(id="status-indicator")
            yield Label(f" | Model: {self.config.transcription.model_size}")
            lang = self.config.transcription.language or "auto"
            yield Label(f" | Language: {lang}")

        with Container(id="main-container"):
            yield TranscriptionLog(id="transcription-log", highlight=True, markup=True)

        with Horizontal(id="controls"):
            yield Button("Record [R]", id="btn-record", variant="primary")
            yield Button("Continuous [C]", id="btn-continuous", variant="warning")
            yield Button("Stop [S]", id="btn-stop", variant="error", disabled=True)
            yield Button("History [H]", id="btn-history")

        yield StatsPanel(id="stats-bar")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize on mount."""
        log = self.query_one("#transcription-log", TranscriptionLog)
        log.write("[bold green]STT Clipboard TUI Started[/]")
        log.write(f"Model: {self.config.transcription.model_size}")
        log.write("Press [R] to record, [C] for continuous mode, [Q] to quit")
        log.write("-" * 50)

        # Load models
        self.set_status("idle")
        await self._load_models()

    @work(thread=True)
    async def _load_models(self) -> None:
        """Load models in background."""
        log = self.query_one("#transcription-log", TranscriptionLog)
        log.write("Loading Whisper model...")
        self.transcriber.load_model()
        log.write("Loading VAD model...")
        self.audio_recorder._load_vad_model()
        log.write("[bold green]Models loaded![/]")
        self.set_status("ready")

    def set_status(self, status: str) -> None:
        """Set the status indicator."""
        indicator = self.query_one("#status-indicator", StatusIndicator)
        indicator.status = status

    def update_stats(self) -> None:
        """Update the stats panel."""
        stats_panel = self.query_one("#stats-bar", StatsPanel)
        stats_panel.update_stats(
            self.stats["total_requests"],
            self.stats["successful"],
            self.stats["failed"],
            self.stats["total_audio"],
            self.stats["total_transcription"],
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

        if self.history:
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
                self.stats["failed"] += 1
                return

            audio_duration = len(audio) / self.config.audio.sample_rate
            self.stats["total_audio"] += audio_duration

            # Transcribe
            self.set_status("transcribing")
            log.write("[yellow]Transcribing...[/]")

            import time

            start = time.time()
            text = self.transcriber.transcribe(audio)
            transcription_time = time.time() - start
            self.stats["total_transcription"] += transcription_time

            if not text or not text.strip():
                log.write("[red]Empty transcription[/]")
                self.stats["failed"] += 1
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
            self.stats["total_requests"] += 1
            self.stats["successful"] += 1
            self.update_stats()

            # Add to history
            if self.history:
                self.history.add(
                    text=text,
                    language=self.transcriber.detected_language,
                    audio_duration=audio_duration,
                    transcription_time=transcription_time,
                )

        except Exception as e:
            log.write(f"[red]Error: {e}[/]")
            self.stats["failed"] += 1

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
                self.stats["total_audio"] += audio_duration

                # Transcribe
                self.set_status("transcribing")

                import time

                start = time.time()
                text = self.transcriber.transcribe(audio)
                transcription_time = time.time() - start
                self.stats["total_transcription"] += transcription_time

                if not text or not text.strip():
                    self.stats["failed"] += 1
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
                self.stats["total_requests"] += 1
                self.stats["successful"] += 1
                self.update_stats()

                # Add to history
                if self.history:
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


def run_tui(config: Config) -> None:
    """Run the TUI application.

    Args:
        config: Application configuration
    """
    app = STTApp(config)
    app.run()


if __name__ == "__main__":
    # Test run
    config = Config()
    run_tui(config)
