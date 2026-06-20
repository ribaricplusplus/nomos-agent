from unittest.mock import Mock

import pytest

from fake_system import repository
from fake_system.models import CallLog, Case
from fake_system.seed import _load_cases


def test_save_call_result_rejects_invalid_duration() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        repository.save_call_result(
            Mock(),
            case_id="CASE-A",
            duration_seconds=-1,
            outcome="failed",
            summary="Invalid test input",
            confidence=0.5,
        )


def test_save_call_result_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        repository.save_call_result(
            Mock(),
            case_id="CASE-A",
            duration_seconds=10,
            outcome="complete",
            summary="Invalid test input",
            confidence=1.1,
        )


def test_save_call_result_creates_log_for_existing_case() -> None:
    session = Mock()
    session.get.return_value = Mock(spec=Case)

    call_log = repository.save_call_result(
        session,
        case_id="CASE-A",
        duration_seconds=90,
        outcome="  reached operator  ",
        summary="  Registration is being processed.  ",
        confidence=0.9,
    )

    assert isinstance(call_log, CallLog)
    assert call_log.case_id == "CASE-A"
    assert call_log.outcome == "reached operator"
    assert call_log.summary == "Registration is being processed."
    session.add.assert_called_once_with(call_log)
    session.flush.assert_called_once()


def test_update_case_status_creates_audit_log() -> None:
    case = Case(
        case_id="CASE-A",
        case_title="Test",
        supplier="Nomos",
        grid_operator="Grid",
        malo_id="123",
        address="Test address",
        meter_number="METER-1",
        status_text="Pending",
        symptom="Test symptom",
        goal="Test goal",
        case_status="OPEN",
        next_action="",
    )
    session = Mock()
    session.get.return_value = case

    updated = repository.update_case_status(
        session,
        case_id="CASE-A",
        new_status="RESOLVED",
        next_action="Close the case",
    )

    assert updated is case
    assert case.case_status == "RESOLVED"
    assert case.next_action == "Close the case"
    audit = session.add.call_args.args[0]
    assert audit.old_value == "OPEN"
    assert audit.new_value == "RESOLVED"


def test_seed_file_maps_every_case_to_legacy_columns() -> None:
    cases = _load_cases()

    assert len(cases) == 10
    assert all(any(character.isalpha() for character in case["case_id"]) for case in cases)
    assert all(any(character.isdigit() for character in case["case_id"]) for case in cases)
    assert set(cases[0]) == {
        "case_id",
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
        "case_status",
        "next_action",
    }
