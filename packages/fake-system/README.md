# @nomos/fake-system

A PostgreSQL-backed stand-in for the Nomos case system. The dashboard and MCP
server share one SQLAlchemy data layer containing:

- cases imported from `data.json`;
- call results recorded by the agent; and
- an audit trail for case-status changes.

The database schema is managed with Alembic. There is no SQLite runtime or
local `.db` file.

## Run locally

From the `nomos-agent` directory:

```bash
docker compose up -d postgres
cd packages/fake-system
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run fake-system-seed
uv run fake-system-web
```

In another terminal:

```bash
uv run fake-system-mcp
```

- Dashboard: `http://localhost:8000`
- MCP endpoint: `http://localhost:8765/mcp`

Running `docker compose up -d` from `nomos-agent` performs migration and seeding
automatically before starting both services.

## Configuration

The application reads a SQLAlchemy URL from `DATABASE_URL`:

```dotenv
DATABASE_URL=postgresql+psycopg://nomos:nomos@localhost:5432/fake_system
```

Use a dedicated database role and secret manager outside local development.

## Database changes

After modifying `src/fake_system/models.py`:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

Migration `0002` replaces the earlier placeholder `customers` table with the
case workflow tables. Back up any data in that placeholder table before
upgrading if it must be retained.

Migration `0003` removes the two temporary metadata columns so the `cases`
table matches the original SQLite column contract exactly.

Migration `0004` changes the original placeholder IDs to stable alphanumeric
IDs and enables cascading ID updates so related call and audit logs are
preserved.

## MCP capabilities

| Kind | Name | Purpose |
| --- | --- | --- |
| tool | `list_cases` | List all cases |
| tool | `get_case(case_id)` | Fetch one case |
| tool | `save_call_result(...)` | Store an agent call result |
| tool | `update_case_status(...)` | Update status and write an audit event |
| tool | `update_case_details(...)` | Update MaLo or other case details with audit events |
| tool | `get_case_summary(case_id)` | Fetch a case and its latest call |
| resource | `cases://all` | Return all cases as JSON |

## Quality checks

```bash
uv run ruff check .
uv run pytest
uv run alembic check
uv run fake-system-smoke
```

The smoke test creates a uniquely named temporary case, verifies PostgreSQL,
dashboard status updates, dashboard call logging, all MCP tools, and audit
logging, then deletes the temporary case and its related records.
