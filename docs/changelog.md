# Changelog

All notable changes to this project are documented here.

For the full changelog, see [CHANGELOG.md](https://github.com/christopherlouet/stt-clipboard/blob/main/CHANGELOG.md).

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
