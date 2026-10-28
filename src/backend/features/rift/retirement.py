"""Explicit boundary for the archived node Rift implementation."""

from src.backend.core.exceptions import BaseAPIException

LEGACY_RIFT_RETIRED_DETAIL = "Legacy node Rift is retired; the new alpha runtime is not implemented."


class LegacyRiftRetiredError(BaseAPIException):
    """No legacy operation may touch storage or return a success."""

    def __init__(self, detail: str = LEGACY_RIFT_RETIRED_DETAIL) -> None:
        super().__init__(status_code=410, detail=detail, error_code="legacy_rift_retired")
