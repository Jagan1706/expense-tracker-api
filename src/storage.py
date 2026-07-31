"""Simple persistence layer for expenses.

Expenses are kept in memory for fast access, and mirrored to a local JSON
file so data survives a server restart. No database is required per the
assignment spec.
"""
import json
import os
from typing import Optional

from src.models import Expense

DATA_FILE = os.environ.get("EXPENSES_DATA_FILE", "expenses.json")


class ExpenseStore:
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self._expenses: dict[str, Expense] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                raw = json.load(f)
            self._expenses = {item["id"]: Expense(**item) for item in raw}
        else:
            self._expenses = {}

    def _persist(self) -> None:
        with open(self.data_file, "w") as f:
            json.dump(
                [json.loads(e.model_dump_json()) for e in self._expenses.values()],
                f,
                indent=2,
                default=str,
            )

    def add(self, expense: Expense) -> Expense:
        self._expenses[expense.id] = expense
        self._persist()
        return expense

    def list_all(self, category: Optional[str] = None) -> list[Expense]:
        values = list(self._expenses.values())
        if category:
            values = [e for e in values if e.category.lower() == category.lower()]
        return sorted(values, key=lambda e: e.date)

    def get(self, expense_id: str) -> Optional[Expense]:
        return self._expenses.get(expense_id)

    def delete(self, expense_id: str) -> bool:
        if expense_id in self._expenses:
            del self._expenses[expense_id]
            self._persist()
            return True
        return False

    def totals(self, category: Optional[str] = None) -> tuple[float, dict[str, float]]:
        by_category: dict[str, float] = {}
        for e in self._expenses.values():
            by_category[e.category] = by_category.get(e.category, 0.0) + e.amount
        overall = sum(by_category.values())
        if category:
            overall = by_category.get(category, 0.0)
        return round(overall, 2), {k: round(v, 2) for k, v in by_category.items()}

    def clear(self) -> None:
        """Used by tests to reset state between runs."""
        self._expenses = {}
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
