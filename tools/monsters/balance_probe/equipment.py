"""Deterministic, legal equipment-only progressions for actual starter imprints.

This analytical tool never changes catalog data or native character progression.
"""

from __future__ import annotations

import random
from copy import deepcopy
from types import SimpleNamespace

from .players import _live_player, _validate_payload

_ARMOR = {
    "light": ("light_hood", "light_chest_armor", "light_bracers", "light_leg_armor"),
    "medium": ("medium_helmet", "medium_chest_armor", "medium_bracers", "medium_leg_armor"),
    "heavy": ("heavy_helmet", "heavy_chest_armor", "heavy_bracers", "heavy_leg_armor"),
}
_ARMOR_SLOTS = ("head_armor", "chest_armor", "arms_armor", "legs_armor")
_ADDITIONS = {
    "feetwear": "boots",
    "gloves_garment": "gloves",
    "belt_accessory": "belt",
    "ring_1": "ring",
    "ring_2": "ring",
    "amulet": "amulet",
    "earring": "earring",
}
_OFFENSE = ["weapon_accuracy", "crit_chance", "armor_penetration_pct_bonus"]
_DEFENSE = ["hp_bonus", "armor_flat"]


def _priorities(slot: str, *, shield: bool, strength: bool) -> list[str]:
    if slot == "off_hand":
        return (
            ["shield_guard_power_bonus", "evasion_bonus"]
            if shield
            else ["off_hand_accuracy", "crit_chance", "armor_penetration_pct_bonus"]
        )
    if slot in {"main_hand", "two_hand"}:
        return _OFFENSE
    if slot.startswith("ring_") or slot in {"amulet", "earring"}:
        attribute = {
            "ring_1": "strength" if strength else "agility",
            "ring_2": "perception",
            "amulet": "endurance",
            "earring": "strength",
        }[slot]
        return [f"attribute_{attribute}", "hp_bonus", "crit_chance", "evasion_bonus", "en_bonus"]
    if slot == "belt_accessory":
        return ["hp_bonus", "en_bonus"]
    if slot in _ARMOR_SLOTS:
        return _DEFENSE + ["evasion_bonus"]
    return ["evasion_bonus"]


def _plan(factory, slot: str, base_id: str, priorities: list[str]) -> dict:
    from src.backend.features.items.resources.affixes.catalog import AFFIX_CATALOG

    base = factory.catalog.get_base_item(base_id)
    tags = factory._build_affix_tags(base)
    kind = factory._affix_item_type(factory._resolve_item_type(base), slot, tags)
    common = set.intersection(*(set(factory._pool_for_item(kind, slot, tags, tier, set())) for tier in range(1, 5)))
    ordered = [key for key in priorities if key in common]
    # Search only for middling quality, never maximum damage. Same roll sequence
    # across material tiers preserves the quality of every retained affix.
    for attempt in range(256):
        seed = f"starter-full-v1:{base_id}:{slot}:{attempt}"
        rng = random.Random(seed)
        qualities = [factory._roll_affix(AFFIX_CATALOG[key], 1.0, rng, item_tier=1)["roll_quality"] for key in ordered]
        if all(0.3 <= quality <= 0.7 for quality in qualities):
            return {"slot": slot, "base_id": base_id, "priority": ordered, "seed": seed}
    raise ValueError(f"No median seed within bounded search for {base_id}/{slot}")


def build_full_players(imprint_ids: tuple[str, ...], tiers: tuple[int, ...]) -> dict[str, dict]:
    """Return saved-player compatible payloads keyed by ``imprint_id.tN``.

    Skills, attributes and symbiote remain exactly native at all equipment tiers.
    Requested affix capacity is 0,1,2,3,4,4; narrower useful pools lower real rarity.
    """
    from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
    from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder
    from src.backend.features.items.dto.instance import ItemGenerationRequestDTO, ItemOriginRefDTO
    from src.backend.features.items.resources.item_grade import AFFIX_CONTAINER_RULES, GRADE_BY_RARITY_TIER
    from src.backend.features.items.runtime.item_factory import ItemFactory

    if not tiers or any(type(tier) is not int or tier not in range(6) for tier in tiers):
        raise ValueError("Equipment suite supports only T0..T5")
    factory = ItemFactory()
    result = {}
    for identity in imprint_ids:
        native = _live_player(identity, SimpleNamespace(mastery=None))
        context = native["input_context"]
        native_items = context["items"]
        bases = {
            slot: native_items["by_id"][item_id]["base_id"]
            for slot, item_id in native_items["layout"]["equipment"].items()
        }
        armor_class = factory.catalog.get_base_item(bases["chest_armor"]).armor_class
        bases.update(dict(zip(_ARMOR_SLOTS, _ARMOR[armor_class], strict=True)))
        bases.update(_ADDITIONS)
        shield = "skill_shield_mastery" in native["skills"]
        strength = "skill_macing" in native["skills"] or shield
        plans = [
            _plan(factory, slot, base_id, _priorities(slot, shield=shield, strength=strength))
            for slot, base_id in bases.items()
        ]
        for tier in tiers:
            items = {"layout": {"equipment": {}}, "by_id": {}}
            review, shortages = [], []
            target = (0, 1, 2, 3, 4, 4)[tier]
            for plan in plans:
                slot, base_id = plan["slot"], plan["base_id"]
                base = factory.catalog.get_base_item(base_id)
                material = factory._resolve_material(base.allowed_materials, None, tier)
                if material.tier != tier:
                    raise ValueError(f"{base_id}: requested material T{tier}, got T{material.tier}")
                count = min(target, len(plan["priority"]))
                rarity = next(
                    grade
                    for grade in range(tier + 1)
                    if int(AFFIX_CONTAINER_RULES[GRADE_BY_RARITY_TIER[grade]]["min"])
                    <= count
                    <= int(AFFIX_CONTAINER_RULES[GRADE_BY_RARITY_TIER[grade]]["max"])
                )
                item = factory.generate_player_item(
                    ItemGenerationRequestDTO(
                        base_id=base_id,
                        target_slot=slot,
                        material_id=material.id,
                        rarity_tier=rarity,
                        affix_count=count,
                        forced_affix_ids=plan["priority"][:count],
                        allowed_affix_ids=plan["priority"] or ["__no_useful_combat_affixes__"],
                        origin_ref=ItemOriginRefDTO(seed=plan["seed"]),
                        request_ai_text=False,
                    )
                )
                item.instance_id = f"starter-full-v1:{identity}:t{tier}:{slot}"
                data = item.model_dump(mode="json")
                data["item_id"] = item.instance_id
                data["mechanics"] = {
                    **item.mechanics,
                    "power": item.power,
                    "bonuses": dict(item.bonuses),
                    "damage_spread": item.damage_spread,
                    "triggers": list(item.triggers),
                    "related_skill": item.metadata.get("related_skill"),
                    "armor_class": base.armor_class,
                }
                items["layout"]["equipment"][slot] = item.instance_id
                items["by_id"][item.instance_id] = data
                review.append(
                    {
                        "slot": slot,
                        "base_id": base_id,
                        "name": item.name,
                        "material_id": material.id,
                        "material_tier": material.tier,
                        "rarity_tier": rarity,
                        "affixes": deepcopy(item.mechanics["affixes"]),
                    }
                )
                if count < target:
                    shortages.append(
                        {
                            "slot": slot,
                            "requested_affixes": target,
                            "actual_affixes": count,
                            "reason": "Useful legal affix pool exhausted; actual rarity lowered.",
                        }
                    )
            new_context = {**deepcopy(context), "items": items}
            skills = deepcopy(native["skills"])
            raw = CharacterCombatMathModelBuilder().build_raw(**new_context, skills=skills)
            loadout = CharacterCombatActorInputBuilder._loadout(items, skills, context["symbiote"])
            key = f"{identity}.t{tier}"
            payload = {
                "name": f"{native['name']} · full T{tier}",
                "raw": raw,
                "skills": skills,
                "loadout": loadout,
                "equipment": items,
                "input_context": new_context,
                "equipment_review": review,
                "source": {"mode": "generated_full_combat_set", "imprint_id": identity, "tier": tier},
                "build_notes": {
                    "affix_count_target": target,
                    "affix_shortages": shortages,
                    "omitted_slots": {"outer_garment": "Weather-only base/pool; no current combat contribution."},
                    "quality": "Bounded middling roll search, quality 0.30..0.70; fixed seed per base and slot.",
                    "progression": "Equipment only; native skills, attributes and symbiote retained, including item-sync effects.",
                },
            }
            result[key] = _validate_payload(payload, name=key)
    return result
