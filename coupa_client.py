"""Thin OAuth2 REST client for Coupa Core API (instance-scoped).

Instance capability differs by licensed module and customer contract. The client
speaks generic REST/JSON and never assumes a module is licensed before the
instance confirms it via a real response.
"""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import httpx


class CoupaError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


def normalise_base_url(value: str) -> str:
    url = (value or "").strip().rstrip("/")
    if not url.startswith("https://"):
        raise CoupaError("Instance URL must be an HTTPS host, e.g. https://acme.coupahost.com.")
    return url


def rest_items(body: Any) -> list[dict[str, Any]]:
    """Normalise Coupa Core API list envelopes to a list of objects."""
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if not isinstance(body, dict):
        return []
    for key in ("items", "results", "value"):
        items = body.get(key)
        if isinstance(items, list):
            return items
    return []


class CoupaClient:
    """OAuth2 client-credentials REST client for Coupa's instance-scoped Core API."""

    def __init__(
        self,
        instance_url: str,
        client_id: str,
        client_secret: str,
        *,
        timeout: float = 30.0,
    ):
        self.instance_url = normalise_base_url(instance_url)
        self.token_url = f"{self.instance_url}/oauth2/token"
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._token: str | None = None
        self._token_expiry: float = 0.0

    async def _ensure_token(self, http: httpx.AsyncClient) -> None:
        if self._token and time.time() < self._token_expiry - 30:
            return
        try:
            resp = await http.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": (
                        "core.requisition.read core.requisition.write "
                        "core.purchase_order.read core.invoice.read "
                        "core.supplier.read core.supplier.write "
                        "core.contract.read core.expense_report.read"
                    ),
                },
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise CoupaError(f"Could not reach Coupa OAuth2 token endpoint: {exc}", retryable=True) from exc
        if resp.status_code >= 400:
            raise CoupaError(
                f"Coupa OAuth2 token request failed (HTTP {resp.status_code}). Check client ID/secret and instance URL.",
                retryable=resp.status_code >= 500 or resp.status_code == 429,
            )
        payload = resp.json()
        token = payload.get("access_token")
        if not token:
            raise CoupaError("Coupa OAuth2 response did not include an access_token.")
        self._token = token
        self._token_expiry = time.time() + int(payload.get("expires_in", 3600))

    async def request(self, method: str, path: str, *, params: dict | None = None, json_body: dict | None = None) -> Any:
        url = urljoin(self.instance_url + "/", path.lstrip("/"))
        async with httpx.AsyncClient() as http:
            await self._ensure_token(http)
            headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
            try:
                resp = await http.request(method, url, headers=headers, params=params, json=json_body, timeout=self.timeout)
            except httpx.HTTPError as exc:
                raise CoupaError(f"Could not reach Coupa Core API: {exc}", retryable=True) from exc
        if resp.status_code == 404:
            raise CoupaError("Resource not found, or this module is not licensed on this Coupa instance.", retryable=False)
        if resp.status_code == 403:
            raise CoupaError("This Coupa module is not licensed/scoped for the connected OAuth client.", retryable=False)
        if resp.status_code == 429:
            raise CoupaError("Coupa Core API rate limit hit. Retry shortly.", retryable=True)
        if resp.status_code >= 400:
            raise CoupaError(f"Coupa Core API request failed (HTTP {resp.status_code}).", retryable=resp.status_code >= 500)
        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {}
