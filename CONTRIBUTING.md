# Contributing to STT Clipboard

Thank you for your interest in contributing to STT Clipboard!

## Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/christopherlouet/stt-clipboard.git
cd stt-clipboard
```

### 2. Install dependencies

```bash
./scripts/install_deps.sh
```

### 3. Set up development environment

```bash
./scripts/setup_dev.sh
```

This will:
- Install development dependencies (pytest, linters, security tools)
- Set up pre-commit hooks
- Run initial checks

## Development Workflow

### Pre-commit Hooks

Pre-commit hooks are automatically installed and will run on every commit. They perform:

1. **Code Formatting**
   - Black (Python formatter)
   - isort (import sorting)
   - Ruff (fast linter/formatter)

2. **Code Quality**
   - Ruff (linting)
   - MyPy (type checking)
   - ShellCheck (bash script linting)
   - YAML linting

3. **Security**
   - Bandit (code vulnerability scanning)
   - detect-secrets (secret detection)
   - Gitleaks (secret scanning)
   - Safety (dependency vulnerability check)

4. **Tests**
   - pytest (runs on git push)

### Running checks manually

```bash
# Run all pre-commit hooks
uv run pre-commit run --all-files

# Run specific checks
uv run black .                  # Format code
uv run ruff check .            # Lint code
uv run ruff check --fix .      # Lint and auto-fix
uv run mypy src/               # Type check
uv run bandit -r src/          # Security scan
uv run pytest                  # Run tests
uv run pytest --cov            # Run tests with coverage
```

### Code Style

- **Line length**: 100 characters
- **Python version**: 3.10+
- **Formatting**: Black + isort (automatic via pre-commit)
- **Type hints**: Encouraged but not required

### Testing

Write tests for new features:

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_specific.py

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only fast tests
uv run pytest -m "not slow"
```

### Security

**Before committing:**
- Never commit secrets, API keys, or credentials
- Pre-commit hooks will scan for secrets automatically
- If a secret is detected, remove it and update `.secrets.baseline` if it's a false positive

**To update the secrets baseline:**
```bash
uv run detect-secrets scan --baseline .secrets.baseline
```

**Check for vulnerabilities:**
```bash
uv run bandit -r src/
uv run safety check
```

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, descriptive commit messages
   - Follow the code style guidelines
   - Add tests for new features
   - Update documentation as needed

3. **Run checks locally**
   ```bash
   uv run pre-commit run --all-files
   uv run pytest
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **PR Review**
   - Address review comments
   - Ensure CI passes
   - Update changelog if needed

## Project Structure

```
stt-clipboard/
├── src/                    # Source code
│   ├── main.py            # Entry point
│   ├── audio_capture.py   # Audio recording
│   ├── transcription.py   # Whisper transcription
│   ├── clipboard.py       # Clipboard integration
│   ├── notifications.py   # Desktop notifications
│   └── ...
├── tests/                 # Test files
├── config/                # Configuration files
├── scripts/               # Utility scripts
└── systemd/              # Systemd service files
```

## Reporting Issues

When reporting bugs, please include:
- OS and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.
