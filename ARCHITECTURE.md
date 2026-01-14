# STT Clipboard Architecture

This document explains the technical architecture of the system.

## System Compatibility

**Supported Platforms:**
- **Distributions**: Debian, Ubuntu, Fedora, RHEL, CentOS, Rocky Linux, AlmaLinux
- **Display Servers**: Wayland and X11 (auto-detected)
- **Languages**: French and English (auto-detected)

The system automatically detects the environment and adapts accordingly.

## Overview

```
┌──────────────────────────────────────────────────────────────┐
│                         User                                  │
│                Presses keyboard shortcut                      │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│  Keyboard Shortcut → trigger script                          │
│  - trigger.sh → "TRIGGER_COPY"                              │
│  - trigger_paste.sh → "TRIGGER_PASTE"                       │
│  - trigger_paste_terminal.sh → "TRIGGER_PASTE_TERMINAL"    │
│  Sends message via netcat to Unix socket                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│  src/hotkey.py - TriggerServer                               │
│  - Listens on /tmp/stt-clipboard.sock                        │
│  - Parses trigger type and calls STTService.process_request()│
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────────┐
│  src/main.py - STTService (orchestration)                    │
│  5-step pipeline (6th step optional):                        │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ↓                             ↓
┌──────────────────┐          ┌──────────────────┐
│  STEP 1: AUDIO   │          │ Models loaded    │
│                  │          │ at startup:      │
│ AudioRecorder    │          │ - Whisper base   │
│ record_until_    │          │ - Silero VAD     │
│ silence()        │          │ (resident in     │
│                  │          │  memory)         │
│ • sounddevice    │          └──────────────────┘
│   captures audio │
│ • silero-vad     │
│   detects speech │
│ • Ring buffer    │
│ • Stops at 1.2s  │
│   silence        │
└────────┬─────────┘
         │ audio: np.ndarray (float32, 16kHz)
         ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: TRANSCRIPTION                                       │
│                                                               │
│  WhisperTranscriber.transcribe(audio)                        │
│                                                               │
│  • faster-whisper (CTranslate2 backend)                      │
│  • Model: base, int8 quantization                            │
│  • Optimizations:                                            │
│    - language="" (auto-detect FR/EN)                         │
│    - beam_size=5 (balanced accuracy/speed)                   │
│    - vad_filter=False (external VAD)                         │
│                                                               │
│  Performance: ~1-2s for 5s audio                             │
└────────┬─────────────────────────────────────────────────────┘
         │ text: str (raw from Whisper)
         │ detected_language: str (e.g., "fr" or "en")
         ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: POST-PROCESSING                                     │
│                                                               │
│  PunctuationProcessor.process(text, detected_language)       │
│                                                               │
│  • Language-aware typography:                                │
│    French: Space before ? ! : ;                              │
│    English: No space before punctuation                      │
│  • Capitalization after: . ! ?                               │
│  • French apostrophes: l', d', qu'                           │
│  • Clean Whisper artifacts                                   │
│  • Regex-based (no ML, fast)                                 │
└────────┬─────────────────────────────────────────────────────┘
         │ text: str (formatted)
         ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: CLIPBOARD                                           │
│                                                               │
│  ClipboardManager.copy(text)                                 │
│                                                               │
│  • Auto-detects Wayland (wl-copy) or X11 (xclip)            │
│  • subprocess.Popen with stdin                               │
│  • 2s timeout                                                │
│  • Retry logic on failure                                    │
└────────┬─────────────────────────────────────────────────────┘
         │ ✓ Text in clipboard
         ↓
┌──────────────────────────────────────────────────────────────┐
│  STEP 5: AUTO-PASTE (Optional)                               │
│                                                               │
│  AutoPaster.paste()                                          │
│                                                               │
│  • TRIGGER_COPY: Skip this step                             │
│  • TRIGGER_PASTE: Simulate Ctrl+V (standard apps)           │
│  • TRIGGER_PASTE_TERMINAL: Simulate Ctrl+Shift+V (terminals)│
│  • Uses xdotool (X11) or ydotool (Wayland)                  │
└────────┬─────────────────────────────────────────────────────┘
         │ ✓ Text appears in application
         ↓
┌──────────────────────────────────────────────────────────────┐
│              Text ready to use                               │
└──────────────────────────────────────────────────────────────┘
```

## Modules

### src/main.py (Orchestration)

**Role**: Entry point, orchestrates the complete pipeline

**Main classes:**
- `STTService`: Main service with methods:
  - `initialize()`: Loads models at startup
  - `process_request()`: Complete pipeline (4 steps)
  - `run_daemon()`: Systemd service mode
  - `run_oneshot()`: CLI test mode

**Execution modes:**
1. **Daemon** (`--daemon`): Systemd service, waits for triggers
2. **Oneshot** (`--mode oneshot`): Manual test, single transcription

**Lifecycle:**
```python
# Daemon mode
1. Load Whisper model (~2-3s, once)
2. Load VAD model (~0.5s, once)
3. Start TriggerServer (Unix socket)
4. Infinite loop:
   - Wait for trigger
   - process_request()
   - Log stats
```

### src/audio_capture.py (Audio Capture + VAD)

**Role**: Record audio with automatic silence detection

**Main classes:**
- `AudioRecorder`: Audio capture + VAD management

**Algorithm:**
```python
1. Open sounddevice stream (callback mode)
2. For each audio chunk:
   a. Detect speech with silero-vad
   b. If speech detected:
      - Add pre-buffer to main buffer
      - Continue recording
      - Update last_speech_time
   c. If no speech and speech_started:
      - Check silence duration
      - If > threshold: stop
   d. If no speech and !speech_started:
      - Add to pre-buffer (capture speech start)
3. Return audio as np.ndarray
```

**Optimizations:**
- Callback-based streaming (low latency)
- Ring buffer with collections.deque
- 0.5s pre-buffer to capture speech start
- Min speech duration 0.3s (avoids false starts)

**VAD (Silero):**
- Loaded via `torch.hub.load("snakers4/silero-vad")`
- Inference ~1ms per chunk
- Configurable threshold (default: 0.5)

### src/transcription.py (STT Engine)

**Role**: Audio → text transcription with faster-whisper

**Main classes:**
- `WhisperTranscriber`: Wrapper around faster-whisper

**Critical optimizations:**
```python
model = WhisperModel(
    model_size="base",
    device="cpu",
    compute_type="int8",        # 2-3x speedup vs float32
    download_root="./models"
)

segments, info = model.transcribe(
    audio,
    language=None,              # Auto-detect FR/EN (+100-200ms)
    beam_size=5,                # Balanced accuracy/speed
    best_of=5,
    temperature=0.0,            # Deterministic
    vad_filter=False,           # External VAD
    word_timestamps=False,      # +15% speed
    condition_on_previous_text=False
)
```

**Performance:**
- Cold start: ~2-3s (load model)
- Warm inference: ~1-2s for 5s audio
- RTF (Real-Time Factor): ~0.2-0.4x

**Backend: CTranslate2**
- C++ optimized for CPU
- Int8 quantization
- Batch processing
- Memory efficient

### src/punctuation.py (Post-processing)

**Role**: Apply language-aware typography and clean artifacts

**Main classes:**
- `PunctuationProcessor`: Post-processing pipeline

**Applied rules:**
```python
# 1. French spacing (when French detected)
"pourquoi?"  → "pourquoi ?"
"attention!"  → "attention !"
"bonjour:"    → "bonjour :"

# 2. English spacing (when English detected)
"why ?"      → "why?"
"hello !"    → "hello!"

# 3. Capitalization (both languages)
"hello. how are you" → "Hello. How are you"

# 4. French apostrophes (French only)
"l ecole"  → "l'école"
"qu est ce" → "qu'est-ce"

# 5. Clean artifacts (both languages)
"......"    → "."
"uh uh"     → "" (filler words)
"  "        → " " (multiple spaces)
```

**Implementation:**
- Regex-based (no ML, ultra-fast)
- ~10ms latency
- Deterministic

### src/clipboard.py (Clipboard Integration)

**Role**: Copy text to clipboard (Wayland or X11)

**Main classes:**
- `ClipboardManager`: Auto-detecting clipboard wrapper
- `WaylandClipboardManager`: wl-clipboard implementation
- `X11ClipboardManager`: xclip/xsel implementation

**Implementation:**
```python
# Auto-detect session type
session_type = detect_session_type()  # wayland, x11, or unknown

if session_type == "wayland":
    manager = WaylandClipboardManager()  # Uses wl-copy
elif session_type == "x11":
    manager = X11ClipboardManager()      # Uses xclip or xsel
else:
    # Fallback: try both
    manager = ClipboardManager()
```

**Session detection:**
- Checks `$XDG_SESSION_TYPE` environment variable
- Fallback to `$WAYLAND_DISPLAY` or `$DISPLAY`
- Automatically uses the correct tool

**Retry logic:**
- 1 retry by default
- 2s timeout
- Logs errors

**Supported tools:**
- **Wayland**: `wl-copy` / `wl-paste` (wl-clipboard package)
- **X11**: `xclip` (preferred) or `xsel` (fallback)

**Tool selection priority:**
1. Check `$XDG_SESSION_TYPE` environment variable
2. Fallback to `$WAYLAND_DISPLAY` or `$DISPLAY`
3. Try WaylandClipboardManager first, then X11ClipboardManager
4. Raise error if neither tool is available

**Example usage:**
```python
# Auto-detect and create appropriate manager
manager = ClipboardManager()  # Returns WaylandClipboardManager or X11ClipboardManager

# Copy text (works on both Wayland and X11)
manager.copy("Hello, world!")

# The user can paste with Ctrl+V
```

**Distribution compatibility:**
- Debian/Ubuntu: `sudo apt install wl-clipboard xclip`
- RHEL/Fedora: `sudo dnf install wl-clipboard xclip`
- Both tools are automatically installed by `install_deps.sh`

### src/hotkey.py (Trigger System)

**Role**: Receive triggers from keyboard shortcut

**Main classes:**
- `TriggerServer`: Async Unix socket server
- `TriggerClient`: Client to send triggers

**Architecture:**
```
Ubuntu Shortcut
       ↓
scripts/trigger.sh
       ↓
echo "TRIGGER" | nc -U /tmp/stt-clipboard.sock
       ↓
TriggerServer (asyncio.start_unix_server)
       ↓
Callback: STTService.process_request()
```

**Unix socket advantages:**
- No network port (security)
- Low latency (<1ms)
- Permission control (chmod 0600)
- No polling

**Alternative (not implemented):**
- evdev for direct keyboard capture
- Requires input group permissions
- More complex, not necessary here

### src/config.py (Configuration)

**Role**: YAML configuration management

**Main classes:**
- `Config`: Main configuration
- `AudioConfig`, `VADConfig`, etc.: Sub-configs

**Features:**
- Automatic validation
- Sensible defaults
- Type-safe (dataclasses)
- Human-readable YAML

**Example:**
```python
config = Config.from_yaml("config/config.yaml")
config.validate()  # Raises ValueError if invalid

# Type-safe access
silence_duration = config.audio.silence_duration
model_size = config.transcription.model_size
```

## System Dependencies & Installation

### Multi-Distribution Support

The installation script (`scripts/install_deps.sh`) automatically detects the Linux distribution and installs appropriate packages:

**Distribution Detection:**
```bash
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"        # Debian/Ubuntu
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"        # Fedora, RHEL 8+, Rocky, AlmaLinux
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"        # CentOS 7, RHEL 7
fi
```

**Package Mapping:**

| Dependency | Debian/Ubuntu | RHEL/Fedora |
|------------|---------------|-------------|
| **PortAudio** | libportaudio2, portaudio19-dev | portaudio, portaudio-devel |
| **Python Dev** | python3-dev | python3-devel |
| **Build Tools** | build-essential | gcc, gcc-c++, make |
| **Wayland Clipboard** | wl-clipboard | wl-clipboard |
| **X11 Clipboard** | xclip | xclip |
| **Netcat** | netcat-openbsd | nmap-ncat |

### Display Server Detection

The installation script also detects the display server and installs appropriate clipboard tools:

```bash
SESSION_TYPE="${XDG_SESSION_TYPE:-unknown}"

if [ "$SESSION_TYPE" = "x11" ]; then
    # Install xclip for X11
elif [ "$SESSION_TYPE" = "wayland" ]; then
    # wl-clipboard already installed
else
    # Unknown: install both for compatibility
fi
```

At runtime, `src/clipboard.py` uses the same detection to choose the right tool.

## Performance Breakdown

**Typical latency (5s of speech):**

| Step | Time | Notes |
|------|------|-------|
| Hotkey → Trigger | <50ms | Unix socket |
| Recording | ~6.2s | 5s speech + 1.2s silence |
| Transcription | ~1-2s | RTF 0.2-0.4x (base model) |
| Post-processing | <10ms | Simple regex |
| Clipboard | <20ms | wl-copy |
| **Total** | **~7.3-8.3s** | Perceived: ~1-2s after speech ends |

**Memory breakdown:**

| Component | Memory |
|-----------|--------|
| Python runtime | ~50MB |
| Whisper base (int8) | ~400MB |
| Silero VAD | ~50MB |
| Audio buffers | ~10MB |
| **Total (idle)** | ~100MB |
| **Total (transcription)** | ~500MB |

## Critical Optimizations

### 1. Daemon Architecture
**Without daemon:**
```
User trigger → Load models (2-3s) → Transcribe (1-2s) = 3-5s latency
```

**With daemon:**
```
Startup: Load models once (2-3s)
User trigger → Transcribe (1-2s) = 1-2s latency
```

**Gain: 2-3s per request**

### 2. faster-whisper vs Whisper
```python
# Standard Whisper
model = whisper.load_model("base")
result = model.transcribe(audio)
# ~4-6s for 5s audio

# faster-whisper
model = WhisperModel("base", compute_type="int8")
result = model.transcribe(audio)
# ~1-2s for 5s audio

# Gain: 3-4x speedup
```

### 3. Transcription Parameters
```python
# Slow (beam search)
beam_size=5, best_of=5
# ~2-3s for 5s audio, high accuracy

# Fast (greedy)
beam_size=1, best_of=1, temperature=0
# ~1s for 5s audio, -3% accuracy

# Current: Balanced
beam_size=5, best_of=5, temperature=0
# ~1-2s, optimal accuracy/speed
```

### 4. Language Detection
```python
# Auto-detect (current setting)
language=None  # or ""
# +100-200ms per transcription
# Applies correct punctuation rules

# Fixed language
language="fr"
# Skip detection, ~100ms faster
# But loses bilingual support

# Trade-off: Auto-detection worth the latency
```

### 5. Silero VAD vs Energy-based
```python
# Energy-based VAD
threshold = audio.mean() * 2
is_speech = audio.max() > threshold
# Simple but false positives

# Silero VAD
speech_prob = vad_model(audio)
is_speech = speech_prob > 0.5
# ~1ms inference, much more accurate

# Gain: Robustness, no false triggers
```

## Security & Privacy

### Data Processed
- **Audio**: In-memory only, never saved
- **Text**: Copied to clipboard, not stored by app
- **Logs**: Metadata only (duration, size), no content

### Network
- **Zero network connection** in production
- Only exception: Model download at installation
- Can block with firewall after installation

### Permissions
- **Audio**: Microphone access (standard for STT)
- **Clipboard**: wl-copy (no special permissions)
- **Socket**: /tmp/stt-clipboard.sock (chmod 0600, user only)

### Potential Vulnerabilities
1. **Socket injection**: Mitigated by 0600 permissions
2. **Clipboard hijacking**: Native Wayland limitation
3. **Resource exhaustion**: Mitigated by max_recording_duration

## Testing Strategy

### Unit Tests
```bash
tests/test_imports.py       # Verify imports
tests/test_system.py        # Integration test
```

### Manual Tests
```bash
# Test audio module
python -m src.audio_capture

# Test transcription
python -m src.transcription

# Test clipboard
python -m src.clipboard

# Test punctuation
python -m src.punctuation

# Test trigger
python -m src.hotkey        # Server
python -m src.hotkey client # Client
```

### Benchmarks
```bash
./scripts/benchmark.py --iterations 10
# Measures: transcription time, RTF, stats
```

## Debugging

### Detailed Logs
```bash
# Debug mode
python -m src.main --mode oneshot --log-level DEBUG

# Journalctl
journalctl --user -u stt-clipboard -f

# File
tail -f logs/stt-clipboard.log
```

### Profiling
```python
# Add to src/main.py
import cProfile
cProfile.run('service.run_oneshot()', 'profile.stats')

# Analyze
python -m pstats profile.stats
```

### Common Issues
1. **Slow transcription**: CPU throttling, check governor
2. **Poor accuracy**: Ambient noise, bad microphone
3. **Socket errors**: Service not started, permissions
4. **Clipboard fails**: No active Wayland session

## Future Extensions

### 1. More Languages
```python
# Support Spanish, German, etc.
# Whisper supports 99+ languages
config.transcription.language = ""  # Auto-detect
```

### 2. Voice Commands
```python
# In punctuation.py
def detect_commands(text: str) -> Optional[str]:
    if "new paragraph" in text.lower():
        return "\n\n"
    # etc.
```

### 3. History
```python
# In main.py
transcription_history = []
def process_request():
    # ...
    transcription_history.append({
        "timestamp": time.time(),
        "text": text,
        "duration": audio_duration
    })
```

### 4. GUI
```python
# PyQt6 or GTK4
class STTGui:
    def show_preview(self, text: str):
        # Preview before clipboard
        # Buttons: Accept / Edit / Cancel
```

## Conclusion

**Simple but effective** architecture:
- Daemon to eliminate cold-start
- faster-whisper for performance
- Synchronous pipeline (no unnecessary async complexity)
- Unix socket for triggers (simple, robust)
- Universal clipboard (Wayland + X11 support)
- Bilingual support with language-aware punctuation
- Multi-distribution compatibility (Debian + RHEL families)

**Auto-detection at every level:**
1. **Distribution**: apt, dnf, or yum → installs correct packages
2. **Display server**: Wayland or X11 → uses appropriate clipboard tool
3. **Language**: French or English → applies correct punctuation rules

**Accepted trade-offs:**
- Base model vs Tiny: +5% accuracy, -40% speed ✓
- Auto-detection: +100-200ms, correct punctuation ✓
- CPU-only: Compatible everywhere, no GPU ✓
- Offline: Maximum privacy, no cloud ✓
- Multi-distro: Slightly more complex install script, universal compatibility ✓

**Platform support matrix:**

| Platform | Clipboard | Status |
|----------|-----------|--------|
| Ubuntu/Debian + Wayland | wl-clipboard | ✅ Tested |
| Ubuntu/Debian + X11 | xclip | ✅ Tested |
| Fedora/RHEL + Wayland | wl-clipboard | ✅ Supported |
| Fedora/RHEL + X11 | xclip | ✅ Supported |

**Result: Daily-usable system across all major Linux distributions!**
