from __future__ import annotations

from math import isfinite
from typing import TYPE_CHECKING, TypeGuard

from src.backend.features.character.runtime.gear_score import GEAR_SCORE_VERSION, CharacterGearScoreCalculator

if TYPE_CHECKING:
    from typing import Any

    from src.backend.features.arena.integrations.stream_client import ArenaStreamClient
    from src.backend.infrastructure.actor_state.managers import CharacterSessionManager
    from src.backend.infrastructure.arena.managers import ArenaSessionManager


class ArenaIntegration:
    """Read current Character scores and adapt them to Arena's integer contract."""

    def __init__(
        self,
        *,
        session_manager: ArenaSessionManager,
        stream_client: ArenaStreamClient,
        character_sessions: CharacterSessionManager | None = None,
        gear_score_calculator: CharacterGearScoreCalculator | None = None,
    ) -> None:
        self.session_manager = session_manager
        self.stream_client = stream_client
        self.character_sessions = character_sessions
        self.gear_score_calculator = gear_score_calculator or CharacterGearScoreCalculator()

    async def fetch_gear_score(self, char_id: int) -> int:
        if self.character_sessions is not None:
            session = await self.character_sessions.get_session(char_id)
            if isinstance(session, dict):
                metrics_raw = session.get("metrics")
                metrics: dict[str, Any] = metrics_raw if isinstance(metrics_raw, dict) else {}
                cached = metrics.get("gear_score")
                if _valid_cache(cached, metrics):
                    return max(0, round(float(cached)))
                breakdown = self.gear_score_calculator.calculate_breakdown_from_active_character(session)
                score = float(breakdown["total"])
                await self.character_sessions.patch_fields(
                    char_id,
                    {
                        "$.metrics.gear_score": score,
                        "$.metrics.gear_score_breakdown": breakdown,
                        "$.metrics.gear_score_version": GEAR_SCORE_VERSION,
                    },
                )
                return max(0, round(score))

        scores = await self.stream_client.request_gear_scores([char_id])
        if char_id not in scores:
            raise RuntimeError(f"character gear score unavailable: char_id={char_id}")
        return max(0, round(scores[char_id]))

    async def fetch_gear_scores(self, char_ids: list[int]) -> dict[int, int]:
        if self.character_sessions is None:
            return {
                key: max(0, round(value))
                for key, value in (await self.stream_client.request_gear_scores(char_ids)).items()
            }

        scores: dict[int, int] = {}
        sessions = await self.character_sessions.get_sessions_batch(char_ids)
        for char_id, session in sessions.items():
            if not isinstance(session, dict):
                continue
            metrics_raw = session.get("metrics")
            metrics: dict[str, Any] = metrics_raw if isinstance(metrics_raw, dict) else {}
            cached = metrics.get("gear_score")
            if _valid_cache(cached, metrics):
                scores[char_id] = max(0, round(float(cached)))
                continue
            breakdown = self.gear_score_calculator.calculate_breakdown_from_active_character(session)
            score = float(breakdown["total"])
            await self.character_sessions.patch_fields(
                char_id,
                {
                    "$.metrics.gear_score": score,
                    "$.metrics.gear_score_breakdown": breakdown,
                    "$.metrics.gear_score_version": GEAR_SCORE_VERSION,
                },
            )
            scores[char_id] = max(0, round(score))

        missing = [char_id for char_id in char_ids if char_id not in scores]
        if missing:
            scores.update(
                {
                    key: max(0, round(value))
                    for key, value in (await self.stream_client.request_gear_scores(missing)).items()
                }
            )
        return scores


def _valid_cache(score: Any, metrics: dict[str, Any]) -> TypeGuard[int | float]:
    return (
        metrics.get("gear_score_version") == GEAR_SCORE_VERSION
        and isinstance(score, (int, float))
        and not isinstance(score, bool)
        and isfinite(score)
        and score >= 0
    )
