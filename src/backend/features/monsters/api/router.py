from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from src.backend.core.database import get_db
from src.backend.features.monsters.api.access import require_monster_catalog_read, require_monster_catalog_write
from src.backend.features.monsters.catalog.bootstrap import MonsterCatalogBootstrapService
from src.backend.features.monsters.catalog.bootstrap_contracts import MonsterCatalogBootstrapDTO
from src.backend.features.monsters.catalog.contracts import (
    MonsterRole,  # noqa: TC001 - FastAPI resolves query annotations
)
from src.backend.features.monsters.catalog.repositories.monster_generation_repository import MonsterGenerationRepository
from src.backend.features.monsters.catalog.services.generated_rebuild_service import MonsterGeneratedRebuildService
from src.backend.features.monsters.inspection.dto.catalog_view import (
    CatalogMonstersResponseDTO,
    CatalogMonstersSummaryDTO,
)
from src.backend.features.monsters.inspection.dto.generated_view import (
    GeneratedMonstersResponseDTO,
    GeneratedMonstersSummaryDTO,
    MonsterDataRebuildRequestDTO,
    MonsterDataRebuildResponseDTO,
)
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService
from src.backend.features.monsters.inspection.services.generated_view_service import GeneratedMonsterViewService

router = APIRouter(
    prefix="/api/admin/monsters",
    tags=["monsters-admin"],
    dependencies=[Depends(require_monster_catalog_read)],
)


@router.get("/catalog/bootstrap", response_model=MonsterCatalogBootstrapDTO)
async def get_monster_catalog_bootstrap(
    response: Response,
    include_system: bool = False,
    if_none_match: Annotated[str | None, Header()] = None,
):
    payload = MonsterCatalogBootstrapService().build(include_system=include_system)
    etag = f'"{payload.version}"'
    headers = {"ETag": etag, "Cache-Control": "private, no-cache", "Vary": "X-Internal-Service-Key"}
    candidates = [value.strip().removeprefix("W/") for value in (if_none_match or "").split(",")]
    if etag in candidates or "*" in candidates:
        return Response(status_code=304, headers=headers)
    response.headers.update(headers)
    return payload


@router.get("/catalog", response_model=CatalogMonstersResponseDTO)
async def get_monster_catalog(
    family_id: str | None = None,
    clan_id: str | None = None,
    role: MonsterRole | None = None,
    include_members: bool = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CatalogMonstersResponseDTO:
    return CatalogMonsterViewService().list_catalog(
        family_id=family_id,
        clan_id=clan_id,
        role=role,
        include_members=include_members,
        limit=limit,
        offset=offset,
    )


@router.get("/catalog/summary", response_model=CatalogMonstersSummaryDTO)
async def get_monster_catalog_summary(family_id: str | None = None) -> CatalogMonstersSummaryDTO:
    return CatalogMonsterViewService().summary(family_id=family_id)


def get_generated_monster_view_service(db_session=Depends(get_db)) -> GeneratedMonsterViewService:
    return GeneratedMonsterViewService(MonsterGenerationRepository(db_session))


def get_monster_generated_rebuild_service(db_session=Depends(get_db)) -> MonsterGeneratedRebuildService:
    return MonsterGeneratedRebuildService(session=db_session)


@router.get("/generated", response_model=GeneratedMonstersResponseDTO)
async def get_generated_monsters(
    service: Annotated[GeneratedMonsterViewService, Depends(get_generated_monster_view_service)],
    family_id: str | None = None,
    clan_id: str | None = None,
    role: str | None = None,
    include_members: bool = True,
    light: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GeneratedMonstersResponseDTO:
    return await service.list_generated(
        family_id=family_id,
        clan_id=clan_id,
        role=role,
        include_members=include_members,
        light=light,
        limit=limit,
        offset=offset,
    )


@router.get("/generated/summary", response_model=GeneratedMonstersSummaryDTO)
async def get_generated_monsters_summary(
    service: Annotated[GeneratedMonsterViewService, Depends(get_generated_monster_view_service)],
    family_id: str | None = None,
) -> GeneratedMonstersSummaryDTO:
    return await service.summary(family_id=family_id)


@router.post("/generated/rebuild/plan", response_model=MonsterDataRebuildResponseDTO)
async def plan_generated_monster_rebuild(
    payload: MonsterDataRebuildRequestDTO,
    service: Annotated[MonsterGeneratedRebuildService, Depends(get_monster_generated_rebuild_service)],
) -> MonsterDataRebuildResponseDTO:
    try:
        return await service.plan(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/generated/rebuild/apply",
    response_model=MonsterDataRebuildResponseDTO,
    dependencies=[Depends(require_monster_catalog_write)],
)
async def apply_generated_monster_rebuild(
    payload: MonsterDataRebuildRequestDTO,
    service: Annotated[MonsterGeneratedRebuildService, Depends(get_monster_generated_rebuild_service)],
) -> MonsterDataRebuildResponseDTO:
    try:
        return await service.apply(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


__all__ = [
    "get_generated_monster_view_service",
    "get_monster_generated_rebuild_service",
    "router",
]
