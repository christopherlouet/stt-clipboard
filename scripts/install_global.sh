#!/bin/bash

# STT Clipboard - Global Installation Script
# This script installs the STT Clipboard commands (stt, stt-tui) globally
# so they can be executed from any directory.
#
# Usage: ./scripts/install_global.sh
#
# After installation, you can run:
#   - stt-tui          : Launch the TUI interface
#   - stt              : Run the CLI (daemon/oneshot/continuous modes)
#   - stt --tui        : Alternative way to launch TUI
#
# Configuration:
#   The commands look for config in this order:
#   1. STT_CONFIG environment variable
#   2. ./config/config.yaml (current directory)
#   3. ~/.config/stt-clipboard/config.yaml

set -e  # Exit on error

echo "========================================"
echo "STT Clipboard - Global Installation"
echo "========================================"
echo ""

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install package in editable mode with uv
echo "[1/4] Installing package with uv (editable mode)..."
cd "$PROJECT_ROOT"
uv pip install -e .
echo "✓ Package installed in .venv"
echo ""

# Create symlinks in ~/.local/bin
echo "[2/4] Creating global symlinks..."
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

VENV_BIN="$PROJECT_ROOT/.venv/bin"

# Create symlinks for stt and stt-tui
if [ -f "$VENV_BIN/stt" ]; then
    ln -sf "$VENV_BIN/stt" "$LOCAL_BIN/stt"
    echo "✓ Created symlink: $LOCAL_BIN/stt -> $VENV_BIN/stt"
else
    echo "⚠ stt not found in $VENV_BIN"
fi

if [ -f "$VENV_BIN/stt-tui" ]; then
    ln -sf "$VENV_BIN/stt-tui" "$LOCAL_BIN/stt-tui"
    echo "✓ Created symlink: $LOCAL_BIN/stt-tui -> $VENV_BIN/stt-tui"
else
    echo "⚠ stt-tui not found in $VENV_BIN"
fi
echo ""

# Setup user config directory
echo "[3/4] Setting up user configuration..."
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
USER_CONFIG_DIR="$XDG_CONFIG_HOME/stt-clipboard"

if [ ! -d "$USER_CONFIG_DIR" ]; then
    mkdir -p "$USER_CONFIG_DIR"
    echo "✓ Created config directory: $USER_CONFIG_DIR"
fi

# Copy default config if not exists
if [ ! -f "$USER_CONFIG_DIR/config.yaml" ]; then
    if [ -f "$PROJECT_ROOT/config/config.yaml" ]; then
        cp "$PROJECT_ROOT/config/config.yaml" "$USER_CONFIG_DIR/config.yaml"

        # Update paths in user config to use absolute paths
        # Note: Using | as delimiter since paths contain /
        sed -i "s|download_root: ./models|download_root: $PROJECT_ROOT/models|g" "$USER_CONFIG_DIR/config.yaml"
        sed -i "s|file: ./logs/stt-clipboard.log|file: $USER_CONFIG_DIR/logs/stt-clipboard.log|g" "$USER_CONFIG_DIR/config.yaml"
        sed -i "s|file: ./data/history.json|file: $USER_CONFIG_DIR/data/history.json|g" "$USER_CONFIG_DIR/config.yaml"

        echo "✓ Copied default config to: $USER_CONFIG_DIR/config.yaml"
        echo "  (Paths updated for global usage)"
    else
        echo "⚠ No default config found. You'll need to create one manually."
    fi
else
    echo "✓ Config already exists: $USER_CONFIG_DIR/config.yaml"
fi

# Create logs and data directories
mkdir -p "$USER_CONFIG_DIR/logs"
mkdir -p "$USER_CONFIG_DIR/data"
echo ""

# Verify installation
echo "[4/4] Verifying installation..."

# Check if ~/.local/bin is in PATH
if command -v stt-tui &> /dev/null; then
    echo "✓ stt-tui command is available in PATH"
elif [ -f "$LOCAL_BIN/stt-tui" ]; then
    echo "✓ stt-tui installed at: $LOCAL_BIN/stt-tui"
    echo "  ⚠ $LOCAL_BIN is not in your PATH (see instructions below)"
fi

if command -v stt &> /dev/null; then
    echo "✓ stt command is available in PATH"
elif [ -f "$LOCAL_BIN/stt" ]; then
    echo "✓ stt installed at: $LOCAL_BIN/stt"
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Usage:"
echo "  stt-tui              Launch the TUI interface"
echo "  stt --mode daemon    Run in daemon mode"
echo "  stt --mode oneshot   Single transcription"
echo "  stt --help           Show all options"
echo ""
echo "Configuration:"
echo "  Edit: $USER_CONFIG_DIR/config.yaml"
echo ""
echo "If commands are not found, add the bin directory to your PATH:"
echo ""
echo "  # For bash:"
echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo ""
echo "  # For zsh:"
echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
echo "  source ~/.zshrc"
echo ""
