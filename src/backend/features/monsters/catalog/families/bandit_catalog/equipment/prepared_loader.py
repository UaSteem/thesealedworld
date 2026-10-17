"""Read prepared Python equipment definitions, without generation or persistence."""

from copy import deepcopy
from importlib import import_module

from src.backend.features.monsters.catalog.prepared_equipment import PreparedEquipmentSetDTO

_PACKAGE = "src.backend.features.monsters.catalog.families.bandit_catalog.equipment.prepared"


def list_prepared_equipment() -> tuple[tuple[str, int], ...]:
    try:
        index = import_module(f"{_PACKAGE}.index").DATA
    except ModuleNotFoundError as error:
        if error.name in {_PACKAGE, f"{_PACKAGE}.index"}:
            raise LookupError("Prepared bandit_gang equipment is not built") from error
        raise
    result = []
    for reference in index:
        variant_id, tier_name = reference.split(".")
        result.append((variant_id, int(tier_name.removeprefix("tier_"))))
    return tuple(result)


def get_prepared_equipment(variant_id: str, tier: int) -> PreparedEquipmentSetDTO:
    if not isinstance(variant_id, str) or not variant_id.isidentifier() or type(tier) is not int:
        raise ValueError("Expected a variant ID and integer tier")
    if (variant_id, tier) not in list_prepared_equipment():
        raise LookupError(f"No prepared bandit_gang equipment: {variant_id}, tier {tier}")
    payload = import_module(f"{_PACKAGE}.{variant_id}.tier_{tier}").DATA
    result = PreparedEquipmentSetDTO.model_validate(deepcopy(payload))
    if result.family_id != "bandit_gang" or result.variant_id != variant_id or result.tier != tier:
        raise ValueError("Prepared equipment identity differs from its module")
    return result
