"""Immutable authored point budgets and exact senior-rank cores."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator, model_validator


class _ProfileContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MonsterAssemblyBudgetDTO(_ProfileContract):
    mode: Literal["fixed", "relative_gs"] = "fixed"
    reference_gs: Annotated[float, Field(gt=0, allow_inf_nan=False)] | None = None
    base_points: Annotated[StrictInt, Field(ge=0)]
    gs_bonus_max: Annotated[StrictInt, Field(ge=0)] = 0
    gs_threshold: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 35
    gs_step_size: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 5
    gs_points_per_step: Annotated[StrictInt, Field(ge=0)] = 0

    @field_validator("gs_threshold", "gs_step_size", "reference_gs", mode="before")
    @classmethod
    def strict_number(cls, value):
        if value is not None and type(value) not in (int, float):
            raise ValueError("GS threshold and step size must be finite numbers")
        return value

    @model_validator(mode="after")
    def relative_reference_required(self) -> Self:
        if self.mode == "relative_gs" and self.reference_gs is None:
            raise ValueError("relative_gs requires reference_gs")
        return self


class MonsterAssemblyRoleDTO(_ProfileContract):
    role: Literal["minion", "veteran", "elite", "boss"]
    min_count: Annotated[StrictInt, Field(ge=0)] = 0
    max_count: Annotated[StrictInt, Field(ge=1, le=8)]

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.min_count > self.max_count:
            raise ValueError("role minimum exceeds maximum")
        return self


class MonsterPoolBudgetDTO(MonsterAssemblyBudgetDTO):
    player_gs_ratio: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    scaled_points: Annotated[StrictInt, Field(ge=0)]
    gs_steps: Annotated[StrictInt, Field(ge=0)] = 0
    gs_cap_reached: StrictBool = False
    bonus_points: Annotated[StrictInt, Field(ge=0)] = 0
    effective_points: Annotated[StrictInt, Field(ge=0)]
    spent_points: Annotated[StrictInt, Field(ge=0)] = 0
    remaining_points: Annotated[StrictInt, Field(ge=0)] = 0

    @model_validator(mode="after")
    def valid_accounting(self) -> Self:
        if self.mode == "fixed":
            if self.player_gs_ratio is not None or self.scaled_points != self.base_points:
                raise ValueError("fixed pool must retain nominal base")
            if self.bonus_points != min(self.gs_steps * self.gs_points_per_step, self.gs_bonus_max):
                raise ValueError("pool bonus does not match capped steps")
        else:
            if self.player_gs_ratio is None or self.gs_steps != 0:
                raise ValueError("relative pool requires ratio and no stepped bonus")
            if self.scaled_points != min(self.base_points, self.effective_points):
                raise ValueError("relative scaled points are inconsistent")
            if self.bonus_points != max(0, self.effective_points - self.base_points):
                raise ValueError("relative bonus is inconsistent")
            if self.effective_points > self.base_points + self.gs_bonus_max:
                raise ValueError("relative pool exceeds cap")
        if self.effective_points != self.scaled_points + self.bonus_points:
            raise ValueError("pool effective points do not match scaled base and bonus")
        if self.spent_points + self.remaining_points != self.effective_points:
            raise ValueError("pool spending does not match effective points")
        if self.gs_cap_reached != (self.gs_bonus_max > 0 and self.bonus_points == self.gs_bonus_max):
            raise ValueError("pool cap flag does not match bonus")
        return self


class MonsterAssemblyProfileDTO(_ProfileContract):
    id: Annotated[StrictStr, Field(min_length=1, pattern=r"\S")]
    minions: MonsterAssemblyBudgetDTO
    seniors: MonsterAssemblyBudgetDTO
    roles: Annotated[tuple[MonsterAssemblyRoleDTO, ...], Field(min_length=1)]
    allow_repeated_members: StrictBool = True
    min_members: Annotated[StrictInt, Field(ge=2, le=8)] = 2
    max_members: Annotated[StrictInt, Field(ge=2, le=8)] = 8

    @model_validator(mode="after")
    def valid_profile(self) -> Self:
        if self.min_members > self.max_members:
            raise ValueError("minimum members exceeds maximum")
        if len({r.role for r in self.roles}) != len(self.roles):
            raise ValueError("role identifiers must be unique")
        if not any(r.role == "minion" for r in self.roles):
            raise ValueError("profile requires a minion pool role")
        if sum(r.min_count for r in self.roles) > self.max_members:
            raise ValueError("role minima exceed member ceiling")
        return self
