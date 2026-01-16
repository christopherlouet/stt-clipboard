#!/usr/bin/env python3
"""Tests for transcription module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.config import TranscriptionConfig
from src.transcription import WhisperTranscriber, get_transcriber, transcribe_audio


class TestWhisperTranscriberInit:
    """Tests for WhisperTranscriber initialization."""

    @patch("src.transcription.Path.mkdir")
    def test_initializes_with_config(self, mock_mkdir: MagicMock):
        """Test that transcriber initializes with provided config."""
        config = TranscriptionConfig(
            model_size="tiny",
            language="fr",
            device="cpu",
            compute_type="int8",
        )

        transcriber = WhisperTranscriber(config)

        assert transcriber.config == config
        assert transcriber.model is None
        assert transcriber.load_time == 0.0
        assert transcriber.detected_language is None

    @patch("src.transcription.Path.mkdir")
    def test_creates_download_directory(self, mock_mkdir: MagicMock):
        """Test that download directory is created."""
        config = TranscriptionConfig(download_root="./test_models")

        WhisperTranscriber(config)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestWhisperTranscriberLoadModel:
    """Tests for WhisperTranscriber.load_model method."""

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_loads_model_successfully(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that model is loaded successfully."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        config = TranscriptionConfig(model_size="tiny")
        transcriber = WhisperTranscriber(config)

        transcriber.load_model()

        assert transcriber.model == mock_model_instance
        assert transcriber.load_time > 0
        mock_whisper_model.assert_called_once_with(
            model_size_or_path="tiny",
            device="cpu",
            compute_type="int8",
            download_root="./models",
            cpu_threads=0,
            num_workers=1,
        )

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_does_not_reload_if_already_loaded(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that model is not reloaded if already loaded."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        transcriber.load_model()
        transcriber.load_model()  # Second call

        # Should only be called once
        assert mock_whisper_model.call_count == 1

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_raises_error_on_load_failure(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that RuntimeError is raised on load failure."""
        mock_whisper_model.side_effect = RuntimeError("Failed to load model")

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        with pytest.raises(RuntimeError, match="Model loading failed"):
            transcriber.load_model()


class TestWhisperTranscriberTranscribe:
    """Tests for WhisperTranscriber.transcribe method."""

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_transcribes_audio_successfully(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test successful transcription."""
        # Setup mock
        mock_segment = MagicMock()
        mock_segment.text = " bonjour "
        mock_info = MagicMock()
        mock_info.language = "fr"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        # Create transcriber and audio
        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        # Transcribe
        result = transcriber.transcribe(audio)

        assert result == "bonjour"
        assert transcriber.detected_language == "fr"

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_loads_model_if_not_loaded(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that model is loaded if not already loaded."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        # Should load model automatically
        transcriber.transcribe(audio)

        mock_whisper_model.assert_called_once()

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_handles_empty_language_for_auto_detect(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that empty language string is converted to None for auto-detect."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        # Empty string should trigger auto-detection
        config = TranscriptionConfig(language="")
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        transcriber.transcribe(audio)

        # Check that language=None was passed to transcribe
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] is None

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_converts_int16_audio_to_float32(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that int16 audio is converted to float32."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        # Create int16 audio
        audio = np.zeros(16000, dtype=np.int16)

        transcriber.transcribe(audio)

        # The audio passed to transcribe should be float32
        call_args = mock_model.transcribe.call_args[0]
        assert call_args[0].dtype == np.float32

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_normalizes_audio_if_needed(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that audio is normalized if values exceed [-1, 1]."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        # Create audio with values > 1
        audio = np.array([2.0, -2.0, 1.5], dtype=np.float32)

        transcriber.transcribe(audio)

        # The audio passed should be normalized
        call_args = mock_model.transcribe.call_args[0]
        assert np.abs(call_args[0]).max() <= 1.0

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_joins_multiple_segments(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that multiple segments are joined."""
        mock_segment1 = MagicMock()
        mock_segment1.text = " hello "
        mock_segment2 = MagicMock()
        mock_segment2.text = " world "
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment1, mock_segment2], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        result = transcriber.transcribe(audio)

        assert result == "hello world"

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_raises_error_on_transcription_failure(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that RuntimeError is raised on transcription failure."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("Transcription failed")
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        with pytest.raises(RuntimeError, match="Transcription failed"):
            transcriber.transcribe(audio)


class TestWhisperTranscriberGetModelInfo:
    """Tests for WhisperTranscriber.get_model_info method."""

    @patch("src.transcription.Path.mkdir")
    def test_returns_model_info(self, mock_mkdir: MagicMock):
        """Test that model info is returned correctly."""
        config = TranscriptionConfig(
            model_size="base",
            language="en",
            device="cpu",
            compute_type="int8",
            beam_size=5,
        )
        transcriber = WhisperTranscriber(config)

        info = transcriber.get_model_info()

        assert info["model_size"] == "base"
        assert info["language"] == "en"
        assert info["device"] == "cpu"
        assert info["compute_type"] == "int8"
        assert info["beam_size"] == 5
        assert info["loaded"] is False
        assert info["load_time"] == 0.0

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_shows_loaded_status(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that loaded status is shown correctly."""
        mock_whisper_model.return_value = MagicMock()

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        info = transcriber.get_model_info()

        assert info["loaded"] is True
        assert info["load_time"] > 0


class TestWhisperTranscriberUnloadModel:
    """Tests for WhisperTranscriber.unload_model method."""

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_unloads_model(self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock):
        """Test that model is unloaded."""
        mock_whisper_model.return_value = MagicMock()

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        assert transcriber.model is not None

        transcriber.unload_model()

        assert transcriber.model is None

    @patch("src.transcription.Path.mkdir")
    def test_unload_when_not_loaded(self, mock_mkdir: MagicMock):
        """Test unload when model is not loaded."""
        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        # Should not raise
        transcriber.unload_model()

        assert transcriber.model is None


class TestGetTranscriber:
    """Tests for get_transcriber function."""

    @patch("src.transcription.Path.mkdir")
    def test_creates_default_transcriber(self, mock_mkdir: MagicMock):
        """Test that default transcriber is created."""
        # Reset singleton
        import src.transcription

        src.transcription._default_transcriber = None

        transcriber = get_transcriber()

        assert isinstance(transcriber, WhisperTranscriber)

    @patch("src.transcription.Path.mkdir")
    def test_returns_same_instance(self, mock_mkdir: MagicMock):
        """Test that same instance is returned."""
        import src.transcription

        src.transcription._default_transcriber = None

        transcriber1 = get_transcriber()
        transcriber2 = get_transcriber()

        assert transcriber1 is transcriber2

    @patch("src.transcription.Path.mkdir")
    def test_uses_provided_config(self, mock_mkdir: MagicMock):
        """Test that provided config is used."""
        import src.transcription

        src.transcription._default_transcriber = None

        config = TranscriptionConfig(model_size="base")
        transcriber = get_transcriber(config)

        assert transcriber.config.model_size == "base"


class TestTranscribeAudio:
    """Tests for transcribe_audio convenience function."""

    @patch("src.transcription.get_transcriber")
    def test_uses_transcriber(self, mock_get_transcriber: MagicMock):
        """Test that the convenience function uses the transcriber."""
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = "transcribed text"
        mock_get_transcriber.return_value = mock_transcriber

        audio = np.zeros(16000, dtype=np.float32)
        result = transcribe_audio(audio)

        assert result == "transcribed text"
        mock_transcriber.transcribe.assert_called_once_with(audio)


class TestTranscribeWithTimestamps:
    """Tests for WhisperTranscriber.transcribe_with_timestamps method."""

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_transcribes_with_timestamps_successfully(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test successful transcription with timestamps."""
        # Setup mock segment with timestamps
        mock_segment = MagicMock()
        mock_segment.text = " bonjour "
        mock_segment.start = 0.5
        mock_segment.end = 1.2
        mock_info = MagicMock()
        mock_info.language = "fr"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        result = transcriber.transcribe_with_timestamps(audio)

        assert len(result) == 1
        assert result[0] == ("bonjour", 0.5, 1.2)
        # Verify word_timestamps=True was passed
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["word_timestamps"] is True

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_transcribes_multiple_segments_with_timestamps(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test transcription with multiple segments."""
        mock_segment1 = MagicMock()
        mock_segment1.text = " hello "
        mock_segment1.start = 0.0
        mock_segment1.end = 0.8
        mock_segment2 = MagicMock()
        mock_segment2.text = " world "
        mock_segment2.start = 1.0
        mock_segment2.end = 1.5
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment1, mock_segment2], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        result = transcriber.transcribe_with_timestamps(audio)

        assert len(result) == 2
        assert result[0] == ("hello", 0.0, 0.8)
        assert result[1] == ("world", 1.0, 1.5)

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_loads_model_if_not_loaded_for_timestamps(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that model is loaded if not already loaded."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        # Should load model automatically
        transcriber.transcribe_with_timestamps(audio)

        mock_whisper_model.assert_called_once()

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_converts_int16_audio_for_timestamps(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that int16 audio is converted to float32 for timestamps."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        # Create int16 audio
        audio = np.zeros(16000, dtype=np.int16)

        transcriber.transcribe_with_timestamps(audio)

        # The audio passed to transcribe should be float32
        call_args = mock_model.transcribe.call_args[0]
        assert call_args[0].dtype == np.float32

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_normalizes_audio_for_timestamps(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that audio is normalized if values exceed [-1, 1]."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)

        # Create audio with values > 1
        audio = np.array([2.0, -2.0, 1.5], dtype=np.float32)

        transcriber.transcribe_with_timestamps(audio)

        # The audio passed should be normalized
        call_args = mock_model.transcribe.call_args[0]
        assert np.abs(call_args[0]).max() <= 1.0

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_raises_error_on_timestamps_failure(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that RuntimeError is raised on timestamps transcription failure."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("Transcription failed")
        mock_whisper_model.return_value = mock_model

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        with pytest.raises(RuntimeError, match="Transcription failed"):
            transcriber.transcribe_with_timestamps(audio)

    @patch("src.transcription.Path.mkdir")
    @patch("src.transcription.WhisperModel")
    def test_handles_empty_language_for_auto_detect_timestamps(
        self, mock_whisper_model: MagicMock, mock_mkdir: MagicMock
    ):
        """Test that empty language string triggers auto-detect for timestamps."""
        mock_segment = MagicMock()
        mock_segment.text = "test"
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_whisper_model.return_value = mock_model

        # Empty string should trigger auto-detection
        config = TranscriptionConfig(language="")
        transcriber = WhisperTranscriber(config)
        audio = np.zeros(16000, dtype=np.float32)

        transcriber.transcribe_with_timestamps(audio)

        # Check that language=None was passed to transcribe
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
