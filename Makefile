.PHONY: help install install-dev test test-cov lint format security clean run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	./scripts/install_deps.sh

install-dev: ## Install development dependencies and setup pre-commit hooks
	./scripts/setup_dev.sh

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html --cov-report=term

lint: ## Run linters (ruff, mypy)
	uv run ruff check .
	uv run mypy src/

format: ## Format code (black, isort, ruff)
	uv run black .
	uv run isort .
	uv run ruff check --fix .

security: ## Run security checks (bandit, safety, detect-secrets)
	uv run bandit -c pyproject.toml -r src/
	uv run safety scan --output screen || true
	uv run detect-secrets scan --baseline .secrets.baseline

pre-commit: ## Run all pre-commit hooks
	uv run pre-commit run --all-files

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true

run: ## Run in one-shot mode
	uv run python -m src.main --mode oneshot

run-daemon: ## Run in daemon mode
	uv run python -m src.main --daemon

benchmark: ## Run performance benchmark
	uv run ./scripts/benchmark.py --iterations 10

sync: ## Sync dependencies with uv
	uv sync

update: ## Update dependencies
	uv sync --upgrade
