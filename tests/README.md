# Tests

This directory contains test cases and testing utilities for the Hack Tractor project.

## Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for combined components
- `fixtures/` - Test fixtures and mock data
- `utils/` - Testing utilities and helpers

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_equipment_interface.py

# Run tests with coverage report
pytest --cov=src
```

## Writing Tests

- Create test files with the `test_` prefix
- Use descriptive test names that explain the expected behavior
- Mock external dependencies and hardware interfaces
- Test both success and failure cases
