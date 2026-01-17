"""Configuration management for STT Clipboard.

This module provides type-safe configuration dataclasses for the STT Clipboard
service. Configuration can be loaded from YAML files or instantiated directly
with Python code.

Example:
    Load configuration from YAML file::

        config = Config.from_yaml("config/config.yaml")

    Create configuration programmatically::

        config = Config(
            transcription=TranscriptionConfig(model_size="base", language="fr"),
            audio=AudioConfig(silence_duration=1.5),
        )

    Validate and use configuration::

        config.validate()
        transcriber = WhisperTranscriber(config.transcription)
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class AudioConfig:
    """Audio capture configuration.

    Controls how audio is recorded from the microphone before transcription.
    The default values are optimized for speech recognition with Whisper.

    Attributes:
        sample_rate: Audio sample rate in Hz. Whisper expects 16000 Hz.
            Supported values: 8000, 16000, 22050, 44100, 48000.
        channels: Number of audio channels. Use 1 (mono) for speech recognition.
        silence_duration: Duration of silence (in seconds) before stopping recording.
            Lower values = faster response, higher values = better capture of pauses.
        min_speech_duration: Minimum speech duration (in seconds) to accept.
            Recordings shorter than this are discarded to avoid noise triggers.
        max_recording_duration: Maximum recording duration (in seconds) as a safety limit.
        blocksize: Number of samples per audio block. Smaller = lower latency.

    Example:
        ::

            audio_config = AudioConfig(
                sample_rate=16000,
                silence_duration=1.5,  # Stop after 1.5s silence
                max_recording_duration=60,  # Allow up to 60s recordings
            )
    """

    sample_rate: int = 16000
    channels: int = 1
    silence_duration: float = 1.2
    min_speech_duration: float = 0.3
    max_recording_duration: int = 30
    blocksize: int = 512


@dataclass
class VADConfig:
    """Voice Activity Detection (VAD) configuration.

    Controls the Silero VAD model parameters for detecting speech in audio.
    VAD helps distinguish speech from background noise.

    Attributes:
        threshold: Speech probability threshold (0.0 to 1.0).
            Higher = more strict (may miss quiet speech).
            Lower = more sensitive (may trigger on noise).
        min_silence_duration_ms: Minimum silence duration in milliseconds
            before considering speech has ended.
        speech_pad_ms: Padding in milliseconds added before and after
            detected speech segments.

    Example:
        ::

            vad_config = VADConfig(
                threshold=0.6,  # Stricter detection (less false positives)
            )
    """

    threshold: float = 0.5
    min_silence_duration_ms: int = 300
    speech_pad_ms: int = 300
    cache_enabled: bool = False  # Enable LRU cache for VAD results
    cache_size: int = 100  # Maximum number of cached audio chunks


@dataclass
class TranscriptionConfig:
    """Whisper transcription configuration.

    Controls the faster-whisper model parameters for speech-to-text conversion.

    Attributes:
        model_size: Whisper model size. Options: "tiny", "base", "small", "medium", "large".
            Larger models are more accurate but slower and use more memory.
            Recommended: "base" for good accuracy/speed balance.
        language: Language code for transcription. Empty string "" for auto-detection.
            Supported: "fr" (French), "en" (English), and other Whisper languages.
        device: Compute device. "cpu" or "cuda" (if GPU available).
        compute_type: Quantization type. "int8" for fastest CPU inference,
            "float16" for GPU, "float32" for maximum accuracy.
        beam_size: Beam search width. Higher = more accurate but slower.
            Use 1 for fastest inference, 5 for better accuracy.
        best_of: Number of candidates to generate. Higher = better quality.
        temperature: Sampling temperature. 0.0 = deterministic (recommended).
        download_root: Directory for downloading and caching Whisper models.

    Example:
        ::

            # Fast configuration for quick responses
            fast_config = TranscriptionConfig(
                model_size="tiny",
                beam_size=1,
                compute_type="int8",
            )

            # Accurate configuration for best quality
            accurate_config = TranscriptionConfig(
                model_size="base",
                beam_size=5,
                language="",  # Auto-detect
            )
    """

    model_size: str = "tiny"
    language: str = "fr"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 1
    best_of: int = 1
    temperature: float = 0.0
    download_root: str = "./models"
    warmup_enabled: bool = True  # Warmup model at startup for faster first transcription


@dataclass
class PunctuationConfig:
    """Punctuation post-processing configuration.

    Controls how transcribed text is processed for proper typography.

    Attributes:
        enabled: Whether to apply punctuation post-processing.
        french_spacing: Apply French typography rules (space before ? ! : ;).
            Automatically disabled for English when language is detected.

    Example:
        ::

            # Disable French spacing for English-only use
            punct_config = PunctuationConfig(french_spacing=False)
    """

    enabled: bool = True
    french_spacing: bool = True


@dataclass
class ClipboardConfig:
    """Clipboard configuration.

    Controls how transcribed text is copied to the system clipboard.

    Attributes:
        enabled: Whether to copy transcribed text to clipboard.
        timeout: Timeout in seconds for clipboard operations.

    Example:
        ::

            clipboard_config = ClipboardConfig(timeout=5.0)
    """

    enabled: bool = True
    timeout: float = 2.0


@dataclass
class PasteConfig:
    """Auto-paste configuration.

    Controls automatic pasting after copying text to clipboard.
    This feature simulates keyboard shortcuts (Ctrl+V or Ctrl+Shift+V).

    Attributes:
        enabled: Whether to enable auto-paste functionality.
        timeout: Timeout in seconds for paste operations.
        delay_ms: Delay in milliseconds between copy and paste operations.
            Allows clipboard to be ready before pasting.
        preferred_tool: Preferred paste tool. Options:
            - "auto": Auto-detect best available tool
            - "xdotool": Use xdotool (X11 only)
            - "ydotool": Use ydotool (works on Wayland, requires daemon)
            - "wtype": Use wtype (Wayland only, types text directly)

    Example:
        ::

            # Use ydotool for Wayland
            paste_config = PasteConfig(
                preferred_tool="ydotool",
                delay_ms=150,  # Longer delay for reliability
            )
    """

    enabled: bool = True
    timeout: float = 2.0
    delay_ms: int = 100
    preferred_tool: str = "auto"


@dataclass
class LoggingConfig:
    """Logging configuration.

    Controls application logging behavior.

    Attributes:
        level: Log level. Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
        file: Path to log file. Set to empty string to disable file logging.
        format: Loguru format string for log messages.

    Example:
        ::

            # Debug logging to custom file
            logging_config = LoggingConfig(
                level="DEBUG",
                file="./logs/debug.log",
            )
    """

    level: str = "INFO"
    file: str = "./logs/stt-clipboard.log"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )


@dataclass
class HotkeyConfig:
    """Hotkey/trigger configuration.

    Controls the Unix socket server for receiving trigger events from
    keyboard shortcuts or external scripts.

    Attributes:
        enabled: Whether to enable the trigger server in daemon mode.
        socket_path: Path to the Unix socket file.
            The socket is secured with 0600 permissions (owner-only access).

    Example:
        ::

            hotkey_config = HotkeyConfig(
                enabled=True,
                socket_path="/tmp/my-stt-service.sock",
            )

    Security Note:
        The Unix socket uses 0600 permissions to prevent unauthorized access.
        Only the socket owner can send trigger events or read responses.
    """

    enabled: bool = False
    # Unix socket in /tmp is standard practice, secured with 0600 permissions
    socket_path: str = "/tmp/stt-clipboard.sock"  # nosec B108


@dataclass
class Config:
    """Main configuration class."""

    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    punctuation: PunctuationConfig = field(default_factory=PunctuationConfig)
    clipboard: ClipboardConfig = field(default_factory=ClipboardConfig)
    paste: PasteConfig = field(default_factory=PasteConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)

    @classmethod
    def from_yaml(cls, config_path: str | None = None) -> "Config":
        """Load configuration from YAML file.

        Args:
            config_path: Path to config file. If None, uses default location.

        Returns:
            Config instance
        """
        if config_path is None:
            config_path = "config/config.yaml"

        config_file = Path(config_path)

        if not config_file.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Parse each section
        audio_data = data.get("audio", {})
        vad_data = data.get("vad", {})
        transcription_data = data.get("transcription", {})
        punctuation_data = data.get("punctuation", {})
        clipboard_data = data.get("clipboard", {})
        paste_data = data.get("paste", {})
        logging_data = data.get("logging", {})
        hotkey_data = data.get("hotkey", {})

        return cls(
            audio=AudioConfig(**audio_data),
            vad=VADConfig(**vad_data),
            transcription=TranscriptionConfig(**transcription_data),
            punctuation=PunctuationConfig(**punctuation_data),
            clipboard=ClipboardConfig(**clipboard_data),
            paste=PasteConfig(**paste_data),
            logging=LoggingConfig(**logging_data),
            hotkey=HotkeyConfig(**hotkey_data),
        )

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Audio validation
        if self.audio.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError(f"Invalid sample_rate: {self.audio.sample_rate}")

        if self.audio.channels not in [1, 2]:
            raise ValueError(f"Invalid channels: {self.audio.channels}")

        if self.audio.silence_duration <= 0:
            raise ValueError(f"silence_duration must be positive: {self.audio.silence_duration}")

        if self.audio.max_recording_duration <= 0:
            raise ValueError(
                f"max_recording_duration must be positive: {self.audio.max_recording_duration}"
            )

        # VAD validation
        if not 0 <= self.vad.threshold <= 1:
            raise ValueError(f"VAD threshold must be between 0 and 1: {self.vad.threshold}")

        # Transcription validation
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if self.transcription.model_size not in valid_models:
            raise ValueError(
                f"Invalid model_size: {self.transcription.model_size}. Must be one of {valid_models}"
            )

        valid_compute_types = ["int8", "int16", "float16", "float32"]
        if self.transcription.compute_type not in valid_compute_types:
            raise ValueError(
                f"Invalid compute_type: {self.transcription.compute_type}. Must be one of {valid_compute_types}"
            )

        if self.transcription.beam_size < 1:
            raise ValueError(f"beam_size must be >= 1: {self.transcription.beam_size}")

        # Logging validation
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {self.logging.level}. Must be one of {valid_levels}"
            )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of config
        """
        return {
            "audio": {
                "sample_rate": self.audio.sample_rate,
                "channels": self.audio.channels,
                "silence_duration": self.audio.silence_duration,
                "min_speech_duration": self.audio.min_speech_duration,
                "max_recording_duration": self.audio.max_recording_duration,
                "blocksize": self.audio.blocksize,
            },
            "vad": {
                "threshold": self.vad.threshold,
                "min_silence_duration_ms": self.vad.min_silence_duration_ms,
                "speech_pad_ms": self.vad.speech_pad_ms,
                "cache_enabled": self.vad.cache_enabled,
                "cache_size": self.vad.cache_size,
            },
            "transcription": {
                "model_size": self.transcription.model_size,
                "language": self.transcription.language,
                "device": self.transcription.device,
                "compute_type": self.transcription.compute_type,
                "beam_size": self.transcription.beam_size,
                "best_of": self.transcription.best_of,
                "temperature": self.transcription.temperature,
                "download_root": self.transcription.download_root,
                "warmup_enabled": self.transcription.warmup_enabled,
            },
            "punctuation": {
                "enabled": self.punctuation.enabled,
                "french_spacing": self.punctuation.french_spacing,
            },
            "clipboard": {
                "enabled": self.clipboard.enabled,
                "timeout": self.clipboard.timeout,
            },
            "paste": {
                "enabled": self.paste.enabled,
                "timeout": self.paste.timeout,
                "delay_ms": self.paste.delay_ms,
                "preferred_tool": self.paste.preferred_tool,
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "format": self.logging.format,
            },
            "hotkey": {
                "enabled": self.hotkey.enabled,
                "socket_path": self.hotkey.socket_path,
            },
        }

    def save_to_yaml(self, config_path: str) -> None:
        """Save configuration to YAML file.

        Args:
            config_path: Path to save config file
        """
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
