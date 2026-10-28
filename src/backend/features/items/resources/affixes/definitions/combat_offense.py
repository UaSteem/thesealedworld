from ..schemas import (
    AffixCatalogEntryDTO,
    AffixDescriptiveDTO,
    AffixRollProfileDTO,
    AffixTechnicalDTO,
)

weapon_accuracy = AffixCatalogEntryDTO(
    id="weapon_accuracy",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="main_hand_accuracy_add",
        base_value=0.003,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.05, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Weapon Accuracy",
        ui_template="+{value}% Accuracy",
        narrative_tags=("precision",),
    ),
)

armor_penetration_pct_bonus = AffixCatalogEntryDTO(
    id="armor_penetration_pct_bonus",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="armor_penetration_pct_add",
        base_value=0.003,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.08, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Armor Penetration %",
        ui_template="+{value}% Armor Penetration",
        narrative_tags=("ferocity",),
    ),
)

crit_chance = AffixCatalogEntryDTO(
    id="crit_chance",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="crit_chance_add",
        base_value=0.002,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.05, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Critical Chance",
        ui_template="+{value}% Crit Chance",
        narrative_tags=("ferocity",),
    ),
)

crit_power = AffixCatalogEntryDTO(
    id="crit_power",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="crit_power_add",
        base_value=0.004,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.08, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Critical Power",
        ui_template="+{value}% Crit Damage",
        narrative_tags=("ferocity",),
    ),
)

off_hand_accuracy = AffixCatalogEntryDTO(
    id="off_hand_accuracy",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="off_hand_accuracy_add",
        base_value=0.0025,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.05, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Off-Hand Accuracy",
        ui_template="+{value}% Off-Hand Accuracy",
        narrative_tags=("precision", "agility"),
    ),
)

vampiric_power_bonus = AffixCatalogEntryDTO(
    id="vampiric_power_bonus",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="vampiric_power_add",
        base_value=0.002,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.06, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Vampiric Power",
        ui_template="+{value}% Vampiric Power",
        narrative_tags=("blood_drain",),
    ),
)

vampiric_trigger_chance_bonus = AffixCatalogEntryDTO(
    id="vampiric_trigger_chance_bonus",
    group="combat_offense",
    technical=AffixTechnicalDTO(
        modifier_id="vampiric_trigger_chance_add",
        base_value=0.002,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.06, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Vampiric Trigger Chance",
        ui_template="+{value}% Vampiric Chance",
        narrative_tags=("blood_drain",),
    ),
)

COMBAT_OFFENSE_AFFIXES = [
    weapon_accuracy,
    armor_penetration_pct_bonus,
    crit_chance,
    crit_power,
    off_hand_accuracy,
    vampiric_power_bonus,
    vampiric_trigger_chance_bonus,
]
