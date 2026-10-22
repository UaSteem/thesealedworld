from __future__ import annotations

from typing import Any

from src.backend.core.database import get_session_context
from src.backend.features.character.repositories import CharacterProgressionRepository, SkillRepository
from src.shared.enums.skill_enums import SkillProgressState


async def checkpoint_combat_progression(character_sessions: Any, char_id: int, combat_id: str) -> None:
    """Do not finish combat work until XP and its Redis receipt reach SQL together."""
    async with get_session_context() as session:
        progression_repo = CharacterProgressionRepository(session)
        await progression_repo.lock_character(char_id)
        document = await character_sessions.get_session(char_id)
        progression = (document or {}).get("progression") or {}
        receipts = dict(progression.get("combat_receipts") or {})
        if combat_id not in receipts:
            raise RuntimeError("Combat progression disappeared before durable checkpoint")
        rows = []
        for key, value in (document.get("skills") or {}).items():
            payload = value if isinstance(value, dict) else {"xp": value}
            rows.append(
                {
                    "character_id": char_id,
                    "skill_key": key,
                    "total_xp": float(payload.get("xp", payload.get("total_xp", 0.0)) or 0.0),
                    "is_unlocked": bool(payload.get("unlocked", True)),
                    "progress_state": SkillProgressState(payload.get("state") or SkillProgressState.PLUS.value),
                }
            )
        await SkillRepository(session).upsert_progress_rows(rows)
        await progression_repo.set_free_xp(char_id, float(progression.get("free_xp") or 0.0), combat_receipts=receipts)
