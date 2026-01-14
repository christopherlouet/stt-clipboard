#!/bin/bash

# STT Clipboard - Trigger Script (Copy + Paste Mode)
# This script sends a TRIGGER_PASTE event to copy and auto-paste
# Configure this as your desktop keyboard shortcut command for auto-paste

SOCKET_PATH="/tmp/stt-clipboard.sock"

# Check if socket exists
if [ ! -S "$SOCKET_PATH" ]; then
    # Try to show notification if notify-send available
    if command -v notify-send &> /dev/null; then
        notify-send "STT Error" "Service not running. Start with: systemctl --user start stt-clipboard"
    fi
    echo "Error: Socket not found at $SOCKET_PATH"
    echo "Is the STT service running?"
    echo "Start with: systemctl --user start stt-clipboard"
    exit 1
fi

# Send TRIGGER_PASTE
if echo "TRIGGER_PASTE" | nc -U -w 2 "$SOCKET_PATH" > /dev/null 2>&1; then
    echo "Paste trigger sent successfully"
    exit 0
else
    if command -v notify-send &> /dev/null; then
        notify-send "STT Error" "Failed to send trigger"
    fi
    echo "Error: Failed to send trigger"
    exit 1
fi
