"""Read-only discovery metadata for contract inspection clients."""

from pydantic import BaseModel, ConfigDict, Field

from src.backend.features.monsters.encounters.profiles.contracts import MonsterAssemblyProfileDTO
from src.backend.features.monsters.encounters.profiles.registry import MINION_REFERENCE_GS


class MonsterContractChoiceDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str


class MonsterPartyModeChoiceDTO(MonsterContractChoiceDTO):
    available: bool


class MonsterEncounterContractDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = 6
    reference_player_gs_by_tier: dict[int, float] = Field(default_factory=lambda: dict(enumerate(MINION_REFERENCE_GS)))
    provisional_reference_tiers: tuple[int, ...] = (6, 7)
    profile_override_example: MonsterAssemblyProfileDTO
    encounter_types: tuple[MonsterContractChoiceDTO, ...]
    difficulties: tuple[MonsterContractChoiceDTO, ...]
    party_modes: tuple[MonsterPartyModeChoiceDTO, ...]
    location_tiers: tuple[int, ...]
    families: tuple[MonsterContractChoiceDTO, ...]
