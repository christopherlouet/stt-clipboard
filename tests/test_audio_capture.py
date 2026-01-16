#!/usr/bin/env python3
"""Tests for audio capture module."""

import collections
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.audio_capture import AudioRecorder
from src.config import AudioConfig, VADConfig


class TestAudioRecorderInit:
    """Tests for AudioRecorder initialization."""

    def test_initializes_with_default_configs(self):
        """Test initialization with default configs."""
        audio_config = AudioConfig()
        vad_config = VADConfig()

        recorder = AudioRecorder(audio_config, vad_config)

        assert recorder.audio_config == audio_config
        assert recorder.vad_config == vad_config
        assert recorder.is_recording is False
        assert recorder.speech_started is False
        assert recorder.vad_model is None

    def test_initializes_with_custom_configs(self):
        """Test initialization with custom configs."""
        audio_config = AudioConfig(
            sample_rate=44100,
            channels=2,
            silence_duration=2.0,
            max_recording_duration=60,
        )
        vad_config = VADConfig(threshold=0.7)

        recorder = AudioRecorder(audio_config, vad_config)

        assert recorder.audio_config.sample_rate == 44100
        assert recorder.audio_config.channels == 2
        assert recorder.audio_config.silence_duration == 2.0
        assert recorder.vad_config.threshold == 0.7

    def test_initializes_buffer_with_correct_max_size(self):
        """Test buffer is initialized with correct max size."""
        audio_config = AudioConfig(sample_rate=16000, max_recording_duration=30)
        vad_config = VADConfig()

        recorder = AudioRecorder(audio_config, vad_config)

        expected_max = 16000 * 30  # sample_rate * max_duration
        assert recorder.buffer.maxlen == expected_max

    def test_initializes_pre_buffer_with_correct_size(self):
        """Test pre-buffer is initialized with correct size."""
        audio_config = AudioConfig(sample_rate=16000)
        vad_config = VADConfig()

        recorder = AudioRecorder(audio_config, vad_config)

        expected_pre_buffer = int(0.5 * 16000)  # 0.5s * sample_rate
        assert recorder.pre_buffer.maxlen == expected_pre_buffer

    def test_initializes_with_callbacks(self):
        """Test initialization with callbacks."""
        audio_config = AudioConfig()
        vad_config = VADConfig()
        on_start = MagicMock()
        on_end = MagicMock()

        recorder = AudioRecorder(
            audio_config, vad_config, on_speech_start=on_start, on_speech_end=on_end
        )

        assert recorder.on_speech_start == on_start
        assert recorder.on_speech_end == on_end

    def test_calculates_min_speech_samples(self):
        """Test min speech samples calculation."""
        audio_config = AudioConfig(sample_rate=16000, min_speech_duration=0.3)
        vad_config = VADConfig()

        recorder = AudioRecorder(audio_config, vad_config)

        expected = int(0.3 * 16000)  # 4800 samples
        assert recorder.min_speech_samples == expected


class TestAudioRecorderLoadVadModel:
    """Tests for VAD model loading."""

    @patch("src.audio_capture.torch.hub.load")
    def test_loads_vad_model(self, mock_torch_load: MagicMock):
        """Test VAD model is loaded correctly."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        recorder._load_vad_model()

        assert recorder.vad_model == mock_model
        mock_model.eval.assert_called_once()
        mock_torch_load.assert_called_once_with(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )

    @patch("src.audio_capture.torch.hub.load")
    def test_does_not_reload_if_already_loaded(self, mock_torch_load: MagicMock):
        """Test model is not reloaded if already loaded."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        recorder._load_vad_model()
        recorder._load_vad_model()  # Second call

        assert mock_torch_load.call_count == 1

    @patch("src.audio_capture.torch.hub.load")
    def test_raises_error_on_load_failure(self, mock_torch_load: MagicMock):
        """Test RuntimeError is raised on load failure."""
        mock_torch_load.side_effect = RuntimeError("Failed to load")

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        with pytest.raises(RuntimeError, match="VAD model loading failed"):
            recorder._load_vad_model()


class TestAudioRecorderDetectSpeech:
    """Tests for speech detection."""

    @patch("src.audio_capture.torch.hub.load")
    def test_detects_speech(self, mock_torch_load: MagicMock):
        """Test speech detection returns probability."""
        mock_model = MagicMock()
        mock_model.return_value.item.return_value = 0.95
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        audio_chunk = np.zeros(512, dtype=np.float32)
        prob = recorder._detect_speech(audio_chunk)

        assert prob == 0.95

    @patch("src.audio_capture.torch.hub.load")
    def test_converts_int16_to_float32(self, mock_torch_load: MagicMock):
        """Test int16 audio is converted to float32."""
        mock_model = MagicMock()
        mock_model.return_value.item.return_value = 0.5
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        audio_chunk = np.zeros(512, dtype=np.int16)
        recorder._detect_speech(audio_chunk)

        # Model should be called with float32 tensor
        mock_model.assert_called()

    @patch("src.audio_capture.torch.hub.load")
    def test_normalizes_audio_if_needed(self, mock_torch_load: MagicMock):
        """Test audio is normalized if values exceed 1.0."""
        mock_model = MagicMock()
        mock_model.return_value.item.return_value = 0.5
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        # Audio with values > 1.0 (unnormalized int16 range)
        audio_chunk = np.array([32767, -32768, 16000], dtype=np.float32)
        recorder._detect_speech(audio_chunk)

        mock_model.assert_called()

    @patch("src.audio_capture.torch.hub.load")
    def test_returns_zero_on_detection_error(self, mock_torch_load: MagicMock):
        """Test returns 0.0 on detection error."""
        mock_model = MagicMock()
        mock_model.side_effect = RuntimeError("Detection failed")
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        audio_chunk = np.zeros(512, dtype=np.float32)
        prob = recorder._detect_speech(audio_chunk)

        assert prob == 0.0


class TestAudioRecorderAudioCallback:
    """Tests for audio callback handling."""

    @patch("src.audio_capture.torch.hub.load")
    def test_handles_speech_start(self, mock_torch_load: MagicMock):
        """Test speech start callback is invoked."""
        mock_model = MagicMock()
        mock_model.return_value.item.return_value = 0.9
        mock_torch_load.return_value = (mock_model, None)

        on_speech_start = MagicMock()

        audio_config = AudioConfig()
        vad_config = VADConfig(threshold=0.5)
        recorder = AudioRecorder(audio_config, vad_config, on_speech_start=on_speech_start)
        recorder._load_vad_model()

        # Simulate audio callback with speech
        indata = np.zeros((512, 1), dtype=np.float32)
        recorder._audio_callback(indata, 512, None, None)

        on_speech_start.assert_called_once()
        assert recorder.speech_started is True

    @patch("src.audio_capture.torch.hub.load")
    def test_adds_audio_to_buffer_during_speech(self, mock_torch_load: MagicMock):
        """Test audio is added to buffer during speech."""
        mock_model = MagicMock()
        mock_model.return_value.item.return_value = 0.9
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig(threshold=0.5)
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model()

        # Simulate audio callback with speech
        indata = np.ones((512, 1), dtype=np.float32) * 0.5
        recorder._audio_callback(indata, 512, None, None)

        assert len(recorder.buffer) == 512

    @patch("src.audio_capture.torch.hub.load")
    def test_adds_audio_to_pre_buffer_without_speech(self, mock_torch_load: MagicMock):
        """Test audio is added to pre-buffer when no speech."""
        mock_model = MagicMock()
        mock_model.return_value.item.return_value = 0.1  # Below threshold
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig()
        vad_config = VADConfig(threshold=0.5)
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model()

        # Simulate audio callback without speech
        indata = np.zeros((512, 1), dtype=np.float32)
        recorder._audio_callback(indata, 512, None, None)

        assert len(recorder.pre_buffer) == 512
        assert len(recorder.buffer) == 0

    @patch("src.audio_capture.torch.hub.load")
    @patch("src.audio_capture.time.time")
    def test_stops_recording_on_silence(self, mock_time: MagicMock, mock_torch_load: MagicMock):
        """Test recording stops after silence duration."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig(silence_duration=1.0)
        vad_config = VADConfig(threshold=0.5)
        recorder = AudioRecorder(audio_config, vad_config)
        recorder._load_vad_model()
        recorder.is_recording = True
        recorder.speech_started = True

        # First call: speech detected
        mock_model.return_value.item.return_value = 0.9
        mock_time.return_value = 0.0
        recorder.last_speech_time = 0.0

        indata = np.zeros((512, 1), dtype=np.float32)
        recorder._audio_callback(indata, 512, None, None)

        # Second call: silence after 1.5s
        mock_model.return_value.item.return_value = 0.1  # No speech
        mock_time.return_value = 1.5  # 1.5s later
        recorder._audio_callback(indata, 512, None, None)

        assert recorder.is_recording is False

    def test_handles_stream_status_warning(self):
        """Test stream status warnings are logged."""
        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        # Mock the detect_speech to avoid VAD loading
        recorder._detect_speech = MagicMock(return_value=0.0)

        # Simulate callback with status
        indata = np.zeros((512, 1), dtype=np.float32)
        status = "Input overflow"

        # Should not raise, just log
        recorder._audio_callback(indata, 512, None, status)


class TestAudioRecorderRecordUntilSilence:
    """Tests for record_until_silence method."""

    @patch("src.audio_capture.sd.InputStream")
    @patch("src.audio_capture.torch.hub.load")
    @patch("src.audio_capture.time.sleep")
    @patch("src.audio_capture.time.time")
    def test_returns_audio_on_successful_recording(
        self,
        mock_time: MagicMock,
        mock_sleep: MagicMock,
        mock_torch_load: MagicMock,
        mock_stream: MagicMock,
    ):
        """Test successful recording returns audio data."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig(sample_rate=16000, min_speech_duration=0.1)
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        # Mock context manager
        mock_context = MagicMock()
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_context)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        # Time progression to simulate recording
        time_calls = [0.0, 0.0, 0.1, 0.2]
        mock_time.side_effect = time_calls

        # Populate buffer and stop recording on first sleep
        min_samples = int(0.1 * 16000)  # 1600 samples

        def stop_recording(_):
            # Add samples to buffer AFTER record_until_silence clears it
            recorder.buffer.extend(np.zeros(min_samples + 100, dtype=np.float32))
            recorder.is_recording = False

        mock_sleep.side_effect = stop_recording

        result = recorder.record_until_silence()

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    @patch("src.audio_capture.sd.InputStream")
    @patch("src.audio_capture.torch.hub.load")
    def test_returns_none_on_stream_error(self, mock_torch_load: MagicMock, mock_stream: MagicMock):
        """Test returns None when stream raises error."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        mock_stream.side_effect = RuntimeError("Audio device error")

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        result = recorder.record_until_silence()

        assert result is None

    @patch("src.audio_capture.sd.InputStream")
    @patch("src.audio_capture.torch.hub.load")
    @patch("src.audio_capture.time.sleep")
    @patch("src.audio_capture.time.time")
    def test_returns_none_if_recording_too_short(
        self,
        mock_time: MagicMock,
        mock_sleep: MagicMock,
        mock_torch_load: MagicMock,
        mock_stream: MagicMock,
    ):
        """Test returns None if recording is too short."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig(sample_rate=16000, min_speech_duration=0.3)
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        # Buffer with insufficient samples
        recorder.buffer = collections.deque(np.zeros(100, dtype=np.float32), maxlen=16000 * 30)

        mock_context = MagicMock()
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_context)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        time_calls = [0.0, 0.0, 0.1]
        mock_time.side_effect = time_calls

        def stop_recording(_):
            recorder.is_recording = False

        mock_sleep.side_effect = stop_recording

        result = recorder.record_until_silence()

        assert result is None

    @patch("src.audio_capture.sd.InputStream")
    @patch("src.audio_capture.torch.hub.load")
    @patch("src.audio_capture.time.sleep")
    @patch("src.audio_capture.time.time")
    def test_respects_max_recording_duration(
        self,
        mock_time: MagicMock,
        mock_sleep: MagicMock,
        mock_torch_load: MagicMock,
        mock_stream: MagicMock,
    ):
        """Test recording stops at max duration."""
        mock_model = MagicMock()
        mock_torch_load.return_value = (mock_model, None)

        audio_config = AudioConfig(
            sample_rate=16000, max_recording_duration=5, min_speech_duration=0.1
        )
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        mock_context = MagicMock()
        mock_stream.return_value.__enter__ = MagicMock(return_value=mock_context)
        mock_stream.return_value.__exit__ = MagicMock(return_value=False)

        # Simulate time progressing past max duration
        call_count = [0]

        def time_effect():
            call_count[0] += 1
            if call_count[0] <= 2:
                return 0.0
            return 6.0  # Past max duration

        mock_time.side_effect = time_effect

        def sleep_effect(_):
            # Add samples to buffer to simulate recording
            recorder.buffer.extend(np.zeros(3200, dtype=np.float32))

        mock_sleep.side_effect = sleep_effect

        result = recorder.record_until_silence()

        assert result is not None  # Should have returned audio


class TestAudioRecorderDevices:
    """Tests for device management."""

    @patch("src.audio_capture.sd.query_devices")
    def test_get_available_devices(self, mock_query: MagicMock):
        """Test getting available audio devices."""
        mock_query.return_value = [
            {"name": "Microphone", "max_input_channels": 2},
            {"name": "Speaker", "max_input_channels": 0},
            {"name": "Webcam Mic", "max_input_channels": 1},
        ]

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        devices = recorder.get_available_devices()

        assert len(devices) == 2
        assert devices[0]["name"] == "Microphone"
        assert devices[1]["name"] == "Webcam Mic"

    @patch("src.audio_capture.sd.default")
    def test_set_default_device(self, mock_default: MagicMock):
        """Test setting default audio device."""
        mock_default.device = (0, 0)

        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        recorder.set_default_device(2)

        assert mock_default.device == (2, 0)

    @patch("src.audio_capture.sd.default")
    def test_reset_default_device(self, mock_default: MagicMock):
        """Test resetting to system default device."""
        audio_config = AudioConfig()
        vad_config = VADConfig()
        recorder = AudioRecorder(audio_config, vad_config)

        recorder.set_default_device(None)

        mock_default.reset.assert_called_once()


class TestListAudioDevices:
    """Tests for list_audio_devices function."""

    @patch("src.audio_capture.sd.query_devices")
    @patch("src.audio_capture.sd.default")
    def test_lists_input_devices(self, mock_default: MagicMock, mock_query: MagicMock, capsys):
        """Test listing audio input devices."""
        mock_default.device = (0, 0)
        mock_query.return_value = [
            {
                "name": "Default Mic",
                "max_input_channels": 2,
                "default_samplerate": 44100,
            },
            {"name": "Speaker", "max_input_channels": 0, "default_samplerate": 48000},
        ]

        from src.audio_capture import list_audio_devices

        list_audio_devices()

        captured = capsys.readouterr()
        assert "Default Mic" in captured.out
        assert "[DEFAULT]" in captured.out
        assert "Speaker" not in captured.out  # Not an input device


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
