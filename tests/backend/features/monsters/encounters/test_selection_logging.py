import pytest
from loguru import logger

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


@pytest.fixture
def records():
    captured = []
    sink = logger.add(lambda message: captured.append(message.record))
    yield captured
    logger.remove(sink)


@pytest.mark.parametrize("mode,status", [("solo", "selected"), ("group", "rejected")])
def test_order_and_result_logs_are_correlated_without_changing_selection(records, mode, status):
    order = MonsterEncounterOrderDTO(
        encounter_type="ordinary", location_tier=0, family_ids=("goblin_tribe",), seed=13, player_gear_score=36.326, party_mode=mode
    )
    result = MonsterEncounterSelectionService().select(order)
    events = [record for record in records if record["message"].startswith("MonsterEncounterSelection")]
    assert [record["message"] for record in events] == [
        "MonsterEncounterSelectionRequested",
        "MonsterEncounterSelectionCompleted",
    ]
    requested, completed = [record["extra"] for record in events]
    assert requested["selection_id"] == completed["selection_id"]
    assert requested["seed"] == completed["seed"] == 13
    assert requested["party_mode"] == mode
    assert completed["status"] == status
    assert completed["duration_ms"] >= 0
    assert completed["completed_at"] >= requested["requested_at"]
    assert completed["members"] == (
        [member.model_dump(mode="json", exclude={"name"}) for member in result.selection.members]
        if result.selection
        else []
    )
    assert completed["reason_codes"] == [reason.code for reason in result.reasons]


def test_unexpected_failure_is_logged_and_propagated(records):
    class BrokenPreparation:
        def prepare(self, order):
            raise RuntimeError("broken dependency")

    with pytest.raises(RuntimeError, match="broken dependency"):
        MonsterEncounterSelectionService(preparation=BrokenPreparation()).select(
            MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=0, seed=13, family_ids=("goblin_tribe",), player_gear_score=36.326)
        )
    events = [record for record in records if record["message"].startswith("MonsterEncounterSelection")]
    assert [record["message"] for record in events] == [
        "MonsterEncounterSelectionRequested",
        "MonsterEncounterSelectionFailed",
    ]
    assert events[-1]["exception"] is not None
    assert events[-1]["extra"]["selection_id"] == events[0]["extra"]["selection_id"]
