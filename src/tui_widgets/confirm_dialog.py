"""Confirmation dialog for TUI settings."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDialog(ModalScreen[bool]):
    """Modal dialog for confirming actions with unsaved changes."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Vertical {
        background: $surface;
        border: round $primary;
        padding: 1 2;
        width: 50;
        max-width: 80%;
        height: 12;
    }

    ConfirmDialog .dialog-title {
        text-style: bold;
        margin-bottom: 1;
        text-align: center;
        color: $text;
        width: 100%;
    }

    ConfirmDialog .dialog-message {
        margin-bottom: 1;
        text-align: center;
        color: $text-muted;
        width: 100%;
    }

    ConfirmDialog .dialog-buttons {
        height: 3;
        margin-top: 1;
        width: 100%;
        align: center middle;
    }

    ConfirmDialog Button {
        margin: 0 1;
        min-width: 12;
        height: 3;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "confirm", "Confirm"),
    ]

    def __init__(
        self,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_label: str = "Yes",
        cancel_label: str = "No",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.title_text = title
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Vertical():
            yield Label(self.title_text, classes="dialog-title")
            yield Label(self.message, classes="dialog-message")
            with Horizontal(classes="dialog-buttons"):
                yield Button(self.cancel_label, id="btn-cancel", variant="default")
                yield Button(self.confirm_label, id="btn-confirm", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(False)

    def action_confirm(self) -> None:
        """Confirm the dialog."""
        self.dismiss(True)


class RestartWarningDialog(ModalScreen[bool]):
    """Modal dialog warning that restart is required."""

    DEFAULT_CSS = """
    RestartWarningDialog {
        align: center middle;
    }

    RestartWarningDialog > Vertical {
        background: $surface;
        border: round $warning;
        padding: 1 2;
        width: 60;
        max-width: 90%;
        min-height: 16;
        max-height: 80%;
    }

    RestartWarningDialog .dialog-title {
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
        text-align: center;
        width: 100%;
    }

    RestartWarningDialog .dialog-message {
        margin-bottom: 0;
        text-align: center;
        color: $text-muted;
        width: 100%;
    }

    RestartWarningDialog .dialog-fields {
        margin: 1 0;
        padding: 1;
        height: auto;
        width: 100%;
        background: $surface-darken-1;
        border: round $surface-darken-2;
    }

    RestartWarningDialog .dialog-fields Label {
        color: $text;
        width: 100%;
    }

    RestartWarningDialog .dialog-buttons {
        height: 3;
        margin-top: 1;
        width: 100%;
        align: center middle;
    }

    RestartWarningDialog Button {
        margin: 0 1;
        min-width: 12;
        height: 3;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "save", "Save"),
    ]

    def __init__(
        self,
        changed_fields: list[str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.changed_fields = changed_fields

    def compose(self) -> ComposeResult:
        """Compose the restart warning dialog."""
        with Vertical():
            yield Label("Restart Required", classes="dialog-title")
            yield Label(
                "The following settings require restart:",
                classes="dialog-message",
            )
            with Vertical(classes="dialog-fields"):
                for field in self.changed_fields:
                    yield Label(f"  - {field}")
            yield Label(
                "Save changes anyway?",
                classes="dialog-message",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Save", id="btn-save", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(False)

    def action_save(self) -> None:
        """Save despite restart warning."""
        self.dismiss(True)
