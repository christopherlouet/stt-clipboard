# Changelog

All notable changes to this project are documented here.

For the full changelog, see [CHANGELOG.md](https://github.com/christopherlouet/stt-clipboard/blob/main/CHANGELOG.md).

## [1.3.0] - 2026-01-17

### Added

- **Text User Interface (TUI)** with Textual framework
  - Interactive terminal UI with status indicator, stats panel, and transcription log
  - Keyboard bindings: R (Record), C (Continuous), S (Stop), H (History), O (Settings), Q (Quit)
  - Settings editor with hot-reload and tabbed interface
  - Real-time statistics display (requests, success rate, RTF)
  - New `--tui` flag and `make tui` command

- **Global Installation** (`scripts/install_global.sh`)
  - Install `stt` and `stt-tui` commands system-wide
  - Config auto-copied to `~/.config/stt-clipboard/`

- **Continuous Dictation Mode**
  - New `--mode continuous` for uninterrupted dictation sessions
  - Each pause triggers clipboard copy

- **Transcription History with Persistence**
  - JSON file persistence with configurable location
  - View history in TUI with H key

- **Multi-Language Support**
  - Added German (DE), Spanish (ES), and Italian (IT)

- **Startup System Tools Validation**
  - Validates clipboard and paste tool availability at startup

## [1.2.0] - 2026-01-16

### Added

- **MkDocs Documentation** with Material theme
  - Full documentation site at [https://christopherlouet.github.io/stt-clipboard/](https://christopherlouet.github.io/stt-clipboard/)
  - Getting Started guide (installation, quickstart, configuration)
  - User Guide (basic usage, auto-paste, service management, troubleshooting)
  - Architecture documentation (overview, components)
  - Development guide (contributing, testing, security)
  - API Reference
- Documentation badge in README
- GitHub Actions workflow for automatic documentation deployment to GitHub Pages

### Changed

- Updated README with link to full documentation

## [1.1.0] - 2026-01-16

### Added

- **macOS Auto-Paste Support**: New `MacPaster` class using `osascript` for keyboard simulation
  - Simulates Cmd+V for standard paste
  - Simulates Cmd+Shift+V for terminal paste
  - Auto-detected on macOS systems

- **Multi-Distribution CI**: GitHub Actions now tests on:
  - Ubuntu (Debian-based)
  - Fedora (Red Hat-based)
  - Arch Linux

### Changed

- Updated `create_autopaster()` to detect and use `MacPaster` on macOS
- Improved auto-paster fallback logic across platforms

## [1.0.0] - 2025-01-15

### Added

- Initial release
- Offline speech-to-text using faster-whisper
- Voice Activity Detection with Silero VAD
- Bilingual support (French/English) with auto-detection
- Language-aware punctuation processing
- Universal clipboard support (Wayland, X11, macOS)
- Auto-paste functionality (xdotool, ydotool, wtype)
- Systemd service integration
- Comprehensive configuration via YAML

### Features

- **Privacy-First**: 100% offline processing
- **Low Latency**: ~7-8s total for recording + transcription
- **Multi-Platform**: Linux (Wayland/X11) and macOS support
- **Configurable**: Extensive options for audio, transcription, and behavior

---

See the [GitHub Releases](https://github.com/christopherlouet/stt-clipboard/releases) for detailed release notes.
