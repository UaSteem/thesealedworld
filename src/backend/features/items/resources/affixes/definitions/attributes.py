from ..schemas import (
    AffixCatalogEntryDTO,
    AffixDescriptiveDTO,
    AffixRollProfileDTO,
    AffixTechnicalDTO,
)

attribute_strength = AffixCatalogEntryDTO(
    id="attribute_strength",
    group="attributes",
    technical=AffixTechnicalDTO(
        # Targets the attributes block, not modifiers — feeds derivation bridge via MODIFIER_RULES.
        modifier_id="strength_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Strength",
        ui_template="+{value} Strength",
        narrative_tags=("ferocity",),
    ),
)

attribute_perception = AffixCatalogEntryDTO(
    id="attribute_perception",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="perception_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Perception",
        ui_template="+{value} Perception",
        narrative_tags=("awareness",),
    ),
)

attribute_agility = AffixCatalogEntryDTO(
    id="attribute_agility",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="agility_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Agility",
        ui_template="+{value} Agility",
        narrative_tags=("agility",),
    ),
)

attribute_endurance = AffixCatalogEntryDTO(
    id="attribute_endurance",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="endurance_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Endurance",
        ui_template="+{value} Endurance",
        narrative_tags=("vitality",),
    ),
)

attribute_intellect = AffixCatalogEntryDTO(
    id="attribute_intellect",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="intellect_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Intellect",
        ui_template="+{value} Intellect",
        narrative_tags=("knowledge",),
    ),
)

attribute_memory = AffixCatalogEntryDTO(
    id="attribute_memory",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="memory_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Memory",
        ui_template="+{value} Memory",
        narrative_tags=("knowledge",),
    ),
)

attribute_mental = AffixCatalogEntryDTO(
    id="attribute_mental",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="mental_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Mental",
        ui_template="+{value} Mental",
        narrative_tags=("resolve",),
    ),
)

attribute_projection = AffixCatalogEntryDTO(
    id="attribute_projection",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="projection_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Projection",
        ui_template="+{value} Projection",
        narrative_tags=("focus",),
    ),
)

attribute_prediction = AffixCatalogEntryDTO(
    id="attribute_prediction",
    group="attributes",
    technical=AffixTechnicalDTO(
        modifier_id="prediction_add",
        base_value=0.25,
        value_kind="flat_int",
        roll_profile=AffixRollProfileDTO(step_spread=0.10, rounding="floor_int", round_digits=0),
        min_item_tier=1,
    ),
    descriptive=AffixDescriptiveDTO(
        display_name="Prediction",
        ui_template="+{value} Prediction",
        narrative_tags=("foresight",),
    ),
)

ATTRIBUTES_AFFIXES = [
    attribute_strength,
    attribute_perception,
    attribute_agility,
    attribute_endurance,
    attribute_intellect,
    attribute_memory,
    attribute_mental,
    attribute_projection,
    attribute_prediction,
]
