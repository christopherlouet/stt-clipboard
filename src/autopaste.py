"""Auto-paste functionality for simulating keyboard paste operations."""

import os
import platform
import shutil
import subprocess
from abc import ABC, abstractmethod

from loguru import logger


class AutoPasteError(Exception):
    """Exception raised when auto-paste operations fail."""

    pass


class BaseAutoPaster(ABC):
    """Base class for auto-paste implementations."""

    def __init__(self, timeout: float = 2.0):
        """Initialize auto-paster.

        Args:
            timeout: Timeout for paste operations
        """
        self.timeout = timeout

    @abstractmethod
    def paste(self) -> bool:
        """Simulate Ctrl+V paste operation.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this paste method is available.

        Returns:
            True if available, False otherwise
        """
        pass


class XdotoolPaster(BaseAutoPaster):
    """Auto-paste implementation using xdotool (X11)."""

    def is_available(self) -> bool:
        """Check if xdotool is available and we're in X11."""
        # Check if xdotool is installed
        try:
            result = subprocess.run(
                ["which", "xdotool"],
                capture_output=True,
                timeout=1,
                check=False,
            )
            if result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

        # Check if we have a DISPLAY (X11 session)
        return bool(os.environ.get("DISPLAY"))

    def paste(self) -> bool:
        """Simulate Ctrl+V using xdotool."""
        try:
            result = subprocess.run(
                ["xdotool", "key", "ctrl+v"],
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )

            if result.returncode == 0:
                logger.debug("xdotool paste successful")
                return True
            else:
                logger.error(f"xdotool paste failed: {result.stderr.decode()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("xdotool paste timeout")
            return False
        except Exception as e:
            logger.error(f"xdotool paste error: {e}")
            return False


class YdotoolPaster(BaseAutoPaster):
    """Auto-paste implementation using ydotool (universal)."""

    def __init__(self, timeout: float = 2.0, use_shift: bool = False):
        """Initialize ydotool paster.

        Args:
            timeout: Timeout for paste operations
            use_shift: If True, use Ctrl+Shift+V (for terminals), else Ctrl+V
        """
        super().__init__(timeout)
        self.use_shift = use_shift

    def is_available(self) -> bool:
        """Check if ydotool is available and daemon is running."""
        # Check if ydotool is installed
        try:
            result = subprocess.run(
                ["which", "ydotool"],
                capture_output=True,
                timeout=1,
                check=False,
            )
            if result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

        # Check if ydotoold daemon is running
        try:
            result = subprocess.run(
                ["pgrep", "ydotoold"],
                capture_output=True,
                timeout=1,
                check=False,
            )
            if result.returncode != 0:
                logger.debug("ydotoold daemon not running")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

        return True

    def paste(self) -> bool:
        """Simulate Ctrl+V or Ctrl+Shift+V using ydotool.

        ydotool uses key codes: Ctrl=29, Shift=42, V=47
        Format: KEY:DOWN, KEY:UP
        """
        try:
            if self.use_shift:
                # Press Ctrl+Shift+V: Ctrl down, Shift down, V down, V up, Shift up, Ctrl up
                cmd = ["ydotool", "key", "29:1", "42:1", "47:1", "47:0", "42:0", "29:0"]
            else:
                # Press Ctrl+V: Ctrl down, V down, V up, Ctrl up
                cmd = ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )

            if result.returncode == 0:
                logger.debug("ydotool paste successful")
                return True
            else:
                logger.error(f"ydotool paste failed: {result.stderr.decode()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("ydotool paste timeout")
            return False
        except Exception as e:
            logger.error(f"ydotool paste error: {e}")
            return False


class WtypePaster(BaseAutoPaster):
    """Auto-paste implementation using wtype (Wayland, direct typing)."""

    def is_available(self) -> bool:
        """Check if wtype is available and we're in Wayland."""
        # Check if wtype is installed
        try:
            result = subprocess.run(
                ["which", "wtype"],
                capture_output=True,
                timeout=1,
                check=False,
            )
            if result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

        # Check if we have a WAYLAND_DISPLAY (Wayland session)
        return bool(os.environ.get("WAYLAND_DISPLAY"))

    def paste(self) -> bool:
        """Paste text using wtype (types clipboard content directly).

        Note: wtype cannot simulate Ctrl+V, so we need to get clipboard
        content and type it directly. This approach has limitations with
        special characters.
        """
        try:
            # Get clipboard content first
            from src.clipboard import paste_from_clipboard

            text = paste_from_clipboard(timeout=self.timeout)
            if not text:
                logger.error("wtype paste failed: no clipboard content")
                return False

            # Type the text using wtype
            result = subprocess.run(
                ["wtype", text],
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )

            if result.returncode == 0:
                logger.debug("wtype paste successful")
                return True
            else:
                logger.error(f"wtype paste failed: {result.stderr.decode()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("wtype paste timeout")
            return False
        except Exception as e:
            logger.error(f"wtype paste error: {e}")
            return False


class MacPaster(BaseAutoPaster):
    """Auto-paste implementation using osascript (macOS)."""

    def is_available(self) -> bool:
        """Check if osascript is available and we're on macOS."""
        # Check if we're on macOS
        if platform.system() != "Darwin":
            return False

        # Check if osascript is available (should always be on macOS)
        return shutil.which("osascript") is not None

    def paste(self) -> bool:
        """Simulate Cmd+V using osascript and System Events.

        Note: This requires Accessibility permissions to be granted to the
        terminal or application running this code. Users need to enable this
        in System Preferences → Security & Privacy → Privacy → Accessibility.
        """
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke "v" using command down',
                ],
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )

            if result.returncode == 0:
                logger.debug("osascript paste successful")
                return True
            else:
                stderr = result.stderr.decode("utf-8", errors="ignore").strip()
                logger.error(f"osascript paste failed: {stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"osascript paste timed out after {self.timeout}s")
            return False

        except Exception as e:
            logger.error(f"osascript paste error: {e}")
            return False


def _detect_available_tools(timeout: float = 2.0) -> list[BaseAutoPaster]:
    """Detect which paste tools are available on the system.

    Args:
        timeout: Timeout for tool operations

    Returns:
        List of available paste tool instances, in order of preference
    """
    available: list[BaseAutoPaster] = []

    # Try osascript (macOS) - check first as it's platform-specific
    mac = MacPaster(timeout)
    if mac.is_available():
        available.append(mac)
        logger.debug("osascript is available (macOS)")

    # Try xdotool (X11)
    xdotool = XdotoolPaster(timeout)
    if xdotool.is_available():
        available.append(xdotool)
        logger.debug("xdotool is available")

    # Try ydotool (universal)
    ydotool = YdotoolPaster(timeout)
    if ydotool.is_available():
        available.append(ydotool)
        logger.debug("ydotool is available")

    # Try wtype (Wayland, last resort)
    wtype = WtypePaster(timeout)
    if wtype.is_available():
        available.append(wtype)
        logger.debug("wtype is available")

    return available


def create_autopaster(
    preferred_tool: str = "auto",
    timeout: float = 2.0,
) -> BaseAutoPaster:
    """Create an auto-paster instance with automatic tool detection.

    Args:
        preferred_tool: Preferred tool ("auto", "osascript", "xdotool", "ydotool", "wtype")
        timeout: Timeout for paste operations

    Returns:
        Auto-paster instance

    Raises:
        RuntimeError: If no paste tool is available
    """
    available_tools = _detect_available_tools(timeout)

    if not available_tools:
        raise RuntimeError(
            "No auto-paste tool available. Please install xdotool (X11), "
            "ydotool (universal), wtype (Wayland), or use osascript (macOS)"
        )

    # If preferred tool is specified, try to find it
    if preferred_tool != "auto":
        tool_map = {
            "osascript": MacPaster,
            "xdotool": XdotoolPaster,
            "ydotool": YdotoolPaster,
            "wtype": WtypePaster,
        }

        preferred_class = tool_map.get(preferred_tool)
        if preferred_class:
            # Check if this specific tool is available
            for tool in available_tools:
                if isinstance(tool, preferred_class):
                    logger.info(f"Using preferred auto-paste tool: {preferred_tool}")
                    return tool

            logger.warning(
                f"Preferred tool '{preferred_tool}' not available, falling back to auto-detection"
            )

    # Return first available tool (highest priority)
    tool = available_tools[0]
    logger.info(f"Using auto-paste tool: {tool.__class__.__name__}")
    return tool


# Convenience function for direct paste
def auto_paste(timeout: float = 2.0, preferred_tool: str = "auto") -> bool:
    """Perform auto-paste operation.

    Args:
        timeout: Timeout for paste operation
        preferred_tool: Preferred tool ("auto", "osascript", "xdotool", "ydotool", "wtype")

    Returns:
        True if successful, False otherwise

    Raises:
        RuntimeError: If no paste tool is available
    """
    paster = create_autopaster(preferred_tool=preferred_tool, timeout=timeout)
    return paster.paste()
