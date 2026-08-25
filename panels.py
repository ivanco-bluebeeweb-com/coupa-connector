"""Coupa Connector panel UI, aligned with UI_INTERFACE_STANDARD.md.

The left sidebar contains plain stacked content only: no card containers, all
form controls have visible labels with contextual placeholders, and App
settings is the last element. Setup instructions live solely in the help
dialog and are not duplicated in the form/sidebar. The connect form stretches
to the full width of the sidebar and its fields stretch to the form's width.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__coupa_settings"),
    )


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"), node,
    ])


def _connection_rows(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No Coupa instances connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for index, connection in enumerate(connections):
        if index:
            children.append(ui.Divider())
        label = connection.get("label") or connection.get("instance_url", "")
        children.append(ui.Stack(direction="v", gap=1, align="start", children=[
            ui.Text(label, variant="body"),
            ui.Text(f"Instance: {connection.get('instance_url', '')}", variant="caption"),
        ]))
    return ui.Stack(direction="v", gap=2, align="stretch", children=children)


def _connect_form() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("How do I set this up?", variant="ghost", size="sm", icon="HelpCircle",
                  on_click=ui.Call("__panel__coupa_connect_help")),
        ui.Form(action="connect_coupa", submit_label="Verify and connect", children=[
            _field("Instance label (optional)", ui.Input(param_name="label", placeholder="e.g. Acme production instance")),
            _field("Coupa instance URL", ui.Input(param_name="instance_url", placeholder="https://acme.coupahost.com")),
            _field("OAuth client ID", ui.Input(param_name="client_id", placeholder="Client ID from Coupa admin OAuth2 Clients")),
            _field("OAuth client secret", ui.Password(param_name="client_secret", placeholder="Secret for that client ID")),
        ]),
    ])


@ext.panel("coupa_connect_help", slot="center", title="Connect Coupa", center_overlay=True)
async def coupa_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Ask your Coupa administrator to create an OAuth2/OpenID Connect Client under Setup, then paste its instance URL, client ID, and client secret here.", variant="body"),
        ui.Alert(title="Instance-specific availability", message="Coupa licenses modules (Requisitions, Purchase Orders, Invoices, Suppliers, Contracts, Expense Reports) independently per instance. Run the access audit after connecting to see what's actually enabled.", type="info"),
        ui.Alert(title="Not included", message="Sourcing (RFx/auctions) and full Supplier Information Management onboarding workflows are separate Coupa modules not covered by this connector.", type="info"),
    ])


@ext.panel("coupa_sidebar", slot="left", title="Coupa", default_width=340, min_width=280, max_width=460)
async def coupa_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    body: list[ui.UINode] = [ui.Text("Coupa", variant="title")]
    if connections:
        body.append(_connection_rows(connections))
        body.append(ui.Divider())
        body.append(ui.ListItem(title="Overview", icon="LayoutDashboard",
                                 on_click=ui.Call("__panel__coupa_center")))
        for label, key in [
            ("Requisitions", "requisitions"), ("Purchase Orders", "purchase_orders"),
            ("Invoices", "invoices"), ("Suppliers", "suppliers"),
            ("Contracts", "contracts"), ("Expense Reports", "expense_reports"),
        ]:
            body.append(ui.ListItem(title=label, icon="ChevronRight",
                                     on_click=ui.Call("__panel__coupa_center", {"section": key})))
    else:
        body.append(_connect_form())
    body.append(ui.Divider())
    body.append(_settings_button())
    return ui.Stack(direction="v", gap=3, align="stretch", children=body)


@ext.panel("coupa_center", slot="center", title="Coupa overview", icon="ShoppingCart", center_overlay=True)
async def coupa_center_panel(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Connect a Coupa instance from the sidebar to see it here.", icon="🟦")

    from schemas import (
        AuditAccessParams, ListRequisitionsParams, ListPurchaseOrdersParams,
        ListInvoicesParams, ListSuppliersParams, ListContractsParams,
        ListExpenseReportsParams,
    )

    conn_id = connections[0].get("id", "")
    section = kwargs.get("section", "")
    body: list[ui.UINode] = []

    async def _section_table(title: str, result, columns) -> None:
        body.append(ui.Text(title, variant="subtitle"))
        if result.success and result.data and result.data.items:
            rows = [{"id": r.id, "title": r.title} for r in result.data.items]
            body.append(ui.DataTable(columns=columns, rows=rows))
        else:
            body.append(ui.Empty(message=f"No {title.lower()} found, or this module isn't licensed here.", icon="Inbox"))

    if not section:
        body.append(ui.Text("Access audit", variant="subtitle"))
        audit_result = await h.audit_coupa_access(ctx, AuditAccessParams(connection_id=conn_id))
        if audit_result.success and audit_result.data:
            r = audit_result.data
            body.append(ui.Stats(children=[
                ui.Stat(label="Available", value=str(r.available_count)),
                ui.Stat(label="Unavailable", value=str(r.unavailable_count)),
            ]))
            for c in r.checks:
                color = "green" if c.available else "red"
                body.append(ui.Stack(direction="h", gap=2, align="center", children=[
                    ui.Badge(label="OK" if c.available else "BLOCKED", color=color),
                    ui.Text(c.name, variant="body"),
                ]))
        else:
            body.append(ui.Text("Could not run the access audit.", variant="caption"))
    elif section == "requisitions":
        result = await h.list_requisitions(ctx, ListRequisitionsParams(connection_id=conn_id, top=25))
        await _section_table("Requisitions", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])
    elif section == "purchase_orders":
        result = await h.list_purchase_orders(ctx, ListPurchaseOrdersParams(connection_id=conn_id, top=25))
        await _section_table("Purchase Orders", result, [{"key": "id", "label": "PO"}, {"key": "title", "label": "Title"}])
    elif section == "invoices":
        result = await h.list_invoices(ctx, ListInvoicesParams(connection_id=conn_id, top=25))
        await _section_table("Invoices", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])
    elif section == "suppliers":
        result = await h.list_suppliers(ctx, ListSuppliersParams(connection_id=conn_id, top=25))
        await _section_table("Suppliers", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Name"}])
    elif section == "contracts":
        result = await h.list_contracts(ctx, ListContractsParams(connection_id=conn_id, top=25))
        await _section_table("Contracts", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])
    elif section == "expense_reports":
        result = await h.list_expense_reports(ctx, ListExpenseReportsParams(connection_id=conn_id, top=25))
        await _section_table("Expense Reports", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Name"}])

    return ui.Stack(direction="v", gap=3, align="stretch", children=body)
