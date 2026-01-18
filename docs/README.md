# Documentation

This directory contains additional documentation for STT Clipboard.

## Table of Contents

- [Project Documentation](#project-documentation)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Running Security Scans](#running-security-scans)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Project Documentation

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Main documentation and user guide |
| [QUICKSTART.md](../QUICKSTART.md) | Quick start guide (5 minutes) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Development and contribution guidelines |
| [SECURITY.md](../SECURITY.md) | Security policy and vulnerability reporting |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Technical architecture documentation |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and release notes |
| [tests/README.md](../tests/README.md) | Testing documentation |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        STT Clipboard                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────────┐    ┌──────────────┐            │
│  │ Hotkey  │───▶│   Audio     │───▶│ Transcription│            │
│  │ Trigger │    │  Capture    │    │  (Whisper)   │            │
│  └─────────┘    │  + VAD      │    └──────┬───────┘            │
│                 └─────────────┘           │                     │
│                                           ▼                     │
│  ┌─────────┐    ┌─────────────┐    ┌──────────────┐            │
│  │  Paste  │◀───│  Clipboard  │◀───│ Punctuation  │            │
│  │ (opt.)  │    │  (wl/xclip) │    │  Processor   │            │
│  └─────────┘    └─────────────┘    └──────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration

The configuration file is located at `config/config.yaml`:

```yaml
# Audio settings
audio:
  silence_duration: 1.2      # Seconds of silence to stop recording
  max_recording_duration: 30 # Maximum recording length
  min_speech_duration: 0.3   # Minimum speech to avoid false starts

# Transcription settings
transcription:
  model_size: base           # tiny, base, small, medium
  language: ""               # Empty for auto-detect, or "fr"/"en"
  compute_type: int8         # Quantization level
  beam_size: 5               # Higher = more accurate but slower

# Auto-paste settings (optional)
paste:
  enabled: true
  preferred_tool: auto       # auto, xdotool, ydotool, wtype
```

## Running Security Scans

```bash
# Run all security checks
make security

# Individual scans
uv run bandit -c pyproject.toml -r src/    # Code vulnerabilities
uv run safety scan                          # Dependency CVEs
uv run detect-secrets scan                  # Secrets detection

# Pre-commit (runs all checks)
uv run pre-commit run --all-files
```

## Testing

See [tests/README.md](../tests/README.md) for detailed testing documentation.

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
uv run pytest tests/test_main.py -v

# Run tests matching a pattern
uv run pytest -k "test_transcribe" -v
```

### Current Coverage

| Module | Coverage |
|--------|----------|
| config.py | 100% |
| notifications.py | 100% |
| main.py | 96% |
| clipboard.py | 88% |
| autopaste.py | 86% |
| punctuation.py | 86% |
| audio_capture.py | 79% |
| hotkey.py | 79% |
| transcription.py | 71% |
| **Total** | **86%** |

## Troubleshooting

### Service won't start

```bash
# Check service status
systemctl --user status stt-clipboard

# View logs
journalctl --user -u stt-clipboard -n 50

# Check socket
ls -la /tmp/stt-clipboard.sock
```

### Slow transcription

- Check CPU governor: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor`
- Close heavy applications
- Try `tiny` model instead of `base` for faster (but less accurate) results

### Poor accuracy

- Reduce background noise
- Speak clearly and at moderate pace
- Try `base` or `small` model for better accuracy
- Check microphone levels with `alsamixer` or `pavucontrol`

### Clipboard fails

```bash
# Wayland - check wl-copy
which wl-copy
wl-copy "test"
wl-paste

# X11 - check xclip
which xclip
echo "test" | xclip -selection clipboard
xclip -selection clipboard -o
```

### Socket errors

```bash
# Remove stale socket
rm -f /tmp/stt-clipboard.sock

# Restart service
systemctl --user restart stt-clipboard
```

## FAQ

### Q: Does it work offline?
**A:** Yes, 100% offline. Models are downloaded once during setup, then all processing is local.

### Q: What languages are supported?
**A:** French, English, German, Spanish, and Italian with automatic detection. Punctuation is adapted per language.

### Q: How much disk space is needed?
**A:** ~2GB for models and dependencies.

### Q: Can I use a different Whisper model?
**A:** Yes, change `model_size` in config.yaml. Options: `tiny` (fast), `base` (balanced), `small`, `medium` (accurate).

### Q: Does it work on both Wayland and X11?
**A:** Yes, the clipboard and paste tools are auto-detected based on your session type.

### Q: How do I trigger transcription?
**A:** Configure a hotkey in your desktop environment to run `./scripts/trigger.sh` (copy only) or `./scripts/trigger_paste.sh` (copy + paste).

### Q: Is my audio saved anywhere?
**A:** No, audio is processed in memory only and never saved to disk.

---

For more information, see the [main README](../README.md) or open an issue on GitHub.
