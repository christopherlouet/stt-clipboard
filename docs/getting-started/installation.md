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

## Global Installation

Install `stt` and `stt-tui` commands for system-wide access:

```bash
./scripts/install_global.sh
```

This will:

1. Install the package in editable mode with uv
2. Create symlinks in `~/.local/bin`
3. Copy default config to `~/.config/stt-clipboard/`
4. Create logs and data directories

After installation, you can run from anywhere:

```bash
stt-tui              # Launch TUI interface
stt --mode daemon    # Run in daemon mode
stt --mode oneshot   # Single transcription
stt --help           # Show all options
```

!!! note "PATH Configuration"
    If commands are not found, add `~/.local/bin` to your PATH:

    === "Bash"
        ```bash
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc
        ```

    === "Zsh"
        ```bash
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        source ~/.zshrc
        ```

### Configuration Location

For global installation, config is searched in this order:

1. `STT_CONFIG` environment variable
2. `./config/config.yaml` (current directory)
3. `~/.config/stt-clipboard/config.yaml` (user config)

Override with environment variable:

```bash
STT_CONFIG=/path/to/config.yaml stt-tui
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration](configuration.md)
- [Text User Interface](../user-guide/tui.md)
