"""Validate buildability without calculating combat, generating or persisting content."""

from src.backend.features.game_catalog.combat.resources.abilities import get_ability_catalog_entry
from src.backend.features.game_catalog.skills.services.catalog_service import SkillCatalogService
from src.backend.features.items.services.catalog_service import ItemCatalogService
from src.backend.features.monsters.catalog.contracts import FamilyDefinition, MemberDefinition
from src.backend.features.monsters.catalog.prepared_equipment import (
    PreparedEquipmentSetDTO,
    get_member_prepared_equipment,
)
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping
from src.backend.features.monsters.catalog.skill_contract import MONSTER_COMBAT_SKILL_KEYS
from src.backend.features.monsters.instances.dto.build_readiness import (
    MonsterBuildIssueCode,
    MonsterBuildIssueDTO,
    MonsterBuildReadinessDTO,
)
from src.backend.features.monsters.instances.runtime.tier_scaling import TIER_SCALING_CONFIG


class MonsterBuildNotReadyError(ValueError):
    def __init__(self, report: MonsterBuildReadinessDTO):
        self.report = report
        reasons = "; ".join(f"{issue.code}: {issue.message}" for issue in report.issues)
        super().__init__(f"Cannot build {report.member_id} at tier {report.tier}: {reasons}")


class MonsterBuildReadinessService:
    """Inspect exact member/tier inputs. Never substitute another clan or tier."""

    def check(
        self,
        *,
        member: MemberDefinition,
        family: FamilyDefinition,
        tier: int,
        prepared: PreparedEquipmentSetDTO | None = None,
    ) -> MonsterBuildReadinessDTO:
        issues: list[MonsterBuildIssueDTO] = []

        def add(code: MonsterBuildIssueCode, path: str, message: str) -> None:
            issues.append(MonsterBuildIssueDTO(code, path, message))

        valid_tier = type(tier) is int and tier in TIER_SCALING_CONFIG
        if not valid_tier:
            add("unsupported_tier", "tier", f"Unsupported instance tier: {tier!r}")
        elif not member.min_tier <= tier <= member.max_tier:
            add("tier_unavailable", "tier", f"Member allows tiers {member.min_tier}..{member.max_tier}")
        if member.family_id != family.id or member.clan_id not in family.clan_ids:
            add("family_mismatch", "member.family_id", "Member/clan does not belong to the supplied family")

        skills = SkillCatalogService()
        for skill_id in member.skills:
            if skills.get(skill_id) is None:
                add("unknown_skill", "member.skills", f"Unknown skill: {skill_id}")
            elif skill_id not in MONSTER_COMBAT_SKILL_KEYS:
                add("unsupported_skill", "member.skills", f"Not a monster combat skill: {skill_id}")
        for ability_id in member.ability_ids:
            if get_ability_catalog_entry(ability_id) is None:
                add("unknown_ability", "member.ability_ids", f"Unknown ability: {ability_id}")

        if prepared is None and valid_tier and member.min_tier <= tier <= member.max_tier:
            try:
                prepared = get_member_prepared_equipment(member=member, tier=tier)
            except (LookupError, ValueError) as error:
                add("equipment_unavailable", "equipment", str(error))
        if prepared is not None:
            expected = {
                "family_id": member.family_id,
                "clan_id": member.clan_id,
                "variant_id": member.variant_id,
                "role": member.role,
                "tier": tier,
            }
            if member.equipment_set_id is not None:
                expected["equipment_set_id"] = member.equipment_set_id
            for field, value in expected.items():
                if getattr(prepared, field) != value:
                    add(
                        "equipment_identity_mismatch",
                        f"equipment.{field}",
                        f"Expected {value!r}, got {getattr(prepared, field)!r}",
                    )
            expected_slots = {slot: base for slot, base in member.fixed_loadout.items() if base}
            actual_slots = [item.slot for item in prepared.items]
            if set(actual_slots) != set(expected_slots) or len(actual_slots) != len(set(actual_slots)):
                add("equipment_slots_mismatch", "equipment.items", "Prepared slots differ from member loadout")
            catalog = ItemCatalogService.load_default()
            for item in prepared.items:
                path = f"equipment.items.{item.slot}"
                expected_base = expected_slots.get(item.slot)
                natural = None
                if expected_base and catalog.get_base_item(expected_base) is None:
                    try:
                        natural = get_natural_equipment_mapping(expected_base)
                    except ValueError:
                        add("unknown_item_base", path, f"Unknown member equipment: {expected_base}")
                if natural is not None:
                    expected_base = natural.base_id
                    if item.generation.natural_key != natural.natural_key:
                        add("equipment_base_mismatch", path, "Natural equipment differs from member loadout")
                if expected_base is not None and item.base_id != expected_base:
                    add("equipment_base_mismatch", path, f"Expected base {expected_base}, got {item.base_id}")
                if catalog.get_base_item(item.base_id) is None:
                    add("unknown_item_base", path, f"Unknown item base: {item.base_id}")
                material_id = item.generation.material_id
                if material_id and catalog.get_material(material_id) is None:
                    add("unknown_material", path, f"Unknown material: {material_id}")
                natural_key = item.generation.natural_key
                if natural_key:
                    try:
                        mapping = get_natural_equipment_mapping(natural_key)
                    except ValueError:
                        add("unknown_natural_equipment", path, f"Unknown natural equipment: {natural_key}")
                    else:
                        if mapping.base_id != item.base_id:
                            add("equipment_base_mismatch", path, "Natural mapping and mechanical item base differ")
                skill_id = item.combat.related_skill
                if skill_id and skills.get(skill_id) is None:
                    add("unknown_skill", f"{path}.related_skill", f"Unknown item skill: {skill_id}")
        return MonsterBuildReadinessDTO(member_id=member.id, tier=tier, issues=tuple(issues))

    def require_ready(
        self,
        *,
        member: MemberDefinition,
        family: FamilyDefinition,
        tier: int,
        prepared: PreparedEquipmentSetDTO | None = None,
    ) -> None:
        report = self.check(member=member, family=family, tier=tier, prepared=prepared)
        if not report.ready:
            raise MonsterBuildNotReadyError(report)
