#!/usr/bin/env python3
"""Tests for notifications module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.notifications import notify_recording_started, notify_text_copied, send_notification


class TestSendNotification:
    """Tests for send_notification function."""

    @patch("src.notifications.subprocess.run")
    def test_sends_notification_with_correct_arguments(self, mock_run: MagicMock):
        """Test that notify-send is called with correct arguments."""
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification("Test Title", "Test Message", urgency="normal")

        assert result is True
        mock_run.assert_called_once_with(
            ["notify-send", "--urgency=normal", "Test Title", "Test Message"],
            check=True,
            capture_output=True,
            timeout=2.0,
        )

    @patch("src.notifications.subprocess.run")
    def test_sends_notification_with_low_urgency(self, mock_run: MagicMock):
        """Test notification with low urgency."""
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification("Title", "Message", urgency="low")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "--urgency=low" in call_args

    @patch("src.notifications.subprocess.run")
    def test_sends_notification_with_critical_urgency(self, mock_run: MagicMock):
        """Test notification with critical urgency."""
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification("Title", "Message", urgency="critical")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "--urgency=critical" in call_args

    @patch("src.notifications.subprocess.run")
    def test_returns_false_when_notify_send_not_found(self, mock_run: MagicMock):
        """Test that False is returned when notify-send is not available."""
        mock_run.side_effect = FileNotFoundError("notify-send not found")

        result = send_notification("Title", "Message")

        assert result is False

    @patch("src.notifications.subprocess.run")
    def test_returns_false_on_timeout(self, mock_run: MagicMock):
        """Test that False is returned on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="notify-send", timeout=2.0)

        result = send_notification("Title", "Message")

        assert result is False

    @patch("src.notifications.subprocess.run")
    def test_returns_false_on_subprocess_error(self, mock_run: MagicMock):
        """Test that False is returned on subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="notify-send")

        result = send_notification("Title", "Message")

        assert result is False

    @patch("src.notifications.subprocess.run")
    def test_returns_false_on_generic_exception(self, mock_run: MagicMock):
        """Test that False is returned on generic exception."""
        mock_run.side_effect = RuntimeError("Unknown error")

        result = send_notification("Title", "Message")

        assert result is False

    @patch("src.notifications.subprocess.run")
    def test_handles_special_characters_in_message(self, mock_run: MagicMock):
        """Test that special characters are handled correctly."""
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification("Title", "Message with 'quotes' and \"double quotes\"")

        assert result is True

    @patch("src.notifications.subprocess.run")
    def test_handles_newlines_in_message(self, mock_run: MagicMock):
        """Test that newlines are handled correctly."""
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification("Title", "Line 1\nLine 2\nLine 3")

        assert result is True

    @patch("src.notifications.subprocess.run")
    def test_handles_unicode_characters(self, mock_run: MagicMock):
        """Test that unicode characters are handled correctly."""
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification("Titre", "Message avec des accents: é è à ç")

        assert result is True


class TestNotifyRecordingStarted:
    """Tests for notify_recording_started function."""

    @patch("src.notifications.send_notification")
    def test_calls_send_notification_with_correct_title(self, mock_send: MagicMock):
        """Test that the correct title is used."""
        mock_send.return_value = True

        notify_recording_started()

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "STT Clipboard"

    @patch("src.notifications.send_notification")
    def test_calls_send_notification_with_french_message(self, mock_send: MagicMock):
        """Test that the French recording message is used."""
        mock_send.return_value = True

        notify_recording_started()

        call_args = mock_send.call_args
        assert "Enregistrement en cours" in call_args[0][1]
        assert "Parlez maintenant" in call_args[0][1]

    @patch("src.notifications.send_notification")
    def test_uses_normal_urgency(self, mock_send: MagicMock):
        """Test that normal urgency is used."""
        mock_send.return_value = True

        notify_recording_started()

        call_args = mock_send.call_args
        assert call_args[1]["urgency"] == "normal"

    @patch("src.notifications.send_notification")
    def test_returns_true_on_success(self, mock_send: MagicMock):
        """Test that True is returned on success."""
        mock_send.return_value = True

        result = notify_recording_started()

        assert result is True

    @patch("src.notifications.send_notification")
    def test_returns_false_on_failure(self, mock_send: MagicMock):
        """Test that False is returned on failure."""
        mock_send.return_value = False

        result = notify_recording_started()

        assert result is False


class TestNotifyTextCopied:
    """Tests for notify_text_copied function."""

    @patch("src.notifications.send_notification")
    def test_calls_send_notification_with_correct_title(self, mock_send: MagicMock):
        """Test that the correct title is used."""
        mock_send.return_value = True

        notify_text_copied("Test text")

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "STT Clipboard"

    @patch("src.notifications.send_notification")
    def test_includes_text_in_message(self, mock_send: MagicMock):
        """Test that the copied text is included in the message."""
        mock_send.return_value = True

        notify_text_copied("Hello world")

        call_args = mock_send.call_args
        assert "Hello world" in call_args[0][1]

    @patch("src.notifications.send_notification")
    def test_includes_french_label(self, mock_send: MagicMock):
        """Test that the French label is included."""
        mock_send.return_value = True

        notify_text_copied("Test")

        call_args = mock_send.call_args
        assert "Texte copié dans le presse-papiers" in call_args[0][1]

    @patch("src.notifications.send_notification")
    def test_truncates_long_text(self, mock_send: MagicMock):
        """Test that text longer than 100 characters is truncated."""
        mock_send.return_value = True
        long_text = "a" * 150

        notify_text_copied(long_text)

        call_args = mock_send.call_args
        message = call_args[0][1]
        # Should contain truncated text with ellipsis
        assert "..." in message
        # Should not contain the full 150 characters
        assert "a" * 150 not in message

    @patch("src.notifications.send_notification")
    def test_does_not_truncate_short_text(self, mock_send: MagicMock):
        """Test that text of exactly 100 characters is not truncated."""
        mock_send.return_value = True
        exact_text = "a" * 100

        notify_text_copied(exact_text)

        call_args = mock_send.call_args
        message = call_args[0][1]
        # Should contain full text without ellipsis
        assert "a" * 100 in message
        assert "..." not in message

    @patch("src.notifications.send_notification")
    def test_truncates_at_101_characters(self, mock_send: MagicMock):
        """Test that text of 101 characters is truncated."""
        mock_send.return_value = True
        text_101 = "a" * 101

        notify_text_copied(text_101)

        call_args = mock_send.call_args
        message = call_args[0][1]
        # Should be truncated
        assert "..." in message

    @patch("src.notifications.send_notification")
    def test_uses_normal_urgency(self, mock_send: MagicMock):
        """Test that normal urgency is used."""
        mock_send.return_value = True

        notify_text_copied("Test")

        call_args = mock_send.call_args
        assert call_args[1]["urgency"] == "normal"

    @patch("src.notifications.send_notification")
    def test_returns_true_on_success(self, mock_send: MagicMock):
        """Test that True is returned on success."""
        mock_send.return_value = True

        result = notify_text_copied("Test")

        assert result is True

    @patch("src.notifications.send_notification")
    def test_returns_false_on_failure(self, mock_send: MagicMock):
        """Test that False is returned on failure."""
        mock_send.return_value = False

        result = notify_text_copied("Test")

        assert result is False

    @patch("src.notifications.send_notification")
    def test_handles_empty_text(self, mock_send: MagicMock):
        """Test handling of empty text."""
        mock_send.return_value = True

        result = notify_text_copied("")

        assert result is True
        mock_send.assert_called_once()

    @patch("src.notifications.send_notification")
    def test_handles_unicode_text(self, mock_send: MagicMock):
        """Test handling of unicode text."""
        mock_send.return_value = True

        result = notify_text_copied("Texte avec des accents: é è à ç ù")

        assert result is True


class TestNotifyNoSpeechDetected:
    """Tests for notify_no_speech_detected function."""

    @patch("src.notifications.send_notification")
    def test_calls_send_notification_with_correct_title(self, mock_send: MagicMock):
        """Test that the correct title is used."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = True

        notify_no_speech_detected()

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "STT Clipboard"

    @patch("src.notifications.send_notification")
    def test_includes_no_speech_message(self, mock_send: MagicMock):
        """Test that the no-speech message is included."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = True

        notify_no_speech_detected()

        call_args = mock_send.call_args
        message = call_args[0][1]
        # Should indicate no speech was detected
        assert "parole" in message.lower() or "speech" in message.lower()

    @patch("src.notifications.send_notification")
    def test_uses_low_urgency(self, mock_send: MagicMock):
        """Test that low urgency is used (not critical)."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = True

        notify_no_speech_detected()

        call_args = mock_send.call_args
        assert call_args[1]["urgency"] == "low"

    @patch("src.notifications.send_notification")
    def test_returns_true_on_success(self, mock_send: MagicMock):
        """Test that True is returned on success."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = True

        result = notify_no_speech_detected()

        assert result is True

    @patch("src.notifications.send_notification")
    def test_returns_false_on_failure(self, mock_send: MagicMock):
        """Test that False is returned on failure."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = False

        result = notify_no_speech_detected()

        assert result is False

    @patch("src.notifications.send_notification")
    def test_custom_duration_in_message(self, mock_send: MagicMock):
        """Test that custom timeout duration is included in message."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = True

        notify_no_speech_detected(timeout_seconds=30)

        call_args = mock_send.call_args
        message = call_args[0][1]
        assert "30" in message

    @patch("src.notifications.send_notification")
    def test_default_duration_in_message(self, mock_send: MagicMock):
        """Test that default timeout duration is used if not specified."""
        from src.notifications import notify_no_speech_detected

        mock_send.return_value = True

        notify_no_speech_detected()

        # Should have some duration value in the message
        mock_send.assert_called_once()
        message = mock_send.call_args[0][1]
        assert "30" in message  # Default timeout is 30s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
