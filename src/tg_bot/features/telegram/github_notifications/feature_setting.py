from typing import Any


def create_orchestrator(container: Any) -> Any:
    from .orchestrator import GitHubNotificationsOrchestrator

    return GitHubNotificationsOrchestrator(container)
