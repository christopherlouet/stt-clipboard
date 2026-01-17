"""Speech-to-text transcription using faster-whisper.

This module provides the core transcription functionality using the faster-whisper
library, which is a CTranslate2-based implementation of OpenAI's Whisper model.
It offers significant speed improvements over the original Whisper implementation.

Key features:
    - Automatic language detection (French/English)
    - INT8 quantization for fast CPU inference
    - Lazy model loading to minimize startup time
    - Real-time factor (RTF) logging for performance monitoring

Example:
    Basic usage with default configuration::

        from src.transcription import WhisperTranscriber
        from src.config import TranscriptionConfig

        config = TranscriptionConfig(model_size="base", language="")
        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        # Transcribe audio (16kHz float32 numpy array)
        text = transcriber.transcribe(audio_data)

    Using the convenience function::

        from src.transcription import transcribe_audio

        text = transcribe_audio(audio_data)

Performance tips:
    - Use "int8" compute_type for fastest CPU inference
    - Use "tiny" or "base" models for real-time applications
    - Pre-load the model at service startup to avoid cold-start latency
"""

import time
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from loguru import logger

from src.config import TranscriptionConfig


class WhisperTranscriber:
    """Transcriber using faster-whisper with CTranslate2 backend."""

    def __init__(self, config: TranscriptionConfig):
        """Initialize transcriber.

        Args:
            config: Transcription configuration
        """
        self.config = config
        self.model: WhisperModel | None = None
        self.load_time: float = 0.0
        self.detected_language: str | None = None  # Store last detected language

        # Ensure download directory exists
        Path(config.download_root).mkdir(parents=True, exist_ok=True)

        logger.info(
            f"WhisperTranscriber initialized: model={config.model_size}, "
            f"lang={config.language or 'auto-detect'}, device={config.device}, "
            f"compute_type={config.compute_type}"
        )

    def load_model(self) -> None:
        """Load the Whisper model into memory.

        This is typically called once at service startup to avoid
        cold-start latency.
        """
        if self.model is not None:
            logger.debug("Model already loaded, skipping")
            return

        start_time = time.time()
        logger.info(f"Loading Whisper model: {self.config.model_size}...")

        try:
            self.model = WhisperModel(
                model_size_or_path=self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
                download_root=self.config.download_root,
                cpu_threads=0,  # Auto-detect
                num_workers=1,
            )

            self.load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {self.load_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data (float32, normalized to [-1, 1])

        Returns:
            Transcribed text
        """
        if self.model is None:
            logger.info("Model not loaded, loading now...")
            self.load_model()

        start_time = time.time()
        audio_duration = len(audio) / 16000  # Assuming 16kHz

        try:
            # Ensure audio is the right format
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()

            logger.debug(
                f"Starting transcription: {audio_duration:.2f}s audio, {len(audio)} samples"
            )

            # Convert empty string to None for auto-detection
            # faster-whisper requires None (not "") for language auto-detection
            language = self.config.language if self.config.language else None

            # Transcribe
            segments, info = self.model.transcribe(
                audio,
                language=language,
                beam_size=self.config.beam_size,
                best_of=self.config.best_of,
                temperature=self.config.temperature,
                vad_filter=False,  # We use external VAD
                word_timestamps=False,  # Faster without timestamps
                condition_on_previous_text=False,  # No context needed
            )

            # Collect all segments
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text.strip())

            # Join segments
            text = " ".join(text_segments).strip()

            # Store detected language for punctuation processing
            self.detected_language = info.language

            transcription_time = time.time() - start_time

            logger.info(
                f"Transcription complete: {transcription_time:.2f}s "
                f"(audio: {audio_duration:.2f}s, "
                f"RTF: {transcription_time / audio_duration:.2f}x, "
                f"chars: {len(text)}, "
                f"detected_lang: {info.language})"
            )

            # Log detected language if different from configured
            if self.config.language and info.language != self.config.language:
                logger.warning(
                    f"Detected language: {info.language} (expected: {self.config.language})"
                )

            return text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    def transcribe_with_timestamps(self, audio: np.ndarray) -> list[tuple[str, float, float]]:
        """Transcribe audio with word timestamps.

        Args:
            audio: Audio data

        Returns:
            List of (text, start_time, end_time) tuples
        """
        if self.model is None:
            self.load_model()

        try:
            # Ensure audio is the right format
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()

            # Convert empty string to None for auto-detection
            language = self.config.language if self.config.language else None

            # Transcribe with timestamps
            segments, info = self.model.transcribe(
                audio,
                language=language,
                beam_size=self.config.beam_size,
                word_timestamps=True,
            )

            # Collect segments with timestamps
            results = []
            for segment in segments:
                results.append((segment.text.strip(), segment.start, segment.end))

            return results

        except Exception as e:
            logger.error(f"Transcription with timestamps failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_size": self.config.model_size,
            "language": self.config.language,
            "device": self.config.device,
            "compute_type": self.config.compute_type,
            "beam_size": self.config.beam_size,
            "loaded": self.model is not None,
            "load_time": self.load_time,
        }

    def unload_model(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            self.model = None
            logger.info("Model unloaded from memory")


# Convenience functions
_default_transcriber: WhisperTranscriber | None = None


def get_transcriber(config: TranscriptionConfig | None = None) -> WhisperTranscriber:
    """Get or create default transcriber singleton.

    Args:
        config: Transcription config, or None for defaults

    Returns:
        WhisperTranscriber instance
    """
    global _default_transcriber

    if _default_transcriber is None:
        if config is None:
            config = TranscriptionConfig()
        _default_transcriber = WhisperTranscriber(config)

    return _default_transcriber


def transcribe_audio(audio: np.ndarray, config: TranscriptionConfig | None = None) -> str:
    """Transcribe audio (convenience function).

    Args:
        audio: Audio data
        config: Optional config

    Returns:
        Transcribed text
    """
    transcriber = get_transcriber(config)
    return transcriber.transcribe(audio)


# Example usage and testing
if __name__ == "__main__":
    import sys

    print("Whisper Transcription Test")
    print("=" * 60)

    # Create test config
    config = TranscriptionConfig(
        model_size="tiny",
        language="fr",
        device="cpu",
        compute_type="int8",
        beam_size=1,
    )

    # Create transcriber
    transcriber = WhisperTranscriber(config)

    # Load model
    print("\nLoading model...")
    transcriber.load_model()

    # Show model info
    info = transcriber.get_model_info()
    print("\nModel Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test with sample audio
    print("\nTesting with sample audio...")

    # Try to load test audio if available
    try:
        import scipy.io.wavfile as wavfile

        test_file = "test_recording.wav"
        if Path(test_file).exists():
            print(f"Loading {test_file}...")
            sample_rate, audio_data = wavfile.read(test_file)

            # Convert to float32
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0

            # Resample if needed (simple, not perfect)
            if sample_rate != 16000:
                print(f"Warning: Sample rate is {sample_rate}Hz, expected 16000Hz")

            # Transcribe
            print("\nTranscribing...")
            text = transcriber.transcribe(audio_data)

            print("\nResult:")
            print(f"  Text: {text}")
            print(f"  Length: {len(text)} characters")

        else:
            print(f"Test file not found: {test_file}")
            print("Run audio_capture.py first to create a test recording")

    except ImportError:
        print("scipy not available for loading test audio")
        print("Install scipy to test with audio files")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\nTest complete!")
