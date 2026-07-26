# Developer Workflow Guide: Phase 6
## AI Shopping Assistant Backend

This document details the workflow instructions for generating migrations, applying database schemas, and running validation scripts.

---

## 1. Prerequisites

Verify that the local PostgreSQL Docker container is running:
```bash
docker compose ps
```
If not running, launch the infrastructure container:
```bash
docker compose up -d postgres
```

---

## 2. Alembic Migrations Flow

When you add or edit database models inside `src/models/`, execute the following steps:

### Step 2.1: Generate Migration Script
Alembic compares the python models registered in `Base.metadata` against the physical PostgreSQL database state.
Run the autogenerate command:
```bash
uv run alembic revision --autogenerate -m "add_phase_6_models"
```
This generates a new migration file inside `alembic/versions/`.

### Step 2.2: Review the Generated Migration File
Open the new version script inside `alembic/versions/` and verify that:
* All 12 tables (`users`, `merchants`, `categories`, `products`, `product_images`, `product_prices`, `price_history`, `product_reviews`, `wishlists`, `wishlist_items`, `search_history`, `notifications`) are created with correct columns.
* Check constraints, unique indexes, and foreign key connections are mapped.
* Add `op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")` inside the `upgrade()` function *before* the `idx_products_title_trgm` index creation to support trigram matching.

### Step 2.3: Apply Migrations
Apply the migrations to upgrade the physical database:
```bash
uv run alembic upgrade head
```
Verify that the `alembic_version` table is updated with the latest revision ID.

---

## 3. Schema Rollback (If needed)
If you make a mistake and need to roll back the migration, run:
```bash
uv run alembic downgrade -1
```
This executes the `downgrade()` function of the latest migration, removing the tables safely.

---

## 4. Run Integration Verification
To verify relationships, cascades, and constraints under a live transaction context:
```bash
uv run pytest tests/integration/test_phase_6_models.py
```
This validates insertion, querying, cascading, and check constraint validation on PostgreSQL.
