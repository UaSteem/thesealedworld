from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


def order(seed=1, gs=36.326):
    return MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="easy",
        location_tier=0,
        family_ids=("goblin_tribe",),
        seed=seed,
        player_gear_score=gs,
    )


def test_pool_builds_all_identity_variants_and_rebinds_current_order():
    service = MonsterEncounterSelectionService()
    pool = service.build_pool(order())
    assert len(pool.groups[0].variants) > 4
    assert len(set(pool.groups[0].variants)) == len(pool.groups[0].variants)
    assert {len(v) for v in pool.groups[0].variants} == {3, 4}
    changed = order(seed=19, gs=36.4)
    assert service.cache_identity(order()) == service.cache_identity(changed)
    result = service.select_from_pool(changed, pool)
    assert result.preparation.order == changed
    assert result.selection.assembly_input.order == changed
    assert result.minions.player_gs_ratio != service.select_from_pool(order(), pool).minions.player_gs_ratio


def test_enumerator_retains_every_multiset_at_largest_two_sizes():
    from itertools import combinations_with_replacement

    from src.backend.features.monsters.encounters.services.variant_pool import canonical_variants

    service = MonsterEncounterSelectionService()
    result = service.select(order())
    config = result.selection.assembly_input.configuration
    base = result.preparation.candidates[0]
    candidates = tuple(
        base.model_copy(update={"member_id": name, "role": "minion", "assembly_cost": 1}) for name in ("a", "b")
    )
    config = config.model_copy(
        update={
            "count": config.count.model_copy(update={"min_count": 2, "max_count": 3}),
            "minions": config.minions.model_copy(update={"effective_points": 3}),
        }
    )
    actual = canonical_variants(config, candidates)
    expected = {
        tuple((name, 0) for name in names)
        for size in (2, 3)
        for names in combinations_with_replacement(("a", "b"), size)
    }
    assert set(actual) == expected


def test_pool_json_roundtrip_has_no_request_specific_seed_or_gs_and_no_readiness_on_hit(monkeypatch):
    from src.backend.features.monsters.encounters.services.variant_pool import MonsterEncounterVariantPoolDTO

    service = MonsterEncounterSelectionService()
    pool = service.build_pool(order())
    encoded = pool.model_dump_json()
    assert "player_gear_score" not in encoded and "player_gs_ratio" not in encoded and '"seed"' not in encoded
    decoded = MonsterEncounterVariantPoolDTO.model_validate_json(encoded)
    monkeypatch.setattr(
        service._preparation, "prepare", lambda *_: (_ for _ in ()).throw(AssertionError("cache hit must not prepare"))
    )
    assert service.select_from_pool(order(99, 36.4), decoded).preparation.order.seed == 99


def test_cache_key_excludes_seed_and_raw_gs_but_not_effective_budgets():
    service = MonsterEncounterSelectionService()
    assert service.cache_identity(order(1, 36.326)) == service.cache_identity(order(999, 36.4))
    assert service.cache_identity(order(1, 36.326)) != service.cache_identity(order(1, 50))


def test_cached_typed_rejection_rebinds_order():
    service = MonsterEncounterSelectionService()
    first = order().model_copy(update={"player_gear_score": None})
    artifact = service.build_pool(first)
    later = first.model_copy(update={"seed": 123})
    result = service.select_from_pool(later, artifact)
    assert result.status == "rejected" and result.reasons[0].code == "player_gear_score_required"
    assert result.preparation.order == later


def test_policy_revision_invalidates_cache_identity(monkeypatch):
    from src.backend.features.monsters.encounters.services import variant_pool

    service = MonsterEncounterSelectionService()
    first = service.cache_identity(order())
    monkeypatch.setattr(variant_pool, "semantic_revision", lambda: "changed-authored-mechanics")
    assert service.cache_identity(order()) != first


def test_pool_deserialization_rejects_invalid_candidate_references():
    import pytest
    from pydantic import ValidationError

    from src.backend.features.monsters.encounters.services.variant_pool import MonsterEncounterVariantPoolDTO

    pool = MonsterEncounterSelectionService().build_pool(order()).model_dump(mode="json")
    pool["groups"][0]["variants"][0][0] = 99999
    with pytest.raises(ValidationError):
        MonsterEncounterVariantPoolDTO.model_validate(pool)


def test_builtin_goblin_overall_minimum_is_three_and_external_override_remains_authoritative():
    from src.backend.features.monsters.encounters.profiles.registry import get_profile

    service = MonsterEncounterSelectionService()
    initial = order(gs=28.357)
    pool = service.build_pool(initial)
    assert {len(v) for group in pool.groups for v in group.variants} == {3}
    for seed in range(100):
        assert len(service.select_from_pool(initial.model_copy(update={"seed": seed}), pool).selection.members) == 3
    external = initial.model_copy(update={"profile_override": get_profile("solo", "ordinary", "easy")})
    external_pool = service.build_pool(external)
    assert {len(v) for group in external_pool.groups for v in group.variants} == {2, 3}
    assert service.cache_identity(initial) != service.cache_identity(external)
