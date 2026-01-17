"""Configuration management for STT Clipboard."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from src.languages import SupportedLanguage


@dataclass
class AudioConfig:
    """Audio capture configuration."""

    sample_rate: int = 16000
    channels: int = 1
    silence_duration: float = 1.2
    min_speech_duration: float = 0.3
    max_recording_duration: int = 30
    blocksize: int = 512


@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""

    threshold: float = 0.5
    min_silence_duration_ms: int = 300
    speech_pad_ms: int = 300


@dataclass
class TranscriptionConfig:
    """Transcription configuration."""

    model_size: str = "tiny"
    language: str = "fr"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 1
    best_of: int = 1
    temperature: float = 0.0
    download_root: str = "./models"


@dataclass
class PunctuationConfig:
    """Punctuation post-processing configuration."""

    enabled: bool = True
    french_spacing: bool = True


@dataclass
class ClipboardConfig:
    """Clipboard configuration."""

    enabled: bool = True
    timeout: float = 2.0


@dataclass
class PasteConfig:
    """Auto-paste configuration."""

    enabled: bool = True
    timeout: float = 2.0
    delay_ms: int = 100  # Delay between copy and paste (milliseconds)
    preferred_tool: str = "auto"  # "auto", "xdotool", "ydotool", "wtype"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = "./logs/stt-clipboard.log"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""

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

        # Language validation (empty string means auto-detect)
        if self.transcription.language:
            valid_languages = SupportedLanguage.all_codes()
            if self.transcription.language not in valid_languages:
                raise ValueError(
                    f"Invalid language: {self.transcription.language}. "
                    f"Must be one of {valid_languages} or empty for auto-detect"
                )

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
