"""SQLAlchemy ORM models for the Nomos case workflow."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_title: Mapped[str] = mapped_column(String(255))
    supplier: Mapped[str] = mapped_column(String(200))
    grid_operator: Mapped[str] = mapped_column(String(200))
    malo_id: Mapped[str] = mapped_column(String(32), index=True)
    address: Mapped[str] = mapped_column(Text)
    meter_number: Mapped[str] = mapped_column(String(64), index=True)
    registration_date: Mapped[date | None] = mapped_column(Date)
    supply_start: Mapped[date | None] = mapped_column(Date)
    status_text: Mapped[str] = mapped_column(Text)
    symptom: Mapped[str] = mapped_column(Text)
    goal: Mapped[str] = mapped_column(Text)
    case_status: Mapped[str] = mapped_column(String(32), default="OPEN", server_default="OPEN")
    next_action: Mapped[str] = mapped_column(Text, default="", server_default="")
    call_logs: Mapped[list[CallLog]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "case_title": self.case_title,
            "supplier": self.supplier,
            "grid_operator": self.grid_operator,
            "malo_id": self.malo_id,
            "address": self.address,
            "meter_number": self.meter_number,
            "registration_date": self.registration_date.isoformat()
            if self.registration_date
            else None,
            "supply_start": self.supply_start.isoformat() if self.supply_start else None,
            "status_text": self.status_text,
            "symptom": self.symptom,
            "goal": self.goal,
            "case_status": self.case_status,
            "next_action": self.next_action,
        }


class CallLog(Base):
    __tablename__ = "call_logs"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="ck_call_logs_duration_nonnegative"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_call_logs_confidence_range",
        ),
    )

    call_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.case_id", ondelete="CASCADE", onupdate="CASCADE"), index=True
    )
    call_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)

    case: Mapped[Case] = relationship(back_populates="call_logs")

    def as_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "case_id": self.case_id,
            "call_datetime": self.call_datetime.isoformat() if self.call_datetime else None,
            "duration_seconds": self.duration_seconds,
            "outcome": self.outcome,
            "summary": self.summary,
            "confidence": float(self.confidence),
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.case_id", ondelete="CASCADE", onupdate="CASCADE"), index=True
    )
    changed_field: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    changed_by: Mapped[str] = mapped_column(String(100))

    case: Mapped[Case] = relationship(back_populates="audit_logs")

    def as_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "case_id": self.case_id,
            "changed_field": self.changed_field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "changed_by": self.changed_by,
        }
