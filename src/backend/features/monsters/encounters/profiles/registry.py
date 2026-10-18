"""Single lookup boundary: party mode -> encounter type -> difficulty."""

from collections.abc import Mapping
from types import MappingProxyType

from .contracts import MonsterAssemblyProfileDTO
from .resources.solo import profiles

PROFILES: Mapping[str, Mapping[str, Mapping[str, MonsterAssemblyProfileDTO]]] = MappingProxyType(
    {
        "solo": MappingProxyType({key: MappingProxyType(value) for key, value in profiles().items()}),
        "group": MappingProxyType({}),
    }
)


# Explicit provisional experimental-GS references; not calibrated balance.
MINION_REFERENCE_GS = (36.326, 55.977, 66.664, 119.849, 171.053, 312.108, 508.203, 814.358)

GS_TIER_REFERENCES = ((35, 5), (55, 8), (85, 12), (120, 15), (170, 20), (230, 25), (300, 30), (380, 40))


def get_profile(
    party_mode: str, encounter_type: str, difficulty: str, location_tier: int = 0
) -> MonsterAssemblyProfileDTO | None:
    profile = PROFILES.get(party_mode, {}).get(encounter_type, {}).get(difficulty)
    if profile is None:
        return None
    if type(location_tier) is not int or not 0 <= location_tier < len(GS_TIER_REFERENCES):
        raise ValueError("location_tier must be an integer from 0 to 7")
    threshold, step_size = GS_TIER_REFERENCES[location_tier]
    return profile.model_copy(
        update={
            "minions": profile.minions.model_copy(
                update={
                    "mode": "relative_gs",
                    "reference_gs": MINION_REFERENCE_GS[location_tier],
                    "gs_points_per_step": 0,
                }
            ),
            "seniors": profile.seniors.model_copy(update={"gs_threshold": threshold, "gs_step_size": step_size}),
        }
    )
