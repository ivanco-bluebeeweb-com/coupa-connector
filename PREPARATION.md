# Coupa Connector — Preparation

**Version:** 0.1.0 (planning)
**Date:** 2026-08-25
**Product owner:** Vlad / Bluebeeweb
**Related delivery task:** BBW Imperal Apps #2581 — `[App Development] Coupa Connector`
**Scope decision:** maximum feasible capability through the instance's licensed
Core API modules (per standing "максимальный функционал" instruction).

## 1. App passport

**Name:** Coupa Connector
**One-line purpose:** Connect an organization's own Coupa Business Spend Management
instance to read and safely manage the Source-to-Pay cycle — Requisitions,
Purchase Orders, Invoices, Suppliers, Contracts, and Expense Reports — through
Coupa's official Core API.

**Why now:** Coupa is Gartner's Source-to-Pay Leader and the most recognisable
UX-first challenger to SAP Ariba — it rounds out the Procurement category with a
non-SAP-stack option, matching how SAP Ariba/Oracle Procurement Cloud already
cover the SAP/Oracle-aligned side of the market.

**What it is not:**
- Not a replacement for Coupa's own approval chains/workflow engine.
- Does not implement the Sourcing module's RFx/auction lifecycle (see
  `CONNECTOR_DISCOVERY.md` §4 — deferred, separate module surface).
- Does not assume any Core API resource is licensed for a given instance — every
  call treats the resource as potentially unavailable until a real response
  confirms it.

## 2. Human problem

> A procurement analyst, AP clerk, or expense approver needs to check a
> requisition's approval status, look up a purchase order or invoice, review a
> supplier's record, or see which expense reports are pending — without opening
> Coupa's own multi-tab UI.

### Personas and high-value moments
| Persona | Trigger | Value |
|---|---|---|
| Procurement analyst | Needs requisition/PO status | Track approvals in plain language |
| AP clerk | Needs invoice status/amount | See what's paid/pending without hunting tabs |
| Expense approver | Needs pending expense reports | Quick approval-queue visibility |
| Category manager | Needs supplier/contract lookup | See who's contracted and on what terms |

## 3. Scope (Tier 1 + Tier 2)

- `connect_coupa` / `disconnect_coupa` / `list_connections` — OAuth2 client
  credentials, instance-scoped, multi-instance support.
- `list_requisitions` / `get_requisition` / `create_requisition`
- `list_purchase_orders` / `get_purchase_order`
- `list_invoices` / `get_invoice`
- `list_suppliers` / `get_supplier`
- `list_contracts` / `get_contract`
- `list_expense_reports` / `get_expense_report`
- `audit_coupa_access` — capability probe across all six modules.

## 4. Non-goals (this release)

- Sourcing events/RFx (separate module, deferred).
- Full SIM onboarding workflow orchestration (deferred; basic supplier CRUD only).
- Punchout/catalog integration (separate B2B messaging surface, out of scope).

## 5. Security

- OAuth2 client credentials stored via `ext.secret`, never hardcoded.
- Public git repo with zero secrets committed.
- Every module treated as potentially unlicensed until a real response confirms it.
