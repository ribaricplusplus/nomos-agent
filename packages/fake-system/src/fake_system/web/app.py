"""FastAPI dashboard: render customers and update them."""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from fake_system import repository
from fake_system.config import get_settings
from fake_system.db import get_db

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Fake System — Customer Dashboard")

PLANS = ["free", "pro", "enterprise"]
STATUSES = ["active", "suspended", "churned"]


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    customers = repository.list_customers(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "customers": customers}
    )


@app.get("/customers/{customer_id}/edit", response_class=HTMLResponse, response_model=None)
def edit_customer(
    customer_id: str, request: Request, db: Session = Depends(get_db)
) -> HTMLResponse | RedirectResponse:
    customer = repository.get_customer(db, customer_id)
    if customer is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "customer": customer, "plans": PLANS, "statuses": STATUSES},
    )


@app.post("/customers/{customer_id}")
def save_customer(
    customer_id: str,
    name: str = Form(...),
    email: str = Form(...),
    company: str = Form(""),
    plan: str = Form("free"),
    status: str = Form("active"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    repository.update_customer(
        db,
        customer_id,
        name=name,
        email=email,
        company=company or None,
        plan=plan,
        status=status,
        notes=notes or None,
    )
    return RedirectResponse("/", status_code=303)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


def serve() -> None:
    """Console-script entrypoint: run the dashboard with uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "fake_system.web.app:app",
        host=settings.web_host,
        port=settings.web_port,
    )
