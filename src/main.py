"""Smart Expense Tracker API.

A small REST API for managing personal expenses: add, list, filter by
category, compute totals, and delete. Data is persisted to a local JSON
file (no database required).
"""
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from src.models import Expense, ExpenseCreate, TotalResponse
from src.storage import ExpenseStore

app = FastAPI(
    title="Smart Expense Tracker API",
    description="Manage personal expenses: add, list, filter, total, delete.",
    version="1.0.0",
)

store = ExpenseStore()


@app.get("/", tags=["health"])
def root():
    return {"message": "Smart Expense Tracker API is running. See /docs for the API reference."}


@app.post("/expenses", response_model=Expense, status_code=201, tags=["expenses"])
def add_expense(payload: ExpenseCreate):
    """Add a new expense. The server assigns the id."""
    expense = Expense(id=str(uuid.uuid4()), **payload.model_dump())
    return store.add(expense)


@app.get("/expenses", response_model=list[Expense], tags=["expenses"])
def list_expenses(category: str | None = Query(default=None, description="Filter by category")):
    """View all expenses, optionally filtered by category."""
    return store.list_all(category=category)


@app.get("/expenses/total", response_model=TotalResponse, tags=["expenses"])
def get_totals(category: str | None = Query(default=None, description="Restrict overall_total to one category")):
    """Calculate total expenses overall and broken down by category."""
    overall, by_category = store.totals(category=category)
    return TotalResponse(overall_total=overall, by_category=by_category)


@app.get("/expenses/{expense_id}", response_model=Expense, tags=["expenses"])
def get_expense(expense_id: str):
    expense = store.get(expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail=f"Expense '{expense_id}' not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=200, tags=["expenses"])
def delete_expense(expense_id: str):
    deleted = store.delete(expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Expense '{expense_id}' not found")
    return JSONResponse(content={"message": f"Expense '{expense_id}' deleted"})
