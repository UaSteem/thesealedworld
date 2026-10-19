from src.frontend.integrations.backend_api.diagnostic_sessions import DiagnosticSessionsApi


class CombatSessionsApi(DiagnosticSessionsApi):
    endpoint = "/api/internal/combat/sessions"

    async def get_session(self, session_id: str) -> dict | None:
        try:
            raw = await self._request("GET", f"/api/internal/combat/sessions/{session_id}")
            return raw if isinstance(raw, dict) else None
        except Exception:
            return None
