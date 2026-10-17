"""Reasons why authored content cannot produce a requested instance."""

from dataclasses import dataclass
from typing import Literal

MonsterBuildIssueCode = Literal[
    "unsupported_tier",
    "tier_unavailable",
    "family_mismatch",
    "unknown_skill",
    "unsupported_skill",
    "unknown_ability",
    "equipment_unavailable",
    "equipment_identity_mismatch",
    "equipment_slots_mismatch",
    "equipment_base_mismatch",
    "unknown_item_base",
    "unknown_material",
    "unknown_natural_equipment",
]


@dataclass(frozen=True, slots=True)
class MonsterBuildIssueDTO:
    code: MonsterBuildIssueCode
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class MonsterBuildReadinessDTO:
    member_id: str
    tier: int
    issues: tuple[MonsterBuildIssueDTO, ...]

    @property
    def ready(self) -> bool:
        return not self.issues
