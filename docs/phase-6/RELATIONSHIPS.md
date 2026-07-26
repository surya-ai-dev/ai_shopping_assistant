# Database Relationships & Cascades: Phase 6
## AI Shopping Assistant Backend

This document details the configuration, parameters, and rationale behind SQLAlchemy relationships, cascades, and loading styles.

---

## 1. Summary of SQLAlchemy Relationships

We implement relationships using SQLAlchemy 2.0 type annotations with `Mapped` and `relationship()`.

| Relationship Name | Model 1 | Model 2 | Cardinality | Configuration details |
| :--- | :--- | :--- | :--- | :--- |
| `Category.children` | `Category` | `Category` | One-to-Many | Self-referential, remote_side="Category.id" |
| `Category.products` | `Category` | `Product` | One-to-Many | `cascade="save-update, merge"` |
| `Product.images` | `Product` | `ProductImage` | One-to-Many | `cascade="all, delete-orphan"`, ordered by `position` |
| `Product.prices` | `Product` | `ProductPrice` | One-to-Many | `cascade="all, delete-orphan"` |
| `Merchant.prices` | `Merchant` | `ProductPrice` | One-to-Many | `cascade="all, delete-orphan"` |
| `ProductPrice.price_histories` | `ProductPrice` | `PriceHistory` | One-to-Many | `cascade="all, delete-orphan"` |
| `Product.reviews` | `Product` | `ProductReview` | One-to-Many | `cascade="all, delete-orphan"` |
| `User.reviews` | `User` | `ProductReview` | One-to-Many | `cascade="save-update, merge"`, keeps reviews on user deletion |
| `User.wishlists` | `User` | `Wishlist` | One-to-Many | `cascade="all, delete-orphan"` |
| `Wishlist.items` | `Wishlist` | `WishlistItem` | One-to-Many | `cascade="all, delete-orphan"` |
| `Product.wishlist_items` | `Product` | `WishlistItem` | One-to-Many | `cascade="all, delete-orphan"` |
| `User.search_histories` | `User` | `SearchHistory` | One-to-Many | `cascade="all, delete-orphan"` |
| `User.notifications` | `User` | `Notification` | One-to-Many | `cascade="all, delete-orphan"` |

---

## 2. Cascade Rationale

### 2.1 `cascade="all, delete-orphan"`
* **Applies to**: `Product.images`, `Product.prices`, `Product.reviews`, `Wishlist.items`, `Product.wishlist_items`, `User.wishlists`, `User.notifications`, `User.search_histories`.
* **Why**: These child models have no independent existence without their parent (e.g. a `WishlistItem` cannot exist without a parent `Wishlist`). If the parent is deleted or the link is removed, PostgreSQL deletes the child row.
* **Passive Deletes**: We configure `passive_deletes=True` on relationships. This tells SQLAlchemy not to load all child objects from the database just to delete them in Python. Instead, it relies on PostgreSQL's native `ON DELETE CASCADE` foreign keys to perform the deletion, which is significantly faster.

### 2.2 `cascade="save-update, merge"` (No Delete Cascade)
* **Applies to**: `Category.products`, `User.reviews`.
* **Why**: If a product category is deleted, we do NOT want to delete all associated products. Instead, the product is kept but is classified as unassigned (category_id becomes `NULL`). If a user deletes their account, their written reviews are kept for catalog integrity but anonymized (user_id becomes `NULL`).

---

## 3. Query Loading Strategies

By default, SQLAlchemy uses **Lazy Loading** (`lazy="select"`), meaning related tables are only queried when they are accessed. In asynchronous contexts, accessing a lazy-loaded relationship outside of the session raises an `sqlalchemy.exc.MissingGreenletContext` error.
To prevent this, we explicitly configure query-level eager loading in the repositories:

### 3.1 `joinedload()` (SQL JOIN)
* **Used for**: Many-to-One relationships, such as loading the `Category` of a `Product` or the `Merchant` of a `ProductPrice`.
* **Why**: Performs a standard SQL `LEFT OUTER JOIN` in the initial query. Since there is only one related parent record, it is efficient and does not suffer from cartesian product duplication.

### 3.2 `selectinload()` (SQL SELECT IN)
* **Used for**: One-to-Many relationships, such as loading a product's list of `ProductPrice` offers or images.
* **Why**: Executes a second SQL query using an `IN` clause (e.g. `SELECT * FROM product_prices WHERE product_id IN (...)`). This prevents SQL join duplicates and is highly optimized.
