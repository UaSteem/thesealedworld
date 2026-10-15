import uuid

import pytest

from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO
from src.backend.features.monsters.catalog.materialization.generation_builder import (
    MonsterClanGenerationBuilder,
    _MemberPlan,
)
from src.backend.features.monsters.catalog.materialization.hashing import compute_context_hash, normalize_tags
from src.backend.features.monsters.catalog.registry import get_family_config
from src.backend.features.monsters.dto.generation import GeneratedClan


class FakeRepository:
    def __init__(self) -> None:
        self.created: tuple[GeneratedClan, list] | None = None
        self.by_identity: dict[str, GeneratedClan] = {}

    async def get_clan_by_identity_hash(self, identity_hash: str) -> GeneratedClan | None:
        return self.by_identity.get(identity_hash)

    async def get_clans_by_context_hash(self, context_hash: str) -> list[GeneratedClan]:
        return []

    async def get_clan_members(self, clan_id: uuid.UUID | str) -> list:
        return []

    async def create_clan_with_members(self, clan: GeneratedClan, members: list) -> GeneratedClan:
        self.created = (clan, members)
        clan.members.extend(member for member in members if member not in clan.members)
        for member in clan.members:
            member.clan = clan
        self.by_identity[clan.identity_hash] = clan
        return clan

    async def update_clan_narrative(self, clan: GeneratedClan) -> GeneratedClan:
        return clan


class FakeItemGeneration:
    def __init__(self) -> None:
        self.batches = []

    async def generate_runtime_projections(self, requests):
        self.batches.append(list(requests))
        projections = []
        for index, request in enumerate(requests):
            owner_key = str(request.runtime_metadata["owner_key"])
            projections.append(
                RuntimeItemProjectionDTO(
                    item_id=f"item-{index}",
                    owner_key=owner_key,
                    base_id=request.base_id,
                    item_type="accessory"
                    if request.target_slot == "amulet"
                    else ("weapon" if request.target_slot in {"main_hand", "off_hand", "two_hand"} else "armor"),
                    slot=str(request.target_slot),
                    combat={
                        "power": 3,
                        "implicit_bonuses": {},
                        "bonuses": {"main_hand_accuracy": "+0.01"},
                        "tags": list(request.extra_narrative_tags),
                    },
                    generation={
                        "item_grade": request.item_grade,
                        "rarity_tier": request.rarity_tier,
                        "affixes": [{"affix_id": request.allowed_affix_ids[0]}] if request.allowed_affix_ids else [],
                        "natural_key": request.runtime_metadata.get("natural_key"),
                        "source_context": request.source_context,
                    },
                )
            )
        return projections


def _clan_flavor(name: str = "Test Clan") -> dict[str, object]:
    return {
        "name_ru": name,
        "description": "Authored clan flavor for generation tests.",
        "encounter_texts": {
            "patrol": "Patrol text.",
            "ambush": "Ambush text.",
            "lair": "Lair text.",
            "random_meeting": "Random meeting text.",
        },
    }


@pytest.mark.unit
def test_generation_builder_uses_natural_mapping_item_kind_for_wolf_offhand_and_amulet() -> None:
    family = get_family_config("wolf_pack")
    assert family is not None
    variant = family.variants["pack_leader"]
    builder = MonsterClanGenerationBuilder(repository=FakeRepository(), item_generation=FakeItemGeneration())
    plan = _MemberPlan(
        member_id=uuid.uuid4(),
        owner_key="member-0",
        variant=variant,
        member_model=None,
        member_tier=3,
    )

    item_requests = builder._build_item_requests(family, [plan], "wolf-clan")
    by_slot = {str(request.target_slot): request for request in item_requests}

    assert by_slot["off_hand"].base_id == "buckler"
    assert by_slot["off_hand"].source_context["item_kind"] == "shield"
    assert by_slot["amulet"].base_id == "amulet"
    assert by_slot["amulet"].source_context["item_kind"] == "accessory"


@pytest.mark.unit
def test_d4_context_tags_are_preserved_for_context_metadata() -> None:
    tags = normalize_tags(["d4_rift_rat_king", "rat_swarm", "unknown_noise"])

    assert tags == ["d4_rift_rat_king", "rat_swarm", "unknown_noise"]
    assert compute_context_hash(2, "city_ruins", tags) != compute_context_hash(2, "city_ruins", [])
    assert compute_context_hash(2, "city_ruins", tags) == compute_context_hash(7, "city_ruins", tags)
