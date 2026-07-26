# Scalability & Database Performance Analysis: Phase 6
## AI Shopping Assistant Backend

This document analyzes how our database schema, indexes, and structures behave as the system scales from 10,000 products to 10,000,000 products and users.

---

## 1. Storage & Memory Projections

| Scale (Products) | Users | Expected DB Size | Index Size | Performance Bottlenecks |
| :--- | :--- | :--- | :--- | :--- |
| **10,000** | 1,000 | ~50 MB | ~10 MB | None. Entire database fits in RAM. |
| **100,000** | 10,000 | ~500 MB | ~100 MB | Slow sequential scans if indexes are missed. |
| **1,000,000** | 100,000 | ~6 GB | ~1.5 GB | Memory pressure. Index operations start spilling to disk if cache is too small. |
| **10,000,000**| 1,000,000| ~70 GB | ~18 GB | B-Tree index traversal depth increases. GIN search overhead grows. |

---

## 2. Scalability Parameters & Optimizations

### 2.1 UUID Index Bloat
* **Issue**: Because UUID v4 values are random, inserting rows with UUID primary keys triggers random writes across the B-Tree index page leaves. As the index grows larger than PostgreSQL's memory cache (`shared_buffers`), updates cause intensive disk I/O ("B-Tree leaf fragmentation").
* **Mitigation**:
  1. For the high-write logs (like `PriceHistory` or `SearchHistory`), we can use sequentially ordered UUIDs (like UUIDv7) at the application layer or partition tables.
  2. Ensure PostgreSQL has adequate `shared_buffers` configured (typically 25% of system RAM in production).

### 2.2 JSONB Query Performance
* **Issue**: Scanning JSONB documents using nested queries (e.g. `attributes ->> 'processor'`) requires parsing the JSON payload for every row. At 10M rows, this results in high CPU utilization.
* **Mitigation**:
  1. We implement a GIN index: `Index("idx_products_attributes_gin", "attributes", postgresql_using="gin")`. GIN indexes decompose the JSON document into separate keys and values, allowing fast lookups (O(log N)).
  2. If certain attributes are queried constantly, we can extract them into virtual expression columns or dedicated table columns.

### 2.3 Time-Series Price History Scaling
* **Issue**: With 10M products, each price checked daily generates `10,000,000 * 365 = 3.65 Billion` price history records per year. A single PostgreSQL table will grind to a halt under this volume.
* **Mitigation**:
  1. **Table Partitioning**: Partition the `price_history` table by range based on `recorded_at` (e.g. monthly partitions). This keeps individual B-Tree index sizes small, speeds up deletes of old data (dropping partitions), and speeds up time-range queries.
  2. **Data Rollups**: Create background cron workers to aggregate old price history into weekly averages, pruning individual detailed points older than a year.

### 2.4 Vacuuming & Autovacuum Configuration
* **Issue**: Because we use soft deletes and run frequent price updates, PostgreSQL accumulates dead tuples (old row versions created by MVCC updates). This causes table bloat.
* **Mitigation**:
  1. Tune `autovacuum` parameters in PostgreSQL: decrease `autovacuum_vacuum_scale_factor` to `0.05` and `autovacuum_vacuum_threshold` to `1000` to trigger background cleanup operations more frequently.
