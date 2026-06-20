# nomos-agent

A pnpm monorepo for Nomos. Packages live under [`packages/`](./packages).

## Packages

| Package | Stack | What it is |
| --- | --- | --- |
| [`packages/fake-system`](./packages/fake-system) | Python (uv) · FastAPI · SQLAlchemy · Alembic · MCP | A stand-in "external system" that stores customer data. Ships a small dashboard to view/edit the data and an MCP server that **Hermes** connects to. |

## Prerequisites

- [pnpm](https://pnpm.io) ≥ 9
- [uv](https://docs.astral.sh/uv/) (manages the Python packages)
- Docker + Compose (for Postgres and running services in containers)

## Quick start

```bash
# 1. Install the workspace (node side) and the Python package
pnpm install
pnpm fake-system install:py        # -> uv sync inside packages/fake-system

# 2. Bring up Postgres (+ migrate, seed, web, mcp) with Docker
cp .env.example .env
docker compose up -d               # or: pnpm up

# Dashboard:   http://localhost:8000
# MCP server:  http://localhost:8765/mcp   (streamable HTTP — point Hermes here)
```

### Running the fake-system locally (without containers for the app)

```bash
docker compose up -d postgres      # just the database
cd packages/fake-system
cp .env.example .env
uv sync
uv run alembic upgrade head        # migrations
uv run fake-system-seed            # sample data
uv run fake-system-web             # dashboard on :8000
uv run fake-system-mcp             # MCP server on :8765 (separate terminal)
```

## Compose services

- `postgres` — Postgres 17.
- `fake-system-migrate` — one-shot: runs Alembic migrations then seeds, then exits.
- `fake-system-web` — the customer dashboard (port 8000).
- `fake-system-mcp` — the MCP server Hermes connects to (port 8765).
