import uuid

from src.backend.features.monsters.catalog.registry import get_all_family_configs
from src.backend.features.monsters.public import (
    GeneratedClan,
    HabitatClanPoolEntryDTO,
)


class FakeRepository:
    def __init__(self) -> None:
        self.clans: dict[str, GeneratedClan] = {}
        self.entries: list[HabitatClanPoolEntryDTO] = []

    async def get_clan_by_identity_hash(self, identity_hash: str) -> GeneratedClan | None:
        return self.clans.get(identity_hash)

    async def upsert_habitat_clan_pool_entry(self, entry: HabitatClanPoolEntryDTO) -> HabitatClanPoolEntryDTO:
        self.entries = [item for item in self.entries if item.clan_identity_hash != entry.clan_identity_hash]
        self.entries.append(entry)
        return entry


class FakeFactory:
    def __init__(self, repository: FakeRepository) -> None:
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
        self.repository.clans[clan.identity_hash] = clan
        return clan


def _clan_flavors(*family_ids: str) -> dict[str, dict[str, object]]:
    return {
        family_id: {
            "name_ru": family_id.replace("_", " ").title(),
            "description": f"Authored {family_id} clan flavor.",
            "encounter_texts": {
                "patrol": f"{family_id} patrol.",
                "ambush": f"{family_id} ambush.",
                "lair": f"{family_id} lair.",
                "random_meeting": f"{family_id} random meeting.",
            },
        }
        for family_id in family_ids
    }


def test_old_family_tier_availability_helper_is_removed() -> None:
    import src.backend.features.monsters.catalog.registry as resources

    assert not hasattr(resources, "get_available_variants_for_family_tier")
    assert get_all_family_configs()
