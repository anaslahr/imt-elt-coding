# TP2 — Silver & Gold Layers: Clean, Conform, Aggregate

## 📖 Recap

In TP1, you built the **Bronze layer**: raw data from S3 (CSV, JSONL, and Parquet) is now loaded into 6 PostgreSQL tables. But the Bronze data is "dirty":
- It contains **internal columns** prefixed with `_` (cost data, supplier IDs, debug fields)
- It contains **PII** (hashed passwords, IP addresses, device fingerprints)
- Data types may be wrong (dates stored as strings, booleans as integers)
- Some values are NULL or invalid

The e-commerce team **still can't answer their questions** from raw data alone. We need to clean it.

---

## 🎯 Objective

1. **Silver**: Clean and conform Bronze data (remove `_*` columns, handle PII, validate data types)
2. **Gold**: Create business-ready aggregation tables that answer the e-commerce team's questions:
   - 📊 *"How much revenue are we generating day by day?"* → `gold.daily_revenue`
   - 🏆 *"Which products sell the most?"* → `gold.product_performance`
   - 💰 *"Who are our top customers?"* → `gold.customer_ltv`

**Files you will work on:**
- `src/transform.py` — Silver transformation (Bronze → Silver)
- `src/gold.py` — Gold aggregations (Silver → Gold)

---

## 📋 Prerequisites

- TP1 completed (Bronze tables populated in PostgreSQL)
- Same environment as TP1 (`.env` configured, `venv` active)

---

## Step 1 — Transform: Bronze → Silver (45 min)

📁 **File:** `src/transform.py`

### Principle

The Silver layer contains **cleaned and conformed** data:
- ❌ No more internal columns (`_*`)
- ❌ No more sensitive PII (passwords, IPs)
- ✅ Correct data types
- ✅ NULL values handled
- ✅ Validated data

### Naming conventions

| Bronze table | Silver table | Type |
|-------------|-------------|------|
| `products` | `dim_products` | Dimension (descriptive attributes) |
| `users` | `dim_users` | Dimension |
| `orders` | `fct_orders` | Fact (business events) |
| `order_line_items` | `fct_order_lines` | Fact |

> 💡 `dim_` = dimension tables (slowly changing reference data), `fct_` = fact tables (transactional events). This is standard data warehouse naming.

> 📝 **Note**: In TP1 you also loaded `reviews` (JSONL) and `clickstream` (Parquet) into Bronze. For this TP, we focus on transforming the 4 core tables above. Reviews and clickstream transforms are available as a **bonus** exercise.

### 1.1 Implement `_drop_internal_columns()`

This is the core cleaning function — it removes all columns prefixed with `_`.

**Steps:**
1. Find all column names that start with `_` (use a list comprehension on `df.columns`)
2. Drop them from the DataFrame
3. Print how many were removed (for logging/debugging)
4. Return the cleaned DataFrame


Answer:
"""
# Step 1
df = _drop_internal_columns(df)

# Step 2
if 'quantity' in df.columns:
  df = df[df['quantity'] > 0]

# Step 3
if 'line_total_usd' in df.columns and 'unit_price_usd' in df.columns and 'quantity' in df.columns:
  expected_total = df['unit_price_usd'] * df['quantity']
  difference = abs(df['line_total_usd'] - expected_total)
  bad_rows = difference > 0.01
  if bad_rows.sum() > 0:
      print(f"      Removed {bad_rows.sum()} rows with incorrect line totals")
  df = df[~bad_rows]

# Step 4
_load_to_silver(df, "fct_order_lines")

return df
"""

### 1.2 Implement `transform_products()`

Follow the steps in the code comments:
1. Remove `_*` columns (e.g. `_internal_cost_usd`, `_supplier_id`)
2. Normalize `tags` (replace `|` with `,`)
3. Validate `price_usd > 0` (drop invalid rows)
4. Convert `is_active` and `is_hype_product` to booleans
5. Load into `silver.dim_products`

Answer:
"""
# Step 1
df = _drop_internal_columns(df)

# Step 2
if 'tags' in df.columns:
    df['tags'] = df['tags'].str.replace('|', ', ')

# Step 3
if 'price_usd' in df.columns:
    df = df[df['price_usd'] > 0]

# Step 4
if 'is_active' in df.columns:
    df['is_active'] = df['is_active'].astype(bool)
if 'is_hype_product' in df.columns:
    df['is_hype_product'] = df['is_hype_product'].astype(bool)

# Step 5
_load_to_silver(df, "dim_products")

return df
"""

### 1.3 Implement `transform_users()`

⚠️ **PII Warning**: The Silver layer must NEVER contain passwords, IPs, or fingerprints.

1. Remove `_*` columns (8 columns — `_hashed_password`, `_ga_client_id`, `_fbp`, `_device_fingerprint`, `_last_ip`, `_failed_login_count`, `_account_flags`, `_internal_segment_id`)
2. Replace NULL `loyalty_tier` with `"none"` (unclassified users)
3. Normalize emails (lowercase + strip whitespace)
4. Load into `silver.dim_users`

Answer:
"""
# Step 1
df = _drop_internal_columns(df)

# Step 2
if 'loyalty_tier' in df.columns:
    df['loyalty_tier'] = df['loyalty_tier'].fillna('none')

# Step 3
if 'email' in df.columns:
    df['email'] = df['email'].str.lower().str.strip()

# Step 4
_load_to_silver(df, "dim_users")

return df
"""

### 1.4 Implement `transform_orders()`

1. Remove `_*` columns (6 columns — `_stripe_charge_id`, `_paypal_txn_id`, `_internal_channel`, `_fraud_score`, `_fulfillment_warehouse`, `_ab_test_variant`)
2. Validate statuses (allowed: `delivered`, `shipped`, `processing`, `returned`, `cancelled`, `chargeback`)
3. Convert `order_date` to proper datetime
4. Replace NULL `coupon_code` with `""` (empty string)
5. Load into `silver.fct_orders`

Answer:
"""
# Step 1
df = _drop_internal_columns(df)

# Step 2
valid_statuses = ['delivered', 'shipped', 'processing', 'returned', 'cancelled', 'chargeback']
if 'status' in df.columns:
    df = df[df['status'].isin(valid_statuses)]

# Step 3
if 'order_date' in df.columns:
    df['order_date'] = pd.to_datetime(df['order_date'])

# Step 4
if 'coupon_code' in df.columns:
    df['coupon_code'] = df['coupon_code'].fillna('')

# Step 5:
_load_to_silver(df, "fct_orders")
"""

### 1.5 Implement `transform_order_line_items()`

1. Remove `_*` columns (3 columns — `_warehouse_id`, `_internal_batch_code`, `_pick_slot`)
2. Validate `quantity > 0` (drop invalid rows)
3. Check `line_total_usd ≈ unit_price_usd × quantity` (log discrepancies)
4. Load into `silver.fct_order_lines`

Answer:
"""
# Step 1
df = _drop_internal_columns(df)

# Step 2
if 'quantity' in df.columns:
    df = df[df['quantity'] > 0]

# Step 3
if 'line_total_usd' in df.columns and 'unit_price_usd' in df.columns and 'quantity' in df.columns:
  expected_total = df['unit_price_usd'] * df['quantity']
  difference = abs(df['line_total_usd'] - expected_total)
  bad_rows = difference > 0.01
  if bad_rows.sum() > 0:
      print(f"      Removed {bad_rows.sum()} rows with incorrect line totals")
  df = df[~bad_rows]

# Step 4
_load_to_silver(df, "fct_order_lines")

return df
"""

### 1.6 Implement `transform_all()`

Call each of the 4 transform functions and store their results in the `results` dictionary. The keys should match the Silver table names (`dim_products`, `dim_users`, `fct_orders`, `fct_order_lines`).

Answer:
"""
results = {}
results["dim_products"] = transform_products()
results["dim_users"] = transform_users()
results["fct_orders"] = transform_orders()
results["fct_order_lines"] = transform_order_line_items()
"""

### 1.7 Verify



```bash
python pipeline.py --step transform
```

Expected output:
```
============================================================
  🥈 TRANSFORM → Silver (silver_group0)
============================================================

  📦 Transform: products → dim_products
    🧹 X internal columns removed: [...]
    ✅ silver_group0.dim_products — ... rows loaded
  👤 Transform: users → dim_users
    🧹 8 internal columns removed: [...]
    ✅ silver_group0.dim_users — ... rows loaded
  🛍️ Transform: orders → fct_orders
    🧹 X internal columns removed: [...]
    ✅ silver_group0.fct_orders — ... rows loaded
  📋 Transform: order_line_items → fct_order_lines
    🧹 X internal columns removed: [...]
    ✅ silver_group0.fct_order_lines — ... rows loaded

  ✅ Transformation complete — 4 tables in silver_group0
```
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
####################################################################################################################
##########################################################
**SQL Validation** — verify that Silver has fewer columns than Bronze:

```sql
-- Bronze products: ~21 columns
SELECT COUNT(*) FROM information_schema.columns
WHERE table_schema = 'bronze_group0' AND table_name = 'products';

-- Silver dim_products: fewer columns (no _* prefix)
SELECT COUNT(*) FROM information_schema.columns
WHERE table_schema = 'silver_group0' AND table_name = 'dim_products';
```

> ✅ **Checkpoint**: Silver tables must have fewer columns than Bronze. The `_*` columns are gone.

---

## Step 2 — Gold Layer: Analytics Aggregations (30 min)

📁 **File:** `src/gold.py`

### Principle

The Gold layer contains **business-ready** tables: aggregated, joined, and optimized for dashboards. This is where we finally answer the e-commerce team's questions.

Two approaches are possible for each Gold table:
- **Option A — SQL (recommended)**: Write a SQL query with JOINs and GROUP BY, execute it with `pd.read_sql()`, then save the result
- **Option B — Pandas**: Read Silver tables into DataFrames and use `.merge()` / `.groupby()` / `.agg()`

### 2.1 Implement `create_daily_revenue()`

> 📊 *The marketing team asks: "How much revenue per day?"*

Write a SQL query that:
- Joins `fct_orders` with `fct_order_lines` (on `order_id`)
- Excludes cancelled and chargeback orders
- Groups by `DATE(order_date)`
- Computes: `total_orders` (COUNT DISTINCT), `total_revenue` (SUM), `avg_order_value` (AVG), `total_items` (SUM of quantity)
- Orders by date

Then use `pd.read_sql()` to execute it and `_create_gold_table()` to save it.

> 💡 Use `ROUND(CAST(... AS numeric), 2)` for clean decimal output and `COALESCE(..., 0)` for NULL handling.

answer:
"""
query = f"""
        SELECT
            DATE(o.order_date) AS order_date,
            COUNT(DISTINCT o.order_id) AS total_orders,
            SUM(o.total_usd) AS total_revenue,
            AVG(o.total_usd) AS avg_order_value,
            SUM(ol.quantity) AS total_items
        FROM {SILVER_SCHEMA}.fct_orders o
        LEFT JOIN {SILVER_SCHEMA}.fct_order_lines ol ON o.order_id = ol.order_id
        WHERE o.status NOT IN ('cancelled', 'chargeback')
        GROUP BY DATE(o.order_date)
        ORDER BY order_date
    """

    df = pd.read_sql(query, get_engine())
    _create_gold_table(df, "daily_revenue")
"""

### 2.2 Implement `create_product_performance()`

> 🏆 *The product team asks: "Which products sell the most?"*

Join `fct_order_lines` ↔ `dim_products` ↔ `fct_orders`, grouped by product.

Expected columns: `product_id`, `product_name`, `brand`, `category`, `total_quantity_sold`, `total_revenue`, `num_orders`, `avg_unit_price`.

**Hints:**
- Use `INNER JOIN` to link line items with products and orders
- Filter out cancelled/chargeback orders
- Group by `product_id, product_name, brand, category`
- Order by `total_revenue DESC`

answer: 
"""
query = f"""
    SELECT
        ol.product_id,
        ol.product_name,
        p.brand,
        p.category,
        SUM(ol.quantity) AS total_quantity_sold,
        SUM(ol.line_total_usd) AS total_revenue,
        COUNT(DISTINCT ol.order_id) AS num_orders,
        AVG(ol.unit_price_usd) AS avg_unit_price
    FROM {SILVER_SCHEMA}.fct_order_lines ol
    JOIN {SILVER_SCHEMA}.dim_products p
        ON ol.product_id = p.product_id
    GROUP BY
        ol.product_id,
        ol.product_name,
        p.brand,
        p.category
    """
"""

### 2.3 Implement `create_customer_ltv()`

> 💰 *The sales team asks: "Who are our best customers?"*

Join `fct_orders` ↔ `dim_users`, grouped by customer.

Expected columns: `user_id`, `email`, `first_name`, `last_name`, `loyalty_tier`, `total_orders`, `total_spent`, `avg_order_value`, `first_order_date`, `last_order_date`, `days_as_customer`.

**Hints:**
- Join with `dim_users` for customer info
- `first_order_date = MIN(order_date)`, `last_order_date = MAX(order_date)`
- `days_as_customer = EXTRACT(DAY FROM MAX - MIN)`
- Order by `total_spent DESC`

answer:
""""
query = f"""
        SELECT
            o.user_id,
            u.email,
            u.first_name,
            u.last_name,
            u.loyalty_tier,
            COUNT(o.order_id) AS total_orders,
            SUM(o.total_usd) AS total_spent,
            AVG(o.total_usd) AS avg_order_value,
            MIN(o.order_date) AS first_order_date,
            MAX(o.order_date) AS last_order_date,
            EXTRACT(DAY FROM MAX(o.order_date) - MIN(o.order_date)) AS days_as_customer
        FROM {SILVER_SCHEMA}.fct_orders o
        JOIN {SILVER_SCHEMA}.dim_users u
            ON o.user_id = u.user_id
        GROUP BY
            o.user_id,
            u.email,
            u.first_name,
            u.last_name,
            u.loyalty_tier
    """
"""

### 2.4 Implement `create_gold_layer()`

Call the 3 Gold creation functions.
create_daily_revenue()
create_product_performance()
create_customer_ltv()

### 2.5 Verify

```bash
python pipeline.py --step gold
```


**SQL Validation** — check the Gold tables:

```sql
-- Daily revenue
SELECT * FROM gold_group0.daily_revenue ORDER BY order_date LIMIT 5;

-- Top 5 products by revenue
SELECT product_name, brand, total_revenue
FROM gold_group0.product_performance
ORDER BY total_revenue DESC
LIMIT 5;

-- Top 5 customers by spending
SELECT first_name, last_name, loyalty_tier, total_spent, total_orders
FROM gold_group0.customer_ltv
ORDER BY total_spent DESC
LIMIT 5;
```

> ✅ **Checkpoint**: The Gold tables contain aggregated, meaningful business data.

---

## Step 3 — Run the Full Pipeline 🚀

Now run the complete pipeline end-to-end:

```bash
python pipeline.py
```

Or step by step:
```bash
python pipeline.py --step extract
python pipeline.py --step transform
python pipeline.py --step gold
```

validation, also output for the command:
"""
============================================================
  🏪 KICKZ EMPIRE — ELT Pipeline
============================================================

============================================================
  🥉 EXTRACT → Bronze (bronze_group1)
============================================================

products: 228 rows, 21 columns
users: 5000 rows, 28 columns
orders: 17072 rows, 31 columns
order_line_items: 30884 rows, 16 columns
reviews: 2930 rows, 20 columns
clickstream: 544041 rows, 27 columns

  ✅ Extraction complete — 6 tables loaded into bronze_group1

============================================================
  🥈 TRANSFORM → Silver (silver_group1)
============================================================

  📦 Transform: products → dim_products
      Dropped 4 internal columns
    ✅ silver_group1.dim_products — 228 rows loaded
  👤 Transform: users → dim_users
      Dropped 8 internal columns
    ✅ silver_group1.dim_users — 5000 rows loaded
  🛍️ Transform: orders → fct_orders
      Dropped 6 internal columns
    ✅ silver_group1.fct_orders — 17072 rows loaded
  📋 Transform: order_line_items → fct_order_lines
      Dropped 3 internal columns
    ✅ silver_group1.fct_order_lines — 30884 rows loaded

  ✅ Transformation complete — 4 tables in silver_group1

============================================================
  🥇 GOLD Layer (gold_group1)
============================================================

  📊 Gold: daily_revenue
    ✅ gold_group1.daily_revenue — 30 rows
  🏆 Gold: product_performance
    ✅ gold_group1.product_performance — 228 rows
  💰 Gold: customer_ltv
    ✅ gold_group1.customer_ltv — 4832 rows

  ✅ Transformation complete — 4 tables in silver_group1

============================================================
  🥇 GOLD Layer (gold_group1)
============================================================

  📊 Gold: daily_revenue
    ✅ gold_group1.daily_revenue — 30 rows
  🏆 Gold: product_performance
    ✅ gold_group1.product_performance — 228 rows
  💰 Gold: customer_ltv
    ✅ gold_group1.customer_ltv — 4832 rows

  ✅ Gold layer created in gold_group1

============================================================
  ✅ Pipeline completed in 317.5s
============================================================

"""

##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
####################################################################################################################
##########################################################
**Final validation:**

```sql
-- Number of tables per schema
SELECT schemaname, COUNT(*) AS nb_tables
FROM pg_tables
WHERE schemaname IN ('bronze_group0', 'silver_group0', 'gold_group0')
GROUP BY schemaname
ORDER BY schemaname;
```

Expected:
| Schema | Tables |
|--------|--------|
| bronze_group0 | 6 |
| silver_group0 | 4 |
| gold_group0 | 3 |

---

## 🎁 Bonus (if you finish early)

1. **Transform reviews**: Create `silver.dim_reviews` from `bronze.reviews` — remove `_moderation_score`, `_sentiment_raw`, `_toxicity_score`, `_language_detected`, `_review_source`, validate ratings (1–5).
2. **Transform clickstream**: Create `silver.fct_clickstream` from `bronze.clickstream` — remove `_ga_client_id`, `_gtm_container_id`, `_dom_*`, `_ttfb_ms`, `_connection_type`, `_js_heap_size_mb`, `_consent_string`, filter out bots (`is_bot = True`).
3. **Add payments**: Integrate `payment_transactions.csv` into the pipeline (Bronze → Silver → Gold). Create a `gold.payment_summary` table.
4. **UPSERT / idempotency**: Modify `_load_to_bronze()` and `_load_to_silver()` to use SQL MERGE/UPSERT instead of `replace`.
5. **Data quality checks**: Add validation assertions (e.g. "Gold daily_revenue total must equal Silver fct_orders total minus cancellations").
6. **Pandas vs SQL benchmark**: Implement one Gold table using both SQL and Pandas approaches. Compare the code complexity and execution time.

---

## 🔜 Next: Homework & TP3

### Homework (before next session)

If you haven't finished TP2 in class, complete it at home and push to GitHub.

**Additionally:**
- Write **unit tests** using `pytest` for your transform functions (see the test skeleton in `tests/`)
- Add **structured logging** (JSON format) to replace `print()` statements
- Review a classmate's code on GitHub (peer review)

### TP3 — Tests, Logging & Quality

In the next TP, we will:
- Write comprehensive pytest tests (unit + integration)
- Add structured JSON logging and error handling
- Explore code quality tools (linting, type checking)

---

## 📚 Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [pandas.DataFrame.to_sql()](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html)
- [pandas.read_sql()](https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html)
- [Medallion Architecture (Bronze/Silver/Gold)](https://www.databricks.com/glossary/medallion-architecture)
- [Dimensional Modeling (dim_ / fct_)](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
