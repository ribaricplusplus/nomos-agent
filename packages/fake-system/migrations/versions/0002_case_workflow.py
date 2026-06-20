"""replace the placeholder customer model with the Nomos case workflow

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_customers_email", table_name="customers")
    op.drop_table("customers")

    op.create_table(
        "cases",
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("case_title", sa.String(length=255), nullable=False),
        sa.Column("supplier", sa.String(length=200), nullable=False),
        sa.Column("grid_operator", sa.String(length=200), nullable=False),
        sa.Column("malo_id", sa.String(length=32), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("meter_number", sa.String(length=64), nullable=False),
        sa.Column("registration_date", sa.Date(), nullable=True),
        sa.Column("supply_start", sa.Date(), nullable=True),
        sa.Column("status_text", sa.Text(), nullable=False),
        sa.Column("symptom", sa.Text(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column(
            "case_status", sa.String(length=32), server_default="OPEN", nullable=False
        ),
        sa.Column("next_action", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("case_id"),
    )
    op.create_index("ix_cases_malo_id", "cases", ["malo_id"])
    op.create_index("ix_cases_meter_number", "cases", ["meter_number"])

    op.create_table(
        "call_logs",
        sa.Column("call_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column(
            "call_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(length=100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_call_logs_confidence_range",
        ),
        sa.CheckConstraint(
            "duration_seconds >= 0", name="ck_call_logs_duration_nonnegative"
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("call_id"),
    )
    op.create_index("ix_call_logs_call_datetime", "call_logs", ["call_datetime"])
    op.create_index("ix_call_logs_case_id", "call_logs", ["case_id"])

    op.create_table(
        "audit_logs",
        sa.Column("audit_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("changed_field", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("changed_by", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index("ix_audit_logs_changed_at", "audit_logs", ["changed_at"])
    op.create_index("ix_audit_logs_case_id", "audit_logs", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_case_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_changed_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_call_logs_case_id", table_name="call_logs")
    op.drop_index("ix_call_logs_call_datetime", table_name="call_logs")
    op.drop_table("call_logs")
    op.drop_index("ix_cases_meter_number", table_name="cases")
    op.drop_index("ix_cases_malo_id", table_name="cases")
    op.drop_table("cases")

    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("plan", sa.String(length=32), server_default="free", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customers_email", "customers", ["email"], unique=True)
