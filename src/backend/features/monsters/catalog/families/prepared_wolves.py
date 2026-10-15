"""Approved ordinary wolf roster; original legacy resource remains intact."""

from copy import deepcopy

from src.backend.features.monsters.catalog.families.wolves import WOLVES_FAMILY

PREPARED_WOLVES_FAMILY = deepcopy(WOLVES_FAMILY)
variants = PREPARED_WOLVES_FAMILY["variants"]
# Retain the existing boss stat profile until the separate balance pass.
huntmaster = variants.pop("winter_maw")
variants.pop("blood_howl")
huntmaster.update(
    id="pack_huntmaster",
    narrative_hint="A cunning wolf pack huntmaster who coordinates pursuit and cuts off escaping prey.",
    extra_tags=["cunning", "coordinator", "hunter"],
)
fenrir = variants.pop("alpha_prime")
variants["pack_huntmaster"] = huntmaster
variants["alpha_prime"] = fenrir
PREPARED_WOLVES_FAMILY["hierarchy"]["boss"] = ["pack_huntmaster", "alpha_prime"]
