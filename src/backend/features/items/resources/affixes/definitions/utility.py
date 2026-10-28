from ..schemas import (
    AffixCatalogEntryDTO,
    AffixDescriptiveDTO,
    AffixRollProfileDTO,
    AffixTechnicalDTO,
)

luck_bonus = AffixCatalogEntryDTO(
    id="luck_bonus",
    group="utility",
    technical=AffixTechnicalDTO(
        # Future world field — not yet wired to a combat modifier.
        modifier_id="luck_add",
        base_value=0.0025,
        value_kind="probability",
        roll_profile=AffixRollProfileDTO(step_spread=0.08, rounding="decimal", round_digits=4),
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Luck",
        ui_template="+{value}% Luck",
        narrative_tags=("fortune",),
    ),
)

UTILITY_AFFIXES = [
    luck_bonus,
]
