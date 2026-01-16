# Components

## File Structure

```
stt-clipboard/
├── src/
│   ├── main.py              # Service orchestration
│   ├── audio_capture.py     # Audio recording + VAD
│   ├── transcription.py     # Whisper transcription
│   ├── punctuation.py       # Language-aware post-processing
│   ├── clipboard.py         # Wayland/X11/macOS clipboard
│   ├── autopaste.py         # Auto-paste (keyboard simulation)
│   ├── hotkey.py            # Trigger server (Unix socket)
│   ├── notifications.py     # Desktop notifications
│   └── config.py            # Configuration management
├── config/
│   └── config.yaml          # User configuration
├── scripts/
│   ├── install_deps.sh      # Dependency installation
│   ├── install_service.sh   # Service installation
│   ├── trigger.sh           # Copy-only mode trigger
│   ├── trigger_paste.sh     # Auto-paste mode trigger
│   └── trigger_paste_terminal.sh # Terminal paste trigger
├── systemd/
│   └── stt-clipboard.service # Systemd service file
├── models/                  # Whisper models (auto-downloaded)
└── logs/                    # Application logs
```

## Core Modules

### main.py - STTService

The main orchestrator that coordinates all components.

```python
class STTService:
    """Main STT service orchestrator."""

    def __init__(self, config: Config):
        self.transcriber = WhisperTranscriber(config.transcription)
        self.audio_recorder = AudioRecorder(config.audio, config.vad)
        self.punctuation_processor = PunctuationProcessor(...)
        self.autopaster = create_autopaster(...)

    async def process_request(self, trigger_type: TriggerType):
        # 1. Record audio
        # 2. Transcribe
        # 3. Post-process
        # 4. Copy to clipboard
        # 5. Auto-paste (optional)
```

### audio_capture.py - AudioRecorder

Handles audio recording with Voice Activity Detection.

- Uses `sounddevice` for low-latency audio capture
- Silero VAD for speech detection (~1ms inference)
- Ring buffer with 0.5s pre-buffer to capture speech start

### transcription.py - WhisperTranscriber

Wraps faster-whisper for efficient transcription.

- CTranslate2 backend for CPU optimization
- int8 quantization for 2-3x speedup
- Auto-detects French/English

### punctuation.py - PunctuationProcessor

Language-aware post-processing.

- French: Adds space before `? ! : ;`
- English: Removes spaces before punctuation
- Capitalizes sentences

### clipboard.py - ClipboardManager

Universal clipboard integration.

```python
class BaseClipboardManager(ABC):
    def copy(self, text: str) -> bool: ...
    def paste(self) -> str | None: ...
    def clear(self) -> bool: ...

class WaylandClipboardManager  # wl-copy
class X11ClipboardManager      # xclip/xsel
class MacClipboardManager      # pbcopy/pbpaste
```

### autopaste.py - Auto-Paste

Keyboard simulation for automatic pasting.

```python
class BaseAutoPaster(ABC):
    def paste(self) -> bool: ...
    def is_available(self) -> bool: ...

class XdotoolPaster   # X11
class YdotoolPaster   # Universal/Wayland
class WtypePaster     # Wayland (direct typing)
class MacPaster       # macOS (osascript)
```

### hotkey.py - TriggerServer

Unix socket server for hotkey integration.

- Listens on `/tmp/stt-clipboard.sock`
- Secured with 0600 permissions
- Handles trigger types: COPY, PASTE, PASTE_TERMINAL

### config.py - Configuration

Type-safe configuration management.

```python
@dataclass
class Config:
    audio: AudioConfig
    vad: VADConfig
    transcription: TranscriptionConfig
    punctuation: PunctuationConfig
    clipboard: ClipboardConfig
    paste: PasteConfig
    logging: LoggingConfig
    hotkey: HotkeyConfig
```
