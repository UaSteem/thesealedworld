"""Inspectable result of selecting one concrete monster squad."""

from typing import Literal, Self

from pydantic import Field, StrictBool, model_validator

from src.backend.features.monsters.encounters.profiles.contracts import MonsterPoolBudgetDTO

from .preparation import MonsterEncounterPreparationDTO
from .selection import Identifier, MonsterSquadRejectionReasonDTO, MonsterSquadSelectionDTO, _Contract


class MonsterSquadSelectionAttemptDTO(_Contract):
    configuration_id: Identifier
    clan_id: Identifier | None = None
    feasible: StrictBool
    reasons: tuple[MonsterSquadRejectionReasonDTO, ...] = ()

    @model_validator(mode="after")
    def validate_reasons(self) -> Self:
        if self.feasible == bool(self.reasons):
            raise ValueError("feasible attempts have no reasons; infeasible attempts require reasons")
        return self


class MonsterEncounterSelectionDTO(_Contract):
    status: Literal["selected", "rejected"]
    preparation: MonsterEncounterPreparationDTO
    selection: MonsterSquadSelectionDTO | None = None
    reasons: tuple[MonsterSquadRejectionReasonDTO, ...] = ()
    attempts: tuple[MonsterSquadSelectionAttemptDTO, ...] = ()
    selection_strategy: Literal["point_budget"] = "point_budget"
    profile_source: Literal["builtin", "external"] | None = None
    profile_id: str | None = None
    variant_id: str | None = None
    minions: MonsterPoolBudgetDTO | None = None
    seniors: MonsterPoolBudgetDTO | None = None
    budget_base: int | None = Field(default=None, ge=0)
    budget_bonus: int | None = Field(default=None, ge=0)
    budget_effective: int | None = Field(default=None, ge=0)
    budget_spent: int | None = Field(default=None, ge=0)
    budget_remaining: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.status == "selected":
            if self.selection is None or self.preparation.status != "prepared" or self.reasons:
                raise ValueError("selected requires prepared inputs and selection without reasons")
            if self.selection.assembly_input.order != self.preparation.order:
                raise ValueError("selection order differs from preparation")
            context = self.selection.assembly_input
            if context.admission != self.preparation.admission:
                raise ValueError("selection admission differs from preparation")
            if context.configuration not in self.preparation.configurations:
                raise ValueError("selection configuration is outside preparation")
            if any(member not in self.preparation.candidates for member in context.candidates):
                raise ValueError("selection candidate is outside preparation")
            config = context.configuration
            for field in (
                "profile_source",
                "profile_id",
                "variant_id",
                "budget_base",
                "budget_bonus",
                "budget_effective",
            ):
                if getattr(self, field) != getattr(config, field):
                    raise ValueError(f"selection {field} differs from configuration")
            for name in ("minions", "seniors"):
                actual = getattr(self, name)
                expected = getattr(config, name)
                spent_pool = sum(
                    m.assembly_cost for m in self.selection.members if (m.role == "minion") == (name == "minions")
                )
                if (
                    actual is None
                    or actual.model_dump(exclude={"spent_points", "remaining_points"})
                    != expected.model_dump(exclude={"spent_points", "remaining_points"})
                    or actual.spent_points != spent_pool
                    or actual.remaining_points != expected.effective_points - spent_pool
                ):
                    raise ValueError(f"selection {name} accounting is inconsistent")
            spent = sum(member.assembly_cost for member in self.selection.members)
            if self.budget_spent != spent or self.budget_remaining != config.budget_effective - spent:
                raise ValueError("selection budget accounting is inconsistent")
        elif self.selection is not None or not self.reasons:
            raise ValueError("rejected requires reasons and no selection")
        return self
