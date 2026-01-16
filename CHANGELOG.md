# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 86% code coverage (339 tests)
- Tests for all major modules:
  - `test_main.py` - STTService, setup_logging, main() function
  - `test_transcription.py` - WhisperTranscriber, transcribe_with_timestamps
  - `test_clipboard.py` - Wayland/X11 managers, error handling
  - `test_hotkey.py` - TriggerServer/Client, socket handling
  - `test_config.py` - Configuration loading and validation
  - `test_notifications.py` - Desktop notification functions
  - `test_punctuation.py` - French/English punctuation rules
  - `test_audio_capture.py` - AudioRecorder with VAD
  - `test_autopaste.py` - Xdotool/Ydotool/Wtype pasters
- CI badges in README (CI status, coverage)
- Ruff linter badge

### Changed
- Improved test coverage from 33% to 86%
- Enhanced error handling in clipboard and hotkey modules

## [1.0.0] - 2025-01-14

### Added
- Initial release of STT Clipboard
- **Core Features**:
  - Offline speech-to-text using Whisper (faster-whisper) with base model
  - Voice activity detection with Silero VAD
  - ~1-2s transcription latency after speech ends
  - 92-95% accuracy for clean audio
  - ~500MB memory usage during transcription
  - CPU-optimized (int8 compute type)

- **Bilingual Support**:
  - Automatic language detection for French and English
  - Language-aware punctuation (French spacing rules, English rules)
  - Auto-detection adds ~100-200ms latency

- **Platform Support**:
  - Universal clipboard: Wayland (wl-clipboard) and X11 (xclip) with auto-detection
  - Multi-distribution: Debian/Ubuntu (apt) and RHEL/Fedora/CentOS (dnf/yum)
  - Auto-paste support: xdotool (X11), ydotool (universal), wtype (Wayland)

- **System Integration**:
  - Desktop notifications for recording status and clipboard updates
  - Systemd service for auto-start on login
  - Unix socket trigger system for hotkey integration
  - Configuration management (YAML)
  - Comprehensive logging with loguru

- **Developer Experience**:
  - Test suite with pytest
  - uv for fast dependency management
  - Pre-commit hooks (formatting, linting, security)
  - Security scanning (Bandit, Safety, detect-secrets)
  - Type checking (MyPy)
  - Code formatting (Black, isort, Ruff)
  - CI/CD with GitHub Actions

- **Documentation**:
  - README with installation and usage guide
  - Quick start guide (QUICKSTART.md)
  - Contributing guide (CONTRIBUTING.md)
  - Security policy (SECURITY.md)
  - Architecture documentation (ARCHITECTURE.md)

### Security
- 100% offline processing - no network dependency
- No data leaves your machine
- Audio processed in-memory only (never saved to disk)
- Unix socket secured with 0o600 permissions

## [0.1.0] - 2025-01-10

### Added
- Initial development version
- Basic speech-to-text functionality
- Whisper integration with faster-whisper
- Clipboard support (X11 only)
- Basic configuration system

### Changed
- Migrated from OpenAI Whisper to faster-whisper for better performance

---

[Unreleased]: https://github.com/christopherlouet/stt-clipboard/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/christopherlouet/stt-clipboard/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/christopherlouet/stt-clipboard/releases/tag/v0.1.0
