"""Tests for clipboard retry with exponential backoff."""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.clipboard import ClipboardManager


class TestCopyWithBackoff:
    """Tests for copy_with_backoff method."""

    @patch("src.clipboard.create_clipboard_manager")
    def test_returns_true_on_first_success(self, mock_create: MagicMock):
        """Test returns True when first attempt succeeds."""
        mock_manager = MagicMock()
        mock_manager.copy.return_value = True
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        result = manager.copy_with_backoff("test text")

        assert result is True
        assert mock_manager.copy.call_count == 1

    @patch("src.clipboard.create_clipboard_manager")
    def test_retries_on_failure(self, mock_create: MagicMock):
        """Test retries when first attempt fails."""
        mock_manager = MagicMock()
        # Fail twice, succeed on third
        mock_manager.copy.side_effect = [False, False, True]
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        result = manager.copy_with_backoff("test text", max_retries=3)

        assert result is True
        assert mock_manager.copy.call_count == 3

    @patch("src.clipboard.create_clipboard_manager")
    def test_returns_false_after_max_retries(self, mock_create: MagicMock):
        """Test returns False when all retries exhausted."""
        mock_manager = MagicMock()
        mock_manager.copy.return_value = False
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        result = manager.copy_with_backoff("test text", max_retries=3)

        assert result is False
        # 1 initial + 3 retries = 4 total
        assert mock_manager.copy.call_count == 4

    @patch("src.clipboard.create_clipboard_manager")
    @patch("time.sleep")
    def test_uses_exponential_backoff_delays(self, mock_sleep: MagicMock, mock_create: MagicMock):
        """Test uses exponential backoff between retries."""
        mock_manager = MagicMock()
        mock_manager.copy.side_effect = [False, False, False, True]
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        manager.copy_with_backoff("test text", max_retries=3, backoff_base=0.1)

        # Check sleep was called with exponential delays
        # Attempt 1 fails -> sleep(0.1 * 2^0 = 0.1)
        # Attempt 2 fails -> sleep(0.1 * 2^1 = 0.2)
        # Attempt 3 fails -> sleep(0.1 * 2^2 = 0.4)
        # Attempt 4 succeeds
        assert mock_sleep.call_count == 3
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls[0] == pytest.approx(0.1, rel=0.01)
        assert calls[1] == pytest.approx(0.2, rel=0.01)
        assert calls[2] == pytest.approx(0.4, rel=0.01)

    @patch("src.clipboard.create_clipboard_manager")
    @patch("time.sleep")
    def test_respects_max_delay(self, mock_sleep: MagicMock, mock_create: MagicMock):
        """Test backoff delay is capped at max_delay."""
        mock_manager = MagicMock()
        mock_manager.copy.side_effect = [False, False, False, False, False, True]
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        manager.copy_with_backoff("test text", max_retries=5, backoff_base=0.5, max_delay=1.0)

        # Check delays are capped at max_delay
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        # Delays: 0.5, 1.0, 1.0, 1.0, 1.0 (capped at 1.0)
        assert all(delay <= 1.0 for delay in calls)

    @patch("src.clipboard.create_clipboard_manager")
    @patch("time.sleep")
    def test_no_sleep_on_first_attempt(self, mock_sleep: MagicMock, mock_create: MagicMock):
        """Test no sleep delay before first attempt."""
        mock_manager = MagicMock()
        mock_manager.copy.return_value = True
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        manager.copy_with_backoff("test text")

        mock_sleep.assert_not_called()

    @patch("src.clipboard.create_clipboard_manager")
    def test_default_parameters(self, mock_create: MagicMock):
        """Test default parameters are reasonable."""
        mock_manager = MagicMock()
        mock_manager.copy.return_value = False
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        start = time.time()
        manager.copy_with_backoff("test text")
        elapsed = time.time() - start

        # With default max_retries=3, should try 4 times
        assert mock_manager.copy.call_count == 4
        # Total time should be reasonable (not too long)
        assert elapsed < 5.0

    @patch("src.clipboard.create_clipboard_manager")
    def test_handles_exception_as_failure(self, mock_create: MagicMock):
        """Test exceptions are treated as failures and retried."""
        mock_manager = MagicMock()
        mock_manager.copy.side_effect = [Exception("Test error"), True]
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        result = manager.copy_with_backoff("test text", max_retries=2)

        assert result is True
        assert mock_manager.copy.call_count == 2

    @patch("src.clipboard.create_clipboard_manager")
    @patch("time.sleep")
    def test_zero_retries_means_single_attempt(self, mock_sleep: MagicMock, mock_create: MagicMock):
        """Test max_retries=0 means only one attempt."""
        mock_manager = MagicMock()
        mock_manager.copy.return_value = False
        mock_create.return_value = mock_manager

        manager = ClipboardManager()
        result = manager.copy_with_backoff("test text", max_retries=0)

        assert result is False
        assert mock_manager.copy.call_count == 1
        mock_sleep.assert_not_called()


class TestCopyToClipboardWithBackoff:
    """Tests for copy_to_clipboard_with_backoff convenience function."""

    @patch("src.clipboard.get_clipboard_manager")
    def test_calls_copy_with_backoff(self, mock_get_manager: MagicMock):
        """Test convenience function uses copy_with_backoff."""
        from src.clipboard import copy_to_clipboard_with_backoff

        mock_manager = MagicMock()
        mock_manager.copy_with_backoff.return_value = True
        mock_get_manager.return_value = mock_manager

        result = copy_to_clipboard_with_backoff(
            "test", max_retries=5, backoff_base=0.2, max_delay=2.0
        )

        assert result is True
        mock_manager.copy_with_backoff.assert_called_once_with(
            "test", max_retries=5, backoff_base=0.2, max_delay=2.0
        )

    @patch("src.clipboard.get_clipboard_manager")
    def test_uses_default_parameters(self, mock_get_manager: MagicMock):
        """Test convenience function uses default parameters."""
        from src.clipboard import copy_to_clipboard_with_backoff

        mock_manager = MagicMock()
        mock_manager.copy_with_backoff.return_value = True
        mock_get_manager.return_value = mock_manager

        copy_to_clipboard_with_backoff("test")

        mock_manager.copy_with_backoff.assert_called_once_with(
            "test", max_retries=3, backoff_base=0.1, max_delay=2.0
        )
