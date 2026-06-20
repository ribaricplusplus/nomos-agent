"""Idempotently seed PostgreSQL with the synthetic cases from data.json."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from fake_system.db import session_scope
from fake_system.models import Case

DATA_FILE = Path(__file__).resolve().parents[2] / "data.json"
SOURCE_FIELDS = (
    "case_title",
    "supplier",
    "grid_operator",
    "malo_id",
    "address",
    "meter_number",
    "registration_date",
    "supply_start",
    "status_text",
    "symptom",
    "goal",
)
BATCH_SIZE = 500


def _parse_date(value: str) -> date | None:
    return datetime.strptime(value, "%d.%m.%Y").date() if value else None


def _load_cases() -> list[dict]:
    with DATA_FILE.open(encoding="utf-8") as source:
        payload = json.load(source)

    return [
        {
            "case_id": item["id"],
            "case_title": item["case_title"],
            "supplier": item["lieferant"],
            "grid_operator": item["vnb_name"],
            "malo_id": item["malo_id"],
            "address": item["lieferstelle"],
            "meter_number": item["zaehlernummer"],
            "registration_date": _parse_date(item["anmeldung_datum"]),
            "supply_start": _parse_date(item["lieferbeginn"]),
            "status_text": item["statustext"],
            "symptom": item["symptom"],
            "goal": item["goal"],
            "case_status": "OPEN",
            "next_action": "",
        }
        for item in payload["cases"]
    ]


def seed() -> int:
    """Synchronize every source case while preserving status and next action."""
    cases = _load_cases()

    with session_scope() as session:
        for start in range(0, len(cases), BATCH_SIZE):
            batch = cases[start : start + BATCH_SIZE]
            statement = insert(Case).values(batch)
            statement = statement.on_conflict_do_update(
                index_elements=[Case.case_id],
                set_={
                    field: getattr(statement.excluded, field) for field in SOURCE_FIELDS
                },
            )
            session.execute(statement)
    return len(cases)


def main() -> None:
    synchronized = seed()
    print(
        f"Synchronized {synchronized} case(s); operational status data was preserved."
    )
