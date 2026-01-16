# Contributing

Thank you for considering contributing to STT Clipboard!

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/christopherlouet/stt-clipboard.git
cd stt-clipboard

# Install development dependencies
./scripts/setup_dev.sh

# This installs:
# - All project dependencies
# - Development tools (pytest, black, ruff, mypy)
# - Pre-commit hooks
```

## Workflow

We follow the **Explore → Plan → Code → Commit** workflow:

### 1. Explore

Before making changes, understand the existing code:

```bash
# Read relevant source files
# Understand the patterns and conventions
# Identify what needs to change
```

### 2. Plan

For non-trivial changes, plan before coding:

- List files to create/modify
- Identify potential risks
- Consider edge cases

### 3. Code

Implement following the plan:

```bash
# Create a feature branch
git checkout -b feature/your-feature

# Make changes
# Write tests
# Run quality checks
make pre-commit
```

### 4. Commit

Create clean, atomic commits:

```bash
# Stage changes
git add .

# Commit with conventional format
git commit -m "feat(module): add new feature"
```

## Code Style

### Python Conventions

- **Type hints** are mandatory on all public functions
- **No `Any`** except in exceptional documented cases
- Use **dataclasses** for complex objects
- Prefer **pure functions** when possible

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables/Functions | snake_case | `get_user_by_id` |
| Classes | PascalCase | `AudioRecorder` |
| Constants | SCREAMING_SNAKE | `MAX_RETRY_COUNT` |
| Files | snake_case | `audio_capture.py` |

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type check
uv run mypy src/

# Run all checks
make pre-commit
```

## Testing

### Requirements

- Minimum 80% coverage on new code
- No mocks except for external dependencies
- Test edge cases (None, empty, limits)

### Running Tests

```bash
# Run all tests
make test

# With coverage
make test-cov

# Specific test file
uv run pytest tests/test_module.py -v
```

### Test Structure

```python
class TestModuleName:
    """Tests for module_name."""

    class TestFunctionName:
        """Tests for function_name."""

        def test_should_expected_behavior_when_condition(self):
            # Arrange
            input_data = ...

            # Act
            result = function_name(input_data)

            # Assert
            assert result == expected
```

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

### Types

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code refactoring |
| `test` | Tests |
| `docs` | Documentation |
| `style` | Formatting |
| `chore` | Maintenance |
| `perf` | Performance |

### Examples

```bash
feat(autopaste): add macOS support via osascript
fix(clipboard): handle empty text gracefully
docs(readme): update installation instructions
test(transcription): add edge case tests
```

## Pull Requests

### Before Submitting

- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Type checks pass (`uv run mypy src/`)
- [ ] Documentation updated if needed

### PR Description

Include:

1. **Summary**: What does this PR do?
2. **Changes**: List of changes made
3. **Testing**: How was it tested?
4. **Screenshots**: If UI changes (N/A for this project)

## Branch Naming

- `main` - Production (protected)
- `develop` - Development
- `feature/xxx` - New features
- `fix/xxx` - Bug fixes
- `refactor/xxx` - Refactoring

## Security

- **Never** commit secrets (.env, credentials)
- **Validate** all user inputs
- **Use** subprocess with argument lists (no `shell=True`)
- **Never** log sensitive data (audio, transcribed text)

## Getting Help

- Check existing [GitHub Issues](https://github.com/christopherlouet/stt-clipboard/issues)
- Open a new issue for questions
- Join discussions on PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
