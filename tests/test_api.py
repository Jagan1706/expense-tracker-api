"""Test suite for the Smart Expense Tracker API.

Run with: pytest
Each test resets the store's JSON file so tests don't leak state between runs.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use a dedicated test data file so we never touch a real expenses.json
os.environ["EXPENSES_DATA_FILE"] = "test_expenses.json"

from src.main import app, store  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    """Clear the store before every test so each test starts clean."""
    store.clear()
    yield
    store.clear()


def make_expense(**overrides):
    payload = {
        "title": "Coffee",
        "amount": 4.5,
        "category": "Food",
        "date": "2026-07-01",
    }
    payload.update(overrides)
    return payload


def test_root_health_check():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "running" in resp.json()["message"]


def test_add_expense_returns_generated_id():
    resp = client.post("/expenses", json=make_expense())
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data and len(data["id"]) > 0
    assert data["title"] == "Coffee"
    assert data["amount"] == 4.5
    assert data["category"] == "Food"
    assert data["date"] == "2026-07-01"


def test_add_expense_rejects_non_positive_amount():
    resp = client.post("/expenses", json=make_expense(amount=0))
    assert resp.status_code == 422

    resp = client.post("/expenses", json=make_expense(amount=-5))
    assert resp.status_code == 422


def test_add_expense_rejects_blank_title():
    resp = client.post("/expenses", json=make_expense(title="   "))
    assert resp.status_code == 422


def test_list_all_expenses():
    client.post("/expenses", json=make_expense(title="Coffee", category="Food"))
    client.post("/expenses", json=make_expense(title="Bus ticket", category="Travel", amount=2.0))

    resp = client.get("/expenses")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    titles = {e["title"] for e in data}
    assert titles == {"Coffee", "Bus ticket"}


def test_filter_expenses_by_category():
    client.post("/expenses", json=make_expense(title="Coffee", category="Food"))
    client.post("/expenses", json=make_expense(title="Bus ticket", category="Travel", amount=2.0))
    client.post("/expenses", json=make_expense(title="Lunch", category="Food", amount=12.0))

    resp = client.get("/expenses", params={"category": "Food"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(e["category"] == "Food" for e in data)


def test_filter_by_category_is_case_insensitive():
    client.post("/expenses", json=make_expense(title="Coffee", category="Food"))
    resp = client.get("/expenses", params={"category": "food"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_totals_overall_and_by_category():
    client.post("/expenses", json=make_expense(title="Coffee", category="Food", amount=4.5))
    client.post("/expenses", json=make_expense(title="Lunch", category="Food", amount=12.0))
    client.post("/expenses", json=make_expense(title="Bus ticket", category="Travel", amount=2.0))

    resp = client.get("/expenses/total")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_total"] == pytest.approx(18.5)
    assert data["by_category"]["Food"] == pytest.approx(16.5)
    assert data["by_category"]["Travel"] == pytest.approx(2.0)


def test_totals_with_no_expenses_is_zero():
    resp = client.get("/expenses/total")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_total"] == 0
    assert data["by_category"] == {}


def test_get_single_expense_by_id():
    created = client.post("/expenses", json=make_expense()).json()
    resp = client.get(f"/expenses/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_nonexistent_expense_returns_404():
    resp = client.get("/expenses/does-not-exist")
    assert resp.status_code == 404


def test_delete_expense():
    created = client.post("/expenses", json=make_expense()).json()
    expense_id = created["id"]

    resp = client.delete(f"/expenses/{expense_id}")
    assert resp.status_code == 200

    # Confirm it's actually gone
    resp = client.get(f"/expenses/{expense_id}")
    assert resp.status_code == 404


def test_delete_nonexistent_expense_returns_404():
    resp = client.delete("/expenses/does-not-exist")
    assert resp.status_code == 404


def test_data_persists_to_json_file():
    client.post("/expenses", json=make_expense())
    assert os.path.exists(os.environ["EXPENSES_DATA_FILE"])
