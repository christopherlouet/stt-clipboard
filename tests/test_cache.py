"""Tests for AudioChunkCache."""

from unittest.mock import MagicMock

import numpy as np

from src.cache import AudioChunkCache


class TestAudioChunkCacheInit:
    """Tests for AudioChunkCache initialization."""

    def test_initializes_with_default_size(self):
        """Test cache initializes with default max_size."""
        cache = AudioChunkCache()
        assert cache.max_size == 100

    def test_initializes_with_custom_size(self):
        """Test cache initializes with custom max_size."""
        cache = AudioChunkCache(max_size=50)
        assert cache.max_size == 50

    def test_initializes_empty(self):
        """Test cache starts empty."""
        cache = AudioChunkCache()
        assert cache.size == 0
        assert cache.hits == 0
        assert cache.misses == 0


class TestAudioChunkCacheGetOrCompute:
    """Tests for get_or_compute method."""

    def test_computes_on_cache_miss(self):
        """Test compute function is called on cache miss."""
        cache = AudioChunkCache(max_size=10)
        chunk = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        compute_fn = MagicMock(return_value=0.75)

        result = cache.get_or_compute(chunk, compute_fn)

        assert result == 0.75
        compute_fn.assert_called_once()
        assert cache.misses == 1

    def test_returns_cached_on_hit(self):
        """Test cached value is returned on cache hit."""
        cache = AudioChunkCache(max_size=10)
        chunk = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        compute_fn = MagicMock(return_value=0.75)

        # First call - miss
        result1 = cache.get_or_compute(chunk, compute_fn)
        # Second call - hit
        result2 = cache.get_or_compute(chunk, compute_fn)

        assert result1 == result2 == 0.75
        compute_fn.assert_called_once()  # Only called once
        assert cache.hits == 1
        assert cache.misses == 1

    def test_different_chunks_different_results(self):
        """Test different chunks produce different cache entries."""
        cache = AudioChunkCache(max_size=10)
        chunk1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk2 = np.array([0.4, 0.5, 0.6], dtype=np.float32)

        compute_fn = MagicMock(side_effect=[0.5, 0.8])

        result1 = cache.get_or_compute(chunk1, compute_fn)
        result2 = cache.get_or_compute(chunk2, compute_fn)

        assert result1 == 0.5
        assert result2 == 0.8
        assert cache.misses == 2
        assert compute_fn.call_count == 2


class TestAudioChunkCacheLRUEviction:
    """Tests for LRU eviction behavior."""

    def test_evicts_oldest_when_full(self):
        """Test oldest entry is evicted when cache is full."""
        cache = AudioChunkCache(max_size=3)

        # Fill cache with 3 entries
        for i in range(3):
            chunk = np.array([i * 0.1], dtype=np.float32)
            cache.get_or_compute(chunk, lambda i=i: i)  # Capture i by default arg

        assert cache.size == 3

        # Add 4th entry - should evict first
        chunk4 = np.array([0.9], dtype=np.float32)
        cache.get_or_compute(chunk4, lambda: 99)

        assert cache.size == 3

        # First entry should be evicted (cache miss if we request it again)
        old_misses = cache.misses
        chunk1 = np.array([0.0], dtype=np.float32)
        cache.get_or_compute(chunk1, lambda: 100)

        assert cache.misses == old_misses + 1

    def test_recently_used_not_evicted(self):
        """Test recently used entries are not evicted."""
        cache = AudioChunkCache(max_size=3)

        # Fill cache
        chunks = [np.array([i * 0.1], dtype=np.float32) for i in range(3)]
        for i, chunk in enumerate(chunks):
            cache.get_or_compute(chunk, lambda i=i: i)

        # Access first entry to make it recently used
        cache.get_or_compute(chunks[0], lambda: 0)

        # Add new entry - should evict second (not first, as it was recently used)
        new_chunk = np.array([0.9], dtype=np.float32)
        cache.get_or_compute(new_chunk, lambda: 99)

        # First entry should still be cached (hit)
        old_hits = cache.hits
        cache.get_or_compute(chunks[0], lambda: 0)
        assert cache.hits == old_hits + 1

        # Second entry should be evicted (miss)
        old_misses = cache.misses
        cache.get_or_compute(chunks[1], lambda: 1)
        assert cache.misses == old_misses + 1


class TestAudioChunkCacheStats:
    """Tests for cache statistics."""

    def test_hit_rate_calculation(self):
        """Test hit rate is calculated correctly."""
        cache = AudioChunkCache(max_size=10)
        chunk = np.array([0.1, 0.2], dtype=np.float32)

        # 1 miss
        cache.get_or_compute(chunk, lambda: 0.5)
        # 3 hits
        for _ in range(3):
            cache.get_or_compute(chunk, lambda: 0.5)

        # 3 hits / 4 total = 75%
        assert cache.hit_rate == 0.75

    def test_hit_rate_zero_when_empty(self):
        """Test hit rate is 0 when no requests made."""
        cache = AudioChunkCache(max_size=10)
        assert cache.hit_rate == 0.0

    def test_stats_method(self):
        """Test stats method returns correct statistics."""
        cache = AudioChunkCache(max_size=10)
        chunk = np.array([0.1], dtype=np.float32)

        cache.get_or_compute(chunk, lambda: 0.5)
        cache.get_or_compute(chunk, lambda: 0.5)

        stats = cache.stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestAudioChunkCacheClear:
    """Tests for cache clearing."""

    def test_clear_removes_all_entries(self):
        """Test clear removes all entries."""
        cache = AudioChunkCache(max_size=10)

        # Add entries
        for i in range(5):
            chunk = np.array([i * 0.1], dtype=np.float32)
            cache.get_or_compute(chunk, lambda i=i: i)  # Capture i by default arg

        assert cache.size == 5

        cache.clear()

        assert cache.size == 0

    def test_clear_resets_stats(self):
        """Test clear resets hit/miss stats."""
        cache = AudioChunkCache(max_size=10)
        chunk = np.array([0.1], dtype=np.float32)

        cache.get_or_compute(chunk, lambda: 0.5)
        cache.get_or_compute(chunk, lambda: 0.5)

        cache.clear()

        assert cache.hits == 0
        assert cache.misses == 0


class TestAudioChunkCacheHashConsistency:
    """Tests for consistent hashing of audio chunks."""

    def test_same_array_same_hash(self):
        """Test identical arrays produce same hash."""
        cache = AudioChunkCache(max_size=10)

        chunk1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk2 = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        compute_fn = MagicMock(return_value=0.5)

        cache.get_or_compute(chunk1, compute_fn)
        cache.get_or_compute(chunk2, compute_fn)

        # Second call should be a hit
        assert cache.hits == 1
        compute_fn.assert_called_once()

    def test_different_dtype_different_hash(self):
        """Test arrays with different dtypes are treated separately."""
        cache = AudioChunkCache(max_size=10)

        chunk_float32 = np.array([0.1, 0.2], dtype=np.float32)
        chunk_float64 = np.array([0.1, 0.2], dtype=np.float64)

        compute_fn = MagicMock(side_effect=[0.5, 0.6])

        cache.get_or_compute(chunk_float32, compute_fn)
        cache.get_or_compute(chunk_float64, compute_fn)

        # Both should be misses
        assert cache.misses == 2

    def test_small_difference_different_hash(self):
        """Test small differences in arrays produce different hashes."""
        cache = AudioChunkCache(max_size=10)

        chunk1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk2 = np.array([0.1, 0.2, 0.30001], dtype=np.float32)

        compute_fn = MagicMock(side_effect=[0.5, 0.6])

        cache.get_or_compute(chunk1, compute_fn)
        cache.get_or_compute(chunk2, compute_fn)

        # Both should be misses (different chunks)
        assert cache.misses == 2


class TestAudioChunkCacheEdgeCases:
    """Tests for edge cases."""

    def test_handles_empty_array(self):
        """Test cache handles empty arrays."""
        cache = AudioChunkCache(max_size=10)
        empty_chunk = np.array([], dtype=np.float32)

        result = cache.get_or_compute(empty_chunk, lambda: 0.0)

        assert result == 0.0
        assert cache.size == 1

    def test_handles_large_array(self):
        """Test cache handles large arrays."""
        cache = AudioChunkCache(max_size=10)
        large_chunk = np.random.randn(16000).astype(np.float32)  # 1 second at 16kHz

        result = cache.get_or_compute(large_chunk, lambda: 0.8)

        assert result == 0.8
        assert cache.size == 1

    def test_max_size_one(self):
        """Test cache works with max_size=1."""
        cache = AudioChunkCache(max_size=1)

        chunk1 = np.array([0.1], dtype=np.float32)
        chunk2 = np.array([0.2], dtype=np.float32)

        cache.get_or_compute(chunk1, lambda: 1)
        cache.get_or_compute(chunk2, lambda: 2)

        assert cache.size == 1

        # chunk1 should be evicted
        compute_fn = MagicMock(return_value=1)
        cache.get_or_compute(chunk1, compute_fn)
        compute_fn.assert_called_once()  # Miss - had to recompute
