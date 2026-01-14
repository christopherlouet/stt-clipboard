# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-14

### Added
- Initial release of STT Clipboard
- **Bilingual support**: Automatic language detection for French and English
- **Language-aware punctuation**: French spacing rules for French text, English rules for English text
- **Universal clipboard support**: Works on both Wayland (wl-clipboard) and X11 (xclip) with auto-detection
- **Multi-distribution support**: Debian/Ubuntu (apt) and RHEL/Fedora/CentOS (dnf/yum) with auto-detection
- Offline speech-to-text using Whisper (faster-whisper) with base model
- Voice activity detection with Silero VAD
- Desktop notifications for recording status and clipboard updates
- Systemd service for auto-start on login
- Unix socket trigger system for hotkey integration
- Configuration management (YAML)
- Comprehensive logging with loguru
- Test suite with pytest
- Development tooling:
  - uv for fast dependency management
  - Pre-commit hooks (formatting, linting, security)
  - Security scanning (Bandit, Safety, detect-secrets, Gitleaks)
  - Type checking (MyPy)
  - Code formatting (Black, isort, Ruff)
- Documentation:
  - README with installation and usage guide
  - Quick start guide
  - CONTRIBUTING guide for developers
  - SECURITY policy
  - Architecture documentation
- CI/CD with GitHub Actions
- GPLv3 license

### Features
- ~1-2s transcription latency after speech ends
- Auto-detection adds ~100-200ms latency but applies correct punctuation rules
- 92-95% accuracy for clean audio
- ~500MB memory usage during transcription
- CPU-optimized (int8 compute type)
