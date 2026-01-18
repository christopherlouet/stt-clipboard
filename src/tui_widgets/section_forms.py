"""Section forms for TUI settings."""

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Static

from src.config import (
    AudioConfig,
    ClipboardConfig,
    HistoryConfig,
    HotkeyConfig,
    LoggingConfig,
    PasteConfig,
    PunctuationConfig,
    TranscriptionConfig,
    VADConfig,
)
from src.tui_widgets.form_fields import (
    FloatInput,
    NumberInput,
    SelectField,
    SwitchField,
    TextInput,
)


class ConfigSection(Static):
    """Base class for configuration sections."""

    DEFAULT_CSS = """
    ConfigSection {
        height: auto;
        padding: 1;
        width: 100%;
        margin-bottom: 1;
    }
    """

    def get_values(self) -> dict[str, Any]:
        """Get all field values as a dictionary."""
        raise NotImplementedError

    def set_values(self, values: dict[str, Any]) -> None:
        """Set field values from a dictionary."""
        raise NotImplementedError

    def validate_all(self) -> list[str]:
        """Validate all fields and return list of error messages."""
        errors: list[str] = []
        # Query each specific field type to get proper typing
        for num_field in list(self.query(NumberInput)):
            validation = num_field.validate()
            if not validation.is_valid:
                errors.append(validation.error_message)
        for float_field in list(self.query(FloatInput)):
            validation = float_field.validate()
            if not validation.is_valid:
                errors.append(validation.error_message)
        for select_field in list(self.query(SelectField)):
            validation = select_field.validate()
            if not validation.is_valid:
                errors.append(validation.error_message)
        for text_field in list(self.query(TextInput)):
            validation = text_field.validate()
            if not validation.is_valid:
                errors.append(validation.error_message)
        return errors


class AudioSection(ConfigSection):
    """Audio configuration section."""

    def __init__(self, config: AudioConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose audio settings fields."""
        yield SelectField(
            label="Sample Rate",
            field_id="audio-sample-rate",
            options=[
                ("8000 Hz", "8000"),
                ("16000 Hz (Recommended)", "16000"),
                ("22050 Hz", "22050"),
                ("44100 Hz", "44100"),
                ("48000 Hz", "48000"),
            ],
            default=str(self.config.sample_rate),
            help_text="Audio sampling rate",
            requires_restart=True,
        )
        yield SelectField(
            label="Channels",
            field_id="audio-channels",
            options=[
                ("Mono (1)", "1"),
                ("Stereo (2)", "2"),
            ],
            default=str(self.config.channels),
            help_text="Audio channels",
            requires_restart=True,
        )
        yield FloatInput(
            label="Silence Duration",
            field_id="audio-silence-duration",
            default=self.config.silence_duration,
            min_value=0.1,
            max_value=10.0,
            help_text="Seconds of silence to stop recording",
        )
        yield FloatInput(
            label="Min Speech Duration",
            field_id="audio-min-speech-duration",
            default=self.config.min_speech_duration,
            min_value=0.1,
            max_value=5.0,
            help_text="Minimum seconds of speech to record",
        )
        yield NumberInput(
            label="Max Recording Duration",
            field_id="audio-max-recording-duration",
            default=self.config.max_recording_duration,
            min_value=1,
            max_value=300,
            help_text="Maximum recording length (seconds)",
        )
        yield NumberInput(
            label="Block Size",
            field_id="audio-blocksize",
            default=self.config.blocksize,
            min_value=64,
            max_value=4096,
            help_text="Audio buffer block size",
            requires_restart=True,
        )

    def get_values(self) -> dict[str, Any]:
        """Get audio config values."""
        selects = list(self.query(SelectField))
        floats = list(self.query(FloatInput))
        numbers = list(self.query(NumberInput))

        return {
            "sample_rate": int(selects[0].value) if selects else 16000,
            "channels": int(selects[1].value) if len(selects) > 1 else 1,
            "silence_duration": floats[0].value if floats else 1.2,
            "min_speech_duration": floats[1].value if len(floats) > 1 else 0.3,
            "max_recording_duration": numbers[0].value if numbers else 30,
            "blocksize": numbers[1].value if len(numbers) > 1 else 512,
        }

    def get_config(self) -> AudioConfig:
        """Get AudioConfig from form values."""
        values = self.get_values()
        return AudioConfig(
            sample_rate=values["sample_rate"],
            channels=values["channels"],
            silence_duration=values["silence_duration"],
            min_speech_duration=values["min_speech_duration"],
            max_recording_duration=values["max_recording_duration"],
            blocksize=values["blocksize"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set audio config values."""
        pass


class VADSection(ConfigSection):
    """VAD configuration section."""

    def __init__(self, config: VADConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose VAD settings fields."""
        yield FloatInput(
            label="Threshold",
            field_id="vad-threshold",
            default=self.config.threshold,
            min_value=0.0,
            max_value=1.0,
            help_text="Speech detection sensitivity (0-1)",
        )
        yield NumberInput(
            label="Min Silence Duration (ms)",
            field_id="vad-min-silence-duration-ms",
            default=self.config.min_silence_duration_ms,
            min_value=0,
            max_value=2000,
            help_text="Minimum silence to detect pause",
        )
        yield NumberInput(
            label="Speech Pad (ms)",
            field_id="vad-speech-pad-ms",
            default=self.config.speech_pad_ms,
            min_value=0,
            max_value=1000,
            help_text="Padding added around speech",
        )

    def get_values(self) -> dict[str, Any]:
        """Get VAD config values."""
        floats = list(self.query(FloatInput))
        numbers = list(self.query(NumberInput))

        return {
            "threshold": floats[0].value if floats else 0.5,
            "min_silence_duration_ms": numbers[0].value if numbers else 300,
            "speech_pad_ms": numbers[1].value if len(numbers) > 1 else 300,
        }

    def get_config(self) -> VADConfig:
        """Get VADConfig from form values."""
        values = self.get_values()
        return VADConfig(
            threshold=values["threshold"],
            min_silence_duration_ms=values["min_silence_duration_ms"],
            speech_pad_ms=values["speech_pad_ms"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set VAD config values."""
        pass


class TranscriptionSection(ConfigSection):
    """Transcription configuration section."""

    def __init__(self, config: TranscriptionConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose transcription settings fields."""
        yield SelectField(
            label="Model Size",
            field_id="transcription-model-size",
            options=[
                ("Tiny (fastest)", "tiny"),
                ("Base (recommended)", "base"),
                ("Small", "small"),
                ("Medium", "medium"),
                ("Large (most accurate)", "large"),
            ],
            default=self.config.model_size,
            help_text="Whisper model size",
            requires_restart=True,
        )
        yield SelectField(
            label="Language",
            field_id="transcription-language",
            options=[
                (f"{code.upper()} - {name}", code)
                for code, name in [
                    ("fr", "French"),
                    ("en", "English"),
                    ("de", "German"),
                    ("es", "Spanish"),
                    ("it", "Italian"),
                ]
            ],
            default=self.config.language,
            help_text="Transcription language",
            allow_blank=True,
            blank_label="Auto-detect",
        )
        yield SelectField(
            label="Device",
            field_id="transcription-device",
            options=[
                ("CPU", "cpu"),
                ("CUDA (GPU)", "cuda"),
            ],
            default=self.config.device,
            help_text="Compute device",
            requires_restart=True,
        )
        yield SelectField(
            label="Compute Type",
            field_id="transcription-compute-type",
            options=[
                ("int8 (fastest)", "int8"),
                ("int16", "int16"),
                ("float16", "float16"),
                ("float32 (most accurate)", "float32"),
            ],
            default=self.config.compute_type,
            help_text="Model quantization",
            requires_restart=True,
        )
        yield NumberInput(
            label="Beam Size",
            field_id="transcription-beam-size",
            default=self.config.beam_size,
            min_value=1,
            max_value=10,
            help_text="Search beam width",
        )
        yield NumberInput(
            label="Best Of",
            field_id="transcription-best-of",
            default=self.config.best_of,
            min_value=1,
            max_value=10,
            help_text="Candidates to consider",
        )
        yield FloatInput(
            label="Temperature",
            field_id="transcription-temperature",
            default=self.config.temperature,
            min_value=0.0,
            max_value=1.0,
            help_text="Sampling temperature",
        )
        yield TextInput(
            label="Download Root",
            field_id="transcription-download-root",
            default=self.config.download_root,
            help_text="Model download directory",
            requires_restart=True,
        )
        yield SwitchField(
            label="Streaming Enabled",
            field_id="transcription-streaming-enabled",
            default=self.config.streaming_enabled,
            help_text="Enable streaming output",
        )

    def get_values(self) -> dict[str, Any]:
        """Get transcription config values."""
        selects = list(self.query(SelectField))
        numbers = list(self.query(NumberInput))
        floats = list(self.query(FloatInput))
        texts = list(self.query(TextInput))
        switches = list(self.query(SwitchField))

        return {
            "model_size": selects[0].value if selects else "tiny",
            "language": selects[1].value if len(selects) > 1 else "",
            "device": selects[2].value if len(selects) > 2 else "cpu",
            "compute_type": selects[3].value if len(selects) > 3 else "int8",
            "beam_size": numbers[0].value if numbers else 1,
            "best_of": numbers[1].value if len(numbers) > 1 else 1,
            "temperature": floats[0].value if floats else 0.0,
            "download_root": texts[0].value if texts else "./models",
            "streaming_enabled": switches[0].value if switches else False,
        }

    def get_config(self) -> TranscriptionConfig:
        """Get TranscriptionConfig from form values."""
        values = self.get_values()
        return TranscriptionConfig(
            model_size=values["model_size"],
            language=values["language"],
            device=values["device"],
            compute_type=values["compute_type"],
            beam_size=values["beam_size"],
            best_of=values["best_of"],
            temperature=values["temperature"],
            download_root=values["download_root"],
            streaming_enabled=values["streaming_enabled"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set transcription config values."""
        pass


class PunctuationSection(ConfigSection):
    """Punctuation configuration section."""

    def __init__(self, config: PunctuationConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose punctuation settings fields."""
        yield SwitchField(
            label="Enabled",
            field_id="punctuation-enabled",
            default=self.config.enabled,
            help_text="Enable punctuation processing",
        )
        yield SwitchField(
            label="French Spacing",
            field_id="punctuation-french-spacing",
            default=self.config.french_spacing,
            help_text="Add space before ? ! : ; (French style)",
        )

    def get_values(self) -> dict[str, Any]:
        """Get punctuation config values."""
        switches = list(self.query(SwitchField))
        return {
            "enabled": switches[0].value if switches else True,
            "french_spacing": switches[1].value if len(switches) > 1 else True,
        }

    def get_config(self) -> PunctuationConfig:
        """Get PunctuationConfig from form values."""
        values = self.get_values()
        return PunctuationConfig(
            enabled=values["enabled"],
            french_spacing=values["french_spacing"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set punctuation config values."""
        pass


class ClipboardSection(ConfigSection):
    """Clipboard configuration section."""

    def __init__(self, config: ClipboardConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose clipboard settings fields."""
        yield SwitchField(
            label="Enabled",
            field_id="clipboard-enabled",
            default=self.config.enabled,
            help_text="Copy transcription to clipboard",
        )
        yield FloatInput(
            label="Timeout",
            field_id="clipboard-timeout",
            default=self.config.timeout,
            min_value=0.1,
            max_value=30.0,
            help_text="Clipboard operation timeout (seconds)",
        )
        yield NumberInput(
            label="Max Retries",
            field_id="clipboard-max-retries",
            default=self.config.max_retries,
            min_value=0,
            max_value=10,
            help_text="Retry attempts on failure",
        )
        yield FloatInput(
            label="Backoff Base",
            field_id="clipboard-backoff-base",
            default=self.config.backoff_base,
            min_value=0.01,
            max_value=5.0,
            help_text="Exponential backoff base (seconds)",
        )
        yield FloatInput(
            label="Max Delay",
            field_id="clipboard-max-delay",
            default=self.config.max_delay,
            min_value=0.1,
            max_value=30.0,
            help_text="Maximum delay between retries",
        )

    def get_values(self) -> dict[str, Any]:
        """Get clipboard config values."""
        switches = list(self.query(SwitchField))
        floats = list(self.query(FloatInput))
        numbers = list(self.query(NumberInput))

        return {
            "enabled": switches[0].value if switches else True,
            "timeout": floats[0].value if floats else 2.0,
            "max_retries": numbers[0].value if numbers else 3,
            "backoff_base": floats[1].value if len(floats) > 1 else 0.1,
            "max_delay": floats[2].value if len(floats) > 2 else 2.0,
        }

    def get_config(self) -> ClipboardConfig:
        """Get ClipboardConfig from form values."""
        values = self.get_values()
        return ClipboardConfig(
            enabled=values["enabled"],
            timeout=values["timeout"],
            max_retries=values["max_retries"],
            backoff_base=values["backoff_base"],
            max_delay=values["max_delay"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set clipboard config values."""
        pass


class PasteSection(ConfigSection):
    """Paste configuration section."""

    def __init__(self, config: PasteConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose paste settings fields."""
        yield SwitchField(
            label="Enabled",
            field_id="paste-enabled",
            default=self.config.enabled,
            help_text="Enable auto-paste after copy",
        )
        yield FloatInput(
            label="Timeout",
            field_id="paste-timeout",
            default=self.config.timeout,
            min_value=0.1,
            max_value=30.0,
            help_text="Paste operation timeout (seconds)",
        )
        yield NumberInput(
            label="Delay (ms)",
            field_id="paste-delay-ms",
            default=self.config.delay_ms,
            min_value=0,
            max_value=2000,
            help_text="Delay between copy and paste",
        )
        yield SelectField(
            label="Preferred Tool",
            field_id="paste-preferred-tool",
            options=[
                ("Auto (detect best)", "auto"),
                ("xdotool (X11)", "xdotool"),
                ("ydotool (universal)", "ydotool"),
                ("wtype (Wayland)", "wtype"),
            ],
            default=self.config.preferred_tool,
            help_text="Paste tool preference",
        )

    def get_values(self) -> dict[str, Any]:
        """Get paste config values."""
        switches = list(self.query(SwitchField))
        floats = list(self.query(FloatInput))
        numbers = list(self.query(NumberInput))
        selects = list(self.query(SelectField))

        return {
            "enabled": switches[0].value if switches else True,
            "timeout": floats[0].value if floats else 2.0,
            "delay_ms": numbers[0].value if numbers else 100,
            "preferred_tool": selects[0].value if selects else "auto",
        }

    def get_config(self) -> PasteConfig:
        """Get PasteConfig from form values."""
        values = self.get_values()
        return PasteConfig(
            enabled=values["enabled"],
            timeout=values["timeout"],
            delay_ms=values["delay_ms"],
            preferred_tool=values["preferred_tool"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set paste config values."""
        pass


class LoggingSection(ConfigSection):
    """Logging configuration section."""

    def __init__(self, config: LoggingConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose logging settings fields."""
        yield SelectField(
            label="Level",
            field_id="logging-level",
            options=[
                ("DEBUG (verbose)", "DEBUG"),
                ("INFO (recommended)", "INFO"),
                ("WARNING", "WARNING"),
                ("ERROR", "ERROR"),
                ("CRITICAL", "CRITICAL"),
            ],
            default=self.config.level,
            help_text="Log verbosity level",
        )
        yield TextInput(
            label="File",
            field_id="logging-file",
            default=self.config.file,
            help_text="Log file path",
        )

    def get_values(self) -> dict[str, Any]:
        """Get logging config values."""
        selects = list(self.query(SelectField))
        texts = list(self.query(TextInput))

        return {
            "level": selects[0].value if selects else "INFO",
            "file": texts[0].value if texts else "./logs/stt-clipboard.log",
        }

    def get_config(self) -> LoggingConfig:
        """Get LoggingConfig from form values."""
        values = self.get_values()
        return LoggingConfig(
            level=values["level"],
            file=values["file"],
            format=self.config.format,  # Keep existing format
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set logging config values."""
        pass


class HotkeySection(ConfigSection):
    """Hotkey configuration section."""

    def __init__(self, config: HotkeyConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose hotkey settings fields."""
        yield SwitchField(
            label="Enabled",
            field_id="hotkey-enabled",
            default=self.config.enabled,
            help_text="Enable hotkey trigger system",
        )
        yield TextInput(
            label="Socket Path",
            field_id="hotkey-socket-path",
            default=self.config.socket_path,
            help_text="Unix socket for trigger communication",
        )

    def get_values(self) -> dict[str, Any]:
        """Get hotkey config values."""
        switches = list(self.query(SwitchField))
        texts = list(self.query(TextInput))

        return {
            "enabled": switches[0].value if switches else False,
            "socket_path": texts[0].value if texts else "/tmp/stt-clipboard.sock",
        }

    def get_config(self) -> HotkeyConfig:
        """Get HotkeyConfig from form values."""
        values = self.get_values()
        return HotkeyConfig(
            enabled=values["enabled"],
            socket_path=values["socket_path"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set hotkey config values."""
        pass


class HistorySection(ConfigSection):
    """History configuration section."""

    def __init__(self, config: HistoryConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose history settings fields."""
        yield SwitchField(
            label="Enabled",
            field_id="history-enabled",
            default=self.config.enabled,
            help_text="Save transcription history",
        )
        yield TextInput(
            label="File",
            field_id="history-file",
            default=self.config.file,
            help_text="History file path",
        )
        yield NumberInput(
            label="Max Entries",
            field_id="history-max-entries",
            default=self.config.max_entries,
            min_value=1,
            max_value=10000,
            help_text="Maximum history entries",
        )
        yield SwitchField(
            label="Auto Save",
            field_id="history-auto-save",
            default=self.config.auto_save,
            help_text="Automatically save after each entry",
        )

    def get_values(self) -> dict[str, Any]:
        """Get history config values."""
        switches = list(self.query(SwitchField))
        texts = list(self.query(TextInput))
        numbers = list(self.query(NumberInput))

        return {
            "enabled": switches[0].value if switches else True,
            "file": texts[0].value if texts else "./data/history.json",
            "max_entries": numbers[0].value if numbers else 100,
            "auto_save": switches[1].value if len(switches) > 1 else True,
        }

    def get_config(self) -> HistoryConfig:
        """Get HistoryConfig from form values."""
        values = self.get_values()
        return HistoryConfig(
            enabled=values["enabled"],
            file=values["file"],
            max_entries=values["max_entries"],
            auto_save=values["auto_save"],
        )

    def set_values(self, values: dict[str, Any]) -> None:
        """Set history config values."""
        pass
