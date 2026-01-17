"""Model warmup utilities for STT Clipboard.

This module provides functionality to pre-warm the transcription model
by running a dummy transcription at service startup. This ensures the
first real transcription request doesn't suffer from cold-start latency.

Example:
    Warmup a transcriber::

        from src.warmup import warmup_transcriber

        transcriber = WhisperTranscriber(config)
        transcriber.load_model()

        result = warmup_transcriber(transcriber)
        if result.success:
            print(f"Warmup completed in {result.duration_seconds:.2f}s")

Why warmup is needed:
    - JIT compilation of PyTorch operations happens on first inference
    - Memory allocation patterns are established
    - CPU caches are populated
    - First real transcription becomes faster and more predictable
"""

import time
from dataclasses import dataclass

import numpy as np
from loguru import logger

from src.transcription import WhisperTranscriber


@dataclass
class WarmupResult:
    """Result of a model warmup operation.

    Attributes:
        success: Whether warmup completed successfully.
        duration_seconds: Time taken for warmup in seconds.
        audio_duration_seconds: Duration of the warmup audio in seconds.
        error_message: Error message if warmup failed, None otherwise.
    """

    success: bool
    duration_seconds: float
    audio_duration_seconds: float
    error_message: str | None = None


def warmup_transcriber(
    transcriber: WhisperTranscriber,
    audio_duration: float = 1.0,
    sample_rate: int = 16000,
) -> WarmupResult:
    """Perform model warmup by transcribing silent audio.

    This function generates near-silent audio and runs it through the
    transcription pipeline. This warms up:
    - PyTorch JIT compilation
    - CTranslate2 inference engine
    - Memory allocation patterns

    Args:
        transcriber: The WhisperTranscriber instance to warm up.
            The model should already be loaded.
        audio_duration: Duration of warmup audio in seconds. Default 1.0s.
        sample_rate: Sample rate of the generated audio. Default 16000 Hz.

    Returns:
        WarmupResult with success status and timing information.

    Example:
        ::

            transcriber = WhisperTranscriber(config)
            transcriber.load_model()

            result = warmup_transcriber(transcriber)
            print(f"Warmup took {result.duration_seconds:.2f}s")
    """
    logger.info("Starting model warmup...")

    # Generate near-silent audio (very small random noise)
    # This simulates real audio without producing any meaningful transcription
    num_samples = int(audio_duration * sample_rate)
    warmup_audio = np.random.randn(num_samples).astype(np.float32) * 0.001

    start_time = time.time()
    error_message = None
    success = True

    try:
        # Run transcription to warm up the model
        _ = transcriber.transcribe(warmup_audio)

    except Exception as e:
        logger.error(f"Warmup failed: {e}")
        success = False
        error_message = str(e)

    duration = time.time() - start_time

    if success:
        logger.info(f"Model warmup completed in {duration:.2f}s")
    else:
        logger.warning(f"Model warmup failed after {duration:.2f}s: {error_message}")

    return WarmupResult(
        success=success,
        duration_seconds=duration,
        audio_duration_seconds=audio_duration,
        error_message=error_message,
    )
