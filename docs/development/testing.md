# Testing

STT Clipboard uses pytest for testing with a focus on reliability and maintainability.

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# With verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_autopaste.py

# Run specific test class
uv run pytest tests/test_autopaste.py::TestMacPaster

# Run specific test
uv run pytest tests/test_autopaste.py::TestMacPaster::test_paste_success -v
```

### With Coverage

```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Using Make

```bash
make test      # Run tests
make test-cov  # Run with coverage
```

## Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_audio_capture.py
├── test_autopaste.py
├── test_clipboard.py
├── test_config.py
├── test_hotkey.py
├── test_punctuation.py
└── test_transcription.py
```

### Test Organization

Tests are organized by module, with nested classes for grouping:

```python
class TestModuleName:
    """Tests for module_name."""

    class TestFunctionName:
        """Tests for function_name."""

        def test_should_do_something_when_condition(self):
            """Test description."""
            pass
```

## Writing Tests

### Test Naming

Use descriptive names that explain the behavior:

```python
# Good
def test_should_return_empty_string_when_input_is_none():
    pass

def test_should_raise_error_when_file_not_found():
    pass

# Avoid
def test_function1():
    pass

def test_error():
    pass
```

### AAA Pattern

Follow Arrange-Act-Assert:

```python
def test_should_transcribe_audio_correctly(self):
    # Arrange
    audio_data = load_test_audio("hello.wav")
    transcriber = WhisperTranscriber(config)

    # Act
    result = transcriber.transcribe(audio_data)

    # Assert
    assert result.text == "Hello"
    assert result.language == "en"
```

### Fixtures

Use pytest fixtures for shared setup:

```python
# conftest.py
import pytest
from src.config import Config

@pytest.fixture
def config():
    """Provide test configuration."""
    return Config.from_yaml("config/config.yaml")

@pytest.fixture
def audio_recorder(config):
    """Provide configured audio recorder."""
    return AudioRecorder(config.audio, config.vad)
```

Usage:

```python
def test_should_record_audio(audio_recorder):
    result = audio_recorder.record()
    assert result is not None
```

## Mocking Guidelines

### When to Mock

- External APIs and services
- Hardware access (microphone, clipboard)
- File system operations
- Network calls

### When NOT to Mock

- Internal business logic
- Data transformations
- Pure functions

### Mock Examples

```python
from unittest.mock import patch, MagicMock

class TestClipboardManager:
    @patch("subprocess.run")
    def test_should_copy_text_to_clipboard(self, mock_run):
        # Arrange
        mock_run.return_value = MagicMock(returncode=0)
        manager = WaylandClipboardManager()

        # Act
        result = manager.copy("test text")

        # Assert
        assert result is True
        mock_run.assert_called_once()
```

## Testing Different Components

### Audio Capture

```python
class TestAudioRecorder:
    @patch("sounddevice.InputStream")
    def test_should_start_recording(self, mock_stream):
        recorder = AudioRecorder(audio_config, vad_config)
        recorder.start()
        mock_stream.assert_called()
```

### Transcription

```python
class TestWhisperTranscriber:
    def test_should_detect_language(self):
        # Use actual model for integration tests
        transcriber = WhisperTranscriber(config)
        result = transcriber.transcribe(french_audio)
        assert result.language == "fr"
```

### Clipboard

```python
class TestClipboardManager:
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_should_use_wl_copy_on_wayland(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/wl-copy"
        manager = create_clipboard_manager()
        assert isinstance(manager, WaylandClipboardManager)
```

### Auto-Paste

```python
class TestMacPaster:
    @patch("subprocess.run")
    def test_should_simulate_cmd_v(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        paster = MacPaster(config)
        result = paster.paste()
        assert result is True
```

## Test Coverage

### Requirements

- Minimum 80% coverage on new code
- Focus on critical paths
- Test edge cases

### Checking Coverage

```bash
# Terminal report
uv run pytest --cov=src --cov-report=term-missing

# HTML report for detailed view
uv run pytest --cov=src --cov-report=html
```

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## Edge Cases to Test

### Input Validation

```python
def test_should_handle_none_input(self):
    result = process(None)
    assert result == ""

def test_should_handle_empty_string(self):
    result = process("")
    assert result == ""

def test_should_handle_whitespace_only(self):
    result = process("   ")
    assert result == ""
```

### Boundary Conditions

```python
def test_should_handle_max_length(self):
    long_text = "a" * 10000
    result = process(long_text)
    assert len(result) <= MAX_LENGTH

def test_should_handle_unicode(self):
    result = process("Héllo 世界 🌍")
    assert "Héllo" in result
```

### Error Conditions

```python
def test_should_raise_on_invalid_config(self):
    with pytest.raises(ConfigError):
        Config.from_yaml("nonexistent.yaml")

def test_should_timeout_on_long_operation(self):
    with pytest.raises(TimeoutError):
        slow_operation(timeout=0.001)
```

## CI Integration

Tests run automatically on:

- Push to any branch
- Pull requests to main

See `.github/workflows/ci.yml` for configuration.

## Debugging Tests

### Verbose Output

```bash
uv run pytest -v -s  # Show print statements
```

### Run Single Test

```bash
uv run pytest tests/test_module.py::TestClass::test_method -v
```

### Debug with pdb

```python
def test_debugging():
    import pdb; pdb.set_trace()
    result = function()
    assert result
```

Or use `--pdb` flag:

```bash
uv run pytest --pdb  # Drop into debugger on failure
```
