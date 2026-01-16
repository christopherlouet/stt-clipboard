# Installation

## Requirements

- **Python**: 3.10 or higher
- **Operating System**: Linux (Debian, Ubuntu, Arch, Fedora, RHEL) or macOS 12+
- **Disk Space**: ~2GB (models + dependencies)
- **Microphone**: Working audio input device

## Automatic Installation

The installation script automatically detects your platform:

```bash
./scripts/install_deps.sh
```

This will:

1. Detect your platform (macOS, Debian/Ubuntu, Arch Linux, RHEL/Fedora)
2. Install system packages (portaudio, clipboard tools)
3. Install uv (fast Python package manager)
4. Install Python dependencies
5. Download Whisper model (~140MB)

## Manual Installation

### Linux (Debian/Ubuntu)

```bash
# System dependencies
sudo apt update
sudo apt install -y libportaudio2 portaudio19-dev python3-dev build-essential

# Clipboard (Wayland)
sudo apt install -y wl-clipboard

# Clipboard (X11)
sudo apt install -y xclip

# Auto-paste tools
sudo apt install -y xdotool ydotool
```

### Linux (Arch Linux)

```bash
# System dependencies
sudo pacman -Syu --noconfirm portaudio python python-pip base-devel

# Clipboard and auto-paste
sudo pacman -S --noconfirm wl-clipboard xclip xdotool ydotool
```

### Linux (Fedora/RHEL)

```bash
# System dependencies
sudo dnf install -y portaudio portaudio-devel python3-devel gcc gcc-c++ make

# Clipboard and auto-paste
sudo dnf install -y wl-clipboard xclip xdotool ydotool
```

### macOS

```bash
# Using Homebrew
brew install portaudio python@3.12
```

!!! note "macOS Auto-Paste"
    Auto-paste on macOS requires Accessibility permissions.
    Go to **System Settings → Privacy & Security → Accessibility** and enable access for your terminal.

### Python Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

## Verify Installation

```bash
# Test imports
uv run python -c "
import sounddevice
import torch
from faster_whisper import WhisperModel
print('All imports successful!')
"

# Test one-shot mode
uv run python -m src.main --mode oneshot
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration](configuration.md)
