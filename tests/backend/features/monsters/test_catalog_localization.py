from dataclasses import replace

from src.backend.features.monsters.catalog.bootstrap import MonsterCatalogBootstrapService
from src.backend.features.monsters.catalog.families.wolf_catalog.family import WOLF_FAMILY
from src.backend.features.monsters.catalog.nested_contracts import resolve_family
from src.backend.features.monsters.catalog.texts import MonsterTextDTO, resolve_text


def test_locale_fallback_and_new_language_are_data_only():
    resources = {"test": {"ru": MonsterTextDTO("Имя", "Описание"), "de": MonsterTextDTO("Name", "Beschreibung")}}
    assert resolve_text("test", "de-DE", resources=resources).locale == "de"
    fallback = resolve_text("test", "fr", resources=resources)
    assert fallback.locale == "ru" and fallback.fallback


def test_default_art_and_variant_override():
    clan = WOLF_FAMILY.clans[0]
    ordinary = clan.members[0]
    basis = WOLF_FAMILY.bases[0]
    assert ordinary.image is None and basis.default_image is not None
    _, _, inherited = resolve_family(WOLF_FAMILY)
    assert inherited[0].image == basis.default_image
    assert inherited[0].image_source == "default_base"
    art = replace(basis.default_image, asset_id="test.override")
    alternate = replace(ordinary, image=art)
    _, _, overridden = resolve_family(replace(WOLF_FAMILY, clans=(replace(clan, members=(alternate,)),)))
    assert overridden[0].image == art
    assert overridden[0].image_source == "variant_override"


def test_bootstrap_has_locale_metadata_and_localized_hash():
    service = MonsterCatalogBootstrapService()
    ru = service.build(locale="ru")
    de = service.build(locale="de")
    assert ru.locale == "ru" and de.locale == "de"
    assert ru.version != de.version
    assert all(m.description and m.name for m in ru.members.values())
    assert all(m.image_source == "default_base" and m.base_id for m in ru.members.values())


def test_missing_ru_and_unknown_resources_fail_explicitly():
    import pytest

    with pytest.raises(ValueError, match="Missing default"):
        resolve_text("test", "en", resources={"test": {"en": MonsterTextDTO("Name", "Description")}})
    with pytest.raises(ValueError, match="Unknown monster text"):
        resolve_text("missing", resources={})


def test_real_bootstrap_selects_added_language_without_code_change(monkeypatch):
    from src.backend.features.monsters.catalog.resources import texts

    resources = dict(texts.MONSTER_TEXTS)
    resources["wolf.member.cub"] = {
        **resources["wolf.member.cub"],
        "de": MonsterTextDTO("Wolfsjunges", "Ein junger Wolf."),
    }
    monkeypatch.setattr(texts, "MONSTER_TEXTS", resources)
    result = MonsterCatalogBootstrapService().build(locale="de-DE")
    assert result.members["wolf_pack.base.cub"].name == "Wolfsjunges"
    assert result.members["wolf_pack.base.cub"].text_locale == "de"
    assert result.members["wolf_pack.base.runner"].text_locale == "ru"
    assert result.members["wolf_pack.base.runner"].text_fallback
    assert result.available_locales == ["de", "ru"]


def test_all_numeric_mechanics_and_asset_ids_preserved():
    import json
    from pathlib import Path

    from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
    from src.backend.features.monsters.catalog.registry import get_catalog

    baseline = json.loads(Path(__file__).with_name("catalog_mechanics_baseline.json").read_text(encoding="utf8"))
    for member in get_catalog().members.values():
        assert {
            key: value for key, value in thaw_catalog_value(member.mechanics).items() if key != "narrative_hint"
        } == baseline[member.id]["mechanics"]
        assert (member.image.asset_id if member.image else None) == baseline[member.id]["image"]
