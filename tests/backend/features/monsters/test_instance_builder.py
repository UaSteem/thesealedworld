import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backend.features.monsters.catalog.prepared_equipment import get_prepared_equipment
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.inspection.services.equipment_stats_service import MonsterEquipmentStatsService


@pytest.mark.parametrize("family_id", ("goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang"))
def test_extraction_preserves_every_prepared_preview(family_id):
    hashes = json.loads((Path(__file__).parent / "fixtures/instance_extraction_preview_hashes.json").read_text())
    catalog = get_catalog()
    for identity, expected in hashes.items():
        member_id, tier = identity.rsplit(":", 1)
        member = catalog.members[member_id]
        if member.family_id != family_id:
            continue
        preview = MonsterEquipmentStatsService().preview(
            member=member,
            family=catalog.families[family_id],
            prepared=get_prepared_equipment(family_id=family_id, variant_id=member.variant_id, tier=int(tier)),
        )
        encoded = json.dumps(preview.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        assert hashlib.sha256(encoded.encode()).hexdigest() == expected, identity


def test_inspection_uses_instance_builder(monkeypatch):
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    member = get_catalog().members["goblin_tribe.base.goblin_spearman"]
    prepared = get_prepared_equipment(family_id=member.family_id, variant_id=member.variant_id, tier=3)
    family = get_catalog().families[member.family_id]
    original = MonsterInstanceBuilder.build
    calls = []

    def recording(self, **kwargs):
        calls.append(kwargs)
        return original(self, **kwargs)

    monkeypatch.setattr(MonsterInstanceBuilder, "build", recording)
    MonsterEquipmentStatsService().preview(member=member, family=family, prepared=prepared)
    assert len(calls) == 1
    assert calls[0] == {"member": member, "family": family, "prepared": prepared}


@pytest.mark.parametrize(
    "member_id",
    (
        "goblin_tribe.base.goblin_bomber",
        "wolf_pack.base.alpha_prime",
        "rat_swarm.base.rat_king",
        "bandit_gang.base.bandit_thug",
    ),
)
def test_instance_result_matches_studio_and_has_no_shared_mutable_state(member_id, monkeypatch):
    from src.backend.features.items.services.generation_service import ItemGenerationService
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    def forbidden(*args, **kwargs):
        raise AssertionError("Prepared instance cannot generate equipment")

    monkeypatch.setattr(ItemGenerationService, "generate_runtime_projections", forbidden)
    catalog = get_catalog()
    member = catalog.members[member_id]
    family = catalog.families[member.family_id]
    prepared = get_prepared_equipment(family_id=family.id, variant_id=member.variant_id, tier=3)
    before = prepared.model_dump(mode="json")
    kwargs = {"member": member, "family": family, "prepared": prepared}
    builder = MonsterInstanceBuilder()
    built = builder.build(**kwargs)
    expected = deepcopy(built)
    studio = MonsterEquipmentStatsService().preview(**kwargs).technical
    assert built.equipped.raw == studio["equipped_trace"]["raw"]
    assert built.equipped.loadout == studio["equipped_trace"]["loadout"]
    assert built.equipped.values == studio["equipped"]
    assert built.skills == studio["skills"]
    built.equipped.raw["attributes"]["strength"]["base"] = -100
    built.equipped.loadout["known_feints"].clear()
    built.equipped.values["hp"] = -100
    assert builder.build(**kwargs) == expected
    assert prepared.model_dump(mode="json") == before
