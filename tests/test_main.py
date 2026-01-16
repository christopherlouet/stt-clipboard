#!/usr/bin/env python3
"""Tests for main module - STT service orchestration."""

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.config import (
    AudioConfig,
    ClipboardConfig,
    Config,
    HotkeyConfig,
    LoggingConfig,
    PasteConfig,
    PunctuationConfig,
    TranscriptionConfig,
    VADConfig,
)
from src.hotkey import TriggerType
from src.main import STTService, setup_logging


@pytest.fixture
def mock_config() -> Config:
    """Create a mock configuration for testing."""
    return Config(
        audio=AudioConfig(
            sample_rate=16000,
            channels=1,
            silence_duration=1.2,
            min_speech_duration=0.3,
            max_recording_duration=30,
            blocksize=512,
        ),
        vad=VADConfig(
            threshold=0.5,
            min_silence_duration_ms=300,
            speech_pad_ms=300,
        ),
        transcription=TranscriptionConfig(
            model_size="tiny",
            language="fr",
            device="cpu",
            compute_type="int8",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            download_root="./models",
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
            enabled=False,  # Disabled for simpler testing
            timeout=2.0,
            delay_ms=100,
            preferred_tool="auto",
        ),
        logging=LoggingConfig(
            level="INFO",
            file="",  # Empty string to skip file logging in tests
            format="<level>{message}</level>",
        ),
        hotkey=HotkeyConfig(
            enabled=False,
            socket_path="/tmp/test-stt.sock",
        ),
    )


class TestSTTServiceInit:
    """Tests for STTService initialization."""

    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    def test_initializes_with_config(
        self,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that service initializes with provided config."""
        service = STTService(mock_config)

        assert service.config == mock_config
        mock_transcriber.assert_called_once_with(mock_config.transcription)
        mock_recorder.assert_called_once_with(mock_config.audio, mock_config.vad)
        mock_processor.assert_called_once()

    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    def test_initializes_stats(
        self,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that stats are initialized correctly."""
        service = STTService(mock_config)

        assert service.stats["total_requests"] == 0
        assert service.stats["successful_transcriptions"] == 0
        assert service.stats["failed_transcriptions"] == 0
        assert service.stats["total_transcription_time"] == 0.0
        assert service.stats["total_audio_duration"] == 0.0

    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    def test_autopaster_disabled_when_paste_disabled(
        self,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that autopaster is None when paste is disabled."""
        mock_config.paste.enabled = False

        service = STTService(mock_config)

        assert service.autopaster is None

    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.create_autopaster")
    def test_autopaster_created_when_paste_enabled(
        self,
        mock_create_autopaster: MagicMock,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that autopaster is created when paste is enabled."""
        mock_config.paste.enabled = True
        mock_paster = MagicMock()
        mock_create_autopaster.return_value = mock_paster

        service = STTService(mock_config)

        assert service.autopaster == mock_paster
        mock_create_autopaster.assert_called_once_with(
            preferred_tool=mock_config.paste.preferred_tool,
            timeout=mock_config.paste.timeout,
        )


class TestSTTServiceInitialize:
    """Tests for STTService.initialize method."""

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    async def test_loads_whisper_model(
        self,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test that initialize loads the Whisper model."""
        mock_transcriber = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber

        service = STTService(mock_config)
        await service.initialize()

        mock_transcriber.load_model.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    async def test_loads_vad_model(
        self,
        mock_processor: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that initialize loads the VAD model."""
        mock_recorder = MagicMock()
        mock_recorder_class.return_value = mock_recorder

        service = STTService(mock_config)
        await service.initialize()

        mock_recorder._load_vad_model.assert_called_once()


class TestSTTServiceProcessRequest:
    """Tests for STTService.process_request method."""

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.copy_to_clipboard")
    @patch("src.main.notify_recording_started")
    @patch("src.main.notify_text_copied")
    async def test_successful_transcription(
        self,
        mock_notify_copied: MagicMock,
        mock_notify_started: MagicMock,
        mock_copy: MagicMock,
        mock_processor_class: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test successful transcription flow."""
        # Setup mocks
        audio_data = np.zeros(16000, dtype=np.float32)  # 1 second of audio

        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = audio_data
        mock_recorder_class.return_value = mock_recorder

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "bonjour"
        mock_transcriber.detected_language = "fr"
        mock_transcriber_class.return_value = mock_transcriber

        mock_processor = MagicMock()
        mock_processor.process.return_value = "Bonjour"
        mock_processor_class.return_value = mock_processor

        mock_copy.return_value = True

        # Execute
        service = STTService(mock_config)
        result = await service.process_request()

        # Verify
        assert result == "Bonjour"
        assert service.stats["total_requests"] == 1
        assert service.stats["successful_transcriptions"] == 1
        assert service.stats["failed_transcriptions"] == 0
        mock_notify_started.assert_called_once()
        mock_notify_copied.assert_called_once_with("Bonjour")

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.notify_recording_started")
    async def test_returns_none_when_audio_recording_fails(
        self,
        mock_notify_started: MagicMock,
        mock_processor: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that None is returned when audio recording fails."""
        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = None
        mock_recorder_class.return_value = mock_recorder

        service = STTService(mock_config)
        result = await service.process_request()

        assert result is None
        assert service.stats["failed_transcriptions"] == 1

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.notify_recording_started")
    async def test_returns_none_when_transcription_empty(
        self,
        mock_notify_started: MagicMock,
        mock_processor: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test that None is returned when transcription is empty."""
        audio_data = np.zeros(16000, dtype=np.float32)

        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = audio_data
        mock_recorder_class.return_value = mock_recorder

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""
        mock_transcriber_class.return_value = mock_transcriber

        service = STTService(mock_config)
        result = await service.process_request()

        assert result is None
        assert service.stats["failed_transcriptions"] == 1

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.copy_to_clipboard")
    @patch("src.main.notify_recording_started")
    async def test_returns_none_when_clipboard_fails(
        self,
        mock_notify_started: MagicMock,
        mock_copy: MagicMock,
        mock_processor_class: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test that None is returned when clipboard copy fails."""
        audio_data = np.zeros(16000, dtype=np.float32)

        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = audio_data
        mock_recorder_class.return_value = mock_recorder

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "bonjour"
        mock_transcriber.detected_language = "fr"
        mock_transcriber_class.return_value = mock_transcriber

        mock_processor = MagicMock()
        mock_processor.process.return_value = "Bonjour"
        mock_processor_class.return_value = mock_processor

        mock_copy.return_value = False

        service = STTService(mock_config)
        result = await service.process_request()

        assert result is None
        assert service.stats["failed_transcriptions"] == 1

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.notify_recording_started")
    async def test_skips_punctuation_when_disabled(
        self,
        mock_notify_started: MagicMock,
        mock_processor_class: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test that punctuation processing is skipped when disabled."""
        mock_config.punctuation.enabled = False
        mock_config.clipboard.enabled = False  # Skip clipboard for simpler test

        audio_data = np.zeros(16000, dtype=np.float32)

        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = audio_data
        mock_recorder_class.return_value = mock_recorder

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "bonjour"
        mock_transcriber_class.return_value = mock_transcriber

        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        service = STTService(mock_config)
        result = await service.process_request()

        # Processor.process should NOT be called
        mock_processor.process.assert_not_called()
        assert result == "bonjour"

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.notify_recording_started")
    async def test_handles_exception_gracefully(
        self,
        mock_notify_started: MagicMock,
        mock_processor: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that exceptions are handled gracefully."""
        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.side_effect = RuntimeError("Test error")
        mock_recorder_class.return_value = mock_recorder

        service = STTService(mock_config)
        result = await service.process_request()

        assert result is None
        assert service.stats["failed_transcriptions"] == 1


class TestSTTServiceShutdown:
    """Tests for STTService.shutdown method."""

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    async def test_stops_trigger_server_if_running(
        self,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that shutdown stops the trigger server."""
        service = STTService(mock_config)
        mock_server = AsyncMock()
        service.trigger_server = mock_server

        await service.shutdown()

        mock_server.stop.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    async def test_shutdown_without_trigger_server(
        self,
        mock_processor: MagicMock,
        mock_recorder: MagicMock,
        mock_transcriber: MagicMock,
        mock_config: Config,
    ):
        """Test that shutdown works when trigger server is None."""
        service = STTService(mock_config)
        service.trigger_server = None

        # Should not raise
        await service.shutdown()


class TestSetupLogging:
    """Tests for setup_logging function."""

    @patch("src.main.logger")
    def test_removes_default_handler(self, mock_logger: MagicMock, mock_config: Config):
        """Test that the default logger handler is removed."""
        setup_logging(mock_config)

        mock_logger.remove.assert_called_once()

    @patch("src.main.logger")
    def test_adds_stderr_handler(self, mock_logger: MagicMock, mock_config: Config):
        """Test that a stderr handler is added."""
        setup_logging(mock_config)

        # logger.add should be called at least once (for stderr)
        assert mock_logger.add.call_count >= 1

    @patch("src.main.logger")
    def test_adds_file_handler_when_configured(self, mock_logger: MagicMock, mock_config: Config):
        """Test that a file handler is added when configured."""
        mock_config.logging.file = "/tmp/test.log"

        with patch("pathlib.Path.mkdir"):
            setup_logging(mock_config)

        # logger.add should be called twice (stderr + file)
        assert mock_logger.add.call_count == 2


class TestTriggerTypeHandling:
    """Tests for trigger type handling in process_request."""

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.copy_to_clipboard")
    @patch("src.main.notify_recording_started")
    @patch("src.main.notify_text_copied")
    @patch("src.main.create_autopaster")
    async def test_auto_paste_on_paste_trigger(
        self,
        mock_create_autopaster: MagicMock,
        mock_notify_copied: MagicMock,
        mock_notify_started: MagicMock,
        mock_copy: MagicMock,
        mock_processor_class: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test that auto-paste is triggered on PASTE trigger type."""
        mock_config.paste.enabled = True

        # Setup mocks
        audio_data = np.zeros(16000, dtype=np.float32)

        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = audio_data
        mock_recorder_class.return_value = mock_recorder

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "bonjour"
        mock_transcriber.detected_language = "fr"
        mock_transcriber_class.return_value = mock_transcriber

        mock_processor = MagicMock()
        mock_processor.process.return_value = "Bonjour"
        mock_processor_class.return_value = mock_processor

        mock_copy.return_value = True

        mock_paster = MagicMock()
        mock_paster.paste.return_value = True
        mock_create_autopaster.return_value = mock_paster

        # Execute
        service = STTService(mock_config)
        result = await service.process_request(trigger_type=TriggerType.PASTE)

        # Verify
        assert result == "Bonjour"
        mock_paster.paste.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.main.WhisperTranscriber")
    @patch("src.main.AudioRecorder")
    @patch("src.main.PunctuationProcessor")
    @patch("src.main.copy_to_clipboard")
    @patch("src.main.notify_recording_started")
    @patch("src.main.notify_text_copied")
    async def test_no_paste_on_copy_trigger(
        self,
        mock_notify_copied: MagicMock,
        mock_notify_started: MagicMock,
        mock_copy: MagicMock,
        mock_processor_class: MagicMock,
        mock_recorder_class: MagicMock,
        mock_transcriber_class: MagicMock,
        mock_config: Config,
    ):
        """Test that paste is not triggered on COPY trigger type."""
        mock_config.paste.enabled = True

        # Setup mocks
        audio_data = np.zeros(16000, dtype=np.float32)

        mock_recorder = MagicMock()
        mock_recorder.record_until_silence.return_value = audio_data
        mock_recorder_class.return_value = mock_recorder

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "bonjour"
        mock_transcriber.detected_language = "fr"
        mock_transcriber_class.return_value = mock_transcriber

        mock_processor = MagicMock()
        mock_processor.process.return_value = "Bonjour"
        mock_processor_class.return_value = mock_processor

        mock_copy.return_value = True

        # Execute - COPY trigger should not auto-paste
        # We need to patch create_autopaster to avoid RuntimeError
        with patch("src.main.create_autopaster") as mock_create:
            mock_paster = MagicMock()
            mock_create.return_value = mock_paster
            service = STTService(mock_config)
            await service.process_request(trigger_type=TriggerType.COPY)

            # Verify paste was NOT called
            mock_paster.paste.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
