from src.frontend.core.api import BaseApiClient


class DiagnosticSessionsApi(BaseApiClient):
    endpoint: str

    async def list_page(self, *, cursor: str = "0:0", limit: int = 100) -> tuple[list[dict], str | None]:
        """Read one diagnostic page without silently discarding its continuation."""
        response = await self.client.request(
            "GET",
            f"{self.base_url}{self.endpoint}",
            params={"cursor": cursor, "limit": limit},
            headers=self._headers(None),
        )
        response.raise_for_status()
        raw = response.json()
        rows = raw.get("data", []) if isinstance(raw, dict) else raw
        return (rows if isinstance(rows, list) else []), response.headers.get("X-Next-Cursor") or None

    async def list_active(self) -> list[dict]:
        """Return only the first diagnostic sample; this is not a total count."""
        rows, _ = await self.list_page()
        return rows
