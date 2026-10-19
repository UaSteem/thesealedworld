from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from src.backend.core.operator_auth import require_operator_read
from src.backend.infrastructure.combat.managers.session import CombatSessionManager

router = APIRouter(
    prefix="/api/internal/combat", tags=["combat-internal"], dependencies=[Depends(require_operator_read)]
)


def _session_manager(request: Request) -> CombatSessionManager:
    return CombatSessionManager(request.app.state.redis)


def _fmt_ts(ts: str | int | None) -> str:
    if not ts:
        return "—"
    try:
        import datetime

        return datetime.datetime.fromtimestamp(int(ts)).strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return str(ts)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, request: Request) -> dict:
    mgr = _session_manager(request)
    meta = await mgr.get_meta(session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found")
    fields = (
        "active",
        "status",
        "battle_type",
        "step_counter",
        "active_actors_count",
        "winner",
        "started_at",
        "last_activity_at",
    )
    return {"session_id": session_id, **{key: meta[key] for key in fields if key in meta}}


@router.get("/sessions")
async def list_active_sessions(
    request: Request,
    response: Response,
    cursor: Annotated[str, Query(pattern=r"^[0-9]+:[0-9]+$", max_length=50)] = "0:0",
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[dict]:
    mgr = _session_manager(request)
    try:
        sessions, next_cursor = await mgr.list_session_page(cursor=cursor, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if next_cursor:
        response.headers["X-Next-Cursor"] = next_cursor
    now = int(time.time())
    result = []
    for sid, meta in sessions:
        last_ts = meta.get("last_activity_at")
        idle_sec = (now - int(last_ts)) if last_ts else None
        result.append(
            {
                "session_id": sid,
                "status": meta.get("status", "unknown"),
                "battle_type": meta.get("battle_type", "—"),
                "step": meta.get("step_counter", "0"),
                "alive": meta.get("active_actors_count", "?"),
                "winner": meta.get("winner") or "—",
                "started_at": _fmt_ts(meta.get("started_at")),
                "idle": f"{idle_sec}s" if idle_sec is not None else "—",
            }
        )
    return result
