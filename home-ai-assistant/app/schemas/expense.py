from datetime import date, datetime

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    amount: float
    currency: str = "CNY"
    category: str
    subcategory: str | None = None
    description: str | None = None
    payment_method: str | None = None
    expense_date: date | None = None


class ExpenseUpdate(BaseModel):
    amount: float | None = None
    category: str | None = None
    subcategory: str | None = None
    description: str | None = None
    payment_method: str | None = None
    expense_date: date | None = None


class ExpenseResponse(BaseModel):
    id: int
    amount: float
    currency: str
    category: str
    subcategory: str | None
    description: str | None
    payment_method: str | None
    expense_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
