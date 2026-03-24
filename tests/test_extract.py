"""
TP3 — Unit tests for src/extract.py
=====================================

These tests verify that extraction functions correctly read from S3
and load into Bronze, without needing real AWS or database connections.

We mock:
  - _get_s3_client → so we don't need real AWS credentials
  - _load_to_bronze → so we don't need a real database
  - _read_csv_from_s3 / _read_jsonl_from_s3 → to inject fake data
"""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.extract import (
    extract_products,
    extract_users,
    extract_orders,
)


class TestExtractProducts:
    """Tests for extract_products()."""

    @patch("src.extract._load_to_bronze")
    @patch("src.extract._read_csv_from_s3")
    def test_extracts_and_loads(self, mock_read_csv, mock_load, sample_products):
        # TODO: Test that extract_products reads from S3 and loads to Bronze
        # Steps:
        #   1. mock_read_csv.return_value = sample_products
        #   2. result = extract_products()
        #   3. Assert result has the expected number of rows
        #   4. Assert mock_load was called (mock_load.assert_called_once())
        pass

    @patch("src.extract._load_to_bronze")
    @patch("src.extract._read_csv_from_s3")
    def test_returns_dataframe(self, mock_read_csv, mock_load, sample_products):
        # TODO: Test that the function returns a pandas DataFrame
        # Hint: isinstance(result, pd.DataFrame)
        pass


class TestExtractUsers:
    """Tests for extract_users()."""

    @patch("src.extract._load_to_bronze")
    @patch("src.extract._read_csv_from_s3")
    def test_extracts_and_loads(self, mock_read_csv, mock_load, sample_users):
        # TODO: Same pattern as TestExtractProducts
        pass


class TestExtractOrders:
    """Tests for extract_orders()."""

    @patch("src.extract._load_to_bronze")
    @patch("src.extract._read_csv_from_s3")
    def test_extracts_and_loads(self, mock_read_csv, mock_load, sample_orders):
        # TODO: Same pattern as TestExtractProducts
        pass
