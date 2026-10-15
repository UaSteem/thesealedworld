from __future__ import annotations

import uuid

import pytest

from src.backend.features.monsters.dto.generation import GeneratedClan, MonsterGenerationContext, MonsterHabitatDTO
from src.backend.features.monsters.public import EncounterMonsterService


class FakeClanFactory:
    def __init__(self, repository: FakeMonsterRepository) -> None:
        self.repository = repository
        self.calls: list[dict] = []

    async def build_clan_template(self, **kwargs) -> GeneratedClan:
        self.calls.append(dict(kwargs))
        clan = GeneratedClan(
            id=uuid.uuid4(),
            family_id=kwargs["family_id"],
            identity_hash=kwargs["identity_hash"],
            context_identity={"habitat": kwargs["context"].habitat.model_dump(mode="json")},
            context_hash=kwargs["context_hash"],
            selected_traits=[],
            title="Generated",
            description="Generated",
            encounter_texts={},
            generation_version=2,
            resource_version="1",
        )
        self.repository.clans_by_identity[clan.identity_hash] = clan
        return clan


class FakeMonsterRepository:
    def __init__(self) -> None:
        self.clans_by_identity: dict[str, GeneratedClan] = {}
        self.prune_requests: list[dict[str, set[tuple[str, str]]]] = []

    async def get_clan_by_identity_hash(self, identity_hash: str) -> GeneratedClan | None:
        return self.clans_by_identity.get(identity_hash)

    async def delete_generated_clans_outside_zone_contexts(self, expected: dict[str, set[tuple[str, str]]]) -> int:
        self.prune_requests.append(expected)
        return 3


def _context() -> MonsterGenerationContext:
    return MonsterGenerationContext(
        zone_id="rift:starter_rift",
        biome_id="broken_road",
        habitat=MonsterHabitatDTO(biome="broken_road", keys=["road_tract", "scavenger_camp"]),
        tier=1,
        tags=["road_tract", "scavenger_camp"],
        difficulty="mid",
        context_meta={"clan_flavor": {"name_ru": "Authored"}},
    )


@pytest.mark.unit
def test_prepare_encounter_monsters_legacy_api_is_removed() -> None:
    repo = FakeMonsterRepository()
    service = EncounterMonsterService(repo, factory=FakeClanFactory(repo))  # type: ignore[arg-type]

    assert not hasattr(service, "prepare_encounter_monsters")
    assert not hasattr(service, "ensure_clan_for_hash_context")
