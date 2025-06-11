# Test Suite Documentation

This directory contains comprehensive unit tests for the maintenance backend application.

## Test Structure

```
tests/
├── conftest.py                           # Shared fixtures and test configuration
├── test_repositories/                    # Repository layer tests
│   ├── __init__.py
│   └── test_base_repository.py          # CRUDBaseRepository tests
├── test_services/                       # Service layer tests
│   ├── __init__.py
│   └── test_usuario/                    # User service tests
│       ├── __init__.py
│       ├── test_super_admin_case.py     # SuperAdminCase tests
│       └── test_usuario_service.py      # UsuarioService tests
└── README.md                           # This file
```

## Key Features Tested

### Repository Layer (`test_repositories/`)

- **CRUDBaseRepository**: Complete CRUD operations testing
- **Advanced Filtering**: ILIKE, exact match, and pattern matching
- **Error Handling**: Database exceptions and edge cases
- **Pagination**: Skip and limit functionality

### Service Layer (`test_services/`)

- **SuperAdminCase**: Permission validation and business logic
- **UsuarioService**: Complete user management workflow
- **Error Handling**: HTTP exceptions and service-level errors
- **Integration**: Mocked dependencies and external services

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r test-requirements.txt
```

### Quick Start

```bash
# Run all tests
python run_tests.py all

# Run with coverage
python run_tests.py coverage

# Run specific test file
python run_tests.py specific tests/test_repositories/test_base_repository.py
```

### Available Commands

| Command           | Description                    |
| ----------------- | ------------------------------ |
| `all`             | Run all tests                  |
| `unit`            | Run unit tests only            |
| `integration`     | Run integration tests only     |
| `coverage`        | Run tests with coverage report |
| `fast`            | Run tests excluding slow tests |
| `specific <file>` | Run specific test file         |

### Direct pytest Commands

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test class
pytest tests/test_repositories/test_base_repository.py::TestCRUDBaseRepository -v

# Run specific test method
pytest tests/test_services/test_usuario/test_super_admin_case.py::TestSuperAdminCase::test_obtener_filtros_all_parameters -v
```

## Test Patterns

### Mocking Strategy

- **Database Sessions**: Mocked using `AsyncMock`
- **External Services**: Firebase, CompaniaService, etc.
- **Repository Calls**: Patched at the import level

### Fixture Usage

- **Shared Fixtures**: Defined in `conftest.py`
- **Test-Specific Fixtures**: Defined within test classes
- **Parameterized Tests**: For testing multiple scenarios

### Async Testing

All async tests use `@pytest.mark.asyncio` decorator and proper async/await patterns.

## Coverage Goals

- **Target Coverage**: 80% minimum
- **Critical Paths**: 95%+ coverage for business logic
- **Edge Cases**: Comprehensive error handling testing

## Test Data Management

### Mock Objects

- Consistent test data across tests
- Realistic data structures
- Edge case scenarios included

### Fixtures

- Reusable test data
- Proper isolation between tests
- Clean setup and teardown

## Best Practices

1. **AAA Pattern**: Arrange, Act, Assert
2. **Single Responsibility**: One concept per test
3. **Descriptive Names**: Clear test method names
4. **Isolation**: No dependencies between tests
5. **Comprehensive**: Happy path, edge cases, and error scenarios

## Contributing

When adding new tests:

1. Follow the existing directory structure
2. Use appropriate fixtures from `conftest.py`
3. Include both positive and negative test cases
4. Add proper documentation
5. Ensure tests are isolated and deterministic

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes the project root
2. **Async Issues**: Use proper `@pytest.mark.asyncio` decorator
3. **Mock Problems**: Check patch targets match actual import paths
4. **Fixture Scope**: Ensure fixture scopes match test requirements

### Debug Tips

```bash
# Run with debug output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run specific failing test
pytest tests/path/to/test.py::test_name -v -s
```
