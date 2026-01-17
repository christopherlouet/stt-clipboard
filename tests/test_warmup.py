"""Tests for model warmup functionality."""

import time
from unittest.mock import MagicMock, patch

import numpy as np

from src.warmup import WarmupResult, warmup_transcriber


class TestWarmupTranscriber:
    """Tests for warmup_transcriber function."""

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_calls_transcribe(self, mock_transcriber_class: MagicMock):
        """Test warmup performs a transcription."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        result = warmup_transcriber(mock_transcriber)

        mock_transcriber.transcribe.assert_called_once()
        assert result.success is True

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_uses_silent_audio(self, mock_transcriber_class: MagicMock):
        """Test warmup uses silent/near-silent audio."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        warmup_transcriber(mock_transcriber)

        # Get the audio passed to transcribe
        call_args = mock_transcriber.transcribe.call_args
        audio = call_args[0][0]

        # Audio should be quiet (near-zero values)
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert np.abs(audio).max() < 0.1  # Should be very quiet

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_measures_time(self, mock_transcriber_class: MagicMock):
        """Test warmup measures execution time."""
        mock_transcriber = MagicMock()

        def slow_transcribe(audio):
            time.sleep(0.05)  # 50ms delay
            return ""

        mock_transcriber.transcribe.side_effect = slow_transcribe

        result = warmup_transcriber(mock_transcriber)

        assert result.duration_seconds >= 0.05
        assert result.duration_seconds < 1.0  # Reasonable upper bound

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_returns_result_object(self, mock_transcriber_class: MagicMock):
        """Test warmup returns WarmupResult with all fields."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        result = warmup_transcriber(mock_transcriber)

        assert isinstance(result, WarmupResult)
        assert hasattr(result, "success")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "audio_duration_seconds")
        assert hasattr(result, "error_message")

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_handles_transcription_error(self, mock_transcriber_class: MagicMock):
        """Test warmup handles transcription errors gracefully."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.side_effect = RuntimeError("Model error")

        result = warmup_transcriber(mock_transcriber)

        assert result.success is False
        assert result.error_message is not None
        assert "Model error" in result.error_message

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_uses_configurable_duration(self, mock_transcriber_class: MagicMock):
        """Test warmup uses specified audio duration."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        result = warmup_transcriber(mock_transcriber, audio_duration=0.5)

        call_args = mock_transcriber.transcribe.call_args
        audio = call_args[0][0]

        # Audio should be ~0.5 seconds at 16kHz
        expected_samples = int(0.5 * 16000)
        assert len(audio) == expected_samples
        assert result.audio_duration_seconds == 0.5

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_default_duration_one_second(self, mock_transcriber_class: MagicMock):
        """Test warmup uses 1 second audio by default."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        result = warmup_transcriber(mock_transcriber)

        call_args = mock_transcriber.transcribe.call_args
        audio = call_args[0][0]

        # Default should be 1 second at 16kHz
        expected_samples = 16000
        assert len(audio) == expected_samples
        assert result.audio_duration_seconds == 1.0


class TestWarmupResult:
    """Tests for WarmupResult dataclass."""

    def test_warmup_result_creation(self):
        """Test WarmupResult can be created with all fields."""
        result = WarmupResult(
            success=True,
            duration_seconds=0.5,
            audio_duration_seconds=1.0,
            error_message=None,
        )

        assert result.success is True
        assert result.duration_seconds == 0.5
        assert result.audio_duration_seconds == 1.0
        assert result.error_message is None

    def test_warmup_result_with_error(self):
        """Test WarmupResult with error message."""
        result = WarmupResult(
            success=False,
            duration_seconds=0.1,
            audio_duration_seconds=1.0,
            error_message="Something went wrong",
        )

        assert result.success is False
        assert result.error_message == "Something went wrong"


class TestWarmupIntegration:
    """Integration tests for warmup with real-ish transcriber."""

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_with_empty_result(self, mock_transcriber_class: MagicMock):
        """Test warmup handles empty transcription result."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        result = warmup_transcriber(mock_transcriber)

        assert result.success is True
        # Empty result is expected for silent audio

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_with_whitespace_result(self, mock_transcriber_class: MagicMock):
        """Test warmup handles whitespace-only transcription."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "   \n\t   "

        result = warmup_transcriber(mock_transcriber)

        assert result.success is True

    @patch("src.warmup.WhisperTranscriber")
    def test_warmup_logs_duration(self, mock_transcriber_class: MagicMock):
        """Test warmup logs the warmup duration."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = ""

        with patch("src.warmup.logger") as mock_logger:
            warmup_transcriber(mock_transcriber)

            # Should log warmup completion
            mock_logger.info.assert_called()
            log_message = str(mock_logger.info.call_args)
            assert "warmup" in log_message.lower() or "Warmup" in log_message
