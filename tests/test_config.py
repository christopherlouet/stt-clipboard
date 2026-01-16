#!/usr/bin/env python3
"""Tests for configuration module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import (
    AudioConfig,
    ClipboardConfig,
    Config,
    HotkeyConfig,
    LoggingConfig,
    PasteConfig,
    PunctuationConfig,
    TranscriptionConfig,
    VADConfig,
)


class TestAudioConfig:
    """Tests for AudioConfig dataclass."""

    def test_default_values(self):
        """Test default values for AudioConfig."""
        config = AudioConfig()

        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.silence_duration == 1.2
        assert config.min_speech_duration == 0.3
        assert config.max_recording_duration == 30
        assert config.blocksize == 512

    def test_custom_values(self):
        """Test custom values for AudioConfig."""
        config = AudioConfig(
            sample_rate=44100,
            channels=2,
            silence_duration=2.0,
            min_speech_duration=0.5,
            max_recording_duration=60,
            blocksize=1024,
        )

        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.silence_duration == 2.0
        assert config.min_speech_duration == 0.5
        assert config.max_recording_duration == 60
        assert config.blocksize == 1024


class TestVADConfig:
    """Tests for VADConfig dataclass."""

    def test_default_values(self):
        """Test default values for VADConfig."""
        config = VADConfig()

        assert config.threshold == 0.5
        assert config.min_silence_duration_ms == 300
        assert config.speech_pad_ms == 300

    def test_custom_values(self):
        """Test custom values for VADConfig."""
        config = VADConfig(
            threshold=0.7,
            min_silence_duration_ms=500,
            speech_pad_ms=400,
        )

        assert config.threshold == 0.7
        assert config.min_silence_duration_ms == 500
        assert config.speech_pad_ms == 400


class TestTranscriptionConfig:
    """Tests for TranscriptionConfig dataclass."""

    def test_default_values(self):
        """Test default values for TranscriptionConfig."""
        config = TranscriptionConfig()

        assert config.model_size == "tiny"
        assert config.language == "fr"
        assert config.device == "cpu"
        assert config.compute_type == "int8"
        assert config.beam_size == 1
        assert config.best_of == 1
        assert config.temperature == 0.0
        assert config.download_root == "./models"

    def test_custom_values(self):
        """Test custom values for TranscriptionConfig."""
        config = TranscriptionConfig(
            model_size="base",
            language="en",
            device="cuda",
            compute_type="float16",
            beam_size=5,
            best_of=3,
            temperature=0.2,
            download_root="/tmp/models",
        )

        assert config.model_size == "base"
        assert config.language == "en"
        assert config.device == "cuda"
        assert config.compute_type == "float16"
        assert config.beam_size == 5
        assert config.best_of == 3
        assert config.temperature == 0.2
        assert config.download_root == "/tmp/models"


class TestPunctuationConfig:
    """Tests for PunctuationConfig dataclass."""

    def test_default_values(self):
        """Test default values for PunctuationConfig."""
        config = PunctuationConfig()

        assert config.enabled is True
        assert config.french_spacing is True

    def test_custom_values(self):
        """Test custom values for PunctuationConfig."""
        config = PunctuationConfig(enabled=False, french_spacing=False)

        assert config.enabled is False
        assert config.french_spacing is False


class TestClipboardConfig:
    """Tests for ClipboardConfig dataclass."""

    def test_default_values(self):
        """Test default values for ClipboardConfig."""
        config = ClipboardConfig()

        assert config.enabled is True
        assert config.timeout == 2.0

    def test_custom_values(self):
        """Test custom values for ClipboardConfig."""
        config = ClipboardConfig(enabled=False, timeout=5.0)

        assert config.enabled is False
        assert config.timeout == 5.0


class TestPasteConfig:
    """Tests for PasteConfig dataclass."""

    def test_default_values(self):
        """Test default values for PasteConfig."""
        config = PasteConfig()

        assert config.enabled is True
        assert config.timeout == 2.0
        assert config.delay_ms == 100
        assert config.preferred_tool == "auto"

    def test_custom_values(self):
        """Test custom values for PasteConfig."""
        config = PasteConfig(
            enabled=False,
            timeout=3.0,
            delay_ms=200,
            preferred_tool="xdotool",
        )

        assert config.enabled is False
        assert config.timeout == 3.0
        assert config.delay_ms == 200
        assert config.preferred_tool == "xdotool"


class TestLoggingConfig:
    """Tests for LoggingConfig dataclass."""

    def test_default_values(self):
        """Test default values for LoggingConfig."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.file == "./logs/stt-clipboard.log"
        assert "{time:" in config.format

    def test_custom_values(self):
        """Test custom values for LoggingConfig."""
        config = LoggingConfig(
            level="DEBUG",
            file="/var/log/stt.log",
            format="{message}",
        )

        assert config.level == "DEBUG"
        assert config.file == "/var/log/stt.log"
        assert config.format == "{message}"


class TestHotkeyConfig:
    """Tests for HotkeyConfig dataclass."""

    def test_default_values(self):
        """Test default values for HotkeyConfig."""
        config = HotkeyConfig()

        assert config.enabled is False
        assert config.socket_path == "/tmp/stt-clipboard.sock"

    def test_custom_values(self):
        """Test custom values for HotkeyConfig."""
        config = HotkeyConfig(enabled=True, socket_path="/run/user/1000/stt.sock")

        assert config.enabled is True
        assert config.socket_path == "/run/user/1000/stt.sock"


class TestConfig:
    """Tests for main Config class."""

    def test_default_values(self):
        """Test default values for Config."""
        config = Config()

        assert isinstance(config.audio, AudioConfig)
        assert isinstance(config.vad, VADConfig)
        assert isinstance(config.transcription, TranscriptionConfig)
        assert isinstance(config.punctuation, PunctuationConfig)
        assert isinstance(config.clipboard, ClipboardConfig)
        assert isinstance(config.paste, PasteConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.hotkey, HotkeyConfig)

    def test_custom_sub_configs(self):
        """Test Config with custom sub-configs."""
        audio = AudioConfig(sample_rate=44100)
        config = Config(audio=audio)

        assert config.audio.sample_rate == 44100


class TestConfigFromYaml:
    """Tests for Config.from_yaml method."""

    def test_returns_default_when_file_not_exists(self):
        """Test that default config is returned when file doesn't exist."""
        config = Config.from_yaml("/nonexistent/path/config.yaml")

        # Should return default config
        assert config.audio.sample_rate == 16000

    def test_loads_from_yaml_file(self):
        """Test loading config from YAML file."""
        yaml_content = """
audio:
  sample_rate: 44100
  channels: 2
transcription:
  model_size: base
  language: en
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = Config.from_yaml(f.name)

            assert config.audio.sample_rate == 44100
            assert config.audio.channels == 2
            assert config.transcription.model_size == "base"
            assert config.transcription.language == "en"

            # Cleanup
            Path(f.name).unlink()

    def test_handles_empty_yaml_file(self):
        """Test loading from empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()

            config = Config.from_yaml(f.name)

            # Should use defaults
            assert config.audio.sample_rate == 16000

            Path(f.name).unlink()

    def test_handles_partial_yaml_file(self):
        """Test loading from partial YAML file."""
        yaml_content = """
audio:
  sample_rate: 22050
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = Config.from_yaml(f.name)

            # audio.sample_rate should be overridden
            assert config.audio.sample_rate == 22050
            # Other audio defaults should remain
            assert config.audio.channels == 1
            # Other sections should use defaults
            assert config.transcription.model_size == "tiny"

            Path(f.name).unlink()

    def test_uses_default_path_when_none(self):
        """Test that default path is used when config_path is None."""
        # This may fail if config/config.yaml doesn't exist
        # But if it does, it should load it
        config = Config.from_yaml(None)
        assert isinstance(config, Config)


class TestConfigValidate:
    """Tests for Config.validate method."""

    def test_valid_config_passes(self):
        """Test that valid config passes validation."""
        config = Config()
        # Should not raise
        config.validate()

    def test_invalid_sample_rate_fails(self):
        """Test that invalid sample rate fails validation."""
        config = Config(audio=AudioConfig(sample_rate=12345))

        with pytest.raises(ValueError, match="Invalid sample_rate"):
            config.validate()

    def test_valid_sample_rates(self):
        """Test that valid sample rates pass validation."""
        valid_rates = [8000, 16000, 22050, 44100, 48000]

        for rate in valid_rates:
            config = Config(audio=AudioConfig(sample_rate=rate))
            config.validate()  # Should not raise

    def test_invalid_channels_fails(self):
        """Test that invalid channels fails validation."""
        config = Config(audio=AudioConfig(channels=3))

        with pytest.raises(ValueError, match="Invalid channels"):
            config.validate()

    def test_negative_silence_duration_fails(self):
        """Test that negative silence duration fails validation."""
        config = Config(audio=AudioConfig(silence_duration=-1.0))

        with pytest.raises(ValueError, match="silence_duration must be positive"):
            config.validate()

    def test_zero_silence_duration_fails(self):
        """Test that zero silence duration fails validation."""
        config = Config(audio=AudioConfig(silence_duration=0))

        with pytest.raises(ValueError, match="silence_duration must be positive"):
            config.validate()

    def test_negative_max_recording_duration_fails(self):
        """Test that negative max recording duration fails validation."""
        config = Config(audio=AudioConfig(max_recording_duration=-1))

        with pytest.raises(ValueError, match="max_recording_duration must be positive"):
            config.validate()

    def test_vad_threshold_below_zero_fails(self):
        """Test that VAD threshold below 0 fails validation."""
        config = Config(vad=VADConfig(threshold=-0.1))

        with pytest.raises(ValueError, match="VAD threshold must be between 0 and 1"):
            config.validate()

    def test_vad_threshold_above_one_fails(self):
        """Test that VAD threshold above 1 fails validation."""
        config = Config(vad=VADConfig(threshold=1.5))

        with pytest.raises(ValueError, match="VAD threshold must be between 0 and 1"):
            config.validate()

    def test_invalid_model_size_fails(self):
        """Test that invalid model size fails validation."""
        config = Config(transcription=TranscriptionConfig(model_size="giant"))

        with pytest.raises(ValueError, match="Invalid model_size"):
            config.validate()

    def test_valid_model_sizes(self):
        """Test that valid model sizes pass validation."""
        valid_sizes = ["tiny", "base", "small", "medium", "large"]

        for size in valid_sizes:
            config = Config(transcription=TranscriptionConfig(model_size=size))
            config.validate()  # Should not raise

    def test_invalid_compute_type_fails(self):
        """Test that invalid compute type fails validation."""
        config = Config(transcription=TranscriptionConfig(compute_type="invalid"))

        with pytest.raises(ValueError, match="Invalid compute_type"):
            config.validate()

    def test_valid_compute_types(self):
        """Test that valid compute types pass validation."""
        valid_types = ["int8", "int16", "float16", "float32"]

        for ctype in valid_types:
            config = Config(transcription=TranscriptionConfig(compute_type=ctype))
            config.validate()  # Should not raise

    def test_beam_size_less_than_one_fails(self):
        """Test that beam size less than 1 fails validation."""
        config = Config(transcription=TranscriptionConfig(beam_size=0))

        with pytest.raises(ValueError, match="beam_size must be >= 1"):
            config.validate()

    def test_invalid_log_level_fails(self):
        """Test that invalid log level fails validation."""
        config = Config(logging=LoggingConfig(level="INVALID"))

        with pytest.raises(ValueError, match="Invalid logging level"):
            config.validate()

    def test_valid_log_levels(self):
        """Test that valid log levels pass validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = Config(logging=LoggingConfig(level=level))
            config.validate()  # Should not raise

    def test_case_insensitive_log_level(self):
        """Test that log level validation is case insensitive."""
        config = Config(logging=LoggingConfig(level="debug"))
        config.validate()  # Should not raise


class TestConfigToDict:
    """Tests for Config.to_dict method."""

    def test_converts_to_dict(self):
        """Test conversion to dictionary."""
        config = Config()
        result = config.to_dict()

        assert isinstance(result, dict)
        assert "audio" in result
        assert "vad" in result
        assert "transcription" in result
        assert "punctuation" in result
        assert "clipboard" in result
        assert "paste" in result
        assert "logging" in result
        assert "hotkey" in result

    def test_nested_structure(self):
        """Test that nested structure is correct."""
        config = Config(audio=AudioConfig(sample_rate=44100))
        result = config.to_dict()

        assert result["audio"]["sample_rate"] == 44100
        assert result["audio"]["channels"] == 1

    def test_all_fields_present(self):
        """Test that all fields are present in dict."""
        config = Config()
        result = config.to_dict()

        # Check audio fields
        assert "sample_rate" in result["audio"]
        assert "channels" in result["audio"]
        assert "silence_duration" in result["audio"]

        # Check transcription fields
        assert "model_size" in result["transcription"]
        assert "language" in result["transcription"]
        assert "device" in result["transcription"]


class TestConfigSaveToYaml:
    """Tests for Config.save_to_yaml method."""

    def test_saves_to_yaml_file(self):
        """Test saving config to YAML file."""
        config = Config(audio=AudioConfig(sample_rate=44100))

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_config.yaml"

            config.save_to_yaml(str(filepath))

            # Verify file was created
            assert filepath.exists()

            # Verify content
            with open(filepath) as f:
                loaded = yaml.safe_load(f)

            assert loaded["audio"]["sample_rate"] == 44100

    def test_creates_parent_directories(self):
        """Test that parent directories are created."""
        config = Config()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "deep" / "config.yaml"

            config.save_to_yaml(str(filepath))

            assert filepath.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
