"""Pydantic models used across the Expense Tracker API."""
from datetime import date as date_type
from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    """Payload for creating a new expense. The client does not supply an id;
    the server generates one so uniqueness is guaranteed."""

    title: str = Field(..., min_length=1, description="Short description of the expense")
    amount: float = Field(..., gt=0, description="Amount spent, must be positive")
    category: str = Field(..., min_length=1, description="Category, e.g. 'Food', 'Travel'")
    date: date_type = Field(..., description="Date the expense occurred (YYYY-MM-DD)")

    @field_validator("title", "category")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class Expense(ExpenseCreate):
    """An expense as stored/returned by the API, including its generated id."""

    id: str


class TotalResponse(BaseModel):
    overall_total: float
    by_category: dict[str, float]