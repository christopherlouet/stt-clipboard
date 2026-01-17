"""Tests for startup system tools validation."""

from unittest.mock import MagicMock, patch

from src.config import Config


class TestCheckClipboardTool:
    """Tests for check_clipboard_tool helper."""

    @patch("src.clipboard.is_macos", return_value=False)
    @patch("shutil.which")
    def test_returns_true_when_wl_copy_available(
        self, mock_which: MagicMock, mock_is_macos: MagicMock
    ):
        """Test returns True when wl-copy is available."""
        from src.clipboard import check_clipboard_tool

        mock_which.side_effect = lambda x: "/usr/bin/wl-copy" if x == "wl-copy" else None

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            result = check_clipboard_tool()

        assert result is True

    @patch("src.clipboard.is_macos", return_value=False)
    @patch("shutil.which")
    def test_returns_true_when_xclip_available(
        self, mock_which: MagicMock, mock_is_macos: MagicMock
    ):
        """Test returns True when xclip is available for X11."""
        from src.clipboard import check_clipboard_tool

        mock_which.side_effect = lambda x: "/usr/bin/xclip" if x == "xclip" else None

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            result = check_clipboard_tool()

        assert result is True

    @patch("src.clipboard.is_macos", return_value=False)
    @patch("shutil.which")
    def test_returns_true_when_xsel_available(
        self, mock_which: MagicMock, mock_is_macos: MagicMock
    ):
        """Test returns True when xsel is available for X11."""
        from src.clipboard import check_clipboard_tool

        mock_which.side_effect = lambda x: "/usr/bin/xsel" if x == "xsel" else None

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            result = check_clipboard_tool()

        assert result is True

    @patch("src.clipboard.is_macos", return_value=False)
    @patch("shutil.which")
    def test_returns_false_when_no_tools_available(
        self, mock_which: MagicMock, mock_is_macos: MagicMock
    ):
        """Test returns False when no clipboard tools are available."""
        from src.clipboard import check_clipboard_tool

        mock_which.return_value = None

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            result = check_clipboard_tool()

        assert result is False

    @patch("src.clipboard.is_macos", return_value=True)
    @patch("shutil.which")
    def test_returns_true_when_pbcopy_available_on_macos(
        self, mock_which: MagicMock, mock_is_macos: MagicMock
    ):
        """Test returns True when pbcopy is available on macOS."""
        from src.clipboard import check_clipboard_tool

        mock_which.side_effect = lambda x: "/usr/bin/pbcopy" if x == "pbcopy" else None

        result = check_clipboard_tool()

        assert result is True


class TestCheckPasteTool:
    """Tests for check_paste_tool helper."""

    @patch("shutil.which")
    def test_returns_true_when_xdotool_available(self, mock_which: MagicMock):
        """Test returns True when xdotool is available."""
        from src.autopaste import check_paste_tool

        mock_which.return_value = "/usr/bin/xdotool"

        result = check_paste_tool("xdotool")

        assert result is True

    @patch("shutil.which")
    def test_returns_true_when_ydotool_available(self, mock_which: MagicMock):
        """Test returns True when ydotool is available."""
        from src.autopaste import check_paste_tool

        mock_which.return_value = "/usr/bin/ydotool"

        result = check_paste_tool("ydotool")

        assert result is True

    @patch("shutil.which")
    def test_returns_true_when_wtype_available(self, mock_which: MagicMock):
        """Test returns True when wtype is available."""
        from src.autopaste import check_paste_tool

        mock_which.return_value = "/usr/bin/wtype"

        result = check_paste_tool("wtype")

        assert result is True

    @patch("shutil.which")
    def test_returns_false_when_tool_not_available(self, mock_which: MagicMock):
        """Test returns False when specified tool is not available."""
        from src.autopaste import check_paste_tool

        mock_which.return_value = None

        result = check_paste_tool("xdotool")

        assert result is False

    @patch("shutil.which")
    def test_auto_mode_returns_true_when_any_tool_available(self, mock_which: MagicMock):
        """Test auto mode returns True when any paste tool is available."""
        from src.autopaste import check_paste_tool

        mock_which.side_effect = lambda x: "/usr/bin/ydotool" if x == "ydotool" else None

        result = check_paste_tool("auto")

        assert result is True

    @patch("shutil.which")
    def test_auto_mode_returns_false_when_no_tools_available(self, mock_which: MagicMock):
        """Test auto mode returns False when no paste tools are available."""
        from src.autopaste import check_paste_tool

        mock_which.return_value = None

        result = check_paste_tool("auto")

        assert result is False


class TestValidateSystemTools:
    """Tests for validate_system_tools method."""

    @patch("src.config.check_clipboard_tool")
    @patch("src.config.check_paste_tool")
    def test_returns_true_when_all_tools_available(
        self, mock_paste: MagicMock, mock_clipboard: MagicMock
    ):
        """Test returns True when all required tools are available."""
        mock_clipboard.return_value = True
        mock_paste.return_value = True

        config = Config()
        result = config.validate_system_tools()

        assert result.is_valid is True
        assert len(result.errors) == 0

    @patch("src.config.check_clipboard_tool")
    @patch("src.config.check_paste_tool")
    def test_returns_error_when_clipboard_tool_missing(
        self, mock_paste: MagicMock, mock_clipboard: MagicMock
    ):
        """Test returns error when clipboard tool is missing."""
        mock_clipboard.return_value = False
        mock_paste.return_value = True

        config = Config()
        result = config.validate_system_tools()

        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("clipboard" in e.lower() for e in result.errors)

    @patch("src.config.check_clipboard_tool")
    @patch("src.config.check_paste_tool")
    def test_skips_paste_validation_when_disabled(
        self, mock_paste: MagicMock, mock_clipboard: MagicMock
    ):
        """Test skips paste tool validation when paste is disabled."""
        mock_clipboard.return_value = True

        config = Config()
        config.paste.enabled = False
        result = config.validate_system_tools()

        assert result.is_valid is True
        mock_paste.assert_not_called()

    @patch("src.config.check_clipboard_tool")
    @patch("src.config.check_paste_tool")
    def test_skips_clipboard_validation_when_disabled(
        self, mock_paste: MagicMock, mock_clipboard: MagicMock
    ):
        """Test skips clipboard tool validation when clipboard is disabled."""
        mock_paste.return_value = True

        config = Config()
        config.clipboard.enabled = False
        result = config.validate_system_tools()

        assert result.is_valid is True
        mock_clipboard.assert_not_called()

    @patch("src.config.check_clipboard_tool")
    @patch("src.config.check_paste_tool")
    def test_returns_error_and_warning_when_tools_missing(
        self, mock_paste: MagicMock, mock_clipboard: MagicMock
    ):
        """Test returns error for clipboard and warning for paste when missing."""
        mock_clipboard.return_value = False
        mock_paste.return_value = False

        config = Config()
        result = config.validate_system_tools()

        assert result.is_valid is False
        assert len(result.errors) >= 1  # Clipboard error
        assert len(result.warnings) >= 1  # Paste warning

    @patch("src.config.check_clipboard_tool")
    @patch("src.config.check_paste_tool")
    def test_returns_warning_for_optional_missing_tools(
        self, mock_paste: MagicMock, mock_clipboard: MagicMock
    ):
        """Test returns warning when optional paste tool is missing."""
        mock_clipboard.return_value = True
        mock_paste.return_value = False

        config = Config()
        result = config.validate_system_tools()

        # Paste is optional, so should still be valid
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("paste" in w.lower() for w in result.warnings)
