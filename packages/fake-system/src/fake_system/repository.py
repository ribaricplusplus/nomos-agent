"""Data-access functions shared by the dashboard and the MCP server."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from fake_system.models import Customer

# Fields a caller is allowed to set/update on a customer.
EDITABLE_FIELDS = ("name", "email", "company", "plan", "status", "notes")


def _as_uuid(customer_id: uuid.UUID | str) -> uuid.UUID:
    return customer_id if isinstance(customer_id, uuid.UUID) else uuid.UUID(str(customer_id))


def list_customers(session: Session) -> Sequence[Customer]:
    return session.scalars(select(Customer).order_by(Customer.created_at)).all()


def get_customer(session: Session, customer_id: uuid.UUID | str) -> Customer | None:
    return session.get(Customer, _as_uuid(customer_id))


def create_customer(session: Session, **fields) -> Customer:
    customer = Customer(**{k: v for k, v in fields.items() if k in EDITABLE_FIELDS})
    session.add(customer)
    session.flush()
    return customer


def update_customer(
    session: Session, customer_id: uuid.UUID | str, **fields
) -> Customer | None:
    """Update the given fields. Only keys in EDITABLE_FIELDS with non-None values apply."""
    customer = get_customer(session, customer_id)
    if customer is None:
        return None
    for key, value in fields.items():
        if key in EDITABLE_FIELDS and value is not None:
            setattr(customer, key, value)
    session.flush()
    return customer
