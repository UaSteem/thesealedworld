from src.frontend.integrations.backend_api.diagnostic_sessions import DiagnosticSessionsApi


class ScenarioSessionsApi(DiagnosticSessionsApi):
    endpoint = "/api/internal/scenario/sessions"
