"""Cache utilities for STT Clipboard.

This module provides caching functionality to improve performance of
repeated computations, particularly for VAD (Voice Activity Detection)
inference on similar audio chunks.

Example:
    Using the cache with VAD detection::

        from src.cache import AudioChunkCache
        import numpy as np

        cache = AudioChunkCache(max_size=100)

        def compute_vad(chunk):
            # Expensive VAD inference
            return model(chunk)

        # First call - computes and caches
        result = cache.get_or_compute(audio_chunk, compute_vad)

        # Second call with same chunk - returns cached value
        result = cache.get_or_compute(audio_chunk, compute_vad)

        print(f"Cache hit rate: {cache.hit_rate:.1%}")
"""

import hashlib
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import numpy as np
from loguru import logger


class AudioChunkCache:
    """LRU cache for audio chunk computations.

    This cache stores results of expensive computations (like VAD inference)
    keyed by the hash of the input audio chunk. It uses an LRU (Least Recently
    Used) eviction policy when the cache is full.

    Attributes:
        max_size: Maximum number of entries in the cache.
        hits: Number of cache hits.
        misses: Number of cache misses.

    Example:
        ::

            cache = AudioChunkCache(max_size=50)

            # Cache VAD results
            speech_prob = cache.get_or_compute(
                audio_chunk,
                lambda: vad_model(audio_chunk)
            )

            # Check statistics
            print(f"Hit rate: {cache.hit_rate:.1%}")
    """

    def __init__(self, max_size: int = 100):
        """Initialize the audio chunk cache.

        Args:
            max_size: Maximum number of entries to store in the cache.
                When this limit is reached, the least recently used entry
                is evicted. Default is 100.
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0

        logger.debug(f"AudioChunkCache initialized: max_size={max_size}")

    @property
    def size(self) -> int:
        """Get current number of entries in cache.

        Returns:
            Number of cached entries.
        """
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as a float between 0.0 and 1.0.
            Returns 0.0 if no requests have been made.
        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def _compute_hash(self, chunk: np.ndarray) -> str:
        """Compute a hash for an audio chunk.

        The hash is computed from the raw bytes of the numpy array,
        including its dtype for uniqueness.

        Args:
            chunk: Audio data as numpy array.

        Returns:
            Hexadecimal hash string.
        """
        # Include dtype in hash for uniqueness
        dtype_bytes = str(chunk.dtype).encode()
        chunk_bytes = chunk.tobytes()
        combined = dtype_bytes + chunk_bytes
        return hashlib.md5(combined, usedforsecurity=False).hexdigest()

    def get_or_compute(self, chunk: np.ndarray, compute_fn: Callable[[], Any]) -> Any:
        """Get cached value or compute and cache it.

        This is the main method for using the cache. If the chunk is
        already cached, the cached value is returned. Otherwise, the
        compute function is called, its result is cached, and returned.

        Args:
            chunk: Audio chunk to use as cache key.
            compute_fn: Function to call if value is not cached.
                Should take no arguments and return the value to cache.

        Returns:
            Cached or computed value.

        Example:
            ::

                result = cache.get_or_compute(
                    audio_chunk,
                    lambda: expensive_computation(audio_chunk)
                )
        """
        key = self._compute_hash(chunk)

        # Check for cache hit
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self.hits += 1
            logger.trace(f"Cache hit: {key[:8]}...")
            return self._cache[key]

        # Cache miss - compute value
        self.misses += 1
        value = compute_fn()

        # Evict oldest if cache is full
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.trace(f"Cache evicted: {oldest_key[:8]}...")

        # Store in cache
        self._cache[key] = value
        logger.trace(f"Cache stored: {key[:8]}...")

        return value

    def clear(self) -> None:
        """Clear all cached entries and reset statistics.

        This removes all entries from the cache and resets the
        hit/miss counters to zero.
        """
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.debug("Cache cleared")

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing:
                - size: Current number of entries
                - max_size: Maximum cache size
                - hits: Number of cache hits
                - misses: Number of cache misses
                - hit_rate: Hit rate as float (0.0 to 1.0)

        Example:
            ::

                stats = cache.stats()
                print(f"Size: {stats['size']}/{stats['max_size']}")
                print(f"Hit rate: {stats['hit_rate']:.1%}")
        """
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
        }
