from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import ValidationError

from src.backend.core.database import get_db
from src.backend.features.monsters.api.access import require_monster_catalog_read, require_monster_catalog_write
from src.backend.features.monsters.api.dependencies import get_cached_monster_selection_service
from src.backend.features.monsters.catalog.bootstrap import MonsterCatalogBootstrapService
from src.backend.features.monsters.catalog.bootstrap_contracts import MonsterCatalogBootstrapDTO
from src.backend.features.monsters.catalog.contracts import (
    MonsterRole,  # noqa: TC001 - FastAPI resolves query annotations
)
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.catalog.repositories.monster_generation_repository import MonsterGenerationRepository
from src.backend.features.monsters.catalog.services.generated_rebuild_service import (
    MonsterGeneratedRebuildService,  # noqa: TC001 - FastAPI inspects annotations
)
from src.backend.features.monsters.catalog.texts import localized_definition
from src.backend.features.monsters.encounters.dto.preparation import MonsterEncounterPreparationDTO
from src.backend.features.monsters.encounters.dto.result import MonsterEncounterSelectionDTO
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import ENCOUNTER_PROFILE_KINDS
from src.backend.features.monsters.encounters.profiles.registry import get_profile
from src.backend.features.monsters.encounters.services.cached_selection_service import (
    CachedMonsterEncounterSelectionService,  # noqa: TC001 - FastAPI inspects dependency annotations
)
from src.backend.features.monsters.encounters.services.encounter_preparation_service import (
    MonsterEncounterPreparationService,
)
from src.backend.features.monsters.inspection.dto.catalog_view import (
    CatalogEquipmentViewDTO,
    CatalogMonstersResponseDTO,
    CatalogMonstersSummaryDTO,
)
from src.backend.features.monsters.inspection.dto.encounter_contract import (
    MonsterContractChoiceDTO,
    MonsterEncounterContractDTO,
    MonsterPartyModeChoiceDTO,
)
from src.backend.features.monsters.inspection.dto.generated_view import (
    GeneratedMonstersResponseDTO,
    GeneratedMonstersSummaryDTO,
    MonsterDataRebuildRequestDTO,
    MonsterDataRebuildResponseDTO,
)
from src.backend.features.monsters.inspection.services.catalog_view_service import CatalogMonsterViewService
from src.backend.features.monsters.inspection.services.generated_view_service import GeneratedMonsterViewService
from src.backend.features.monsters.inspection.services.player_comparison_service import validate_player_attributes
from src.backend.infrastructure.monsters.managers.encounter_pool import EncounterPoolCacheUnavailable

router = APIRouter(
    prefix="/api/admin/monsters",
    tags=["monsters-admin"],
    dependencies=[Depends(require_monster_catalog_read)],
)


@router.get("/encounters/contract", response_model=MonsterEncounterContractDTO)
async def get_monster_encounter_contract() -> MonsterEncounterContractDTO:
    catalog = get_catalog()
    family_ids = {clan.family_id for clan in catalog.find_clans(include_system=False)}
    labels = {"ordinary": "Обычная встреча", "patrol": "Патруль", "guard": "Охрана", "leader": "Главарь"}
    example = get_profile(party_mode="solo", encounter_type="ordinary", difficulty="easy")
    assert example is not None
    return MonsterEncounterContractDTO(
        profile_override_example=example,
        encounter_types=tuple(MonsterContractChoiceDTO(id=key, name=labels[key]) for key in ENCOUNTER_PROFILE_KINDS),
        difficulties=tuple(
            MonsterContractChoiceDTO(id=key, name=name)
            for key, name in (("easy", "Лёгкая"), ("normal", "Средняя"), ("hard", "Тяжёлая"))
        ),
        party_modes=(
            MonsterPartyModeChoiceDTO(id="solo", name="Соло", available=True),
            MonsterPartyModeChoiceDTO(id="group", name="Группа", available=False),
        ),
        location_tiers=tuple(range(8)),
        families=tuple(
            MonsterContractChoiceDTO(id=family.id, name=localized_definition(family)["name"])
            for family in catalog.families.values()
            if family.id in family_ids
        ),
    )


@router.get("/encounters/preview", response_model=MonsterEncounterPreparationDTO)
async def preview_monster_encounter(
    order: Annotated[str, Query(min_length=2, max_length=10000)],
) -> MonsterEncounterPreparationDTO:
    return MonsterEncounterPreparationService().prepare(_parse_encounter_order(order))


def _parse_encounter_order(order: str) -> MonsterEncounterOrderDTO:
    try:
        return MonsterEncounterOrderDTO.model_validate_json(order)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_context=False, include_input=False)) from exc


@router.get("/encounters/select", response_model=MonsterEncounterSelectionDTO)
async def select_monster_encounter(
    order: Annotated[str, Query(min_length=2, max_length=10000)],
    response: Response,
    service: Annotated[CachedMonsterEncounterSelectionService, Depends(get_cached_monster_selection_service)],
) -> MonsterEncounterSelectionDTO:
    parsed = _parse_encounter_order(order)
    try:
        result, status = await service.select(parsed)
    except EncounterPoolCacheUnavailable as exc:
        raise HTTPException(status_code=503, detail={"code": "monster_pool_cache_unavailable", "message": str(exc)}) from exc
    response.headers["X-Monster-Pool-Cache"] = status
    return result


@router.get("/catalog/bootstrap", response_model=MonsterCatalogBootstrapDTO)
async def get_monster_catalog_bootstrap(
    response: Response,
    include_system: bool = False,
    locale: str = "ru",
    if_none_match: Annotated[str | None, Header()] = None,
):
    payload = MonsterCatalogBootstrapService().build(include_system=include_system, locale=locale)
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
    locale: str = "ru",
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CatalogMonstersResponseDTO:
    return CatalogMonsterViewService().list_catalog(
        family_id=family_id,
        clan_id=clan_id,
        role=role,
        include_members=include_members,
        locale=locale,
        limit=limit,
        offset=offset,
    )


@router.get("/catalog/summary", response_model=CatalogMonstersSummaryDTO)
async def get_monster_catalog_summary(family_id: str | None = None) -> CatalogMonstersSummaryDTO:
    return CatalogMonsterViewService().summary(family_id=family_id)


@router.get("/catalog/equipment", response_model=CatalogEquipmentViewDTO)
async def get_monster_catalog_equipment(
    member_id: Annotated[str, Query(min_length=1)],
    tier: Annotated[int, Query(ge=0, le=7)],
    player_attributes: Annotated[str | None, Query(max_length=1000)] = None,
) -> CatalogEquipmentViewDTO:
    try:
        return CatalogMonsterViewService().equipment(
            member_id=member_id,
            tier=tier,
            player_attributes=validate_player_attributes(json.loads(player_attributes))
            if player_attributes is not None
            else None,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def get_generated_monster_view_service(db_session=Depends(get_db)) -> GeneratedMonsterViewService:
    return GeneratedMonsterViewService(MonsterGenerationRepository(db_session))


def get_monster_generated_rebuild_service() -> MonsterGeneratedRebuildService:
    raise HTTPException(
        status_code=410,
        detail={
            "code": "legacy_monster_runtime_retired",
            "message": "Persisted monster rebuild is retired; use the Python catalog.",
        },
    )


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
