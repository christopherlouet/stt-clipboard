"""Tests for TUI settings screen."""

import pytest

from src.config import (
    AudioConfig,
    ClipboardConfig,
    Config,
    HistoryConfig,
    HotkeyConfig,
    LoggingConfig,
    PasteConfig,
    PunctuationConfig,
    TranscriptionConfig,
    VADConfig,
)
from src.tui_settings import RESTART_REQUIRED_FIELDS, SectionHeader, SettingsScreen, StatusBar
from src.tui_widgets.confirm_dialog import ConfirmDialog, RestartWarningDialog
from src.tui_widgets.section_forms import (
    AudioSection,
    ClipboardSection,
    HistorySection,
    HotkeySection,
    LoggingSection,
    PasteSection,
    PunctuationSection,
    TranscriptionSection,
    VADSection,
)


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    return Config(
        audio=AudioConfig(
            sample_rate=16000,
            channels=1,
            blocksize=512,
            silence_duration=1.2,
            min_speech_duration=0.3,
            max_recording_duration=30,
        ),
        vad=VADConfig(
            threshold=0.5,
            min_silence_duration_ms=300,
            speech_pad_ms=300,
        ),
        transcription=TranscriptionConfig(
            model_size="tiny",
            language="",
            device="cpu",
            compute_type="int8",
            beam_size=5,
        ),
        punctuation=PunctuationConfig(
            enabled=True,
            french_spacing=True,
        ),
        clipboard=ClipboardConfig(
            enabled=True,
            timeout=2.0,
        ),
        paste=PasteConfig(
            enabled=False,
            preferred_tool="auto",
            timeout=2.0,
            delay_ms=100,
        ),
        hotkey=HotkeyConfig(
            socket_path="/tmp/test-stt-settings.sock",
        ),
        logging=LoggingConfig(
            level="INFO",
            format="{time:HH:mm:ss} | {level} | {message}",
            file="",
        ),
        history=HistoryConfig(
            enabled=False,
            file="",
            max_entries=100,
            auto_save=True,
        ),
    )


class TestSectionHeader:
    """Tests for SectionHeader widget."""

    class TestInitialization:
        """Tests for SectionHeader creation."""

        def test_should_create_section_header(self) -> None:
            """Test creating SectionHeader widget."""
            header = SectionHeader("Test Section")
            assert header is not None

        def test_should_have_default_css(self) -> None:
            """Test that SectionHeader has CSS defined."""
            assert SectionHeader.DEFAULT_CSS is not None
            assert "background" in SectionHeader.DEFAULT_CSS


class TestRestartRequiredFields:
    """Tests for restart required fields configuration."""

    def test_should_include_audio_sample_rate(self) -> None:
        """Test that audio sample rate is in restart required fields."""
        assert "audio-sample-rate" in RESTART_REQUIRED_FIELDS

    def test_should_include_audio_channels(self) -> None:
        """Test that audio channels is in restart required fields."""
        assert "audio-channels" in RESTART_REQUIRED_FIELDS

    def test_should_include_model_size(self) -> None:
        """Test that model size is in restart required fields."""
        assert "transcription-model-size" in RESTART_REQUIRED_FIELDS

    def test_should_include_compute_type(self) -> None:
        """Test that compute type is in restart required fields."""
        assert "transcription-compute-type" in RESTART_REQUIRED_FIELDS

    def test_should_not_include_history_enabled(self) -> None:
        """Test that history enabled is NOT in restart required fields (can be hot-reloaded)."""
        assert "history-enabled" not in RESTART_REQUIRED_FIELDS

    def test_should_not_include_history_file(self) -> None:
        """Test that history file is NOT in restart required fields (can be hot-reloaded)."""
        assert "history-file" not in RESTART_REQUIRED_FIELDS


class TestStatusBar:
    """Tests for StatusBar widget."""

    class TestInitialization:
        """Tests for StatusBar creation."""

        def test_should_create_status_bar(self) -> None:
            """Test creating StatusBar widget."""
            bar = StatusBar()
            assert bar._is_valid is True
            assert bar._is_modified is False
            assert bar._error_count == 0

    class TestSetStatus:
        """Tests for status updates."""

        def test_should_update_valid_status(self) -> None:
            """Test updating to valid status."""
            bar = StatusBar()
            bar.set_status(is_valid=True, is_modified=False, error_count=0)
            assert bar._is_valid is True
            assert bar._is_modified is False

        def test_should_update_modified_status(self) -> None:
            """Test updating to modified status."""
            bar = StatusBar()
            bar.set_status(is_valid=True, is_modified=True, error_count=0)
            assert bar._is_modified is True

        def test_should_update_error_count(self) -> None:
            """Test updating error count."""
            bar = StatusBar()
            bar.set_status(is_valid=False, is_modified=True, error_count=3)
            assert bar._is_valid is False
            assert bar._error_count == 3


class TestSettingsScreen:
    """Tests for SettingsScreen."""

    class TestInitialization:
        """Tests for SettingsScreen creation."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating SettingsScreen with config."""
            screen = SettingsScreen(test_config)
            assert screen.config == test_config
            assert screen.config_path == "config/config.yaml"

        def test_should_accept_custom_config_path(self, test_config: Config) -> None:
            """Test creating SettingsScreen with custom config path."""
            screen = SettingsScreen(test_config, config_path="/custom/path.yaml")
            assert screen.config_path == "/custom/path.yaml"

        def test_should_initialize_as_not_modified(self, test_config: Config) -> None:
            """Test that screen starts as not modified."""
            screen = SettingsScreen(test_config)
            assert screen._is_modified is False

        def test_should_have_get_actual_restart_fields_method(self, test_config: Config) -> None:
            """Test that get_actual_restart_fields method exists."""
            screen = SettingsScreen(test_config)
            assert hasattr(screen, "_get_actual_restart_fields")

    class TestBindings:
        """Tests for keyboard bindings."""

        def test_should_have_escape_binding(self, test_config: Config) -> None:
            """Test that escape binding exists."""
            screen = SettingsScreen(test_config)
            binding_keys = [b.key for b in screen.BINDINGS]
            assert "escape" in binding_keys

        def test_should_have_save_binding(self, test_config: Config) -> None:
            """Test that save binding exists."""
            screen = SettingsScreen(test_config)
            binding_keys = [b.key for b in screen.BINDINGS]
            assert "ctrl+s" in binding_keys

        def test_should_have_tab_number_bindings(self, test_config: Config) -> None:
            """Test that tab number bindings exist for 4 grouped tabs."""
            screen = SettingsScreen(test_config)
            binding_keys = [b.key for b in screen.BINDINGS]
            # Now only 4 tabs: Audio, Transcription, Output, System
            for i in range(1, 5):
                assert str(i) in binding_keys

        def test_should_have_reset_binding(self, test_config: Config) -> None:
            """Test that reset binding exists."""
            screen = SettingsScreen(test_config)
            binding_keys = [b.key for b in screen.BINDINGS]
            assert "ctrl+r" in binding_keys


class TestConfirmDialog:
    """Tests for ConfirmDialog."""

    class TestInitialization:
        """Tests for ConfirmDialog creation."""

        def test_should_create_with_defaults(self) -> None:
            """Test creating ConfirmDialog with default values."""
            dialog = ConfirmDialog()
            assert dialog.title_text == "Confirm"
            assert dialog.message == "Are you sure?"
            assert dialog.confirm_label == "Yes"
            assert dialog.cancel_label == "No"

        def test_should_create_with_custom_values(self) -> None:
            """Test creating ConfirmDialog with custom values."""
            dialog = ConfirmDialog(
                title="Custom Title",
                message="Custom message?",
                confirm_label="OK",
                cancel_label="Cancel",
            )
            assert dialog.title_text == "Custom Title"
            assert dialog.message == "Custom message?"
            assert dialog.confirm_label == "OK"
            assert dialog.cancel_label == "Cancel"

    class TestBindings:
        """Tests for dialog bindings."""

        def test_should_have_escape_binding(self) -> None:
            """Test that escape binding exists."""
            dialog = ConfirmDialog()
            binding_keys = [b[0] for b in dialog.BINDINGS]
            assert "escape" in binding_keys

        def test_should_have_enter_binding(self) -> None:
            """Test that enter binding exists."""
            dialog = ConfirmDialog()
            binding_keys = [b[0] for b in dialog.BINDINGS]
            assert "enter" in binding_keys


class TestRestartWarningDialog:
    """Tests for RestartWarningDialog."""

    class TestInitialization:
        """Tests for RestartWarningDialog creation."""

        def test_should_create_with_changed_fields(self) -> None:
            """Test creating RestartWarningDialog with changed fields."""
            dialog = RestartWarningDialog(changed_fields=["Model Size", "Device"])
            assert len(dialog.changed_fields) == 2
            assert "Model Size" in dialog.changed_fields
            assert "Device" in dialog.changed_fields


class TestSectionForms:
    """Tests for configuration section forms."""

    class TestAudioSection:
        """Tests for AudioSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating AudioSection with config."""
            section = AudioSection(test_config.audio)
            assert section.config == test_config.audio

    class TestVADSection:
        """Tests for VADSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating VADSection with config."""
            section = VADSection(test_config.vad)
            assert section.config == test_config.vad

    class TestTranscriptionSection:
        """Tests for TranscriptionSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating TranscriptionSection with config."""
            section = TranscriptionSection(test_config.transcription)
            assert section.config == test_config.transcription

    class TestPunctuationSection:
        """Tests for PunctuationSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating PunctuationSection with config."""
            section = PunctuationSection(test_config.punctuation)
            assert section.config == test_config.punctuation

    class TestClipboardSection:
        """Tests for ClipboardSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating ClipboardSection with config."""
            section = ClipboardSection(test_config.clipboard)
            assert section.config == test_config.clipboard

    class TestPasteSection:
        """Tests for PasteSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating PasteSection with config."""
            section = PasteSection(test_config.paste)
            assert section.config == test_config.paste

    class TestLoggingSection:
        """Tests for LoggingSection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating LoggingSection with config."""
            section = LoggingSection(test_config.logging)
            assert section.config == test_config.logging

    class TestHotkeySection:
        """Tests for HotkeySection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating HotkeySection with config."""
            section = HotkeySection(test_config.hotkey)
            assert section.config == test_config.hotkey

    class TestHistorySection:
        """Tests for HistorySection."""

        def test_should_create_with_config(self, test_config: Config) -> None:
            """Test creating HistorySection with config."""
            section = HistorySection(test_config.history)
            assert section.config == test_config.history


class TestSettingsImports:
    """Tests for settings module imports."""

    def test_should_import_settings_screen(self) -> None:
        """Test SettingsScreen import."""
        from src.tui_settings import SettingsScreen

        assert SettingsScreen is not None

    def test_should_import_status_bar(self) -> None:
        """Test StatusBar import."""
        from src.tui_settings import StatusBar

        assert StatusBar is not None

    def test_should_import_confirm_dialog(self) -> None:
        """Test ConfirmDialog import."""
        from src.tui_widgets import ConfirmDialog

        assert ConfirmDialog is not None

    def test_should_import_all_section_forms(self) -> None:
        """Test all section form imports."""
        from src.tui_widgets import (
            AudioSection,
            ClipboardSection,
            HistorySection,
            HotkeySection,
            LoggingSection,
            PasteSection,
            PunctuationSection,
            TranscriptionSection,
            VADSection,
        )

        assert AudioSection is not None
        assert VADSection is not None
        assert TranscriptionSection is not None
        assert PunctuationSection is not None
        assert ClipboardSection is not None
        assert PasteSection is not None
        assert LoggingSection is not None
        assert HotkeySection is not None
        assert HistorySection is not None


class TestSettingsScreenActions:
    """Tests for SettingsScreen action methods."""

    def test_should_have_action_reset_method(self, test_config: Config) -> None:
        """Test that action_reset method exists."""
        screen = SettingsScreen(test_config)
        assert hasattr(screen, "action_reset")
        assert callable(screen.action_reset)

    def test_should_store_original_config(self, test_config: Config) -> None:
        """Test that original config is stored for reset."""
        screen = SettingsScreen(test_config)
        assert screen._original_config == test_config

    def test_should_have_tab_switch_methods(self, test_config: Config) -> None:
        """Test that tab switch action methods exist."""
        screen = SettingsScreen(test_config)
        assert hasattr(screen, "action_tab_1")
        assert hasattr(screen, "action_tab_2")
        assert hasattr(screen, "action_tab_3")
        assert hasattr(screen, "action_tab_4")


class TestTUIIntegration:
    """Tests for TUI settings integration."""

    def test_should_have_settings_binding_in_tui(self) -> None:
        """Test that 'o' binding exists in main TUI."""
        from src.tui import STTApp

        binding_keys = [b[0] for b in STTApp.BINDINGS]
        assert "o" in binding_keys

    def test_should_have_action_settings_method(self, test_config: Config) -> None:
        """Test that action_settings method exists."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert hasattr(app, "action_settings")
        assert callable(app.action_settings)

    def test_should_store_config_path(self, test_config: Config) -> None:
        """Test that config_path is stored."""
        from src.tui import STTApp

        app = STTApp(test_config, config_path="/custom/path.yaml")
        assert app.config_path == "/custom/path.yaml"

    def test_should_initialize_stats_attributes(self, test_config: Config) -> None:
        """Test that stats attributes are initialized correctly."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert app._total_requests == 0
        assert app._successful == 0
        assert app._failed == 0
        assert app._total_audio == 0.0
        assert app._total_transcription == 0.0

    def test_stats_attributes_have_correct_types(self, test_config: Config) -> None:
        """Test that stats attributes have correct types."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert isinstance(app._total_requests, int)
        assert isinstance(app._successful, int)
        assert isinstance(app._failed, int)
        assert isinstance(app._total_audio, float)
        assert isinstance(app._total_transcription, float)


class TestStatsPanel:
    """Tests for StatsPanel widget."""

    def test_should_create_stats_panel(self) -> None:
        """Test creating StatsPanel widget."""
        from src.tui import StatsPanel

        panel = StatsPanel()
        assert panel.total_requests == 0
        assert panel.successful == 0
        assert panel.failed == 0
        assert panel.total_audio == 0.0
        assert panel.total_transcription == 0.0

    def test_should_update_stats(self) -> None:
        """Test updating stats."""
        from src.tui import StatsPanel

        panel = StatsPanel()
        panel.update_stats(
            total=10,
            successful=8,
            failed=2,
            audio_duration=45.5,
            transcription_time=12.3,
        )
        assert panel.total_requests == 10
        assert panel.successful == 8
        assert panel.failed == 2
        assert panel.total_audio == 45.5
        assert panel.total_transcription == 12.3

    def test_should_have_default_css(self) -> None:
        """Test that StatsPanel has CSS defined."""
        from src.tui import StatsPanel

        assert StatsPanel.DEFAULT_CSS is not None
        assert "background" in StatsPanel.DEFAULT_CSS


class TestStatusIndicator:
    """Tests for StatusIndicator widget."""

    def test_should_create_status_indicator(self) -> None:
        """Test creating StatusIndicator widget."""
        from src.tui import StatusIndicator

        indicator = StatusIndicator()
        assert indicator.status == "idle"

    def test_should_have_reactive_status(self) -> None:
        """Test that status is reactive."""
        from src.tui import StatusIndicator

        # Verify the reactive attribute exists on the class
        assert hasattr(StatusIndicator, "status")


class TestReloadConfig:
    """Tests for hot-reloading configuration."""

    def test_should_have_reload_config_method(self, test_config: Config) -> None:
        """Test that reload_config method exists."""
        from src.tui import STTApp

        app = STTApp(test_config)
        assert hasattr(app, "reload_config")
        assert callable(app.reload_config)

    def test_should_enable_history_on_reload(self, test_config: Config) -> None:
        """Test that history is enabled when reload_config is called with enabled=True."""
        from src.tui import STTApp

        # Start with history disabled
        test_config.history.enabled = False
        app = STTApp(test_config)
        assert app.history is None

        # Create new config with history enabled
        new_config = Config(
            audio=test_config.audio,
            vad=test_config.vad,
            transcription=test_config.transcription,
            punctuation=test_config.punctuation,
            clipboard=test_config.clipboard,
            paste=test_config.paste,
            hotkey=test_config.hotkey,
            logging=test_config.logging,
            history=HistoryConfig(
                enabled=True,
                file="./data/test_history.json",
                max_entries=50,
                auto_save=True,
            ),
        )

        # Reload config
        app.reload_config(new_config)

        # History should now be enabled
        assert app.history is not None
        assert app.config.history.enabled is True

    def test_should_disable_history_on_reload(self, test_config: Config) -> None:
        """Test that history is disabled when reload_config is called with enabled=False."""
        from src.tui import STTApp

        # Start with history enabled
        test_config.history.enabled = True
        test_config.history.file = "./data/test_history.json"
        app = STTApp(test_config)
        assert app.history is not None

        # Create new config with history disabled
        new_config = Config(
            audio=test_config.audio,
            vad=test_config.vad,
            transcription=test_config.transcription,
            punctuation=test_config.punctuation,
            clipboard=test_config.clipboard,
            paste=test_config.paste,
            hotkey=test_config.hotkey,
            logging=test_config.logging,
            history=HistoryConfig(
                enabled=False,
                file="",
                max_entries=100,
                auto_save=True,
            ),
        )

        # Reload config
        app.reload_config(new_config)

        # History should now be disabled
        assert app.history is None
        assert app.config.history.enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
