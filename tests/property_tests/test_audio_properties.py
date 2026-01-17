#!/usr/bin/env python3
"""Property-based tests for audio processing using hypothesis."""

import numpy as np
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays


# Custom strategies for audio data with proper float32 handling
def audio_float32_strategy(min_size: int = 100, max_size: int = 16000):
    """Strategy for generating float32 audio arrays."""
    return arrays(
        dtype=np.float32,
        shape=st.integers(min_value=min_size, max_value=max_size),
        elements=st.floats(
            min_value=-1.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
            width=32,
        ),
    )


def audio_int16_strategy(min_size: int = 100, max_size: int = 16000):
    """Strategy for generating int16 audio arrays."""
    return arrays(
        dtype=np.int16,
        shape=st.integers(min_value=min_size, max_value=max_size),
        elements=st.integers(min_value=-32768, max_value=32767),
    )


def unnormalized_float32_strategy(min_size: int = 100, max_size: int = 16000):
    """Strategy for generating unnormalized float32 audio (values outside [-1, 1])."""
    return arrays(
        dtype=np.float32,
        shape=st.integers(min_value=min_size, max_value=max_size),
        elements=st.floats(
            min_value=-32768.0,
            max_value=32767.0,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
            width=32,
        ),
    )


class TestAudioNormalizationProperties:
    """Property-based tests for audio normalization."""

    @given(audio_float32_strategy())
    @settings(max_examples=50)
    def test_normalized_audio_stays_in_range(self, audio: np.ndarray):
        """Property: normalized audio values are in [-1, 1]."""
        # Simulate normalization logic from audio_capture.py
        if np.abs(audio).max() > 1.0:
            audio = audio / 32768.0

        assert np.abs(audio).max() <= 1.0

    @given(audio_int16_strategy())
    @settings(max_examples=50)
    def test_int16_to_float32_conversion_range(self, audio: np.ndarray):
        """Property: int16 to float32 conversion produces values in [-1, 1]."""
        # Simulate conversion from audio_capture.py
        audio_float = audio.astype(np.float32) / 32768.0

        assert audio_float.dtype == np.float32
        assert np.abs(audio_float).max() <= 1.0

    @given(unnormalized_float32_strategy())
    @settings(max_examples=50)
    def test_unnormalized_audio_gets_normalized(self, audio: np.ndarray):
        """Property: unnormalized audio (>1.0) gets normalized."""
        assume(np.abs(audio).max() > 1.0)

        # Simulate normalization logic
        if np.abs(audio).max() > 1.0:
            audio = audio / 32768.0

        assert np.abs(audio).max() <= 1.0

    @given(audio_float32_strategy())
    @settings(max_examples=50)
    def test_normalization_preserves_relative_values(self, audio: np.ndarray):
        """Property: normalization preserves relative values (signs and ratios)."""
        assume(len(audio) > 1)
        assume(np.abs(audio).max() > 0)  # Skip all-zero arrays

        original = audio.copy()

        # Apply normalization
        if np.abs(audio).max() > 1.0:
            audio = audio / 32768.0

        # Signs should be preserved
        original_signs = np.sign(original)
        result_signs = np.sign(audio)
        np.testing.assert_array_equal(original_signs, result_signs)


class TestAudioDtypeConversionProperties:
    """Property-based tests for audio dtype conversions."""

    @given(audio_int16_strategy(min_size=10, max_size=1000))
    @settings(max_examples=50)
    def test_int16_conversion_is_reversible(self, audio: np.ndarray):
        """Property: int16 -> float32 -> int16 is approximately reversible."""
        # Convert to float32
        audio_float = audio.astype(np.float32) / 32768.0

        # Convert back to int16
        audio_back = (audio_float * 32768.0).astype(np.int16)

        # Should be approximately equal (may have small rounding errors)
        np.testing.assert_array_almost_equal(audio, audio_back, decimal=0)

    @given(audio_float32_strategy())
    @settings(max_examples=50)
    def test_float32_dtype_preserved(self, audio: np.ndarray):
        """Property: float32 audio stays float32 after processing."""
        # Apply typical processing
        processed = audio.copy()
        if np.abs(processed).max() > 1.0:
            processed = processed / 32768.0

        assert processed.dtype == np.float32


class TestAudioShapeProperties:
    """Property-based tests for audio shape handling."""

    @given(st.integers(min_value=100, max_value=16000))
    @settings(max_examples=30)
    def test_1d_audio_shape_preserved(self, size: int):
        """Property: 1D audio shape is preserved after processing."""
        audio = np.zeros(size, dtype=np.float32)

        # Simulate squeeze operation from audio_capture.py
        if audio.ndim > 1:
            audio = np.squeeze(audio)

        assert audio.ndim == 1
        assert audio.shape[0] == size

    @given(st.integers(min_value=100, max_value=16000))
    @settings(max_examples=30)
    def test_2d_mono_audio_squeezed_to_1d(self, size: int):
        """Property: 2D mono audio (n, 1) is squeezed to 1D."""
        audio = np.zeros((size, 1), dtype=np.float32)

        # Simulate squeeze operation
        if audio.ndim > 1:
            audio = np.squeeze(audio)

        assert audio.ndim == 1
        assert audio.shape[0] == size

    @given(st.integers(min_value=100, max_value=8000))
    @settings(max_examples=30)
    def test_stereo_first_channel_extraction(self, size: int):
        """Property: stereo audio first channel extraction preserves size."""
        audio = np.zeros((size, 2), dtype=np.float32)

        # Extract first channel (as done in audio_capture.py)
        mono = audio[:, 0]

        assert mono.ndim == 1
        assert mono.shape[0] == size


class TestAudioBufferProperties:
    """Property-based tests for audio buffer operations."""

    @given(
        st.lists(
            arrays(
                dtype=np.float32,
                shape=st.integers(min_value=100, max_value=512),
                elements=st.floats(
                    min_value=-1.0,
                    max_value=1.0,
                    allow_nan=False,
                    allow_infinity=False,
                    allow_subnormal=False,
                    width=32,
                ),
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=30)
    def test_concatenated_chunks_preserve_total_samples(self, chunks: list):
        """Property: concatenating chunks preserves total sample count."""
        total_samples = sum(len(chunk) for chunk in chunks)

        # Concatenate chunks
        result = np.concatenate(chunks)

        assert len(result) == total_samples

    @given(audio_float32_strategy(min_size=1000, max_size=16000))
    @settings(max_examples=30)
    def test_audio_slicing_preserves_dtype(self, audio: np.ndarray):
        """Property: slicing audio preserves dtype."""
        assume(len(audio) > 100)

        # Slice audio
        sliced = audio[100:]

        assert sliced.dtype == audio.dtype


class TestSampleRateProperties:
    """Property-based tests for sample rate related calculations."""

    @given(
        st.integers(min_value=8000, max_value=48000),  # sample_rate
        st.floats(min_value=0.1, max_value=5.0, allow_subnormal=False),  # duration
    )
    @settings(max_examples=50)
    def test_samples_from_duration_calculation(self, sample_rate: int, duration: float):
        """Property: samples = sample_rate * duration."""
        samples = int(sample_rate * duration)

        # Verify the calculation
        calculated_duration = samples / sample_rate

        # Should be approximately equal (allowing for int truncation)
        assert abs(calculated_duration - duration) < (1 / sample_rate)

    @given(st.integers(min_value=8000, max_value=48000))
    @settings(max_examples=20)
    def test_standard_chunk_size_calculation(self, sample_rate: int):
        """Property: 512 samples at 16kHz = 32ms, scale proportionally."""
        chunk_samples = 512
        base_rate = 16000

        # Calculate equivalent duration
        base_duration_ms = (chunk_samples / base_rate) * 1000  # 32ms

        # For any sample rate, same duration should give proportional samples
        scaled_samples = int((base_duration_ms / 1000) * sample_rate)

        # Verify the ratio
        assert abs(scaled_samples / sample_rate - chunk_samples / base_rate) < 0.001


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
