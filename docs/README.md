# Documentation

This directory contains additional documentation for STT Clipboard.

## Project Documentation

- [README.md](../README.md) - Main documentation and user guide
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development and contribution guidelines
- [SECURITY.md](../SECURITY.md) - Security policy and vulnerability reporting
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture documentation
- [CHANGELOG.md](../CHANGELOG.md) - Version history and release notes

## Running Security Scans

```bash
# Run all security checks
make security

# Individual scans
uv run bandit -c pyproject.toml -r src/    # Code vulnerabilities
uv run safety scan                          # Dependency CVEs
uv run detect-secrets scan                 # Secrets detection

# Pre-commit (runs all checks)
uv run pre-commit run --all-files
```

## Testing

See [tests/README.md](../tests/README.md) for testing documentation.

```bash
# Run all tests
make test

# Run with coverage
make test-cov
```
