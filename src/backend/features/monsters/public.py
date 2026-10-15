"""Transitional public exports for dependency wiring and cross-feature consumers.

This module does not change the existing orchestration or persistence behavior.
"""

from importlib import import_module

_EXPORTS = {
    "CatalogSearchService": ("src.backend.features.monsters.catalog.search", "CatalogSearchService"),
    "MonsterSearchFilters": ("src.backend.features.monsters.catalog.search", "MonsterSearchFilters"),
    "MonsterCatalogBootstrapService": (
        "src.backend.features.monsters.catalog.bootstrap",
        "MonsterCatalogBootstrapService",
    ),
    "get_catalog_member": ("src.backend.features.monsters.catalog.registry", "get_catalog_member"),
    "get_catalog_clan": ("src.backend.features.monsters.catalog.registry", "get_catalog_clan"),
    "get_catalog_family": ("src.backend.features.monsters.catalog.registry", "get_catalog_family"),
    "get_catalog": ("src.backend.features.monsters.catalog.registry", "get_catalog"),
    "MONSTER_ENCOUNTER_PROFILES": (
        "src.backend.features.monsters.encounters.policies.encounter_profiles",
        "MONSTER_ENCOUNTER_PROFILES",
    ),
    "EncounterDifficulty": (
        "src.backend.features.monsters.encounters.policies.encounter_profiles",
        "EncounterDifficulty",
    ),
    "EncounterKind": ("src.backend.features.monsters.encounters.policies.encounter_profiles", "EncounterKind"),
    "MonsterItemAffixKind": (
        "src.backend.features.monsters.catalog.resources.item_affix_profiles",
        "MonsterItemAffixKind",
    ),
    "GROUP_ASSEMBLY_CONFIG": (
        "src.backend.features.monsters.encounters.policies.group_assembler",
        "GROUP_ASSEMBLY_CONFIG",
    ),
    "MonsterEncounterProfile": (
        "src.backend.features.monsters.encounters.policies.encounter_profiles",
        "MonsterEncounterProfile",
    ),
    "AnchorProjectionBootstrapService": (
        "src.backend.features.monsters.catalog.services.anchor_projection_bootstrap",
        "AnchorProjectionBootstrapService",
    ),
    "ClanFactory": ("src.backend.features.monsters.catalog.materialization.clan_factory", "ClanFactory"),
    "ClanPoolPolicyDTO": ("src.backend.features.monsters.dto.generation", "ClanPoolPolicyDTO"),
    "EncounterMonsterService": (
        "src.backend.features.monsters.catalog.services.encounter_monster_service",
        "EncounterMonsterService",
    ),
    "GeneratedClan": ("src.backend.features.monsters.dto.generation", "GeneratedClan"),
    "GeneratedMonster": ("src.backend.features.monsters.dto.generation", "GeneratedMonster"),
    "HabitatClanPoolEntryDTO": ("src.backend.features.monsters.dto.generation", "HabitatClanPoolEntryDTO"),
    "HabitatClanPoolMaterializationResult": (
        "src.backend.features.monsters.encounters.services.habitat_clan_pool_materialization_service",
        "HabitatClanPoolMaterializationResult",
    ),
    "HabitatClanPoolMaterializationService": (
        "src.backend.features.monsters.encounters.services.habitat_clan_pool_materialization_service",
        "HabitatClanPoolMaterializationService",
    ),
    "MonsterActorCommitmentIntegration": (
        "src.backend.features.monsters.instances.integrations.actor_commitments",
        "MonsterActorCommitmentIntegration",
    ),
    "MonsterClanGenerationBuilder": (
        "src.backend.features.monsters.catalog.materialization.generation_builder",
        "MonsterClanGenerationBuilder",
    ),
    "MonsterCombatActorInputBuilder": (
        "src.backend.features.monsters.instances.runtime.combat_actor_input",
        "MonsterCombatActorInputBuilder",
    ),
    "MonsterGearScoreService": (
        "src.backend.features.monsters.instances.services.gear_score_service",
        "MonsterGearScoreService",
    ),
    "MonsterGenerationRepository": (
        "src.backend.features.monsters.catalog.repositories.monster_generation_repository",
        "MonsterGenerationRepository",
    ),
    "MonsterGroupMemberPreview": ("src.backend.features.monsters.dto.generation", "MonsterGroupMemberPreview"),
    "MonsterGroupResult": ("src.backend.features.monsters.dto.generation", "MonsterGroupResult"),
    "MonsterGroupService": (
        "src.backend.features.monsters.encounters.services.monster_group_service",
        "MonsterGroupService",
    ),
    "MonsterHabitatDTO": ("src.backend.features.monsters.dto.generation", "MonsterHabitatDTO"),
    "MonsterIntelProjector": ("src.backend.features.monsters.inspection.intel_projector", "MonsterIntelProjector"),
    "MonsterLocationContextIntegration": (
        "src.backend.features.monsters.encounters.integrations.location_context",
        "MonsterLocationContextIntegration",
    ),
    "build_monster_item_request": (
        "src.backend.features.monsters.instances.integrations.item_generation",
        "build_monster_item_request",
    ),
    "build_scaled_skills": (
        "src.backend.features.monsters.catalog.materialization.generation_fields",
        "build_scaled_skills",
    ),
    "get_all_family_configs": ("src.backend.features.monsters.catalog.registry", "get_all_family_configs"),
    "get_available_variants_for_tier_window": (
        "src.backend.features.monsters.catalog.registry",
        "get_available_variants_for_tier_window",
    ),
    "get_family_config": ("src.backend.features.monsters.catalog.registry", "get_family_config"),
    "get_family_visual": ("src.backend.features.monsters.catalog.resources.visuals", "get_family_visual"),
    "get_natural_equipment_mapping": (
        "src.backend.features.monsters.catalog.resources.equipment_mapping",
        "get_natural_equipment_mapping",
    ),
    "habitat_scope_config_from_population_profile": (
        "src.backend.features.monsters.encounters.services.habitat_clan_pool_materialization_service",
        "habitat_scope_config_from_population_profile",
    ),
    "resolve_monster_ai_archetype": (
        "src.backend.features.monsters.instances.runtime.ai_archetype",
        "resolve_monster_ai_archetype",
    ),
    "to_item_generation_request": (
        "src.backend.features.monsters.instances.integrations.item_generation",
        "to_item_generation_request",
    ),
    "version_generated_asset_url": (
        "src.backend.features.monsters.catalog.resources.visuals",
        "version_generated_asset_url",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    try:
        module, symbol = _EXPORTS[name]
    except KeyError:
        raise AttributeError(name) from None
    return getattr(import_module(module), symbol)
