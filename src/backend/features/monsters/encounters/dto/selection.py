"""Immutable encounter contracts; catalog eligibility and buildability belong to selection services."""

from collections.abc import Mapping
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator, model_validator

from src.backend.features.monsters.catalog.contracts import MonsterRole
from src.backend.features.monsters.catalog.search import MonsterSearchFilters

Identifier = Annotated[StrictStr, Field(min_length=1, pattern=r"\S")]
Tier = Annotated[StrictInt, Field(ge=0, le=7)]
PositiveCount = Annotated[StrictInt, Field(ge=1)]


class _Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


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


class MonsterSquadRequestDTO(_Contract):
    """Role rules are exhaustive. No profile precedence or implicit random seed.

    Catalog existence, tags, system-clan eligibility and instance readiness must
    be checked by the future selector, which has access to the catalog.
    """

    tier: Tier
    count: MonsterSquadCountDTO
    roles: Annotated[tuple[MonsterSquadRoleRuleDTO, ...], Field(min_length=1)]
    filters: MonsterSearchFilters = Field(default_factory=MonsterSearchFilters)
    selection_mode: Literal["random", "specified"] = "random"
    seed: StrictInt | None = None
    specified_members: tuple[Identifier, ...] = ()
    same_clan: StrictBool = True
    allow_repeated_members: StrictBool = False

    @field_validator("filters", mode="before")
    @classmethod
    def validate_filters(cls, value: object) -> MonsterSearchFilters:
        # Reuse the catalog dataclass while enforcing its external input boundary:
        # Pydantic's default dataclass schema otherwise ignores unknown fields.
        if isinstance(value, MonsterSearchFilters):
            return value
        if not isinstance(value, Mapping):
            raise ValueError("filters must be a catalog filter or an object")
        try:
            return MonsterSearchFilters(**dict(value))
        except (TypeError, ValueError) as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def validate_constraints(self) -> Self:
        if len({rule.role for rule in self.roles}) != len(self.roles):
            raise ValueError("role rules must be unique")
        if sum(rule.min_count for rule in self.roles) > self.count.max_count:
            raise ValueError("role minima exceed maximum squad size")
        if sum(rule.max_count for rule in self.roles) < self.count.min_count:
            raise ValueError("role maxima cannot fill minimum squad size")
        if self.selection_mode == "random":
            if self.seed is None or self.specified_members:
                raise ValueError("random selection requires a seed and forbids specified_members")
        else:
            if self.seed is not None or not self.specified_members:
                raise ValueError("specified selection requires member IDs and forbids a seed")
            if not self.count.min_count <= len(self.specified_members) <= self.count.max_count:
                raise ValueError("specified member count is outside requested range")
            if not self.allow_repeated_members and len(set(self.specified_members)) != len(self.specified_members):
                raise ValueError("repeated specified members are forbidden")
        return self


class MonsterSquadMemberDTO(_Contract):
    member_id: Identifier
    family_id: Identifier
    clan_id: Identifier
    variant_id: Identifier
    role: MonsterRole
    tier: Tier


class MonsterSquadSelectionDTO(_Contract):
    status: Literal["selected"] = "selected"
    request: MonsterSquadRequestDTO
    members: tuple[MonsterSquadMemberDTO, ...]

    @model_validator(mode="after")
    def validate_members(self) -> Self:
        request = self.request
        if not request.count.min_count <= len(self.members) <= request.count.max_count:
            raise ValueError("selected count is outside requested range")
        ids = tuple(member.member_id for member in self.members)
        if not request.allow_repeated_members and len(set(ids)) != len(ids):
            raise ValueError("repeated members are forbidden")
        if request.same_clan and len({member.clan_id for member in self.members}) != 1:
            raise ValueError("selected members must belong to the same clan")
        if request.selection_mode == "specified" and ids != request.specified_members:
            raise ValueError("selected order and identities must match specified_members")
        rules = {rule.role: rule for rule in request.roles}
        for member in self.members:
            if member.tier != request.tier:
                raise ValueError("selected tier differs from requested tier")
            if member.role not in rules:
                raise ValueError("selected role is not allowed")
            for category, identity in (
                ("family_ids", member.family_id),
                ("clan_ids", member.clan_id),
                ("member_ids", member.member_id),
            ):
                allowed = getattr(request.filters, category)
                if allowed and identity not in allowed:
                    raise ValueError(f"selected member violates {category}")
        for role, rule in rules.items():
            count = sum(member.role == role for member in self.members)
            if not rule.min_count <= count <= rule.max_count:
                raise ValueError(f"selected count violates role rule: {role}")
        return self


class MonsterSquadRejectionReasonDTO(_Contract):
    code: Literal[
        "no_candidates",
        "tier_unavailable",
        "members_unbuildable",
        "insufficient_distinct_members",
        "role_requirements_unmet",
        "count_requirements_unmet",
        "clan_constraint_unmet",
        "specified_member_unavailable",
        "constraints_unsatisfiable",
    ]
    path: Identifier
    message: Identifier
    member_ids: tuple[Identifier, ...] = ()


class MonsterSquadRejectionDTO(_Contract):
    status: Literal["rejected"] = "rejected"
    request: MonsterSquadRequestDTO
    reasons: Annotated[tuple[MonsterSquadRejectionReasonDTO, ...], Field(min_length=1)]


MonsterSquadResultDTO = Annotated[MonsterSquadSelectionDTO | MonsterSquadRejectionDTO, Field(discriminator="status")]
