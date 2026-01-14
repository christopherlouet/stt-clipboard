#!/bin/bash

# STT Clipboard - Trigger Script
# This script sends a trigger event to the STT service
# Configure this as your desktop keyboard shortcut command

SOCKET_PATH="/tmp/stt-clipboard.sock"

# Accept trigger type as parameter (default: TRIGGER_COPY for backward compatibility)
TRIGGER_TYPE="${1:-TRIGGER_COPY}"

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

# Send trigger
if echo "$TRIGGER_TYPE" | nc -U -w 2 "$SOCKET_PATH" > /dev/null 2>&1; then
    echo "Trigger sent successfully"
    exit 0
else
    if command -v notify-send &> /dev/null; then
        notify-send "STT Error" "Failed to send trigger"
    fi
    echo "Error: Failed to send trigger"
    exit 1
fi
