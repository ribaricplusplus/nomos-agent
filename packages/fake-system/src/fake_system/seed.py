"""Seed the database with sample customer data (idempotent)."""

from __future__ import annotations

from sqlalchemy import func, select

from fake_system.db import session_scope
from fake_system.models import Customer

SEED_CUSTOMERS = [
    {
        "name": "Ada Lovelace",
        "email": "ada@analytical.io",
        "company": "Analytical Engines",
        "plan": "enterprise",
        "status": "active",
        "notes": "Early adopter. Cares about correctness.",
    },
    {
        "name": "Grace Hopper",
        "email": "grace@cobol.dev",
        "company": "Compiler Co",
        "plan": "pro",
        "status": "active",
        "notes": "Filed several feature requests.",
    },
    {
        "name": "Alan Turing",
        "email": "alan@bombe.uk",
        "company": "Bletchley Ltd",
        "plan": "pro",
        "status": "suspended",
        "notes": "Payment on hold.",
    },
    {
        "name": "Katherine Johnson",
        "email": "katherine@orbit.space",
        "company": "Orbital Mechanics",
        "plan": "free",
        "status": "active",
        "notes": None,
    },
    {
        "name": "Dennis Ritchie",
        "email": "dennis@unix.org",
        "company": "Bell Systems",
        "plan": "enterprise",
        "status": "active",
        "notes": "Requested an on-prem deployment.",
    },
]


def seed() -> int:
    """Insert sample customers if the table is empty. Returns rows inserted."""
    with session_scope() as session:
        existing = session.scalar(select(func.count()).select_from(Customer))
        if existing:
            return 0
        session.add_all(Customer(**data) for data in SEED_CUSTOMERS)
        return len(SEED_CUSTOMERS)


def main() -> None:
    inserted = seed()
    if inserted:
        print(f"Seeded {inserted} customers.")
    else:
        print("Customers already present; skipping seed.")
