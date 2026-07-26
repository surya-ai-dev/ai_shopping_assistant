# Code Review Checklist & Self-Audit: Phase 6
## AI Shopping Assistant Backend

This document acts as our self-review audit checklist to verify code quality and compliance with SQLAlchemy 2.0.

---

## 1. Code Review Checklist

### 1.1 Model Integrity
* [x] **Primary Keys**: Every database model class declares a primary key column (`id`).
* [x] **Inheritance**: All models subclass `BaseModel` to register on the central metadata collector.
* [x] **Mixins Order**: Mixins are inherited *before* `BaseModel` in the class declaration to ensure Python's Method Resolution Order (MRO) applies properties correctly.
* [x] **Enums**: All enums subclass `StrEnum` and are mapped using `Enum(..., native_enum=False)` to prevent migration alteration bottlenecks in PostgreSQL.
* [x] **Decimals**: All financial columns (`price`, `shipping_cost`, `desired_price`) are mapped using Python's `Decimal` type and database `Numeric(10, 2)` bounds.

### 1.2 Relationship Safety
* [x] **Bidirectional Mapping**: Every relationship defines `back_populates` referencing the correct attribute on the partner model.
* [x] **Lazy Loading**: Relationships do not use `lazy="immediate"` or static joins that could trigger N+1 anomalies. They rely on explicit query-level eager loading (`joinedload` or `selectinload`).
* [x] **Cascade Configuration**: All child-dependent models configure `cascade="all, delete-orphan"` along with `passive_deletes=True`.

### 1.3 Schema Constraints & Indexes
* [x] **Indexes**: All foreign key columns declare `index=True` to speed up join queries.
* [x] **Check Constraints**: Value boundaries (like review rating limits or pricing positivity) are protected by explicit database check constraints.
* [x] **Unique Constraints**: Logical duplicate prevention is handled by unique constraints (e.g. `uq_product_merchant_price`).

---

## 2. Naming Conventions Compliance

We verify that all tables, columns, constraints, and indexes follow a unified, predictable structure:

* **Tables**: Lowercase plural names matching entity groups (e.g., `users`, `products`, `wishlist_items`).
* **Foreign Keys**: `fk_<source_table>_<target_table>` (automatically generated or defined).
* **Unique Constraints**: `uq_<table_name>_<column_names>` (e.g., `uq_wishlist_product_item`).
* **Check Constraints**: `chk_<table_name>_<column_name>_<rule>` (e.g., `chk_price_history_non_negative`).
* **Indexes**: `idx_<table_name>_<column_names>` (e.g., `idx_notifications_user_unread`).
* **GIN Indexes**: `idx_<table_name>_<column_names>_gin` (e.g., `idx_products_attributes_gin`).
