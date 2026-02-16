# Unit Testing Cheatsheet

Quick reference for writing effective unit tests.

## 🎯 The AAA Pattern

```python
def test_example():
    # ===== ARRANGE =====
    # Set up test data and mocks
    mock_service = Mock()
    handler = Handler(service=mock_service)
    
    # ===== ACT =====
    # Execute the code
    result = handler.method(data)
    
    # ===== ASSERT =====
    # Verify the result
    assert result == expected
```

## 🔧 Common Test Patterns

### Testing Success Cases
```python
@pytest.mark.asyncio
async def test_create_success(mock_service, sample_data):
    mock_service.create.return_value = expected_result
    result = await handler.create(sample_data)
    assert result == expected_result
```

### Testing Exceptions
```python
def test_raises_exception(mock_service):
    mock_service.get.side_effect = NotFoundException()
    
    with pytest.raises(NotFoundException) as exc:
        handler.get(id)
    
    assert "not found" in str(exc.value.message)
```

### Testing with Parametrize
```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
    ("", False),
])
def test_validate(input, expected):
    assert validate(input) == expected
```

### Testing Async Code
```python
@pytest.mark.asyncio
async def test_async_method():
    result = await async_function()
    assert result is not None
```

## 🎭 Mocking Quick Reference

### Basic Mock
```python
from unittest.mock import Mock, AsyncMock

mock_obj = Mock()
mock_obj.method.return_value = "value"

async_mock = AsyncMock()
async_mock.method.return_value = "value"
```

### Mock Side Effects (Exceptions)
```python
mock_service.method.side_effect = Exception("Error")
```

### Mock Multiple Calls
```python
mock_service.method.side_effect = [result1, result2, result3]
```

### Verify Mock Calls
```python
# Called once
mock_service.method.assert_called_once()

# Called with specific args
mock_service.method.assert_called_with(arg1, arg2)

# Called N times
assert mock_service.method.call_count == 3

# Never called
mock_service.method.assert_not_called()
```

### Patch (Replace Real Code)
```python
from unittest.mock import patch

@patch('app.services.group.Logger')
def test_with_patch(mock_logger):
    # Logger is mocked in this test
    service.method()
    mock_logger.info.assert_called()
```

## ✅ Test Naming Convention

```python
test_<method>_<scenario>_<expected_result>

# Examples:
test_create_group_with_valid_data_returns_group()
test_create_group_with_duplicate_name_raises_error()
test_get_group_with_invalid_id_returns_none()
```

## 🎯 What to Test (Priority Order)

1. ✅ **Business Logic** - Core functionality
2. ✅ **Error Handling** - Exception cases
3. ✅ **Edge Cases** - Null, empty, boundary values
4. ✅ **Validation** - Input validation
5. ⚠️ **Getters/Setters** - Lower priority

## 📊 Coverage Commands

```bash
# Run tests with coverage
pytest --cov=app

# Generate HTML report
pytest --cov=app --cov-report=html

# Show missing lines
pytest --cov=app --cov-report=term-missing

# Fail if coverage < 80%
pytest --cov=app --cov-fail-under=80
```

## 🚀 Pytest Commands

```bash
# Run all tests
pytest

# Run specific file
pytest tests/unit/test_handler.py

# Run specific test
pytest tests/unit/test_handler.py::test_create_success

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run tests matching pattern
pytest -k "create"

# Run only unit tests
pytest tests/unit/

# Parallel execution (with pytest-xdist)
pytest -n auto
```

## 🔍 Debugging Tests

```python
# Add breakpoint
def test_something():
    breakpoint()  # Debugger stops here
    result = function()
    assert result

# Print debug info
def test_something():
    result = function()
    print(f"Result: {result}")  # Run with pytest -s
    assert result
```

## 📝 Common Fixtures

```python
@pytest.fixture
def sample_data():
    """Returns test data"""
    return {"key": "value"}

@pytest.fixture
def mock_service():
    """Returns mocked service"""
    return Mock()

@pytest.fixture(scope="session")
def db_connection():
    """Created once per test session"""
    conn = create_connection()
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def reset_state():
    """Runs automatically before each test"""
    reset_global_state()
```

## 🎓 FIRST Principles

- **F**ast - Tests run in milliseconds
- **I**ndependent - Tests don't depend on each other
- **R**epeatable - Same result every time
- **S**elf-validating - Clear pass/fail
- **T**imely - Written with the code

## ⚠️ Common Mistakes

### ❌ Don't Do This:
```python
# Testing private methods
def test_private():
    obj._private_method()

# Testing multiple things
def test_everything():
    assert result.field1 == x
    assert result.field2 == y
    assert result.field3 == z

# Hard-coded test data
def test_with_hardcoded_data():
    result = function("test123")  # Magic value

# Slow tests
def test_slow():
    time.sleep(5)  # Don't sleep in tests!

# Dependent tests
def test_step1():
    global state
    state = create()

def test_step2():
    update(state)  # Depends on test_step1
```

### ✅ Do This Instead:
```python
# Test public interface
def test_public():
    obj.public_method()

# One assertion per test
def test_field1():
    assert result.field1 == x

def test_field2():
    assert result.field2 == y

# Use fixtures
def test_with_fixture(sample_data):
    result = function(sample_data)

# Mock slow operations
@patch('time.sleep')
def test_fast(mock_sleep):
    function()  # Instant!

# Independent tests
def test_step1():
    state = create()
    assert state

def test_step2():
    state = create()  # Create fresh state
    update(state)
    assert state
```

## 🎯 Quick Checklist

Before committing tests, check:
- [ ] All tests pass
- [ ] Tests are independent
- [ ] Tests are fast (< 100ms each)
- [ ] Descriptive test names
- [ ] Follows AAA pattern
- [ ] Mocks external dependencies
- [ ] Tests behavior, not implementation
- [ ] Coverage > 80%

## 📚 Useful Assert Statements

```python
# Equality
assert result == expected
assert result != wrong_value

# Booleans
assert condition is True
assert condition is False

# None checks
assert value is None
assert value is not None

# Type checks
assert isinstance(result, MyClass)

# Membership
assert item in collection
assert item not in collection

# Comparisons
assert value > 0
assert value >= 0
assert value < 100

# String checks
assert "substring" in text
assert text.startswith("prefix")
assert text.endswith("suffix")

# Collection checks
assert len(collection) == 5
assert not collection  # Empty

# Attribute checks
assert hasattr(obj, 'attribute')

# Custom messages
assert result == expected, f"Expected {expected}, got {result}"
```

## 🔧 Mock Configuration

```python
from unittest.mock import Mock, AsyncMock, MagicMock, ANY

# Basic mock
mock = Mock()
mock.method.return_value = value

# Async mock
async_mock = AsyncMock()
await async_mock.method()

# Mock properties
mock = Mock()
mock.property = "value"

# Mock with spec (only allows real methods)
mock = Mock(spec=RealClass)

# Match any value in assertion
mock.method.assert_called_with(ANY, specific_value)

# Mock magic methods
mock = MagicMock()
len(mock)  # Works with magic methods
```

## 🎨 Test Organization

```
tests/
├── unit/
│   ├── test_handlers.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   └── test_endpoints.py
├── conftest.py  # Shared fixtures
└── __init__.py
```

## 💡 Pro Tips

1. **Test file naming**: `test_*.py` or `*_test.py`
2. **Test class naming**: `Test*` (e.g., `TestGroupHandler`)
3. **Test method naming**: `test_*` (e.g., `test_create_group`)
4. **One assert per test** (or closely related asserts)
5. **Use fixtures** for repeated test data
6. **Mock external dependencies** only
7. **Keep tests simple** - Tests should be easier than the code
8. **Test edge cases** - null, empty, boundary values
9. **Fast tests** - Use mocks to avoid slow operations
10. **Independent tests** - Tests should not share state

## 📖 Resources

- Pytest docs: https://docs.pytest.org/
- Unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Testing best practices: https://testingpyramid.com/

---

**Remember: Good tests = Confident refactoring!** 🚀
