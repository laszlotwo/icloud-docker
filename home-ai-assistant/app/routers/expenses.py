from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Expense)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if category:
        query = query.filter(Expense.category == category)
    return query.order_by(Expense.expense_date.desc()).limit(limit).all()


@router.post("", response_model=ExpenseResponse)
def create_expense(body: ExpenseCreate, db: Session = Depends(get_db)):
    data = body.model_dump()
    if not data.get("expense_date"):
        data["expense_date"] = date.today()
    expense = Expense(**data)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/summary")
def get_summary(
    period: str = "month",
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    from datetime import timedelta
    today = date.today()
    if period == "today":
        s, e = today, today
    elif period == "week":
        s = today - timedelta(days=today.weekday())
        e = today
    elif period == "month":
        s = today.replace(day=1)
        e = today
    elif period == "year":
        s = today.replace(month=1, day=1)
        e = today
    else:
        s = start_date or today.replace(day=1)
        e = end_date or today

    expenses = db.query(Expense).filter(Expense.expense_date >= s, Expense.expense_date <= e).all()
    total = sum(x.amount for x in expenses)
    by_category: dict[str, float] = {}
    for x in expenses:
        by_category[x.category] = by_category.get(x.category, 0) + x.amount

    return {
        "period": f"{s} 至 {e}",
        "total": round(total, 2),
        "count": len(expenses),
        "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
    }


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="记录不存在")
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, body: ExpenseUpdate, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="记录不存在")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(expense)
    db.commit()
    return {"deleted": True}
