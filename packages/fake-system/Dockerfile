# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies first (cached layer). uv.lock is optional on first build.
COPY pyproject.toml ./
COPY uv.lock* ./
RUN uv sync --no-dev --no-install-project

# Now copy the project source and install the package itself.
COPY . .
RUN uv sync --no-dev

EXPOSE 8000 8765

# Default command; overridden per-service in compose.yml.
CMD ["fake-system-web"]
