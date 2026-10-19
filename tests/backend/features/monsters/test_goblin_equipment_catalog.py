"""Shared family equipment preserves the complete existing goblin mechanics."""

import json
from dataclasses import replace

import pytest

from src.backend.features.monsters.catalog.equipment_contracts import (
    EquipmentEntryDTO,
    EquipmentSetDTO,
    FamilyEquipmentDTO,
)
from src.backend.features.monsters.catalog.families.goblin_catalog.family import GOBLIN_FAMILY
from src.backend.features.monsters.catalog.nested_contracts import resolve_family
from tests.backend.features.monsters.test_nested_starter_catalogs import normalize

BEFORE = json.loads(
    '{"goblin_sneak": {"mechanics": {"id": "goblin_sneak", "role": "minion", "narrative_hint": "Щуплый гоблин прячется за чужими спинами и выбирает момент для внезапного выпада.", "spawn_weight": 20, "extra_tags": ["stealth", "assassin", "dual_wield", "knife"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 11, "agility": 14, "endurance": 12, "intellect": 10, "memory": 7, "mental": 8, "perception": 13, "projection": 6, "prediction": 9}, "fixed_loadout": {"main_hand": "knife", "off_hand": "knife", "two_hand": null, "head_armor": null, "chest_armor": "leather_armor", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_fencing", "skill_dual_wield", "skill_light_armor"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_sneak", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sneak-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_scavenger": {"mechanics": {"id": "goblin_scavenger", "role": "minion", "narrative_hint": "Зоркий гоблин тащит полезный хлам и никогда не проходит мимо брошенного оружия.", "spawn_weight": 20, "extra_tags": ["scavenger", "hoarder", "scrap", "buckler"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 12, "agility": 14, "endurance": 13, "intellect": 10, "memory": 7, "mental": 8, "perception": 11, "projection": 6, "prediction": 9}, "fixed_loadout": {"main_hand": "mace", "off_hand": "buckler", "two_hand": null, "head_armor": null, "chest_armor": "leather_armor", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_macing", "skill_shield_mastery", "skill_light_armor"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_scavenger", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_scavenger-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_cutter": {"mechanics": {"id": "goblin_cutter", "role": "minion", "narrative_hint": "Задиристый боец с потрёпанным клинком охотно ввязывается в близкую схватку.", "spawn_weight": 20, "extra_tags": ["knife", "bleeder", "ambusher", "dual_wield"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 11, "agility": 14, "endurance": 13, "intellect": 10, "memory": 7, "mental": 9, "perception": 12, "projection": 6, "prediction": 8}, "fixed_loadout": {"main_hand": "dagger", "off_hand": "knife", "two_hand": null, "head_armor": null, "chest_armor": "leather_armor", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_fencing", "skill_dual_wield", "skill_light_armor"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_cutter", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_cutter-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_sparkpick": {"mechanics": {"id": "goblin_sparkpick", "role": "minion", "narrative_hint": "Любознательный гоблин возится с необычными инструментами и мерцающими находками.", "spawn_weight": 20, "extra_tags": ["scrap", "ether", "reckless", "buckler"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 12, "agility": 14, "endurance": 13, "intellect": 11, "memory": 8, "mental": 9, "perception": 10, "projection": 7, "prediction": 6}, "fixed_loadout": {"main_hand": "hatchet", "off_hand": "buckler", "two_hand": null, "head_armor": null, "chest_armor": "leather_armor", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_macing", "skill_shield_mastery", "skill_light_armor"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_sparkpick", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_sparkpick-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_spearman": {"mechanics": {"id": "goblin_spearman", "role": "veteran", "narrative_hint": "Длинное копьё помогает небольшому гоблину держать противника подальше от себя.", "spawn_weight": 50, "extra_tags": ["infantry", "shield"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 13, "agility": 14, "endurance": 15, "intellect": 11, "memory": 9, "mental": 10, "perception": 12, "projection": 8, "prediction": 7}, "fixed_loadout": {"main_hand": "spear", "off_hand": "shield", "two_hand": null, "head_armor": null, "chest_armor": "jerkin", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_polearms", "skill_medium_armor", "skill_shield_mastery"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_spearman", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_spearman-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_slinger": {"mechanics": {"id": "goblin_slinger", "role": "veteran", "narrative_hint": "Подвижный стрелок перебирает запас снарядов и высматривает удобную цель.", "spawn_weight": 50, "extra_tags": ["ranged", "archer", "fast", "quiver"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 12, "agility": 15, "endurance": 13, "intellect": 11, "memory": 10, "mental": 9, "perception": 14, "projection": 7, "prediction": 8}, "fixed_loadout": {"main_hand": null, "off_hand": null, "two_hand": "shortbow", "head_armor": null, "chest_armor": "leather_armor", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": "quiver_training"}, "skills": ["skill_archery", "skill_ranged_combat", "skill_light_armor"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_slinger", "source_path": "assets/monster_defaults/goblin_tribe/svg/goblin_slinger.svg", "review_status": "accepted", "display_mirror": false}}, "goblin_scrapguard": {"mechanics": {"id": "goblin_scrapguard", "role": "veteran", "narrative_hint": "Пластины собранной защиты прикрывают гоблина, привыкшего стоять впереди остальных.", "spawn_weight": 50, "extra_tags": ["shield", "defender", "scrap"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 14, "agility": 13, "endurance": 15, "intellect": 10, "memory": 9, "mental": 11, "perception": 12, "projection": 8, "prediction": 7}, "fixed_loadout": {"main_hand": "mace", "off_hand": "shield", "two_hand": null, "head_armor": null, "chest_armor": "jerkin", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_macing", "skill_medium_armor", "skill_shield_mastery"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_scrapguard", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_scrapguard-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_tinkerer": {"mechanics": {"id": "goblin_tinkerer", "role": "elite", "narrative_hint": "Опытный умелец чинит снаряжение и испытывает устройства сомнительной надёжности.", "spawn_weight": 150, "extra_tags": ["engineer", "duelist", "scrap", "buckler"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 11, "agility": 15, "endurance": 13, "intellect": 16, "memory": 12, "mental": 10, "perception": 14, "projection": 9, "prediction": 8}, "fixed_loadout": {"main_hand": "rapier", "off_hand": "buckler", "two_hand": null, "head_armor": null, "chest_armor": "jerkin", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_fencing", "skill_shield_mastery", "skill_medium_armor", "skill_tactics"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_tinkerer", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_tinkerer-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_bomber": {"mechanics": {"id": "goblin_bomber", "role": "elite", "narrative_hint": "Гоблин бережно несёт опасные самоделки и слишком радуется каждому взрыву.", "spawn_weight": 150, "extra_tags": ["bomber", "explosives", "reckless", "archer", "fire_arrows"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 12, "agility": 16, "endurance": 15, "intellect": 14, "memory": 9, "mental": 11, "perception": 13, "projection": 8, "prediction": 10}, "fixed_loadout": {"main_hand": null, "off_hand": null, "two_hand": "shortbow", "head_armor": null, "chest_armor": "jerkin", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": "quiver_fire"}, "skills": ["skill_archery", "skill_medium_armor", "skill_ranged_combat", "skill_tactics"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_bomber", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_bomber-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_trapmaster": {"mechanics": {"id": "goblin_trapmaster", "role": "elite", "narrative_hint": "Хитрый мастер предпочитает заранее подготовленный путь прямой схватке.", "spawn_weight": 150, "extra_tags": ["trapper", "engineer", "controller", "dual_wield", "precision"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 11, "agility": 14, "endurance": 13, "intellect": 16, "memory": 12, "mental": 10, "perception": 15, "projection": 8, "prediction": 9}, "fixed_loadout": {"main_hand": "stiletto", "off_hand": "main_gauche", "two_hand": null, "head_armor": null, "chest_armor": "jerkin", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_fencing", "skill_dual_wield", "skill_medium_armor", "skill_tactics", "skill_anatomy"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_trapmaster", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_trapmaster-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "goblin_chief": {"mechanics": {"id": "goblin_chief", "role": "boss", "narrative_hint": "Матёрый предводитель выделяется добротным оружием и привычкой распоряжаться другими.", "spawn_weight": 600, "extra_tags": ["leader", "commander", "heavy_armor", "shield"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 21, "agility": 20, "endurance": 22, "intellect": 16, "memory": 15, "mental": 19, "perception": 18, "projection": 17, "prediction": 14}, "fixed_loadout": {"main_hand": "battle_axe", "off_hand": "kite_shield", "two_hand": null, "head_armor": null, "chest_armor": "plate_chest", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_macing", "skill_shield_mastery", "skill_heavy_armor", "skill_tactics", "skill_anatomy"], "member_model": null}, "image": {"asset_id": "goblin_tribe.goblin_chief", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/goblin_chief-face-v1.png", "review_status": "accepted", "display_mirror": false}}, "scrap_king": {"mechanics": {"id": "scrap_king", "role": "boss", "narrative_hint": "Тяжело вооружённый главарь выходит вперёд сам, демонстрируя клану трофейную защиту и оружие.", "spawn_weight": 600, "extra_tags": ["king", "heavy_armor", "engineer", "two_handed", "scrap"], "min_tier": 0, "max_tier": 5, "base_stats": {"strength": 21, "agility": 15, "endurance": 22, "intellect": 20, "memory": 17, "mental": 19, "perception": 16, "projection": 18, "prediction": 14}, "fixed_loadout": {"main_hand": null, "off_hand": null, "two_hand": "warhammer", "head_armor": null, "chest_armor": "plate_chest", "arms_armor": null, "legs_armor": null, "feetwear": null, "chest_garment": null, "legs_garment": null, "outer_garment": null, "gloves_garment": null, "amulet": "amulet", "ring_1": null, "ring_2": null, "belt_accessory": null, "quiver": null}, "skills": ["skill_macing", "skill_heavy_armor", "skill_two_handed", "skill_tactics", "skill_anatomy"], "member_model": null}, "image": {"asset_id": "goblin_tribe.scrap_king", "source_path": "assets/monster_defaults/goblin_tribe/face_repair_candidates/scrap_king-standing-v1.png", "review_status": "accepted", "display_mirror": false}}}'
)


def test_all_twelve_goblins_preserve_mechanics_and_art():
    members = resolve_family(GOBLIN_FAMILY)[2]
    assert len(members) == 12
    for member in members:
        from tests.backend.features.monsters.catalog.alpha_expectations import approved_mechanics

        historical = BEFORE[member.variant_id]
        expected = {**historical, "mechanics": approved_mechanics("goblin_tribe", member.variant_id, historical["mechanics"])}
        assert {"mechanics": normalize(member.mechanics), "image": normalize(member.image)} == expected
        assert member.equipment_set_id
        assert member.equipment_source == "base_set"
    assert all(b.loadout is None and b.equipment_set_id for b in GOBLIN_FAMILY.bases)


def test_family_equipment_shares_item_references_without_merging_distinct_sets():
    equipment = GOBLIN_FAMILY.equipment
    assert len({entry.base_id for entry in equipment.entries}) == len(equipment.entries)
    assert len(equipment.entries) == 20
    assert len(equipment.sets) == 12


def test_clan_override_changes_only_selected_basis_equipment():
    basis = GOBLIN_FAMILY.bases[0]
    other = next(b for b in GOBLIN_FAMILY.bases if b.equipment_set_id != basis.equipment_set_id)
    clan = replace(GOBLIN_FAMILY.clans[0], equipment_overrides={basis.id: other.equipment_set_id})
    result = resolve_family(replace(GOBLIN_FAMILY, clans=(clan,)))[2]
    target = next(m for m in result if m.base_id == basis.id)
    donor = next(m for m in result if m.base_id == other.id)
    assert target.mechanics["fixed_loadout"] == donor.mechanics["fixed_loadout"]
    assert target.base_stats == basis.stats.model_dump()
    assert target.equipment_source == "clan_override"
    assert all(m.equipment_source == "base_set" for m in result if m.base_id != basis.id)


@pytest.mark.parametrize("overrides", ({"missing": "missing"}, {"goblin_sneak": "missing"}))
def test_unknown_override_rejected(overrides):
    with pytest.raises(ValueError):
        replace(GOBLIN_FAMILY, clans=(replace(GOBLIN_FAMILY.clans[0], equipment_overrides=overrides),))


def test_invalid_item_set_and_slot_rejected():
    with pytest.raises(ValueError, match="item"):
        FamilyEquipmentDTO(entries=(EquipmentEntryDTO("bad", "missing_item"),), sets=())
    with pytest.raises(ValueError, match="entry"):
        FamilyEquipmentDTO(entries=(), sets=(EquipmentSetDTO("bad", {"main_hand": "missing"}),))
    with pytest.raises(ValueError, match="slot"):
        FamilyEquipmentDTO(
            entries=(EquipmentEntryDTO("knife", "knife"),), sets=(EquipmentSetDTO("bad", {"chest_armor": "knife"}),)
        )
    with pytest.raises(ValueError, match="set"):
        replace(GOBLIN_FAMILY, bases=(replace(GOBLIN_FAMILY.bases[0], equipment_set_id="missing"),))


def test_equipment_definitions_are_immutable():
    equipment = GOBLIN_FAMILY.equipment
    with pytest.raises(TypeError):
        equipment.sets[0].slots["main_hand"] = "dagger"
    with pytest.raises(TypeError):
        GOBLIN_FAMILY.clans[0].equipment_overrides["goblin_sneak"] = "sneak"


def test_basis_requires_exactly_one_equipment_source():
    basis = GOBLIN_FAMILY.bases[0]
    from src.backend.features.monsters.catalog.nested_contracts import BaseLoadoutDTO

    with pytest.raises(ValueError, match="exactly one"):
        replace(basis, equipment_set_id=None)
    with pytest.raises(ValueError, match="exactly one"):
        replace(basis, loadout=BaseLoadoutDTO(main_hand="knife"))


def test_same_set_can_be_shared_by_several_bases():
    basis, second, *others = GOBLIN_FAMILY.bases
    shared = replace(second, equipment_set_id=basis.equipment_set_id)
    members = resolve_family(replace(GOBLIN_FAMILY, bases=(basis, shared, *others)))[2]
    selected = [m for m in members if m.base_id in (basis.id, second.id)]
    assert selected[0].equipment_set_id == selected[1].equipment_set_id
    assert selected[0].mechanics["fixed_loadout"] == selected[1].mechanics["fixed_loadout"]
