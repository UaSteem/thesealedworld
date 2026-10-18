"""Document examples stay parseable against the actual public contract."""

import json
from pathlib import Path

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO


def test_documented_order_examples():
    data = json.loads(Path("docs/ru/backend/features/monsters/squad_contract_examples.json").read_text(encoding="utf-8"))
    assert data
    for order in data.values():
        MonsterEncounterOrderDTO.model_validate(order)
