from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from src.backend.core.operator_auth import require_operator_read
from src.backend.infrastructure.exploration.managers import ExplorationEncounterRuntimeManager

router = APIRouter(
    prefix="/api/internal/exploration", tags=["exploration-internal"], dependencies=[Depends(require_operator_read)]
)


@router.get("/sessions")
async def list_encounter_sessions(
    request: Request,
    response: Response,
    cursor: Annotated[str, Query(pattern=r"^[0-9]+:[0-9]+$", max_length=50)] = "0:0",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[dict]:
    try:
        sessions, next_cursor = await ExplorationEncounterRuntimeManager(request.app.state.redis).list_session_page(
            cursor=cursor, limit=limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if next_cursor:
        response.headers["X-Next-Cursor"] = next_cursor
    return sessions
