"""Settings screen for TUI configuration editor."""

from typing import Any

from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Rule, Static, TabbedContent, TabPane

from src.config import Config
from src.tui_widgets.confirm_dialog import ConfirmDialog, RestartWarningDialog
from src.tui_widgets.form_fields import FormField
from src.tui_widgets.section_forms import (
    AudioSection,
    ClipboardSection,
    ConfigSection,
    HistorySection,
    HotkeySection,
    LoggingSection,
    PasteSection,
    PunctuationSection,
    TranscriptionSection,
    VADSection,
)

# Responsive breakpoints
BREAKPOINT_COMPACT = 80
BREAKPOINT_WIDE = 120

# Fields that require application restart when changed
# Note: history-enabled and history-file can be hot-reloaded, no restart needed
RESTART_REQUIRED_FIELDS = [
    "audio-sample-rate",
    "audio-channels",
    "audio-blocksize",
    "transcription-model-size",
    "transcription-device",
    "transcription-compute-type",
    "transcription-download-root",
    "hotkey-enabled",
    "hotkey-socket-path",
]


class StatusBar(Static):
    """Status bar showing validation status."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $surface;
        padding: 0 1;
    }

    StatusBar .status-valid {
        color: $success;
    }

    StatusBar .status-error {
        color: $error;
    }

    StatusBar .status-modified {
        color: $warning;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._is_valid = True
        self._is_modified = False
        self._error_count = 0

    def set_status(self, is_valid: bool, is_modified: bool, error_count: int = 0) -> None:
        """Update status display."""
        self._is_valid = is_valid
        self._is_modified = is_modified
        self._error_count = error_count
        self._update_display()

    def _update_display(self) -> None:
        """Update the status bar text."""
        parts = []

        if self._is_modified:
            parts.append("[*] Modified")

        if not self._is_valid:
            parts.append(f"[!] {self._error_count} error(s)")
        else:
            parts.append("Valid")

        parts.append("| [*] = Requires restart")

        self.update(" | ".join(parts))


class SectionHeader(Static):
    """Header for a settings section within a grouped tab."""

    DEFAULT_CSS = """
    SectionHeader {
        background: $primary-darken-3;
        color: $text;
        padding: 0 1;
        margin: 1 0 0 0;
        text-style: bold;
        width: 100%;
    }
    """


class SettingsScreen(Screen):
    """Settings screen for editing configuration with grouped tabs."""

    DEFAULT_CSS = """
    SettingsScreen {
        background: $surface;
    }

    SettingsScreen #settings-content {
        width: 100%;
        height: 1fr;
        min-height: 10;
    }

    SettingsScreen TabbedContent {
        width: 100%;
        height: 1fr;
        min-height: 10;
    }

    SettingsScreen ContentSwitcher {
        width: 100%;
        height: 1fr;
        min-height: 10;
    }

    SettingsScreen TabPane {
        padding: 0;
        width: 100%;
        height: 1fr;
        min-height: 10;
    }

    SettingsScreen .tab-scroll {
        width: 100%;
        height: 1fr;
        min-height: 10;
        padding: 1;
    }

    SettingsScreen #button-bar {
        dock: bottom;
        height: auto;
        min-height: 3;
        width: 100%;
        background: $surface-darken-1;
        padding: 1;
    }

    SettingsScreen #button-bar Button {
        margin-left: 1;
        min-width: 12;
    }

    SettingsScreen #btn-reset {
        dock: left;
    }

    SettingsScreen #status-bar {
        width: 1fr;
        margin-right: 2;
    }

    SettingsScreen Rule {
        margin: 1 0;
        color: $primary-darken-2;
    }

    SettingsScreen SectionHeader {
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        margin: 1 0 0 0;
        text-style: bold;
        width: 100%;
    }

    SettingsScreen ConfigSection {
        width: 100%;
        height: auto;
        padding: 1;
    }

    SettingsScreen FormField {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    /* ===== RESPONSIVE: Compact mode (< 80 cols) ===== */
    SettingsScreen.-compact #button-bar {
        padding: 0;
        min-height: 2;
    }

    SettingsScreen.-compact #button-bar Button {
        min-width: 8;
        margin-left: 0;
    }

    SettingsScreen.-compact #status-bar {
        display: none;
    }

    SettingsScreen.-compact #btn-reset {
        display: none;
    }

    SettingsScreen.-compact .tab-scroll {
        padding: 0;
    }

    SettingsScreen.-compact SectionHeader {
        padding: 0;
        margin: 0;
    }

    SettingsScreen.-compact ConfigSection {
        padding: 0;
    }

    SettingsScreen.-compact Rule {
        display: none;
    }

    /* ===== RESPONSIVE: Wide mode (> 120 cols) ===== */
    SettingsScreen.-wide .tab-scroll {
        padding: 2;
    }

    SettingsScreen.-wide ConfigSection {
        padding: 1 2;
    }

    SettingsScreen.-wide #button-bar {
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
        Binding("ctrl+r", "reset", "Reset", show=True),
        Binding("1", "tab_1", "Audio", show=False),
        Binding("2", "tab_2", "Transcription", show=False),
        Binding("3", "tab_3", "Output", show=False),
        Binding("4", "tab_4", "System", show=False),
    ]

    def __init__(
        self,
        config: Config,
        config_path: str = "config/config.yaml",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.config_path = config_path
        self._original_config = config  # Keep reference for reset
        self._is_modified = False

    def compose(self) -> ComposeResult:
        """Compose the settings screen with grouped tabs."""
        yield Header()

        with Vertical(id="settings-content"):
            with TabbedContent(id="settings-tabs"):
                # Tab 1: Audio (Audio + VAD)
                with TabPane("Audio", id="tab-audio"):
                    with VerticalScroll(classes="tab-scroll"):
                        yield SectionHeader("Recording")
                        yield AudioSection(self.config.audio, id="section-audio")
                        yield Rule()
                        yield SectionHeader("Voice Detection (VAD)")
                        yield VADSection(self.config.vad, id="section-vad")

                # Tab 2: Transcription
                with TabPane("Transcription", id="tab-transcription"):
                    with VerticalScroll(classes="tab-scroll"):
                        yield TranscriptionSection(
                            self.config.transcription, id="section-transcription"
                        )

                # Tab 3: Output (Punctuation + Clipboard + Paste)
                with TabPane("Output", id="tab-output"):
                    with VerticalScroll(classes="tab-scroll"):
                        yield SectionHeader("Punctuation")
                        yield PunctuationSection(self.config.punctuation, id="section-punctuation")
                        yield Rule()
                        yield SectionHeader("Clipboard")
                        yield ClipboardSection(self.config.clipboard, id="section-clipboard")
                        yield Rule()
                        yield SectionHeader("Auto-Paste")
                        yield PasteSection(self.config.paste, id="section-paste")

                # Tab 4: System (Logging + Hotkey + History)
                with TabPane("System", id="tab-system"):
                    with VerticalScroll(classes="tab-scroll"):
                        yield SectionHeader("Logging")
                        yield LoggingSection(self.config.logging, id="section-logging")
                        yield Rule()
                        yield SectionHeader("Hotkey Trigger")
                        yield HotkeySection(self.config.hotkey, id="section-hotkey")
                        yield Rule()
                        yield SectionHeader("History")
                        yield HistorySection(self.config.history, id="section-history")

        with Horizontal(id="button-bar"):
            yield Button("Reset", id="btn-reset", variant="default")
            yield StatusBar(id="status-bar")
            yield Button("Cancel", id="btn-cancel", variant="default")
            yield Button("Save", id="btn-save", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._update_status()
        # Apply responsive layout based on initial size
        self._apply_responsive_layout(self.app.size.width)

    def on_resize(self, event: events.Resize) -> None:
        """Handle screen resize for responsive layout."""
        self._apply_responsive_layout(event.size.width)

    def _apply_responsive_layout(self, width: int) -> None:
        """Apply responsive CSS classes based on screen width."""
        self.remove_class("-compact", "-wide")

        if width < BREAKPOINT_COMPACT:
            self.add_class("-compact")
        elif width >= BREAKPOINT_WIDE:
            self.add_class("-wide")

    def on_form_field_changed(self, event: FormField.Changed) -> None:
        """Handle form field changes."""
        self._is_modified = True
        self._update_status()

    def _update_status(self) -> None:
        """Update the status bar."""
        errors = self._validate_all()
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_status(
            is_valid=len(errors) == 0,
            is_modified=self._is_modified,
            error_count=len(errors),
        )

        # Enable/disable save button based on validation
        save_btn = self.query_one("#btn-save", Button)
        save_btn.disabled = len(errors) > 0

    def _validate_all(self) -> list[str]:
        """Validate all sections and return errors."""
        errors: list[str] = []
        # Query each section type explicitly
        for section in [
            self._get_section(AudioSection),
            self._get_section(VADSection),
            self._get_section(TranscriptionSection),
            self._get_section(PunctuationSection),
            self._get_section(ClipboardSection),
            self._get_section(PasteSection),
            self._get_section(LoggingSection),
            self._get_section(HotkeySection),
            self._get_section(HistorySection),
        ]:
            if section is not None:
                errors.extend(section.validate_all())
        return errors

    def _get_section(self, section_type: type[ConfigSection]) -> ConfigSection | None:
        """Get a section by type, returning None if not mounted."""
        try:
            return self.query_one(section_type)
        except Exception:  # noqa: S110  # nosec B110 - Section may not be mounted yet
            return None

    def _get_current_config(self) -> Config:
        """Build a Config object from current form values."""
        audio_section = self.query_one(AudioSection)
        vad_section = self.query_one(VADSection)
        transcription_section = self.query_one(TranscriptionSection)
        punctuation_section = self.query_one(PunctuationSection)
        clipboard_section = self.query_one(ClipboardSection)
        paste_section = self.query_one(PasteSection)
        logging_section = self.query_one(LoggingSection)
        hotkey_section = self.query_one(HotkeySection)
        history_section = self.query_one(HistorySection)

        return Config(
            audio=audio_section.get_config(),
            vad=vad_section.get_config(),
            transcription=transcription_section.get_config(),
            punctuation=punctuation_section.get_config(),
            clipboard=clipboard_section.get_config(),
            paste=paste_section.get_config(),
            logging=logging_section.get_config(),
            hotkey=hotkey_section.get_config(),
            history=history_section.get_config(),
        )

    async def _save_config(self) -> Config | None:
        """Save the configuration to file.

        Returns:
            The new config if saved successfully, None otherwise.
        """
        try:
            new_config = self._get_current_config()

            # Validate the config using the Config.validate() method
            new_config.validate()

            # Save to YAML
            new_config.save_to_yaml(self.config_path)

            return new_config
        except ValueError as e:
            self.notify(f"Validation error: {e}", severity="error")
            return None
        except Exception as e:
            self.notify(f"Save error: {e}", severity="error")
            return None

    def _get_actual_restart_fields(self) -> list[str]:
        """Compare current config with original and return fields that actually changed.

        Note: History fields are not included as they can be hot-reloaded.
        """
        current = self._get_current_config()
        original = self._original_config
        changed: list[str] = []

        # Check audio fields
        if current.audio.sample_rate != original.audio.sample_rate:
            changed.append("audio-sample-rate")
        if current.audio.channels != original.audio.channels:
            changed.append("audio-channels")
        if current.audio.blocksize != original.audio.blocksize:
            changed.append("audio-blocksize")

        # Check transcription fields
        if current.transcription.model_size != original.transcription.model_size:
            changed.append("transcription-model-size")
        if current.transcription.device != original.transcription.device:
            changed.append("transcription-device")
        if current.transcription.compute_type != original.transcription.compute_type:
            changed.append("transcription-compute-type")
        if current.transcription.download_root != original.transcription.download_root:
            changed.append("transcription-download-root")

        # Note: history fields can be hot-reloaded, no restart needed

        # Check hotkey fields
        if current.hotkey.enabled != original.hotkey.enabled:
            changed.append("hotkey-enabled")
        if current.hotkey.socket_path != original.hotkey.socket_path:
            changed.append("hotkey-socket-path")

        return changed

    @work
    async def action_save(self) -> None:
        """Save settings."""
        if not self._is_modified:
            self.app.pop_screen()
            return

        # Check for restart-required fields by comparing actual values
        actual_restart_fields = self._get_actual_restart_fields()
        if actual_restart_fields:
            # Show restart warning dialog
            field_names = [f.replace("-", " ").title() for f in actual_restart_fields]
            result = await self.app.push_screen_wait(
                RestartWarningDialog(changed_fields=field_names)
            )
            if not result:
                return

        # Save configuration
        new_config = await self._save_config()
        if new_config:
            # Hot-reload settings that don't require restart
            if hasattr(self.app, "reload_config"):
                self.app.reload_config(new_config)
            self.notify("Settings saved successfully", severity="information")
            self.app.pop_screen()
        # Error notification is handled in _save_config

    @work
    async def action_cancel(self) -> None:
        """Cancel and close settings."""
        if self._is_modified:
            # Show confirmation dialog
            result = await self.app.push_screen_wait(
                ConfirmDialog(
                    title="Unsaved Changes",
                    message="You have unsaved changes. Discard them?",
                    confirm_label="Discard",
                    cancel_label="Keep Editing",
                )
            )
            if not result:
                return

        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-cancel":
            self.action_cancel()
        elif event.button.id == "btn-reset":
            self.action_reset()

    @work
    async def action_reset(self) -> None:
        """Reset all settings to original values."""
        if not self._is_modified:
            self.notify("No changes to reset", severity="information")
            return

        result = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Reset Settings",
                message="Reset all settings to their original values?",
                confirm_label="Reset",
                cancel_label="Cancel",
            )
        )
        if result:
            # Reload the screen with original config
            self.app.pop_screen()
            self.app.push_screen(SettingsScreen(self._original_config, self.config_path))
            self.notify("Settings reset", severity="information")

    def action_tab_1(self) -> None:
        """Switch to Audio tab."""
        self._switch_tab("tab-audio")

    def action_tab_2(self) -> None:
        """Switch to Transcription tab."""
        self._switch_tab("tab-transcription")

    def action_tab_3(self) -> None:
        """Switch to Output tab."""
        self._switch_tab("tab-output")

    def action_tab_4(self) -> None:
        """Switch to System tab."""
        self._switch_tab("tab-system")

    def _switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = tab_id
        except Exception:  # noqa: S110  # nosec B110 - Tab may not be mounted yet
            pass
