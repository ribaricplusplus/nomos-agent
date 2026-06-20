"""Transactional data access shared by the dashboard and MCP server."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from fake_system.models import AuditLog, CallLog, Case


def list_cases(session: Session) -> Sequence[Case]:
    return session.scalars(select(Case).order_by(Case.case_id)).all()


def get_case(session: Session, case_id: str) -> Case | None:
    return session.get(Case, case_id)


def save_call_result(
    session: Session,
    *,
    case_id: str,
    duration_seconds: int,
    outcome: str,
    summary: str,
    confidence: float,
) -> CallLog | None:
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not outcome.strip():
        raise ValueError("outcome must not be empty")
    if not summary.strip():
        raise ValueError("summary must not be empty")
    if get_case(session, case_id) is None:
        return None

    call_log = CallLog(
        case_id=case_id,
        duration_seconds=duration_seconds,
        outcome=outcome.strip(),
        summary=summary.strip(),
        confidence=confidence,
    )
    session.add(call_log)
    session.flush()
    return call_log


def update_case_status(
    session: Session,
    *,
    case_id: str,
    new_status: str,
    next_action: str,
    changed_by: str = "AI_AGENT",
) -> Case | None:
    normalized_status = new_status.strip().upper()
    if not normalized_status:
        raise ValueError("new_status must not be empty")
    if len(normalized_status) > 32:
        raise ValueError("new_status must be at most 32 characters")

    case = get_case(session, case_id)
    if case is None:
        return None

    old_status = case.case_status
    case.case_status = normalized_status
    case.next_action = next_action.strip()
    session.add(
        AuditLog(
            case_id=case_id,
            changed_field="case_status",
            old_value=old_status,
            new_value=normalized_status,
            changed_by=changed_by,
        )
    )
    session.flush()
    return case


def get_latest_call(session: Session, case_id: str) -> CallLog | None:
    statement = (
        select(CallLog)
        .where(CallLog.case_id == case_id)
        .order_by(CallLog.call_datetime.desc(), CallLog.call_id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def list_call_logs(session: Session, case_id: str | None = None) -> Sequence[CallLog]:
    statement = select(CallLog)
    if case_id is not None:
        statement = statement.where(CallLog.case_id == case_id)
    return session.scalars(
        statement.order_by(CallLog.call_datetime.desc(), CallLog.call_id.desc())
    ).all()


def list_audit_logs(session: Session, case_id: str | None = None) -> Sequence[AuditLog]:
    statement = select(AuditLog)
    if case_id is not None:
        statement = statement.where(AuditLog.case_id == case_id)
    return session.scalars(
        statement.order_by(AuditLog.changed_at.desc(), AuditLog.audit_id.desc())
    ).all()
