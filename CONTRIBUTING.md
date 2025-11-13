# Contributing to xml-lib

Thank you for considering contributing to xml-lib! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Quality Gates](#quality-gates)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Code of Conduct

This project follows a code of conduct that all contributors are expected to uphold. Be respectful, inclusive, and considerate in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/xml-lib.git
   cd xml-lib
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/farukalpay/xml-lib.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (recommended) or pip
- Git

### Installation

1. Install dependencies:
   ```bash
   # With Poetry (recommended)
   poetry install

   # Or with pip
   pip install -e ".[dev]"
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Verify installation:
   ```bash
   # Run tests
   pytest

   # Run linters
   make lint
   ```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following our [Style Guide](#style-guide)

3. Write tests for your changes

4. Run the quality gates (see below)

5. Commit your changes with clear, descriptive messages:
   ```bash
   git commit -m "feat: Add new validation rule for X"
   ```

### Commit Message Format

We follow the conventional commits format:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic changes)
- `refactor:` - Code refactoring
- `test:` - Test additions or modifications
- `chore:` - Maintenance tasks

## Quality Gates

All contributions must pass these quality gates before being merged:

### 1. Tests

Run all tests and ensure they pass:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xml_lib --cov-report=term-missing

# Run specific test markers
pytest -m "not slow"          # Skip slow tests
pytest -m integration         # Only integration tests
pytest -m property            # Only property-based tests
```

**Required coverage:** 80% or higher for new code

### 2. Type Checking

Ensure all type hints are correct:

```bash
mypy xml_lib
```

**No type errors allowed.**

### 3. Linting

Code must pass all linters:

```bash
# Run all linters
make lint

# Or individually:
ruff check xml_lib          # Fast Python linter
black --check xml_lib       # Code formatting
isort --check xml_lib       # Import sorting
```

### 4. Formatting

Code must be formatted with Black:

```bash
# Check formatting
black --check xml_lib

# Auto-format
black xml_lib
```

### 5. Documentation

- All public functions must have docstrings
- Docstrings must follow Google style
- Update README.md if adding user-facing features
- Update docs/api.md for public API changes

### 6. Contracts

Core modules use runtime contracts (via `icontract`):

```python
from icontract import require, ensure

@require(lambda x: x > 0, "x must be positive")
@ensure(lambda result: result > 0, "result must be positive")
def square(x: int) -> int:
    return x * x
```

## Testing

### Test Organization

- `tests/test_*.py` - Unit and integration tests
- Tests are organized by module (e.g., `test_validator.py` for `validator.py`)
- Use pytest fixtures for setup/teardown
- Mark tests appropriately (`@pytest.mark.slow`, etc.)

### Writing Tests

1. **Unit tests** - Test individual functions/methods in isolation
2. **Integration tests** - Test components working together
3. **Property-based tests** - Use Hypothesis for invariant testing
4. **API tests** - Test the public API in `tests/test_api.py`

### Test Guidelines

- One test file per module
- Descriptive test names: `test_validator_detects_invalid_xml`
- Use fixtures for common setup
- Mock external dependencies
- Test both success and failure cases
- Test edge cases and boundary conditions

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_validator.py

# Run a specific test
pytest tests/test_validator.py::test_validator_with_valid_xml

# Run tests matching a pattern
pytest -k "validator"

# Run with verbose output
pytest -v
```

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def validate_xml(project_path: Path, schemas_dir: Path) -> ValidationResult:
    """Validate XML files in a project.

    This function validates all XML files in the given project directory
    against the schemas in the schemas directory.

    Args:
        project_path: Path to the project directory
        schemas_dir: Path to the schemas directory

    Returns:
        ValidationResult containing validation status and any errors

    Raises:
        XMLFileNotFoundError: If project_path doesn't exist
        XMLConfigurationError: If schemas_dir is invalid

    Example:
        >>> result = validate_xml(Path("project"), Path("schemas"))
        >>> if result.is_valid:
        ...     print("Validation passed!")
    """
    pass
```

### Documentation Files

- `README.md` - Main project documentation
- `docs/api.md` - Public API reference
- `docs/*.md` - Feature-specific guides
- Docstrings - Inline code documentation

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code coverage is maintained or improved
3. ✅ Type checking passes (mypy)
4. ✅ Linting passes (ruff, black)
5. ✅ Documentation is updated
6. ✅ Commit messages follow conventions
7. ✅ Branch is up to date with main

### Submission

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub

3. Fill out the PR template completely

4. Link any related issues

5. Request review from maintainers

### PR Checklist

The PR description should include:

- [ ] Description of changes
- [ ] Motivation and context
- [ ] Type of change (bug fix, feature, breaking change, etc.)
- [ ] Testing performed
- [ ] Documentation updates
- [ ] Breaking changes (if any)

### Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, a maintainer will merge your PR

## Style Guide

### Python Style

- **PEP 8** compliance (enforced by ruff and black)
- **Type hints** for all function signatures
- **Docstrings** for all public functions/classes
- **Line length**: 100 characters (enforced by black)
- **Import ordering**: Use isort
- **Naming**:
  - Classes: `PascalCase`
  - Functions/methods: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: `_leading_underscore`

### Code Principles

1. **Explicit is better than implicit** - Clear code over clever code
2. **Fail fast** - Validate inputs early, raise exceptions for invalid config
3. **Result objects over exceptions** - Use `ValidationResult` for per-file errors
4. **Type safety** - Use type hints and mypy
5. **Testability** - Write testable code, use dependency injection
6. **Documentation** - Code should be self-documenting with docstrings

### Error Handling

- Use **exceptions** for "cannot even start" errors:
  - Missing files: `XMLFileNotFoundError`
  - Configuration issues: `XMLConfigurationError`
  - Parse errors: `XMLParseError`

- Use **result objects** for per-file issues:
  - `ValidationResult` - Validation errors/warnings
  - `LintResult` - Linting issues
  - `PublishResult` - Publishing errors

```python
# Good: Use exceptions for setup failures
if not project_path.exists():
    raise XMLFileNotFoundError("Project not found", path=project_path)

# Good: Use result objects for validation issues
result = ValidationResult(
    is_valid=False,
    errors=[ValidationError(file="test.xml", message="Invalid XML")],
)
```

## Additional Resources

- [Architecture Decision Records](docs/adr/) - Design decisions
- [API Documentation](docs/api.md) - Public API reference
- [Pipeline Guide](docs/PIPELINE_GUIDE.md) - Pipeline automation
- [Streaming Guide](docs/STREAMING_GUIDE.md) - Large file handling

## Questions?

- Open an issue with the `question` label
- Reach out to maintainers
- Check existing issues and discussions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to xml-lib! 🎉
