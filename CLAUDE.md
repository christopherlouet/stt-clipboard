# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STT Clipboard is a privacy-focused, offline bilingual (French/English) speech-to-text system for Linux. It uses Whisper for transcription, Silero VAD for voice activity detection, and works on both Wayland and X11 display servers across Debian/Ubuntu and RHEL-based distributions.

## Common Commands

### Development
```bash
# Install all dependencies (auto-detects distribution and display server)
./scripts/install_deps.sh

# Setup development environment (installs dev deps, pre-commit hooks)
./scripts/setup_dev.sh

# Run in one-shot mode (test transcription once)
uv run python -m src.main --mode oneshot

# Run in daemon mode (for development/debugging)
uv run python -m src.main --daemon --log-level DEBUG

# Run specific module tests
uv run python -m src.audio_capture    # Test audio recording
uv run python -m src.transcription    # Test transcription
uv run python -m src.clipboard        # Test clipboard
uv run python -m src.punctuation      # Test punctuation processing

# Run hotkey trigger system
uv run python -m src.hotkey           # Start server (terminal 1)
uv run python -m src.hotkey client    # Send trigger (terminal 2)

# Test trigger modes
./scripts/trigger.sh                  # Copy-only mode (default)
./scripts/trigger.sh TRIGGER_COPY     # Copy-only mode (explicit)
./scripts/trigger_paste.sh            # Copy + auto-paste mode (Ctrl+V)
./scripts/trigger_paste_terminal.sh   # Copy + terminal paste mode (Ctrl+Shift+V)
```

### Testing and Quality
```bash
# Run tests
uv run pytest
uv run pytest --cov=src --cov-report=html    # With coverage

# Format code
uv run black .
uv run isort .

# Lint
uv run ruff check .
uv run ruff check --fix .

# Type check
uv run mypy src/

# Security scans
uv run bandit -c pyproject.toml -r src/
uv run detect-secrets scan --baseline .secrets.baseline

# Run all pre-commit hooks
uv run pre-commit run --all-files

# Performance benchmark
uv run ./scripts/benchmark.py --iterations 10
```

### Service Management
```bash
# Install systemd service (auto-starts on login)
./scripts/install_service.sh

# Service control
systemctl --user start stt-clipboard
systemctl --user stop stt-clipboard
systemctl --user restart stt-clipboard
systemctl --user status stt-clipboard

# View logs
journalctl --user -u stt-clipboard -f           # Real-time
journalctl --user -u stt-clipboard -n 50        # Last 50 lines
tail -f logs/stt-clipboard.log                  # File logs
```

### Makefile Shortcuts
```bash
make help           # Show all targets
make install-dev    # Setup dev environment
make test           # Run tests
make test-cov       # Tests with coverage
make lint           # Run linters
make format         # Format code
make security       # Security scans
make pre-commit     # All pre-commit hooks
make clean          # Clean artifacts
make run            # One-shot mode
make benchmark      # Performance test
```

## Architecture

### System Flow
1. **Hotkey Trigger**: User presses keyboard shortcut → trigger script → Unix socket (`/tmp/stt-clipboard.sock`)
   - `trigger.sh`: Sends `TRIGGER_COPY` (copy-only mode)
   - `trigger_paste.sh`: Sends `TRIGGER_PASTE` (copy + auto-paste with Ctrl+V)
   - `trigger_paste_terminal.sh`: Sends `TRIGGER_PASTE_TERMINAL` (copy + auto-paste with Ctrl+Shift+V for terminals)
2. **Audio Capture** (`src/audio_capture.py`): Records audio using sounddevice, detects speech/silence with Silero VAD, stops after 1.2s silence
3. **Transcription** (`src/transcription.py`): faster-whisper (CTranslate2) transcribes audio, auto-detects French/English
4. **Post-processing** (`src/punctuation.py`): Language-aware punctuation (French: space before `? ! : ;`, English: no space)
5. **Clipboard** (`src/clipboard.py`): Auto-detects Wayland (wl-copy) or X11 (xclip) and copies text
6. **Auto-paste** (`src/autopaste.py`): *Optional* - Simulates keystroke using xdotool/ydotool/wtype
   - TRIGGER_PASTE: Simulates Ctrl+V (for standard applications)
   - TRIGGER_PASTE_TERMINAL: Simulates Ctrl+Shift+V (for terminal applications)

### Key Components

**src/main.py** - Orchestration and entry point
- `STTService` class coordinates the 5-step pipeline (6th step is optional auto-paste)
- Two modes: `--daemon` (systemd service) and `--mode oneshot` (CLI test)
- Models are loaded once at startup (Whisper + VAD) and kept in memory
- Handles three trigger types:
  - `TRIGGER_COPY` (copy only)
  - `TRIGGER_PASTE` (copy + auto-paste with Ctrl+V)
  - `TRIGGER_PASTE_TERMINAL` (copy + auto-paste with Ctrl+Shift+V for terminals)

**src/audio_capture.py** - Audio recording with VAD
- `AudioRecorder` uses sounddevice callback-based streaming for low latency
- Silero VAD detects speech with ~1ms inference per chunk
- Ring buffer with 0.5s pre-buffer to capture speech start
- Stops recording after configured silence duration (default: 1.2s)

**src/transcription.py** - Whisper STT engine
- `WhisperTranscriber` wraps faster-whisper with CTranslate2 backend
- Uses `int8` quantization for 2-3x speedup vs float32
- Auto-detects French/English (adds ~100-200ms but enables proper punctuation)
- Beam size 5 for balanced accuracy/speed
- Performance: ~1-2s transcription for 5s audio (RTF 0.2-0.4x)

**src/punctuation.py** - Language-aware post-processing
- `PunctuationProcessor` applies language-specific typography rules
- French: adds space before `? ! : ;`, handles apostrophes (`l'`, `d'`, `qu'`)
- English: removes spaces before punctuation
- Capitalizes sentences, cleans Whisper artifacts
- Regex-based, ~10ms latency, deterministic

**src/clipboard.py** - Universal clipboard integration
- Auto-detects display server via `$XDG_SESSION_TYPE` or fallback env vars
- `WaylandClipboardManager`: uses `wl-copy` from wl-clipboard package
- `X11ClipboardManager`: uses `xclip` (preferred) or `xsel` (fallback)
- Retry logic with 2s timeout

**src/autopaste.py** - Auto-paste keyboard simulation
- Simulates Ctrl+V or Ctrl+Shift+V keystroke to paste clipboard content into active application
- `BaseAutoPaster`: Abstract class for paste implementations
- `XdotoolPaster`: Uses `xdotool` for X11 (`xdotool key ctrl+v`)
- `YdotoolPaster`: Uses `ydotool` for Wayland/universal
  - `use_shift=False`: Ctrl+V for standard apps (`ydotool key 29:1 47:1 47:0 29:0`)
  - `use_shift=True`: Ctrl+Shift+V for terminals (`ydotool key 29:1 42:1 47:1 47:0 42:0 29:0`)
- `WtypePaster`: Uses `wtype` for Wayland (types text directly, fallback option)
- `create_autopaster()`: Factory with automatic tool detection and fallback chain
- Graceful degradation: if no paste tool available, service continues in copy-only mode

**src/hotkey.py** - Unix socket trigger server
- `TriggerServer` is an async Unix socket server listening on `/tmp/stt-clipboard.sock`
- `TriggerType` enum: COPY, PASTE, PASTE_TERMINAL, UNKNOWN (legacy support)
- Parses incoming messages and passes type to callback:
  - "TRIGGER_COPY" → TriggerType.COPY
  - "TRIGGER_PASTE" → TriggerType.PASTE
  - "TRIGGER_PASTE_TERMINAL" → TriggerType.PASTE_TERMINAL
- `TriggerClient` sends typed trigger commands via netcat
- No network port (security), <1ms latency, permission control (chmod 0600)

**src/config.py** - YAML configuration management
- Type-safe dataclasses with automatic validation
- `Config.from_yaml("config/config.yaml")` loads and validates all settings
- Sensible defaults for all parameters

### Multi-Platform Compatibility

**Distribution Auto-detection** (`scripts/install_deps.sh`):
- Detects apt (Debian/Ubuntu) vs dnf (Fedora/RHEL 8+/Rocky/AlmaLinux) vs yum (CentOS 7)
- Installs distribution-appropriate packages (e.g., `libportaudio2` vs `portaudio`)

**Display Server Auto-detection** (runtime):
- Checks `$XDG_SESSION_TYPE`, fallback to `$WAYLAND_DISPLAY` or `$DISPLAY`
- Selects appropriate clipboard tool: `wl-copy` (Wayland) or `xclip` (X11)

**Language Auto-detection** (transcription):
- Whisper detects French vs English automatically
- Applies correct punctuation rules based on detected language

## Configuration

Edit `config/config.yaml` to customize behavior:

**Audio settings**:
- `silence_duration: 1.2` - Silence threshold to stop recording (seconds)
- `max_recording_duration: 30` - Safety limit for recording length
- `min_speech_duration: 0.3` - Avoid false starts from noise

**Transcription settings**:
- `model_size: base` - Options: `tiny` (fast), `base` (accurate), `small`, `medium`
- `language: ""` - Auto-detect FR/EN (empty), or force `"fr"` or `"en"` for ~100ms speedup
- `compute_type: int8` - Quantization level (int8 is fastest)
- `beam_size: 5` - Higher = more accurate but slower (1 = greedy/fastest)

**Punctuation settings**:
- `french_spacing: true` - Apply French typography rules when French detected

**VAD settings**:
- `threshold: 0.5` - Speech detection sensitivity (0.0-1.0, higher = stricter)

**Auto-paste settings**:
- `enabled: true` - Enable/disable auto-paste functionality
- `timeout: 2.0` - Timeout for paste operations (seconds)
- `delay_ms: 100` - Delay between copy and paste (milliseconds, prevents race conditions)
- `preferred_tool: auto` - Paste tool preference: `"auto"` (detect best available), `"xdotool"` (X11), `"ydotool"` (universal), `"wtype"` (Wayland)

After changing config: `systemctl --user restart stt-clipboard`

## Performance Characteristics

- **Cold start**: ~2-3s (model loading)
- **Warm transcription**: ~1-2s for 5s audio
- **Memory**: ~100MB idle, ~500MB during transcription
- **CPU**: 1 core at 100% for ~1s during transcription
- **Accuracy**: 92-95% WER for clean French/English audio
- **Total latency**: ~7-8s (includes recording + silence detection + transcription)

## Critical Optimizations

1. **Daemon architecture**: Models loaded once at startup, not per-request (saves 2-3s per request)
2. **faster-whisper + int8**: 3-4x speedup vs standard Whisper
3. **External VAD**: Silero VAD is faster and more accurate than Whisper's built-in VAD
4. **Callback-based audio**: Low latency streaming vs blocking read
5. **Unix socket**: <1ms trigger latency vs HTTP or file polling

## Security Notes

- All processing is 100% offline (no network after model download)
- Audio is never saved to disk, processed in-memory only
- Logs contain metadata only (duration, performance), never audio or text content
- Unix socket secured with 0600 permissions (owner-only access)
- Pre-commit hooks scan for secrets, vulnerabilities, and code quality issues

## Code Style

- **Line length**: 100 characters
- **Python version**: 3.10+
- **Formatting**: Black + isort (automatic via pre-commit)
- **Linting**: Ruff + mypy
- **Security**: Bandit + Safety + detect-secrets
- All hooks run automatically on commit

## Testing Strategy

**Manual module tests**: Each module has `if __name__ == "__main__"` for standalone testing
**Unit tests**: `tests/` directory with pytest
**Integration test**: `tests/test_system.py` for end-to-end validation
**Benchmarks**: `scripts/benchmark.py` for performance regression testing
**Pre-commit hooks**: Automatic formatting, linting, security, and type checking

## Troubleshooting Common Issues

**Service won't start**: Check `journalctl --user -u stt-clipboard -n 50` for errors, ensure dependencies installed
**Slow transcription**: Check CPU governor (`cpupower frequency-set -g performance`), close heavy apps
**Poor accuracy**: Reduce background noise, check microphone quality, try `base` model instead of `tiny`
**Clipboard fails**: Verify correct display server tool installed (`wl-copy` for Wayland, `xclip` for X11)
**Socket errors**: Ensure service is running, check socket permissions at `/tmp/stt-clipboard.sock`
