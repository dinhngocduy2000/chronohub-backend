# Quick Start: Testing Your FastAPI Application

This guide will get you up and running with testing in 5 minutes.

## 1. Install Testing Dependencies

```bash
make install-dev
```

Or manually:

```bash
pip install -r requirements-dev.txt
```

## 2. Run Your First Test

```bash
make test
```

You should see output like:

```
collected 11 items

tests/unit/test_group_handler.py::TestGroupHandler::test_create_group_success PASSED
tests/unit/test_group_handler.py::TestGroupHandler::test_create_group_with_exception PASSED
tests/unit/test_group_service.py::TestGroupService::test_create_group_success PASSED
...

========== 11 passed in 2.34s ==========
```

## 3. Understanding the Test Structure

### Your endpoint code (app/router/group.py):

```python
self.router.add_api_route(
    path="/create",
    endpoint=self.handler.create_group,
    methods=["POST"],
    response_model=GroupInfo,
    status_code=status.HTTP_201_CREATED,
)
```

### Unit test (tests/unit/test_group_handler.py):

```python
@pytest.mark.asyncio
async def test_create_group_success(
    mock_group_service,      # Mocked dependencies
    sample_group_create_dto, # Test data
    mock_credential          # Mocked user
):
    # Arrange - Set up mocks
    mock_group_service.create_group.return_value = sample_group_info
    handler = GroupHandler(service=mock_group_service)

    # Act - Call the method
    result = await handler.create_group(
        group_create=sample_group_create_dto,
        credential=mock_credential
    )

    # Assert - Verify the result
    assert result.name == "Test Group"
    mock_group_service.create_group.assert_called_once()
```

### Integration test (tests/integration/test_group_endpoints.py):

```python
def test_create_group_endpoint_success(test_client, mock_group_service):
    # Arrange - Prepare request
    request_data = {
        "name": "Test Group",
        "description": "Test Description"
    }
    
    # Act - Make HTTP request
    response = test_client.post(
        "/api/v1/groups/create",
        json=request_data
    )
    
    # Assert - Check response
    assert response.status_code == 201
    assert response.json()["name"] == "Test Group"
```

## 4. Test Your Own Endpoint

Let's say you have a new endpoint in `app/router/task.py`:

```python
self.router.add_api_route(
    path="/create",
    endpoint=self.handler.create_task,
    methods=["POST"],
)
```

Create `tests/unit/test_task_handler.py`:

```python
import pytest
from app.handler.task import TaskHandler

class TestTaskHandler:
    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_task_service):
        # Arrange
        handler = TaskHandler(service=mock_task_service)
        task_data = {"title": "Test Task"}
        
        # Act
        result = await handler.create_task(task_data)
        
        # Assert
        assert result is not None
        mock_task_service.create_task.assert_called_once()
```

## 5. Common Testing Patterns

### Testing Success Cases

```python
def test_success(test_client):
    response = test_client.post("/endpoint", json={"data": "value"})
    assert response.status_code == 200
    assert response.json()["field"] == "expected_value"
```

### Testing Validation Errors

```python
def test_missing_required_field(test_client):
    response = test_client.post("/endpoint", json={})
    assert response.status_code == 422  # Validation error
```

### Testing Business Logic Errors

```python
def test_duplicate_name(mock_service):
    mock_service.create.side_effect = BadRequestException("Already exists")
    
    with pytest.raises(BadRequestException) as exc:
        await handler.create(data)
    
    assert "Already exists" in str(exc.value.message)
```

### Testing with Mocks

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    mock_service = AsyncMock()
    mock_service.get_data.return_value = {"id": 1}
    
    result = await mock_service.get_data()
    assert result["id"] == 1
```

## 6. Useful Commands

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run with coverage report
make test-cov

# Run specific test file
pytest tests/unit/test_group_handler.py

# Run specific test function
pytest tests/unit/test_group_handler.py::TestGroupHandler::test_create_group_success

# Run tests matching a pattern
pytest -k "create_group"

# Run in verbose mode
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

## 7. Debugging Failed Tests

When a test fails, pytest shows:

```
FAILED tests/unit/test_group_handler.py::test_create_group_success - AssertionError: assert 'Wrong Name' == 'Test Group'
```

To debug:

1. **Check the assertion:**
   ```python
   assert result.name == "Test Group"  # What did result.name actually contain?
   ```

2. **Add print statements:**
   ```python
   print(f"Result: {result}")  # Run with pytest -s
   ```

3. **Check mock calls:**
   ```python
   mock_service.create_group.assert_called_once_with(expected_args)
   ```

4. **Run only that test:**
   ```bash
   pytest tests/unit/test_group_handler.py::test_create_group_success -v
   ```

## 8. Next Steps

1. ✅ Read the full [Testing Guide](TESTING_GUIDE.md)
2. ✅ Check [tests/README.md](tests/README.md) for test structure
3. ✅ Write tests for your own endpoints
4. ✅ Aim for >80% code coverage
5. ✅ Run tests before committing code

## 9. Common Issues

### "ModuleNotFoundError"

```bash
# Make sure you're in the project root and venv is activated
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### "No tests ran"

```bash
# Check you're in the correct directory
pwd  # Should be /path/to/chronohub-backend

# Check test files follow naming convention
ls tests/  # Should have test_*.py files
```

### "Import errors in tests"

```bash
# Make sure app is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Or add to pytest.ini:

```ini
[pytest]
pythonpath = .
```

## 10. Example: Testing Your `create_group` Endpoint

The endpoint you selected is already tested! Check:

- **Unit test:** `tests/unit/test_group_handler.py`
- **Service test:** `tests/unit/test_group_service.py`
- **Integration test:** `tests/integration/test_group_endpoints.py`

Run these specific tests:

```bash
# Test the handler
pytest tests/unit/test_group_handler.py -v

# Test the service
pytest tests/unit/test_group_service.py -v

# Test the endpoint
pytest tests/integration/test_group_endpoints.py -v
```

## Need Help?

- 📚 Full guide: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- 📁 Test examples: `tests/` directory
- 🔍 Pytest docs: https://docs.pytest.org/
- 🚀 FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/

Happy testing! 🎉
