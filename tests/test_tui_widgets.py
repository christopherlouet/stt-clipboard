"""Tests for TUI widgets."""

from src.tui_widgets.form_fields import (
    FieldValidation,
    FloatInput,
    NumberInput,
    SelectField,
    SwitchField,
    TextInput,
)


class TestFieldValidation:
    """Tests for FieldValidation dataclass."""

    class TestInitialization:
        """Tests for FieldValidation creation."""

        def test_should_create_valid_result(self) -> None:
            """Test creating a valid result."""
            result = FieldValidation(is_valid=True)
            assert result.is_valid is True
            assert result.error_message == ""

        def test_should_create_invalid_result_with_message(self) -> None:
            """Test creating an invalid result with error message."""
            result = FieldValidation(is_valid=False, error_message="Test error")
            assert result.is_valid is False
            assert result.error_message == "Test error"


class TestNumberInput:
    """Tests for NumberInput widget."""

    class TestInitialization:
        """Tests for NumberInput creation."""

        def test_should_create_with_defaults(self) -> None:
            """Test creating NumberInput with default values."""
            field = NumberInput(label="Test", field_id="test-field")
            assert field.label_text == "Test"
            assert field.field_id == "test-field"
            assert field.default == 0
            assert field.min_value is None
            assert field.max_value is None

        def test_should_create_with_range(self) -> None:
            """Test creating NumberInput with min/max values."""
            field = NumberInput(
                label="Test",
                field_id="test-field",
                default=50,
                min_value=0,
                max_value=100,
            )
            assert field.default == 50
            assert field.min_value == 0
            assert field.max_value == 100

        def test_should_set_requires_restart_flag(self) -> None:
            """Test that requires_restart flag is set."""
            field = NumberInput(
                label="Test",
                field_id="test-field",
                requires_restart=True,
            )
            assert field.requires_restart is True

        def test_should_store_help_text(self) -> None:
            """Test that help text is stored."""
            field = NumberInput(
                label="Test",
                field_id="test-field",
                help_text="This is help",
            )
            assert field.help_text == "This is help"


class TestFloatInput:
    """Tests for FloatInput widget."""

    class TestInitialization:
        """Tests for FloatInput creation."""

        def test_should_create_with_defaults(self) -> None:
            """Test creating FloatInput with default values."""
            field = FloatInput(label="Test", field_id="test-field")
            assert field.label_text == "Test"
            assert field.field_id == "test-field"
            assert field.default == 0.0

        def test_should_create_with_range(self) -> None:
            """Test creating FloatInput with min/max values."""
            field = FloatInput(
                label="Test",
                field_id="test-field",
                default=0.5,
                min_value=0.0,
                max_value=1.0,
            )
            assert field.default == 0.5
            assert field.min_value == 0.0
            assert field.max_value == 1.0

        def test_should_set_step_value(self) -> None:
            """Test that step value is set."""
            field = FloatInput(
                label="Test",
                field_id="test-field",
                step=0.01,
            )
            assert field.step == 0.01


class TestSelectField:
    """Tests for SelectField widget."""

    class TestInitialization:
        """Tests for SelectField creation."""

        def test_should_create_with_options(self) -> None:
            """Test creating SelectField with options."""
            options = [("Option 1", "opt1"), ("Option 2", "opt2")]
            field = SelectField(
                label="Test",
                field_id="test-field",
                options=options,
                default="opt1",
            )
            assert field.label_text == "Test"
            assert field.options == options
            assert field.default == "opt1"

        def test_should_allow_blank_option(self) -> None:
            """Test creating SelectField with blank option."""
            options = [("Option 1", "opt1")]
            field = SelectField(
                label="Test",
                field_id="test-field",
                options=options,
                allow_blank=True,
                blank_label="None",
            )
            assert field.allow_blank is True
            assert field.blank_label == "None"


class TestSwitchField:
    """Tests for SwitchField widget."""

    class TestInitialization:
        """Tests for SwitchField creation."""

        def test_should_create_with_default_false(self) -> None:
            """Test creating SwitchField with default False."""
            field = SwitchField(label="Test", field_id="test-field")
            assert field.default is False
            assert field._value is False

        def test_should_create_with_default_true(self) -> None:
            """Test creating SwitchField with default True."""
            field = SwitchField(label="Test", field_id="test-field", default=True)
            assert field.default is True
            assert field._value is True

    class TestValidation:
        """Tests for SwitchField validation."""

        def test_should_always_be_valid(self) -> None:
            """Test that SwitchField is always valid."""
            field = SwitchField(label="Test", field_id="test-field")
            result = field.validate()
            assert result.is_valid is True


class TestTextInput:
    """Tests for TextInput widget."""

    class TestInitialization:
        """Tests for TextInput creation."""

        def test_should_create_with_defaults(self) -> None:
            """Test creating TextInput with default values."""
            field = TextInput(label="Test", field_id="test-field")
            assert field.label_text == "Test"
            assert field.default == ""
            assert field.required is False

        def test_should_create_with_default_value(self) -> None:
            """Test creating TextInput with default value."""
            field = TextInput(
                label="Test",
                field_id="test-field",
                default="default value",
            )
            assert field.default == "default value"
            assert field._value == "default value"

        def test_should_set_required_flag(self) -> None:
            """Test that required flag is set."""
            field = TextInput(
                label="Test",
                field_id="test-field",
                required=True,
            )
            assert field.required is True

        def test_should_set_placeholder(self) -> None:
            """Test that placeholder is set."""
            field = TextInput(
                label="Test",
                field_id="test-field",
                placeholder="Enter text...",
            )
            assert field.placeholder == "Enter text..."


class TestWidgetImports:
    """Tests for widget module imports."""

    def test_should_import_field_validation(self) -> None:
        """Test FieldValidation import."""
        from src.tui_widgets import FieldValidation

        assert FieldValidation is not None

    def test_should_import_number_input(self) -> None:
        """Test NumberInput import."""
        from src.tui_widgets import NumberInput

        assert NumberInput is not None

    def test_should_import_float_input(self) -> None:
        """Test FloatInput import."""
        from src.tui_widgets import FloatInput

        assert FloatInput is not None

    def test_should_import_select_field(self) -> None:
        """Test SelectField import."""
        from src.tui_widgets import SelectField

        assert SelectField is not None

    def test_should_import_switch_field(self) -> None:
        """Test SwitchField import."""
        from src.tui_widgets import SwitchField

        assert SwitchField is not None

    def test_should_import_text_input(self) -> None:
        """Test TextInput import."""
        from src.tui_widgets import TextInput

        assert TextInput is not None
