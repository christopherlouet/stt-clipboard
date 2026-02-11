#!/usr/bin/env python3
"""Tests for rate limiter in hotkey module."""

import time

import pytest

from src.hotkey import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter class (T013)."""

    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within the limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=10.0)

        for _ in range(5):
            assert limiter.allow() is True

    def test_rate_limiter_rejects_over_limit(self):
        """Test that the 6th request within the window is rejected."""
        limiter = RateLimiter(max_requests=5, window_seconds=10.0)

        for _ in range(5):
            limiter.allow()

        assert limiter.allow() is False

    def test_rate_limiter_allows_after_window_expires(self):
        """Test that requests are allowed again after the window expires."""
        limiter = RateLimiter(max_requests=5, window_seconds=1.0)

        # Fill up the window
        for _ in range(5):
            limiter.allow()

        assert limiter.allow() is False

        # Wait for window to expire
        time.sleep(1.1)

        assert limiter.allow() is True

    def test_rate_limiter_sliding_window(self):
        """Test that the sliding window correctly evicts old timestamps."""
        limiter = RateLimiter(max_requests=3, window_seconds=1.0)

        # Send 3 requests
        for _ in range(3):
            limiter.allow()

        # 4th should be rejected
        assert limiter.allow() is False

        # Wait for window to slide
        time.sleep(1.1)

        # Now old timestamps are expired, new request should be allowed
        assert limiter.allow() is True

    def test_rate_limiter_thread_safety(self):
        """Test that RateLimiter is thread-safe."""
        import threading

        limiter = RateLimiter(max_requests=10, window_seconds=10.0)
        results = []
        barrier = threading.Barrier(20)

        def try_request():
            barrier.wait()
            results.append(limiter.allow())

        threads = [threading.Thread(target=try_request) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        allowed = sum(1 for r in results if r)
        rejected = sum(1 for r in results if not r)

        assert allowed == 10
        assert rejected == 10

    def test_rate_limiter_default_constants(self):
        """Test that default constants are 5 requests per 10 seconds."""
        limiter = RateLimiter()
        assert limiter.max_requests == 5
        assert limiter.window_seconds == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
