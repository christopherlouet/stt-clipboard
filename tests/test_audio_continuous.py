"""Tests for continuous recording mode in audio capture."""

import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.audio_capture import AudioRecorder
from src.config import AudioConfig, VADConfig


@pytest.fixture
def audio_config():
    """Create audio configuration for tests."""
    return AudioConfig(
        sample_rate=16000,
        channels=1,
        silence_duration=0.3,
        min_speech_duration=0.1,
        max_recording_duration=10,
        blocksize=512,
    )


@pytest.fixture
def vad_config():
    """Create VAD configuration for tests."""
    return VADConfig(
        threshold=0.5,
        min_silence_duration_ms=100,
        speech_pad_ms=100,
    )


class TestContinuousRecordingState:
    """Tests for continuous recording state management."""

    def test_initial_state_not_continuous(self, audio_config, vad_config):
        """Test that recorder starts not in continuous mode."""
        recorder = AudioRecorder(audio_config, vad_config)
        assert not recorder.is_continuous_recording()
        assert not recorder._continuous_mode

    def test_stop_continuous_sets_event(self, audio_config, vad_config):
        """Test that stop_continuous sets the stop event."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._continuous_mode = True
        recorder.is_recording = True
        recorder.stop_continuous()
        assert recorder._stop_continuous.is_set()

    def test_is_continuous_recording_requires_both_flags(self, audio_config, vad_config):
        """Test is_continuous_recording checks both flags."""
        recorder = AudioRecorder(audio_config, vad_config)

        # Neither flag set
        assert not recorder.is_continuous_recording()

        # Only continuous mode
        recorder._continuous_mode = True
        recorder.is_recording = False
        assert not recorder.is_continuous_recording()

        # Only is_recording
        recorder._continuous_mode = False
        recorder.is_recording = True
        assert not recorder.is_continuous_recording()

        # Both flags set
        recorder._continuous_mode = True
        recorder.is_recording = True
        assert recorder.is_continuous_recording()


class TestContinuousRecordingCallback:
    """Tests for audio callback behavior in continuous mode."""

    def test_callback_creates_segment_on_silence(self, audio_config, vad_config):
        """Test that callback creates segment when silence detected in continuous mode."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()
        recorder._continuous_mode = True
        recorder.is_recording = True
        recorder.speech_started = True

        # Fill buffer with some audio
        test_audio = np.random.randn(audio_config.sample_rate).astype(np.float32) * 0.5
        recorder.buffer.extend(test_audio)

        # Simulate silence detected (past silence threshold)
        recorder.last_speech_time = time.time() - audio_config.silence_duration - 0.1

        # Mock VAD to return no speech
        with patch.object(recorder, "_detect_speech", return_value=0.1):
            indata = np.zeros((audio_config.blocksize, 1), dtype=np.float32)
            recorder._audio_callback(indata, audio_config.blocksize, None, None)

        # Should have created a segment and signaled ready
        assert recorder._segment_ready.is_set()
        assert recorder._current_segment is not None
        assert len(recorder._current_segment) > 0

    def test_callback_resets_after_segment(self, audio_config, vad_config):
        """Test that callback resets state after segment in continuous mode."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()
        recorder._continuous_mode = True
        recorder.is_recording = True
        recorder.speech_started = True

        # Fill buffer
        test_audio = np.random.randn(audio_config.sample_rate).astype(np.float32) * 0.5
        recorder.buffer.extend(test_audio)

        # Simulate silence
        recorder.last_speech_time = time.time() - audio_config.silence_duration - 0.1

        with patch.object(recorder, "_detect_speech", return_value=0.1):
            indata = np.zeros((audio_config.blocksize, 1), dtype=np.float32)
            recorder._audio_callback(indata, audio_config.blocksize, None, None)

        # Buffer should be cleared and speech_started reset
        assert len(recorder.buffer) == 0
        assert not recorder.speech_started

    def test_callback_continues_recording_in_continuous_mode(self, audio_config, vad_config):
        """Test that is_recording stays True in continuous mode after silence."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()
        recorder._continuous_mode = True
        recorder.is_recording = True
        recorder.speech_started = True

        # Fill buffer
        test_audio = np.random.randn(audio_config.sample_rate).astype(np.float32) * 0.5
        recorder.buffer.extend(test_audio)

        # Simulate silence
        recorder.last_speech_time = time.time() - audio_config.silence_duration - 0.1

        with patch.object(recorder, "_detect_speech", return_value=0.1):
            indata = np.zeros((audio_config.blocksize, 1), dtype=np.float32)
            recorder._audio_callback(indata, audio_config.blocksize, None, None)

        # Should still be recording
        assert recorder.is_recording

    def test_callback_ignores_short_segments(self, audio_config, vad_config):
        """Test that callback ignores segments shorter than minimum."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()
        recorder._continuous_mode = True
        recorder.is_recording = True
        recorder.speech_started = True

        # Put very short audio in buffer (less than min_speech_samples)
        short_audio = np.random.randn(100).astype(np.float32) * 0.5
        recorder.buffer.extend(short_audio)

        # Simulate silence
        recorder.last_speech_time = time.time() - audio_config.silence_duration - 0.1

        with patch.object(recorder, "_detect_speech", return_value=0.1):
            indata = np.zeros((audio_config.blocksize, 1), dtype=np.float32)
            recorder._audio_callback(indata, audio_config.blocksize, None, None)

        # Should not have created a segment
        assert not recorder._segment_ready.is_set()
        assert recorder._current_segment is None


class TestContinuousRecordingIntegration:
    """Integration tests for continuous recording with mocked audio."""

    @patch("src.audio_capture.sd.InputStream")
    def test_record_continuous_yields_segments(self, mock_stream, audio_config, vad_config):
        """Test that record_continuous yields audio segments."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()

        # Prepare test segments
        segment1 = np.random.randn(audio_config.sample_rate).astype(np.float32) * 0.5
        segment2 = np.random.randn(audio_config.sample_rate).astype(np.float32) * 0.5

        def simulate_segments():
            """Simulate segment production in a separate thread."""
            time.sleep(0.1)
            recorder._current_segment = segment1
            recorder._segment_ready.set()
            time.sleep(0.1)
            recorder._current_segment = segment2
            recorder._segment_ready.set()
            time.sleep(0.1)
            recorder.stop_continuous()

        # Start simulation thread
        sim_thread = threading.Thread(target=simulate_segments)
        sim_thread.start()

        # Collect yielded segments
        segments = list(recorder.record_continuous())

        sim_thread.join()

        assert len(segments) >= 2

    @patch("src.audio_capture.sd.InputStream")
    def test_record_continuous_stops_on_stop_call(self, mock_stream, audio_config, vad_config):
        """Test that record_continuous stops when stop_continuous is called."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()

        def stop_after_delay():
            time.sleep(0.2)
            recorder.stop_continuous()

        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()

        # This should complete when stop is called
        list(recorder.record_continuous())  # Consume the generator
        stop_thread.join()

        # After stopping, continuous mode should be disabled
        assert not recorder._continuous_mode
        assert not recorder.is_recording

    @patch("src.audio_capture.sd.InputStream")
    def test_record_continuous_yields_remaining_buffer(self, mock_stream, audio_config, vad_config):
        """Test that remaining buffer is yielded when stopping."""
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model = MagicMock()

        def add_buffer_and_stop():
            time.sleep(0.1)
            # Add audio to buffer while recording
            test_audio = np.random.randn(audio_config.sample_rate).astype(np.float32)
            recorder.buffer.extend(test_audio)
            recorder.stop_continuous()

        stop_thread = threading.Thread(target=add_buffer_and_stop)
        stop_thread.start()

        segments = list(recorder.record_continuous())
        stop_thread.join()

        # Should have yielded the buffered audio as final segment
        assert len(segments) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
