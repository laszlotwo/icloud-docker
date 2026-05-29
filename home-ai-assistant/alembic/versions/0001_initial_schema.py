"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "device_manuals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("brand", sa.String(100)),
        sa.Column("model_number", sa.String(100)),
        sa.Column("category", sa.String(50)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("file_path", sa.String(500)),
        sa.Column("tags", sa.String(500)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "vault_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column("url", sa.String(500)),
        sa.Column("salt", sa.LargeBinary(16), nullable=False),
        sa.Column("username_encrypted", sa.LargeBinary),
        sa.Column("password_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("notes_encrypted", sa.LargeBinary),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "item_locations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_name", sa.String(200), nullable=False, index=True),
        sa.Column("description", sa.Text),
        sa.Column("location", sa.String(500), nullable=False),
        sa.Column("room", sa.String(50)),
        sa.Column("container", sa.String(200)),
        sa.Column("tags", sa.String(500)),
        sa.Column("last_confirmed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(10), server_default="CNY"),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("description", sa.String(500)),
        sa.Column("payment_method", sa.String(50)),
        sa.Column("expense_date", sa.Date, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("reminder_type", sa.String(20), nullable=False),
        sa.Column("trigger_spec", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="1"),
        sa.Column("last_triggered_at", sa.DateTime),
        sa.Column("next_trigger_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "conversation_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tool_calls_json", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("conversation_history")
    op.drop_table("reminders")
    op.drop_table("expenses")
    op.drop_table("item_locations")
    op.drop_table("vault_entries")
    op.drop_table("device_manuals")
