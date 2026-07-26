# Database Schema Specification: Phase 6
## AI Shopping Assistant Backend

This document provides a detailed catalog of the database tables, physical data types, constraints, and default values implemented in Phase 6.

---

## 1. Tables Catalog

| Table Name | Entity Class | Primary Key | Description |
| :--- | :--- | :--- | :--- |
| `users` | `User` | UUID | Stores user credentials, active state, and roles. |
| `merchants` | `Merchant` | UUID | Stores retailers offering products (e.g., Amazon). |
| `categories` | `Category` | UUID | Hierarchical catalog taxonomy tree. |
| `products` | `Product` | UUID | Master product record with specifications. |
| `product_images` | `ProductImage` | UUID | Product-associated image assets and sorting order. |
| `product_prices` | `ProductPrice` | UUID | Retailer active offers, deep links, and prices. |
| `price_history` | `PriceHistory` | UUID | Time-series historical price movements log. |
| `product_reviews` | `ProductReview` | UUID | Customer and external scraped review logs. |
| `wishlists` | `Wishlist` | UUID | User-curated product folder groups. |
| `wishlist_items` | `WishlistItem` | UUID | M:N bridge linking wishlists and products. |
| `search_history` | `SearchHistory` | UUID | Logs user search actions for AI insights. |
| `notifications` | `Notification` | UUID | Sent notifications, unread flags, and types. |

---

## 2. Table Column Specifications

### 2.1 Table: `users`
* **id**: `UUID` (Primary Key, native PostgreSQL UUID, default `gen_random_uuid()`)
* **email**: `VARCHAR(255)` (Unique, Indexed, Non-Nullable)
* **hashed_password**: `VARCHAR(255)` (Nullable, supporting OAuth2 credentials)
* **first_name**: `VARCHAR(100)` (Nullable)
* **last_name**: `VARCHAR(100)` (Nullable)
* **role**: `VARCHAR(50)` (Non-Nullable, validated against `UserRole` enum)
* **is_active**: `BOOLEAN` (Default `True`, Non-Nullable)
* **is_superuser**: `BOOLEAN` (Default `False`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable, timezone-aware)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable, timezone-aware)

### 2.2 Table: `merchants`
* **id**: `UUID` (Primary Key, native UUID)
* **name**: `VARCHAR(100)` (Unique, Indexed, Non-Nullable)
* **domain**: `VARCHAR(255)` (Unique, Indexed, Non-Nullable)
* **status**: `VARCHAR(50)` (Non-Nullable, validated against `MerchantStatus` enum)
* **logo_url**: `TEXT` (Nullable)
* **api_config**: `JSONB` (Default `{}`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.3 Table: `categories`
* **id**: `UUID` (Primary Key, native UUID)
* **name**: `VARCHAR(100)` (Non-Nullable)
* **slug**: `VARCHAR(120)` (Unique, Indexed, Non-Nullable)
* **description**: `TEXT` (Nullable)
* **parent_id**: `UUID` (Nullable, ForeignKey to `categories.id` on delete CASCADE, Indexed)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.4 Table: `products`
* **id**: `UUID` (Primary Key, native UUID)
* **title**: `TEXT` (Non-Nullable, GIN indexed for trigram search)
* **description**: `TEXT` (Nullable)
* **brand**: `VARCHAR(100)` (Indexed, Nullable)
* **model_name**: `VARCHAR(100)` (Indexed, Nullable)
* **sku**: `VARCHAR(128)` (Indexed, Nullable)
* **status**: `VARCHAR(50)` (Non-Nullable, validated against `ProductStatus` enum)
* **category_id**: `UUID` (Nullable, ForeignKey to `categories.id` on delete SET NULL, Indexed)
* **attributes**: `JSONB` (Default `{}`, GIN indexed, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.5 Table: `product_images`
* **id**: `UUID` (Primary Key, native UUID)
* **product_id**: `UUID` (ForeignKey to `products.id` on delete CASCADE, Indexed, Non-Nullable)
* **url**: `TEXT` (Non-Nullable)
* **alt_text**: `VARCHAR(255)` (Nullable)
* **position**: `INTEGER` (Default `0`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.6 Table: `product_prices`
* **id**: `UUID` (Primary Key, native UUID)
* **product_id**: `UUID` (ForeignKey to `products.id` on delete CASCADE, Indexed, Non-Nullable)
* **merchant_id**: `UUID` (ForeignKey to `merchants.id` on delete CASCADE, Indexed, Non-Nullable)
* **price**: `NUMERIC(10, 2)` (Non-Nullable, Check price >= 0)
* **currency**: `VARCHAR(10)` (Non-Nullable, validated against `Currency` enum)
* **url**: `TEXT` (Non-Nullable)
* **is_in_stock**: `BOOLEAN` (Default `True`, Non-Nullable)
* **shipping_cost**: `NUMERIC(10, 2)` (Nullable, Check shipping_cost >= 0)
* **last_updated**: `TIMESTAMPTZ` (Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.7 Table: `price_history`
* **id**: `UUID` (Primary Key, native UUID)
* **product_price_id**: `UUID` (ForeignKey to `product_prices.id` on delete CASCADE, Indexed, Non-Nullable)
* **price**: `NUMERIC(10, 2)` (Non-Nullable, Check price >= 0)
* **currency**: `VARCHAR(10)` (Non-Nullable)
* **is_in_stock**: `BOOLEAN` (Default `True`, Non-Nullable)
* **recorded_at**: `TIMESTAMPTZ` (Default `now()`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.8 Table: `product_reviews`
* **id**: `UUID` (Primary Key, native UUID)
* **product_id**: `UUID` (ForeignKey to `products.id` on delete CASCADE, Indexed, Non-Nullable)
* **user_id**: `UUID` (Nullable, ForeignKey to `users.id` on delete SET NULL, Indexed)
* **rating**: `DOUBLE PRECISION` (Non-Nullable, Check rating >= 0.0 AND rating <= 5.0)
* **title**: `VARCHAR(255)` (Nullable)
* **content**: `TEXT` (Nullable)
* **author_name**: `VARCHAR(100)` (Nullable)
* **source**: `VARCHAR(50)` (Non-Nullable, validated against `ReviewSource` enum)
* **review_date**: `TIMESTAMPTZ` (Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.9 Table: `wishlists`
* **id**: `UUID` (Primary Key, native UUID)
* **user_id**: `UUID` (ForeignKey to `users.id` on delete CASCADE, Indexed, Non-Nullable)
* **name**: `VARCHAR(100)` (Non-Nullable)
* **description**: `TEXT` (Nullable)
* **visibility**: `VARCHAR(50)` (Non-Nullable, validated against `WishlistVisibility` enum)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.10 Table: `wishlist_items`
* **id**: `UUID` (Primary Key, native UUID)
* **wishlist_id**: `UUID` (ForeignKey to `wishlists.id` on delete CASCADE, Indexed, Non-Nullable)
* **product_id**: `UUID` (ForeignKey to `products.id` on delete CASCADE, Indexed, Non-Nullable)
* **desired_price**: `NUMERIC(10, 2)` (Nullable, Check desired_price >= 0)
* **added_at**: `TIMESTAMPTZ` (Default `now()`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.11 Table: `search_history`
* **id**: `UUID` (Primary Key, native UUID)
* **user_id**: `UUID` (ForeignKey to `users.id` on delete CASCADE, Indexed, Non-Nullable)
* **query**: `TEXT` (Non-Nullable)
* **filters**: `JSONB` (Default `{}`, Non-Nullable)
* **results_count**: `INTEGER` (Default `0`, Non-Nullable, Check results_count >= 0)
* **searched_at**: `TIMESTAMPTZ` (Default `now()`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)

### 2.12 Table: `notifications`
* **id**: `UUID` (Primary Key, native UUID)
* **user_id**: `UUID` (ForeignKey to `users.id` on delete CASCADE, Indexed, Non-Nullable)
* **title**: `VARCHAR(255)` (Non-Nullable)
* **message**: `TEXT` (Non-Nullable)
* **type**: `VARCHAR(50)` (Non-Nullable, validated against `NotificationType` enum)
* **is_read**: `BOOLEAN` (Default `False`, Non-Nullable)
* **link**: `TEXT` (Nullable)
* **sent_at**: `TIMESTAMPTZ` (Default `now()`, Non-Nullable)
* **is_deleted**: `BOOLEAN` (Default `False`, Non-Nullable)
* **created_at**: `TIMESTAMPTZ` (Non-Nullable)
* **updated_at**: `TIMESTAMPTZ` (Non-Nullable)
