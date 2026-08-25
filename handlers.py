"""Chat functions for the capability-aware Coupa Connector.

Every handler resolves the target instance connection explicitly (by
connection_id, or the sole connection if only one exists) and never assumes
a Core API module is licensed before a real call confirms it.
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import coupa_client as cc
from app import chat
from schemas import (
    AccessAudit, AuditAccessParams, Capability, ConnectionList,
    ConnectionRefParams, ConnectCoupaParams, CreateRequisitionParams,
    DeleteResult, DisconnectCoupaParams, GetContractParams,
    GetExpenseReportParams, GetInvoiceParams, GetPurchaseOrderParams,
    GetRequisitionParams, GetSupplierParams, ListContractsParams,
    ListExpenseReportsParams, ListInvoicesParams, ListPurchaseOrdersParams,
    ListRequisitionsParams, ListSuppliersParams, NoParams,
    CoupaConnection, CoupaRecord, CoupaRecordList,
)

_SECRET_NAME = "coupa_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(connection: dict) -> CoupaConnection:
    label = connection.get("label") or connection.get("instance_url", "")
    return CoupaConnection(
        id=connection.get("id", ""),
        title=label,
        label=label,
        instance_url=connection.get("instance_url", ""),
    )


async def _resolve_connection(ctx, connection_id: str) -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for connection in connections:
            if connection.get("id") == connection_id:
                return connection
        return None
    return connections[0]


async def _no_connection_error() -> ActionResult:
    return ActionResult.error(
        "No Coupa instance is connected yet. Use connect_coupa first.",
        code="COUPA_NOT_CONNECTED",
    )


def _client_from(connection: dict) -> cc.CoupaClient:
    return cc.CoupaClient(
        connection["instance_url"], connection["client_id"], connection["client_secret"],
    )


def _record(body: dict, id_key: str, title_keys: list[str]) -> CoupaRecord:
    rid = str(body.get(id_key, ""))
    title = ""
    for key in title_keys:
        if body.get(key):
            title = str(body[key])
            break
    return CoupaRecord(id=rid, title=title or rid, fields=body)


@chat.function("connect_coupa", "Connect a Coupa instance (OAuth2 client credentials), after validating connectivity.", action_type="write", chain_callable=True, data_model=CoupaConnection, event="coupa-connector.connect_coupa", effects=["coupa.provider.connected"])
async def connect_coupa(ctx, params: ConnectCoupaParams) -> ActionResult:
    """Imperal action: connect_coupa."""
    client = cc.CoupaClient(params.instance_url, params.client_id, params.client_secret)
    try:
        await client.request("get", "/requisitions", params={"limit": 1})
    except cc.CoupaError as exc:
        if "not licensed" not in str(exc).lower() and "not found" not in str(exc).lower():
            return ActionResult.error(str(exc), code="COUPA_CONNECT_FAILED", retryable=exc.retryable)

    connections = await _load_connections(ctx)
    connection = {
        "id": str(uuid.uuid4()),
        "label": params.label.strip() or params.instance_url,
        "instance_url": client.instance_url,
        "client_id": params.client_id,
        "client_secret": params.client_secret,
    }
    connections.append(connection)
    await _save_connections(ctx, connections)
    return ActionResult.ok(_connection_entity(connection))


@chat.function("disconnect_coupa", "Disconnect one Coupa instance: deletes only the credentials saved in Imperal. Nothing is changed in Coupa.", action_type="write", chain_callable=True, data_model=DeleteResult, event="coupa-connector.disconnect_coupa", effects=["coupa.provider.disconnected"])
async def disconnect_coupa(ctx, params: DisconnectCoupaParams) -> ActionResult:
    """Imperal action: disconnect_coupa."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("No connection found with that id.", code="COUPA_CONNECTION_NOT_FOUND")
    await _save_connections(ctx, remaining)
    return ActionResult.ok(DeleteResult(deleted=True, id=params.connection_id))


@chat.function("list_connections", "List the connected Coupa instances.", action_type="read", chain_callable=True, data_model=ConnectionList, event="coupa-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """Imperal action: list_connections."""
    connections = await _load_connections(ctx)
    items = [_connection_entity(c) for c in connections]
    return ActionResult.ok(ConnectionList(items=items, total=len(items)))


async def _list_resource(ctx, params, path: str, id_key: str, title_keys: list[str], extra_params: dict | None = None) -> ActionResult:
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    query = {"limit": params.top}
    if extra_params:
        query.update({k: v for k, v in extra_params.items() if v})
    try:
        body = await client.request("get", path, params=query)
    except cc.CoupaError as exc:
        return ActionResult.error(str(exc), code="COUPA_REQUEST_FAILED", retryable=exc.retryable)
    items = cc.rest_items(body)
    records = [_record(item, id_key, title_keys) for item in items]
    return ActionResult.ok(CoupaRecordList(items=records, total=len(records)))


async def _get_resource(ctx, params, path: str, id_key: str, title_keys: list[str]) -> ActionResult:
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    try:
        body = await client.request("get", path)
    except cc.CoupaError as exc:
        return ActionResult.error(str(exc), code="COUPA_REQUEST_FAILED", retryable=exc.retryable)
    return ActionResult.ok(_record(body, id_key, title_keys))


@chat.function("list_requisitions", "List Requisitions on the connected Coupa instance, optionally filtered by status.", action_type="read", chain_callable=True, data_model=CoupaRecordList, event="coupa-connector.list_requisitions")
async def list_requisitions(ctx, params: ListRequisitionsParams) -> ActionResult:
    """Imperal action: list_requisitions."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/requisitions", "id", ["justification", "name"], extra)


@chat.function("get_requisition", "Read one Requisition in full by its unique identifier.", action_type="read", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.get_requisition")
async def get_requisition(ctx, params: GetRequisitionParams) -> ActionResult:
    """Imperal action: get_requisition."""
    return await _get_resource(ctx, params, f"/requisitions/{params.requisition_id}", "id", ["justification", "name"])


@chat.function("create_requisition", "Create a new Requisition with line items.", action_type="write", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.create_requisition", effects=["coupa.requisition.created"])
async def create_requisition(ctx, params: CreateRequisitionParams) -> ActionResult:
    """Imperal action: create_requisition."""
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    payload = {
        "justification": params.justification,
        "requested-by": {"email": params.requested_by_email},
        "requisition-lines": params.lines,
    }
    try:
        body = await client.request("post", "/requisitions", json_body=payload)
    except cc.CoupaError as exc:
        return ActionResult.error(str(exc), code="COUPA_REQUEST_FAILED", retryable=exc.retryable)
    return ActionResult.ok(_record(body, "id", ["justification", "name"]))


@chat.function("list_purchase_orders", "List Purchase Orders, optionally filtered by supplier.", action_type="read", chain_callable=True, data_model=CoupaRecordList, event="coupa-connector.list_purchase_orders")
async def list_purchase_orders(ctx, params: ListPurchaseOrdersParams) -> ActionResult:
    """Imperal action: list_purchase_orders."""
    extra = {"supplier": params.supplier} if params.supplier else None
    return await _list_resource(ctx, params, "/purchase_orders", "id", ["po-number", "name"], extra)


@chat.function("get_purchase_order", "Read one Purchase Order in full by its unique identifier.", action_type="read", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.get_purchase_order")
async def get_purchase_order(ctx, params: GetPurchaseOrderParams) -> ActionResult:
    """Imperal action: get_purchase_order."""
    return await _get_resource(ctx, params, f"/purchase_orders/{params.order_id}", "id", ["po-number", "name"])


@chat.function("list_invoices", "List Invoices, optionally filtered by status.", action_type="read", chain_callable=True, data_model=CoupaRecordList, event="coupa-connector.list_invoices")
async def list_invoices(ctx, params: ListInvoicesParams) -> ActionResult:
    """Imperal action: list_invoices."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/invoices", "id", ["invoice-number", "name"], extra)


@chat.function("get_invoice", "Read one Invoice in full by its unique identifier.", action_type="read", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.get_invoice")
async def get_invoice(ctx, params: GetInvoiceParams) -> ActionResult:
    """Imperal action: get_invoice."""
    return await _get_resource(ctx, params, f"/invoices/{params.invoice_id}", "id", ["invoice-number", "name"])


@chat.function("list_suppliers", "List Suppliers registered on this Coupa instance.", action_type="read", chain_callable=True, data_model=CoupaRecordList, event="coupa-connector.list_suppliers")
async def list_suppliers(ctx, params: ListSuppliersParams) -> ActionResult:
    """Imperal action: list_suppliers."""
    extra = {"name": params.query} if params.query else None
    return await _list_resource(ctx, params, "/suppliers", "id", ["name"], extra)


@chat.function("get_supplier", "Read one Supplier in full by its Supplier ID.", action_type="read", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.get_supplier")
async def get_supplier(ctx, params: GetSupplierParams) -> ActionResult:
    """Imperal action: get_supplier."""
    return await _get_resource(ctx, params, f"/suppliers/{params.supplier_id}", "id", ["name"])


@chat.function("list_contracts", "List Contracts, optionally filtered by status.", action_type="read", chain_callable=True, data_model=CoupaRecordList, event="coupa-connector.list_contracts")
async def list_contracts(ctx, params: ListContractsParams) -> ActionResult:
    """Imperal action: list_contracts."""
    return await _list_resource(ctx, params, "/contracts", "id", ["name", "title"])


@chat.function("get_contract", "Read one Contract in full by its unique identifier.", action_type="read", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.get_contract")
async def get_contract(ctx, params: GetContractParams) -> ActionResult:
    """Imperal action: get_contract."""
    return await _get_resource(ctx, params, f"/contracts/{params.contract_id}", "id", ["name", "title"])


@chat.function("list_expense_reports", "List Expense Reports, optionally filtered by status.", action_type="read", chain_callable=True, data_model=CoupaRecordList, event="coupa-connector.list_expense_reports")
async def list_expense_reports(ctx, params: ListExpenseReportsParams) -> ActionResult:
    """Imperal action: list_expense_reports."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/expense_reports", "id", ["name"], extra)


@chat.function("get_expense_report", "Read one Expense Report in full by its unique identifier.", action_type="read", chain_callable=True, data_model=CoupaRecord, event="coupa-connector.get_expense_report")
async def get_expense_report(ctx, params: GetExpenseReportParams) -> ActionResult:
    """Imperal action: get_expense_report."""
    return await _get_resource(ctx, params, f"/expense_reports/{params.expense_report_id}", "id", ["name"])


@chat.function("audit_coupa_access", "Probe every core Coupa Core API module (Requisitions, POs, Invoices, Suppliers, Contracts, Expense Reports) and report which are actually enabled for this instance, without changing anything.", action_type="read", chain_callable=True, data_model=AccessAudit, event="coupa-connector.audit_coupa_access")
async def audit_coupa_access(ctx, params: AuditAccessParams) -> ActionResult:
    """Imperal action: audit_coupa_access."""
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    probes = [
        ("Requisitions", "/requisitions"),
        ("Purchase Orders", "/purchase_orders"),
        ("Invoices", "/invoices"),
        ("Suppliers", "/suppliers"),
        ("Contracts", "/contracts"),
        ("Expense Reports", "/expense_reports"),
    ]
    checks: list[Capability] = []
    for name, path in probes:
        try:
            await client.request("get", path, params={"limit": 1})
            checks.append(Capability(name=name, available=True, note="Reachable"))
        except cc.CoupaError as exc:
            checks.append(Capability(name=name, available=False, note=str(exc)))
    available = sum(1 for c in checks if c.available)
    return ActionResult.ok(AccessAudit(
        instance_url=connection.get("instance_url", ""),
        capabilities=checks,
        checks=checks,
        available_count=available,
        unavailable_count=len(checks) - available,
    ))
