"""Accepted physical gear-score model shared by gameplay and analytical tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
from src.backend.features.character.dto.modifiers import CombatModifiersDTO
from src.backend.features.character.runtime.rules.base_power_assembler import BasePowerAssembler


@dataclass(frozen=True)
class GearScoreConfig:
    # Provisional presentation scales; not calibrated against win rates.
    base_ehp_weight: float = 0.1
    extra_ehp_weight: float = 0.05
    dual_wield_offense_factor: float = 0.8
    base_offense_weight: float = 1.1
    extra_offense_weight: float = 0.55
    support_weight: float = 1.0
    # Provisional reference: monster perception 10 * 0.03; not a catalog average.
    reference_anti_dodge: float = 0.30
    # Provisional target avoidance for valuing suppression, not own accuracy.
    reference_target_evasion: float = 0.30
    reference_target_dodge_cap: float = 0.75
    reference_armor: float = 0.0
    reference_armor_mastery: float = 0.0
    reference_armor_coef: float = 0.027
    incoming_penetration_pct: float = 0.0
    incoming_penetration_flat: float = 0.0
    light_armor_coef: float = 0.014
    medium_armor_coef: float = 0.018
    heavy_armor_coef: float = 0.027
    armor_cap: float = 0.9
    parry_skill_multiplier: float = 4.0
    # Accurate incoming melee attacks per own exchange, not enemy count.
    reference_incoming_melee_opportunities: float = 1.0

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not isfinite(value) or value < 0:
                raise ValueError(f"{key} must be finite and non-negative")
        if self.armor_cap >= 1 or self.incoming_penetration_pct > 1:
            raise ValueError("armor cap must be below one and penetration at most one")
        if self.reference_target_dodge_cap > 1:
            raise ValueError("reference target dodge cap must be at most one")


def _number(value: Any) -> float:
    result = float(value or 0)
    if not isfinite(result):
        raise ValueError("Non-finite combat input")
    return result


def _clamp(value: float, cap: float = 1.0) -> float:
    return max(0.0, min(cap, value))


GEAR_SCORE_VERSION = "physical-v5"


class GearScoreModel:
    def __init__(self, config: GearScoreConfig | None = None) -> None:
        self.config = config or GearScoreConfig()

    def calculate_from_raw(
        self,
        raw: dict[str, Any],
        *,
        skills: dict[str, Any] | None = None,
        loadout: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
        return self.calculate_from_calculated(values, skills=skills, loadout=loadout)

    def calculate_from_calculated(
        self,
        values: dict[str, Any],
        *,
        skills: dict[str, Any] | None = None,
        loadout: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Values must be waterfall output BEFORE BasePowerAssembler projection."""
        c = self.config
        mods = CombatModifiersDTO().model_dump()
        mods.update(values)
        mods = {key: _number(value) for key, value in mods.items()}
        skill = {key: _number(value) for key, value in (skills or {}).items()}
        layout = (loadout or {}).get("layout", {})
        BasePowerAssembler.apply_to_values(mods, loadout_layout=layout, skills=skill)

        def s(key):
            return _clamp(skill.get(key, 0.0))

        armor_type = layout.get("body", "").removeprefix("skill_").removesuffix("_armor")
        if armor_type not in ("light", "medium"):
            armor_type = next((t for t in ("heavy", "medium", "light") if s(f"skill_{t}_armor") > 0), "heavy")
        mastery = s(f"skill_{armor_type}_armor")
        coef = getattr(c, f"{armor_type}_armor_coef")
        gate = 0.35 + 0.65 * mastery
        armor = max(0.0, mods["armor"] * (1 - c.incoming_penetration_pct) - c.incoming_penetration_flat)

        def reduction(power):
            return _clamp(1 - 1 / (1 + max(0.0, power) * gate * coef), c.armor_cap)

        armor_pct = reduction(armor)
        hp = max(0.0, mods["hp"])
        base_ehp = hp / (1 - armor_pct)
        shield = layout.get("off_hand") == "skill_shield_mastery"
        dodge = 0.0 if shield else _clamp(mods["evasion"] - c.reference_anti_dodge, mods["dodge_cap"])
        parry = _clamp(
            mods["parry"] * (1 + c.parry_skill_multiplier * skill.get("skill_parrying", 0)), mods["parry_cap"]
        )
        shield_mastery = s("skill_shield_mastery")
        shield_gate = 0.35 + 0.65 * shield_mastery
        block = 0.0
        blocked_pct = armor_pct
        if shield:
            block = _clamp(
                mods["shield_guard_power"] * 0.015 * (1 + max(0, mods["evasion"])) * shield_gate,
                0.45 + 0.30 * shield_mastery,
            )
            guard = (
                (mods["shield_guard_power"] + mods["physical_endurance_power"])
                * 0.35
                * shield_gate
                * max(0.35, 1 - max(0, mods["evasion"]) * 0.45)
            )
            blocked_pct = reduction(
                max(0, (mods["armor"] + guard) * (1 - c.incoming_penetration_pct) - c.incoming_penetration_flat)
            )
        # Parry/dodge cancel; block continues into armor with extra shield power.
        passed = (1 - dodge) * (1 - parry) * ((1 - block) * (1 - armor_pct) + block * (1 - blocked_pct))
        # Linear scoring proxies, not an additional survivable HP pool.
        block_fraction = _clamp((blocked_pct - armor_pct) / (1 - armor_pct))
        defense_parts = {
            "dodge": base_ehp * dodge,
            "parry": base_ehp * (1 - dodge) * parry,
            "block": base_ehp * (1 - dodge) * (1 - parry) * block * block_fraction,
        }
        extra_ehp = sum(defense_parts.values())
        hand_details = {}
        base_offense = extra_offense = 0.0
        hands = ["main_hand"]
        if (
            layout.get("tactical_style") == "skill_dual_wield"
            and layout.get("off_hand")
            and layout.get("off_hand") != "skill_shield_mastery"
        ):
            hands.append("off_hand")  # Guaranteed exchange follow-up, not a proc.
        dual_factor = c.dual_wield_offense_factor if len(hands) == 2 else 1.0
        for hand in hands:
            weapon = layout.get(hand, "")
            mastery_weapon = s(weapon)
            style = s(layout.get("tactical_style", ""))
            penalty = max(0, mods[f"{hand}_accuracy_penalty"]) * max(0.1, 1 - 0.45 * mastery_weapon - 0.45 * style)
            accuracy = _clamp(
                0.60 + 0.40 * mastery_weapon + mods[f"{hand}_accuracy"] + mods["accuracy"] - penalty,
                _clamp(0.90 + mods["accuracy_cap"]),
            )
            damage = max(0, mods[f"{hand}_damage_base"] + mods["physical_damage_bonus"])
            damage *= max(0, 1 - mods[f"{hand}_damage_spread"] / 2) * max(0, mods["damage_mult"])
            pen = max(0, mods[f"{hand}_armor_penetration_pct"] + mods["armor_penetration_pct"])
            target_power = max(0, c.reference_armor * max(0, 1 - pen) - mods["armor_penetration_flat"])
            target_pct = _clamp(
                1 - 1 / (1 + target_power * (0.35 + 0.65 * c.reference_armor_mastery) * c.reference_armor_coef),
                c.armor_cap,
            )
            ignore = _clamp(mods[f"{hand}_armor_ignore_chance"] + mods["armor_ignore_chance"])
            raw_expected = damage * accuracy * (1 - target_pct * (1 - ignore))
            expected = raw_expected * dual_factor
            crit = _clamp(
                (mods[f"{hand}_crit_chance"] + mods["crit_chance"]) * (1 + skill.get(weapon, 0)),
                mods[f"{hand}_crit_cap"],
            )
            crit_mult = 2.0 if layout.get(f"{hand}_trigger", "").split(".")[-1] == "weapon_heavy_crit" else 1.0
            if layout.get("tactical_style_trigger", "").split(".")[-1] == "style_dual_cross_cut":
                crit_mult *= 1 + 0.25 * ((1.5 + 1.5 * s("skill_dual_wield")) - 1)
            bonus = expected * crit * max(0, crit_mult - 1)
            base_offense += expected
            extra_offense += bonus
            hand_details[hand] = {
                "accuracy": accuracy,
                "mean_damage_on_hit": damage,
                "crit_chance": crit,
                "expected_crit_multiplier": crit_mult,
                "base_expected_damage_before_style_discount": raw_expected,
                "style_offense_factor": dual_factor,
                "base_expected_damage": expected,
                "extra_expected_damage": bonus,
            }
        # First-order passive reactions to the reference attack stream. Defense
        # branches are sequential; blocked contacts occur only after no parry.
        ranged = (
            layout.get("tactical_style") == "skill_ranged_combat"
            or layout.get("main_hand") == "skill_archery"
            or layout.get("off_hand") == "skill_archery"
        )
        counter_base = _clamp(min(mods["counter_attack_chance"], mods["counter_attack_cap"]))
        dodge_counter = parry_counter = shield_counter = 0.0
        if not ranged:
            if armor_type == "light":
                dodge_counter = dodge * (0.5 * counter_base + 0.5 * _clamp(counter_base * (1 + mastery)))
            if armor_type == "medium":
                parry_counter = (1 - dodge) * parry * mastery * counter_base
            if shield:
                shield_counter = (1 - parry) * block * _clamp(mods["counter_attack_chance"] * shield_gate, 0.5)
        opportunities = c.reference_incoming_melee_opportunities
        # Counter origin uses main hand; dual context then schedules its usual
        # offhand. Reuse the ordinary strike pair without recursively reacting.
        counter_damage = base_offense + extra_offense
        main_pen = max(0, mods["main_hand_armor_penetration_pct"] + mods["armor_penetration_pct"])
        shield_target_power = max(0, c.reference_armor * max(0, 1 - main_pen) - mods["armor_penetration_flat"])
        shield_target_reduction = _clamp(
            1 - 1 / (1 + shield_target_power * (0.35 + 0.65 * c.reference_armor_mastery) * c.reference_armor_coef),
            c.armor_cap,
        )
        # The instant shield response has no accuracy/spread/crit roll.
        shield_damage = max(0, mods["main_hand_damage_base"]) * 0.5 * shield_gate * (1 - shield_target_reduction)
        passive_counter_damage = opportunities * (
            (dodge_counter + parry_counter) * counter_damage + shield_counter * shield_damage
        )
        crit_bonus = extra_offense
        extra_offense += passive_counter_damage
        counter_details = {
            "incoming_melee_opportunities": opportunities,
            "counter_chance_given_window": counter_base,
            "dodge_counter_probability": dodge_counter,
            "parry_counter_probability": parry_counter,
            "shield_counter_probability": shield_counter,
            "counter_sequence_expected_damage": counter_damage,
            "shield_counter_damage": shield_damage,
            "extra_expected_damage": passive_counter_damage,
        }
        # Value suppression separately from own hit accuracy. Subtract before
        # capping: raw evasion above the target cap can absorb suppression.
        # Use ordinary strikes only, excluding crit/counter compounding.
        target_dodge = _clamp(c.reference_target_evasion, c.reference_target_dodge_cap)
        remaining_dodge = _clamp(
            c.reference_target_evasion - max(0.0, mods["anti_dodge_chance"]), c.reference_target_dodge_cap
        )
        suppressed_dodge = target_dodge - remaining_dodge
        anti_dodge_bonus = base_offense * suppressed_dodge
        extra_offense += anti_dodge_bonus
        anti_dodge_details = {
            "anti_dodge_chance": mods["anti_dodge_chance"],
            "reference_target_evasion": c.reference_target_evasion,
            "reference_target_dodge_cap": c.reference_target_dodge_cap,
            "target_dodge_chance": target_dodge,
            "remaining_dodge_chance": remaining_dodge,
            "suppressed_dodge_probability": suppressed_dodge,
            "extra_expected_damage": anti_dodge_bonus,
        }
        support = sum(max(0, mods[key]) for key in ("combat_hp_regen", "combat_en_regen", "combat_stamina_regen"))
        amounts = dict(
            base_ehp=base_ehp,
            extra_ehp=max(0, extra_ehp),
            base_offense=base_offense,
            extra_offense=extra_offense,
            support=support,
        )
        components = {
            key: {"value": value, "weight": getattr(c, f"{key}_weight"), "score": value * getattr(c, f"{key}_weight")}
            for key, value in amounts.items()
        }
        components["extra_ehp"]["parts"] = {
            name: {"value": value, "weight": c.extra_ehp_weight, "score": value * c.extra_ehp_weight}
            for name, value in defense_parts.items()
        }
        components["extra_offense"]["parts"] = {
            name: {"value": value, "weight": c.extra_offense_weight, "score": value * c.extra_offense_weight}
            for name, value in {
                "crit": crit_bonus,
                "counter": passive_counter_damage,
                "anti_dodge": anti_dodge_bonus,
            }.items()
        }
        components["extra_offense"]["passive_counters"] = counter_details
        components["extra_offense"]["anti_dodge"] = anti_dodge_details
        return {
            "version": GEAR_SCORE_VERSION,
            "total": round(sum(part["score"] for part in components.values()), 3),
            "components": components,
            "effective": {
                "dual_wield_offense_factor": dual_factor,
                "hp": hp,
                "armor_type": armor_type,
                "armor_reduction": armor_pct,
                "dodge_chance": dodge,
                "parry_chance": parry,
                "block_chance": block,
                "blocked_armor_reduction": blocked_pct,
                "damage_pass_fraction": passed,
                "hands": hand_details,
            },
            "assumptions": asdict(c),
            "limitations": [
                "Physical melee reference only; not an enemy-independent strength estimate.",
                "extra_ehp is a linear prevention scoring proxy based on armored EHP, not reciprocal expected EHP. Nested parts are included once in their aggregate.",
                "Defense conditional on an accurate incoming hit; no attacker miss credit. Reference target has no parry/block.",
                "Base offense retains own accuracy without target dodge discount; anti-dodge receives a separate linear suppression proxy on ordinary strikes, weighted once as extra offense. No crit/counter compounding.",
                "No live tunable overrides, integer damage rounding or minimum-one damage floor.",
                "Unmodeled magic, unarmed efficiency, ranged positioning, proc extra attacks, DOT/control, feints, resource exhaustion and arbitrary item triggers.",
                "Passive counters use explicit accurate incoming melee opportunities; first response plus deterministic dual offhand only. Recursive reactions, deaths before followup and shield-opening benefit are excluded.",
                "Only heavy-crit and dual-cross-cut crit amplification modeled; no separate skill score.",
                "Support is the uncalibrated sum of per-round resource regeneration; no healing double count.",
                "Weights are the accepted physical GS model; unmodeled effects receive no score.",
            ],
        }
