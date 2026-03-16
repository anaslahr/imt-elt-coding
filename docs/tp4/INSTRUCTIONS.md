# TP4 — CI/CD, Monitoring & Evaluation

## 📖 Context

Your pipeline is tested, logged, and production-ready code-wise. The final step is **industrialization**: making sure it runs automatically, is monitored, and can be deployed reliably.

This is the evaluation TP — your deliverables at the end of this session will be graded.

---

## 🎯 Objective

1. Set up **GitHub Actions** CI/CD pipeline (lint → test → report)
2. Add a **monitoring dashboard** (pipeline execution metrics)
3. Package the project for **production deployment**
4. Prepare your **presentation deliverables**

---

## 📋 Prerequisites

- TP1, TP2, TP3 completed (pipeline working, tested, logged)
- GitHub repository with all code pushed

---

## Step 1 — GitHub Actions CI/CD (30 min)

### Principle

Every `git push` should automatically:
1. **Lint** the code (formatting, style)
2. **Run tests** (unit + coverage)
3. **Generate a report** (coverage badge, test results)

### 1.1 Create the workflow file

📁 **File:** `.github/workflows/ci.yml`

```yaml
name: ELT Pipeline CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8

      - name: Lint with flake8
        run: |
          # Stop on syntax errors or undefined names
          flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
          # Warnings (non-blocking)
          flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics

      - name: Run tests with coverage
        env:
          # Use mock/test values — CI doesn't connect to real DB
          RDS_HOST: localhost
          RDS_PORT: "5432"
          RDS_DATABASE: test_db
          RDS_USER: test_user
          RDS_PASSWORD: test_pass
          BRONZE_SCHEMA: bronze_test
          SILVER_SCHEMA: silver_test
          GOLD_SCHEMA: gold_test
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
```

### 1.2 Push and verify

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI pipeline"
git push
```

Go to your GitHub repository → **Actions** tab → verify the workflow runs successfully.

> ✅ **Checkpoint**: Green CI badge on your repository.

---

## Step 2 — Pipeline Monitoring (30 min)

### Principle

In production, you need to know:
- ✅ Did the pipeline run successfully?
- ⏱ How long did each step take?
- 📊 How many rows were processed?
- ❌ What failed and why?

### 2.1 Add execution metrics

📁 **File:** `src/monitoring.py`

Create a module with two dataclasses to track pipeline execution:

**`StepMetrics`** — tracks a single pipeline step:
- `step_name` (str): e.g. "extract", "transform", "gold"
- `status` (str): "pending" → "running" → "success" / "failed"
- `start_time`, `end_time` (str): ISO format timestamps
- `duration_seconds` (float): how long the step took
- `rows_processed` (int): total rows handled
- `tables_created` (list): names of tables created
- `errors` (list): any error messages

**`PipelineReport`** — aggregates all steps:
- `pipeline_name` (str): "KICKZ EMPIRE ELT"
- `run_id` (str): timestamp of the run
- `steps` (list): list of `StepMetrics`
- `add_step()`: add a step to the report
- `to_json()`: serialize to JSON string
- `save(filepath)`: write JSON to file

> 💡 Use `@dataclass` with `field(default_factory=list)` for mutable default values. Use `dataclasses.asdict()` to convert to a dict for JSON serialization.

### 2.2 Integrate metrics into the pipeline

Modify `pipeline.py` to track execution time and row counts for each step.

### 2.3 Generate a report after each run

After running `python pipeline.py`, a `pipeline_report.json` file should be generated with:

```json
{
  "pipeline_name": "KICKZ EMPIRE ELT",
  "run_id": "2026-03-25T10:30:00Z",
  "steps": [
    {
      "step_name": "extract",
      "status": "success",
      "duration_seconds": 12.3,
      "rows_processed": 53188,
      "tables_created": ["products", "users", "orders", "order_line_items"]
    },
    ...
  ]
}
```

> ✅ **Checkpoint**: Pipeline generates a JSON report after each run.

---

## Step 3 — Production Packaging (20 min)

### 3.1 Clean up the repository

Ensure your repo is clean and professional:

- [ ] `.gitignore` is complete (no `.env`, `__pycache__`, `venv/`, `*.pyc`)
- [ ] `requirements.txt` has all dependencies pinned
- [ ] `README.md` has clear setup and run instructions
- [ ] All code follows consistent formatting (run `black src/` if available)
- [ ] No hardcoded credentials anywhere
- [ ] No unused imports or dead code

### 3.2 Write a comprehensive README

Your `README.md` should include:

1. **Project description** (what it does, business context)
2. **Architecture diagram** (Bronze → Silver → Gold)
3. **Setup instructions** (step by step)
4. **How to run** (full pipeline + individual steps)
5. **How to test** (pytest commands)
6. **Team members** (names, roles)

### 3.3 Tag a release

```bash
git tag -a v1.0.0 -m "TP4: Production-ready ELT pipeline"
git push origin v1.0.0
```

---

## 📝 Evaluation Deliverables

### What to submit

| Deliverable | Deadline | Format |
|------------|----------|--------|
| **GitHub Repository** | Wednesday evening | Link to repo (all code pushed) |
| **Pipeline Report** | Wednesday evening | `pipeline_report.json` in repo |
| **Presentation Video** | Thursday noon | Video (5-10 min per team) |

### Grading criteria (/20)

| Criteria | Points | Description |
|----------|--------|-------------|
| **Pipeline functionality** | 5 | Bronze → Silver → Gold works end-to-end |
| **Code quality** | 4 | Clean code, proper structure, error handling, logging |
| **Test coverage** | 3 | ≥80% coverage, meaningful tests, mocks |
| **CI/CD** | 3 | GitHub Actions passing, lint + test |
| **Monitoring & reporting** | 2 | Pipeline report, execution metrics |
| **Presentation** | 3 | Clear explanation of architecture, choices, challenges |

### Presentation content (5-10 min video)

1. **Architecture overview** — Show your pipeline diagram (Bronze → Silver → Gold)
2. **Technical choices** — Why SQLAlchemy? Why this data model? Trade-offs?
3. **Demo** — Run the pipeline and show the results (Gold tables, SQL queries)
4. **Data quality** — What issues did you find? How did you handle them?
5. **Challenge & learnings** — What was the hardest part? What would you improve?

---

## 🎁 Bonus (extra credit)

1. **Scheduled execution**: Use `cron` or a task scheduler to run the pipeline automatically (show the configuration).
2. **Alerting**: Send a Slack/email notification if the pipeline fails (can be a mock/proof of concept).
3. **Dashboard**: Create a simple dashboard (Streamlit, Grafana, or even a Jupyter notebook) that visualizes the Gold tables.
4. **Prefect orchestration**: Wrap the pipeline in Prefect flows/tasks for better observability and retry logic.
5. **Additional datasets**: Integrate more KICKZ EMPIRE datasets (payments, reviews, clickstream) into the full pipeline.

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [flake8](https://flake8.pycqa.org/)
- [black (formatter)](https://black.readthedocs.io/)
- [Prefect Documentation](https://docs.prefect.io/)
- [Streamlit](https://streamlit.io/)
