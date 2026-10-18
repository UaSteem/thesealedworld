"""Immutable external order and internal composition contracts."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator, model_validator

from src.backend.features.monsters.catalog.contracts import MonsterRole
from src.backend.features.monsters.encounters.profiles.contracts import MonsterAssemblyProfileDTO, MonsterPoolBudgetDTO

Identifier = Annotated[StrictStr, Field(min_length=1, pattern=r"\S")]
Tier = Annotated[StrictInt, Field(ge=0, le=7)]
PositiveCount = Annotated[StrictInt, Field(ge=1)]


class _Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MonsterEncounterOrderDTO(_Contract):
    encounter_type: Identifier
    location_tier: Tier
    family_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=1)]
    seed: StrictInt
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    party_mode: Literal["solo", "group"] = "solo"
    player_gear_score: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None

    profile_override: MonsterAssemblyProfileDTO | None = None

    @field_validator("player_gear_score", mode="before")
    @classmethod
    def strict_score(cls, value):
        if value is not None and type(value) not in (int, float):
            raise ValueError("player_gear_score must be a finite number")
        return value


class MonsterSquadCountDTO(_Contract):
    min_count: PositiveCount
    max_count: PositiveCount

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.min_count > self.max_count:
            raise ValueError("min_count must not exceed max_count")
        return self


class MonsterSquadRoleRuleDTO(_Contract):
    role: MonsterRole
    min_count: Annotated[StrictInt, Field(ge=0)] = 0
    max_count: PositiveCount

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.min_count > self.max_count:
            raise ValueError("role min_count must not exceed max_count")
        return self


class MonsterTierRuleDTO(_Contract):
    role: MonsterRole
    min_tier: Tier
    max_tier: Tier

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.min_tier > self.max_tier:
            raise ValueError("min_tier must not exceed max_tier")
        return self


class MonsterAdmissionPolicyDTO(_Contract):
    location_tier: Tier
    roles: Annotated[tuple[MonsterTierRuleDTO, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_roles(self) -> Self:
        if len({r.role for r in self.roles}) != len(self.roles):
            raise ValueError("admission roles must be unique")
        return self


class MonsterSquadConfigurationDTO(_Contract):
    id: Identifier
    family_id: Identifier
    encounter_type: Identifier
    count: MonsterSquadCountDTO
    roles: Annotated[tuple[MonsterSquadRoleRuleDTO, ...], Field(min_length=1)]
    allow_repeated_members: StrictBool
    same_clan: StrictBool = True
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    party_mode: Literal["solo", "group"] = "solo"

    profile_source: Literal["builtin", "external"] = "builtin"
    profile_id: Identifier
    variant_id: Identifier
    gs_threshold: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 35
    gs_step_size: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 5
    gs_steps: Annotated[StrictInt, Field(ge=0)] = 0
    gs_points_per_step: Annotated[StrictInt, Field(ge=0)] = 0
    gs_bonus_max: Annotated[StrictInt, Field(ge=0)] = 0
    gs_cap_reached: StrictBool = False
    minions: MonsterPoolBudgetDTO
    seniors: MonsterPoolBudgetDTO
    budget_base: Annotated[StrictInt, Field(ge=0)]
    budget_bonus: Annotated[StrictInt, Field(ge=0)] = 0
    budget_effective: Annotated[StrictInt, Field(ge=0)]

    @model_validator(mode="after")
    def constraints(self) -> Self:
        for pool in (self.minions, self.seniors):
            if pool.spent_points != 0 or pool.remaining_points != pool.effective_points:
                raise ValueError("configuration pools must be unspent")
        for aggregate, field in (
            ("budget_base", "base_points"),
            ("budget_bonus", "bonus_points"),
            ("budget_effective", "effective_points"),
        ):
            if getattr(self, aggregate) != sum(getattr(pool, field) for pool in (self.minions, self.seniors)):
                raise ValueError("aggregate budget differs from independent pools")
        if len({r.role for r in self.roles}) != len(self.roles):
            raise ValueError("role rules must be unique")
        if sum(r.min_count for r in self.roles) > self.count.max_count:
            raise ValueError("role minima exceed squad maximum")
        if sum(r.max_count for r in self.roles) < self.count.min_count:
            raise ValueError("role maxima cannot fill squad minimum")
        return self


class MonsterSquadMemberDTO(_Contract):
    member_id: Identifier
    family_id: Identifier
    clan_id: Identifier
    variant_id: Identifier
    role: MonsterRole
    tier: Tier
    name: StrictStr = ""
    assembly_cost: PositiveCount


class MonsterSquadAssemblyInputDTO(_Contract):
    order: MonsterEncounterOrderDTO
    admission: MonsterAdmissionPolicyDTO
    configuration: MonsterSquadConfigurationDTO
    candidates: tuple[MonsterSquadMemberDTO, ...]

    @model_validator(mode="after")
    def validate_context(self) -> Self:
        if self.order.location_tier != self.admission.location_tier:
            raise ValueError("admission differs from order location tier")
        if self.order.encounter_type != self.configuration.encounter_type:
            raise ValueError("configuration differs from order encounter type")
        if (self.order.difficulty, self.order.party_mode) != (
            self.configuration.difficulty,
            self.configuration.party_mode,
        ):
            raise ValueError("configuration differs from order difficulty or party mode")
        if self.order.family_ids and self.configuration.family_id not in self.order.family_ids:
            raise ValueError("configuration family violates order")
        rules = {r.role: r for r in self.admission.roles}
        identities = set()
        for member in self.candidates:
            key = (member.member_id, member.tier)
            if key in identities:
                raise ValueError("duplicate candidate identity and tier")
            identities.add(key)
            rule = rules.get(member.role)
            if rule is None or not rule.min_tier <= member.tier <= rule.max_tier:
                raise ValueError("candidate tier violates admission")
            if self.order.family_ids and member.family_id not in self.order.family_ids:
                raise ValueError("candidate family violates order")
        return self


class MonsterSquadSelectionDTO(_Contract):
    status: Literal["selected"] = "selected"
    assembly_input: MonsterSquadAssemblyInputDTO
    members: tuple[MonsterSquadMemberDTO, ...]

    @model_validator(mode="after")
    def validate_members(self) -> Self:
        config = self.assembly_input.configuration
        if not config.count.min_count <= len(self.members) <= config.count.max_count:
            raise ValueError("selected count is outside configuration")
        if not config.allow_repeated_members and len({m.member_id for m in self.members}) != len(self.members):
            raise ValueError("repeated members are forbidden")
        if config.same_clan and len({m.clan_id for m in self.members}) != 1:
            raise ValueError("selected members must belong to same clan")
        rules = {r.role: r for r in config.roles}
        for member in self.members:
            if member not in self.assembly_input.candidates:
                raise ValueError("selected member is outside ready candidate pool")
            if member.family_id != config.family_id or member.role not in rules:
                raise ValueError("selected member violates configuration")
        for name in ("minions", "seniors"):
            spent = sum(m.assembly_cost for m in self.members if (m.role == "minion") == (name == "minions"))
            if spent > getattr(config, name).effective_points:
                raise ValueError(f"selected squad exceeds {name} point budget")
        if sum(m.assembly_cost for m in self.members) > config.budget_effective:
            raise ValueError("selected squad exceeds point budget")
        for role, rule in rules.items():
            if not rule.min_count <= sum(m.role == role for m in self.members) <= rule.max_count:
                raise ValueError(f"selected count violates role rule: {role}")
        return self


class MonsterSquadRejectionReasonDTO(_Contract):
    code: Identifier
    path: Identifier
    message: Identifier
    member_ids: tuple[Identifier, ...] = ()


class MonsterSquadRejectionDTO(_Contract):
    status: Literal["rejected"] = "rejected"
    assembly_input: MonsterSquadAssemblyInputDTO
    reasons: Annotated[tuple[MonsterSquadRejectionReasonDTO, ...], Field(min_length=1)]


MonsterSquadResultDTO = Annotated[MonsterSquadSelectionDTO | MonsterSquadRejectionDTO, Field(discriminator="status")]
