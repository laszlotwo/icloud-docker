import json
from datetime import date, datetime, timedelta

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.location import ItemLocation
from app.models.manual import DeviceManual
from app.models.reminder import Reminder
from app.models.vault import VaultEntry
from app.services.scheduler import remove_reminder_job, schedule_reminder


def handle_get_current_time(_input: dict, _db: Session, _vault_key: bytes | None) -> dict:
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y年%m月%d日"),
        "time": now.strftime("%H:%M"),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
    }


def handle_search_device_manuals(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    query = input_["query"]
    category = input_.get("category")
    limit = input_.get("limit", 3)

    try:
        sql = text("""
            SELECT dm.id, dm.name, dm.brand, dm.category,
                   snippet(device_manuals_fts, 1, '[', ']', '...', 20) as snippet
            FROM device_manuals_fts
            JOIN device_manuals dm ON dm.id = device_manuals_fts.rowid
            WHERE device_manuals_fts MATCH :query
            LIMIT :limit
        """)
        rows = db.execute(sql, {"query": query, "limit": limit}).fetchall()
        results = [
            {"id": r.id, "name": r.name, "brand": r.brand, "category": r.category, "snippet": r.snippet}
            for r in rows
            if not category or r.category == category
        ]
    except Exception:
        # Fallback to LIKE search if FTS fails
        q = f"%{query}%"
        manuals = db.query(DeviceManual).filter(
            (DeviceManual.name.like(q)) | (DeviceManual.content.like(q))
        ).limit(limit).all()
        results = [
            {"id": m.id, "name": m.name, "brand": m.brand, "category": m.category,
             "snippet": m.content[:200]}
            for m in manuals
            if not category or m.category == category
        ]

    return {"results": results, "count": len(results)}


def handle_get_manual_content(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    manual = db.get(DeviceManual, input_["manual_id"])
    if not manual:
        return {"error": "说明书不存在"}
    return {
        "id": manual.id,
        "name": manual.name,
        "brand": manual.brand,
        "category": manual.category,
        "content": manual.content,
    }


def handle_find_item_location(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    item_name = input_["item_name"]
    room = input_.get("room")
    q = f"%{item_name}%"
    query = db.query(ItemLocation).filter(ItemLocation.item_name.like(q))
    if room:
        query = query.filter(ItemLocation.room == room)
    items = query.all()
    if not items:
        return {"found": False, "message": f"未找到\"{item_name}\"的存放记录"}
    return {
        "found": True,
        "items": [
            {
                "id": i.id,
                "item_name": i.item_name,
                "location": i.location,
                "room": i.room,
                "container": i.container,
                "description": i.description,
                "last_confirmed": i.last_confirmed_at.isoformat() if i.last_confirmed_at else None,
            }
            for i in items
        ],
    }


def handle_add_item_location(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    existing = db.query(ItemLocation).filter(
        ItemLocation.item_name == input_["item_name"]
    ).first()
    if existing:
        existing.location = input_["location"]
        existing.room = input_.get("room", existing.room)
        existing.container = input_.get("container", existing.container)
        existing.description = input_.get("description", existing.description)
        existing.updated_at = datetime.now()
        db.commit()
        return {"action": "updated", "id": existing.id, "item_name": existing.item_name}
    item = ItemLocation(
        item_name=input_["item_name"],
        location=input_["location"],
        room=input_.get("room"),
        container=input_.get("container"),
        description=input_.get("description"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"action": "created", "id": item.id, "item_name": item.item_name}


def handle_add_expense(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    expense_date_str = input_.get("expense_date")
    expense_date = date.fromisoformat(expense_date_str) if expense_date_str else date.today()
    expense = Expense(
        amount=input_["amount"],
        category=input_["category"],
        description=input_.get("description"),
        payment_method=input_.get("payment_method"),
        expense_date=expense_date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return {
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "description": expense.description,
        "expense_date": expense.expense_date.isoformat(),
    }


def handle_query_expenses(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    query = db.query(Expense)
    if input_.get("start_date"):
        query = query.filter(Expense.expense_date >= date.fromisoformat(input_["start_date"]))
    if input_.get("end_date"):
        query = query.filter(Expense.expense_date <= date.fromisoformat(input_["end_date"]))
    if input_.get("category"):
        query = query.filter(Expense.category == input_["category"])
    limit = input_.get("limit", 20)
    expenses = query.order_by(Expense.expense_date.desc()).limit(limit).all()
    return {
        "expenses": [
            {
                "id": e.id,
                "amount": e.amount,
                "category": e.category,
                "description": e.description,
                "expense_date": e.expense_date.isoformat(),
                "payment_method": e.payment_method,
            }
            for e in expenses
        ],
        "count": len(expenses),
    }


def handle_get_expense_summary(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    period = input_["period"]
    today = date.today()

    if period == "today":
        start, end = today, today
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        end = today
    elif period == "month":
        start = today.replace(day=1)
        end = today
    elif period == "year":
        start = today.replace(month=1, day=1)
        end = today
    else:
        start = date.fromisoformat(input_.get("start_date", str(today)))
        end = date.fromisoformat(input_.get("end_date", str(today)))

    expenses = db.query(Expense).filter(
        Expense.expense_date >= start,
        Expense.expense_date <= end,
    ).all()

    total = sum(e.amount for e in expenses)
    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    return {
        "period": f"{start} 至 {end}",
        "total": round(total, 2),
        "count": len(expenses),
        "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
    }


def handle_add_reminder(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    reminder = Reminder(
        title=input_["title"],
        description=input_.get("description"),
        reminder_type=input_["reminder_type"],
        trigger_spec=input_["trigger_spec"],
        is_active=True,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    try:
        schedule_reminder(reminder.id, reminder.title, reminder.reminder_type, reminder.trigger_spec)
    except Exception as e:
        return {"error": f"提醒已保存但调度失败: {e}", "id": reminder.id}
    return {"id": reminder.id, "title": reminder.title, "trigger_spec": reminder.trigger_spec}


def handle_list_reminders(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    days_ahead = input_.get("days_ahead", 7)
    include_inactive = input_.get("include_inactive", False)
    query = db.query(Reminder)
    if not include_inactive:
        query = query.filter(Reminder.is_active == True)  # noqa: E712
    reminders = query.order_by(Reminder.next_trigger_at).all()
    return {
        "reminders": [
            {
                "id": r.id,
                "title": r.title,
                "reminder_type": r.reminder_type,
                "trigger_spec": r.trigger_spec,
                "is_active": r.is_active,
                "next_trigger": r.next_trigger_at.isoformat() if r.next_trigger_at else None,
            }
            for r in reminders
        ],
        "count": len(reminders),
    }


def handle_delete_reminder(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    reminder = db.get(Reminder, input_["reminder_id"])
    if not reminder:
        return {"error": "提醒不存在"}
    remove_reminder_job(reminder.id)
    db.delete(reminder)
    db.commit()
    return {"deleted": True, "id": input_["reminder_id"]}


def handle_list_vault_titles(input_: dict, db: Session, _vault_key: bytes | None) -> dict:
    query = db.query(VaultEntry.id, VaultEntry.title, VaultEntry.category, VaultEntry.url)
    if input_.get("category"):
        query = query.filter(VaultEntry.category == input_["category"])
    entries = query.all()
    return {
        "entries": [
            {"id": e.id, "title": e.title, "category": e.category, "url": e.url}
            for e in entries
        ],
        "note": "密码内容不会显示，请在密码库页面查看",
    }


HANDLER_MAP = {
    "get_current_time": handle_get_current_time,
    "search_device_manuals": handle_search_device_manuals,
    "get_manual_content": handle_get_manual_content,
    "find_item_location": handle_find_item_location,
    "add_item_location": handle_add_item_location,
    "add_expense": handle_add_expense,
    "query_expenses": handle_query_expenses,
    "get_expense_summary": handle_get_expense_summary,
    "add_reminder": handle_add_reminder,
    "list_reminders": handle_list_reminders,
    "delete_reminder": handle_delete_reminder,
    "list_vault_titles": handle_list_vault_titles,
}


def dispatch_tool(name: str, tool_input: dict, db: Session, vault_key: bytes | None) -> dict:
    handler = HANDLER_MAP.get(name)
    if not handler:
        return {"error": f"未知工具: {name}"}
    return handler(tool_input, db, vault_key)
