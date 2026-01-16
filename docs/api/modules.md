# API Reference

This section documents the internal modules and their public APIs.

## Core Modules

### main.py - STTService

The main orchestrator that coordinates all components.

```python
class STTService:
    """Main STT service orchestrator."""

    def __init__(self, config: Config):
        """
        Initialize the STT service.

        Args:
            config: Application configuration
        """

    async def process_request(self, trigger_type: TriggerType) -> str | None:
        """
        Process a transcription request.

        Args:
            trigger_type: Type of trigger (COPY, PASTE, PASTE_TERMINAL)

        Returns:
            Transcribed text or None if failed
        """

    async def run_daemon(self) -> None:
        """Run the service in daemon mode."""

    def run_oneshot(self) -> str | None:
        """Run a single transcription and exit."""
```

### audio_capture.py - AudioRecorder

Handles audio recording with Voice Activity Detection.

```python
class AudioRecorder:
    """Records audio with VAD-based silence detection."""

    def __init__(self, audio_config: AudioConfig, vad_config: VADConfig):
        """
        Initialize the audio recorder.

        Args:
            audio_config: Audio capture settings
            vad_config: Voice activity detection settings
        """

    def record(self) -> np.ndarray | None:
        """
        Record audio until silence is detected.

        Returns:
            Audio data as numpy array, or None if failed
        """

    def stop(self) -> None:
        """Stop the current recording."""
```

### transcription.py - WhisperTranscriber

Wraps faster-whisper for efficient transcription.

```python
class WhisperTranscriber:
    """Whisper-based speech-to-text transcriber."""

    def __init__(self, config: TranscriptionConfig):
        """
        Initialize the transcriber.

        Args:
            config: Transcription settings
        """

    def transcribe(self, audio: np.ndarray) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio: Audio data as numpy array

        Returns:
            TranscriptionResult with text and metadata
        """

@dataclass
class TranscriptionResult:
    """Result of a transcription."""
    text: str
    language: str
    confidence: float
```

### punctuation.py - PunctuationProcessor

Language-aware post-processing for punctuation.

```python
class PunctuationProcessor:
    """Applies language-specific punctuation rules."""

    def __init__(self, config: PunctuationConfig):
        """
        Initialize the processor.

        Args:
            config: Punctuation settings
        """

    def process(self, text: str, language: str) -> str:
        """
        Apply punctuation rules based on language.

        Args:
            text: Input text
            language: Language code ('fr' or 'en')

        Returns:
            Text with corrected punctuation
        """
```

### clipboard.py - ClipboardManager

Universal clipboard integration.

```python
class BaseClipboardManager(ABC):
    """Abstract base class for clipboard managers."""

    @abstractmethod
    def copy(self, text: str) -> bool:
        """
        Copy text to clipboard.

        Args:
            text: Text to copy

        Returns:
            True if successful
        """

    @abstractmethod
    def paste(self) -> str | None:
        """
        Get text from clipboard.

        Returns:
            Clipboard content or None
        """

    @abstractmethod
    def clear(self) -> bool:
        """
        Clear the clipboard.

        Returns:
            True if successful
        """

class WaylandClipboardManager(BaseClipboardManager):
    """Clipboard manager using wl-copy (Wayland)."""

class X11ClipboardManager(BaseClipboardManager):
    """Clipboard manager using xclip (X11)."""

class MacClipboardManager(BaseClipboardManager):
    """Clipboard manager using pbcopy (macOS)."""

def create_clipboard_manager() -> BaseClipboardManager:
    """
    Create appropriate clipboard manager for current environment.

    Returns:
        Clipboard manager instance
    """
```

### autopaste.py - Auto-Paste

Keyboard simulation for automatic pasting.

```python
class BaseAutoPaster(ABC):
    """Abstract base class for auto-paste implementations."""

    @abstractmethod
    def paste(self) -> bool:
        """
        Simulate paste keystroke.

        Returns:
            True if successful
        """

    @abstractmethod
    def paste_terminal(self) -> bool:
        """
        Simulate terminal paste keystroke (Ctrl+Shift+V).

        Returns:
            True if successful
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this paster is available on the system.

        Returns:
            True if available
        """

class XdotoolPaster(BaseAutoPaster):
    """Auto-paste using xdotool (X11)."""

class YdotoolPaster(BaseAutoPaster):
    """Auto-paste using ydotool (Universal/Wayland)."""

class WtypePaster(BaseAutoPaster):
    """Auto-paste using wtype (Wayland)."""

class MacPaster(BaseAutoPaster):
    """Auto-paste using osascript (macOS)."""

def create_autopaster(config: PasteConfig) -> BaseAutoPaster | None:
    """
    Create appropriate auto-paster for current environment.

    Args:
        config: Paste configuration

    Returns:
        Auto-paster instance or None if not available
    """
```

### hotkey.py - TriggerServer

Unix socket server for hotkey integration.

```python
class TriggerType(Enum):
    """Types of triggers."""
    COPY = "TRIGGER_COPY"
    PASTE = "TRIGGER_PASTE"
    PASTE_TERMINAL = "TRIGGER_PASTE_TERMINAL"
    UNKNOWN = "UNKNOWN"

class TriggerServer:
    """Unix socket server for receiving triggers."""

    def __init__(self, socket_path: str, callback: Callable):
        """
        Initialize the trigger server.

        Args:
            socket_path: Path to Unix socket
            callback: Function to call on trigger
        """

    async def start(self) -> None:
        """Start listening for triggers."""

    async def stop(self) -> None:
        """Stop the server."""
```

### config.py - Configuration

Type-safe configuration management.

```python
@dataclass
class AudioConfig:
    """Audio capture configuration."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 512
    silence_duration: float = 1.2
    max_recording_duration: float = 30.0
    min_speech_duration: float = 0.3

@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""
    threshold: float = 0.5
    min_silence_duration_ms: int = 100
    speech_pad_ms: int = 30

@dataclass
class TranscriptionConfig:
    """Transcription configuration."""
    model_size: str = "base"
    language: str = ""  # Auto-detect
    compute_type: str = "int8"
    beam_size: int = 5
    device: str = "cpu"

@dataclass
class PunctuationConfig:
    """Punctuation processing configuration."""
    enabled: bool = True
    capitalize_sentences: bool = True

@dataclass
class ClipboardConfig:
    """Clipboard configuration."""
    timeout: float = 2.0

@dataclass
class PasteConfig:
    """Auto-paste configuration."""
    enabled: bool = True
    timeout: float = 2.0
    delay_ms: int = 100
    preferred_tool: str = "auto"

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: str = "logs/stt-clipboard.log"

@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    socket_path: str = "/tmp/stt-clipboard.sock"

@dataclass
class Config:
    """Main application configuration."""
    audio: AudioConfig
    vad: VADConfig
    transcription: TranscriptionConfig
    punctuation: PunctuationConfig
    clipboard: ClipboardConfig
    paste: PasteConfig
    logging: LoggingConfig
    hotkey: HotkeyConfig

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            path: Path to config file

        Returns:
            Config instance
        """
```

### notifications.py - Desktop Notifications

Desktop notification support.

```python
def notify(title: str, message: str, urgency: str = "normal") -> bool:
    """
    Show a desktop notification.

    Args:
        title: Notification title
        message: Notification body
        urgency: low, normal, or critical

    Returns:
        True if successful
    """
```

## Type Definitions

Common types used across modules:

```python
from typing import TypeAlias
import numpy as np
import numpy.typing as npt

# Audio data type
AudioData: TypeAlias = npt.NDArray[np.float32]

# Callback types
TriggerCallback: TypeAlias = Callable[[TriggerType], Awaitable[None]]
```
