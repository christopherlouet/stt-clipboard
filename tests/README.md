# Tests

This directory contains the test suite for STT Clipboard.

## Running Tests

### Run all tests

```bash
make test
# or
uv run pytest
```

### Run with coverage

```bash
make test-cov
# or
uv run pytest --cov=src --cov-report=html --cov-report=term
```

Coverage report will be generated in `htmlcov/index.html`.

### Run specific tests

```bash
# Run a specific test file
uv run pytest tests/test_imports.py

# Run a specific test function
uv run pytest tests/test_imports.py::test_import_main

# Run tests matching a pattern
uv run pytest -k "test_config"

# Run with verbose output
uv run pytest -v

# Run with very verbose output (show all test output)
uv run pytest -vv
```

### Run tests by markers

```bash
# Run only fast tests (skip slow ones)
uv run pytest -m "not slow"

# Run only integration tests
uv run pytest -m integration
```

## Test Structure

```
tests/
├── README.md           # This file
├── conftest.py         # Pytest configuration and fixtures
├── test_imports.py     # Import tests
├── test_autopaste.py   # Auto-paste functionality tests
├── test_hotkey.py      # Hotkey/trigger system tests
└── test_system.py      # System integration tests
```

## Writing Tests

### Test naming convention

- Test files: `test_*.py` or `*_test.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example test

```python
import pytest
from src.config import Config


def test_config_defaults():
    """Test that default config values are set correctly."""
    config = Config()
    assert config.audio.sample_rate == 16000
    assert config.transcription.model_size == "tiny"


@pytest.mark.slow
def test_whisper_transcription():
    """Test actual transcription (marked as slow)."""
    # ... test code
```

### Using fixtures

```python
@pytest.fixture
def sample_audio():
    """Provide sample audio data for tests."""
    import numpy as np
    return np.zeros(16000, dtype=np.float32)


def test_audio_processing(sample_audio):
    """Test audio processing with fixture."""
    assert len(sample_audio) == 16000
```

## Test Markers

Available markers (defined in `pyproject.toml`):

- `@pytest.mark.slow` - Marks slow tests (can be skipped with `-m "not slow"`)
- `@pytest.mark.integration` - Marks integration tests

## Continuous Integration

Tests run automatically on every push and pull request via GitHub Actions.

See `.github/workflows/ci.yml` for CI configuration.

## Coverage

Aim for:
- **Overall coverage**: > 80%
- **Critical modules**: > 90% (transcription, audio_capture)

View coverage report:
```bash
make test-cov
# Open htmlcov/index.html in browser
```

## Debugging Tests

```bash
# Run with debugger (pdb)
uv run pytest --pdb

# Stop on first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l

# Increase verbosity
uv run pytest -vv
```
