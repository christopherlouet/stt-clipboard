# STT Clipboard - Offline Speech-to-Text (Multilingual)

[![Version](https://img.shields.io/badge/version-1.4.2-blue.svg)](https://github.com/christopherlouet/stt-clipboard/releases/tag/v1.4.2)
[![CI](https://github.com/christopherlouet/stt-clipboard/actions/workflows/ci.yml/badge.svg)](https://github.com/christopherlouet/stt-clipboard/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://christopherlouet.github.io/stt-clipboard/)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)](https://github.com/christopherlouet/stt-clipboard)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Professional-grade, privacy-focused speech-to-text system with multilingual support (FR, EN, DE, ES, IT) for Linux and macOS.

## Table of Contents

- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Text User Interface](#text-user-interface-tui)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Documentation](#documentation)

## Quick Start

```bash
# 1. Install dependencies
./scripts/install_deps.sh

# 2. Install global commands (stt, stt-tui)
./scripts/install_global.sh

# 3. Launch the TUI
stt-tui
```

> **Note**: If `stt-tui` is not found, add `~/.local/bin` to your PATH:
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
> ```

## Usage Examples

### Quick Dictation (Email, Document)

```bash
# Single transcription → text copied to clipboard → paste with Ctrl+V
stt --mode oneshot
```

### Continuous Note-Taking

```bash
# Continuous dictation - each pause transcribes and copies
stt --mode continuous
```

### Interactive TUI

```bash
# Full interface with history, settings, and stats
stt-tui
```

### Background Service (Hotkey Trigger)

```bash
# Install service for hotkey-triggered transcription
./scripts/install_service.sh

# Configure a hotkey to run: /path/to/scripts/trigger.sh
# Press hotkey → Speak → Pause → Text appears in clipboard
```

## Text User Interface (TUI) - Multilingual

```
┌───────────────────────────────────────────────────────────────┐
│ STT Clipboard                                        [READY]  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Transcription Log                                            │
│  ─────────────────                                            │
│  [14:30:45] Bonjour, comment allez-vous ?                     │
│  [14:31:02] Hello, this is a test transcription.              │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  [R]ecord  [C]ontinuous  [S]top  [H]istory  [O]ptions  [Q]uit │
├───────────────────────────────────────────────────────────────┤
│  Total: 2 | Success: 2 | Failed: 0 | Audio: 8.5s | RTF: 0.25  │
└───────────────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `R` | Record | Start single recording |
| `C` | Continuous | Start continuous dictation |
| `S` | Stop | Stop current recording |
| `H` | History | View past transcriptions |
| `O` | Options | Open settings editor |
| `Q` | Quit | Exit application |

### Settings Editor

Press `O` to modify settings without editing YAML files:
- **Audio**: Sample rate, silence duration, max recording length
- **Transcription**: Model size, language, compute type
- **Output**: Clipboard, auto-paste, punctuation rules
- **System**: Logging level, history settings

Settings requiring restart are marked with `[*]`.

## Features

- **100% Offline**: All processing happens locally, zero network dependency
- **Multilingual**: French, English, German, Spanish, Italian with smart punctuation
- **Low Latency**: ~1-2s transcription time after speech ends
- **Privacy First**: Audio processed in-memory only, never saved
- **Universal Clipboard**: Wayland (wl-copy), X11 (xclip), macOS (pbcopy)
- **Text User Interface**: Modern terminal UI with settings management
- **Global Commands**: `stt` and `stt-tui` available system-wide
- **Transcription History**: Persistent storage with search
- **Auto-Paste**: Optional automatic paste after transcription

### Performance

| Metric | Value |
|--------|-------|
| Transcription Time | ~0.8-1.2s for 5s audio |
| Total Latency | ~7-8s (includes silence detection) |
| Memory Usage | ~500MB during transcription |
| Accuracy | 5-8% WER for clean audio |

### Supported Platforms

| Platform | Status | Clipboard | Auto-Paste |
|----------|--------|-----------|------------|
| **Ubuntu/Debian** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **Fedora/RHEL** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **Arch Linux** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **macOS 12+** | ✅ Tested | pbcopy | osascript |

## Installation

### Step 1: Install Dependencies

```bash
./scripts/install_deps.sh
```

Auto-detects your platform and installs all required packages.

### Step 2: Install Global Commands

```bash
./scripts/install_global.sh
```

Installs `stt` and `stt-tui` in `~/.local/bin` and copies config to `~/.config/stt-clipboard/`.

**Add to PATH** (if needed):

```bash
# Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### Step 3: Verify Installation

```bash
stt-tui  # or: stt --mode oneshot
```

### Step 4: Systemd Service (Optional)

For hotkey-triggered transcription:

```bash
./scripts/install_service.sh
```

Then configure a keyboard shortcut to run `/path/to/scripts/trigger.sh`.

## Configuration

**Location**: `~/.config/stt-clipboard/config.yaml` (or `config/config.yaml` locally)

### Key Settings

```yaml
audio:
  silence_duration: 1.2    # Seconds of silence to stop recording
  max_recording_duration: 30

transcription:
  model_size: base         # tiny, base, small, medium
  language: ""             # "" = auto-detect, "fr", "en"

paste:
  enabled: false           # Auto-paste after transcription
  preferred_tool: auto     # auto, xdotool, ydotool, wtype, osascript
```

After changes: `systemctl --user restart stt-clipboard` (if using service)

For detailed configuration options, see the [full documentation](https://christopherlouet.github.io/stt-clipboard/getting-started/configuration/).

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `stt-tui` not found | Add `~/.local/bin` to PATH |
| Service won't start | Check logs: `journalctl --user -u stt-clipboard -n 50` |
| No audio input | Test: `uv run python -m src.audio_capture` |
| Clipboard fails | Check session: `echo $XDG_SESSION_TYPE` |

### Quick Diagnostics

```bash
# Test trigger manually
./scripts/trigger.sh

# Check service status
systemctl --user status stt-clipboard

# View logs
journalctl --user -u stt-clipboard -f
```

For detailed troubleshooting, see the [documentation](https://christopherlouet.github.io/stt-clipboard/user-guide/troubleshooting/).

## Development

### Quick Setup

```bash
./scripts/setup_dev.sh   # Install dev dependencies + pre-commit hooks
make test                 # Run tests
make lint                 # Run linters
make tui                  # Launch TUI
```

### Makefile Commands

```bash
make help           # Show all commands
make install-dev    # Setup dev environment
make install-global # Install stt/stt-tui globally
make test-cov       # Tests with coverage
make format         # Format code (black, isort)
make security       # Security scans (bandit, safety)
```

For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

**Full documentation**: [https://christopherlouet.github.io/stt-clipboard/](https://christopherlouet.github.io/stt-clipboard/)

- [Installation Guide](https://christopherlouet.github.io/stt-clipboard/getting-started/installation/)
- [TUI Guide](https://christopherlouet.github.io/stt-clipboard/user-guide/tui/)
- [Configuration](https://christopherlouet.github.io/stt-clipboard/getting-started/configuration/)
- [Auto-Paste Setup](https://christopherlouet.github.io/stt-clipboard/user-guide/auto-paste/)
- [Architecture](https://christopherlouet.github.io/stt-clipboard/architecture/overview/)

## Privacy & Security

- **100% Offline**: No network after initial model download
- **No Audio Storage**: Processed in-memory only
- **Open Source**: Full code inspection available
- **Security Scanning**: Automated via pre-commit hooks

## Credits

Built with [faster-whisper](https://github.com/guillaumekln/faster-whisper), [Silero VAD](https://github.com/snakers4/silero-vad), [Textual](https://github.com/Textualize/textual), and [sounddevice](https://python-sounddevice.readthedocs.io/).

## License

[GNU General Public License v3.0](LICENSE)

---

**Made with care for the privacy-conscious multilingual community**
