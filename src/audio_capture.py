"""Audio capture with Voice Activity Detection (VAD).

This module provides audio recording functionality with intelligent speech detection
using the Silero VAD (Voice Activity Detection) model. It captures audio from the
microphone and automatically stops recording when silence is detected.

Key features:
    - Real-time voice activity detection using Silero VAD
    - Pre-buffering to capture speech onset (avoids cutting off beginnings)
    - Configurable silence duration threshold
    - Callback support for speech start/end events
    - Automatic audio normalization to float32 [-1, 1]

Example:
    Basic recording with VAD::

        from src.audio_capture import AudioRecorder
        from src.config import AudioConfig, VADConfig

        audio_config = AudioConfig(silence_duration=1.2)
        vad_config = VADConfig(threshold=0.5)

        recorder = AudioRecorder(audio_config, vad_config)
        audio = recorder.record_until_silence()

        if audio is not None:
            print(f"Recorded {len(audio) / 16000:.2f} seconds of audio")

    With speech detection callbacks::

        def on_speech():
            print("Speech detected!")

        recorder = AudioRecorder(
            audio_config, vad_config,
            on_speech_start=on_speech
        )

Audio format:
    The recorder outputs audio as a numpy array with:
    - dtype: float32
    - sample_rate: 16000 Hz (configurable)
    - channels: mono (1 channel)
    - range: normalized to [-1.0, 1.0]
"""

import collections
import time
from collections.abc import Callable

import numpy as np
import sounddevice as sd
import torch
from loguru import logger

from src.cache import AudioChunkCache
from src.config import AudioConfig, VADConfig


class AudioRecorder:
    """Audio recorder with silence detection using Silero VAD."""

    def __init__(
        self,
        audio_config: AudioConfig,
        vad_config: VADConfig,
        on_speech_start: Callable | None = None,
        on_speech_end: Callable | None = None,
    ):
        """Initialize audio recorder.

        Args:
            audio_config: Audio configuration
            vad_config: VAD configuration
            on_speech_start: Callback when speech starts
            on_speech_end: Callback when speech ends
        """
        self.audio_config = audio_config
        self.vad_config = vad_config
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end

        # Audio buffer (ring buffer for pre-buffering)
        max_samples = audio_config.sample_rate * audio_config.max_recording_duration
        self.buffer = collections.deque(maxlen=max_samples)

        # Recording state
        self.is_recording = False
        self.speech_started = False
        self.last_speech_time = 0.0
        self.recording_start_time = 0.0

        # VAD model (loaded lazily)
        self.vad_model = None
        self._vad_sample_rate = 16000  # Silero VAD expects 16kHz

        # Pre-buffer for capturing speech start
        self.pre_buffer_duration = 0.5  # seconds
        self.pre_buffer_samples = int(self.pre_buffer_duration * audio_config.sample_rate)
        self.pre_buffer = collections.deque(maxlen=self.pre_buffer_samples)

        # Minimum speech duration (avoid false starts)
        self.min_speech_samples = int(audio_config.min_speech_duration * audio_config.sample_rate)

        # VAD cache (optional, for performance optimization)
        self.vad_cache: AudioChunkCache | None = None
        if vad_config.cache_enabled:
            self.vad_cache = AudioChunkCache(max_size=vad_config.cache_size)
            logger.info(f"VAD cache enabled: max_size={vad_config.cache_size}")

        logger.info(
            f"AudioRecorder initialized: {audio_config.sample_rate}Hz, "
            f"silence={audio_config.silence_duration}s, "
            f"max={audio_config.max_recording_duration}s"
        )

    def _load_vad_model(self):
        """Load Silero VAD model (lazy loading)."""
        if self.vad_model is not None:
            return

        try:
            logger.info("Loading Silero VAD model...")
            # Loading from official Silero VAD repository - safe and expected
            self.vad_model, _ = torch.hub.load(  # nosec B614
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                onnx=False,  # Use PyTorch version
            )
            self.vad_model.eval()
            logger.info("Silero VAD model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}")
            raise RuntimeError(f"VAD model loading failed: {e}")

    def _detect_speech(self, audio_chunk: np.ndarray) -> float:
        """Detect speech in audio chunk using VAD.

        Args:
            audio_chunk: Audio data (float32, normalized to [-1, 1])

        Returns:
            Speech probability (0.0 to 1.0)
        """
        if self.vad_model is None:
            self._load_vad_model()

        try:
            # Ensure audio is the right shape and type
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)

            # Normalize if needed
            if np.abs(audio_chunk).max() > 1.0:
                audio_chunk = audio_chunk / 32768.0

            # Use cache if enabled
            if self.vad_cache is not None:
                return self.vad_cache.get_or_compute(
                    audio_chunk, lambda: self._vad_inference(audio_chunk)
                )

            # Direct VAD inference (no cache)
            return self._vad_inference(audio_chunk)

        except Exception as e:
            logger.warning(f"VAD detection failed: {e}")
            return 0.0

    def _vad_inference(self, audio_chunk: np.ndarray) -> float:
        """Perform VAD inference on audio chunk.

        Args:
            audio_chunk: Audio data (float32, normalized to [-1, 1])

        Returns:
            Speech probability (0.0 to 1.0)
        """
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_chunk)

        # Ensure 1D
        if audio_tensor.dim() > 1:
            audio_tensor = audio_tensor.squeeze()

        # VAD inference
        with torch.no_grad():
            speech_prob = self.vad_model(audio_tensor, self._vad_sample_rate).item()

        return speech_prob

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback for sounddevice stream.

        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        # Convert to float32 if needed
        audio_chunk = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()

        if audio_chunk.dtype == np.int16:
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0

        # Detect speech
        speech_prob = self._detect_speech(audio_chunk)

        current_time = time.time()

        # Check if speech is detected
        is_speech = speech_prob > self.vad_config.threshold

        if is_speech:
            self.last_speech_time = current_time

            if not self.speech_started:
                # Speech just started
                self.speech_started = True

                # Add pre-buffer to main buffer
                if self.pre_buffer:
                    self.buffer.extend(self.pre_buffer)
                    self.pre_buffer.clear()

                if self.on_speech_start:
                    self.on_speech_start()

                logger.debug(f"Speech started (prob={speech_prob:.3f})")

            # Add to buffer
            self.buffer.extend(audio_chunk)

        else:
            # No speech detected
            if self.speech_started:
                # Add to buffer during silence (to capture end of speech)
                self.buffer.extend(audio_chunk)

                # Check if silence duration exceeded
                silence_duration = current_time - self.last_speech_time

                if silence_duration >= self.audio_config.silence_duration:
                    # Silence detected, stop recording
                    logger.debug(f"Silence detected after {silence_duration:.2f}s")
                    self.is_recording = False

            else:
                # Still waiting for speech, add to pre-buffer
                self.pre_buffer.extend(audio_chunk)

    def record_until_silence(self) -> np.ndarray | None:
        """Record audio until silence is detected.

        Returns:
            Audio data as numpy array (float32), or None if failed
        """
        # Reset state
        self.buffer.clear()
        self.pre_buffer.clear()
        self.is_recording = True
        self.speech_started = False
        self.last_speech_time = time.time()
        self.recording_start_time = time.time()

        # Ensure VAD model is loaded
        self._load_vad_model()

        logger.info("Starting audio recording...")

        try:
            # Open audio stream
            with sd.InputStream(
                samplerate=self.audio_config.sample_rate,
                channels=self.audio_config.channels,
                dtype=np.float32,
                blocksize=self.audio_config.blocksize,
                callback=self._audio_callback,
            ):
                # Wait until recording stops (silence detected or timeout)
                while self.is_recording:
                    time.sleep(0.1)

                    # Check for timeout
                    elapsed = time.time() - self.recording_start_time
                    if elapsed >= self.audio_config.max_recording_duration:
                        logger.warning(
                            f"Max recording duration ({self.audio_config.max_recording_duration}s) reached"
                        )
                        break

                    # Check minimum speech duration
                    if not self.speech_started and elapsed > 5.0:
                        logger.warning("No speech detected after 5s, stopping")
                        return None

        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return None

        # Check if we have enough audio
        if len(self.buffer) < self.min_speech_samples:
            logger.warning(
                f"Recording too short: {len(self.buffer)} samples (min {self.min_speech_samples})"
            )
            return None

        # Convert buffer to numpy array
        audio_data = np.array(list(self.buffer), dtype=np.float32)

        recording_duration = len(audio_data) / self.audio_config.sample_rate
        logger.info(f"Recording complete: {recording_duration:.2f}s ({len(audio_data)} samples)")

        return audio_data

    def get_available_devices(self) -> list:
        """Get list of available audio input devices.

        Returns:
            List of device dictionaries
        """
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get("max_input_channels", 0) > 0]

        return input_devices

    def set_default_device(self, device_id: int | None = None):
        """Set default audio input device.

        Args:
            device_id: Device ID, or None for system default
        """
        if device_id is not None:
            sd.default.device = (device_id, sd.default.device[1])
            logger.info(f"Set default input device to: {device_id}")
        else:
            sd.default.reset()
            logger.info("Reset to system default audio device")

    def get_cache_stats(self) -> dict | None:
        """Get VAD cache statistics.

        Returns:
            Dictionary with cache stats if cache is enabled, None otherwise.
        """
        if self.vad_cache is not None:
            return self.vad_cache.stats()
        return None


# Convenience functions
def list_audio_devices():
    """Print list of available audio devices."""
    print("Available Audio Input Devices:")
    print("=" * 60)

    devices = sd.query_devices()

    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            default_marker = " [DEFAULT]" if i == sd.default.device[0] else ""
            print(f"{i}: {device['name']}{default_marker}")
            print(f"   Channels: {device['max_input_channels']}")
            print(f"   Sample Rate: {device['default_samplerate']} Hz")
            print()


# Example usage and testing
if __name__ == "__main__":
    import sys

    # List available devices
    list_audio_devices()

    # Test recording
    print("\nTest Recording")
    print("=" * 60)
    print("Speak into your microphone...")
    print("Recording will stop after 1.2s of silence")
    print()

    # Create test config
    audio_cfg = AudioConfig(
        sample_rate=16000,
        channels=1,
        silence_duration=1.2,
        min_speech_duration=0.3,
        max_recording_duration=30,
    )

    vad_cfg = VADConfig(
        threshold=0.5,
        min_silence_duration_ms=300,
        speech_pad_ms=300,
    )

    # Callbacks
    def on_start():
        print("🎤 Speech detected!")

    def on_end():
        print("🔇 Silence detected, stopping...")

    # Create recorder
    recorder = AudioRecorder(
        audio_config=audio_cfg,
        vad_config=vad_cfg,
        on_speech_start=on_start,
        on_speech_end=on_end,
    )

    # Record
    audio = recorder.record_until_silence()

    if audio is not None:
        print("\n✓ Recording successful!")
        print(f"  Duration: {len(audio) / audio_cfg.sample_rate:.2f}s")
        print(f"  Samples: {len(audio)}")
        print(f"  Shape: {audio.shape}")
        print(f"  Dtype: {audio.dtype}")
        print(f"  Range: [{audio.min():.3f}, {audio.max():.3f}]")

        # Optionally save to file
        save = input("\nSave to file? (y/n): ").strip().lower()
        if save == "y":
            import scipy.io.wavfile as wavfile

            wavfile.write("test_recording.wav", audio_cfg.sample_rate, audio)
            print("Saved to test_recording.wav")
    else:
        print("\n✗ Recording failed")
        sys.exit(1)
