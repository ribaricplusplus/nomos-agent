"""MCP server exposing the PostgreSQL-backed Nomos case workflow."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from fake_system import repository
from fake_system.config import get_settings
from fake_system.db import session_scope

settings = get_settings()

mcp = FastMCP(
    "fake-nomos-mcp",
    instructions=(
        "Read Nomos cases, record calls, and update audited case details or status."
    ),
    host=settings.mcp_host,
    port=settings.mcp_port,
)


@mcp.tool()
def list_cases() -> list[dict]:
    """List every case."""
    with session_scope() as session:
        return [case.as_dict() for case in repository.list_cases(session)]


@mcp.tool()
def get_case(case_id: str) -> dict | None:
    """Get one case by its case ID."""
    with session_scope() as session:
        case = repository.get_case(session, case_id)
        return case.as_dict() if case else None


@mcp.tool()
def save_call_result(
    case_id: str,
    duration_seconds: int,
    outcome: str,
    summary: str,
    confidence: float,
) -> dict:
    """Record the result of an agent call. Confidence must be from 0 to 1."""
    with session_scope() as session:
        call_log = repository.save_call_result(
            session,
            case_id=case_id,
            duration_seconds=duration_seconds,
            outcome=outcome,
            summary=summary,
            confidence=confidence,
        )
        if call_log is None:
            return {"success": False, "error": "Case not found"}
        return {"success": True, "call_log": call_log.as_dict()}


@mcp.tool()
def update_case_status(case_id: str, new_status: str, next_action: str) -> dict:
    """Update a case's status and next action, recording an audit entry."""
    with session_scope() as session:
        case = repository.get_case(session, case_id)
        if case is None:
            return {"success": False, "error": "Case not found"}
        old_status = case.case_status
        updated = repository.update_case_status(
            session,
            case_id=case_id,
            new_status=new_status,
            next_action=next_action,
        )
        return {
            "success": True,
            "case_id": case_id,
            "old_status": old_status,
            "new_status": updated.case_status,
            "next_action": updated.next_action,
        }


@mcp.tool()
def update_case_details(
    case_id: str,
    case_title: str | None = None,
    supplier: str | None = None,
    grid_operator: str | None = None,
    malo_id: str | None = None,
    address: str | None = None,
    meter_number: str | None = None,
    registration_date: str | None = None,
    supply_start: str | None = None,
    status_text: str | None = None,
    symptom: str | None = None,
    goal: str | None = None,
) -> dict:
    """Update supplied case details and audit each changed field.

    Dates must use YYYY-MM-DD. MaLo IDs must contain exactly 11 digits.
    Omit fields that should remain unchanged.
    """
    with session_scope() as session:
        case, changed_fields = repository.update_case_details(
            session,
            case_id=case_id,
            case_title=case_title,
            supplier=supplier,
            grid_operator=grid_operator,
            malo_id=malo_id,
            address=address,
            meter_number=meter_number,
            registration_date=registration_date,
            supply_start=supply_start,
            status_text=status_text,
            symptom=symptom,
            goal=goal,
        )
        if case is None:
            return {"success": False, "error": "Case not found"}
        return {
            "success": True,
            "changed_fields": changed_fields,
            "case": case.as_dict(),
        }


@mcp.tool()
def get_case_summary(case_id: str) -> dict:
    """Get case details together with its latest call log."""
    with session_scope() as session:
        case = repository.get_case(session, case_id)
        latest_call = repository.get_latest_call(session, case_id) if case else None
        return {
            "case": case.as_dict() if case else None,
            "latest_call": latest_call.as_dict() if latest_call else None,
        }


@mcp.resource("cases://all")
def cases_resource() -> str:
    """All cases as a JSON document."""
    with session_scope() as session:
        return json.dumps(
            [case.as_dict() for case in repository.list_cases(session)], indent=2
        )


def main() -> None:
    """Serve MCP over streamable HTTP."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
