"""Monster-owned location admission; exact tiers preserve current numbers."""

from typing import TYPE_CHECKING

from src.backend.features.monsters.encounters.dto.selection import MonsterAdmissionPolicyDTO, MonsterTierRuleDTO

if TYPE_CHECKING:
    from src.backend.features.monsters.catalog.contracts import MonsterRole


class MonsterAdmissionPolicyResolver:
    def resolve(self, location_tier: int) -> MonsterAdmissionPolicyDTO:
        roles: tuple[MonsterRole, ...] = ("minion", "veteran", "elite", "boss")
        return MonsterAdmissionPolicyDTO(
            location_tier=location_tier,
            roles=tuple(
                MonsterTierRuleDTO(role=role, min_tier=location_tier, max_tier=location_tier) for role in roles
            ),
        )
