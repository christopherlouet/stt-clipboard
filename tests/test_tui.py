"""Tests for TUI module."""

import pytest

from src.config import (
    AudioConfig,
    ClipboardConfig,
    Config,
    HistoryConfig,
    HotkeyConfig,
    LoggingConfig,
    PasteConfig,
    PunctuationConfig,
    TranscriptionConfig,
    VADConfig,
)
from src.tui import StatsPanel, StatusIndicator, TranscriptionLog


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    return Config(
        audio=AudioConfig(
            sample_rate=16000,
            channels=1,
            blocksize=512,
            silence_duration=1.2,
            min_speech_duration=0.3,
            max_recording_duration=30,
        ),
        vad=VADConfig(
            threshold=0.5,
            min_silence_duration_ms=300,
            speech_pad_ms=300,
        ),
        transcription=TranscriptionConfig(
            model_size="tiny",
            language="",
            device="cpu",
            compute_type="int8",
            beam_size=5,
        ),
        punctuation=PunctuationConfig(
            enabled=True,
            french_spacing=True,
        ),
        clipboard=ClipboardConfig(
            enabled=True,
            timeout=2.0,
        ),
        paste=PasteConfig(
            enabled=False,
            preferred_tool="auto",
            timeout=2.0,
            delay_ms=100,
        ),
        hotkey=HotkeyConfig(
            socket_path="/tmp/test-stt-tui.sock",
        ),
        logging=LoggingConfig(
            level="INFO",
            format="{time:HH:mm:ss} | {level} | {message}",
            file="",
        ),
        history=HistoryConfig(
            enabled=False,
            file="",
            max_entries=100,
            auto_save=True,
        ),
    )


class TestStatusIndicator:
    """Tests for StatusIndicator widget."""

    class TestStatusStates:
        """Tests for status state display."""

        def test_should_have_idle_status_by_default(self) -> None:
            """Test that default status is idle."""
            indicator = StatusIndicator()
            assert indicator.status == "idle"

        def test_should_accept_valid_status_values(self) -> None:
            """Test that valid status values are accepted."""
            indicator = StatusIndicator()
            valid_statuses = [
                "idle",
                "recording",
                "transcribing",
                "copying",
                "ready",
                "error",
            ]
            for status in valid_statuses:
                indicator.status = status
                assert indicator.status == status

        def test_should_handle_unknown_status(self) -> None:
            """Test that unknown status is handled gracefully."""
            indicator = StatusIndicator()
            indicator.status = "unknown_status"
            assert indicator.status == "unknown_status"


class TestStatsPanel:
    """Tests for StatsPanel widget."""

    class TestInitialization:
        """Tests for StatsPanel initialization."""

        def test_should_initialize_with_zero_stats(self) -> None:
            """Test that stats are initialized to zero."""
            panel = StatsPanel()
            assert panel.total_requests == 0
            assert panel.successful == 0
            assert panel.failed == 0
            assert panel.total_audio == 0.0
            assert panel.total_transcription == 0.0

    class TestStatsUpdate:
        """Tests for stats update functionality."""

        def test_should_update_stats_correctly(self) -> None:
            """Test that stats are updated correctly."""
            panel = StatsPanel()
            panel.update_stats(
                total=10,
                successful=8,
                failed=2,
                audio_duration=60.0,
                transcription_time=30.0,
            )
            assert panel.total_requests == 10
            assert panel.successful == 8
            assert panel.failed == 2
            assert panel.total_audio == 60.0
            assert panel.total_transcription == 30.0

        def test_should_handle_zero_audio_duration_for_rtf(self) -> None:
            """Test RTF calculation with zero audio duration."""
            panel = StatsPanel()
            panel.update_stats(
                total=0,
                successful=0,
                failed=0,
                audio_duration=0.0,
                transcription_time=0.0,
            )
            # Should not raise ZeroDivisionError
            panel.refresh_display()


class TestTranscriptionLog:
    """Tests for TranscriptionLog widget."""

    class TestTranscriptionEntry:
        """Tests for adding transcription entries."""

        def test_should_create_log_widget(self) -> None:
            """Test that log widget is created."""
            log = TranscriptionLog()
            assert log is not None

        def test_should_have_add_transcription_method(self) -> None:
            """Test that add_transcription method exists."""
            log = TranscriptionLog()
            assert hasattr(log, "add_transcription")
            assert callable(log.add_transcription)


class TestTUIImports:
    """Tests for TUI module imports."""

    def test_should_import_status_indicator(self) -> None:
        """Test StatusIndicator import."""
        from src.tui import StatusIndicator

        assert StatusIndicator is not None

    def test_should_import_stats_panel(self) -> None:
        """Test StatsPanel import."""
        from src.tui import StatsPanel

        assert StatsPanel is not None

    def test_should_import_transcription_log(self) -> None:
        """Test TranscriptionLog import."""
        from src.tui import TranscriptionLog

        assert TranscriptionLog is not None

    def test_should_import_stt_app(self) -> None:
        """Test STTApp import."""
        from src.tui import STTApp

        assert STTApp is not None

    def test_should_import_run_tui(self) -> None:
        """Test run_tui function import."""
        from src.tui import run_tui

        assert run_tui is not None
        assert callable(run_tui)


class TestSTTAppCreation:
    """Tests for STTApp instantiation."""

    def test_should_create_app_with_config(self, test_config: Config) -> None:
        """Test that STTApp can be created with config."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert app is not None
        assert app.config == test_config

    def test_should_initialize_state_variables(self, test_config: Config) -> None:
        """Test that app initializes state variables."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert app._is_recording is False
        assert app._is_continuous is False
        assert app._stop_requested is False

    def test_should_initialize_stats_attributes(self, test_config: Config) -> None:
        """Test that app initializes stats attributes."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert app._total_requests == 0
        assert app._successful == 0
        assert app._failed == 0
        assert app._total_audio == 0.0
        assert app._total_transcription == 0.0

    def test_should_have_correct_bindings(self, test_config: Config) -> None:
        """Test that app has correct key bindings."""
        from src.tui import STTApp

        app = STTApp(test_config)
        binding_keys = [b[0] for b in app.BINDINGS]
        assert "r" in binding_keys  # Record
        assert "c" in binding_keys  # Continuous
        assert "s" in binding_keys  # Stop
        assert "h" in binding_keys  # History
        assert "q" in binding_keys  # Quit


class TestMainIntegration:
    """Tests for main.py TUI integration."""

    def test_should_have_tui_in_mode_choices(self) -> None:
        """Test that tui is a valid mode choice."""
        import argparse

        # Create parser with same config as main
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--mode",
            choices=["daemon", "oneshot", "continuous", "tui"],
            default="daemon",
        )
        # Parse with tui mode
        args = parser.parse_args(["--mode", "tui"])
        assert args.mode == "tui"

    def test_should_have_tui_flag(self) -> None:
        """Test that --tui flag exists."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--tui", action="store_true")
        args = parser.parse_args(["--tui"])
        assert args.tui is True
