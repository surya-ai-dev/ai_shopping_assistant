# Database Constraints: Phase 6
## AI Shopping Assistant Backend

This document catalogs the database integrity constraints implemented in Phase 6.

---

## 1. Constraint Classifications

Constraints enforce business rules directly at the database engine level, preventing data corruption even if there are application-level programming errors. We implement four kinds of constraints:

### 1.1 NOT NULL (Nullability checks)
* **Rationale**: Enforces that fields vital to database logic (like `email` or `price`) must contain a valid value on insert or update transactions.

### 1.2 UNIQUE (Uniqueness checks)
* **Rationale**: Ensures no two rows can share the same identifier (e.g. two users cannot register with the same email).

### 1.3 FOREIGN KEY (Referential Integrity)
* **Rationale**: Guarantees that links between tables (like `product_id` linking to `products.id`) are valid and clean. It controls deletion behavior using cascading rules (`ON DELETE CASCADE` or `ON DELETE SET NULL`).

### 1.4 CHECK (Logical check bounds)
* **Rationale**: Enforces mathematical boundary invariants, such as ensuring that product ratings stay between `0.0` and `5.0`, or that prices cannot be negative.

---

## 2. Constraints Catalog

| Table | Constraint Name | Constraint Type | Target Columns | Logical Rule / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `pk_users` | Primary Key | `id` | Must be a unique UUID. |
| `users` | `uq_users_email` | Unique | `email` | No duplicate user emails. |
| `merchants` | `uq_merchants_name` | Unique | `name` | No duplicate merchant names. |
| `merchants` | `uq_merchants_domain`| Unique | `domain` | No duplicate merchant domains. |
| `categories` | `uq_categories_slug` | Unique | `slug` | No duplicate category slugs. |
| `categories` | `fk_categories_parent`| Foreign Key | `parent_id` | Ref `categories.id` ON DELETE CASCADE. |
| `categories` | `uq_categories_name_parent`| Unique | `name`, `parent_id` | No duplicate subcategory under parent. |
| `products` | `fk_products_category`| Foreign Key | `category_id` | Ref `categories.id` ON DELETE SET NULL. |
| `product_images`| `fk_product_images_product`| Foreign Key | `product_id` | Ref `products.id` ON DELETE CASCADE. |
| `product_prices`| `fk_product_prices_product`| Foreign Key | `product_id` | Ref `products.id` ON DELETE CASCADE. |
| `product_prices`| `fk_product_prices_merchant`| Foreign Key | `merchant_id` | Ref `merchants.id` ON DELETE CASCADE. |
| `product_prices`| `uq_product_merchant_price`| Unique | `product_id`, `merchant_id` | One active price entry per merchant/product. |
| `product_prices`| `chk_product_price_non_negative`| Check | `price` | `price >= 0.0` (Free or paid). |
| `product_prices`| `chk_product_shipping_cost_non_negative`| Check | `shipping_cost`| `shipping_cost >= 0.0`. |
| `price_history` | `fk_price_history_product_price`| Foreign Key | `product_price_id`| Ref `product_prices.id` ON DELETE CASCADE. |
| `price_history` | `chk_price_history_non_negative`| Check | `price` | `price >= 0.0`. |
| `product_reviews`| `fk_product_reviews_product`| Foreign Key | `product_id` | Ref `products.id` ON DELETE CASCADE. |
| `product_reviews`| `fk_product_reviews_user`| Foreign Key | `user_id` | Ref `users.id` ON DELETE SET NULL. |
| `product_reviews`| `chk_product_review_rating_range`| Check | `rating` | `rating >= 0.0 AND rating <= 5.0`. |
| `wishlists` | `fk_wishlists_user` | Foreign Key | `user_id` | Ref `users.id` ON DELETE CASCADE. |
| `wishlist_items`| `fk_wishlist_items_wishlist`| Foreign Key | `wishlist_id`| Ref `wishlists.id` ON DELETE CASCADE. |
| `wishlist_items`| `fk_wishlist_items_product`| Foreign Key | `product_id` | Ref `products.id` ON DELETE CASCADE. |
| `wishlist_items`| `uq_wishlist_product_item`| Unique | `wishlist_id`, `product_id` | Cannot add same product twice to wishlist. |
| `wishlist_items`| `chk_wishlist_item_desired_price_non_negative`| Check | `desired_price`| `desired_price >= 0.0`. |
| `search_history`| `fk_search_history_user`| Foreign Key | `user_id` | Ref `users.id` ON DELETE CASCADE. |
| `search_history`| `chk_search_history_results_count_positive`| Check | `results_count`| `results_count >= 0`. |
| `notifications` | `fk_notifications_user`| Foreign Key | `user_id` | Ref `users.id` ON DELETE CASCADE. |
