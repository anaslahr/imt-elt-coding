"""
SOLUTION — Transform (Silver Layer)
"""

import pandas as pd
from sqlalchemy import text

from src.database import get_engine, BRONZE_SCHEMA, SILVER_SCHEMA

# TODO (TP3): Import your logger and create a module-level logger
#   1. from src.logger import get_logger
#   2. logger = get_logger(__name__)


def _read_bronze(table_name: str) -> pd.DataFrame:
    """Read a table from the Bronze schema via SQL."""
    engine = get_engine()
    query = f"SELECT * FROM {BRONZE_SCHEMA}.{table_name}"
    return pd.read_sql(query, engine)


def _drop_internal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove all columns whose name starts with '_'."""
    # TODO: Filter and drop columns starting with '_'
    # Steps: 1. Find columns that start with '_' (list comprehension on df.columns)
    #        2. Drop them with df.drop(columns=...)
    #        3. Print how many were removed, then return
    internal_cols = [col for col in df.columns if col.startswith("_")]
    df = df.drop(columns=internal_cols)
    print(f"    🧹 {len(internal_cols)} internal columns removed: {internal_cols}")
    return df


def _load_to_silver(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    """Load a DataFrame into a table in the Silver schema."""
    engine = get_engine()
    df.to_sql(
        name=table_name,
        con=engine,
        schema=SILVER_SCHEMA,
        if_exists=if_exists,
        index=False,
    )
    print(f"    ✅ {SILVER_SCHEMA}.{table_name} — {len(df)} rows loaded")


def transform_products() -> pd.DataFrame:
    """Transform bronze.products → silver.dim_products."""
    # TODO (TP3): Replace print() with logger.info() and wrap in try/except
    #   - Replace the print below with: logger.info("Transform: products → dim_products")
    #   - Wrap the entire function body in try/except:
    #       try:
    #           ... (existing code)
    #       except Exception as e:
    #           logger.error(f"Failed to transform products: {e}")
    #           raise   ← re-raise so the caller knows it failed
    print("  📦 Transform: products → dim_products")
    df = _read_bronze("products")

    # TODO: Step 1 — Drop internal columns (use the helper you wrote above)
    # 1. Remove internal columns
    df = _drop_internal_columns(df)

    # TODO: Step 2 — Normalize the 'tags' column
    # The tags use '|' as separator — replace with ', ' for cleanliness
    # Look at: .str.replace()
    # 2. Normalize the 'tags' column (replace '|' with ',')
    if "tags" in df.columns:
        df["tags"] = df["tags"].str.replace("|", ", ", regex=False)

    # TODO: Step 3 — Validate price_usd (remove rows where price <= 0)
    # 3. Validate price_usd (must be > 0)
    invalid_prices = df[df["price_usd"] <= 0]
    if len(invalid_prices) > 0:
        # TODO (TP3): Replace with logger.warning(...)
        print(f"    ⚠️  {len(invalid_prices)} products with price <= 0 (removed)")
    df = df[df["price_usd"] > 0]

    # TODO: Step 4 — Convert boolean columns (is_active, is_hype_product)
    # Look at: .astype(bool)
    # 4. Convert booleans
    for col in ["is_active", "is_hype_product"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    # TODO: Step 5 — Load into Silver as "dim_products"
    # 5. Load into Silver
    _load_to_silver(df, "dim_products")
    return df


def transform_users() -> pd.DataFrame:
    """Transform bronze.users → silver.dim_users."""
    # TODO (TP3): Same pattern — replace print with logger.info, add try/except + logger.error + raise
    print("  👤 Transform: users → dim_users")
    df = _read_bronze("users")

    # TODO: Step 1 — Drop internal columns (especially PII: passwords, IPs, fingerprints)
    # 1. Remove internal columns (including PII)
    df = _drop_internal_columns(df)

    # TODO: Step 2 — Replace NULL loyalty_tier with 'none'
    # Look at: .fillna()
    # 2. Replace loyalty_tier NULL with 'none'
    df["loyalty_tier"] = df["loyalty_tier"].fillna("none")

    # TODO: Step 3 — Normalize emails (lowercase + strip whitespace)
    # 3. Normalize emails
    df["email"] = df["email"].str.lower().str.strip()

    # TODO: Step 4 — Load into Silver as "dim_users"
    # 4. Load into Silver
    _load_to_silver(df, "dim_users")
    return df


def transform_orders() -> pd.DataFrame:
    """Transform bronze.orders → silver.fct_orders."""
    # TODO (TP3): Same pattern — replace print with logger.info, add try/except + logger.error + raise
    print("  🛍️ Transform: orders → fct_orders")
    df = _read_bronze("orders")

    # TODO: Step 1 — Drop internal columns
    # 1. Remove internal columns
    df = _drop_internal_columns(df)

    # TODO: Step 2 — Validate statuses
    # Only keep rows with a valid status. The valid set is in the docstring above.
    # Look at: .isin() and boolean indexing
    # 2. Validate statuses
    VALID_STATUSES = {"delivered", "shipped", "processing", "returned", "cancelled", "chargeback"}
    invalid = df[~df["status"].isin(VALID_STATUSES)]
    if len(invalid) > 0:
        # TODO (TP3): Replace with logger.warning(...)
        print(f"    ⚠️  {len(invalid)} orders with invalid status (removed)")
        df = df[df["status"].isin(VALID_STATUSES)]

    # TODO: Step 3 — Convert order_date to a proper datetime type
    # Look at: pd.to_datetime()
    # 3. Convert order_date to datetime
    df["order_date"] = pd.to_datetime(df["order_date"])

    # TODO: Step 4 — Replace NULL coupon_code with empty string
    # Look at: .fillna()
    # 4. Replace coupon_code NULL with ''
    df["coupon_code"] = df["coupon_code"].fillna("")

    # TODO: Step 5 — Load into Silver as "fct_orders"
    # 5. Load into Silver
    _load_to_silver(df, "fct_orders")
    return df


def transform_order_line_items() -> pd.DataFrame:
    """Transform bronze.order_line_items → silver.fct_order_lines."""
    # TODO (TP3): Same pattern — replace print with logger.info, add try/except + logger.error + raise
    print("  📋 Transform: order_line_items → fct_order_lines")
    df = _read_bronze("order_line_items")

    # TODO: Step 1 — Drop internal columns
    # 1. Remove internal columns
    df = _drop_internal_columns(df)

    # TODO: Step 2 — Validate quantity > 0 (remove invalid rows)
    # 2. Validate quantity > 0
    invalid_qty = df[df["quantity"] <= 0]
    if len(invalid_qty) > 0:
        # TODO (TP3): Replace with logger.warning(...)
        print(f"    ⚠️  {len(invalid_qty)} rows with quantity <= 0 (removed)")
    df = df[df["quantity"] > 0]

    # TODO: Step 3 — Verify line_total_usd ≈ unit_price_usd * quantity
    # Compute the difference, flag rows where abs(diff) > 0.01, then clean up
    # This is a data quality check — print how many bad rows you find
    # 3. Verify the line_total calculation
    df["_check"] = abs(df["line_total_usd"] - df["unit_price_usd"] * df["quantity"])
    bad_rows = df[df["_check"] > 0.01]
    if len(bad_rows) > 0:
        # TODO (TP3): Replace with logger.info(...)
        print(f"    ℹ️  {len(bad_rows)} rows with inconsistent line_total")
    df = df.drop(columns=["_check"])

    # TODO: Step 4 — Load into Silver as "fct_order_lines"
    # 4. Load into Silver
    _load_to_silver(df, "fct_order_lines")
    return df


def transform_all() -> dict[str, pd.DataFrame]:
    """Run the complete transformation from Bronze → Silver."""
    print(f"\n{'='*60}")
    print(f"  🥈 TRANSFORM → Silver ({SILVER_SCHEMA})")
    print(f"{'='*60}\n")

    results = {}

    # TODO: Call each transform_*() function and store the result in the dict
    # There are 4 functions to call, each returns a DataFrame
    # Keys should match the Silver table names: dim_products, dim_users, fct_orders, fct_order_lines
    results["dim_products"] = transform_products()
    results["dim_users"] = transform_users()
    results["fct_orders"] = transform_orders()
    results["fct_order_lines"] = transform_order_line_items()

    print(f"\n  ✅ Transformation complete — {len(results)} tables in {SILVER_SCHEMA}")
    return results


if __name__ == "__main__":
    transform_all()
