# Database Design Decisions: Phase 6
## AI Shopping Assistant Backend

This document details the database normalization theory (1NF, 2NF, 3NF) applied to our Phase 6 schema, along with technical decisions and trade-offs.

---

## 1. Normalization Compliance

Database normalization organizes fields and tables to minimize redundancy and prevent dependency anomalies. Our Phase 6 schema adheres strictly to Third Normal Form (3NF).

### 1.1 First Normal Form (1NF)
* **Rule**: Columns must contain atomic values (no repeating groups, CSV lists, or arrays), and each record must have a unique identifier.
* **Compliance**:
  - We use UUID primary keys for all tables.
  - Image lists are extracted from the `products` table and placed into `product_images`. Instead of a comma-separated string or array of URLs, each image is stored as an atomic row.
  - While we use `JSONB` for `Product.attributes` and `SearchHistory.filters`, this does not violate 1NF because the attributes are unstructured/semi-structured properties that do not participate in relational joins. They are stored as atomic JSON fields, queryable natively by PostgreSQL.

### 1.2 Second Normal Form (2NF)
* **Rule**: Must satisfy 1NF, and all non-key columns must be fully functionally dependent on the entire primary key (no partial dependencies on a composite key).
* **Compliance**:
  - Since all tables use a single-column surrogate primary key (`id` UUID), there are no composite primary keys. 
  - All non-key fields (e.g. `title` on `products`, `email` on `users`) depend entirely on the single `id` column.

### 1.3 Third Normal Form (3NF)
* **Rule**: Must satisfy 2NF, and all non-key columns must have no transitive dependencies on the primary key (columns must depend only on the primary key, not on other non-key columns).
* **Compliance**:
  - **Retailer Offers**: Instead of storing merchant names or merchant logos inside the `product_prices` table (which would create a transitive dependency `product_price_id -> merchant_name -> merchant_logo`), we extract them into a separate `merchants` table. `product_prices` stores only a `merchant_id` foreign key.
  - **Category Hierarchy**: Instead of duplicating parent category descriptions inside the child category node, the `parent_id` foreign key references another row in `categories`, resolving the transitive dependency.

---

## 2. Key Design Decisions

### 2.1 UUID vs Integer IDs
* **Decision**: Native 16-byte UUID primary keys.
* **Alternative Considered**: Auto-incrementing integers or bigint IDs.
* **Why Alternative Rejected**: Auto-incrementing integers expose account details or catalog size via simple URL incrementation (e.g., guessing user IDs like `/users/1`, `/users/2`). They also complicate database sharding or offline data insertion because two nodes might generate the same ID. UUIDs can be safely generated on client-side or worker instances, guaranteeing global uniqueness.

### 2.2 Product Prices vs Price History
* **Decision**: Split into `product_prices` (active listing) and `price_history` (time-series audit log).
* **Alternative Considered**: A single `price_history` table where the latest row represents the current active price.
* **Why Alternative Rejected**: Fetching a product's current active price is a highly frequent operation. If we stored it in the history table, we would have to query the max date across millions of history rows. By keeping the current active deal in `product_prices`, fetching current prices is O(1) relative to history size.

### 2.3 VARCHAR(N) vs TEXT
* **Decision**: Explicit limits on indexes (`VARCHAR(100)` or `VARCHAR(255)`) and `TEXT` for free-form descriptions.
* **Alternative Considered**: Unlimited `TEXT` for all string columns.
* **Why Alternative Rejected**: Although PostgreSQL treats `VARCHAR` without limits identically to `TEXT` under the hood, setting explicit limits on key fields provides database-level payload validation. Furthermore, indexing extremely long text fields using B-Trees can bloat the index size and reduce cache efficiency.
