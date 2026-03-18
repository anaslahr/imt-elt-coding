# TP1 — Foundations: Setup & Bronze Layer

## 📖 Business Context

**KICKZ EMPIRE** is a fast-growing e-commerce platform specializing in **sneakers and streetwear** (Nike, Adidas, Jordan, New Balance, Puma…). The store sells sneakers, hoodies, t-shirts, joggers, and accessories to thousands of customers worldwide.

### The problem

The e-commerce team has been collecting data for weeks — orders, product catalogs, user registrations, customer reviews, clickstream events — but it all sits as **raw files in an S3 data lake** in multiple formats (CSV, JSONL, Parquet). No one can easily query it, and the following questions remain unanswered:

> 📊 **Marketing team**: *"How much revenue are we generating day by day? Which products are trending?"*
>
> 🛒 **Sales team**: *"Who are our top customers? What's the average order value?"*
>
> 📈 **Product team**: *"Which brands and categories perform best? What's our conversion rate?"*
>
> 🔒 **Compliance**: *"Are we properly handling PII? Can we audit every data transformation?"*

### The solution: an ELT pipeline

To answer these business questions, you will build an **ELT pipeline** following the **Medallion Architecture** (Bronze → Silver → Gold):

```
S3 (CSV / JSONL / Parquet)  ──→  🥉 Bronze (raw)  ──→  🥈 Silver (clean)  ──→  🥇 Gold (analytics)
```

| Layer | Purpose | Example |
|-------|---------|---------|
| **🥉 Bronze** | Raw data copied **as-is** from S3 into PostgreSQL. No transformation. | `bronze.products`, `bronze.orders` |
| **🥈 Silver** | Cleaned & conformed data. PII removed, types fixed, validated. | `silver.dim_products`, `silver.fct_orders` |
| **🥇 Gold** | Business-ready aggregations for dashboards and reports. | `gold.daily_revenue`, `gold.customer_ltv` |

### In this TP

We focus on the **foundation**: setting up the infrastructure and implementing the **Bronze layer**. By the end of this TP, you will have **6 raw tables** loaded into PostgreSQL from **3 different file formats**, ready to be cleaned in the next TP.

> 📚 For a detailed description of all 12 datasets available in the data lake, see [DATA_PRESENTATION.md](../DATA_PRESENTATION.md).

---

## 🎯 Objective

1. Set up your development environment (Python, `.env`, database connection)
2. Understand the source data (S3 data lake with mixed formats: CSV, JSONL, Parquet)
3. Implement the **Bronze extraction**: read files from S3 (3 formats) and load them as-is into PostgreSQL

**Files you will work on:**
- `src/database.py` — Database connection manager
- `src/extract.py` — Bronze extraction (S3 → PostgreSQL)

---

## 📋 Prerequisites

- Python 3.10+
- Access to the PostgreSQL database (AWS RDS) — credentials in `student_credentials.csv`
- AWS credentials (access key + secret key) to read from the S3 data lake — provided by the instructor

---

## Step 0 — Environment Setup (15 min)

### 0.1 Clone the repo and install dependencies

```bash
git clone <repo-url>
cd imt-elt-coding

python -m venv venv
source venv/bin/activate   # macOS/Linux
# .\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 0.2 Configure the `.env`

```bash
cp .env.example .env
```

Edit `.env` with your credentials (provided by the instructor):

```env
# PostgreSQL (AWS RDS)
RDS_HOST=your-instance.eu-west-3.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=kickz_empire
RDS_USER=your_first_last        # e.g. alice_martin
RDS_PASSWORD=your_password      # from student_credentials.csv

# Schemas (replace 0 with your group number)
BRONZE_SCHEMA=bronze_group0
SILVER_SCHEMA=silver_group0
GOLD_SCHEMA=gold_group0

# AWS S3 data lake (read-only)
S3_BUCKET_NAME=kickz-empire-data
S3_PREFIX=raw
AWS_REGION=eu-west-3
AWS_ACCESS_KEY_ID=your_access_key     # from student_credentials.csv
AWS_SECRET_ACCESS_KEY=your_secret_key  # from student_credentials.csv
```

### 0.3 Implement the DB connection

📁 **File:** `src/database.py`

Complete the two functions marked `TODO`:

1. **`get_engine()`** — Create a SQLAlchemy engine
   - Build the URL: `postgresql://{user}:{password}@{host}:{port}/{database}`
   - Return `create_engine(url)`

2. **`test_connection()`** — Test the connection
   - Use `get_engine().connect()`
   - Execute `SELECT 1`
   - Return `True` on success, `False` otherwise

### 0.4 Verify

```bash
python -m src.database
```

Expected output:
```
🔌 Testing connection to PostgreSQL (AWS RDS)...
✅ Successfully connected!
   Schemas: bronze_group0, silver_group0, gold_group0
```

> ✅ **Checkpoint**: You must see the success message before continuing.

---

## Step 1 — Discover the Data (20 min)

Before writing any extraction code, take a few minutes to understand what you're working with.

### 1.1 Explore the S3 data lake

The raw data lives in **`s3://kickz-empire-data/raw/`**. For this TP, we focus on **6 datasets** stored in **3 different formats**:

| Format | S3 Key | Description | Approx. Rows |
|--------|--------|-------------|--------------|
| **CSV** | `raw/catalog/products.csv` | Product catalog (sneakers, apparel, accessories) | ~230 |
| **CSV** | `raw/users/users.csv` | Registered users with profiles | ~5,000 |
| **CSV** | `raw/orders/orders.csv` | Orders placed on the store | ~17,000 |
| **CSV** | `raw/order_line_items/order_line_items.csv` | Individual items within each order | ~31,000 |
| **JSONL** | `raw/reviews/reviews.jsonl` | Customer product reviews | ~2,930 |
| **Parquet** | `raw/clickstream/dt=YYYY-MM-DD/*.parquet` | Website clickstream events (partitioned by day) | ~544,000 |

> 💡 **Why different formats?** In real data lakes, upstream systems export data in whatever format is most natural for them. CSV is common for transactional systems, JSONL for event logs and APIs, and Parquet for high-volume analytics data. A data engineer must handle them all!

### 1.2 Profile a CSV file

Open a Python REPL or notebook and explore one of the CSV files:

```python
import boto3, os
from io import StringIO
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client("s3",
    region_name="eu-west-3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# --- CSV: Read products.csv ---
response = s3.get_object(Bucket="kickz-empire-data", Key="raw/catalog/products.csv")
df = pd.read_csv(StringIO(response["Body"].read().decode("utf-8")))

print(df.shape)        # rows × columns
print(df.dtypes)       # column types
print(df.head())       # first rows
print(df.describe())   # statistics
```

### 1.3 Profile a JSONL file

JSONL (JSON Lines) stores **one JSON object per line**. It's a common format for event data and APIs:

```python
from io import StringIO

# --- JSONL: Read reviews.jsonl ---
response = s3.get_object(Bucket="kickz-empire-data", Key="raw/reviews/reviews.jsonl")
jsonl_content = response["Body"].read().decode("utf-8")

# pd.read_json() with lines=True reads one JSON object per line
df_reviews = pd.read_json(StringIO(jsonl_content), lines=True)

print(df_reviews.shape)
print(df_reviews.dtypes)
print(df_reviews.head())
```

### 1.4 Profile a Partitioned Parquet dataset

Parquet is a **columnar** binary format, often used for large datasets. The clickstream data is **partitioned by date** — each day has its own folder:

```
raw/clickstream/
    dt=2026-02-05/part-00001.snappy.parquet
    dt=2026-02-05/part-00002.snappy.parquet
    dt=2026-02-06/part-00001.snappy.parquet
    ...
```

To read one partition:

```python
from io import BytesIO
import pyarrow.parquet as pq

# --- Parquet: Read a single partition file ---
response = s3.get_object(
    Bucket="kickz-empire-data",
    Key="raw/clickstream/dt=2026-02-05/part-00001.snappy.parquet"
)
table = pq.read_table(BytesIO(response["Body"].read()))
df_click = table.to_pandas()

print(df_click.shape)
print(df_click.dtypes)
print(df_click.head())
```

> ⚠️ Don't attempt to read **all** partitions interactively — the full clickstream dataset is ~544k rows. Your extraction code will handle this in Step 2.

### 1.5 Questions to answer (write down your observations)

1. How many columns does `products.csv` have? Which ones start with `_` (internal columns)?

products.csv has 21 columns. These columns are internal : _internal_cost_usd, _supplier_id, _warehouse_location, _internal_cost_code

2. How many columns does `users.csv` have? Can you spot PII (passwords, IPs)?

users.csv has 28 columns.
These columns can be considered as PII : user_id, user_uuid, email, first_name, last_name, phone, gender, date_of_birth, city, address_line_1, address_line_2, postal_code, _ga_client_id, _fbp, _device_fingerprint, _last_ip

3. In `orders.csv`, what are the possible values for `status`?

Here are the possible values for status : 
'delivered', 'shipped', 'returned', 'chargeback', 'cancelled', 'processing'

4. In `order_line_items.csv`, does `line_total_usd ≈ unit_price_usd × quantity`?

Yes, exactly.

5. In `reviews.jsonl`, which columns start with `_`? What do `_moderation_score` and `_sentiment_raw` look like?

In reviews.jsonl, these columns start with _ : _moderation_score, _sentiment_raw, _toxicity_score, _language_detected, _review_source.
The moderation score and sentiment raw fields are floats between 0 and 1, respectively representing a score.

6. In the clickstream Parquet file, what does the `event_type` column contain? What `_`-columns exist?

The event_type column contains a string, which is always the same : 'pageview'.
Here are the _ columns : _ga_client_id, _gtm_container_id, _dom_interactive_ms, _dom_complete_ms, _ttfb_ms
> 💡 This profiling step is what real Data Engineers do before building a pipeline. You need to understand the data **before** transforming it.

---

## Step 2 — Extract: S3 → Bronze (45 min)

📁 **File:** `src/extract.py`

### Principle

The Bronze layer stores data **as-is**, without any transformation. It is a faithful copy of the source. We keep even the "dirty" columns (`_internal_*`), as they will be cleaned in TP2.

The raw data lives in the **S3 data lake** (`s3://kickz-empire-data/raw/`). Your code will use **boto3** to read files in 3 different formats and load them into PostgreSQL.

### 2.1 Implement `_read_csv_from_s3()`

This function takes an S3 key (e.g. `"raw/catalog/products.csv"`) and returns a DataFrame.

**Steps:**
1. Get an S3 client using the helper
2. Download the object with `get_object(Bucket=..., Key=...)`
3. Read and decode the body (it's bytes → decode to UTF-8 string)
4. Pass it to `pd.read_csv()` — but remember, `read_csv()` expects a file-like object, not a plain string. What class from the `io` module can help?

> 💡 You already did this interactively in Step 1.2. Now wrap it in a reusable function.

### 2.2 Implement `_read_jsonl_from_s3()`

Very similar to the CSV reader, but for JSONL format (one JSON object per line).

**Key difference:** Instead of `pd.read_csv()`, use `pd.read_json()` with the `lines=True` parameter.

> 💡 Without `lines=True`, pandas would expect a single JSON array. With `lines=True`, it reads one JSON object per line — which is the JSONL format.

### 2.3 Implement `_read_partitioned_parquet_from_s3()`

This is the most complex reader. Partitioned Parquet data is split across many files in date-based folders. You need to:

1. **List** all objects under the S3 prefix — but S3 returns max 1,000 objects per call. What boto3 feature handles this automatically?
2. **Filter** for files ending with `.parquet` (ignore folder markers)
3. **Download** each file and read it — Parquet is binary, not text. Use `BytesIO` instead of `StringIO`, and `pq.read_table()` instead of `pd.read_csv()`
4. **Concatenate** all partition DataFrames into one

> 💡 **Why a paginator?** With ~60+ Parquet files across 30 days, a single `list_objects_v2` call may not return all of them. The paginator loops through all pages automatically.

### 2.4 Implement `_load_to_bronze()`

This function loads a pandas DataFrame into a PostgreSQL table in the Bronze schema.

**Key method:** `df.to_sql()` — check the [pandas docs](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html) for the parameters you'll need:
- Which parameter sets the table name?
- Which parameter takes the SQLAlchemy engine?
- Which parameter sets the schema?
- Which parameter controls the behavior if the table already exists?
- Don't forget to exclude the pandas index from the SQL table

### 2.5 Implement the 4 CSV `extract_*()` functions

Each function follows the same 3-step pattern:
1. **Read** from S3 using the appropriate reader helper
2. **Log** the shape (rows × columns) with a print statement
3. **Load** into Bronze using `_load_to_bronze()` with the right table name

Start with `extract_products()`, then apply the same pattern to:
- `extract_users()` — S3 key is in the docstring
- `extract_orders()` — S3 key is in the docstring
- `extract_order_line_items()` — S3 key is in the docstring

> 💡 Each function's docstring tells you the exact S3 key and target table name.

### 2.6 Implement `extract_reviews()` (JSONL)

Same 3-step pattern as the CSV extractors, but which reader helper should you use for JSONL?

> 💡 Check the S3 key and table name in the function's docstring.

### 2.7 Implement `extract_clickstream()` (Partitioned Parquet)

Same 3-step pattern, but which reader helper should you use for partitioned Parquet? And note: unlike CSV/JSONL, you pass a **prefix** (folder path), not a single file key.

> ⏱️ **Note**: The clickstream extraction takes longer (~30 seconds) because it downloads ~60 Parquet files and concatenates ~544k rows.

### 2.8 Implement `extract_all()`

Call all 6 extract functions and store each result in the `results` dictionary. Group them by format:
- 4 CSV datasets
- 1 JSONL dataset
- 1 Parquet dataset

### 2.9 Verify

```bash
python pipeline.py --step extract
```

Expected output:
```
============================================================
  🏪 KICKZ EMPIRE — ELT Pipeline
============================================================

============================================================
  🥉 EXTRACT → Bronze (bronze_group0)
============================================================

  📦 Products: 229 rows, 21 columns
    ✅ bronze_group0.products — 229 rows loaded
  👤 Users: 5001 rows, 28 columns
    ✅ bronze_group0.users — 5001 rows loaded
  🛍️ Orders: 17073 rows, 30 columns
    ✅ bronze_group0.orders — 17073 rows loaded
  📋 Line items: 30885 rows, 16 columns
    ✅ bronze_group0.order_line_items — 30885 rows loaded
  ⭐ Reviews: 2930 rows, 20 columns
    ✅ bronze_group0.reviews — 2930 rows loaded
  🖱️ Clickstream: 544041 rows, 28 columns
    ✅ bronze_group0.clickstream — 544041 rows loaded

  ✅ Extraction complete — 6 tables loaded into bronze_group0
```

> ✅ **Checkpoint**: Check in PostgreSQL that the 6 tables exist in your bronze schema.

---

## 📊 Validate Your Bronze Layer

Run these SQL queries in PostgreSQL (via DBeaver, pgAdmin, or `psql`) to validate your work:

```sql
-- How many tables in your bronze schema?
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'bronze_group0'
ORDER BY table_name;

-- Row counts per table
SELECT 'products' AS table_name, COUNT(*) AS rows FROM bronze_group0.products
UNION ALL
SELECT 'users', COUNT(*) FROM bronze_group0.users
UNION ALL
SELECT 'orders', COUNT(*) FROM bronze_group0.orders
UNION ALL
SELECT 'order_line_items', COUNT(*) FROM bronze_group0.order_line_items
UNION ALL
SELECT 'reviews', COUNT(*) FROM bronze_group0.reviews
UNION ALL
SELECT 'clickstream', COUNT(*) FROM bronze_group0.clickstream;

-- Inspect the columns of the products table — notice the _ prefixed columns
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'bronze_group0' AND table_name = 'products'
ORDER BY ordinal_position;

-- Quick peek at order statuses
SELECT status, COUNT(*) AS cnt
FROM bronze_group0.orders
GROUP BY status
ORDER BY cnt DESC;

-- Check reviews — what ratings exist?
SELECT rating, COUNT(*) AS cnt
FROM bronze_group0.reviews
GROUP BY rating
ORDER BY rating;

-- Check clickstream — what event types exist?
SELECT event_type, COUNT(*) AS cnt
FROM bronze_group0.clickstream
GROUP BY event_type
ORDER BY cnt DESC;
```

**Expected results:**
- 6 tables in your bronze schema
- ~229 products, ~5,001 users, ~17,073 orders, ~30,885 line items, ~2,930 reviews, ~544,041 clickstream events
- Products table has ~21 columns (including `_internal_cost_usd`, `_supplier_id`, etc.)
- Order statuses: `delivered`, `shipped`, `processing`, `returned`, `cancelled`, `chargeback`
- Review ratings: 1–5 (integer)
- Clickstream event types: `page_view`, `product_view`, `add_to_cart`, `checkout`, etc.

> ✅ **Final Checkpoint**: If you see 6 populated tables in your bronze schema, you're done with TP1!

---

## 🎁 Bonus (if you finish early)

The data lake contains **6 more datasets** that are not covered in this TP. Try extracting them as extra credit!

| Format | S3 Key | Target Table |
|--------|--------|-------------|
| CSV | `raw/payments/payment_transactions.csv` | `bronze.payments` |
| CSV | `raw/inventory/inventory_movements.csv` | `bronze.inventory` |
| JSONL | `raw/marketing/marketing_events.jsonl` | `bronze.marketing` |
| JSONL | `raw/search_events/search_events.jsonl` | `bronze.search_events` |
| JSONL | `raw/abandoned_carts/abandoned_carts.jsonl` | `bronze.abandoned_carts` |
| Parquet | `raw/interactions/` | `bronze.interactions` |

Other bonus ideas:
1. **Data quality report**: Write a short report (notebook or markdown) listing issues you spotted during profiling (NULL values, suspicious columns, data types to fix…). This will be useful for TP2 (Silver layer).
2. **UPSERT method**: Modify `_load_to_bronze()` to use a MERGE/UPSERT instead of `replace` (idempotent loads).
3. **ER diagram**: Draw the relationships between the 6 Bronze tables (draw.io or Mermaid).

---

## 🔜 Next: TP2 — Silver & Gold Layers

In the next TP, you will:
- **Clean** the Bronze data → Silver (remove `_*` columns, handle PII, validate data)
- **Aggregate** Silver data → Gold (daily revenue, product performance, customer LTV)
- **Answer** the business questions the e-commerce team has been waiting for!

---

## 📚 Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [pandas.DataFrame.to_sql()](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html)
- [pandas.read_json() — JSONL support](https://pandas.pydata.org/docs/reference/api/pandas.read_json.html)
- [boto3 S3 get_object()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object.html)
- [boto3 S3 Paginator (list_objects_v2)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/paginator/ListObjectsV2.html)
- [PyArrow — Reading Parquet files](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.read_table.html)
- [Apache Parquet format](https://parquet.apache.org/documentation/latest/)
- [Medallion Architecture (Bronze/Silver/Gold)](https://www.databricks.com/glossary/medallion-architecture)
