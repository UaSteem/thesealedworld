import inspect
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.backend.features.rift.resources.layout_presets import resolve_scheme_for_geometry_pattern
from src.backend.features.rift.runtime.hex.generation.builder import (
    DEFAULT_LAYOUT_SCHEME_KEY,
    RANDOM_LAYOUT_SCHEME_KEY,
    HexRiftStateDTO,
)
from src.backend.features.rift.services.hex_runtime_service import (
    HEX_RIFT_INSTANCES,
    HexRiftInstanceNotFoundError,
    HexRiftInvalidActionError,
    HexRiftRuntimeService,
)

router = APIRouter(prefix="/api/dev/rift/hex-test", tags=["rift-hex-test"])


class HexMoveRequest(BaseModel):
    target_x: int
    target_y: int


class ResolveCombatRequest(BaseModel):
    action: Literal["fight", "escape"]


def _runtime_service() -> HexRiftRuntimeService:
    return HexRiftRuntimeService(instances=HEX_RIFT_INSTANCES)


@router.post("/start", response_model=HexRiftStateDTO)
async def start_hex_rift(
    request: Request,
    seed: str | None = None,
    scale_key: str = "solo",
    difficulty_key: str = "easy",
    scheme_key: str | None = None,
    pattern_key: str | None = None,
    show_all_map: bool = False,
) -> HexRiftStateDTO:
    service = _runtime_service()
    try:
        resolved_scheme_key = (
            resolve_scheme_for_geometry_pattern(scale_key, pattern_key)
            if pattern_key and pattern_key != RANDOM_LAYOUT_SCHEME_KEY
            else RANDOM_LAYOUT_SCHEME_KEY
            if pattern_key == RANDOM_LAYOUT_SCHEME_KEY or scheme_key == RANDOM_LAYOUT_SCHEME_KEY
            else scheme_key or DEFAULT_LAYOUT_SCHEME_KEY
        )
        state = service.start(
            seed=seed,
            scale_key=scale_key,
            difficulty_key=difficulty_key,
            scheme_key=resolved_scheme_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await _save_hex_world_if_available(request, state, seed=seed)
    return service.client_view(state, show_all_map=show_all_map)


async def _save_hex_world_if_available(request: Request, state: HexRiftStateDTO, *, seed: str | None) -> None:
    app_state = getattr(getattr(request, "app", None), "state", None)
    redis_managers = getattr(app_state, "redis_managers", None)
    hex_worlds = getattr(redis_managers, "hex_rift_worlds", None)
    save_world = getattr(hex_worlds, "save_world", None)
    if inspect.iscoroutinefunction(save_world):
        await save_world(state, seed=seed)


@router.get("/{instance_id}/state", response_model=HexRiftStateDTO)
async def get_hex_rift_state(instance_id: str, show_all_map: bool = False) -> HexRiftStateDTO:
    service = _runtime_service()
    return service.client_view(service.get_or_create(instance_id), show_all_map=show_all_map)


@router.post("/{instance_id}/move", response_model=HexRiftStateDTO)
async def move_hex_rift(instance_id: str, request: HexMoveRequest) -> HexRiftStateDTO:
    try:
        return _runtime_service().move(instance_id, target_x=request.target_x, target_y=request.target_y)
    except HexRiftInstanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Hex rift instance not found") from exc
    except HexRiftInvalidActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{instance_id}/resolve-combat", response_model=HexRiftStateDTO)
async def resolve_combat_endpoint(instance_id: str, request: ResolveCombatRequest) -> HexRiftStateDTO:
    try:
        return _runtime_service().resolve_combat(instance_id, action=request.action)
    except HexRiftInstanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Hex rift instance not found") from exc
    except HexRiftInvalidActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{instance_id}/next-floor", response_model=HexRiftStateDTO)
async def next_floor_endpoint(instance_id: str) -> HexRiftStateDTO:
    try:
        return _runtime_service().next_floor(instance_id)
    except HexRiftInstanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Hex rift instance not found") from exc
    except HexRiftInvalidActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
