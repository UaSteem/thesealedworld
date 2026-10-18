"""Immutable, request-neutral ready candidates and canonical squad variants."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from src.backend.features.monsters.encounters.dto.preparation import (
    MonsterPreparationReasonDTO,
    MonsterPreparationStageDTO,
)
from src.backend.features.monsters.encounters.dto.result import MonsterSquadSelectionAttemptDTO
from src.backend.features.monsters.encounters.dto.selection import MonsterAdmissionPolicyDTO, MonsterSquadMemberDTO
from src.backend.features.monsters.instances.dto.build_readiness import MonsterBuildReadinessDTO

POOL_POLICY_REVISION = "canonical-max-and-previous-v1"


@lru_cache(maxsize=1)
def semantic_revision() -> str:
    """Once per process: covers mechanics, prepared content and policy sources."""
    root = Path(__file__).resolve().parents[5]
    digest = sha256(POOL_POLICY_REVISION.encode())
    for file in sorted(root.rglob("*")):
        if file.is_file() and file.suffix in (".py", ".json"):
            digest.update(str(file.relative_to(root)).encode())
            digest.update(file.read_bytes())
    return digest.hexdigest()


CandidateIndex = Annotated[StrictInt, Field(ge=0)]


class VariantGroupDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    configuration_id: str
    clan_id: str | None = None
    candidates: tuple[CandidateIndex, ...]
    variants: tuple[tuple[CandidateIndex, ...], ...]


class MonsterEncounterVariantPoolDTO(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key_identity: str
    status: Literal["prepared", "rejected"]
    admission: MonsterAdmissionPolicyDTO | None = None
    candidates: tuple[MonsterSquadMemberDTO, ...] = ()
    excluded: tuple[MonsterBuildReadinessDTO, ...] = ()
    reasons: tuple[MonsterPreparationReasonDTO, ...] = ()
    stages: tuple[MonsterPreparationStageDTO, ...]
    attempts: tuple[MonsterSquadSelectionAttemptDTO, ...] = ()
    groups: tuple[VariantGroupDTO, ...] = ()

    @model_validator(mode="after")
    def validate_indices(self):
        for group in self.groups:
            allowed = set(group.candidates)
            if any(i < 0 or i >= len(self.candidates) for i in allowed):
                raise ValueError("variant candidate index outside candidate table")
            if any(not roster or len(roster) > 8 or any(i not in allowed for i in roster) for roster in group.variants):
                raise ValueError("variant reference outside group candidates")
            if len(set(group.variants)) != len(group.variants):
                raise ValueError("duplicate canonical squad variant")
        return self


def canonical_variants(config, pool):
    """Determine feasible sizes with compact count DP; enumerate only largest two."""
    from .squad_selection_service import _pool_rosters

    rules = {rule.role: rule for rule in config.roles}
    by_role = tuple(sorted(pool, key=lambda m: (m.role == "minion", m.member_id, m.tier)))
    senior_rules = tuple(r for r in config.roles if r.role != "minion")
    minion_rules = tuple(r for r in config.roles if r.role == "minion")
    senior_states = _pool_rosters(
        rules=senior_rules,
        pool=tuple(m for m in pool if m.role != "minion"),
        min_count=sum(r.min_count for r in senior_rules),
        max_count=config.count.max_count,
        budget=config.seniors.effective_points,
        allow_repeated_members=config.allow_repeated_members,
    )
    minion_states = _pool_rosters(
        rules=minion_rules,
        pool=tuple(m for m in pool if m.role == "minion"),
        min_count=sum(r.min_count for r in minion_rules),
        max_count=config.count.max_count,
        budget=config.minions.effective_points,
        allow_repeated_members=config.allow_repeated_members,
    )
    sizes = {
        sum(a[0]) + sum(b[0])
        for a in senior_states
        for b in minion_states
        if config.count.min_count <= sum(a[0]) + sum(b[0]) <= config.count.max_count
    }
    if not sizes:
        return ()
    maximum = max(sizes)
    targets = sorted(sizes & {maximum, maximum - 1}, reverse=True)
    found = set()

    def walk(start, roster, counts, min_spent, sen_spent, target, identities):
        remaining = target - len(roster)
        if sum(max(0, rule.min_count - counts.get(role, 0)) for role, rule in rules.items()) > remaining:
            return
        if remaining == 0:
            if all(counts.get(role, 0) >= rule.min_count for role, rule in rules.items()):
                found.add(tuple(sorted((m.member_id, m.tier) for m in roster)))
            return
        if start >= len(by_role):
            return
        for index in range(start, len(by_role)):
            member = by_role[index]
            if counts.get(member.role, 0) >= rules[member.role].max_count:
                continue
            if not config.allow_repeated_members and member.member_id in identities:
                continue
            ms = min_spent + (member.assembly_cost if member.role == "minion" else 0)
            ss = sen_spent + (member.assembly_cost if member.role != "minion" else 0)
            if ms > config.minions.effective_points or ss > config.seniors.effective_points:
                continue
            following = dict(counts)
            following[member.role] = following.get(member.role, 0) + 1
            walk(
                index if config.allow_repeated_members else index + 1,
                (*roster, member),
                following,
                ms,
                ss,
                target,
                identities | {member.member_id},
            )

    for target in targets:
        walk(0, (), {}, 0, 0, target, set())
    return tuple(sorted(found))
