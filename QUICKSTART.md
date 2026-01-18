# Quick Start Guide

Get up and running with STT Clipboard in 5 minutes.

## Installation

### 1. Install Dependencies
```bash
./scripts/install_deps.sh
```

This will install:
- Auto-detect distribution: Debian/Ubuntu (apt) or RHEL/Fedora (dnf/yum)
- System dependencies (libportaudio, clipboard tools, etc.)
- Clipboard support: wl-clipboard (Wayland) and/or xclip (X11) - auto-detected
- uv (fast Python package manager)
- Python packages (faster-whisper, sounddevice, etc.)
- Whisper base model (~140MB)

**Supported distributions**: Debian, Ubuntu, RHEL, Fedora, CentOS, Rocky Linux, AlmaLinux

### 2. Test One-Shot Mode
```bash
uv run python -m src.main --mode oneshot
```

- Speak into your microphone (FR, EN, DE, ES, or IT)
- Wait 1.2s of silence
- Text appears in your clipboard
- Paste with Ctrl+V

### 3. Install Service
```bash
./scripts/install_service.sh
```

The service will start automatically on login.

### 4. Configure Keyboard Shortcut

**Ubuntu GNOME:**
1. Settings → Keyboard → Keyboard Shortcuts
2. Click "+" to add
3. Name: `STT Dictation`
4. Command: `<your-project-path>/scripts/trigger.sh`
5. Shortcut: Press your combo (e.g., Super+Shift+S)

**KDE Plasma:**
1. System Settings → Shortcuts → Custom Shortcuts
2. New → Global Shortcut → Command/URL
3. Command: `<your-project-path>/scripts/trigger.sh`
4. Assign shortcut (e.g., Meta+Shift+S)

## Daily Usage

### Three Usage Modes

**Copy-only mode** (e.g., Super+Shift+S):
1. Press shortcut → Speak → Pause 1.2s
2. Text copied to clipboard
3. Manually paste with Ctrl+V (editors) or Ctrl+Shift+V (terminals)

**Auto-paste mode** (e.g., Super+Shift+V):
1. Press shortcut → Speak → Pause 1.2s
2. Text automatically pasted with Ctrl+V (for standard applications)

**Terminal paste mode** (e.g., Super+Shift+T):
1. Press shortcut → Speak → Pause 1.2s
2. Text automatically pasted with Ctrl+Shift+V (for terminal applications)

**Language Detection:**
- Speak in French → French punctuation (space before ? ! : ;)
- Speak in English → English punctuation (no space before punctuation)
- Auto-detection adds ~100-200ms latency

## Useful Commands

```bash
# Start service
systemctl --user start stt-clipboard

# Stop service
systemctl --user stop stt-clipboard

# View real-time logs
journalctl --user -u stt-clipboard -f

# Test triggers manually
./scripts/trigger.sh                  # Copy-only mode
./scripts/trigger_paste.sh            # Auto-paste mode (Ctrl+V)
./scripts/trigger_paste_terminal.sh   # Terminal paste mode (Ctrl+Shift+V)

# Performance benchmark
uv run ./scripts/benchmark.py
```

## Quick Troubleshooting

### Shortcut doesn't work
```bash
# Check service is running
systemctl --user status stt-clipboard

# If stopped, start it
systemctl --user start stt-clipboard

# Test trigger manually
./scripts/trigger.sh
```

### Slow transcription
- Close CPU-intensive apps
- Check: `htop` during transcription
- Base model should take ~1-2s for 5s audio

### Poor accuracy
- Speak more clearly
- Reduce background noise
- Try "base" model (better than "tiny")

## Configuration

Edit `config/config.yaml`:

```yaml
audio:
  silence_duration: 1.2        # Silence time to stop recording

transcription:
  model_size: base             # base (accurate) or tiny (faster)
  language: ""                 # "" = auto-detect, or "fr", "en", "de", "es", "it"

punctuation:
  french_spacing: true         # Auto-apply French spacing for French text
```

After changes:
```bash
systemctl --user restart stt-clipboard
```

## Expected Performance

- **Latency**: ~1-2s after speech ends
- **Accuracy**: 92-95% for clean audio
- **Memory**: ~500MB during transcription
- **CPU**: 1 core at 100% for ~1s
- **Language detection**: +100-200ms with auto-detect

## Support

See `README.md` for complete documentation.
