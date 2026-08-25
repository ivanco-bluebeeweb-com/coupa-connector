"""Coupa Connector App settings center panel.

Connection setup guidance lives exclusively in coupa_connect_help.
This panel contains current connection state and destructive disconnect actions only.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h


def _connection_row(connection: dict) -> ui.UINode:
    label = connection.get("label") or connection.get("instance_url", "")
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(label, variant="body"),
        ui.Text(f"Instance: {connection.get('instance_url', '')}", variant="caption"),
        ui.Button(
            "Disconnect", variant="danger", size="sm",
            on_click=ui.Call("disconnect_coupa", {"connection_id": connection.get("id", "")}),
        ),
    ])


@ext.panel("coupa_settings", slot="center", title="Coupa settings", icon="settings", center_overlay=True)
async def coupa_settings_panel(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=2, align="start", children=[
            ui.Header(text="App settings", level=2, subtitle="Manage saved Coupa instances"),
            ui.Text("No Coupa instances are connected yet.", variant="caption"),
        ])
    rows: list[ui.UINode] = [
        ui.Header(text="App settings", level=2, subtitle="Manage saved Coupa instances"),
        ui.Text("Connections", variant="subtitle"),
    ]
    for index, connection in enumerate(connections):
        if index:
            rows.append(ui.Divider())
        rows.append(_connection_row(connection))
    return ui.Stack(direction="v", gap=3, align="stretch", children=rows)
