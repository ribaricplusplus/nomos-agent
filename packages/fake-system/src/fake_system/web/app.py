"""FastAPI dashboard for PostgreSQL-backed cases, calls, and audit events."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from fake_system import repository
from fake_system.config import get_settings
from fake_system.db import get_db

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Fake Nomos Case Dashboard")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    cases = repository.list_cases(db)
    call_logs = repository.list_call_logs(db)
    audit_logs = repository.list_audit_logs(db)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "cases": cases,
            "call_logs": call_logs,
            "audit_logs": audit_logs,
            "open_cases": sum(case.case_status == "OPEN" for case in cases),
        },
    )


@app.get("/cases/{case_id}", response_class=HTMLResponse, response_model=None)
def case_detail(
    case_id: str, request: Request, db: Session = Depends(get_db)
) -> HTMLResponse | RedirectResponse:
    case = repository.get_case(db, case_id)
    if case is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request,
        "edit.html",
        {
            "case": case,
            "call_logs": repository.list_call_logs(db, case_id),
            "audit_logs": repository.list_audit_logs(db, case_id),
        },
    )


@app.post("/cases/{case_id}/status")
def save_case_status(
    case_id: str,
    case_status: str = Form(..., min_length=1, max_length=32),
    next_action: str = Form("", max_length=10_000),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    repository.update_case_status(
        db,
        case_id=case_id,
        new_status=case_status,
        next_action=next_action,
        changed_by="DASHBOARD",
    )
    return RedirectResponse(f"/cases/{case_id}", status_code=303)


@app.post("/cases/{case_id}/calls")
def save_case_call(
    case_id: str,
    duration_seconds: int = Form(..., ge=0),
    outcome: str = Form(..., min_length=1, max_length=100),
    summary: str = Form(..., min_length=1, max_length=10_000),
    confidence: float = Form(..., ge=0, le=1),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    repository.save_call_result(
        db,
        case_id=case_id,
        duration_seconds=duration_seconds,
        outcome=outcome,
        summary=summary,
        confidence=confidence,
    )
    return RedirectResponse(f"/cases/{case_id}", status_code=303)


@app.get("/healthz")
def healthz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}


def serve() -> None:
    """Run the dashboard with uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "fake_system.web.app:app",
        host=settings.web_host,
        port=settings.web_port,
    )
