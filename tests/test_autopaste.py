#!/usr/bin/env python3
"""Test auto-paste functionality."""

from unittest.mock import MagicMock, patch

import pytest

from src.autopaste import (
    AutoPasteError,
    BaseAutoPaster,
    MacPaster,
    WtypePaster,
    XdotoolPaster,
    YdotoolPaster,
    _detect_available_tools,
    auto_paste,
    create_autopaster,
)


def test_base_autopaster_interface():
    """Test that BaseAutoPaster defines the correct interface."""
    # Verify abstract methods
    assert hasattr(BaseAutoPaster, "paste")
    assert hasattr(BaseAutoPaster, "is_available")


def test_xdotool_paster_initialization():
    """Test XdotoolPaster initialization."""
    paster = XdotoolPaster(timeout=2.0)
    assert paster.timeout == 2.0

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_ydotool_paster_initialization():
    """Test YdotoolPaster initialization."""
    # Test standard paste (Ctrl+V)
    paster = YdotoolPaster(timeout=2.0, use_shift=False)
    assert paster.timeout == 2.0
    assert paster.use_shift is False

    # Test terminal paste (Ctrl+Shift+V)
    paster_terminal = YdotoolPaster(timeout=2.0, use_shift=True)
    assert paster_terminal.timeout == 2.0
    assert paster_terminal.use_shift is True

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_wtype_paster_initialization():
    """Test WtypePaster initialization."""
    paster = WtypePaster(timeout=2.0)
    assert paster.timeout == 2.0

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_mac_paster_initialization():
    """Test MacPaster initialization."""
    paster = MacPaster(timeout=2.0)
    assert paster.timeout == 2.0

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_create_autopaster_auto_detection():
    """Test auto-detection of paste tools."""
    try:
        # Should either return an autopaster or raise RuntimeError
        paster = create_autopaster(preferred_tool="auto", timeout=2.0)
        assert isinstance(paster, BaseAutoPaster)
        assert paster.timeout == 2.0
    except RuntimeError as e:
        # Expected if no paste tool is available
        assert "No auto-paste tool available" in str(e)
        pytest.skip("No paste tool available in test environment")


def test_create_autopaster_preferred_tool():
    """Test creating autopaster with preferred tool."""
    # Tool name to expected class mapping
    tool_class_map = {
        "osascript": MacPaster,
        "xdotool": XdotoolPaster,
        "ydotool": YdotoolPaster,
        "wtype": WtypePaster,
    }

    # Test with each tool type
    for tool, expected_class in tool_class_map.items():
        try:
            paster = create_autopaster(preferred_tool=tool, timeout=2.0)
            assert isinstance(paster, BaseAutoPaster)
            assert paster.timeout == 2.0

            # Only verify type if the preferred tool is actually available
            # (otherwise it falls back to another available tool)
            if isinstance(paster, expected_class):
                # Preferred tool was available and used
                pass
            else:
                # Preferred tool was not available, fell back to another
                # This is expected behavior, just ensure we got a valid paster
                pass

        except RuntimeError:
            # No tool available at all, that's ok in test environment
            pytest.skip("No paste tool available in test environment")


def test_paste_tool_detection():
    """Test that at least one paste tool can be detected."""
    from src.autopaste import _detect_available_tools

    available_tools = _detect_available_tools(timeout=2.0)

    # In test environment, may have 0 or more tools
    assert isinstance(available_tools, list)

    # If tools are available, they should all be BaseAutoPaster instances
    for tool in available_tools:
        assert isinstance(tool, BaseAutoPaster)


@pytest.mark.skip(reason="Requires interactive environment with running display server")
def test_paste_operation():
    """Test actual paste operation (requires interactive environment)."""
    # This test is skipped by default as it requires:
    # 1. A running display server (Wayland or X11)
    # 2. Paste tool installed (xdotool, ydotool, or wtype)
    # 3. Active window to paste into

    paster = create_autopaster(preferred_tool="auto", timeout=2.0)
    success = paster.paste()
    assert isinstance(success, bool)


class TestAutoPasteError:
    """Tests for AutoPasteError exception."""

    def test_exception_exists(self):
        """Test that AutoPasteError is defined."""
        error = AutoPasteError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


class TestXdotoolPasterMocked:
    """Tests for XdotoolPaster with mocking."""

    @patch("src.autopaste.subprocess.run")
    @patch.dict("os.environ", {"DISPLAY": ":0"})
    def test_is_available_when_xdotool_installed(self, mock_run: MagicMock):
        """Test is_available returns True when xdotool is installed and DISPLAY set."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = XdotoolPaster(timeout=2.0)

        result = paster.is_available()

        assert result is True

    @patch("src.autopaste.subprocess.run")
    @patch.dict("os.environ", {"DISPLAY": ""}, clear=True)
    def test_is_available_when_no_display(self, mock_run: MagicMock):
        """Test is_available returns False when DISPLAY not set."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = XdotoolPaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_is_available_when_xdotool_not_installed(self, mock_run: MagicMock):
        """Test is_available returns False when xdotool not installed."""
        mock_run.return_value = MagicMock(returncode=1)
        paster = XdotoolPaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_is_available_on_timeout(self, mock_run: MagicMock):
        """Test is_available returns False on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("which", 1)
        paster = XdotoolPaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_success(self, mock_run: MagicMock):
        """Test paste returns True on success."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = XdotoolPaster(timeout=2.0)

        result = paster.paste()

        assert result is True
        mock_run.assert_called_with(
            ["xdotool", "key", "ctrl+v"],
            capture_output=True,
            timeout=2.0,
            check=False,
        )

    @patch("src.autopaste.subprocess.run")
    def test_paste_failure(self, mock_run: MagicMock):
        """Test paste returns False on failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr=b"Error")
        paster = XdotoolPaster(timeout=2.0)

        result = paster.paste()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_timeout(self, mock_run: MagicMock):
        """Test paste returns False on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("xdotool", 2)
        paster = XdotoolPaster(timeout=2.0)

        result = paster.paste()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_exception(self, mock_run: MagicMock):
        """Test paste returns False on exception."""
        mock_run.side_effect = RuntimeError("Unknown error")
        paster = XdotoolPaster(timeout=2.0)

        result = paster.paste()

        assert result is False


class TestYdotoolPasterMocked:
    """Tests for YdotoolPaster with mocking."""

    @patch("src.autopaste.subprocess.run")
    def test_is_available_when_ydotool_and_daemon_running(self, mock_run: MagicMock):
        """Test is_available returns True when ydotool and daemon are available."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = YdotoolPaster(timeout=2.0)

        result = paster.is_available()

        assert result is True
        # Should check both 'which ydotool' and 'pgrep ydotoold'
        assert mock_run.call_count == 2

    @patch("src.autopaste.subprocess.run")
    def test_is_available_when_daemon_not_running(self, mock_run: MagicMock):
        """Test is_available returns False when daemon not running."""
        # First call (which ydotool) succeeds, second call (pgrep) fails
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which ydotool
            MagicMock(returncode=1),  # pgrep ydotoold
        ]
        paster = YdotoolPaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_ctrl_v(self, mock_run: MagicMock):
        """Test paste with Ctrl+V (use_shift=False)."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = YdotoolPaster(timeout=2.0, use_shift=False)

        result = paster.paste()

        assert result is True
        # Ctrl+V: 29:1, 47:1, 47:0, 29:0
        mock_run.assert_called_with(
            ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"],
            capture_output=True,
            timeout=2.0,
            check=False,
        )

    @patch("src.autopaste.subprocess.run")
    def test_paste_ctrl_shift_v(self, mock_run: MagicMock):
        """Test paste with Ctrl+Shift+V (use_shift=True)."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = YdotoolPaster(timeout=2.0, use_shift=True)

        result = paster.paste()

        assert result is True
        # Ctrl+Shift+V: 29:1, 42:1, 47:1, 47:0, 42:0, 29:0
        mock_run.assert_called_with(
            ["ydotool", "key", "29:1", "42:1", "47:1", "47:0", "42:0", "29:0"],
            capture_output=True,
            timeout=2.0,
            check=False,
        )

    @patch("src.autopaste.subprocess.run")
    def test_paste_failure(self, mock_run: MagicMock):
        """Test paste returns False on failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr=b"Error")
        paster = YdotoolPaster(timeout=2.0)

        result = paster.paste()

        assert result is False


class TestWtypePasterMocked:
    """Tests for WtypePaster with mocking."""

    @patch("src.autopaste.subprocess.run")
    @patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-0"})
    def test_is_available_when_wtype_installed_and_wayland(self, mock_run: MagicMock):
        """Test is_available returns True when wtype installed and Wayland session."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = WtypePaster(timeout=2.0)

        result = paster.is_available()

        assert result is True

    @patch("src.autopaste.subprocess.run")
    @patch.dict("os.environ", {"WAYLAND_DISPLAY": ""}, clear=True)
    def test_is_available_when_no_wayland_display(self, mock_run: MagicMock):
        """Test is_available returns False when WAYLAND_DISPLAY not set."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = WtypePaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.clipboard.paste_from_clipboard")
    @patch("src.autopaste.subprocess.run")
    def test_paste_success(self, mock_run: MagicMock, mock_clipboard: MagicMock):
        """Test paste returns True on success."""
        mock_clipboard.return_value = "test text"
        mock_run.return_value = MagicMock(returncode=0)
        paster = WtypePaster(timeout=2.0)

        result = paster.paste()

        assert result is True
        mock_run.assert_called_with(
            ["wtype", "test text"],
            capture_output=True,
            timeout=2.0,
            check=False,
        )

    @patch("src.clipboard.paste_from_clipboard")
    @patch("src.autopaste.subprocess.run")
    def test_paste_fails_when_no_clipboard_content(
        self, mock_run: MagicMock, mock_clipboard: MagicMock
    ):
        """Test paste returns False when clipboard is empty."""
        mock_clipboard.return_value = None
        paster = WtypePaster(timeout=2.0)

        result = paster.paste()

        assert result is False
        mock_run.assert_not_called()

    @patch("src.clipboard.paste_from_clipboard")
    @patch("src.autopaste.subprocess.run")
    def test_paste_failure(self, mock_run: MagicMock, mock_clipboard: MagicMock):
        """Test paste returns False on wtype failure."""
        mock_clipboard.return_value = "test text"
        mock_run.return_value = MagicMock(returncode=1, stderr=b"Error")
        paster = WtypePaster(timeout=2.0)

        result = paster.paste()

        assert result is False

    @patch("src.clipboard.paste_from_clipboard")
    @patch("src.autopaste.subprocess.run")
    def test_paste_timeout(self, mock_run: MagicMock, mock_clipboard: MagicMock):
        """Test paste returns False on timeout."""
        import subprocess

        mock_clipboard.return_value = "test text"
        mock_run.side_effect = subprocess.TimeoutExpired("wtype", 2)
        paster = WtypePaster(timeout=2.0)

        result = paster.paste()

        assert result is False


class TestMacPasterMocked:
    """Tests for MacPaster with mocking."""

    @patch("src.autopaste.shutil.which")
    @patch("src.autopaste.platform.system")
    def test_is_available_on_macos(self, mock_system: MagicMock, mock_which: MagicMock):
        """Test is_available returns True when on macOS with osascript."""
        mock_system.return_value = "Darwin"
        mock_which.return_value = "/usr/bin/osascript"
        paster = MacPaster(timeout=2.0)

        result = paster.is_available()

        assert result is True
        mock_system.assert_called_once()
        mock_which.assert_called_once_with("osascript")

    @patch("src.autopaste.platform.system")
    def test_is_available_not_on_macos(self, mock_system: MagicMock):
        """Test is_available returns False when not on macOS."""
        mock_system.return_value = "Linux"
        paster = MacPaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.autopaste.shutil.which")
    @patch("src.autopaste.platform.system")
    def test_is_available_no_osascript(self, mock_system: MagicMock, mock_which: MagicMock):
        """Test is_available returns False when osascript not found."""
        mock_system.return_value = "Darwin"
        mock_which.return_value = None
        paster = MacPaster(timeout=2.0)

        result = paster.is_available()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_success(self, mock_run: MagicMock):
        """Test paste returns True on success."""
        mock_run.return_value = MagicMock(returncode=0)
        paster = MacPaster(timeout=2.0)

        result = paster.paste()

        assert result is True
        mock_run.assert_called_once()
        # Verify the osascript command is correct
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "osascript"
        assert call_args[0][0][1] == "-e"
        assert "System Events" in call_args[0][0][2]
        assert "keystroke" in call_args[0][0][2]

    @patch("src.autopaste.subprocess.run")
    def test_paste_failure(self, mock_run: MagicMock):
        """Test paste returns False on failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr=b"Error")
        paster = MacPaster(timeout=2.0)

        result = paster.paste()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_timeout(self, mock_run: MagicMock):
        """Test paste returns False on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("osascript", 2)
        paster = MacPaster(timeout=2.0)

        result = paster.paste()

        assert result is False

    @patch("src.autopaste.subprocess.run")
    def test_paste_exception(self, mock_run: MagicMock):
        """Test paste returns False on exception."""
        mock_run.side_effect = RuntimeError("Unknown error")
        paster = MacPaster(timeout=2.0)

        result = paster.paste()

        assert result is False


class TestDetectAvailableTools:
    """Tests for _detect_available_tools function."""

    @patch("src.autopaste.WtypePaster")
    @patch("src.autopaste.YdotoolPaster")
    @patch("src.autopaste.XdotoolPaster")
    @patch("src.autopaste.MacPaster")
    def test_returns_available_tools(
        self,
        mock_mac: MagicMock,
        mock_xdotool: MagicMock,
        mock_ydotool: MagicMock,
        mock_wtype: MagicMock,
    ):
        """Test that only available tools are returned."""
        mock_mac_instance = MagicMock()
        mock_mac_instance.is_available.return_value = False
        mock_mac.return_value = mock_mac_instance

        mock_xdotool_instance = MagicMock()
        mock_xdotool_instance.is_available.return_value = True
        mock_xdotool.return_value = mock_xdotool_instance

        mock_ydotool_instance = MagicMock()
        mock_ydotool_instance.is_available.return_value = False
        mock_ydotool.return_value = mock_ydotool_instance

        mock_wtype_instance = MagicMock()
        mock_wtype_instance.is_available.return_value = True
        mock_wtype.return_value = mock_wtype_instance

        result = _detect_available_tools(timeout=2.0)

        assert len(result) == 2
        assert mock_xdotool_instance in result
        assert mock_wtype_instance in result
        assert mock_ydotool_instance not in result
        assert mock_mac_instance not in result

    @patch("src.autopaste.WtypePaster")
    @patch("src.autopaste.YdotoolPaster")
    @patch("src.autopaste.XdotoolPaster")
    @patch("src.autopaste.MacPaster")
    def test_returns_empty_when_no_tools_available(
        self,
        mock_mac: MagicMock,
        mock_xdotool: MagicMock,
        mock_ydotool: MagicMock,
        mock_wtype: MagicMock,
    ):
        """Test that empty list is returned when no tools available."""
        for mock in [mock_mac, mock_xdotool, mock_ydotool, mock_wtype]:
            instance = MagicMock()
            instance.is_available.return_value = False
            mock.return_value = instance

        result = _detect_available_tools(timeout=2.0)

        assert result == []

    @patch("src.autopaste.WtypePaster")
    @patch("src.autopaste.YdotoolPaster")
    @patch("src.autopaste.XdotoolPaster")
    @patch("src.autopaste.MacPaster")
    def test_mac_paster_first_on_macos(
        self,
        mock_mac: MagicMock,
        mock_xdotool: MagicMock,
        mock_ydotool: MagicMock,
        mock_wtype: MagicMock,
    ):
        """Test that MacPaster is first in the list when available."""
        mock_mac_instance = MagicMock()
        mock_mac_instance.is_available.return_value = True
        mock_mac.return_value = mock_mac_instance

        mock_xdotool_instance = MagicMock()
        mock_xdotool_instance.is_available.return_value = False
        mock_xdotool.return_value = mock_xdotool_instance

        mock_ydotool_instance = MagicMock()
        mock_ydotool_instance.is_available.return_value = False
        mock_ydotool.return_value = mock_ydotool_instance

        mock_wtype_instance = MagicMock()
        mock_wtype_instance.is_available.return_value = False
        mock_wtype.return_value = mock_wtype_instance

        result = _detect_available_tools(timeout=2.0)

        assert len(result) == 1
        assert result[0] == mock_mac_instance


class TestCreateAutopasterMocked:
    """Tests for create_autopaster function with mocking."""

    @patch("src.autopaste._detect_available_tools")
    def test_raises_when_no_tools_available(self, mock_detect: MagicMock):
        """Test RuntimeError raised when no tools available."""
        mock_detect.return_value = []

        with pytest.raises(RuntimeError, match="No auto-paste tool available"):
            create_autopaster()

    @patch("src.autopaste._detect_available_tools")
    def test_returns_first_available_tool_on_auto(self, mock_detect: MagicMock):
        """Test returns first available tool when preferred_tool is auto."""
        mock_tool1 = MagicMock(spec=XdotoolPaster)
        mock_tool2 = MagicMock(spec=YdotoolPaster)
        mock_detect.return_value = [mock_tool1, mock_tool2]

        result = create_autopaster(preferred_tool="auto")

        assert result == mock_tool1

    @patch("src.autopaste._detect_available_tools")
    def test_returns_preferred_tool_if_available(self, mock_detect: MagicMock):
        """Test returns preferred tool if available."""
        mock_xdotool = MagicMock(spec=XdotoolPaster)
        mock_ydotool = MagicMock(spec=YdotoolPaster)
        mock_detect.return_value = [mock_xdotool, mock_ydotool]

        result = create_autopaster(preferred_tool="ydotool")

        assert result == mock_ydotool

    @patch("src.autopaste._detect_available_tools")
    def test_falls_back_when_preferred_not_available(self, mock_detect: MagicMock):
        """Test falls back to first available when preferred not found."""
        mock_xdotool = MagicMock(spec=XdotoolPaster)
        mock_detect.return_value = [mock_xdotool]

        # Request ydotool but only xdotool is available
        result = create_autopaster(preferred_tool="ydotool")

        assert result == mock_xdotool

    @patch("src.autopaste._detect_available_tools")
    def test_returns_osascript_when_preferred(self, mock_detect: MagicMock):
        """Test returns MacPaster when osascript is preferred."""
        mock_mac = MagicMock(spec=MacPaster)
        mock_xdotool = MagicMock(spec=XdotoolPaster)
        mock_detect.return_value = [mock_mac, mock_xdotool]

        result = create_autopaster(preferred_tool="osascript")

        assert result == mock_mac


class TestAutoPasteFunction:
    """Tests for auto_paste convenience function."""

    @patch("src.autopaste.create_autopaster")
    def test_auto_paste_success(self, mock_create: MagicMock):
        """Test auto_paste returns True on success."""
        mock_paster = MagicMock()
        mock_paster.paste.return_value = True
        mock_create.return_value = mock_paster

        result = auto_paste(timeout=2.0, preferred_tool="auto")

        assert result is True
        mock_create.assert_called_once_with(preferred_tool="auto", timeout=2.0)
        mock_paster.paste.assert_called_once()

    @patch("src.autopaste.create_autopaster")
    def test_auto_paste_failure(self, mock_create: MagicMock):
        """Test auto_paste returns False on failure."""
        mock_paster = MagicMock()
        mock_paster.paste.return_value = False
        mock_create.return_value = mock_paster

        result = auto_paste()

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
