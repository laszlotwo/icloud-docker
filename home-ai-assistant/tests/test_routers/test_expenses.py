from datetime import date


def test_create_and_list_expense(client):
    r = client.post("/api/v1/expenses", json={"amount": 25.5, "category": "餐饮", "description": "午餐", "expense_date": str(date.today())})
    assert r.status_code == 200
    data = r.json()
    assert data["amount"] == 25.5
    assert data["category"] == "餐饮"

    r = client.get("/api/v1/expenses")
    assert r.status_code == 200
    assert any(e["description"] == "午餐" for e in r.json())


def test_expense_summary(client):
    client.post("/api/v1/expenses", json={"amount": 100.0, "category": "购物", "expense_date": str(date.today())})
    r = client.get("/api/v1/expenses/summary?period=month")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 100.0
    assert "购物" in data["by_category"]


def test_delete_expense(client):
    r = client.post("/api/v1/expenses", json={"amount": 10.0, "category": "交通", "expense_date": str(date.today())})
    exp_id = r.json()["id"]
    r = client.delete(f"/api/v1/expenses/{exp_id}")
    assert r.status_code == 200
    r = client.get(f"/api/v1/expenses/{exp_id}")
    assert r.status_code == 404
