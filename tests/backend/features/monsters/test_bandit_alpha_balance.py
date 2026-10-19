import hashlib
import json

import pytest

from src.backend.features.monsters.catalog.contracts import thaw_catalog_value
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


def test_bandit_price_ladder_preserves_other_authored_mechanics():
    members = [m for m in get_catalog().members.values() if m.family_id == "bandit_gang"]
    assert len(members) == 12
    proof = {}
    for m in members:
        assert m.assembly_cost == {
            "bandit_thug": 13,
            "bandit_lookout": 14,
            "bandit_poacher": 15,
            "bandit_knife_rat": 16,
        }.get(m.variant_id, {"veteran": 23, "elite": 30, "boss": 45}.get(m.role))
        proof[m.id] = {
            "role": m.role,
            "mechanics": thaw_catalog_value(m.mechanics),
            "skills": list(m.skills),
            "min_tier": m.min_tier,
            "max_tier": m.max_tier,
            "equipment_set_id": m.equipment_set_id,
        }
    assert (
        hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()
        == "95d4927b6c2590742a93603b0bd27707927e63159c85979a07bd43b8b3cc96c9"
    )


@pytest.mark.parametrize("kind", ("ordinary", "patrol", "guard", "leader"))
@pytest.mark.parametrize("difficulty", ("easy", "normal", "hard"))
def test_bandit_builtin_total_limit_and_affordable_first_tier(kind, difficulty):
    from src.backend.features.monsters.encounters.profiles.registry import MINION_REFERENCE_GS

    order = MonsterEncounterOrderDTO(
        encounter_type=kind,
        difficulty=difficulty,
        location_tier=1,
        family_ids=("bandit_gang",),
        seed=13,
        player_gear_score=MINION_REFERENCE_GS[1],
    )
    resolver = MonsterCompositionPolicyResolver()
    profile = resolver.profile(order)
    assert (profile.min_members, profile.max_members) == (2, 4)
    result = MonsterEncounterSelectionService().select(order)
    assert result.status == "selected"
    assert 2 <= len(result.selection.members) <= 4
    external = profile.model_copy(update={"min_members": 1, "max_members": 8})
    assert resolver.profile(order.model_copy(update={"profile_override": external})) == external


def test_bandits_reject_below_first_family_tier():
    order = MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="easy",
        location_tier=0,
        family_ids=("bandit_gang",),
        seed=13,
        player_gear_score=36,
    )
    assert MonsterEncounterSelectionService().select(order).status == "rejected"
