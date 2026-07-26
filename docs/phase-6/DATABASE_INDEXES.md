# Database Indexes Specification: Phase 6
## AI Shopping Assistant Backend

This document details the index strategies, index types, and database optimization considerations for Phase 6.

---

## 1. Index Types & Rationale

We implement four kinds of indexes in PostgreSQL:

### 1.1 Primary Index (B-Tree)
* **What**: Automatically created on columns marked as primary key.
* **Mechanism**: PostgreSQL builds a B-Tree index on the `id` columns.
* **Complexity**: O(log N) lookup time for single-record fetches.

### 1.2 Secondary Index (B-Tree)
* **What**: Indexes created on search filtering fields (e.g. `brand`, `sku`).
* **Why**: Prevents PostgreSQL from performing a sequential scan on queries like `SELECT * FROM products WHERE brand = 'Sony'`.

### 1.3 Composite Index (Multi-column B-Tree)
* **What**: An index covering multiple columns in a specific order.
* **Why**: Optimizes queries filtering or sorting by multiple fields simultaneously, e.g. `idx_notifications_user_unread` on `(user_id, is_read)` to count unread notifications.
* **Important**: Query filters must match the index prefix (left-to-right order) to utilize it.

### 1.4 Unique Index
* **What**: Enforces uniqueness while providing index lookup speed.
* **Why**: Created automatically on `UNIQUE` columns (e.g., `email`, `slug`).

### 1.5 GIN Index (Generalized Inverted Index)
* **What**: A specialized index for complex data types (JSONB) or text pattern matching.
* **Why**: Used for `idx_products_attributes_gin` to search inside product specification JSON maps, and `idx_products_title_trgm` to search titles using partial matches.

---

## 2. Table Index Definitions

| Table | Index Name | Columns | Index Type | Business Query Optimized |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `idx_users_email` | `email` | B-Tree (Unique) | User login authentication. |
| `merchants` | `idx_merchants_name` | `name` | B-Tree (Unique) | Merchant retrieval by name. |
| `merchants` | `idx_merchants_domain` | `domain` | B-Tree (Unique) | Mapping crawled product URLs to merchants. |
| `categories` | `idx_categories_slug` | `slug` | B-Tree (Unique) | Category navigation path pages. |
| `categories` | `idx_categories_parent` | `parent_id` | B-Tree | Constructing nested category trees. |
| `products` | `idx_products_brand` | `brand` | B-Tree | Brand filtering page navigation. |
| `products` | `idx_products_model` | `model_name` | B-Tree | Exact model lookups. |
| `products` | `idx_products_sku` | `sku` | B-Tree | Barcode searches or crawler sync. |
| `products` | `idx_products_title_trgm` | `title` | GIN (Trigram) | Fuzzy keyword catalog searches. |
| `products` | `idx_products_attributes_gin`| `attributes` | GIN | AI filters matching spec keys. |
| `product_images`| `idx_product_images_prod` | `product_id` | B-Tree | Fetching product detail images. |
| `product_prices`| `idx_product_prices_prod` | `product_id` | B-Tree | Fetching active merchant offers. |
| `product_prices`| `idx_product_prices_merch`| `merchant_id` | B-Tree | Listing products sold by a merchant. |
| `price_history` | `idx_price_history_prod_pr`| `product_price_id`| B-Tree | Fetching logs for price charts. |
| `price_history` | `idx_price_history_price_rec`| `product_price_id`, `recorded_at` | Composite B-Tree | Charting price ranges over time. |
| `product_reviews`| `idx_product_reviews_prod` | `product_id` | B-Tree | Product review listing pages. |
| `product_reviews`| `idx_product_reviews_user` | `user_id` | B-Tree | User-written review lists. |
| `product_reviews`| `idx_product_reviews_rating`| `product_id`, `rating` | Composite B-Tree | Filtering reviews by rating score. |
| `wishlists` | `idx_wishlists_user` | `user_id` | B-Tree | Dashboard wishlist retrieval. |
| `wishlist_items`| `idx_wishlist_items_wish` | `wishlist_id` | B-Tree | Loading wishlist product details. |
| `search_history`| `idx_search_history_user_date`| `user_id`, `searched_at` | Composite B-Tree | Loading user's recent search suggestions. |
| `notifications` | `idx_notifications_unread` | `user_id`, `is_read` | Composite B-Tree | Counting unread notifications. |
