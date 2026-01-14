#!/bin/bash

# STT Clipboard - Systemd Service Installation Script

set -e

echo "========================================"
echo "STT Clipboard - Service Installation"
echo "========================================"
echo ""

# Get absolute path to project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Project directory: $PROJECT_DIR"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./scripts/install_deps.sh first"
    exit 1
fi

# Create systemd user directory
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

# Copy service file
echo "Installing systemd service..."
cp "$PROJECT_DIR/systemd/stt-clipboard.service" "$SYSTEMD_DIR/"

echo "✓ Service file installed to $SYSTEMD_DIR/stt-clipboard.service"

# Reload systemd
echo ""
echo "Reloading systemd..."
systemctl --user daemon-reload

echo "✓ Systemd reloaded"

# Enable service
echo ""
echo "Enabling service to start on login..."
systemctl --user enable stt-clipboard.service

echo "✓ Service enabled"

# Start service
echo ""
read -p "Start service now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl --user start stt-clipboard.service
    echo "✓ Service started"

    # Wait a moment for service to start
    sleep 2

    # Check status
    echo ""
    echo "Service status:"
    systemctl --user status stt-clipboard.service --no-pager
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Service commands:"
echo "  Start:   systemctl --user start stt-clipboard"
echo "  Stop:    systemctl --user stop stt-clipboard"
echo "  Restart: systemctl --user restart stt-clipboard"
echo "  Status:  systemctl --user status stt-clipboard"
echo "  Logs:    journalctl --user -u stt-clipboard -f"
echo ""
echo "Next step: Configure keyboard shortcut (see README.md)"
echo ""
