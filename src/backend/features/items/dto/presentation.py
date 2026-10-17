"""Consumer-independent item cards for inspection and public libraries."""

from typing import Any

from pydantic import BaseModel, Field


class ItemPropertyRowDTO(BaseModel):
    label: str
    value: str


class ItemCardDTO(BaseModel):
    locale: str = "ru"
    title: str
    description: str
    material_label: str
    rarity_label: str
    rarity_color: str
    slot_label: str
    power_label: str
    power_value: str
    properties: list[ItemPropertyRowDTO] = Field(default_factory=list)
    bonuses: list[ItemPropertyRowDTO] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    skill_label: str | None = None
    technical: dict[str, Any]
