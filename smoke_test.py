from pathlib import Path

from fastapi.testclient import TestClient

from app import DB_FILE, app, init_db


def reset_db() -> None:
    db_path = Path(DB_FILE)
    if db_path.exists():
        db_path.unlink()
    init_db()


def main() -> None:
    reset_db()
    client = TestClient(app)

    # A) Search assignment checks
    all_res = client.get("/search")
    assert all_res.status_code == 200
    assert all_res.json()["count"] >= 10

    partial_res = client.get("/search", params={"q": "wire"})
    assert partial_res.status_code == 200
    assert partial_res.json()["count"] >= 1

    category_price_res = client.get(
        "/search",
        params={"category": "Electronics", "minPrice": 1, "maxPrice": 20},
    )
    assert category_price_res.status_code == 200

    invalid_range_res = client.get("/search", params={"minPrice": 50, "maxPrice": 10})
    assert invalid_range_res.status_code == 400

    # B) Database assignment checks
    s1 = client.post("/supplier", json={"name": "Alpha Metals", "city": "Hyderabad"})
    s2 = client.post("/supplier", json={"name": "Beta Plastics", "city": "Chennai"})
    assert s1.status_code == 200 and s2.status_code == 200
    supplier_1 = s1.json()["id"]
    supplier_2 = s2.json()["id"]

    bad_inventory = client.post(
        "/inventory",
        json={"supplier_id": 9999, "product_name": "Bad Item", "quantity": 10, "price": 5},
    )
    assert bad_inventory.status_code == 400

    i1 = client.post(
        "/inventory",
        json={"supplier_id": supplier_1, "product_name": "Steel Coil", "quantity": 100, "price": 10},
    )
    i2 = client.post(
        "/inventory",
        json={"supplier_id": supplier_2, "product_name": "Plastic Sheet", "quantity": 50, "price": 12},
    )
    assert i1.status_code == 200 and i2.status_code == 200

    all_inventory = client.get("/inventory")
    assert all_inventory.status_code == 200
    assert all_inventory.json()["count"] == 2

    grouped = client.get("/inventory/grouped")
    assert grouped.status_code == 200
    grouped_data = grouped.json()["results"]
    assert len(grouped_data) == 2
    assert grouped_data[0]["total_inventory_value"] >= grouped_data[1]["total_inventory_value"]

    print("All smoke tests passed.")


if __name__ == "__main__":
    main()
