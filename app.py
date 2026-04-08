import json
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "inventory_seed.json"
DB_FILE = BASE_DIR / "inventory.db"

app = FastAPI(title="Zeerostock Inventory API")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity >= 0),
            price REAL NOT NULL CHECK (price > 0),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
        """
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


with open(DATA_FILE, "r", encoding="utf-8") as f:
    SEARCH_ITEMS = json.load(f)


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    city: str = Field(min_length=1)


class InventoryCreate(BaseModel):
    supplier_id: int
    product_name: str = Field(min_length=1)
    quantity: int = Field(ge=0)
    price: float = Field(gt=0)


@app.get("/")
def root() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/search")
def search_inventory(
    q: Optional[str] = Query(default=None, description="Product name partial match"),
    category: Optional[str] = Query(default=None),
    minPrice: Optional[float] = Query(default=None, ge=0),
    maxPrice: Optional[float] = Query(default=None, ge=0),
):
    if minPrice is not None and maxPrice is not None and minPrice > maxPrice:
        raise HTTPException(status_code=400, detail="Invalid price range: minPrice cannot exceed maxPrice.")

    results = SEARCH_ITEMS

    if q is not None and q.strip():
        term = q.strip().lower()
        results = [item for item in results if term in item["product_name"].lower()]

    if category is not None and category.strip():
        cat = category.strip().lower()
        results = [item for item in results if item["category"].lower() == cat]

    if minPrice is not None:
        results = [item for item in results if item["price"] >= minPrice]

    if maxPrice is not None:
        results = [item for item in results if item["price"] <= maxPrice]

    return {"count": len(results), "results": results}


@app.post("/supplier")
def create_supplier(payload: SupplierCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO suppliers (name, city) VALUES (?, ?)",
        (payload.name.strip(), payload.city.strip()),
    )
    conn.commit()
    supplier_id = cursor.lastrowid
    conn.close()
    return {"id": supplier_id, "name": payload.name.strip(), "city": payload.city.strip()}


@app.post("/inventory")
def create_inventory(payload: InventoryCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    supplier = cursor.execute("SELECT id FROM suppliers WHERE id = ?", (payload.supplier_id,)).fetchone()
    if supplier is None:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid supplier_id. Supplier does not exist.")

    cursor.execute(
        "INSERT INTO inventory (supplier_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
        (payload.supplier_id, payload.product_name.strip(), payload.quantity, payload.price),
    )
    conn.commit()
    inventory_id = cursor.lastrowid
    conn.close()
    return {
        "id": inventory_id,
        "supplier_id": payload.supplier_id,
        "product_name": payload.product_name.strip(),
        "quantity": payload.quantity,
        "price": payload.price,
    }


@app.get("/inventory")
def get_inventory():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            i.id,
            i.supplier_id,
            s.name AS supplier_name,
            s.city AS supplier_city,
            i.product_name,
            i.quantity,
            i.price,
            (i.quantity * i.price) AS total_value
        FROM inventory i
        JOIN suppliers s ON s.id = i.supplier_id
        ORDER BY i.id ASC
        """
    ).fetchall()
    conn.close()
    return {"count": len(rows), "results": [dict(r) for r in rows]}


@app.get("/inventory/grouped")
def grouped_inventory_by_supplier():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            s.id AS supplier_id,
            s.name AS supplier_name,
            s.city AS city,
            COUNT(i.id) AS item_count,
            COALESCE(SUM(i.quantity * i.price), 0) AS total_inventory_value
        FROM suppliers s
        LEFT JOIN inventory i ON i.supplier_id = s.id
        GROUP BY s.id, s.name, s.city
        ORDER BY total_inventory_value DESC
        """
    ).fetchall()
    conn.close()
    return {"count": len(rows), "results": [dict(r) for r in rows]}
