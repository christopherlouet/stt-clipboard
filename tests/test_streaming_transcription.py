"""Tests for streaming transcription functionality."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import numpy as np

from src.config import TranscriptionConfig
from src.transcription import WhisperTranscriber


class TestTranscribeStreaming:
    """Tests for transcribe_streaming method."""

    @patch("src.transcription.WhisperModel")
    def test_yields_segments_as_iterator(self, mock_whisper_model: MagicMock):
        """Test streaming transcription yields segments one by one."""
        # Setup mock
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        # Create mock segments
        mock_segment1 = MagicMock()
        mock_segment1.text = "Hello"
        mock_segment1.start = 0.0
        mock_segment1.end = 1.0

        mock_segment2 = MagicMock()
        mock_segment2.text = "world"
        mock_segment2.start = 1.0
        mock_segment2.end = 2.0

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (
            iter([mock_segment1, mock_segment2]),
            mock_info,
        )

        # Create transcriber and load model
        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        # Generate test audio
        audio = np.zeros(16000, dtype=np.float32)

        # Call streaming transcribe
        result = transcriber.transcribe_streaming(audio)

        # Should return an iterator
        assert isinstance(result, Iterator)

    @patch("src.transcription.WhisperModel")
    def test_streaming_yields_text_and_timing(self, mock_whisper_model: MagicMock):
        """Test streaming yields text with timing information."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_segment = MagicMock()
        mock_segment.text = " Hello "
        mock_segment.start = 0.5
        mock_segment.end = 1.5

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (iter([mock_segment]), mock_info)

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(16000, dtype=np.float32)
        segments = list(transcriber.transcribe_streaming(audio))

        assert len(segments) == 1
        text, start, end = segments[0]
        assert text == "Hello"  # Should be stripped
        assert start == 0.5
        assert end == 1.5

    @patch("src.transcription.WhisperModel")
    def test_streaming_multiple_segments(self, mock_whisper_model: MagicMock):
        """Test streaming with multiple segments."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_segments = []
        for i in range(3):
            seg = MagicMock()
            seg.text = f"Segment {i}"
            seg.start = float(i)
            seg.end = float(i + 1)
            mock_segments.append(seg)

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (iter(mock_segments), mock_info)

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(48000, dtype=np.float32)
        segments = list(transcriber.transcribe_streaming(audio))

        assert len(segments) == 3
        for i, (text, start, end) in enumerate(segments):
            assert text == f"Segment {i}"
            assert start == float(i)
            assert end == float(i + 1)

    @patch("src.transcription.WhisperModel")
    def test_streaming_updates_detected_language(self, mock_whisper_model: MagicMock):
        """Test streaming updates detected_language attribute."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_segment = MagicMock()
        mock_segment.text = "Bonjour"
        mock_segment.start = 0.0
        mock_segment.end = 1.0

        mock_info = MagicMock()
        mock_info.language = "fr"

        mock_model_instance.transcribe.return_value = (iter([mock_segment]), mock_info)

        config = TranscriptionConfig(language="")
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(16000, dtype=np.float32)

        # Consume the iterator
        list(transcriber.transcribe_streaming(audio))

        assert transcriber.detected_language == "fr"

    @patch("src.transcription.WhisperModel")
    def test_streaming_loads_model_if_not_loaded(self, mock_whisper_model: MagicMock):
        """Test streaming loads model if not already loaded."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_segment = MagicMock()
        mock_segment.text = "Test"
        mock_segment.start = 0.0
        mock_segment.end = 1.0

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (iter([mock_segment]), mock_info)

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        # Don't load model explicitly

        audio = np.zeros(16000, dtype=np.float32)
        list(transcriber.transcribe_streaming(audio))

        # Model should have been loaded
        assert transcriber.model is not None

    @patch("src.transcription.WhisperModel")
    def test_streaming_skips_empty_segments(self, mock_whisper_model: MagicMock):
        """Test streaming skips segments with empty text."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_segment1 = MagicMock()
        mock_segment1.text = "Hello"
        mock_segment1.start = 0.0
        mock_segment1.end = 1.0

        mock_segment2 = MagicMock()
        mock_segment2.text = "   "  # Empty after strip
        mock_segment2.start = 1.0
        mock_segment2.end = 2.0

        mock_segment3 = MagicMock()
        mock_segment3.text = "World"
        mock_segment3.start = 2.0
        mock_segment3.end = 3.0

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (
            iter([mock_segment1, mock_segment2, mock_segment3]),
            mock_info,
        )

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(48000, dtype=np.float32)
        segments = list(transcriber.transcribe_streaming(audio))

        # Should only have 2 segments (empty one skipped)
        assert len(segments) == 2
        assert segments[0][0] == "Hello"
        assert segments[1][0] == "World"

    @patch("src.transcription.WhisperModel")
    def test_streaming_handles_empty_transcription(self, mock_whisper_model: MagicMock):
        """Test streaming handles case with no segments."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (iter([]), mock_info)

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(16000, dtype=np.float32)
        segments = list(transcriber.transcribe_streaming(audio))

        assert len(segments) == 0


class TestTranscribeStreamingToText:
    """Tests for transcribe_streaming_to_text convenience method."""

    @patch("src.transcription.WhisperModel")
    def test_collects_all_segments_to_text(self, mock_whisper_model: MagicMock):
        """Test convenience method collects all segments into text."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_segment1 = MagicMock()
        mock_segment1.text = "Hello"
        mock_segment1.start = 0.0
        mock_segment1.end = 1.0

        mock_segment2 = MagicMock()
        mock_segment2.text = "world"
        mock_segment2.start = 1.0
        mock_segment2.end = 2.0

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (
            iter([mock_segment1, mock_segment2]),
            mock_info,
        )

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(32000, dtype=np.float32)
        text = transcriber.transcribe_streaming_to_text(audio)

        assert text == "Hello world"

    @patch("src.transcription.WhisperModel")
    def test_returns_empty_string_for_no_segments(self, mock_whisper_model: MagicMock):
        """Test returns empty string when no segments."""
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model_instance.transcribe.return_value = (iter([]), mock_info)

        config = TranscriptionConfig()
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        audio = np.zeros(16000, dtype=np.float32)
        text = transcriber.transcribe_streaming_to_text(audio)

        assert text == ""
