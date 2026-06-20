"""MCP server exposing the fake system's customer data.

Hermes connects to this over streamable HTTP at:  http://<MCP_HOST>:<MCP_PORT>/mcp
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from fake_system import repository
from fake_system.config import get_settings
from fake_system.db import session_scope

settings = get_settings()

mcp = FastMCP(
    "fake-system",
    instructions=(
        "Customer records for the Nomos fake system. "
        "Use these tools to read and update customer data."
    ),
    host=settings.mcp_host,
    port=settings.mcp_port,
)


@mcp.tool()
def list_customers() -> list[dict]:
    """List every customer in the fake system."""
    with session_scope() as session:
        return [c.as_dict() for c in repository.list_customers(session)]


@mcp.tool()
def get_customer(customer_id: str) -> dict | None:
    """Get a single customer by id (UUID). Returns null if not found."""
    with session_scope() as session:
        customer = repository.get_customer(session, customer_id)
        return customer.as_dict() if customer else None


@mcp.tool()
def update_customer(
    customer_id: str,
    name: str | None = None,
    email: str | None = None,
    company: str | None = None,
    plan: str | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict | None:
    """Update a customer. Only the fields you pass (non-null) are changed.

    Returns the updated customer, or null if no customer has that id.
    """
    with session_scope() as session:
        customer = repository.update_customer(
            session,
            customer_id,
            name=name,
            email=email,
            company=company,
            plan=plan,
            status=status,
            notes=notes,
        )
        return customer.as_dict() if customer else None


@mcp.resource("customers://all")
def customers_resource() -> str:
    """All customers as a JSON document."""
    with session_scope() as session:
        return json.dumps(
            [c.as_dict() for c in repository.list_customers(session)], indent=2
        )


def main() -> None:
    """Console-script entrypoint: serve over streamable HTTP."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
