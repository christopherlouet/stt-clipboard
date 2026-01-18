"""Form field widgets for TUI settings."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Input, Label, Select, Static, Switch


@dataclass
class FieldValidation:
    """Validation result for a form field."""

    is_valid: bool
    error_message: str = ""


class FormField(Static):
    """Base class for form fields with label and validation."""

    DEFAULT_CSS = """
    FormField {
        height: auto;
        margin-bottom: 1;
        width: 100%;
    }

    FormField .field-label {
        width: auto;
        margin-bottom: 0;
        min-width: 20;
    }

    FormField .field-help {
        color: $text-muted;
        text-style: italic;
        margin-left: 1;
        width: 1fr;
    }

    FormField .field-error {
        color: $error;
        margin-left: 2;
        height: auto;
    }

    FormField .field-container {
        height: auto;
        width: 100%;
    }

    FormField .restart-warning {
        color: $warning;
        text-style: italic;
        margin-left: 1;
    }

    FormField Horizontal {
        height: auto;
        align: left middle;
    }

    /* ===== RESPONSIVE: Compact mode ===== */
    /* Hide help text on small screens to save space */
    SettingsScreen.-compact FormField .field-help {
        display: none;
    }

    SettingsScreen.-compact FormField .restart-warning {
        display: none;
    }

    SettingsScreen.-compact FormField .field-label {
        min-width: 15;
    }

    SettingsScreen.-compact FormField {
        margin-bottom: 0;
    }
    """

    class Changed(Message):
        """Message sent when field value changes."""

        def __init__(self, field: "FormField", value: Any) -> None:
            self.field = field
            self.value = value
            super().__init__()

    def __init__(
        self,
        label: str,
        field_id: str,
        help_text: str = "",
        requires_restart: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.label_text = label
        self.field_id = field_id
        self.help_text = help_text
        self.requires_restart = requires_restart
        self._error_message = ""

    @property
    def value(self) -> Any:
        """Get field value. Override in subclasses."""
        raise NotImplementedError

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set field value. Override in subclasses."""
        raise NotImplementedError

    def validate(self) -> FieldValidation:
        """Validate field value. Override in subclasses."""
        return FieldValidation(is_valid=True)

    def set_error(self, message: str) -> None:
        """Set error message on field."""
        self._error_message = message
        error_label = self.query_one(".field-error", Label)
        error_label.update(message)
        error_label.display = bool(message)

    def clear_error(self) -> None:
        """Clear error message."""
        self.set_error("")


class NumberInput(FormField):
    """Integer input field with validation."""

    DEFAULT_CSS = (
        FormField.DEFAULT_CSS
        + """
    NumberInput Input {
        width: 1fr;
        max-width: 20;
    }

    SettingsScreen.-compact NumberInput Input {
        max-width: 12;
    }
    """
    )

    def __init__(
        self,
        label: str,
        field_id: str,
        default: int = 0,
        min_value: int | None = None,
        max_value: int | None = None,
        help_text: str = "",
        requires_restart: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            label=label,
            field_id=field_id,
            help_text=help_text,
            requires_restart=requires_restart,
            **kwargs,
        )
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self._value = default

    def compose(self) -> ComposeResult:
        """Compose the number input field."""
        with Vertical(classes="field-container"):
            label_parts = [self.label_text]
            if self.requires_restart:
                label_parts.append(" [*]")
            yield Label("".join(label_parts), classes="field-label")
            with Horizontal():
                yield Input(
                    value=str(self.default),
                    placeholder="Enter number",
                    id=f"input-{self.field_id}",
                    type="integer",
                )
                if self.help_text:
                    yield Label(self.help_text, classes="field-help")
            yield Label("", classes="field-error")
            if self.requires_restart:
                yield Label("Requires restart", classes="restart-warning")

    @property
    def value(self) -> int:
        """Get current integer value."""
        return self._value

    @value.setter
    def value(self, new_value: int) -> None:
        """Set integer value."""
        self._value = new_value
        try:
            input_widget = self.query_one(f"#input-{self.field_id}", Input)
            input_widget.value = str(new_value)
        except Exception:  # noqa: S110  # nosec B110 - Widget may not be mounted yet
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        validation = self.validate()
        if validation.is_valid:
            self.clear_error()
            try:
                self._value = int(event.value)
                self.post_message(self.Changed(self, self._value))
            except ValueError:
                pass
        else:
            self.set_error(validation.error_message)

    def validate(self) -> FieldValidation:
        """Validate the number input."""
        try:
            input_widget = self.query_one(f"#input-{self.field_id}", Input)
            value_str = input_widget.value
        except Exception:
            return FieldValidation(is_valid=True)

        if not value_str:
            return FieldValidation(is_valid=False, error_message="Value required")

        try:
            value = int(value_str)
        except ValueError:
            return FieldValidation(is_valid=False, error_message="Must be an integer")

        if self.min_value is not None and value < self.min_value:
            return FieldValidation(
                is_valid=False, error_message=f"Minimum value is {self.min_value}"
            )

        if self.max_value is not None and value > self.max_value:
            return FieldValidation(
                is_valid=False, error_message=f"Maximum value is {self.max_value}"
            )

        return FieldValidation(is_valid=True)


class FloatInput(FormField):
    """Float input field with validation."""

    DEFAULT_CSS = (
        FormField.DEFAULT_CSS
        + """
    FloatInput Input {
        width: 1fr;
        max-width: 20;
    }

    SettingsScreen.-compact FloatInput Input {
        max-width: 12;
    }
    """
    )

    def __init__(
        self,
        label: str,
        field_id: str,
        default: float = 0.0,
        min_value: float | None = None,
        max_value: float | None = None,
        step: float = 0.1,
        help_text: str = "",
        requires_restart: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            label=label,
            field_id=field_id,
            help_text=help_text,
            requires_restart=requires_restart,
            **kwargs,
        )
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self._value = default

    def compose(self) -> ComposeResult:
        """Compose the float input field."""
        with Vertical(classes="field-container"):
            label_parts = [self.label_text]
            if self.requires_restart:
                label_parts.append(" [*]")
            yield Label("".join(label_parts), classes="field-label")
            with Horizontal():
                yield Input(
                    value=str(self.default),
                    placeholder="Enter decimal",
                    id=f"input-{self.field_id}",
                    type="number",
                )
                if self.help_text:
                    yield Label(self.help_text, classes="field-help")
            yield Label("", classes="field-error")
            if self.requires_restart:
                yield Label("Requires restart", classes="restart-warning")

    @property
    def value(self) -> float:
        """Get current float value."""
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        """Set float value."""
        self._value = new_value
        try:
            input_widget = self.query_one(f"#input-{self.field_id}", Input)
            input_widget.value = str(new_value)
        except Exception:  # noqa: S110  # nosec B110 - Widget may not be mounted yet
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        validation = self.validate()
        if validation.is_valid:
            self.clear_error()
            try:
                self._value = float(event.value)
                self.post_message(self.Changed(self, self._value))
            except ValueError:
                pass
        else:
            self.set_error(validation.error_message)

    def validate(self) -> FieldValidation:
        """Validate the float input."""
        try:
            input_widget = self.query_one(f"#input-{self.field_id}", Input)
            value_str = input_widget.value
        except Exception:
            return FieldValidation(is_valid=True)

        if not value_str:
            return FieldValidation(is_valid=False, error_message="Value required")

        try:
            value = float(value_str)
        except ValueError:
            return FieldValidation(is_valid=False, error_message="Must be a decimal number")

        if self.min_value is not None and value < self.min_value:
            return FieldValidation(
                is_valid=False, error_message=f"Minimum value is {self.min_value}"
            )

        if self.max_value is not None and value > self.max_value:
            return FieldValidation(
                is_valid=False, error_message=f"Maximum value is {self.max_value}"
            )

        return FieldValidation(is_valid=True)


class SelectField(FormField):
    """Select field with dropdown options."""

    DEFAULT_CSS = (
        FormField.DEFAULT_CSS
        + """
    SelectField Select {
        width: 1fr;
        max-width: 35;
    }

    SettingsScreen.-compact SelectField Select {
        max-width: 20;
    }
    """
    )

    def __init__(
        self,
        label: str,
        field_id: str,
        options: list[tuple[str, str]],
        default: str = "",
        help_text: str = "",
        requires_restart: bool = False,
        allow_blank: bool = False,
        blank_label: str = "(auto)",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            label=label,
            field_id=field_id,
            help_text=help_text,
            requires_restart=requires_restart,
            **kwargs,
        )
        self.options = options
        self.default = default
        self.allow_blank = allow_blank
        self.blank_label = blank_label
        self._value = default

    def compose(self) -> ComposeResult:
        """Compose the select field."""
        with Vertical(classes="field-container"):
            label_parts = [self.label_text]
            if self.requires_restart:
                label_parts.append(" [*]")
            yield Label("".join(label_parts), classes="field-label")
            with Horizontal():
                # Build options list
                select_options: list[tuple[str, str]] = []
                if self.allow_blank:
                    select_options.append((self.blank_label, ""))
                select_options.extend(self.options)

                yield Select(
                    options=select_options,
                    value=self.default if self.default else Select.BLANK,  # type: ignore[has-type]
                    id=f"select-{self.field_id}",
                    allow_blank=self.allow_blank,
                )
                if self.help_text:
                    yield Label(self.help_text, classes="field-help")
            yield Label("", classes="field-error")
            if self.requires_restart:
                yield Label("Requires restart", classes="restart-warning")

    @property
    def value(self) -> str:
        """Get current selected value."""
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set selected value."""
        self._value = new_value
        try:
            select_widget = self.query_one(f"#select-{self.field_id}", Select)
            select_widget.value = new_value if new_value else Select.BLANK  # type: ignore[has-type]
        except Exception:  # noqa: S110  # nosec B110 - Widget may not be mounted yet
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle selection changes."""
        if event.value is not Select.BLANK:  # type: ignore[has-type]
            self._value = str(event.value)
        else:
            self._value = ""
        self.post_message(self.Changed(self, self._value))

    def validate(self) -> FieldValidation:
        """Validate the select field."""
        if not self.allow_blank and not self._value:
            return FieldValidation(is_valid=False, error_message="Selection required")
        return FieldValidation(is_valid=True)


class SwitchField(FormField):
    """Boolean switch field."""

    DEFAULT_CSS = (
        FormField.DEFAULT_CSS
        + """
    SwitchField .switch-container {
        height: auto;
    }

    SwitchField Switch {
        margin-right: 1;
    }
    """
    )

    def __init__(
        self,
        label: str,
        field_id: str,
        default: bool = False,
        help_text: str = "",
        requires_restart: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            label=label,
            field_id=field_id,
            help_text=help_text,
            requires_restart=requires_restart,
            **kwargs,
        )
        self.default = default
        self._value = default

    def compose(self) -> ComposeResult:
        """Compose the switch field."""
        with Vertical(classes="field-container"):
            with Horizontal(classes="switch-container"):
                yield Switch(value=self.default, id=f"switch-{self.field_id}")
                label_parts = [self.label_text]
                if self.requires_restart:
                    label_parts.append(" [*]")
                yield Label("".join(label_parts), classes="field-label")
            if self.help_text:
                yield Label(self.help_text, classes="field-help")
            if self.requires_restart:
                yield Label("Requires restart", classes="restart-warning")

    @property
    def value(self) -> bool:
        """Get current switch value."""
        return self._value

    @value.setter
    def value(self, new_value: bool) -> None:
        """Set switch value."""
        self._value = new_value
        try:
            switch_widget = self.query_one(f"#switch-{self.field_id}", Switch)
            switch_widget.value = new_value
        except Exception:  # noqa: S110  # nosec B110 - Widget may not be mounted yet
            pass

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes."""
        self._value = event.value
        self.post_message(self.Changed(self, self._value))

    def validate(self) -> FieldValidation:
        """Validate the switch field (always valid)."""
        return FieldValidation(is_valid=True)


class TextInput(FormField):
    """Text input field with validation."""

    DEFAULT_CSS = (
        FormField.DEFAULT_CSS
        + """
    TextInput Input {
        width: 1fr;
        max-width: 60;
    }

    SettingsScreen.-compact TextInput Input {
        max-width: 30;
    }
    """
    )

    def __init__(
        self,
        label: str,
        field_id: str,
        default: str = "",
        placeholder: str = "",
        required: bool = False,
        validator: Callable[[str], FieldValidation] | None = None,
        help_text: str = "",
        requires_restart: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            label=label,
            field_id=field_id,
            help_text=help_text,
            requires_restart=requires_restart,
            **kwargs,
        )
        self.default = default
        self.placeholder = placeholder
        self.required = required
        self.custom_validator = validator
        self._value = default

    def compose(self) -> ComposeResult:
        """Compose the text input field."""
        with Vertical(classes="field-container"):
            label_parts = [self.label_text]
            if self.requires_restart:
                label_parts.append(" [*]")
            yield Label("".join(label_parts), classes="field-label")
            with Horizontal():
                yield Input(
                    value=self.default,
                    placeholder=self.placeholder,
                    id=f"input-{self.field_id}",
                )
                if self.help_text:
                    yield Label(self.help_text, classes="field-help")
            yield Label("", classes="field-error")
            if self.requires_restart:
                yield Label("Requires restart", classes="restart-warning")

    @property
    def value(self) -> str:
        """Get current text value."""
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set text value."""
        self._value = new_value
        try:
            input_widget = self.query_one(f"#input-{self.field_id}", Input)
            input_widget.value = new_value
        except Exception:  # noqa: S110  # nosec B110 - Widget may not be mounted yet
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        validation = self.validate()
        if validation.is_valid:
            self.clear_error()
            self._value = event.value
            self.post_message(self.Changed(self, self._value))
        else:
            self.set_error(validation.error_message)

    def validate(self) -> FieldValidation:
        """Validate the text input."""
        try:
            input_widget = self.query_one(f"#input-{self.field_id}", Input)
            value = input_widget.value
        except Exception:
            return FieldValidation(is_valid=True)

        if self.required and not value.strip():
            return FieldValidation(is_valid=False, error_message="This field is required")

        if self.custom_validator:
            return self.custom_validator(value)

        return FieldValidation(is_valid=True)
