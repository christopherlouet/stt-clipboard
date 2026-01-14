"""Desktop notifications for STT Clipboard."""

import subprocess

from loguru import logger


def send_notification(title: str, message: str, urgency: str = "normal") -> bool:
    """Send a desktop notification using notify-send.

    Args:
        title: Notification title
        message: Notification message
        urgency: Urgency level (low, normal, critical)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, message],
            check=True,
            capture_output=True,
            timeout=2.0,
        )
        logger.debug(f"Notification sent: {title} - {message}")
        return True

    except FileNotFoundError:
        logger.debug("notify-send not available")
        return False

    except subprocess.TimeoutExpired:
        logger.warning("Notification timeout")
        return False

    except Exception as e:
        logger.debug(f"Failed to send notification: {e}")
        return False


def notify_recording_started() -> bool:
    """Notify user that recording has started.

    Returns:
        True if notification was sent successfully
    """
    return send_notification(
        "STT Clipboard", "Enregistrement en cours... Parlez maintenant", urgency="normal"
    )


def notify_text_copied(text: str) -> bool:
    """Notify user that text has been copied to clipboard.

    Args:
        text: The text that was copied

    Returns:
        True if notification was sent successfully
    """
    # Truncate text if too long for notification
    display_text = text if len(text) <= 100 else f"{text[:100]}..."

    return send_notification(
        "STT Clipboard", f"Texte copié dans le presse-papiers:\n{display_text}", urgency="normal"
    )
