"""Shared mechanics and family-owned bindings are separate catalog records."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.backend.features.items.dto.instance import RuntimeItemProjectionDTO


class EquipmentItemDefinitionDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    tier: int = Field(ge=0, le=7)
    profile_id: str = Field(min_length=1)
    item: RuntimeItemProjectionDTO

    @model_validator(mode="after")
    def validate_template(self):
        if self.item.item_id != self.id or self.item.owner_key is not None:
            raise ValueError("Shared item needs its catalog ID and no template owner")
        if self.item.generation.rarity_tier != self.tier:
            raise ValueError("Shared item tier differs from its generation tier")
        return self


class EquipmentItemReferenceDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slot: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    name_ru: str | None = None
    description_ru: str | None = None
    natural_key: str | None = None
