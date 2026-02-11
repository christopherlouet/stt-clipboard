#!/usr/bin/env python3
"""Tests for memory management: model unloading, idle timer, gc.collect."""

from unittest.mock import MagicMock, patch

import pytest

from src.config import Config, MemoryConfig, TranscriptionConfig
from src.transcription import WhisperTranscriber


class TestUnloadModelEnhanced:
    """Tests for enhanced unload_model with gc.collect."""

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_unload_calls_gc_collect(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that unload_model calls gc.collect to free RSS memory."""
        mock_whisper_model.return_value = MagicMock()

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        with patch("src.transcription.gc.collect") as mock_gc:
            transcriber.unload_model()
            mock_gc.assert_called_once()

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_unload_sets_model_to_none(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that unload_model sets model to None."""
        mock_whisper_model.return_value = MagicMock()

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        transcriber.unload_model()

        assert transcriber.model is None

    @patch("src.transcription.Path.mkdir")
    def test_unload_when_not_loaded_does_not_gc(self, mock_mkdir: MagicMock):
        """Test that unload when model not loaded skips gc.collect."""
        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        with patch("src.transcription.gc.collect") as mock_gc:
            transcriber.unload_model()
            mock_gc.assert_not_called()


class TestIsLoadedProperty:
    """Tests for is_loaded property."""

    @patch("src.transcription.Path.mkdir")
    def test_is_loaded_false_initially(self, mock_mkdir: MagicMock):
        """Test that is_loaded is False when model not loaded."""
        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        assert transcriber.is_loaded is False

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_is_loaded_true_after_load(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that is_loaded is True after loading model."""
        mock_whisper_model.return_value = MagicMock()

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        assert transcriber.is_loaded is True

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_is_loaded_false_after_unload(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that is_loaded is False after unloading."""
        mock_whisper_model.return_value = MagicMock()

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()
        transcriber.unload_model()

        assert transcriber.is_loaded is False


class TestIdleTimer:
    """Tests for idle timer in STTService."""

    @patch("src.transcription.Path.mkdir")
    def test_idle_timer_created_when_auto_unload_enabled(self, mock_mkdir: MagicMock):
        """Test that idle timer is available when auto_unload_model is True."""
        config = Config(memory=MemoryConfig(auto_unload_model=True, idle_timeout_seconds=60))
        from src.main import STTService

        with patch.object(STTService, "__init__", lambda self, cfg: None):
            service = STTService.__new__(STTService)
            service.config = config
            service._idle_timer = None
            service.transcriber = MagicMock()

            assert service.config.memory.auto_unload_model is True

    @patch("src.transcription.Path.mkdir")
    def test_idle_timer_not_created_when_disabled(self, mock_mkdir: MagicMock):
        """Test that idle timer is not used when auto_unload_model is False."""
        config = Config(memory=MemoryConfig(auto_unload_model=False))

        assert config.memory.auto_unload_model is False

    def test_reset_idle_timer_cancels_existing(self):
        """Test that resetting idle timer cancels the previous one."""
        from src.main import STTService

        with patch.object(STTService, "__init__", lambda self, cfg: None):
            service = STTService.__new__(STTService)
            service.config = Config(
                memory=MemoryConfig(auto_unload_model=True, idle_timeout_seconds=60)
            )
            service.transcriber = MagicMock()
            service._idle_timer = MagicMock()

            old_timer = service._idle_timer
            service._reset_idle_timer()

            old_timer.cancel.assert_called_once()

    def test_reset_idle_timer_does_nothing_when_disabled(self):
        """Test that reset_idle_timer does nothing when auto_unload is disabled."""
        from src.main import STTService

        with patch.object(STTService, "__init__", lambda self, cfg: None):
            service = STTService.__new__(STTService)
            service.config = Config(memory=MemoryConfig(auto_unload_model=False))
            service.transcriber = MagicMock()
            service._idle_timer = None

            service._reset_idle_timer()

            assert service._idle_timer is None

    @pytest.mark.asyncio
    async def test_on_idle_timeout_unloads_model(self):
        """Test that idle timeout triggers model unloading."""
        from src.main import STTService

        with patch.object(STTService, "__init__", lambda self, cfg: None):
            service = STTService.__new__(STTService)
            service.config = Config(
                memory=MemoryConfig(auto_unload_model=True, idle_timeout_seconds=1)
            )
            service.transcriber = MagicMock()
            service._idle_timer = None

            service._on_idle_timeout()

            service.transcriber.unload_model.assert_called_once()

    def test_default_tui_mode_enables_auto_unload(self):
        """Test that default config has auto_unload_model=True (for TUI)."""
        config = Config()
        assert config.memory.auto_unload_model is True
        assert config.memory.idle_timeout_seconds == 300

    def test_idle_timeout_default_5_minutes(self):
        """Test that default idle timeout is 5 minutes (300 seconds)."""
        config = MemoryConfig()
        assert config.idle_timeout_seconds == 300


class TestTUIIdleTimerIntegration:
    """Tests for idle timer integration in TUI (T009)."""

    def test_stt_app_has_idle_timer_attribute(self):
        """Test that STTApp has _idle_timer attribute."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=True, idle_timeout_seconds=60))
        app = STTApp(config)
        assert hasattr(app, "_idle_timer")
        assert app._idle_timer is None

    def test_stt_app_has_reset_idle_timer_method(self):
        """Test that STTApp has _reset_idle_timer method."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=True))
        app = STTApp(config)
        assert hasattr(app, "_reset_idle_timer")
        assert callable(app._reset_idle_timer)

    def test_stt_app_has_on_idle_timeout_method(self):
        """Test that STTApp has _on_idle_timeout method."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=True))
        app = STTApp(config)
        assert hasattr(app, "_on_idle_timeout")
        assert callable(app._on_idle_timeout)

    def test_stt_app_reset_idle_timer_does_nothing_when_disabled(self):
        """Test that _reset_idle_timer does nothing when auto_unload is disabled."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=False))
        app = STTApp(config)
        app._reset_idle_timer()
        assert app._idle_timer is None

    def test_stt_app_on_idle_timeout_unloads_model(self):
        """Test that _on_idle_timeout calls unload_model on transcriber."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=True, idle_timeout_seconds=60))
        app = STTApp(config)
        app.transcriber = MagicMock()
        app.transcriber.is_loaded = True

        app._on_idle_timeout()

        app.transcriber.unload_model.assert_called_once()

    def test_stt_app_on_idle_timeout_skips_when_not_loaded(self):
        """Test that _on_idle_timeout does nothing when model not loaded."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=True))
        app = STTApp(config)
        app.transcriber = MagicMock()
        app.transcriber.is_loaded = False

        app._on_idle_timeout()

        app.transcriber.unload_model.assert_not_called()

    def test_stt_app_reset_idle_timer_cancels_existing(self):
        """Test that resetting idle timer cancels the existing one."""
        from src.tui import STTApp

        config = Config(memory=MemoryConfig(auto_unload_model=True, idle_timeout_seconds=60))
        app = STTApp(config)
        app._idle_timer = MagicMock()
        old_timer = app._idle_timer

        app._reset_idle_timer()

        old_timer.cancel.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
