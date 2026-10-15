from src.backend.features.monsters.catalog.contracts import MonsterFamilyDTO
from src.backend.features.monsters.catalog.families.prepared_rats import (
    PREPARED_RATS_FAMILY,
    RAT_LEGACY_VARIANTS,
    RAT_PRESENTATION,
)
from src.backend.features.monsters.catalog.families.rats import RATS_FAMILY


def test_approved_rat_roster_and_assets():
    family = MonsterFamilyDTO.model_validate(PREPARED_RATS_FAMILY)
    assert len(family.variants) == 12
    assert set(RAT_LEGACY_VARIANTS).issubset(family.variants)
    assert not set(RAT_LEGACY_VARIANTS.values()).intersection(family.variants)
    assert "disease" not in family.default_tags
    for variant_id in family.variants:
        assert RAT_PRESENTATION[variant_id]["image"]["source_path"].endswith(f"/{variant_id}-v2.png")
        assert RAT_PRESENTATION[variant_id]["image"]["review_status"] == "accepted"
        assert not {"disease", "plague", "poison", "blight", "necrosis"}.intersection(family.variants[variant_id].extra_tags)


def test_rat_mechanics_preserved_without_mutating_legacy_family():
    for variant_id, variant in PREPARED_RATS_FAMILY["variants"].items():
        old_id = RAT_LEGACY_VARIANTS.get(variant_id, variant_id)
        for key, value in RATS_FAMILY["variants"][old_id].items():
            if key not in {"id", "narrative_hint", "extra_tags"}:
                assert variant[key] == value
    assert "disease" in RATS_FAMILY["default_tags"]
    assert "plague_rat" in RATS_FAMILY["variants"]
    assert "burrow_guard" not in RATS_FAMILY["variants"]
