"""Pydantic input contracts and SDL result entities for Coupa Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved Coupa instance connection ID. Omit to use the first connected instance.")


class ConnectCoupaParams(BaseModel):
    label: str = Field("", description="Friendly instance label, e.g. 'Acme Production'.")
    instance_url: str = Field(..., description="Coupa instance base URL, e.g. https://acme.coupahost.com.")
    client_id: str = Field(..., description="OAuth2 client ID issued via Coupa admin (Setup > OAuth2/OpenID Connect Clients).")
    client_secret: str = Field(..., description="OAuth2 client secret for that client.")


class DisconnectCoupaParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved Coupa instance connection ID to remove from Imperal.")


class ListRequisitionsParams(ConnectionRefParams):
    status: str = Field("", description="Optional requisition status filter, e.g. approved, pending_approval.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetRequisitionParams(ConnectionRefParams):
    requisition_id: str = Field(..., description="Coupa requisition unique identifier.")


class CreateRequisitionParams(ConnectionRefParams):
    justification: str = Field(..., description="Requisition justification/description.")
    requested_by_email: str = Field(..., description="Email of the Coupa user this requisition is created for.")
    lines: list[dict] = Field(..., description="List of {description, quantity, price, need_by_date} line dicts.")


class ListPurchaseOrdersParams(ConnectionRefParams):
    supplier: str = Field("", description="Optional supplier name filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetPurchaseOrderParams(ConnectionRefParams):
    order_id: str = Field(..., description="Coupa purchase order unique identifier.")


class ListInvoicesParams(ConnectionRefParams):
    status: str = Field("", description="Optional invoice status filter, e.g. approved, disputed, pending_approval.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetInvoiceParams(ConnectionRefParams):
    invoice_id: str = Field(..., description="Coupa invoice unique identifier.")


class ListSuppliersParams(ConnectionRefParams):
    query: str = Field("", description="Optional supplier name search filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetSupplierParams(ConnectionRefParams):
    supplier_id: str = Field(..., description="Coupa supplier unique identifier.")


class ListContractsParams(ConnectionRefParams):
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetContractParams(ConnectionRefParams):
    contract_id: str = Field(..., description="Coupa contract unique identifier.")


class ListExpenseReportsParams(ConnectionRefParams):
    status: str = Field("", description="Optional expense report status filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetExpenseReportParams(ConnectionRefParams):
    expense_report_id: str = Field(..., description="Coupa expense report unique identifier.")


class AuditAccessParams(ConnectionRefParams):
    pass


class CoupaConnection(sdl.Entity):
    id: str
    title: str
    label: str
    instance_url: str


class ConnectionList(sdl.Entity):
    items: list[CoupaConnection] = Field(default_factory=list)
    total: int = 0


class CoupaRecord(sdl.Entity):
    id: str
    title: str
    fields: dict = Field(default_factory=dict)


class CoupaRecordList(sdl.Entity):
    items: list[CoupaRecord] = Field(default_factory=list)
    total: int = 0


class Capability(sdl.Entity):
    name: str
    available: bool
    note: str


class AccessAudit(sdl.Entity):
    instance_url: str
    capabilities: list[Capability] = Field(default_factory=list)
    available_count: int = 0
    unavailable_count: int = 0
    checks: list[Capability] = Field(default_factory=list)


class DeleteResult(sdl.Entity):
    deleted: bool
    id: str
