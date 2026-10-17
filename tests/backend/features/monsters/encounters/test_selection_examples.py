"""Documented payloads remain valid and selected examples reference buildable content."""

import json
from pathlib import Path

from pydantic import TypeAdapter

from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.encounters.dto.selection import MonsterSquadResultDTO
from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService


def test_documented_squad_payloads_roundtrip_and_selected_content_is_ready():
    root = Path(__file__).resolve().parents[5]
    examples = json.loads(
        (root / "docs/ru/backend/features/monsters/squad_contract_examples.json").read_text(encoding="utf-8")
    )
    adapter = TypeAdapter(MonsterSquadResultDTO)
    catalog = get_catalog()
    for payload in examples.values():
        result = adapter.validate_python(payload)
        assert adapter.validate_json(adapter.dump_json(result)) == result
        if result.status == "rejected":
            assert result.reasons
            assert "members" not in adapter.dump_python(result)
            continue
        for selected in result.members:
            member = catalog.members[selected.member_id]
            assert (selected.role, selected.clan_id, selected.family_id, selected.variant_id) == (
                member.role,
                member.clan_id,
                member.family_id,
                member.variant_id,
            )
            report = MonsterBuildReadinessService().check(
                member=member,
                family=catalog.families[member.family_id],
                tier=selected.tier,
            )
            assert report.ready, report.issues
