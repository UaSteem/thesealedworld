import pytest
from pydantic import TypeAdapter, ValidationError

from src.backend.features.monsters.encounters.dto.selection import (
    MonsterSquadRequestDTO,
    MonsterSquadResultDTO,
    MonsterSquadSelectionDTO,
)


def request(**changes):
    return dict(
        tier=0,
        count=dict(min_count=3, max_count=3),
        roles=[dict(role="minion", min_count=3, max_count=3)],
        seed=17,
        **changes,
    )


def member(identity="a", **changes):
    return (
        dict(
            member_id=identity, family_id="goblins", clan_id="goblins.base", variant_id=identity, role="minion", tier=0
        )
        | changes
    )


def test_watch_and_patrol_roundtrip():
    for rules in (
        [dict(role="minion", min_count=3, max_count=3)],
        [dict(role="minion", min_count=2, max_count=2), dict(role="veteran", min_count=1, max_count=1)],
    ):
        data = request()
        data["roles"] = rules
        dto = MonsterSquadRequestDTO.model_validate(data)
        assert MonsterSquadRequestDTO.model_validate_json(dto.model_dump_json()) == dto


@pytest.mark.parametrize(
    "changes",
    [
        dict(tier=True),
        dict(tier=8),
        dict(seed=None),
        dict(unknown=1),
        dict(filters=dict(unknown=1)),
        dict(filters=dict(member_ids=[2])),
        dict(filters=dict(include_system=1)),
        dict(specified_members=["a"]),
        dict(count=dict(min_count=4, max_count=3)),
        dict(same_clan=1),
    ],
)
def test_invalid_request(changes):
    with pytest.raises(ValidationError):
        MonsterSquadRequestDTO.model_validate(request() | changes)


def test_result_invariants_and_discrimination():
    req = MonsterSquadRequestDTO.model_validate(request())
    members = [member("a"), member("b"), member("c")]
    dto = MonsterSquadSelectionDTO(request=req, members=members)
    assert TypeAdapter(MonsterSquadResultDTO).validate_json(dto.model_dump_json()) == dto
    for invalid in (
        [member("a")] * 3,
        members[:2],
        members[:2] + [member("c", tier=1)],
        members[:2] + [member("c", role="boss")],
        members[:2] + [member("c", clan_id="other")],
    ):
        with pytest.raises(ValidationError):
            MonsterSquadSelectionDTO(request=req, members=invalid)
    with pytest.raises(ValidationError):
        TypeAdapter(MonsterSquadResultDTO).validate_python(dict(status="rejected", request=req, reasons=[]))


@pytest.mark.parametrize(
    "changes",
    [
        dict(selection_mode="specified", seed=None, specified_members=["a", "b"]),
        dict(selection_mode="specified", seed=None, specified_members=["a", "a", "b"]),
        dict(selection_mode="specified", seed=None, specified_members=["a", "b", 3]),
        dict(selection_mode="specified", seed=None, specified_members=["a", "b", "  "]),
        dict(roles=[dict(role="minion", max_count=3), dict(role="minion", max_count=3)]),
        dict(roles=[dict(role="minion", min_count=4, max_count=4)]),
        dict(roles=[dict(role="minion", max_count=2)]),
        dict(roles=[dict(role="minion", max_count=True)]),
        dict(filters=dict(required_tags=["x"], excluded_tags=["x"])),
    ],
)
def test_invalid_explicit_and_role_constraints(changes):
    with pytest.raises(ValidationError):
        MonsterSquadRequestDTO.model_validate(request() | changes)


def test_specified_order_and_id_filters():
    req = MonsterSquadRequestDTO.model_validate(
        request()
        | dict(
            selection_mode="specified",
            seed=None,
            specified_members=["a", "b", "c"],
            filters=dict(family_ids=["goblins"], clan_ids=["goblins.base"], member_ids=["a", "b", "c"]),
        )
    )
    members = [member("a"), member("b"), member("c")]
    MonsterSquadSelectionDTO(request=req, members=members)
    for invalid in (members[::-1], members[:2] + [member("c", family_id="other")]):
        with pytest.raises(ValidationError):
            MonsterSquadSelectionDTO(request=req, members=invalid)


def test_detached_frozen_nested_inputs():
    data = request()
    data["filters"] = dict(member_ids=["a"])
    dto = MonsterSquadRequestDTO.model_validate(data)
    data["roles"][0]["max_count"] = 9
    data["filters"]["member_ids"].append("b")
    assert dto.roles[0].max_count == 3
    assert dto.filters.member_ids == ("a",)
    with pytest.raises(ValidationError):
        dto.roles[0].max_count = 9


def test_rejection_roundtrip_and_no_partial_members():
    adapter = TypeAdapter(MonsterSquadResultDTO)
    data = dict(
        status="rejected",
        request=request(),
        reasons=[
            dict(code="members_unbuildable", path="members.a", message="Equipment is unavailable", member_ids=["a"])
        ],
    )
    dto = adapter.validate_python(data)
    assert adapter.validate_json(adapter.dump_json(dto)) == dto
    for changes in (
        dict(members=[]),
        dict(reasons=[dict(code="unknown", path="x", message="x")]),
        dict(reasons=[dict(code="no_candidates", path=" ", message="x")]),
    ):
        with pytest.raises(ValidationError):
            adapter.validate_python(data | changes)
