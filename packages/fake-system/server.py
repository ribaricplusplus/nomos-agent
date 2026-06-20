from mcp.server.fastmcp import FastMCP
import sqlite3
from datetime import datetime

mcp = FastMCP("fake-nomos-mcp")
DB_NAME = "nomos.db"


@mcp.tool()
def get_case(case_id: str) -> dict:
    """Get one case from the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return {"error": "Case not found"}


@mcp.tool()
def save_call_result(
    case_id: str,
    duration_seconds: int,
    outcome: str,
    summary: str,
    confidence: float
) -> dict:
    """Save call result after the agent completes the call."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO call_logs (
        case_id, call_datetime, duration_seconds, outcome, summary, confidence
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        case_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds,
        outcome,
        summary,
        confidence
    ))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Call log saved"}


@mcp.tool()
def update_case_status(case_id: str, new_status: str, next_action: str) -> dict:
    """Update case status and next action."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT case_status FROM cases WHERE case_id = ?", (case_id,))
    old = cursor.fetchone()

    if not old:
        conn.close()
        return {"error": "Case not found"}

    old_status = old[0]

    cursor.execute("""
    UPDATE cases
    SET case_status = ?, next_action = ?
    WHERE case_id = ?
    """, (new_status, next_action, case_id))

    cursor.execute("""
    INSERT INTO audit_logs (
        case_id, changed_field, old_value, new_value, changed_at, changed_by
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        case_id,
        "case_status",
        old_status,
        new_status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "AI_AGENT"
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "case_id": case_id,
        "old_status": old_status,
        "new_status": new_status,
        "next_action": next_action
    }


@mcp.tool()
def get_case_summary(case_id: str) -> dict:
    """Get case details with latest call log."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    case = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM call_logs
    WHERE case_id = ?
    ORDER BY call_id DESC
    LIMIT 1
    """, (case_id,))
    call = cursor.fetchone()

    conn.close()

    return {
        "case": dict(case) if case else None,
        "latest_call": dict(call) if call else None
    }


if __name__ == "__main__":
    mcp.run()