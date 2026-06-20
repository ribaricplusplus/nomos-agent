"""Live smoke test for PostgreSQL, dashboard forms, and MCP tools."""

from __future__ import annotations

import asyncio
import uuid

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from fake_system import repository
from fake_system.config import get_settings
from fake_system.db import session_scope
from fake_system.models import Case


async def _test_mcp(case_id: str) -> None:
    settings = get_settings()
    endpoint = f"http://localhost:{settings.mcp_port}/mcp"

    async with streamable_http_client(endpoint) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()
            tools = await client.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            expected = {
                "list_cases",
                "get_case",
                "save_call_result",
                "update_case_status",
                "get_case_summary",
            }
            assert expected <= tool_names

            result = await client.call_tool("get_case", {"case_id": case_id})
            assert not result.isError

            result = await client.call_tool(
                "save_call_result",
                {
                    "case_id": case_id,
                    "duration_seconds": 45,
                    "outcome": "MCP smoke test",
                    "summary": "Created through the MCP endpoint",
                    "confidence": 1.0,
                },
            )
            assert not result.isError

            result = await client.call_tool(
                "update_case_status",
                {
                    "case_id": case_id,
                    "new_status": "RESOLVED",
                    "next_action": "Delete temporary smoke-test data",
                },
            )
            assert not result.isError

            result = await client.call_tool("get_case_summary", {"case_id": case_id})
            assert not result.isError


def _create_test_case(case_id: str) -> None:
    with session_scope() as session:
        session.add(
            Case(
                case_id=case_id,
                case_title="Temporary end-to-end smoke test",
                supplier="Nomos Test",
                grid_operator="Grid Test",
                malo_id="99999999999",
                address="Temporary test address",
                meter_number="TEST-METER",
                registration_date=None,
                supply_start=None,
                status_text="Pending smoke test",
                symptom="Temporary test symptom",
                goal="Verify all PostgreSQL workflows",
                case_status="OPEN",
                next_action="",
            )
        )


def _test_dashboard(case_id: str) -> None:
    settings = get_settings()
    base_url = f"http://localhost:{settings.web_port}"
    with httpx.Client(base_url=base_url, follow_redirects=False, timeout=10) as client:
        health = client.get("/healthz")
        health.raise_for_status()
        assert health.json()["database"] == "reachable"

        index = client.get("/")
        index.raise_for_status()
        assert case_id in index.text

        detail = client.get(f"/cases/{case_id}")
        detail.raise_for_status()
        assert "Complete case data" in detail.text
        assert "Record call result" in detail.text

        status = client.post(
            f"/cases/{case_id}/status",
            data={"case_status": "IN_PROGRESS", "next_action": "Dashboard smoke test"},
        )
        assert status.status_code == 303

        call = client.post(
            f"/cases/{case_id}/calls",
            data={
                "duration_seconds": "30",
                "outcome": "Dashboard smoke test",
                "summary": "Created through the dashboard form",
                "confidence": "0.95",
            },
        )
        assert call.status_code == 303


def _verify_database(case_id: str) -> None:
    with session_scope() as session:
        case = repository.get_case(session, case_id)
        assert case is not None
        assert case.case_status == "RESOLVED"
        assert len(repository.list_call_logs(session, case_id)) == 2
        assert len(repository.list_audit_logs(session, case_id)) == 2


def _delete_test_case(case_id: str) -> None:
    with session_scope() as session:
        case = repository.get_case(session, case_id)
        if case is not None:
            session.delete(case)


async def run() -> None:
    case_id = f"TEST-SMOKE-{uuid.uuid4().hex[:8].upper()}"
    _create_test_case(case_id)
    try:
        _test_dashboard(case_id)
        await _test_mcp(case_id)
        _verify_database(case_id)
    finally:
        _delete_test_case(case_id)


def main() -> None:
    asyncio.run(run())
    print("Smoke test passed: PostgreSQL, dashboard, MCP, calls, and audits.")


if __name__ == "__main__":
    main()
