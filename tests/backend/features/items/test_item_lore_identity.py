from types import SimpleNamespace

import pytest

from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO, ItemPlacementRefDTO
from src.backend.features.items.dto.visuals import ItemAppearanceDTO
from src.backend.features.items.integrations.persistence import ItemPersistenceIntegration
from src.backend.features.items.models import ItemInstance, ItemPlacement
from src.backend.features.items.repositories.instance_repository import ItemInstanceRepository
from src.backend.features.items.resources.affixes.catalog import AFFIX_CATALOG
from src.backend.features.items.resources.affixes.narrative import (
    NARRATIVE_TAGS,
    normalize_lore_tags,
    validate_narrative_tags,
)
from src.backend.features.items.runtime.item_factory import ItemFactory
from src.backend.features.items.services.generation_service import ItemGenerationService
from src.backend.features.items.services.text_service import ItemTextService


def make_request(**changes):
    return ItemGenerationRequestDTO(
        base_id="sword",
        material_id="mat_iron_ingot",
        rarity_tier=2,
        forced_affix_ids=["weapon_accuracy", "crit_chance"],
        affix_count=2,
        origin_ref=ItemOriginRefDTO(seed="same-mechanics"),
        **changes,
    )


def test_explicit_material_defines_tier_independently_of_rarity_and_grade():
    item = ItemFactory().generate(make_request().model_copy(update={"rarity_tier": 7, "item_grade": "uncommon"}))
    assert item.item_tier == 1
    assert item.rarity_tier == 7
    assert item.metadata["item_grade"] == "uncommon"
    assert {affix["tier"] for affix in item.mechanics["affixes"]} == {1}
    assert ItemTextService()._build_template_hash_payload(item, make_request())["item_tier"] == 1
    stale_dto = item.model_copy(update={"item_tier": 7})
    assert ItemTextService()._build_template_hash_payload(stale_dto, make_request())["item_tier"] == 1


def test_explicit_material_tier_selects_material_without_rebalancing_grade():
    item = ItemFactory().generate(ItemGenerationRequestDTO(base_id="sword", material_tier=3, rarity_tier=1))
    assert item.item_tier == 3
    assert item.metadata["item_grade"] == "common"
    with pytest.raises(ValueError, match="has tier"):
        ItemFactory().generate(make_request(material_tier=5))


def test_controlled_lore_uses_actual_affix_identities_only_and_has_meanings():
    item = ItemFactory().generate(make_request(extra_narrative_tags=["invented-context"]))
    rolled = item.mechanics["affixes"]
    assert {affix["affix_id"] for affix in rolled} == {"weapon_accuracy", "crit_chance"}
    assert item.lore_tags == ["ferocity", "precision"]
    assert normalize_lore_tags([*rolled, rolled[0]]) == ("ferocity", "precision")
    for entry in AFFIX_CATALOG.values():
        assert validate_narrative_tags(entry.descriptive.narrative_tags)
    payload = ItemTextService()._build_payload(item, make_request())
    assert payload["narrative_meanings"] == {tag: NARRATIVE_TAGS[tag] for tag in item.lore_tags}
    with pytest.raises(ValueError, match="Unknown affix narrative tags"):
        validate_narrative_tags(["unregistered"])
    with pytest.raises(ValueError, match="Unknown rolled affix"):
        normalize_lore_tags([{"affix_id": "unregistered", "value": 1}])


def test_text_cache_ignores_order_rolls_ids_and_context_but_tracks_lore_and_visual():
    request = make_request()
    item = ItemFactory().generate(request)
    service = ItemTextService()
    first = service._build_template_hash_payload(item, request)
    changed_rolls = [
        {**affix, "value": 9999, "roll_quality": 0, "roll": {"step_count": 999}}
        for affix in reversed(item.mechanics["affixes"])
    ]
    changed = item.model_copy(
        update={
            "instance_id": "different-instance",
            "narrative_tags": ["context"],
            "lore_tags": ["wrong-input"],
            "mechanics": {**item.mechanics, "affixes": changed_rolls},
        }
    )
    second = service._build_template_hash_payload(
        changed, request.model_copy(update={"source_context": {"location_id": "elsewhere"}})
    )
    assert first == second
    assert service.build_text_visual_hash(first) == service.build_text_visual_hash(second)
    other_lore = item.model_copy(update={"mechanics": {**item.mechanics, "affixes": [{"affix_id": "hp_bonus"}]}})
    visual = item.model_copy(update={"appearance": ItemAppearanceDTO(visual_variant_id="selected-look")})
    assert service._build_template_hash_payload(other_lore, request) != first
    assert service._build_template_hash_payload(visual, request) != first


class MemorySession:
    def __init__(self):
        self.added = []
        self.executed = []
        self.instance = None
        self.template = None

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        pass

    async def scalar(self, stmt):
        return self.instance

    async def get(self, model, key):
        return self.template

    async def execute(self, stmt):
        self.executed.append(stmt)


@pytest.mark.unit
async def test_instance_persists_selection_and_rereads_ready_lore_without_identifying_or_baseline_duplicates():
    item = ItemFactory().generate(make_request())
    item = item.model_copy(
        update={
            "appearance": ItemAppearanceDTO(
                visual_variant_id="sword_iron_clean",
                visual_set_id="sword",
                width_cells=1,
                height_cells=3,
                volume_units=3,
            )
        }
    )
    session = MemorySession()
    repo = ItemInstanceRepository(session)
    template = await repo.create_text_visual_template(
        item,
        text_visual_hash="shared-hash",
        text_payload={},
        prompt_version="v2",
        text_status="pending",
    )
    assert template.name is None and template.description is None
    instance = await repo.create_mechanical(
        item,
        ItemPlacementRefDTO(holder_type="character", holder_id="42"),
        text_status="pending",
        generated_template_id="shared-template",
    )
    assert isinstance(instance, ItemInstance)
    assert instance.name is None and instance.description is None
    assert instance.is_identified is False
    assert instance.appearance["visual_variant_id"] == "sword_iron_clean"
    assert instance.generation["item_tier"] == 1
    combat_projection = repo._combat_item(
        instance,
        ItemPlacement(
            item_id=instance.id,
            holder_type="character",
            holder_id="42",
            storage_type="equipped",
            slot="main_hand",
        ),
    )
    assert combat_projection["name"]
    assert combat_projection["description"]
    session.instance = instance
    session.template = SimpleNamespace(
        name="Prepared secret", description="Prepared lore", text_status="generated", metadata_={}
    )
    dto = await ItemPersistenceIntegration(repo).get_generated_item(instance.id)
    assert dto.name == "Prepared secret"
    assert dto.appearance == item.appearance
    assert dto.lore_tags == item.lore_tags
    assert dto.item_tier == 1
    assert dto.is_identified is False
    await repo.update_text(instance.id, name="New secret", description="New lore", text_status="generated")
    await repo.update_template_text_for_item(
        instance.id, name="New secret", description="New lore", text_status="generated"
    )
    assert session.template.name == "New secret"
    assert instance.name is None and instance.description is None
    assert instance.is_identified is False
    assert instance.mechanics["affixes"] == item.mechanics["affixes"]


@pytest.mark.unit
async def test_visual_selection_is_before_template_and_uses_separate_randomness():
    from tests.backend.features.items.test_generation_service import FakeTemplatePersistence

    request = make_request()
    expected = ItemFactory().generate(request)
    persistence = FakeTemplatePersistence()
    service = ItemGenerationService(persistence)
    result = await service.generate_mechanical(request)
    assert result.item.mechanics == expected.mechanics
    assert result.item.appearance is not None
    assert result.item.is_identified is False
    payload = persistence.created_items[0]["item"].metadata["text_template_hash_payload"]
    assert payload["visual_variant_id"] == result.item.appearance.visual_variant_id
    persistence.created_templates[0].text_status = "generated"
    persistence.created_templates[0].name = "Ready lore"
    again = await service.generate_mechanical(request)
    assert again.item.name == result.item.name
    assert again.item.name != "Ready lore"
    assert again.item.is_identified is False
    assert again.item.appearance == result.item.appearance


@pytest.mark.unit
async def test_preparing_lore_can_start_after_a_template_was_created_without_ai():
    from tests.backend.features.items.test_generation_service import FakeTemplatePersistence

    persistence = FakeTemplatePersistence()
    service = ItemGenerationService(persistence)
    request = make_request(request_ai_text=False)
    first = await service.generate_mechanical(request)
    second = await service.generate_mechanical(request.model_copy(update={"request_ai_text": True}))
    third = await service.generate_mechanical(request.model_copy(update={"request_ai_text": True}))
    assert first.text_status == "not_requested"
    assert second.text_status == "pending"
    assert second.text_requested_item_ids == second.item_ids
    assert third.text_requested_item_ids == []
    assert len(persistence.created_templates) == 1
    assert first.item.is_identified is second.item.is_identified is False
