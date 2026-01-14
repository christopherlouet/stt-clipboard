"""Clipboard integration for both Wayland and X11."""

import os
import shutil
import subprocess
from abc import ABC, abstractmethod

from loguru import logger


class BaseClipboardManager(ABC):
    """Base class for clipboard managers."""

    def __init__(self, timeout: float = 2.0):
        """Initialize clipboard manager.

        Args:
            timeout: Timeout in seconds for clipboard operations
        """
        self.timeout = timeout

    @abstractmethod
    def copy(self, text: str) -> bool:
        """Copy text to clipboard.

        Args:
            text: Text to copy

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def paste(self) -> str | None:
        """Get text from clipboard.

        Returns:
            Clipboard text or None if failed
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear the clipboard.

        Returns:
            True if successful, False otherwise
        """
        pass


class WaylandClipboardManager(BaseClipboardManager):
    """Clipboard manager for Wayland using wl-clipboard."""

    def __init__(self, timeout: float = 2.0):
        """Initialize Wayland clipboard manager.

        Args:
            timeout: Timeout in seconds for clipboard operations

        Raises:
            RuntimeError: If wl-clipboard is not available
        """
        super().__init__(timeout)
        if not shutil.which("wl-copy"):
            raise RuntimeError(
                "wl-copy not found. Please install wl-clipboard:\n  sudo apt install wl-clipboard"
            )
        logger.debug("Using Wayland clipboard (wl-clipboard)")

    def copy(self, text: str) -> bool:
        """Copy text to Wayland clipboard.

        Args:
            text: Text to copy to clipboard

        Returns:
            True if successful, False otherwise
        """
        if not text:
            logger.warning("Attempted to copy empty text to clipboard")
            return False

        try:
            # Use wl-copy without waiting for it to exit
            # wl-copy will fork to background and keep clipboard content available
            process = subprocess.Popen(
                ["wl-copy"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Send text to wl-copy
            process.stdin.write(text.encode("utf-8"))
            process.stdin.close()

            # Give it a moment to process
            import time

            time.sleep(0.1)

            # Check if process had any immediate errors
            if process.poll() is not None and process.returncode != 0:
                stderr = process.stderr.read().decode("utf-8", errors="ignore").strip()
                logger.error(f"wl-copy failed with code {process.returncode}: {stderr}")
                return False

            logger.info(f"Copied {len(text)} characters to clipboard (Wayland)")
            return True

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False

    def paste(self) -> str | None:
        """Get text from Wayland clipboard.

        Returns:
            Clipboard text or None if failed
        """
        try:
            result = subprocess.run(
                ["wl-paste"], capture_output=True, text=True, timeout=self.timeout, check=False
            )

            if result.returncode == 0:
                text = result.stdout
                logger.debug(f"Retrieved {len(text)} characters from clipboard")
                return text
            else:
                logger.error(f"wl-paste failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"wl-paste timed out after {self.timeout}s")
            return None

        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {e}")
            return None

    def clear(self) -> bool:
        """Clear the Wayland clipboard.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["wl-copy", "--clear"], capture_output=True, timeout=self.timeout, check=False
            )

            if result.returncode == 0:
                logger.debug("Clipboard cleared")
                return True
            else:
                logger.error(f"Failed to clear clipboard: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Failed to clear clipboard: {e}")
            return False


class X11ClipboardManager(BaseClipboardManager):
    """Clipboard manager for X11 using xclip or xsel."""

    def __init__(self, timeout: float = 2.0):
        """Initialize X11 clipboard manager.

        Args:
            timeout: Timeout in seconds for clipboard operations

        Raises:
            RuntimeError: If neither xclip nor xsel is available
        """
        super().__init__(timeout)

        # Check for xclip first (preferred), then xsel
        self.tool = None
        if shutil.which("xclip"):
            self.tool = "xclip"
        elif shutil.which("xsel"):
            self.tool = "xsel"
        else:
            raise RuntimeError(
                "Neither xclip nor xsel found. Please install one:\n"
                "  sudo apt install xclip\n"
                "  or\n"
                "  sudo apt install xsel"
            )

        logger.debug(f"Using X11 clipboard ({self.tool})")

    def copy(self, text: str) -> bool:
        """Copy text to X11 clipboard.

        Args:
            text: Text to copy to clipboard

        Returns:
            True if successful, False otherwise
        """
        if not text:
            logger.warning("Attempted to copy empty text to clipboard")
            return False

        try:
            if self.tool == "xclip":
                # xclip -selection clipboard
                cmd = ["xclip", "-selection", "clipboard"]
            else:  # xsel
                # xsel --clipboard --input
                cmd = ["xsel", "--clipboard", "--input"]

            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )

            if result.returncode == 0:
                logger.info(f"Copied {len(text)} characters to clipboard (X11)")
                return True
            else:
                stderr = result.stderr.decode("utf-8", errors="ignore").strip()
                logger.error(f"{self.tool} failed with code {result.returncode}: {stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"{self.tool} timed out after {self.timeout}s")
            return False

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False

    def paste(self) -> str | None:
        """Get text from X11 clipboard.

        Returns:
            Clipboard text or None if failed
        """
        try:
            if self.tool == "xclip":
                # xclip -selection clipboard -o
                cmd = ["xclip", "-selection", "clipboard", "-o"]
            else:  # xsel
                # xsel --clipboard --output
                cmd = ["xsel", "--clipboard", "--output"]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout, check=False
            )

            if result.returncode == 0:
                text = result.stdout
                logger.debug(f"Retrieved {len(text)} characters from clipboard")
                return text
            else:
                logger.error(f"{self.tool} paste failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"{self.tool} paste timed out after {self.timeout}s")
            return None

        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {e}")
            return None

    def clear(self) -> bool:
        """Clear the X11 clipboard.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear by copying empty string
            return self.copy("")

        except Exception as e:
            logger.error(f"Failed to clear clipboard: {e}")
            return False


def detect_session_type() -> str:
    """Detect if running under Wayland or X11.

    Returns:
        "wayland", "x11", or "unknown"
    """
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()

    if session_type in ["wayland", "x11"]:
        return session_type

    # Fallback detection
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    elif os.environ.get("DISPLAY"):
        return "x11"

    return "unknown"


def create_clipboard_manager(timeout: float = 2.0) -> BaseClipboardManager:
    """Create appropriate clipboard manager for the current session.

    Args:
        timeout: Timeout for clipboard operations

    Returns:
        ClipboardManager instance (Wayland or X11)

    Raises:
        RuntimeError: If session type cannot be determined or tools missing
    """
    session_type = detect_session_type()

    logger.info(f"Detected session type: {session_type}")

    if session_type == "wayland":
        return WaylandClipboardManager(timeout=timeout)
    elif session_type == "x11":
        return X11ClipboardManager(timeout=timeout)
    else:
        # Try both
        try:
            return WaylandClipboardManager(timeout=timeout)
        except RuntimeError:
            try:
                return X11ClipboardManager(timeout=timeout)
            except RuntimeError:
                raise RuntimeError(
                    "Could not initialize clipboard manager.\n"
                    "Please install wl-clipboard (Wayland) or xclip/xsel (X11):\n"
                    "  sudo apt install wl-clipboard xclip"
                )


# Backward compatibility - keep old class name
class ClipboardManager(BaseClipboardManager):
    """Clipboard manager that auto-detects Wayland or X11.

    This is a wrapper that creates the appropriate manager for the current session.
    """

    def __init__(self, timeout: float = 2.0):
        """Initialize clipboard manager (auto-detect session type).

        Args:
            timeout: Timeout in seconds for clipboard operations
        """
        super().__init__(timeout)
        self._manager = create_clipboard_manager(timeout)

    def copy(self, text: str) -> bool:
        """Copy text to clipboard."""
        return self._manager.copy(text)

    def paste(self) -> str | None:
        """Get text from clipboard."""
        return self._manager.paste()

    def clear(self) -> bool:
        """Clear clipboard."""
        return self._manager.clear()

    def copy_with_retry(self, text: str, retries: int = 1) -> bool:
        """Copy text to clipboard with retry logic.

        Args:
            text: Text to copy
            retries: Number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(retries + 1):
            if self.copy(text):
                return True

            if attempt < retries:
                logger.warning(f"Clipboard copy failed, retrying ({attempt + 1}/{retries})...")

        logger.error(f"Failed to copy to clipboard after {retries + 1} attempts")
        return False


# Convenience functions
_default_manager: ClipboardManager | None = None


def get_clipboard_manager(timeout: float = 2.0) -> ClipboardManager:
    """Get or create the default clipboard manager singleton.

    Args:
        timeout: Timeout for clipboard operations

    Returns:
        ClipboardManager instance
    """
    global _default_manager

    if _default_manager is None:
        _default_manager = ClipboardManager(timeout=timeout)

    return _default_manager


def copy_to_clipboard(text: str, timeout: float = 2.0, retries: int = 1) -> bool:
    """Copy text to clipboard (convenience function).

    Args:
        text: Text to copy
        timeout: Operation timeout
        retries: Number of retry attempts

    Returns:
        True if successful, False otherwise
    """
    manager = get_clipboard_manager(timeout=timeout)
    return manager.copy_with_retry(text, retries=retries)


def paste_from_clipboard(timeout: float = 2.0) -> str | None:
    """Get text from clipboard (convenience function).

    Args:
        timeout: Operation timeout

    Returns:
        Clipboard text or None if failed
    """
    manager = get_clipboard_manager(timeout=timeout)
    return manager.paste()


def clear_clipboard(timeout: float = 2.0) -> bool:
    """Clear clipboard (convenience function).

    Args:
        timeout: Operation timeout

    Returns:
        True if successful, False otherwise
    """
    manager = get_clipboard_manager(timeout=timeout)
    return manager.clear()


# Example usage and testing
if __name__ == "__main__":
    import sys

    # Test clipboard operations
    print("Testing Clipboard Integration (Wayland + X11)")
    print("=" * 60)

    # Detect session
    session = detect_session_type()
    print(f"Session type: {session}")
    print()

    # Test copy
    test_text = "Bonjour ! Ceci est un test de dictée vocale."
    print(f"Copying: {test_text}")

    if copy_to_clipboard(test_text):
        print("✓ Copy successful")
    else:
        print("✗ Copy failed")
        sys.exit(1)

    # Test paste
    print("\nRetrieving from clipboard...")
    pasted = paste_from_clipboard()

    if pasted:
        print(f"✓ Paste successful: {pasted}")

        if pasted == test_text:
            print("✓ Text matches!")
        else:
            print("✗ Text mismatch!")
    else:
        print("✗ Paste failed")

    print("\nTest complete!")
