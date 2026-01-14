#!/usr/bin/env python3
"""Benchmark script for STT Clipboard performance testing."""

import argparse
import statistics
import time

import numpy as np
from loguru import logger

from src.config import Config
from src.transcription import WhisperTranscriber


def generate_test_audio(duration: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
    """Generate synthetic test audio (sine wave).

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Audio array
    """
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, dtype=np.float32)

    # Generate sine wave at 440 Hz (A4 note)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    # Add some harmonics for more realistic sound
    audio += 0.5 * np.sin(2 * np.pi * 880 * t)
    audio += 0.25 * np.sin(2 * np.pi * 1320 * t)

    # Normalize
    audio = audio / np.abs(audio).max()

    return audio


def benchmark_transcription(
    transcriber: WhisperTranscriber,
    audio: np.ndarray,
    iterations: int = 10,
) -> dict:
    """Benchmark transcription performance.

    Args:
        transcriber: Transcriber instance
        audio: Audio data
        iterations: Number of iterations

    Returns:
        Benchmark results
    """
    logger.info(f"Running {iterations} transcription iterations...")

    times = []
    audio_duration = len(audio) / 16000

    for i in range(iterations):
        logger.info(f"Iteration {i + 1}/{iterations}...")

        start = time.time()
        _ = transcriber.transcribe(audio)
        elapsed = time.time() - start

        times.append(elapsed)

        rtf = elapsed / audio_duration
        logger.info(f"  Time: {elapsed:.3f}s, RTF: {rtf:.3f}x")

    results = {
        "iterations": iterations,
        "audio_duration": audio_duration,
        "times": times,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "mean_rtf": statistics.mean(times) / audio_duration,
        "median_rtf": statistics.median(times) / audio_duration,
    }

    return results


def print_results(results: dict):
    """Print benchmark results.

    Args:
        results: Benchmark results dictionary
    """
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"\nAudio Duration: {results['audio_duration']:.2f}s")
    print(f"Iterations: {results['iterations']}")
    print("\nTranscription Time:")
    print(f"  Mean:   {results['mean']:.3f}s  (RTF: {results['mean_rtf']:.3f}x)")
    print(f"  Median: {results['median']:.3f}s  (RTF: {results['median_rtf']:.3f}x)")
    print(f"  StdDev: {results['stdev']:.3f}s")
    print(f"  Min:    {results['min']:.3f}s")
    print(f"  Max:    {results['max']:.3f}s")

    # Performance assessment
    print("\nPerformance Assessment:")
    if results["mean_rtf"] < 0.3:
        print("  ✓ EXCELLENT - Extremely fast transcription")
    elif results["mean_rtf"] < 0.5:
        print("  ✓ GOOD - Fast transcription, suitable for interactive use")
    elif results["mean_rtf"] < 1.0:
        print("  ⚠ ACCEPTABLE - Moderate speed, may feel slightly slow")
    else:
        print("  ✗ SLOW - Transcription slower than real-time")

    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark STT Clipboard performance")

    parser.add_argument("--iterations", "-n", type=int, default=10, help="Number of iterations")

    parser.add_argument(
        "--duration", "-d", type=float, default=5.0, help="Test audio duration (seconds)"
    )

    parser.add_argument("--model", "-m", type=str, default="tiny", help="Whisper model size")

    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")

    args = parser.parse_args()

    # Remove logger output for cleaner benchmark display
    logger.remove()
    logger.add(lambda msg: None)  # Silent logger

    print("=" * 60)
    print("STT Clipboard Benchmark")
    print("=" * 60)
    print(f"\nModel: {args.model}")
    print(f"Iterations: {args.iterations}")
    print(f"Test audio duration: {args.duration}s")
    print()

    # Load config
    config = Config.from_yaml(args.config)
    config.transcription.model_size = args.model

    # Create transcriber
    print("Loading model...")
    transcriber = WhisperTranscriber(config.transcription)
    transcriber.load_model()
    print(f"✓ Model loaded in {transcriber.load_time:.2f}s")

    # Generate test audio
    print(f"\nGenerating test audio ({args.duration}s)...")
    audio = generate_test_audio(duration=args.duration)
    print("✓ Test audio generated")

    # Run benchmark
    print()
    results = benchmark_transcription(transcriber, audio, args.iterations)

    # Print results
    print_results(results)


if __name__ == "__main__":
    main()
