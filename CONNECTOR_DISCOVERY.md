# Coupa — Connector Discovery

**Discovery date:** 2026-08-25
**Release scope:** Tier 1 + Tier 2 (maximum coverage across licensed modules), per
standing instruction ("максимальный функционал, полный максимум" applied to every
new app).
**Decision owner:** Vlad — Procurement category build-out.

## 1. Target service and official sources

Coupa is a cloud Business Spend Management (BSM) / Source-to-Pay platform, deployed
per customer as an isolated instance (datacenter subdomain, e.g. `*.coupahost.com`
or a customer-specific domain). Its integration surface is the **Coupa Core API** —
a REST API over HTTPS, JSON-first in current releases (the historically-XML "Coupa
Integration" interfaces are legacy/CSV-batch style and are NOT the target here).

### Official sources referenced
- Coupa Compass (integration documentation portal): <https://compass.coupa.com/>
- Coupa Core API reference (Requisitions, Purchase Orders, Invoices, Suppliers,
  Contracts, Expenses): <https://compass.coupa.com/en-us/products/product-documentation/integration-technical-documentation/the-coupa-core-api>
- Coupa OAuth2 setup guide: <https://compass.coupa.com/en-us/products/product-documentation/integration-technical-documentation/oauth2.0>

(Exact per-endpoint paths/params re-verified against the live Compass portal at
implementation time — Coupa versions its Core API per release train and each
customer instance may run a different release; every module/resource is treated
as potentially unlicensed or unavailable for a given instance until a real response
confirms it, the same honesty gate as every other Procurement connector already in
this portfolio.)

## 2. Auth model — OAuth2 client credentials, instance-scoped

Coupa Core API authenticates via **OAuth2 Client Credentials** issued per customer
instance (Setup > OAuth2/OpenID Connect Clients in the Coupa admin UI). Required
fields to connect:
- `instance_url` — the customer's Coupa instance base URL, e.g. `https://acme.coupahost.com`.
- `client_id` / `client_secret` — the OAuth2 client credentials for a Core API
  integration client.
- `token_url` — derived as `{instance_url}/oauth2/token` (documented fixed pattern,
  not separately configurable per Coupa's own OAuth2 guide).

Scopes are assigned per-client on the Coupa side (e.g. `core.requisition.read`,
`core.purchase_order.write`) — the connector requests the full set of scopes its
own client was granted and treats any 403 as "not licensed/not scoped", not a hard
failure, mirroring the Oracle Fusion ERP/Ariba capability-gated pattern already
established in this portfolio.

## 3. Module/resource scope decision (Tier 1 — this release)

Coupa gates functionality behind independently-licensed modules. Discovery decision:
cover the modules explicitly named in the delivery task, each via its Core API
resource:
- **Requisitions** — `/requisitions`
- **Purchase Orders** — `/purchase_orders`
- **Invoices** — `/invoices`
- **Suppliers** — `/suppliers`
- **Contracts** — `/contracts`
- **Expense Reports** — `/expense_reports`

Each resource is probed independently by `audit_coupa_access` before being assumed
present, exactly like `audit_procurement_access` in the Oracle Procurement Cloud
Connector and `audit_ariba_access` in the SAP Ariba Connector.

## 4. Explicitly deferred (out of Tier 1 scope)

- **Sourcing events** (RFx/auctions) — separate Coupa Sourcing module API surface
  with its own event lifecycle; deferred to a later tier, same reasoning as cXML in
  the Ariba connector (keeps v1 scope bounded to the six resources named in the task).
- **Supplier Information Management (SIM) onboarding workflows** — separate
  questionnaire/registration lifecycle; basic supplier read/write is covered, full
  SIM workflow orchestration deferred.

## 5. Pagination and rate limits

Coupa Core API uses **offset-based pagination** (`offset`/`limit` query params,
default page size varies by resource, typically 50). Rate limits are enforced
per-instance and are not publicly documented as a fixed number — the connector
treats HTTP 429 as retryable, consistent with the portfolio-wide fix already
applied per task #2359 (retryable 429 handling).

## 6. Reused portfolio pattern

Architecture mirrors `sap_ariba_client.py` / `oracle_procurement_client.py`: a thin
async OAuth2 client-credentials REST client, token cached with expiry buffer,
generic list-envelope normalisation, and every list/get handler resolving the
connection then treating the resource as potentially absent until a real response
confirms it.
