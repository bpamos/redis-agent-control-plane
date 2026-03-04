# redis-agent-control-plane

Agent control plane with context engine and RAG workflow for simplifying Redis Enterprise Infrastructure deployments.

## Overview

This project provides an intelligent agent control plane that uses Retrieval-Augmented Generation (RAG) to assist with Redis Enterprise deployment operations. The system is designed to be extensible for other use cases in the future.

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation) (recommended) OR pip + venv

## Quick Start

### 1. Install Dependencies

The Makefile auto-detects whether you have Poetry installed:

```bash
make install
```

**With Poetry (recommended):**

```bash
poetry install
```

**Without Poetry (using venv):**

```bash
make install-venv
# Then activate the virtual environment:
source venv/bin/activate
```

### 2. Run the Application

```bash
make run
```

Or directly with Poetry:

```bash
poetry run python -m redis_agent_control_plane.main
```

### 3. Run Tests

```bash
make test
```

## Development Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Run the application
make test          # Run tests with pytest
make lint          # Run ruff linter
make format        # Format code with black
make type-check    # Run mypy type checker
make all           # Run format, lint, type-check, and test
make clean         # Remove generated files and caches
```

## Project Structure

```
redis-agent-control-plane/
├── src/
│   └── redis_agent_control_plane/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_smoke.py
├── pyproject.toml
├── Makefile
├── AUGGIE.md      # AI assistant operating manual
├── CONTEXT.md     # Repository context and architecture
└── README.md
```

## Contributing

See [AUGGIE.md](AUGGIE.md) for guidelines on working with AI assistance in this repository.

See [CONTEXT.md](CONTEXT.md) for architectural context and constraints.

See [TASKS.md](TASKS.md) for current tasks and development workflow.

## License

TODO: Add license information