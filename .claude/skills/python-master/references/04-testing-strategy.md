
# Python Library Testing

## Quick Start

```bash
pytest                              # Run tests
pytest --cov=my_library             # With coverage
pytest -x                           # Stop on first failure
pytest -k "test_encode"             # Run matching tests
```

## Pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q --cov=my_library --cov-fail-under=85"

[tool.coverage.run]
branch = true
source = ["src/my_library"]
```

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_encoding.py
└── test_decoding.py
```

## Essential Patterns

**Basic test:**
```python
def test_encode_valid_input():
    result = encode(37.7749, -122.4194)
    assert isinstance(result, str)
    assert len(result) == 12
```

**Parametrization:**
```python
@pytest.mark.parametrize("lat,lon,expected", [
    (37.7749, -122.4194, "9q8yy"),
    (40.7128, -74.0060, "dr5ru"),
])
def test_known_values(lat, lon, expected):
    assert encode(lat, lon, precision=5) == expected
```

**Fixtures:**
```python
@pytest.fixture
def sample_data():
    return [(37.7749, -122.4194), (40.7128, -74.0060)]

def test_batch(sample_data):
    results = batch_encode(sample_data)
    assert len(results) == 2
```

**Mocking:**
```python
def test_api_call(mocker):
    mocker.patch("my_lib.client.fetch", return_value={"data": []})
    result = my_lib.get_data()
    assert result == []
```

**Exception testing:**
```python
def test_invalid_raises():
    with pytest.raises(ValueError, match="latitude"):
        encode(91.0, 0.0)
```

For detailed patterns, see:
- **[FIXTURES.md](FIXTURES.md)** - Advanced fixture patterns
- **[HYPOTHESIS.md](HYPOTHESIS.md)** - Property-based testing
- **[CI.md](CI.md)** - CI/CD test configuration

## Test Principles

| Principle | Meaning |
|-----------|---------|
| Independent | No shared state between tests |
| Deterministic | Same result every run |
| Fast | Unit tests < 100ms each |
| Focused | Test behavior, not implementation |

## Checklist

```
Testing:
- [ ] Tests exist for public API
- [ ] Edge cases covered (empty, boundary, error)
- [ ] No external service dependencies (mock them)
- [ ] Coverage > 85%
- [ ] Tests run in CI
```

## Learn More

This skill is based on the [Code Quality](https://mcginniscommawill.com/guides/python-library-development/#code-quality-the-foundation) section of the [Guide to Developing High-Quality Python Libraries](https://mcginniscommawill.com/guides/python-library-development/) by [Will McGinnis](https://mcginniscommawill.com/). See these posts for deeper coverage:

- [Testing with Pytest](https://mcginniscommawill.com/posts/2025-02-04-testing-pytest-intro/)
- [Testing Coverage](https://mcginniscommawill.com/posts/2025-02-09-testing-coverage/)
- [Testing with Tox](https://mcginniscommawill.com/posts/2025-02-13-testing-tox/)
- [Testing with Mocking](https://mcginniscommawill.com/posts/2025-02-16-testing-mocking/)

---

## Reference: FIXTURES

# Pytest Fixtures Reference

## Fixture Scopes

```python
@pytest.fixture  # function scope (default) - runs per test
@pytest.fixture(scope="class")    # per test class
@pytest.fixture(scope="module")   # per test file
@pytest.fixture(scope="session")  # once per test run
```

## Common Patterns

### Setup/Teardown

```python
@pytest.fixture
def database():
    conn = create_connection()
    yield conn  # Test runs here
    conn.close()  # Cleanup after test
```

### Factory Fixtures

```python
@pytest.fixture
def make_user():
    def _make_user(name="Test", email="test@example.com"):
        return User(name=name, email=email)
    return _make_user

def test_users(make_user):
    user1 = make_user(name="Alice")
    user2 = make_user(name="Bob")
```

### Temporary Files

```python
@pytest.fixture
def config_file(tmp_path):
    config = tmp_path / "config.json"
    config.write_text('{"key": "value"}')
    return config
```

### Mocking External Services

```python
@pytest.fixture
def mock_api(mocker):
    return mocker.patch(
        "my_lib.client.requests.get",
        return_value=Mock(json=lambda: {"data": []})
    )
```

## conftest.py

Shared fixtures go in `tests/conftest.py`:

```python
import pytest

@pytest.fixture
def sample_coordinates():
    return [
        (37.7749, -122.4194),
        (40.7128, -74.0060),
    ]
```

All tests in the directory can use these fixtures automatically.

---

## Reference: HYPOTHESIS

# Property-Based Testing with Hypothesis

## Installation

```bash
pip install hypothesis
```

## Basic Usage

```python
from hypothesis import given, strategies as st

@given(st.integers())
def test_integer_property(n):
    assert abs(n) >= 0

@given(st.text())
def test_string_roundtrip(s):
    assert decode(encode(s)) == s
```

## Common Strategies

```python
# Numbers
st.integers(min_value=0, max_value=100)
st.floats(min_value=-90, max_value=90)

# Text
st.text(min_size=1, max_size=100)
st.text(alphabet="abc123")

# Collections
st.lists(st.integers(), min_size=0, max_size=10)
st.dictionaries(st.text(), st.integers())

# Tuples
st.tuples(st.floats(), st.floats())

# Composite
@st.composite
def coordinates(draw):
    lat = draw(st.floats(min_value=-90, max_value=90))
    lon = draw(st.floats(min_value=-180, max_value=180))
    return (lat, lon)
```

## Filtering Invalid Data

```python
from hypothesis import assume

@given(st.floats())
def test_with_valid_floats(x):
    assume(not math.isnan(x))  # Skip NaN values
    assume(x != 0)              # Skip zero
    result = 1 / x
    assert math.isfinite(result)
```

## Settings

```python
from hypothesis import settings

@settings(max_examples=200)  # More thorough
@given(st.integers())
def test_thorough(n):
    ...

@settings(deadline=None)  # No time limit
@given(st.lists(st.integers()))
def test_slow_operation(items):
    ...
```

## Example: Roundtrip Testing

```python
@given(
    st.floats(min_value=-90, max_value=90, allow_nan=False),
    st.floats(min_value=-180, max_value=180, allow_nan=False),
)
def test_encode_decode_roundtrip(lat, lon):
    encoded = encode(lat, lon, precision=12)
    decoded_lat, decoded_lon = decode(encoded)
    assert abs(decoded_lat - lat) < 0.0001
    assert abs(decoded_lon - lon) < 0.0001
```
