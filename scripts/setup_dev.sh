#!/bin/bash

# STT Clipboard - Development Environment Setup
# This script sets up the development environment with pre-commit hooks

set -e

echo "========================================"
echo "STT Clipboard - Dev Environment Setup"
echo "========================================"
echo ""

# Get absolute path to project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Install dev dependencies
echo "Installing development dependencies with uv..."
uv sync --all-extras

echo "✓ Development dependencies installed"
echo ""

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
uv run pre-commit install

echo "✓ Pre-commit hooks installed"
echo ""

# Run pre-commit on all files to verify setup
echo "Running pre-commit checks on all files (this may take a moment)..."
uv run pre-commit run --all-files || {
    echo ""
    echo "⚠ Some pre-commit checks failed. This is normal on first run."
    echo "The hooks will fix formatting issues automatically on commit."
    echo ""
}

echo ""
echo "========================================"
echo "Development Environment Ready!"
echo "========================================"
echo ""
echo "Pre-commit hooks installed:"
echo "  ✓ Code formatting (black, isort, ruff)"
echo "  ✓ Type checking (mypy)"
echo "  ✓ Security scanning (bandit, detect-secrets, gitleaks)"
echo "  ✓ Dependency vulnerability check (safety)"
echo "  ✓ YAML/Shell linting"
echo "  ✓ Tests (pytest - runs on push)"
echo ""
echo "Useful commands:"
echo "  uv run pre-commit run --all-files  # Run all hooks manually"
echo "  uv run pytest                      # Run tests"
echo "  uv run pytest --cov                # Run tests with coverage"
echo "  uv run black .                     # Format code"
echo "  uv run ruff check .                # Lint code"
echo "  uv run mypy src/                   # Type check"
echo "  uv run bandit -r src/              # Security scan"
echo ""
