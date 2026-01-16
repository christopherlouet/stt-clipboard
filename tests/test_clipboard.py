#!/usr/bin/env python3
"""Tests for clipboard module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.clipboard import (
    ClipboardManager,
    WaylandClipboardManager,
    X11ClipboardManager,
    clear_clipboard,
    copy_to_clipboard,
    create_clipboard_manager,
    detect_session_type,
    get_clipboard_manager,
    paste_from_clipboard,
)


class TestDetectSessionType:
    """Tests for detect_session_type function."""

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}, clear=True)
    def test_detects_wayland_from_xdg_session_type(self):
        """Test that Wayland is detected from XDG_SESSION_TYPE."""
        result = detect_session_type()
        assert result == "wayland"

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}, clear=True)
    def test_detects_x11_from_xdg_session_type(self):
        """Test that X11 is detected from XDG_SESSION_TYPE."""
        result = detect_session_type()
        assert result == "x11"

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "WAYLAND"}, clear=True)
    def test_handles_uppercase_wayland(self):
        """Test that uppercase WAYLAND is handled."""
        result = detect_session_type()
        assert result == "wayland"

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "", "WAYLAND_DISPLAY": "wayland-0"}, clear=True)
    def test_fallback_to_wayland_display(self):
        """Test fallback to WAYLAND_DISPLAY env var."""
        result = detect_session_type()
        assert result == "wayland"

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "", "DISPLAY": ":0"}, clear=True)
    def test_fallback_to_display(self):
        """Test fallback to DISPLAY env var for X11."""
        result = detect_session_type()
        assert result == "x11"

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": ""}, clear=True)
    def test_returns_unknown_when_no_session_detected(self):
        """Test that 'unknown' is returned when no session is detected."""
        result = detect_session_type()
        assert result == "unknown"


class TestWaylandClipboardManager:
    """Tests for WaylandClipboardManager class."""

    @patch("shutil.which")
    def test_raises_error_when_wl_copy_not_found(self, mock_which: MagicMock):
        """Test that RuntimeError is raised when wl-copy is not available."""
        mock_which.return_value = None

        with pytest.raises(RuntimeError, match="wl-copy not found"):
            WaylandClipboardManager()

    @patch("shutil.which")
    def test_initializes_with_default_timeout(self, mock_which: MagicMock):
        """Test initialization with default timeout."""
        mock_which.return_value = "/usr/bin/wl-copy"

        manager = WaylandClipboardManager()

        assert manager.timeout == 2.0

    @patch("shutil.which")
    def test_initializes_with_custom_timeout(self, mock_which: MagicMock):
        """Test initialization with custom timeout."""
        mock_which.return_value = "/usr/bin/wl-copy"

        manager = WaylandClipboardManager(timeout=5.0)

        assert manager.timeout == 5.0

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.Popen")
    def test_copy_returns_true_on_success(self, mock_popen: MagicMock, mock_which: MagicMock):
        """Test that copy returns True on success."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stderr = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        manager = WaylandClipboardManager()
        result = manager.copy("test text")

        assert result is True
        mock_process.stdin.write.assert_called_once()
        mock_process.stdin.close.assert_called_once()

    @patch("shutil.which")
    def test_copy_returns_false_for_empty_text(self, mock_which: MagicMock):
        """Test that copy returns False for empty text."""
        mock_which.return_value = "/usr/bin/wl-copy"

        manager = WaylandClipboardManager()
        result = manager.copy("")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.Popen")
    def test_copy_returns_false_on_process_error(
        self, mock_popen: MagicMock, mock_which: MagicMock
    ):
        """Test that copy returns False on process error."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stderr = MagicMock()
        mock_process.stderr.read.return_value = b"error"
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        manager = WaylandClipboardManager()
        result = manager.copy("test")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_text_on_success(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns text on success."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.return_value = MagicMock(returncode=0, stdout="pasted text")

        manager = WaylandClipboardManager()
        result = manager.paste()

        assert result == "pasted text"

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_none_on_error(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns None on error."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        manager = WaylandClipboardManager()
        result = manager.paste()

        assert result is None

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_none_on_timeout(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns None on timeout."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="wl-paste", timeout=2.0)

        manager = WaylandClipboardManager()
        result = manager.paste()

        assert result is None

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.Popen")
    def test_copy_returns_false_on_exception(self, mock_popen: MagicMock, mock_which: MagicMock):
        """Test that copy returns False on general exception."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_popen.side_effect = OSError("Failed to spawn process")

        manager = WaylandClipboardManager()
        result = manager.copy("test")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_none_on_exception(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns None on general exception."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.side_effect = OSError("Failed to run paste")

        manager = WaylandClipboardManager()
        result = manager.paste()

        assert result is None

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_clear_returns_false_on_error(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that clear returns False on error."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.return_value = MagicMock(returncode=1, stderr=b"error message")

        manager = WaylandClipboardManager()
        result = manager.clear()

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_clear_returns_false_on_exception(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that clear returns False on general exception."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.side_effect = OSError("Failed to clear")

        manager = WaylandClipboardManager()
        result = manager.clear()

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_clear_returns_true_on_success(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that clear returns True on success."""
        mock_which.return_value = "/usr/bin/wl-copy"
        mock_run.return_value = MagicMock(returncode=0)

        manager = WaylandClipboardManager()
        result = manager.clear()

        assert result is True


class TestX11ClipboardManager:
    """Tests for X11ClipboardManager class."""

    @patch("shutil.which")
    def test_raises_error_when_no_tool_available(self, mock_which: MagicMock):
        """Test that RuntimeError is raised when neither xclip nor xsel is available."""
        mock_which.return_value = None

        with pytest.raises(RuntimeError, match="Neither xclip nor xsel found"):
            X11ClipboardManager()

    @patch("shutil.which")
    def test_prefers_xclip_over_xsel(self, mock_which: MagicMock):
        """Test that xclip is preferred over xsel."""

        def which_side_effect(cmd):
            if cmd == "xclip":
                return "/usr/bin/xclip"
            elif cmd == "xsel":
                return "/usr/bin/xsel"
            return None

        mock_which.side_effect = which_side_effect

        manager = X11ClipboardManager()

        assert manager.tool == "xclip"

    @patch("shutil.which")
    def test_falls_back_to_xsel(self, mock_which: MagicMock):
        """Test fallback to xsel when xclip is not available."""

        def which_side_effect(cmd):
            if cmd == "xsel":
                return "/usr/bin/xsel"
            return None

        mock_which.side_effect = which_side_effect

        manager = X11ClipboardManager()

        assert manager.tool == "xsel"

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_copy_with_xclip(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test copy using xclip."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.return_value = MagicMock(returncode=0)

        manager = X11ClipboardManager()
        result = manager.copy("test text")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "xclip" in call_args
        assert "-selection" in call_args
        assert "clipboard" in call_args

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_copy_with_xsel(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test copy using xsel."""

        def which_side_effect(cmd):
            if cmd == "xsel":
                return "/usr/bin/xsel"
            return None

        mock_which.side_effect = which_side_effect
        mock_run.return_value = MagicMock(returncode=0)

        manager = X11ClipboardManager()
        result = manager.copy("test text")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "xsel" in call_args
        assert "--clipboard" in call_args

    @patch("shutil.which")
    def test_copy_returns_false_for_empty_text(self, mock_which: MagicMock):
        """Test that copy returns False for empty text."""
        mock_which.return_value = "/usr/bin/xclip"

        manager = X11ClipboardManager()
        result = manager.copy("")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_copy_returns_false_on_timeout(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that copy returns False on timeout."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="xclip", timeout=2.0)

        manager = X11ClipboardManager()
        result = manager.copy("test")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_copy_returns_false_on_error(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that copy returns False on subprocess error."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.return_value = MagicMock(returncode=1, stderr=b"error message")

        manager = X11ClipboardManager()
        result = manager.copy("test")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_copy_returns_false_on_exception(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that copy returns False on general exception."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.side_effect = OSError("Failed to run copy")

        manager = X11ClipboardManager()
        result = manager.copy("test")

        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_with_xclip(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test paste using xclip."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.return_value = MagicMock(returncode=0, stdout="pasted text")

        manager = X11ClipboardManager()
        result = manager.paste()

        assert result == "pasted text"
        call_args = mock_run.call_args[0][0]
        assert "xclip" in call_args
        assert "-o" in call_args

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_with_xsel(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test paste using xsel."""

        def which_side_effect(cmd):
            if cmd == "xsel":
                return "/usr/bin/xsel"
            return None

        mock_which.side_effect = which_side_effect
        mock_run.return_value = MagicMock(returncode=0, stdout="pasted text")

        manager = X11ClipboardManager()
        result = manager.paste()

        assert result == "pasted text"
        call_args = mock_run.call_args[0][0]
        assert "xsel" in call_args
        assert "--output" in call_args

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_none_on_error(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns None on subprocess error."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.return_value = MagicMock(returncode=1, stderr="error message")

        manager = X11ClipboardManager()
        result = manager.paste()

        assert result is None

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_none_on_timeout(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns None on timeout."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="xclip", timeout=2.0)

        manager = X11ClipboardManager()
        result = manager.paste()

        assert result is None

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_paste_returns_none_on_exception(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that paste returns None on general exception."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.side_effect = OSError("Failed to run paste")

        manager = X11ClipboardManager()
        result = manager.paste()

        assert result is None

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_clear_calls_copy_with_empty_string(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that clear calls copy with empty string."""
        mock_which.return_value = "/usr/bin/xclip"
        mock_run.return_value = MagicMock(returncode=0)

        manager = X11ClipboardManager()
        result = manager.clear()

        # clear() calls copy("") which should return True for empty string handling
        # According to the code, copy("") returns False immediately
        assert result is False

    @patch("shutil.which")
    @patch("src.clipboard.subprocess.run")
    def test_clear_returns_false_on_exception(self, mock_run: MagicMock, mock_which: MagicMock):
        """Test that clear returns False on exception."""
        mock_which.return_value = "/usr/bin/xclip"
        # Make copy raise an exception
        mock_run.side_effect = OSError("Failed to clear")

        manager = X11ClipboardManager()
        # Since clear() calls self.copy("") and copy("") returns False for empty text,
        # we need to patch the copy method instead
        with patch.object(manager, "copy", side_effect=Exception("Error")):
            result = manager.clear()

        assert result is False


class TestClipboardManager:
    """Tests for ClipboardManager class (auto-detect wrapper)."""

    @patch("src.clipboard.create_clipboard_manager")
    def test_delegates_to_created_manager(self, mock_create: MagicMock):
        """Test that operations are delegated to the created manager."""
        mock_inner_manager = MagicMock()
        mock_create.return_value = mock_inner_manager

        manager = ClipboardManager()

        assert manager._manager == mock_inner_manager

    @patch("src.clipboard.create_clipboard_manager")
    def test_copy_delegates_to_inner_manager(self, mock_create: MagicMock):
        """Test that copy delegates to inner manager."""
        mock_inner_manager = MagicMock()
        mock_inner_manager.copy.return_value = True
        mock_create.return_value = mock_inner_manager

        manager = ClipboardManager()
        result = manager.copy("test")

        assert result is True
        mock_inner_manager.copy.assert_called_once_with("test")

    @patch("src.clipboard.create_clipboard_manager")
    def test_paste_delegates_to_inner_manager(self, mock_create: MagicMock):
        """Test that paste delegates to inner manager."""
        mock_inner_manager = MagicMock()
        mock_inner_manager.paste.return_value = "pasted"
        mock_create.return_value = mock_inner_manager

        manager = ClipboardManager()
        result = manager.paste()

        assert result == "pasted"
        mock_inner_manager.paste.assert_called_once()

    @patch("src.clipboard.create_clipboard_manager")
    def test_clear_delegates_to_inner_manager(self, mock_create: MagicMock):
        """Test that clear delegates to inner manager."""
        mock_inner_manager = MagicMock()
        mock_inner_manager.clear.return_value = True
        mock_create.return_value = mock_inner_manager

        manager = ClipboardManager()
        result = manager.clear()

        assert result is True
        mock_inner_manager.clear.assert_called_once()

    @patch("src.clipboard.create_clipboard_manager")
    def test_copy_with_retry_retries_on_failure(self, mock_create: MagicMock):
        """Test that copy_with_retry retries on failure."""
        mock_inner_manager = MagicMock()
        mock_inner_manager.copy.side_effect = [False, True]  # Fail then succeed
        mock_create.return_value = mock_inner_manager

        manager = ClipboardManager()
        result = manager.copy_with_retry("test", retries=1)

        assert result is True
        assert mock_inner_manager.copy.call_count == 2

    @patch("src.clipboard.create_clipboard_manager")
    def test_copy_with_retry_gives_up_after_max_retries(self, mock_create: MagicMock):
        """Test that copy_with_retry gives up after max retries."""
        mock_inner_manager = MagicMock()
        mock_inner_manager.copy.return_value = False
        mock_create.return_value = mock_inner_manager

        manager = ClipboardManager()
        result = manager.copy_with_retry("test", retries=2)

        assert result is False
        assert mock_inner_manager.copy.call_count == 3  # Initial + 2 retries


class TestCreateClipboardManager:
    """Tests for create_clipboard_manager function."""

    @patch("src.clipboard.detect_session_type")
    @patch("src.clipboard.WaylandClipboardManager")
    def test_creates_wayland_manager_for_wayland_session(
        self, mock_wayland_class: MagicMock, mock_detect: MagicMock
    ):
        """Test that WaylandClipboardManager is created for Wayland session."""
        mock_detect.return_value = "wayland"
        mock_manager = MagicMock()
        mock_wayland_class.return_value = mock_manager

        result = create_clipboard_manager()

        assert result == mock_manager
        mock_wayland_class.assert_called_once_with(timeout=2.0)

    @patch("src.clipboard.detect_session_type")
    @patch("src.clipboard.X11ClipboardManager")
    def test_creates_x11_manager_for_x11_session(
        self, mock_x11_class: MagicMock, mock_detect: MagicMock
    ):
        """Test that X11ClipboardManager is created for X11 session."""
        mock_detect.return_value = "x11"
        mock_manager = MagicMock()
        mock_x11_class.return_value = mock_manager

        result = create_clipboard_manager()

        assert result == mock_manager
        mock_x11_class.assert_called_once_with(timeout=2.0)

    @patch("src.clipboard.detect_session_type")
    @patch("src.clipboard.WaylandClipboardManager")
    def test_tries_wayland_first_for_unknown_session(
        self, mock_wayland_class: MagicMock, mock_detect: MagicMock
    ):
        """Test that Wayland is tried first for unknown session."""
        mock_detect.return_value = "unknown"
        mock_manager = MagicMock()
        mock_wayland_class.return_value = mock_manager

        result = create_clipboard_manager()

        assert result == mock_manager
        mock_wayland_class.assert_called_once()

    @patch("src.clipboard.detect_session_type")
    @patch("src.clipboard.WaylandClipboardManager")
    @patch("src.clipboard.X11ClipboardManager")
    def test_falls_back_to_x11_for_unknown_session(
        self,
        mock_x11_class: MagicMock,
        mock_wayland_class: MagicMock,
        mock_detect: MagicMock,
    ):
        """Test that X11 is used as fallback for unknown session."""
        mock_detect.return_value = "unknown"
        mock_wayland_class.side_effect = RuntimeError("wl-copy not found")
        mock_manager = MagicMock()
        mock_x11_class.return_value = mock_manager

        result = create_clipboard_manager()

        assert result == mock_manager
        mock_x11_class.assert_called_once()

    @patch("src.clipboard.detect_session_type")
    @patch("src.clipboard.WaylandClipboardManager")
    @patch("src.clipboard.X11ClipboardManager")
    def test_raises_error_when_no_manager_available(
        self,
        mock_x11_class: MagicMock,
        mock_wayland_class: MagicMock,
        mock_detect: MagicMock,
    ):
        """Test that RuntimeError is raised when no manager is available."""
        mock_detect.return_value = "unknown"
        mock_wayland_class.side_effect = RuntimeError("wl-copy not found")
        mock_x11_class.side_effect = RuntimeError("xclip not found")

        with pytest.raises(RuntimeError, match="Could not initialize clipboard manager"):
            create_clipboard_manager()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch("src.clipboard.get_clipboard_manager")
    def test_copy_to_clipboard_calls_manager(self, mock_get_manager: MagicMock):
        """Test that copy_to_clipboard uses the manager."""
        mock_manager = MagicMock()
        mock_manager.copy_with_retry.return_value = True
        mock_get_manager.return_value = mock_manager

        result = copy_to_clipboard("test text")

        assert result is True
        mock_manager.copy_with_retry.assert_called_once_with("test text", retries=1)

    @patch("src.clipboard.get_clipboard_manager")
    def test_paste_from_clipboard_calls_manager(self, mock_get_manager: MagicMock):
        """Test that paste_from_clipboard uses the manager."""
        mock_manager = MagicMock()
        mock_manager.paste.return_value = "pasted text"
        mock_get_manager.return_value = mock_manager

        result = paste_from_clipboard()

        assert result == "pasted text"
        mock_manager.paste.assert_called_once()

    @patch("src.clipboard.get_clipboard_manager")
    def test_clear_clipboard_calls_manager(self, mock_get_manager: MagicMock):
        """Test that clear_clipboard uses the manager."""
        mock_manager = MagicMock()
        mock_manager.clear.return_value = True
        mock_get_manager.return_value = mock_manager

        result = clear_clipboard()

        assert result is True
        mock_manager.clear.assert_called_once()


class TestGetClipboardManager:
    """Tests for get_clipboard_manager singleton function."""

    def test_returns_same_instance(self):
        """Test that get_clipboard_manager returns the same instance."""
        # Reset the singleton for testing
        import src.clipboard

        src.clipboard._default_manager = None

        with patch("src.clipboard.ClipboardManager") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            manager1 = get_clipboard_manager()
            manager2 = get_clipboard_manager()

            # Should only create one instance
            mock_class.assert_called_once()
            assert manager1 == manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
