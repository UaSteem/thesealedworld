import pytest

from src.backend.features.items.services.presentation_service import ItemPresentationService
from src.backend.features.monsters.catalog.families.goblin_catalog.equipment.prepared_loader import (
    get_prepared_equipment,
    list_prepared_equipment,
)


@pytest.fixture
def presentation():
    return ItemPresentationService()


def test_all_prepared_items_have_readable_cards_without_mutation(presentation):
    count = 0
    for variant, tier in list_prepared_equipment():
        for item in get_prepared_equipment(variant, tier).items:
            before = item.model_dump(mode="json")
            card = presentation.present(item)
            assert card.title != "Неизвестный предмет"
            assert card.material_label != "Материал не указан"
            assert card.rarity_label != "Редкость не определена"
            assert card.skill_label != "Неизвестный навык"
            assert all(row.label != "Неизвестное свойство" for row in card.properties + card.bonuses)
            assert all("Неизвестный эффект" not in effect for effect in card.effects)
            assert card.technical == before == item.model_dump(mode="json")
            assert len(card.bonuses) == len(item.combat.bonuses)  # Affixes aren't duplicated.
            count += 1
    assert count == 282


@pytest.mark.parametrize(
    ("key", "command", "expected"),
    [
        ("main_hand_accuracy", "+0.0333", "+3,33%"),
        ("armor", "+3.5", "+3,5"),
        ("evasion", "*1.2", "×1,2"),
        ("evasion", "=0.2", "=20%"),
        ("evasion", "-0.05", "−5%"),
        ("strength", "+2", "+2"),
        ("new_future_stat", "+0.05", "+0,05"),
    ],
)
def test_command_operations_and_declared_units(presentation, key, command, expected):
    row = presentation._row(key, command)
    assert row.value == expected


def test_unknown_data_remains_inspectable_without_id_leaks(presentation):
    item = get_prepared_equipment("goblin_sneak", 3).items[0].model_copy(deep=True)
    item.base_id = "secret_unknown_base"
    item.combat.bonuses = {"secret_unknown_stat": "+1"}
    item.combat.triggers = ["secret_unknown_trigger"]
    item.combat.related_skill = "secret_unknown_skill"
    card = presentation.present(item, locale="de")
    assert card.locale == "ru"
    assert card.bonuses[0].label == "Неизвестное свойство"
    assert "secret_unknown" not in str(card.model_dump(exclude={"technical"}))
    assert card.technical["base_id"] == "secret_unknown_base"


def test_effect_and_skill_texts_are_catalog_descriptions(presentation):
    item = next(item for item in get_prepared_equipment("goblin_sneak", 3).items if item.base_id == "knife")
    card = presentation.present(item)
    assert card.title == "Нож"
    assert card.skill_label == presentation.skills.get("skill_fencing").name_ru
    assert any("Щель в броне" in effect for effect in card.effects)
