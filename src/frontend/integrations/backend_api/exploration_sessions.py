from src.frontend.integrations.backend_api.diagnostic_sessions import DiagnosticSessionsApi


class ExplorationSessionsApi(DiagnosticSessionsApi):
    endpoint = "/api/internal/exploration/sessions"
