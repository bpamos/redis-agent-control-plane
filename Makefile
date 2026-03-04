.PHONY: help install install-poetry install-venv test run lint format type-check clean all

# Detect if Poetry is available
POETRY := $(shell command -v poetry 2> /dev/null)
VENV_PYTHON := venv/bin/python
VENV_PYTEST := venv/bin/pytest
VENV_BLACK := venv/bin/black
VENV_RUFF := venv/bin/ruff
VENV_MYPY := venv/bin/mypy

help:
	@echo "Redis Agent Control Plane - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install dependencies (auto-detects Poetry or venv)"
	@echo "  make install-poetry  Install with Poetry (recommended)"
	@echo "  make install-venv    Install with pip in virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  make run             Run the application"
	@echo "  make test            Run tests with pytest"
	@echo "  make lint            Run ruff linter"
	@echo "  make format          Format code with black"
	@echo "  make type-check      Run mypy type checker"
	@echo "  make all             Run format, lint, type-check, and test"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           Remove generated files and caches"

install:
ifdef POETRY
	@$(MAKE) install-poetry
else
	@echo "Poetry not found, using venv + pip..."
	@$(MAKE) install-venv
endif

install-poetry:
	@echo "Installing dependencies with Poetry..."
	poetry install

install-venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Installing dependencies..."
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt
	@echo "Virtual environment ready. Activate with: source venv/bin/activate"

test:
ifdef POETRY
	@echo "Running tests with Poetry..."
	poetry run pytest -v
else
	@echo "Running tests with venv..."
	PYTHONPATH=src $(VENV_PYTEST) -v
endif

run:
ifdef POETRY
	@echo "Running application with Poetry..."
	poetry run python -m redis_agent_control_plane.main
else
	@echo "Running application with venv..."
	PYTHONPATH=src $(VENV_PYTHON) -m redis_agent_control_plane.main
endif

lint:
ifdef POETRY
	@echo "Running linter with Poetry..."
	poetry run ruff check src tests
else
	@echo "Running linter with venv..."
	$(VENV_RUFF) check src tests
endif

format:
ifdef POETRY
	@echo "Formatting code with Poetry..."
	poetry run black src tests
else
	@echo "Formatting code with venv..."
	$(VENV_BLACK) src tests
endif

type-check:
ifdef POETRY
	@echo "Running type checker with Poetry..."
	poetry run mypy src
else
	@echo "Running type checker with venv..."
	PYTHONPATH=src $(VENV_MYPY) src
endif

all: format lint type-check test
	@echo "All checks passed!"

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf venv
	@echo "Clean complete."

