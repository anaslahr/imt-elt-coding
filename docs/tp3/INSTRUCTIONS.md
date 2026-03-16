# TP3 — Testing, Logging & Data Quality

## 📖 Context

Your ELT pipeline works end-to-end — Bronze, Silver, Gold layers are populated. But in production, "it works on my machine" is not enough. Data pipelines must be:

- **Tested**: Unit tests ensure each function works correctly in isolation
- **Observable**: Structured logs let you trace what happened when something goes wrong
- **Reliable**: Error handling prevents a single bad row from crashing the entire pipeline

In this TP, you will harden your pipeline for production readiness.

---

## 🎯 Objective

1. Write **pytest unit tests** for your transform functions (mock the database)
2. Replace `print()` with **structured logging** (JSON format)
3. Add proper **error handling** with meaningful messages
4. Aim for **≥80% test coverage** on your `src/` modules

**Files you will create / modify:**
- `tests/test_transform.py` — Unit tests for Silver transforms
- `tests/test_extract.py` — Unit tests for extraction functions
- `tests/conftest.py` — Shared pytest fixtures
- `src/transform.py`, `src/extract.py`, `src/gold.py` — Add logging + error handling

---

## 📋 Prerequisites

- TP1 & TP2 completed (full pipeline working)
- Install test dependencies:

```bash
pip install pytest pytest-cov pytest-mock
```

Add them to `requirements.txt`:
```
pytest>=7.0
pytest-cov>=4.0
pytest-mock>=3.10
```

---

## Step 1 — Unit Tests for Transform Functions (45 min)

### Principle

Unit tests verify that each function works correctly **without needing a database**. We use `unittest.mock` to replace database calls with fake data.

### 1.1 Create the test structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_transform.py     # Silver layer tests
└── test_extract.py       # Bronze layer tests
```

### 1.2 Create shared fixtures (`tests/conftest.py`)

```python
import pytest
import pandas as pd


@pytest.fixture
def sample_products():
    """Fake products DataFrame mimicking Bronze data."""
    return pd.DataFrame({
        "product_id": [1, 2, 3],
        "display_name": ["Nike Air Max", "Adidas Ultraboost", "Jordan 1"],
        "brand": ["Nike", "Adidas", "Jordan"],
        "category": ["sneakers", "sneakers", "sneakers"],
        "price_usd": [149.99, 179.99, -10.00],  # one invalid price
        "tags": ["running|casual", "running|boost", "retro|hype"],
        "is_active": [1, 1, 0],
        "is_hype_product": [0, 0, 1],
        "_internal_cost_usd": [50.0, 60.0, 70.0],
        "_supplier_id": ["SUP001", "SUP002", "SUP003"],
    })


@pytest.fixture
def sample_users():
    """Fake users DataFrame mimicking Bronze data."""
    return pd.DataFrame({
        "user_id": [1, 2],
        "email": [" Alice@Example.COM ", "bob@test.com"],
        "first_name": ["Alice", "Bob"],
        "last_name": ["Martin", "Smith"],
        "loyalty_tier": ["gold", None],
        "_hashed_password": ["abc123", "def456"],
        "_last_ip": ["1.2.3.4", "5.6.7.8"],
        "_device_fingerprint": ["fp1", "fp2"],
    })


@pytest.fixture
def sample_orders():
    """Fake orders DataFrame mimicking Bronze data."""
    return pd.DataFrame({
        "order_id": [1, 2, 3],
        "user_id": [1, 2, 1],
        "order_date": ["2026-02-10", "2026-02-11", "2026-02-12"],
        "status": ["delivered", "shipped", "invalid_status"],
        "total_usd": [149.99, 179.99, 50.0],
        "coupon_code": ["SAVE10", None, None],
        "_stripe_charge_id": ["ch_1", "ch_2", "ch_3"],
        "_fraud_score": [0.1, 0.2, 0.9],
    })
```

### 1.3 Write transform tests (`tests/test_transform.py`)

Create a test file that tests your Silver transform functions **without needing a real database**. Use `unittest.mock.patch` to replace `_read_bronze` and `_load_to_silver` with mock objects.

**Structure your tests into classes:**

```python
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.transform import (
    _drop_internal_columns,
    transform_products,
    transform_users,
    transform_orders,
)


class TestDropInternalColumns:
    """Tests for the _drop_internal_columns() helper."""
    # Test that columns starting with '_' are removed
    # Test that regular columns are kept
    # Test edge case: empty DataFrame


class TestTransformProducts:
    """Tests for transform_products()."""
    # Mock _read_bronze to return sample_products fixture
    # Mock _load_to_silver so it doesn't hit the DB
    # Test that invalid prices (<=0) are removed
    # Test that tags are normalized ('|' replaced with ', ')
    # Test that boolean columns are converted


class TestTransformUsers:
    """Tests for transform_users()."""
    # Test that PII columns (_hashed_password, _last_ip, etc.) are removed
    # Test that NULL loyalty_tier is filled with 'none'
    # Test that emails are lowercased and stripped


class TestTransformOrders:
    """Tests for transform_orders()."""
    # Test that invalid statuses are flagged/removed
    # Test that order_date is converted to datetime
    # Test that NULL coupon_code is replaced with ''
```

**Key technique — mocking database calls:**

```python
@patch("src.transform._load_to_silver")   # mock the DB write
@patch("src.transform._read_bronze")      # mock the DB read
def test_something(self, mock_read, mock_load, sample_products):
    mock_read.return_value = sample_products  # inject fake data
    result = transform_products()             # call the real function
    # assert something about result...
```

> 💡 The `@patch` decorators are applied bottom-up: the first `@patch` in the list becomes the **last** argument. That's why `mock_read` comes before `mock_load` in the function signature.

Write **at least 2-3 tests per transform function** covering: normal behavior, edge cases, and data quality checks.

### 1.4 Run the tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing
```

**Goal:** ≥80% coverage on `src/transform.py`.

> ✅ **Checkpoint**: All tests pass, coverage ≥80%.

---

## Step 2 — Structured Logging (30 min)

### Principle

Replace `print()` statements with Python's `logging` module. In production, logs should be **structured** (JSON) so they can be parsed by monitoring tools.

### 2.1 Create a logging configuration

📁 **File:** `src/logger.py`

Create a module that provides a reusable logger with **JSON-formatted output**. Your logger should:

1. **Format logs as JSON** — each log line should be a JSON object with keys: `timestamp`, `level`, `module`, `function`, `message`
2. **Include exception info** when an error is logged
3. **Provide a `get_logger(name)` function** that creates a configured logger

**Useful classes:**
- `logging.Formatter` — subclass it to create a custom JSON formatter
- `logging.StreamHandler` — outputs to stdout
- `json.dumps()` — to serialize the log entry
- `datetime.now(timezone.utc).isoformat()` — for timestamps

> 💡 Check the [Python logging HOWTO](https://docs.python.org/3/howto/logging.html) and the [Formatter docs](https://docs.python.org/3/library/logging.html#logging.Formatter) for guidance.

### 2.2 Replace `print()` with logging

In `src/extract.py`, `src/transform.py`, and `src/gold.py`:

1. Import your logger: `from src.logger import get_logger`
2. Create a module-level logger: `logger = get_logger(__name__)`
3. Replace all `print()` calls:
   - Informational messages → `logger.info(...)`
   - Warnings (e.g. invalid data found) → `logger.warning(...)`
   - Errors → `logger.error(...)`

> 💡 Keep the same message content — just switch from `print()` to the appropriate log level.

### 2.3 Verify

Run the pipeline and observe JSON log output:

```bash
python pipeline.py --step extract
```

Expected output:
```json
{"timestamp": "2026-03-18T10:30:00Z", "level": "INFO", "module": "extract", "function": "extract_products", "message": "Products: 229 rows, 21 columns"}
```

> ✅ **Checkpoint**: All `print()` statements replaced with `logger.info()` / `logger.warning()` / `logger.error()`.

---

## Step 3 — Error Handling (20 min)

### Principle

A single bad row or network timeout should not crash the entire pipeline. Add `try/except` blocks with meaningful error messages.

### 3.1 Add error handling to extraction

Wrap each extract function in a `try/except` block:
- On success: the function works as before
- On failure: log the error with `logger.error()` including the exception message, then re-raise

This ensures errors are **logged** (observable) but still **propagated** (the caller knows something failed).

### 3.2 Add error handling to transforms

Same pattern for each transform function. The key is: **log, then re-raise**.

> 💡 Don't silently swallow exceptions with a bare `except: pass` — that hides bugs. Always re-raise or handle specifically.

### 3.3 Test error scenarios

Write tests that verify your error handling works correctly. Use `@patch` with `side_effect=Exception(...)` to simulate failures:

- What happens when `_read_bronze` raises an exception? Does `transform_products()` propagate it?
- Use `pytest.raises(Exception, match="...")` to assert the right error is raised

> 💡 Look at `unittest.mock.patch(side_effect=...)` in the [mock docs](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.side_effect).

---

## Step 4 — Test Coverage Report (15 min)

### 4.1 Generate a coverage report

```bash
pytest tests/ -v --cov=src --cov-report=html
open htmlcov/index.html
```

### 4.2 Identify untested code

Look at the coverage report and add tests for any uncovered lines. Priority targets:
- Edge cases (empty DataFrames, NULL values, invalid data)
- Error paths (database failures, S3 timeouts)
- Gold layer SQL queries (mock `pd.read_sql()`)

### 4.3 Goal

| Module | Target Coverage |
|--------|----------------|
| `src/transform.py` | ≥ 80% |
| `src/extract.py` | ≥ 70% |
| `src/gold.py` | ≥ 60% |
| `src/database.py` | ≥ 50% |

---

## 🎁 Bonus

1. **Integration tests**: Write tests that use a real database (SQLite in-memory or a test schema) to verify the full Bronze → Silver → Gold flow.
2. **Data quality assertions**: Add runtime assertions (e.g. "Gold daily_revenue total must equal Silver fct_orders total minus cancellations").
3. **Parametrized tests**: Use `@pytest.mark.parametrize` to test multiple scenarios with the same test function.
4. **Pre-commit hooks**: Set up `pre-commit` with `black`, `isort`, `flake8` to enforce code quality before each commit.

---

## 🔜 Next: TP4 — CI/CD & Industrialization

In the next TP, we will:
- Set up **GitHub Actions** to run tests automatically on every push
- Add **monitoring** and alerting for pipeline failures
- Package the pipeline for **production deployment**

---

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/en/stable/)
- [pytest-cov (Coverage)](https://pytest-cov.readthedocs.io/en/latest/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/why.html)
