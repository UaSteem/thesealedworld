from typing import Any, Literal

from pydantic import BaseModel, Field


class RiftCombatPromptEnemyDTO(BaseModel):
    name: str | None = None
    tier: int | None = None
    member_tier: int | None = None
    threat_rating: int | None = None
    hp_percent: int | None = None
    image: str | None = None
    visual: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    role: str | None = None
    variant_key: str | None = None
    monster_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    intel: dict[str, Any] = Field(default_factory=dict)


class RiftCombatPromptActionDTO(BaseModel):
    id: str
    label: str
    action: Literal["attack"]
    style: Literal["danger"] = "danger"
    is_active: bool = True


class RiftCombatPromptDTO(BaseModel):
    source: Literal["rift_transition"]
    title: str
    description: str
    enemies: list[RiftCombatPromptEnemyDTO] = Field(default_factory=list)
    actions: list[RiftCombatPromptActionDTO] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
