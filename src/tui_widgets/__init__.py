"""TUI Widgets for STT Clipboard settings."""

from src.tui_widgets.confirm_dialog import ConfirmDialog, RestartWarningDialog
from src.tui_widgets.form_fields import (
    FieldValidation,
    FloatInput,
    FormField,
    NumberInput,
    SelectField,
    SwitchField,
    TextInput,
)
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

__all__ = [
    # Form fields
    "FieldValidation",
    "FormField",
    "NumberInput",
    "FloatInput",
    "SelectField",
    "SwitchField",
    "TextInput",
    # Section forms
    "AudioSection",
    "VADSection",
    "TranscriptionSection",
    "PunctuationSection",
    "ClipboardSection",
    "PasteSection",
    "LoggingSection",
    "HotkeySection",
    "HistorySection",
    # Dialogs
    "ConfirmDialog",
    "RestartWarningDialog",
]
