"""use alphanumeric case ids and cascade id updates

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ID_MAP = {
    "CASE-A": "NM26-A001",
    "CASE-B": "NM26-B002",
    "CASE-C": "NM26-C003",
}
cases = sa.table("cases", sa.column("case_id", sa.String()))


def upgrade() -> None:
    op.drop_constraint("call_logs_case_id_fkey", "call_logs", type_="foreignkey")
    op.drop_constraint("audit_logs_case_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "call_logs_case_id_fkey",
        "call_logs",
        "cases",
        ["case_id"],
        ["case_id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.create_foreign_key(
        "audit_logs_case_id_fkey",
        "audit_logs",
        "cases",
        ["case_id"],
        ["case_id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )

    for old_id, new_id in ID_MAP.items():
        op.execute(cases.update().where(cases.c.case_id == old_id).values(case_id=new_id))


def downgrade() -> None:
    for old_id, new_id in ID_MAP.items():
        op.execute(cases.update().where(cases.c.case_id == new_id).values(case_id=old_id))

    op.drop_constraint("call_logs_case_id_fkey", "call_logs", type_="foreignkey")
    op.drop_constraint("audit_logs_case_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "call_logs_case_id_fkey",
        "call_logs",
        "cases",
        ["case_id"],
        ["case_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "audit_logs_case_id_fkey",
        "audit_logs",
        "cases",
        ["case_id"],
        ["case_id"],
        ondelete="CASCADE",
    )
