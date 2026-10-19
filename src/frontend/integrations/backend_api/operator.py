"""Server-side operator transport; ordinary site credentials are never inherited."""

from typing import Any

import httpx

from src.frontend.core.api import BaseApiClient


class OperatorApiClient(BaseApiClient):
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        *,
        operator_read_key: str = "",
        operator_write_key: str = "",
        read_only: bool = False,
    ) -> None:
        super().__init__(client, base_url, internal_service_key="", internal_service_header="X-Operator-Key")
        self._operator_read_key = operator_read_key
        self._operator_write_key = operator_write_key
        self._read_only = read_only

    async def _request(self, method: str, endpoint: str, response_model: Any = None, **kwargs: Any) -> Any:
        mutation = method.upper() not in {"GET", "HEAD", "OPTIONS"}
        if mutation and self._read_only:
            response = httpx.Response(403, request=httpx.Request(method, f"{self.base_url}{endpoint}"))
            raise httpx.HTTPStatusError("Selected source is read-only", request=response.request, response=response)
        key = self._operator_write_key if mutation else self._operator_read_key or self._operator_write_key
        headers = {
            name: value
            for name, value in dict(kwargs.pop("headers", {}) or {}).items()
            if name.lower() not in {"x-operator-key", "x-internal-service-key"}
        }
        if key:
            headers["X-Operator-Key"] = key
        return await super()._request(method, endpoint, response_model=response_model, headers=headers, **kwargs)
