# STT Clipboard - Offline Speech-to-Text (French/English)

[![CI](https://github.com/christopherlouet/stt-clipboard/actions/workflows/ci.yml/badge.svg)](https://github.com/christopherlouet/stt-clipboard/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)](https://github.com/christopherlouet/stt-clipboard)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Professional-grade, privacy-focused speech-to-text system with bilingual support (French/English) for Linux. Works on both Wayland and X11. Supports Debian/Ubuntu and RHEL-based distributions.

## Features

- **100% Offline**: All processing happens locally, zero network dependency
- **Bilingual Support**: Automatic language detection for French and English with smart punctuation
- **Low Latency**: ~1-2s transcription time after speech ends
- **Privacy First**: No data leaves your machine
- **Universal Clipboard**: Works on both Wayland (wl-clipboard) and X11 (xclip)
- **Auto-Start**: Systemd service starts on login
- **Simple Workflow**: Press hotkey → Speak → Pause → Text in clipboard

## Performance

- **Transcription Time**: ~0.8-1.2s for 5s of audio
- **Total Latency**: ~7-8s (includes 1.2s silence detection)
- **Memory Usage**: ~500MB during transcription
- **CPU**: Single core at 100% for ~1s during transcription
- **Accuracy**: 5-8% WER (Word Error Rate) for clean French audio

## Requirements

- **Linux Distribution** (auto-detected):
  - Debian/Ubuntu (tested on Ubuntu 25)
  - RHEL/Fedora/CentOS/Rocky Linux/AlmaLinux
- Python 3.10+
- Wayland or X11 session (auto-detected)
- Working microphone
- ~2GB free disk space (models + dependencies)

### Supported Distributions

The installation script automatically detects your distribution and uses the appropriate package manager:

| Distribution | Package Manager | Status |
|--------------|-----------------|--------|
| Debian/Ubuntu | apt | ✅ Tested |
| Fedora | dnf | ✅ Supported |
| RHEL 8/9 | dnf | ✅ Supported |
| CentOS Stream | dnf | ✅ Supported |
| Rocky Linux | dnf | ✅ Supported |
| AlmaLinux | dnf | ✅ Supported |
| CentOS 7 | yum | ✅ Supported |

## Quick Start

### 1. Install Dependencies

```bash
./scripts/install_deps.sh
```

This will:
- Auto-detect your distribution (Debian/Ubuntu or RHEL/Fedora)
- Install system packages (libportaudio, wl-clipboard, etc.)
- Auto-detect display server (Wayland/X11) and install clipboard tools
- Install uv (fast Python package manager)
- Install Python dependencies using uv
- Download Whisper base model (~140MB)

### 2. Test One-Shot Mode

```bash
uv run python -m src.main --mode oneshot
```

Speak into your microphone, pause for 1.2s, and the text should appear in your clipboard.

### 3. Install Systemd Service

```bash
./scripts/install_service.sh
```

This installs and enables the service to start automatically on login.

### 4. Configure Keyboard Shortcut

#### Ubuntu GNOME:

1. Open **Settings** → **Keyboard** → **Keyboard Shortcuts**
2. Scroll to bottom and click **"+"** to add custom shortcut
3. Set:
   - **Name**: STT Dictation
   - **Command**: `/path/to/stt-clipboard/scripts/trigger.sh`
   - **Shortcut**: Press your desired key combo (e.g., **Super+Shift+S**)

#### KDE Plasma:

1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts**
2. Right-click → **New** → **Global Shortcut** → **Command/URL**
3. Set command to: `/path/to/stt-clipboard/scripts/trigger.sh`
4. Assign hotkey (e.g., **Meta+Shift+S**)

### 5. Usage

1. Press your configured hotkey
2. Speak (you'll see log output if running in terminal)
3. Pause for 1.2 seconds
4. Text is automatically copied to clipboard
5. Paste anywhere with **Ctrl+V** (editors) or **Ctrl+Shift+V** (terminals)

## Auto-Paste Mode (Optional)

In addition to copying text to clipboard, STT Clipboard can automatically paste transcribed text into the active application.

### Setup Auto-Paste

1. **Install paste tools** (already included in `install_deps.sh`):
   - **X11**: xdotool (automatically installed)
   - **Wayland**: ydotool (requires enabling daemon)

2. **Enable ydotool daemon** (Wayland only):
   ```bash
   sudo systemctl enable --now ydotool
   ```

3. **Configure keyboard shortcuts**:

   **For standard applications (Ctrl+V paste):**
   - **Name**: STT Dictation (Auto-Paste)
   - **Command**: `/path/to/scripts/trigger_paste.sh`
   - **Shortcut**: e.g., **Super+Shift+V**

   **For terminals (Ctrl+Shift+V paste):**
   - **Name**: STT Dictation (Terminal)
   - **Command**: `/path/to/scripts/trigger_paste_terminal.sh`
   - **Shortcut**: e.g., **Super+Shift+T**

### Usage Modes

STT Clipboard supports three trigger modes:

- **Copy Only** (e.g., Super+Shift+S): Text copied to clipboard, manual paste with Ctrl+V
- **Copy + Auto-Paste** (e.g., Super+Shift+V): Text automatically pasted with Ctrl+V (for standard applications)
- **Copy + Terminal Paste** (e.g., Super+Shift+T): Text automatically pasted with Ctrl+Shift+V (for terminal applications)

### Configuration

Edit `config/config.yaml`:

```yaml
paste:
  enabled: true          # Enable/disable auto-paste
  timeout: 2.0          # Paste operation timeout
  delay_ms: 100         # Delay between copy and paste
  preferred_tool: auto  # "auto", "xdotool", "ydotool", "wtype"
```

After changes: `systemctl --user restart stt-clipboard`

## Configuration

Edit `config/config.yaml` to customize:

```yaml
audio:
  silence_duration: 1.2        # Silence threshold to stop recording
  max_recording_duration: 30   # Maximum recording length

transcription:
  model_size: base             # tiny (fast) or base (more accurate)
  language: ""                 # "" = auto-detect FR/EN, "fr" = French only, "en" = English only

punctuation:
  french_spacing: true         # Auto-apply French spacing when French is detected
```

After changing config, restart the service:
```bash
systemctl --user restart stt-clipboard
```

## Service Management

### Start/Stop Service

```bash
# Start
systemctl --user start stt-clipboard

# Stop
systemctl --user stop stt-clipboard

# Restart
systemctl --user restart stt-clipboard

# Status
systemctl --user status stt-clipboard
```

### View Logs

```bash
# Real-time logs
journalctl --user -u stt-clipboard -f

# Recent logs
journalctl --user -u stt-clipboard -n 50

# File logs
tail -f logs/stt-clipboard.log
```

### Disable Auto-Start

```bash
systemctl --user disable stt-clipboard
```

## Benchmarking

Test transcription performance:

```bash
uv run ./scripts/benchmark.py --iterations 10
```

Expected results (Intel i5/Ryzen 5 or better):
- **RTF** (Real-Time Factor): 0.2-0.3x (transcription faster than real-time)
- **Mean time**: ~0.8-1.2s for 5s audio

## Troubleshooting

### Service won't start

```bash
# Check status
systemctl --user status stt-clipboard

# Check logs
journalctl --user -u stt-clipboard -n 50

# Common issues:
# 1. Dependencies not installed: run ./scripts/install_deps.sh
# 2. uv not found: script will auto-install it
# 3. Permissions: ensure scripts are executable (chmod +x scripts/*.sh)
# 4. RHEL/CentOS: Ensure Python 3.10+ is installed (may need EPEL or python39)
```

### Hotkey doesn't work

```bash
# Test trigger manually
./scripts/trigger.sh

# If "Socket not found":
systemctl --user start stt-clipboard

# If "Failed to send trigger":
# Check logs: journalctl --user -u stt-clipboard -f
```

### No microphone input

```bash
# List available devices
uv run python -c "import sounddevice as sd; print(sd.query_devices())"

# Test recording
uv run python -m src.audio_capture
```

### Transcription is slow

1. Check CPU usage during transcription:
   ```bash
   htop
   ```

2. Try disabling other CPU-intensive apps

3. Consider using `base` model instead of `tiny`:
   ```yaml
   # In config/config.yaml
   transcription:
     model_size: base  # More accurate, ~1.5s transcription
   ```

### Poor transcription accuracy

1. **Check microphone quality**: Test with voice recorder app
2. **Reduce background noise**: Use in quiet environment
3. **Speak clearly**: Natural pace, not too fast
4. **Try base model**: Edit `config/config.yaml`, set `model_size: base`
5. **Adjust VAD threshold**: In config, increase `vad.threshold` to 0.6 or 0.7

### Clipboard not working

```bash
# Check your session type
echo $XDG_SESSION_TYPE
# Output: wayland or x11

# For Wayland - test wl-clipboard
echo "test" | wl-copy && wl-paste
# If not working:
#   Debian/Ubuntu: sudo apt install wl-clipboard
#   RHEL/Fedora:   sudo dnf install wl-clipboard

# For X11 - test xclip
echo "test" | xclip -selection clipboard && xclip -selection clipboard -o
# If not working:
#   Debian/Ubuntu: sudo apt install xclip
#   RHEL/Fedora:   sudo dnf install xclip

# The install script auto-detects and installs the correct tools
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Presses Hotkey                  │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  trigger.sh / trigger_paste.sh / trigger_paste_terminal.sh │
│  → Unix Socket → TriggerServer (hotkey.py)              │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│          STTService.process_request() (main.py)         │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 1: AudioRecorder records until silence (1.2s)    │
│          - sounddevice captures audio                   │
│          - silero-vad detects speech/silence            │
│          (audio_capture.py)                             │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: WhisperTranscriber transcribes audio           │
│          - faster-whisper (CTranslate2)                 │
│          - Optimized for CPU, French/English            │
│          (transcription.py)                             │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: PunctuationProcessor post-processes            │
│          - Language-aware typography (FR/EN)            │
│          - Capitalize sentences                         │
│          (punctuation.py)                               │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 4: ClipboardManager copies to clipboard           │
│          - wl-copy integration                          │
│          (clipboard.py)                                 │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Step 5 (Optional): Auto-paste                          │
│          - Ctrl+V for standard apps (trigger_paste.sh)  │
│          - Ctrl+Shift+V for terminals (trigger_paste_terminal.sh) │
│          (autopaste.py)                                 │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│              Text appears in application                │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
stt-clipboard/
├── src/
│   ├── main.py              # Service orchestration
│   ├── audio_capture.py     # Audio recording + VAD
│   ├── transcription.py     # Whisper transcription
│   ├── punctuation.py       # Language-aware post-processing
│   ├── clipboard.py         # Wayland/X11 clipboard
│   ├── autopaste.py         # Auto-paste (Ctrl+V / Ctrl+Shift+V)
│   ├── hotkey.py            # Trigger server
│   └── config.py            # Configuration management
├── config/
│   └── config.yaml          # User configuration
├── scripts/
│   ├── install_deps.sh      # Dependency installation
│   ├── install_service.sh   # Service installation
│   ├── trigger.sh           # Copy-only mode trigger
│   ├── trigger_paste.sh     # Auto-paste mode trigger (Ctrl+V)
│   ├── trigger_paste_terminal.sh # Terminal paste trigger (Ctrl+Shift+V)
│   └── benchmark.py         # Performance testing
├── systemd/
│   └── stt-clipboard.service # Systemd service file
├── models/                  # Whisper models (auto-downloaded)
├── logs/                    # Application logs
├── pyproject.toml           # Python dependencies and project config
└── README.md                # This file
```

## Advanced Usage

### Change Model

For better accuracy (at cost of speed):

```yaml
# config/config.yaml
transcription:
  model_size: base  # or small, medium
```

Restart service: `systemctl --user restart stt-clipboard`

### Language Configuration

By default, the system auto-detects French and English:

```yaml
transcription:
  language: ""  # Auto-detect (default)
```

For single language (slightly faster):

```yaml
transcription:
  language: "fr"  # French only
  # or
  language: "en"  # English only
```

Notes:
- Auto-detection adds ~100-200ms latency but applies correct punctuation rules
- French text gets French spacing (space before ? ! : ;)
- English text gets English spacing (no space before punctuation)

### Adjust Silence Detection

Make it stop sooner or later:

```yaml
audio:
  silence_duration: 1.0  # Stop after 1.0s silence (faster)
  # or
  silence_duration: 2.0  # Wait 2.0s (for longer pauses)
```

### Custom Socket Path

```yaml
hotkey:
  socket_path: /tmp/my-custom-stt.sock
```

Update trigger.sh accordingly.

## Development

### Setup Development Environment

```bash
./scripts/setup_dev.sh
```

This will:
- Install development dependencies (pytest, linters, security tools)
- Set up pre-commit hooks (formatting, linting, security checks)
- Run initial validation

### Pre-commit Hooks

Pre-commit hooks run automatically on every commit and include:
- **Code formatting** (black, isort, ruff)
- **Type checking** (mypy)
- **Security scanning** (bandit, detect-secrets, gitleaks, safety)
- **Linting** (ruff, yamllint, shellcheck)
- **Tests** (pytest - runs on push)

Run manually:
```bash
# Run all hooks
uv run pre-commit run --all-files

# Run specific tools
uv run black .              # Format code
uv run ruff check .         # Lint code
uv run mypy src/            # Type check
uv run bandit -r src/       # Security scan
```

### Running Tests

```bash
# Test individual modules
uv run python -m src.audio_capture    # Test recording
uv run python -m src.transcription    # Test transcription
uv run python -m src.clipboard        # Test clipboard
uv run python -m src.punctuation      # Test punctuation

# Test trigger system
uv run python -m src.hotkey           # In one terminal
uv run python -m src.hotkey client    # In another terminal

# Run pytest
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Manual Testing

```bash
# One-shot mode (no service)
uv run python -m src.main --mode oneshot

# Daemon mode with debug logging
uv run python -m src.main --daemon --log-level DEBUG
```

### Quick Development Commands

Using the Makefile:
```bash
make help           # Show all available commands
make install-dev    # Setup development environment
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Run linters
make format         # Format code
make security       # Run security checks
make pre-commit     # Run all pre-commit hooks
make clean          # Clean build artifacts
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Performance Tuning

### CPU Governor

For consistent performance:

```bash
sudo cpupower frequency-set -g performance
```

### Model Selection

| Model  | Size  | Speed (5s audio) | Accuracy | Use Case |
|--------|-------|------------------|----------|----------|
| tiny   | 75MB  | ~0.8-1.2s       | Good     | Daily use (recommended) |
| base   | 140MB | ~1.5-2.0s       | Better   | Important transcriptions |
| small  | 460MB | ~3-4s           | Excellent| Critical documents |

## Privacy & Security

- **No Network**: All processing happens locally
- **No Logging of Audio**: Audio is processed in-memory only
- **No Cloud Services**: Zero external dependencies
- **Open Source**: Inspect all code in this repository
- **Logs**: Only contain metadata (duration, performance), never audio or text content
- **Security Scanning**: Automated checks for vulnerabilities and secrets via pre-commit hooks

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Credits

Built with:
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Fast Whisper inference
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio I/O
- [wl-clipboard](https://github.com/bugaevc/wl-clipboard) - Wayland clipboard
- [xclip](https://github.com/astrand/xclip) - X11 clipboard

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Development and contribution guidelines
- [SECURITY.md](SECURITY.md) - Security policy and reporting
- [docs/](docs/) - Additional documentation
  - [Security Scan Results](docs/SECURITY_SCAN_RESULTS.md)
  - [Dependency Vulnerabilities](docs/DEPENDENCY_VULNERABILITIES.md)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ for the privacy-conscious bilingual Linux community**

Works on Debian, Ubuntu, Fedora, RHEL, CentOS, Rocky Linux, and AlmaLinux.
