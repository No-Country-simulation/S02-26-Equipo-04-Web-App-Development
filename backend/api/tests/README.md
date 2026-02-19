# 🧪 Testing Guide - NoCountry Video API

## Overview
This directory contains comprehensive tests for the FastAPI backend using pytest.

**SAFETY GUARANTEED:** All tests use SQLite in-memory databases. Your development/production PostgreSQL databases are never touched.

**Total:** 58 tests ✅
- **53 Unit Tests** (services + endpoints with mocks)
- **5 E2E Tests** (complete multi-step workflows)

---

## 📁 Structure

```
tests/
├── conftest.py                  # Pytest fixtures (db, users, auth, UUID support)
├── unit/
│   ├── test_auth_service.py     # AuthService tests (18 tests)
│   ├── test_user_service.py     # UserService tests (13 tests)
│   ├── test_auth_endpoints.py   # Auth endpoints tests (22 tests)
│   └── __init__.py
├── e2e/
│   ├── test_auth_flows.py       # End-to-end auth flows (5 tests)
│   └── __init__.py
└── __init__.py
```

---

## 🚀 Running Tests

### Run all tests (unit + e2e):
```bash
pytest
# or in Docker:
docker exec fastapi pytest tests/ -v
```

### Run only unit tests:
```bash
pytest tests/unit/
```

### Run only E2E tests:
```bash
pytest tests/e2e/
```

### Run by marker:
```bash
pytest -m unit        # Only unit tests
pytest -m e2e         # Only E2E tests
pytest -m auth        # All auth-related tests
pytest -m "not slow"  # Skip slow tests
```

### Run specific test file:
```bash
pytest tests/unit/test_auth_service.py
pytest tests/e2e/test_auth_flows.py
```

### Run specific test class:
```bash
pytest tests/unit/test_auth_service.py::TestAuthServiceRegister
pytest tests/e2e/test_auth_flows.py::TestCompleteAuthFlows
```

### Run specific test:
```bash
pytest tests/unit/test_auth_service.py::TestAuthServiceRegister::test_register_user_success
pytest tests/e2e/test_auth_flows.py::TestCompleteAuthFlows::test_complete_registration_login_profile_flow
```

### Run with verbose output:
```bash
pytest -v
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

---

## 🏷️ Test Categories (Markers)

Tests are organized with markers for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only E2E tests
pytest -m e2e

# Run only auth-related tests
pytest -m auth

# Run only user management tests
pytest -m user

# Skip slow tests
pytest -m "not slow"
```

Available markers:
- `unit`: Unit tests (fast, isolated)
- `e2e`: End-to-end tests (complete workflows)
- `integration`: Integration tests (may touch external services)
- `slow`: Tests that take more than 1 second
- `auth`: Authentication related tests
- `user`: User management tests
- `profile`: Profile management tests

---

## 📊 Test Coverage

### Unit Tests (53 total):
- **AuthService**: 18 tests
  - Registration: 5 tests
  - Authentication: 6 tests
  - Token Creation: 5 tests
  - Integration: 2 tests

- **UserService**: 13 tests
  - Get User: 3 tests
  - Update User: 8 tests
  - Integration: 2 tests

- **Auth Endpoints**: 22 tests
  - Register: 8 tests (with mocks)
  - Login: 6 tests (with mocks)
  - Me: 4 tests (with mocks)
  - Refresh: 2 tests (with mocks)
  - Logout: 2 tests (with mocks)

### E2E Tests (5 total):
- **Complete Authentication Flows**: 5 tests
  - Registration → Login → Profile → Refresh
  - Register → Profile → Logout
  - Access without token → With token
  - Duplicate registration validation
  - Login error recovery

---

## 🛡️ Safety Features

### Database Isolation:
✅ **SQLite in-memory database** for all tests  
✅ **Fresh database** for each test (function scope)  
✅ **Automatic cleanup** after each test  
✅ **No connection** to real PostgreSQL  
✅ **UUID support** for SQLite via GUID TypeDecorator

### How it works:
```python
@pytest.fixture(scope="function")
def db_session(db_engine):
    """Each test gets a fresh, isolated database session."""
    session = TestingSessionLocal()
    yield session
    session.rollback()  # Cleanup
    session.close()
```

---

## 📝 Writing New Tests

### Unit Test Template:
```python
class TestYourServiceName:
    """Tests for YourService."""
    
    def test_your_function_success(self, db_session: Session):
        """
        Test: Description of what you're testing.
        
        Validates:
        - What should happen
        - Expected behavior
        """
        # Arrange
        service = YourService(db_session)
        test_data = {...}
        
        # Act
        result = service.your_function(test_data)
        
        # Assert
        assert result.field == expected_value
```

### Best Practices:
1. **AAA Pattern**: Arrange, Act, Assert
2. **Descriptive names**: `test_register_user_success`
3. **Docstrings**: Explain what and why
4. **Use fixtures**: Don't create data manually
5. **Test edge cases**: Not just happy path
6. **One assertion concept per test**: Keep tests focused

### E2E Test Template:
```python
@pytest.mark.e2e
@pytest.mark.auth
class TestCompleteAuthFlows:
    """E2E tests for complete authentication workflows"""
    
    def test_complete_flow(self, client: TestClient):
        """
        E2E Flow: Step 1 → Step 2 → Step 3
        
        Steps:
        1. Action 1
        2. Action 2
        3. Verify outcome
        
        Validates:
        - Data consistency across steps
        - Persistence between requests
        """
        # Step 1: First action
        response1 = client.post("/endpoint1", json=data1)
        assert response1.status_code == 201
        
        # Step 2: Use result from step 1
        token = response1.json()["access_token"]
        response2 = client.get("/endpoint2", headers={"Authorization": f"Bearer {token}"})
        assert response2.status_code == 200
        
        # Step 3: Verify final state
        assert response2.json()["field"] == expected_value
```

---

## 🔧 Fixtures Available

### Database:
- `db_session`: SQLAlchemy session with SQLite
- `db_engine`: SQLite engine

### Users:
- `sample_user`: Active, unverified user
- `inactive_user`: Inactive user
- `verified_user`: Active, verified user
- `multiple_users`: List of 5 users
- `authenticated_user`: User with JWT token

### Data:
- `sample_user_data`: Registration data dict
- `sample_profile_update`: Profile update data
- `auth_headers`: HTTP headers with Bearer token

### HTTP:
- `client`: FastAPI TestClient (with overridden dependencies)

---

## 🐛 Debugging Failed Tests

### Show full traceback:
```bash
pytest --tb=long
```

### Stop at first failure:
```bash
pytest -x
```

### Run only failed tests:
```bash
pytest --lf
```

### Print output:
```bash
pytest -s
```

---

## 📦 Dependencies

Required packages (in requirements.txt):
```
pytest==8.0.0
pytest-asyncio==0.23.4
httpx==0.26.0
faker==22.6.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## 🎯 Test Naming Convention

Format: `test_<what>_<scenario>`

Examples:
- ✅ `test_register_user_success`
- ✅ `test_authenticate_user_wrong_password`
- ✅ `test_update_user_duplicate_email`
- ❌ `test_user` (too vague)
- ❌ `testRegisterUser` (wrong naming)

---

## 🔍 Common Patterns

### Testing Exceptions:
```python
with pytest.raises(YourException):
    service.function_that_should_fail()
```

### Testing Database Changes:
```python
user = service.create_user(data)
db_session.refresh(user)  # Reload from DB
assert user.field == expected
```

### Testing Timestamps:
```python
before = datetime.utcnow()
user = service.create_user(data)
assert user.created_at > before
assert user.created_at < datetime.utcnow()
```

---

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

---

## ✅ Checklist Before Pushing

- [ ] All tests pass: `pytest`
- [ ] No warnings: `pytest --strict-warnings`
- [ ] Coverage above 80%: `pytest --cov=app`
- [ ] New features have tests
- [ ] Tests follow AAA pattern
- [ ] Descriptive test names
- [ ] Docstrings added

---

**Happy Testing! 🧪✨**
