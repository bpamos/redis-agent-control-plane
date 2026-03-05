# Contributing to Redis Agent Control Plane

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (recommended) OR pip + venv
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/redis-agent-control-plane.git
cd redis-agent-control-plane

# Install dependencies
make install

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards and best practices outlined below.

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_your_file.py

# Run with coverage
make test-coverage
```

### 4. Run Quality Checks

```bash
# Run all checks
make all

# Or run individually
make lint        # Linting with ruff
make format      # Format with black
make type-check  # Type checking with mypy
```

### 5. Validate Components

```bash
# Validate all components
redis-agent-control-plane validate --all

# Or validate individually
redis-agent-control-plane validate --runbooks
redis-agent-control-plane validate --registry
redis-agent-control-plane validate --steps
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### 7. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

### Code Quality

- All code must pass `ruff` linting
- All code must pass `mypy` type checking
- All code must be formatted with `black`
- All tests must pass

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### Documentation

- Update README.md for user-facing changes
- Update CONTEXT.md for architectural changes
- Add docstrings to all public APIs
- Include examples in docstrings

## Project Structure

```
redis-agent-control-plane/
├── src/redis_agent_control_plane/  # Source code
│   ├── cli/                        # CLI commands
│   ├── orchestration/              # Core orchestration logic
│   └── rag/                        # RAG pipeline
├── tests/                          # Test files
├── runbooks/                       # Runbook YAML files
├── steps/                          # Reusable step library
├── scripts/                        # Validation scripts
└── examples/                       # Example deployment specs
```

## Adding New Features

### Adding a New Runbook

1. Create YAML file in `runbooks/{product}/{platform}/`
2. Follow the runbook schema (see existing runbooks)
3. Add entry to `runbooks/_registry.yaml`
4. Run `redis-agent-control-plane validate --runbooks`
5. Add tests in `tests/test_runbook.py`

### Adding a New Step

1. Create YAML file in `steps/{product}/{category}/`
2. Follow the step schema (see `steps/README.md`)
3. Run `redis-agent-control-plane validate --steps`
4. Add tests in `tests/test_runbook.py`

### Adding a New CLI Command

1. Create command file in `src/redis_agent_control_plane/cli/`
2. Register command in `src/redis_agent_control_plane/main.py`
3. Add tests in `tests/test_cli.py`
4. Update README.md with usage examples

## CI/CD

All pull requests must pass:
- ✅ Linting (ruff)
- ✅ Type checking (mypy)
- ✅ Tests (pytest)
- ✅ Runbook validation
- ✅ Registry validation
- ✅ Step validation

GitHub Actions will automatically run these checks on every PR.

## Getting Help

- Check existing issues on GitHub
- Review documentation in README.md and CONTEXT.md
- Ask questions in pull request comments

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

