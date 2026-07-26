# Entity Relationship Diagram: Phase 6
## AI Shopping Assistant Backend

This document contains the Entity Relationship Diagram (ERD) detailing table columns, primary/foreign keys, and cardinalities.

---

## 1. Mermaid ER Diagram

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar first_name
        varchar last_name
        varchar role
        boolean is_active
        boolean is_superuser
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    merchants {
        uuid id PK
        varchar name UK
        varchar domain UK
        varchar status
        text logo_url
        jsonb api_config
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    categories {
        uuid id PK
        varchar name
        varchar slug UK
        text description
        uuid parent_id FK
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    products {
        uuid id PK
        text title
        text description
        varchar brand
        varchar model_name
        varchar sku
        varchar status
        uuid category_id FK
        jsonb attributes
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    product_images {
        uuid id PK
        uuid product_id FK
        text url
        varchar alt_text
        integer position
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    product_prices {
        uuid id PK
        uuid product_id FK
        uuid merchant_id FK
        numeric price
        varchar currency
        text url
        boolean is_in_stock
        numeric shipping_cost
        timestamptz last_updated
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    price_history {
        uuid id PK
        uuid product_price_id FK
        numeric price
        varchar currency
        boolean is_in_stock
        timestamptz recorded_at
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    product_reviews {
        uuid id PK
        uuid product_id FK
        uuid user_id FK
        double_precision rating
        varchar title
        text content
        varchar author_name
        varchar source
        timestamptz review_date
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    wishlists {
        uuid id PK
        uuid user_id FK
        varchar name
        text description
        varchar visibility
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    wishlist_items {
        uuid id PK
        uuid wishlist_id FK
        uuid product_id FK
        numeric desired_price
        timestamptz added_at
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    search_history {
        uuid id PK
        uuid user_id FK
        text query
        jsonb filters
        integer results_count
        timestamptz searched_at
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    notifications {
        uuid id PK
        uuid user_id FK
        varchar title
        text message
        varchar type
        boolean is_read
        text link
        timestamptz sent_at
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    categories ||--o{ categories : "parent of"
    categories ||--o{ products : "classifies"
    products ||--o{ product_images : "has"
    products ||--o{ product_prices : "offered at"
    merchants ||--o{ product_prices : "offers"
    product_prices ||--o{ price_history : "price points"
    products ||--o{ product_reviews : "reviewed in"
    users ||--o{ product_reviews : "writes"
    users ||--o{ wishlists : "owns"
    wishlists ||--o{ wishlist_items : "contains"
    products ||--o{ wishlist_items : "linked in"
    users ||--o{ search_history : "queries"
    users ||--o{ notifications : "receives"
```

---

## 2. Cardinality Summaries

* **Category Tree**: One parent category has Zero-to-Many child categories (1:N, self-referential).
* **Category to Products**: One category classifies Zero-to-Many products (1:N). If deleted, product relationships are nullified.
* **Product to Images**: One product has Zero-to-Many images (1:N, CASCADE delete).
* **Product Price offers**: One product has Zero-to-Many price listings across merchants (1:N).
* **Merchant prices**: One merchant offers Zero-to-Many price listings (1:N).
* **Price listing history**: One price listing has Zero-to-Many historical logs (1:N, CASCADE).
* **Product Reviews**: One product has Zero-to-Many reviews (1:N). One user writes Zero-to-Many reviews (1:N, SET NULL on user deletion).
* **Wishlist Items M:N Link**: 
  - One user has Zero-to-Many wishlists (1:N).
  - One wishlist contains Zero-to-Many wishlist items (1:N, CASCADE).
  - One product links to Zero-to-Many wishlist items (1:N, CASCADE).
* **User Search & Alerts**: One user has Zero-to-Many search logs and receives Zero-to-Many notifications (1:N, CASCADE).
