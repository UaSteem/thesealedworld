"""Preparation is an inspectable input pool, never a selected squad."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.backend.features.monsters.encounters.profiles.contracts import MonsterAssemblyProfileDTO
from src.backend.features.monsters.instances.dto.build_readiness import MonsterBuildReadinessDTO

from .selection import (
    Identifier,
    MonsterAdmissionPolicyDTO,
    MonsterEncounterOrderDTO,
    MonsterSquadConfigurationDTO,
    MonsterSquadMemberDTO,
    _Contract,
)


class MonsterPreparationReasonDTO(_Contract):
    stage: Literal["order", "admission", "candidates", "composition"]
    code: Literal[
        "unknown_encounter_type",
        "player_gear_score_required",
        "no_candidates",
        "no_ready_candidates",
        "configuration_unavailable",
        "group_profile_unavailable",
    ]
    path: Identifier
    message: Identifier


class MonsterPreparationStageDTO(_Contract):
    name: Literal["order", "admission", "candidates", "composition"]
    status: Literal["completed", "rejected", "skipped"]
    detail: Identifier


class MonsterEncounterPreparationDTO(_Contract):
    status: Literal["prepared", "rejected"]
    order: MonsterEncounterOrderDTO
    profile: MonsterAssemblyProfileDTO | None = None
    profile_source: Literal["builtin", "external"] = "builtin"
    admission: MonsterAdmissionPolicyDTO | None = None
    configurations: tuple[MonsterSquadConfigurationDTO, ...] = ()
    candidates: tuple[MonsterSquadMemberDTO, ...] = ()
    excluded: tuple[MonsterBuildReadinessDTO, ...] = ()
    reasons: tuple[MonsterPreparationReasonDTO, ...] = ()
    stages: Annotated[tuple[MonsterPreparationStageDTO, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if self.status == "prepared" and (
            self.reasons or self.admission is None or not self.candidates or not self.configurations
        ):
            raise ValueError("prepared requires admission, pool and configurations without rejection reasons")
        if self.status == "rejected" and not self.reasons:
            raise ValueError("rejected requires reasons")
        return self
