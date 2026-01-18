# STT Clipboard

**Privacy-focused, offline bilingual (French/English) speech-to-text for Linux and macOS**

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/christopherlouet/stt-clipboard/releases/tag/v1.2.0)
[![CI](https://github.com/christopherlouet/stt-clipboard/actions/workflows/ci.yml/badge.svg)](https://github.com/christopherlouet/stt-clipboard/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)](https://github.com/christopherlouet/stt-clipboard)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **100% Offline**: All processing happens locally, zero network dependency
- **Bilingual Support**: Automatic language detection for French and English
- **Low Latency**: ~1-2s transcription time after speech ends
- **Privacy First**: No data leaves your machine
- **Universal Clipboard**: Works on Wayland, X11, and macOS
- **Auto-Paste**: Automatically paste transcribed text (optional)
- **Text User Interface**: Modern terminal UI with [Textual](https://github.com/Textualize/textual)
- **Transcription History**: Persistent storage of past transcriptions
- **Global Commands**: Install `stt` and `stt-tui` for system-wide access

## Quick Start

```bash
# Install dependencies
./scripts/install_deps.sh

# Launch the TUI (easiest way to start)
make tui

# Or test one-shot mode
uv run python -m src.main --mode oneshot

# Install as service for hotkey trigger
./scripts/install_service.sh

# Install global commands (stt, stt-tui)
./scripts/install_global.sh
```

## Platform Support

| Platform | Status | Clipboard | Auto-Paste |
|----------|--------|-----------|------------|
| **Ubuntu** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **Debian** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **Fedora** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **Arch Linux** | ✅ Tested | wl-copy/xclip | xdotool/ydotool |
| **macOS** | ✅ Tested | pbcopy/pbpaste | osascript (Cmd+V) |

## Performance

| Metric | Value |
|--------|-------|
| Transcription Time | ~0.8-1.2s for 5s audio |
| Total Latency | ~7-8s (includes silence detection) |
| Memory Usage | ~500MB during transcription |
| Accuracy | 5-8% WER for clean audio |

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Hotkey     │────▶│   Record     │────▶│  Transcribe  │
│   Trigger    │     │   Audio      │     │   (Whisper)  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Auto-Paste  │◀────│   Clipboard  │◀────│  Post-Process│
│  (optional)  │     │    Copy      │     │  Punctuation │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Documentation

- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [Configuration](getting-started/configuration.md)
- [Text User Interface](user-guide/tui.md)
- [Troubleshooting](user-guide/troubleshooting.md)

## License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0).
