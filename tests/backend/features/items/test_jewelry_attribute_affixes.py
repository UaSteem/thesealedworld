import pytest

from src.backend.features.character.runtime import CharacterCombatMathModelBuilder
from src.backend.features.items.dto.instance import ItemGenerationRequestDTO
from src.backend.features.items.resources.affixes.catalog import AFFIX_CATALOG
from src.backend.features.items.resources.affixes.pools import AFFIX_POOLS_BY_ITEM_TYPE, AFFIX_POOLS_BY_SLOT
from src.backend.features.items.resources.presentation_texts import TEXTS
from src.backend.features.items.runtime.item_factory import ItemFactory

ATTRIBUTES = (
    "strength",
    "agility",
    "endurance",
    "perception",
    "intellect",
    "memory",
    "mental",
    "projection",
    "prediction",
)
JEWELRY = (("ring", "ring_1"), ("ring", "ring_2"), ("amulet", "amulet"), ("earring", "earring"))


@pytest.mark.unit
@pytest.mark.parametrize("attribute", ATTRIBUTES)
@pytest.mark.parametrize(("base_id", "slot"), JEWELRY)
def test_jewelry_generates_each_attribute_and_routes_it_to_player_attributes(attribute, base_id, slot):
    factory = ItemFactory()
    item = factory.generate_runtime_item(
        ItemGenerationRequestDTO(
            generation_mode="runtime",
            base_id=base_id,
            target_slot=slot,
            material_id="mat_thorium_ingot",
            item_grade="rare",
            forced_affix_ids=[f"attribute_{attribute}"],
            affix_count=1,
            affix_step_count=5,
        )
    )
    affix = item.mechanics["affixes"][0]
    assert affix["affix_id"] == f"attribute_{attribute}"
    assert 1 <= affix["value"] <= 5
    assert set(item.bonuses) == {attribute}
    # The actual tags used by generation must leave all nine attributes available.
    pool = factory._pool_for_item("accessory", slot, item.narrative_tags, 5, set())
    assert {f"attribute_{key}" for key in ATTRIBUTES} <= set(pool)
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes={key: 10 for key in ATTRIBUTES},
        items={
            "layout": {"equipment": {slot: "jewel"}},
            "by_id": {
                "jewel": {
                    "item_id": "jewel",
                    "item_type": "accessory",
                    "mechanics": {"bonuses": item.bonuses},
                    "tags": item.narrative_tags,
                }
            },
        },
    )
    assert raw["attributes"][attribute]["source"] == {"item:jewel": item.bonuses[attribute]}
    assert attribute not in raw["modifiers"]
    assert TEXTS["ru"]["stats"][attribute]


@pytest.mark.unit
def test_attribute_affixes_remain_jewelry_only_and_keep_existing_scaling():
    ids = {f"attribute_{key}" for key in ATTRIBUTES}
    for item_type, pool in AFFIX_POOLS_BY_ITEM_TYPE.items():
        assert (ids & set(pool)) == (ids if item_type == "accessory" else set())
    for slot, pool in AFFIX_POOLS_BY_SLOT.items():
        assert (ids & set(pool)) == (ids if slot in {jewelry_slot for _, jewelry_slot in JEWELRY} else set())
    for affix_id in ids:
        technical = AFFIX_CATALOG[affix_id].technical
        assert technical.base_value == 0.25
        assert technical.value_kind == "flat_int"
        assert technical.min_item_tier == 1
        assert technical.roll_profile.rounding == "floor_int"


@pytest.mark.unit
@pytest.mark.parametrize(("base_id", "slot"), JEWELRY)
def test_player_jewelry_random_rolls_have_at_most_one_primary_attribute(base_id, slot):
    from src.backend.features.items.dto.instance import ItemOriginRefDTO

    factory = ItemFactory()
    for seed in range(20):
        item = factory.generate_player_item(
            ItemGenerationRequestDTO(
                base_id=base_id,
                target_slot=slot,
                rarity_tier=5,
                origin_ref=ItemOriginRefDTO(seed=f"jewelry-limit:{seed}"),
            )
        )
        affixes = item.mechanics["affixes"]
        assert len(affixes) == 4
        assert {a["affix_id"] for a in affixes} <= set(AFFIX_POOLS_BY_SLOT[slot])
        assert sum(AFFIX_CATALOG[a["affix_id"]].group == "attributes" for a in affixes) <= 1


@pytest.mark.unit
def test_player_rejects_multiple_forced_attributes_but_monster_keeps_them():
    request = ItemGenerationRequestDTO(
        base_id="amulet",
        rarity_tier=5,
        forced_affix_ids=["attribute_agility", "attribute_perception"],
        affix_count=4,
        affix_step_count=9,
    )
    with pytest.raises(ValueError, match="at most one"):
        ItemFactory().generate_player_item(request)
    monster = ItemFactory().generate_runtime_item(request)
    assert {a["affix_id"] for a in monster.mechanics["affixes"]} >= {
        "attribute_agility",
        "attribute_perception",
    }
    assert all(a["roll"]["step_count"] == 9 for a in monster.mechanics["affixes"])


@pytest.mark.unit
def test_player_rejects_forced_bundle_with_multiple_attributes():
    with pytest.raises(ValueError, match="at most one"):
        ItemFactory().generate_player_item(
            ItemGenerationRequestDTO(
                base_id="ring",
                material_id="mat_cobalt_ingot",
                item_grade="legendary",
                affix_bundle_ids=["duelist_accessory_4"],
            )
        )
