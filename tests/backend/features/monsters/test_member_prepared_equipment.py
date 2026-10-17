"""Member-aware lookup must never borrow another clan's prepared equipment."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.backend.features.monsters.catalog import get_catalog, prepared_equipment


def _member():
    return get_catalog().members["goblin_tribe.base.goblin_sneak"]


def test_exact_base_member_returns_existing_set():
    member = _member()
    assert prepared_equipment.get_member_prepared_equipment(member=member, tier=2) == (
        prepared_equipment.get_prepared_equipment(family_id=member.family_id, variant_id=member.variant_id, tier=2)
    )


def test_other_clan_cannot_borrow_base_set():
    member = replace(_member(), id="goblin_tribe.ice.goblin_sneak", clan_id="goblin_tribe.ice")
    with pytest.raises(LookupError, match="clan_id"):
        prepared_equipment.get_member_prepared_equipment(member=member, tier=2)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("family_id", "wolf_pack"),
        ("clan_id", "goblin_tribe.other"),
        ("variant_id", "goblin_cutter"),
        ("role", "boss"),
        ("tier", 3),
        ("equipment_set_id", "other_equipment"),
    ],
)
def test_mismatched_loaded_set_is_unavailable(monkeypatch, field, value):
    member = _member()
    saved = prepared_equipment.get_prepared_equipment(
        family_id=member.family_id, variant_id=member.variant_id, tier=2
    ).model_copy(update={field: value})
    monkeypatch.setattr(
        prepared_equipment, "_loader", lambda _: SimpleNamespace(get_prepared_equipment=lambda *_: saved)
    )
    with pytest.raises(LookupError, match=field):
        prepared_equipment.get_member_prepared_equipment(member=member, tier=2)


def test_unsupported_family_fails_without_item_generation(monkeypatch):
    from src.backend.features.items.runtime.item_factory import ItemFactory

    def forbidden(*args, **kwargs):
        pytest.fail("Prepared lookup must never generate items")

    monkeypatch.setattr(ItemFactory, "generate", forbidden, raising=False)
    member = replace(_member(), family_id="unsupported")
    with pytest.raises(LookupError, match="family"):
        prepared_equipment.get_member_prepared_equipment(member=member, tier=2)


@pytest.mark.parametrize("tier", [-1, 8, True, "2"])
def test_invalid_tier_is_rejected_before_loading(monkeypatch, tier):
    monkeypatch.setattr(prepared_equipment, "_loader", lambda _: pytest.fail("Invalid tier was loaded"))
    with pytest.raises(ValueError, match="tier"):
        prepared_equipment.get_member_prepared_equipment(member=_member(), tier=tier)
