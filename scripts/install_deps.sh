#!/bin/bash

# STT Clipboard - Dependency Installation Script
# This script installs all necessary system and Python dependencies using uv
# Supports: Debian/Ubuntu (apt) and RHEL/Fedora/CentOS (dnf/yum)

set -e  # Exit on error

echo "========================================"
echo "STT Clipboard - Dependency Installation"
echo "========================================"
echo ""

# Detect package manager and distribution
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    DISTRO_TYPE="debian"
    echo "Detected: Debian/Ubuntu (apt)"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    DISTRO_TYPE="rhel"
    echo "Detected: RHEL/Fedora/Rocky Linux (dnf)"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    DISTRO_TYPE="rhel"
    echo "Detected: RHEL/CentOS (yum)"
else
    echo "Error: No supported package manager found (apt, dnf, or yum)"
    echo "This script supports Debian/Ubuntu and RHEL-based distributions"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

# Install system dependencies
echo ""
echo "Installing system dependencies..."
echo ""

if [ "$DISTRO_TYPE" = "debian" ]; then
    # Debian/Ubuntu packages
    sudo apt update
    sudo apt install -y \
        libportaudio2 \
        portaudio19-dev \
        python3-dev \
        build-essential \
        wl-clipboard \
        netcat-openbsd
elif [ "$DISTRO_TYPE" = "rhel" ]; then
    # RHEL/Fedora/CentOS packages
    sudo $PKG_MANAGER install -y \
        portaudio \
        portaudio-devel \
        python3-devel \
        gcc \
        gcc-c++ \
        make \
        wl-clipboard \
        nmap-ncat
fi

echo ""
echo "✓ System dependencies installed"

# Detect session type and install X11 support if needed
echo ""
echo "Detecting display server..."
SESSION_TYPE="${XDG_SESSION_TYPE:-unknown}"

if [ "$SESSION_TYPE" = "x11" ] || [ -n "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "X11 session detected, installing xclip for clipboard support..."
    if [ "$DISTRO_TYPE" = "debian" ]; then
        sudo apt install -y xclip
    else
        sudo $PKG_MANAGER install -y xclip
    fi
    echo "✓ X11 support (xclip) installed"
elif [ "$SESSION_TYPE" = "wayland" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "Wayland session detected, using wl-clipboard"
else
    echo "Session type unknown, installing both wl-clipboard and xclip for compatibility..."
    if [ "$DISTRO_TYPE" = "debian" ]; then
        sudo apt install -y xclip
    else
        sudo $PKG_MANAGER install -y xclip
    fi
    echo "✓ Both Wayland and X11 support installed"
fi

# Install auto-paste tools (optional)
echo ""
echo "Installing auto-paste tools (optional)..."

# For X11
if [ "$SESSION_TYPE" = "x11" ] || [ -n "$DISPLAY" ]; then
    echo "Installing xdotool for X11 auto-paste..."
    if [ "$DISTRO_TYPE" = "debian" ]; then
        sudo apt install -y xdotool
    else
        sudo $PKG_MANAGER install -y xdotool
    fi
    echo "✓ xdotool installed"
fi

# For Wayland
if [ "$SESSION_TYPE" = "wayland" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "Installing ydotool for Wayland auto-paste..."
    if [ "$DISTRO_TYPE" = "debian" ]; then
        sudo apt install -y ydotool
    else
        sudo $PKG_MANAGER install -y ydotool
    fi
    echo "✓ ydotool installed"
    echo ""
    echo "NOTE: The ydotoold daemon must be running for ydotool to work"
    echo "Enable with: sudo systemctl enable --now ydotool"
fi

# Check if uv is installed
echo ""
echo "Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✓ uv installed"
else
    echo "✓ uv is already installed"
fi

# Sync dependencies using uv
echo ""
echo "Installing Python dependencies with uv (this may take a few minutes)..."
uv sync

echo ""
echo "✓ Python dependencies installed"

# Pre-download Whisper model
echo ""
echo "Pre-downloading Whisper tiny model..."
echo "This will download approximately 75MB"
echo ""

uv run python3 << 'EOF'
from faster_whisper import WhisperModel
import os

# Create models directory
os.makedirs("./models", exist_ok=True)

# Download tiny model
print("Downloading Whisper tiny model...")
model = WhisperModel("tiny", device="cpu", compute_type="int8", download_root="./models")
print("✓ Model downloaded successfully")
EOF

echo ""
echo "✓ Whisper model downloaded"

# Create log directory
echo ""
echo "Creating log directory..."
mkdir -p logs
echo "✓ Log directory created"

# Test imports
echo ""
echo "Testing Python imports..."
uv run python3 -c "
import sounddevice
import torch
import numpy as np
from faster_whisper import WhisperModel
from loguru import logger
print('✓ All imports successful')
"

# Summary
echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Test one-shot mode: uv run python -m src.main --mode oneshot"
echo "  2. Configure hotkey (see README.md)"
echo "  3. Install systemd service: ./scripts/install_service.sh"
echo ""
echo "For more information, see README.md"
echo ""
