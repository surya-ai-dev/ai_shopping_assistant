# Execution Data Flow: Phase 6
## AI Shopping Assistant Backend

This document details the step-by-step database flow of operations representing a standard user shopping session.

---

## 1. Step-by-Step Data Flow Diagram

```
[User Action: Login/Auth]
         │
         ▼
    [users Table] (Fetch user session, check roles)
         │
         ▼
[User Action: Type Query "gaming laptop"]
         │
         ▼
 [search_history Table] (Insert search terms, log filters, save result counts)
         │
         ▼
   [products Table] (Fuzzy match title/specs, return paginated results)
         │
         ▼
[product_prices Table] (LEFT JOIN active offers from BestBuy, Amazon, etc.)
         │
         ▼
[price_history Table] (Generate time-series price line chart from history points)
         │
         ▼
[User Action: Click "Save to Wishlist"]
         │
         ▼
  [wishlists Table] (Verify wishlist exists or create new)
         │
         ▼
[wishlist_items Table] (Insert join record linking wishlist and product, set target price)
         │
         ▼
[Cron Job: Scraper detects BestBuy price drops below target price]
         │
         ▼
[notifications Table] (Insert unread notification row for the user)
```

---

## 2. Technical Operations Breakdown

### Step 1: User Authentication
* **Database Action**: SELECT
* **Query**: `SELECT * FROM users WHERE email = :email AND is_deleted = FALSE`
* **Performance**: Index Scan on `idx_users_email` (O(1)).

### Step 2: Logging Search Actions (AI Personalization Input)
* **Database Action**: INSERT
* **Query**: `INSERT INTO search_history (id, user_id, query, filters, results_count, searched_at) VALUES (...)`
* **Performance**: Writes search terms and JSONB filter criteria to support downstream recommendation models.

### Step 3: Product Search & Specification Filtering
* **Database Action**: SELECT (JOIN Category)
* **Query**: `SELECT * FROM products WHERE category_id = :id AND attributes ->> 'ram_gb' = '16'`
* **Performance**: Uses GIN indexes on `attributes` and category foreign keys to return products in O(log N).

### Step 4: Loading Detail Page (Deals & History)
* **Database Action**: SELECT (Eager load prices and history)
* **Query**:
  - `SELECT * FROM product_prices WHERE product_id = :id` (Current active deals)
  - `SELECT * FROM price_history WHERE product_price_id IN (:price_ids) ORDER BY recorded_at ASC` (Historical chart data)
* **Performance**: Optimized using `selectinload` to retrieve price history without N+1 query loops.

### Step 5: Wishlist Save & Target Pricing
* **Database Action**: INSERT
* **Query**: `INSERT INTO wishlist_items (id, wishlist_id, product_id, desired_price) VALUES (...)`
* **Performance**: Insertion validated by the unique constraint `uq_wishlist_product_item` to prevent duplicate saves.

### Step 6: Price Alert Delivery
* **Database Action**: INSERT
* **Query**: `INSERT INTO notifications (id, user_id, title, message, type, is_read, sent_at) VALUES (...)`
* **Performance**: Delivers a price drop notification. The user's dashboard counts unread messages using `idx_notifications_user_unread`.
