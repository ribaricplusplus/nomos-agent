import sqlite3
import json

DB_NAME = "nomos.db"


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        case_title TEXT,
        supplier TEXT,
        grid_operator TEXT,
        malo_id TEXT,
        address TEXT,
        meter_number TEXT,
        registration_date TEXT,
        supply_start TEXT,
        status_text TEXT,
        symptom TEXT,
        goal TEXT,
        case_status TEXT,
        next_action TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_logs (
        call_id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT,
        call_datetime TEXT,
        duration_seconds INTEGER,
        outcome TEXT,
        summary TEXT,
        confidence REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT,
        changed_field TEXT,
        old_value TEXT,
        new_value TEXT,
        changed_at TEXT,
        changed_by TEXT
    )
    """)

    conn.commit()
    conn.close()


def seed_cases():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    with open("data.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for case in data["cases"]:
        cursor.execute("""
        INSERT OR IGNORE INTO cases (
            case_id, case_title, supplier, grid_operator, malo_id,
            address, meter_number, registration_date, supply_start,
            status_text, symptom, goal, case_status, next_action
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case["id"],
            case["case_title"],
            case["lieferant"],
            case["vnb_name"],
            case["malo_id"],
            case["lieferstelle"],
            case["zaehlernummer"],
            case["anmeldung_datum"],
            case["lieferbeginn"],
            case["statustext"],
            case["symptom"],
            case["goal"],
            "OPEN",
            ""
        ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    seed_cases()
    print("Database created and cases inserted successfully.")