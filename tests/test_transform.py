"""
TP3 — Unit tests for src/transform.py
======================================

How do fixtures work?
---------------------
In conftest.py, we define functions decorated with @pytest.fixture,
e.g. sample_products(), sample_users(), sample_orders().

When a test has a parameter with the SAME NAME as a fixture,
pytest injects it automatically — no import needed:

    # conftest.py
    @pytest.fixture
    def sample_products():
        return pd.DataFrame({...})

    # test_transform.py
    def test_something(self, sample_products):
        #                     ↑ pytest sees this name, finds the fixture,
        #                       executes it and passes the result here

How does @patch work?
---------------------
transform_products() internally calls _read_bronze() (reads from PostgreSQL)
and _load_to_silver() (writes to PostgreSQL). In tests, we don't have a database.

@patch temporarily replaces these functions with fake objects (mocks):
  - mock_read  = fake _read_bronze  → we control what it returns
  - mock_load  = fake _load_to_silver → does nothing (prevents DB write)

Patches apply bottom-up, so the order of arguments is:
    @patch("src.transform._load_to_silver")  ← 2nd patch → 2nd arg (mock_load)
    @patch("src.transform._read_bronze")     ← 1st patch → 1st arg (mock_read)
    def test_xxx(self, mock_read, mock_load, sample_products):
"""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.transform import (
    _drop_internal_columns,
    transform_products,
    transform_users,
    transform_orders,
)


# =============================================================================
# Example class (complete) — use this as a reference for the classes below
# =============================================================================

class TestDropInternalColumns:
    """Tests for the _drop_internal_columns() helper."""

    def test_removes_internal_columns(self, sample_products):
        result = _drop_internal_columns(sample_products)
        internal_cols = [col for col in result.columns if col.startswith("_")]
        assert len(internal_cols) == 0

    def test_keeps_regular_columns(self, sample_products):
        result = _drop_internal_columns(sample_products)
        assert "product_id" in result.columns
        assert "brand" in result.columns

    def test_edge_case(self):
        df = pd.DataFrame({"_secret": [1], "name": ["a"]})
        result = _drop_internal_columns(df)
        assert list(result.columns) == ["name"]


# =============================================================================
# TODO: Complete the 3 classes below
# =============================================================================

class TestTransformProducts:
    """Tests for transform_products()."""

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_removes_invalid_prices(self, mock_read, mock_load, sample_products):
        # TODO: Test that products with price_usd <= 0 are removed
        # Steps:
        #   1. mock_read.return_value = sample_products  (inject fake data)
        #   2. result = transform_products()              (call the real function)
        #   3. Assert that result has only 2 rows (the one with price -10 is gone)
        #   4. Assert that all remaining prices are > 0
        pass

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_normalizes_tags(self, mock_read, mock_load, sample_products):
        # TODO: Test that '|' in tags is replaced with ', '
        # After transform, "running|casual" should become "running, casual"
        # Hint: assert not result["tags"].str.contains("|", regex=False).any()
        pass

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_converts_booleans(self, mock_read, mock_load, sample_products):
        # TODO: Test that is_active and is_hype_product are converted to bool
        # Hint: result["is_active"].dtype == bool
        pass


class TestTransformUsers:
    """Tests for transform_users()."""

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_removes_pii_columns(self, mock_read, mock_load, sample_users):
        # TODO: Test that internal columns (_hashed_password, _last_ip, _device_fingerprint)
        # are removed from the result
        pass

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_fills_null_loyalty_tier(self, mock_read, mock_load, sample_users):
        # TODO: Test that NULL loyalty_tier values are replaced with "none"
        # Hint: result["loyalty_tier"].notna().all()
        pass

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_normalizes_emails(self, mock_read, mock_load, sample_users):
        # TODO: Test that emails are lowercased and stripped of whitespace
        # " Alice@Example.COM " should become "alice@example.com"
        pass


class TestTransformOrders:
    """Tests for transform_orders()."""

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_removes_invalid_statuses(self, mock_read, mock_load, sample_orders):
        # TODO: Test that rows with invalid statuses are removed
        # "invalid_status" is not in the valid set → should be filtered out
        pass

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_converts_order_date(self, mock_read, mock_load, sample_orders):
        # TODO: Test that order_date is converted to datetime type
        # Hint: "datetime" in str(result["order_date"].dtype)
        pass

    @patch("src.transform._load_to_silver")
    @patch("src.transform._read_bronze")
    def test_replaces_null_coupon_code(self, mock_read, mock_load, sample_orders):
        # TODO: Test that NULL coupon_code values are replaced with ""
        # Hint: result["coupon_code"].notna().all()
        pass
