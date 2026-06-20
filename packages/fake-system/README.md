# @nomos/fake-system

A stand-in "external system" for Nomos that stores **customer data**. It has two faces over one database:

- a small **dashboard** (FastAPI + Jinja2) to view and edit customers, and
- an **MCP server** that **Hermes** connects to in order to read and update that same data.

Python project, managed with [uv](https://docs.astral.sh/uv/). ORM is **SQLAlchemy 2.0**; migrations are **Alembic**.

## Layout

```
packages/fake-system/
├── pyproject.toml            # deps + console scripts (managed by uv)
├── alembic.ini
├── migrations/               # Alembic (env.py + versions/)
└── src/fake_system/
    ├── config.py             # settings from env / .env
    ├── db.py                 # engine + session scope
    ├── models.py             # SQLAlchemy models (Customer)
    ├── repository.py         # CRUD shared by web + MCP
    ├── seed.py               # sample data
    ├── web/app.py            # dashboard (FastAPI)
    └── mcp_server.py         # MCP server (FastMCP, streamable HTTP)
```

## Develop

```bash
cp .env.example .env          # point DATABASE_URL at your Postgres
uv sync                       # create the venv + install deps

uv run alembic upgrade head   # apply migrations
uv run fake-system-seed       # insert sample customers

uv run fake-system-web        # dashboard  -> http://localhost:8000
uv run fake-system-mcp        # MCP server -> http://localhost:8765/mcp
```

A local Postgres is easiest via the repo-root compose file: `docker compose up -d postgres`.

## Migrations

```bash
# after editing models.py
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## MCP server

`fake-system-mcp` serves over **streamable HTTP**. Point Hermes (or any MCP client) at:

```
http://<host>:8765/mcp
```

Exposed capabilities:

| Kind | Name | Purpose |
| --- | --- | --- |
| tool | `list_customers` | List all customers |
| tool | `get_customer(customer_id)` | Fetch one customer by UUID |
| tool | `update_customer(customer_id, …)` | Update provided fields on a customer |
| resource | `customers://all` | All customers as JSON |

Host/port come from `MCP_HOST` / `MCP_PORT` (see `.env.example`).
