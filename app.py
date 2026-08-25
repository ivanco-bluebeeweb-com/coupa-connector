"""Coupa Connector extension declaration and instance-scoped credential storage.

Coupa Core API module availability is instance-, license-, and contract-dependent —
Requisitions, Purchase Orders, Invoices, Suppliers, Contracts, and Expense Reports
are each independently licensed per customer instance. The connector stores one or
more explicitly configured instance connections and handlers must treat any module
as potentially unavailable until a real response confirms it.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "coupa-connector",
    version="0.1.0",
    display_name="Coupa",
    description=(
        "Connect your own Coupa Business Spend Management instance through "
        "OAuth2 client credentials. Read and safely manage Requisitions, "
        "Purchase Orders, Invoices, Suppliers, Contracts, and Expense Reports "
        "through the instance's licensed Core API modules."
    ),
    icon="icon.svg",
    capabilities=["coupa:read", "coupa:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="coupa",
    description=(
        "Coupa Connector — capability-aware, instance-scoped REST operations "
        "for Requisitions, Purchase Orders, Invoices, Suppliers, Contracts, "
        "and Expense Reports, restricted to modules the instance has actually "
        "licensed."
    ),
)

ext.secret(
    "coupa_connections",
    "JSON list of connected Coupa instances and encrypted OAuth credentials. Managed only through connect_coupa and disconnect_coupa.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Coupa instance is connected."""
    import json

    raw = await ctx.secrets.get("coupa_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    return {"connected": bool(connections), "connection_count": len(connections)}
