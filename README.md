# Zeerostock Assignment Solution

This project implements both requested assignments:

- **A: Search-Focused Assignment** (`GET /search` + UI)
- **B: Database-Focused Assignment** (Supplier + Inventory APIs with required grouped query)

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite
- **Frontend:** Plain HTML + JavaScript

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start server:

```bash
uvicorn app:app --reload
```

3. Open:

- UI: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## A) Inventory Search API + UI

### API

`GET /search`

Supported query params:

- `q` -> product name partial match (case-insensitive)
- `category`
- `minPrice`
- `maxPrice`

Behavior:

- Multiple filters can be combined
- If no filters are provided, all static records are returned
- Empty search query is treated as no text filter
- Invalid price range (`minPrice > maxPrice`) returns 400
- No matches returns empty results (`count: 0`)

### Data Source

Uses static JSON data at `data/inventory_seed.json` (12 records).

### UI Features

- Product search input
- Category dropdown
- Min/Max price inputs
- Results table
- Explicit `No results found` state
- Client-side validation for invalid price range

### Search Logic (Short)

Search starts from the complete static dataset, then applies filters in sequence:

1. Product name partial match (`q`) with lowercase normalization
2. Exact category match after lowercase normalization
3. Price lower bound (`minPrice`)
4. Price upper bound (`maxPrice`)

This ensures deterministic filtering and easy combination of conditions.

### Performance improvement for large datasets

Move data from static JSON into a DB and perform filtering directly in SQL with indexed columns (`product_name`, `category`, `price`) plus pagination to avoid loading all rows at once.

---

## B) Inventory Database + APIs

### Schema

#### `suppliers`

- `id` (PK)
- `name`
- `city`

#### `inventory`

- `id` (PK)
- `supplier_id` (FK -> suppliers.id)
- `product_name`
- `quantity` (`>= 0`)
- `price` (`> 0`)

Relationship: **One supplier -> many inventory items**

### APIs

- `POST /supplier`
  - Body: `{ "name": "...", "city": "..." }`

- `POST /inventory`
  - Body: `{ "supplier_id": 1, "product_name": "...", "quantity": 10, "price": 5.5 }`
  - Validates:
    - supplier exists
    - quantity >= 0
    - price > 0

- `GET /inventory`
  - Returns all inventory with supplier details

- `GET /inventory/grouped` (required query output)
  - Returns inventory grouped by supplier
  - Sorted by total inventory value (`SUM(quantity * price)`) descending

### Why SQL (SQLite)?

This data is relational (suppliers and inventory with foreign keys), needs validation constraints, and requires grouped/aggregate queries. SQL is a strong fit for data integrity and efficient reporting queries.

### Indexing/optimization suggestion

Add indexes on `inventory(supplier_id)` for joins and on `inventory(product_name, price)` for common search/filter operations. For large-scale reads, add pagination and cache common grouped reports.
