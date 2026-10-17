"""Shared HTTP presentation contract for item cards in Studio and the library."""

from typing import Any

from pydantic import BaseModel, Field


class ItemCardProperty(BaseModel):
    label: str
    value: str


class ItemCard(BaseModel):
    title: str
    description: str
    material_label: str
    rarity_label: str
    slot_label: str
    power_label: str
    power_value: str
    properties: list[ItemCardProperty] = Field(default_factory=list)
    bonuses: list[ItemCardProperty] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    skill_label: str | None = None
    technical: dict[str, Any] = Field(default_factory=dict)
