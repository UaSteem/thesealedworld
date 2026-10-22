from typing import Any

from loguru import logger as log

from src.backend.core.database import get_session_context
from src.backend.features.character.services.combat_progression import checkpoint_combat_progression
from src.backend.features.combat.runtime.services.data_service import CombatDataService  # noqa: TC001
from src.backend.features.combat.runtime.services.durability_policy import CombatDurabilityPolicy
from src.backend.features.combat.runtime.services.experience_finalizer import CombatExperienceFinalizer
from src.backend.features.combat.runtime.services.finalization_builder import CombatFinalizationBuilder
from src.backend.features.combat.services.finalization_journal import CombatFinalizationJournal
from src.backend.features.combat.services.post_battle_router import CombatPostBattleRouter
from src.backend.features.combat.workers.tasks.chat_announcements import publish_combat_final_announcement
from src.backend.features.expedition import ExpeditionService
from src.backend.features.inventory.events.publisher import InventoryEvents
from src.backend.infrastructure.loot.managers.loot_manager import LootManager
from src.backend.realtime.integrations.notice_publisher import (
    PlayerNoticePublisher,
    RawStreamNoticeProducer,
    RefreshTargets,
)
from src.shared.enums import CoreDomain
from src.shared.infrastructure.log_task_wrapper import logged_task


class RetiredCombatFinalizationError(RuntimeError):
    """A frozen result belongs to a runtime retired from the active build."""


def _build_notice_publisher(ctx: dict) -> PlayerNoticePublisher | None:
    redis = ctx.get("redis_client_internal")
    if redis is None:
        return None
    return PlayerNoticePublisher(RawStreamNoticeProducer(redis))


@logged_task
async def victory_finalizer_task(ctx: dict, data: dict) -> None:
    """
    Финализатор боя (Victory Finalizer).

    Выполняется после определения победителя.
    Отвечает за завершение боя и начисление наград.

    Args:
        ctx: ARQ worker context with runtime, persistence, and cross-feature deps.
        data: Finalization payload containing ``session_id`` and ``winner``.

    Side Effects:
        - Marks the winner in runtime storage.
        - Finalizes XP/progression and persists frozen finalization payloads.
        - Commits post-combat outcomes back into active character sessions.
        - Enqueues the long-term finalization persistence job.
    """
    session_id = data.get("session_id", "unknown")
    winner = data.get("winner", "unknown")

    log.bind(session_id=session_id, winner=winner, status="processing").info("VictoryFinalizerStarted")

    data_service: CombatDataService | None = ctx.get("combat_data_service")
    if not data_service:
        raise RuntimeError("Combat data service unavailable")

    journal = ctx.get("combat_finalization_journal") or CombatFinalizationJournal()
    try:
        finalization = await journal.load(session_id)
        if finalization and finalization.get("legacy_finalized"):
            log.bind(session_id=session_id).warning("VictoryFinalizerLegacyResultAlreadyFinalized")
            return
        if finalization is None:
            meta = await data_service.get_meta(session_id)
            if not isinstance(meta, dict) or not meta:
                raise RuntimeError(f"Combat facts unavailable for finalization: {session_id}")
            global_rate = 0.00005
            game_config = ctx.get("game_config")
            if game_config is not None:
                global_rate = await game_config.get_float("core", "SKILL_PROGRESSION_BASE_RATE", default=0.00005)
            progression_results = await CombatExperienceFinalizer().finalize(
                data_service, session_id, winner, global_rate=global_rate, apply=False
            )
            finalization = await CombatFinalizationBuilder().build(
                data_service, session_id, winner, progression_results=progression_results
            )
            await _freeze_progression_destinations(ctx, finalization)
            # First durable commit precedes closure or any reward mutation.
            frozen = await journal.freeze(finalization)
            # Keep full traces in the cache; the durable core owns rewards/outcome.
            finalization = {**frozen, "analytics": finalization.get("analytics", {})}
            await data_service.save_finalization(
                session_id, finalization, char_ids=finalization.get("participant_char_ids", []), ttl=86400
            )

        async def close_runtime(facts: dict[str, Any]) -> None:
            await data_service.set_battle_winner(session_id, facts["winner_team"])

        async def vitals(facts: dict[str, Any]) -> None:
            await _commit_frozen_player_vitals(ctx, facts)

        async def progression(facts: dict[str, Any]) -> None:
            await _apply_frozen_progression(ctx, facts)

        async def cache(facts: dict[str, Any]) -> None:
            # Reconstruct the result after cache expiry without live runtime keys.
            existing = await data_service.get_finalization(session_id)
            await data_service.save_finalization(
                session_id, existing or facts, char_ids=facts.get("participant_char_ids", []), ttl=86400
            )

        async def rift(facts: dict[str, Any]) -> None:
            await _apply_rift_combat_result(ctx, facts)

        async def durability(facts: dict[str, Any]) -> None:
            await _apply_durability_consequences(ctx, facts)

        async def attach(facts: dict[str, Any]) -> None:
            await _attach_finalization_to_active_sessions(ctx, session_id, facts)

        async def announce(facts: dict[str, Any]) -> None:
            await publish_combat_final_announcement(ctx, facts)

        async def archive(_facts: dict[str, Any]) -> None:
            await _enqueue_finalization_persist(ctx, session_id)

        for step, action in (
            ("closed", close_runtime),
            ("vitals", vitals),
            ("progression", progression),
            ("cache", cache),
            ("rift", rift),
            ("durability", durability),
            ("attached", attach),
            ("announced", announce),
            ("complete", archive),
        ):
            await journal.run_step(session_id, step, action)
        log.bind(session_id=session_id).info("VictoryFinalizerCompleted")
    except Exception as error:
        log.bind(session_id=session_id).exception("VictoryFinalizerFailed")
        if isinstance(error, RetiredCombatFinalizationError):
            await journal.block_retired(session_id)
            raise
        if "job_try" in ctx:
            from arq import Retry

            raise Retry(defer=min(60, 5 * int(ctx["job_try"]))) from None
        raise


async def _apply_frozen_progression(ctx: dict, finalization: dict[str, Any]) -> None:
    sessions = ctx.get("character_sessions")
    combat_id = str(finalization["combat_id"])

    async def apply(recorder: Any | None) -> None:
        for actor in finalization.get("actors", {}).values():
            char_id = actor.get("char_id")
            rewards = actor.get("progression") or {}
            if char_id is None or not rewards:
                continue
            destination = actor.get("progression_destination")
            if not isinstance(destination, dict):
                raise RuntimeError("Frozen combat progression destination is missing")
            if destination.get("kind") == "expedition":
                if recorder is None:
                    raise RuntimeError("Frozen combat expedition recorder is unavailable")
                if not await recorder.apply_progress(
                    int(char_id), rewards, combat_id=combat_id, expedition_run_id=destination["run_id"]
                ):
                    raise RuntimeError("Frozen combat expedition cannot accept progression")
                continue
            if destination.get("kind") != "secured":
                raise RuntimeError("Unknown frozen combat progression destination")
            if sessions is None:
                raise RuntimeError("Character sessions unavailable for combat progression")
            await sessions.apply_skill_progress(int(char_id), rewards, combat_id=combat_id)
            checkpoint = ctx.get("combat_progression_checkpoint") or checkpoint_combat_progression
            await checkpoint(sessions, int(char_id), combat_id)

    if ctx.get("expeditions") is not None or ctx.get("world_locations") is not None:
        async with get_session_context() as session:
            await apply(
                ExpeditionService(
                    session=session,
                    character_sessions=sessions,
                    expedition_manager=ctx.get("expeditions"),
                    world_store=ctx.get("world_locations"),
                    game_config=ctx.get("game_config"),
                )
            )
    else:
        await apply(None)


async def _freeze_progression_destinations(ctx: dict, finalization: dict[str, Any]) -> None:
    actors = [actor for actor in finalization.get("actors", {}).values() if actor.get("char_id") is not None]
    for actor in actors:
        actor["progression_destination"] = {"kind": "secured"}
    if ctx.get("expeditions") is None and ctx.get("world_locations") is None:
        return
    async with get_session_context() as session:
        recorder = ExpeditionService(session=session)
        for actor in actors:
            expedition = await recorder.get_active_run(int(actor["char_id"]))
            if expedition is not None:
                if expedition.status != "active":
                    raise RuntimeError("Combat progression cannot freeze into a non-active expedition")
                actor["progression_destination"] = {"kind": "expedition", "run_id": expedition.run_id}


async def _commit_frozen_player_vitals(ctx: dict, finalization: dict[str, Any]) -> None:
    sessions = ctx.get("character_sessions")
    if sessions is None and finalization.get("participant_char_ids"):
        raise RuntimeError("Character sessions unavailable for combat vitals")
    for actor in finalization.get("actors", {}).values():
        char_id = actor.get("char_id")
        if char_id is None:
            continue
        if not await _session_still_in_combat(sessions, int(char_id), str(finalization["combat_id"])):
            continue
        vitals = actor.get("vitals_final") or {}
        for vital, source, maximum in (
            ("hp", "hp", "max_hp"),
            ("energy", "en", "max_en"),
            ("stamina", "stamina", "max_stamina"),
        ):
            await _update_vital_if_present(sessions, int(char_id), vital, vitals.get(source), vitals.get(maximum))


async def _session_still_in_combat(sessions: Any, char_id: int, combat_id: str) -> bool:
    document = await sessions.get_session(char_id)
    if not isinstance(document, dict):
        raise RuntimeError(f"Character session unavailable during finalization: {char_id}")
    refs = document.get("sessions") or {}
    return str(refs.get("combat_id") or "") == combat_id


async def _session_owns_finalization(sessions: Any, char_id: int, combat_id: str) -> bool:
    document = await sessions.get_session(char_id)
    if not isinstance(document, dict):
        raise RuntimeError(f"Character session unavailable during finalization: {char_id}")
    refs = document.get("sessions") or {}
    return str(refs.get("combat_id") or "") == combat_id or (
        not refs.get("combat_id")
        and str(refs.get("combat_finalization_id") or "") == combat_id
        and document.get("state") in {CoreDomain.COMBAT_RESULT.value, CoreDomain.DEATH.value}
    )


async def _enqueue_finalization_persist(ctx: dict, session_id: str) -> None:
    queue = ctx.get("redis")
    if queue is None:
        raise RuntimeError("Combat persistence queue unavailable")
    await queue.enqueue_job("combat_finalization_persist_task", {"combat_id": session_id})


async def _apply_durability_consequences(ctx: dict, finalization: dict[str, Any]) -> None:
    events = ctx.get("events")
    request = getattr(events, "request", None)
    requests = CombatDurabilityPolicy().resolve(finalization)
    if request is None:
        if requests:
            raise RuntimeError("Combat durability event transport unavailable")
        return

    for durability_request in requests:
        payload = durability_request.as_payload()
        response = await request(
            InventoryEvents.DURABILITY_DAMAGE_REQUESTED,
            payload,
            timeout=30.0,
            correlation_id=durability_request.idempotency_key,
        )
        if not isinstance(response, dict) or response.get("status") not in {"ok", "skipped"}:
            raise RuntimeError(f"Combat durability request failed: {durability_request.idempotency_key}")


async def _apply_rift_combat_result(ctx: dict, finalization: dict[str, Any]) -> None:
    meta = finalization.get("meta") if isinstance(finalization.get("meta"), dict) else {}
    battle_type = str(meta.get("battle_type") or "").lower()
    rift_session_id = str(meta.get("rift_session_id") or "")
    if battle_type != "rift" and not rift_session_id:
        return
    if not rift_session_id:
        raise RuntimeError("Rift combat finalization is missing its session")

    # Retired by the separately authorized Rift alpha retirement. Old frozen
    # work remains visible as pending; it must not resurrect legacy gameplay.
    raise RetiredCombatFinalizationError("Legacy Rift combat finalization is retired")


async def _attach_finalization_to_active_sessions(ctx: dict, session_id: str, finalization: dict[str, Any]) -> None:
    character_sessions = ctx.get("character_sessions")
    if character_sessions is None:
        return

    char_ids = [int(char_id) for char_id in finalization.get("participant_char_ids", []) if _int_or_none(char_id)]
    char_ids = [
        char_id for char_id in char_ids if await _session_owns_finalization(character_sessions, char_id, session_id)
    ]
    dead_char_ids = {
        int(actor.get("char_id"))
        for actor in (finalization.get("actors") or {}).values()
        if isinstance(actor, dict) and actor.get("char_id") in char_ids and actor.get("is_dead") is True
    }
    location_id = (
        (finalization.get("meta") or {}).get("location_id") if isinstance(finalization.get("meta"), dict) else None
    )
    notice_publisher = _build_notice_publisher(ctx)
    death_marked: set[int] = set()
    if dead_char_ids:
        async with get_session_context() as session:
            expedition_service = ExpeditionService(
                session=session,
                character_sessions=character_sessions,
                expedition_manager=ctx.get("expeditions"),
                loot_manager=LootManager(ctx["redis_service"]) if ctx.get("redis_service") is not None else None,
                world_store=ctx.get("world_locations"),
                commit_on_write=True,
                game_config=ctx.get("game_config"),
                notice_publisher=notice_publisher,
            )
            for char_id in dead_char_ids:
                if await expedition_service.mark_death_pending(
                    char_id=char_id,
                    combat_id=session_id,
                    location_id=str(location_id) if location_id else None,
                ):
                    await expedition_service.finalize_death_corpse(char_id=char_id)
                    death_marked.add(char_id)

    post_combat = await CombatPostBattleRouter().build_outcomes(ctx, finalization)
    for char_id in char_ids:
        outcome = post_combat.get(char_id)
        outcome_payload = outcome.model_dump(mode="json") if outcome is not None else None
        if char_id in death_marked:
            if outcome_payload is not None:
                await character_sessions.patch_fields(char_id, {"$.sessions.post_combat": outcome_payload})
                await character_sessions.mark_dirty(
                    char_id,
                    reason="combat_post_battle_outcome_attached",
                    paths=["$.sessions.post_combat"],
                )
            continue
        await character_sessions.patch_fields(
            char_id,
            {
                "$.sessions.combat_id": None,
                "$.sessions.combat_finalization_id": str(session_id),
                "$.sessions.post_combat": outcome_payload,
                "$.state": CoreDomain.COMBAT_RESULT.value,
            },
        )
        await character_sessions.mark_dirty(
            char_id,
            reason="combat_finalization_attached",
            paths=["$.sessions.combat_finalization_id", "$.sessions.combat_id", "$.sessions.post_combat", "$.state"],
        )

    # Combat resolved without a direct player request — wake each participant's
    # HUD to re-fetch the status fragment (vitals/state changed in the worker).
    if notice_publisher is not None:
        for char_id in char_ids:
            await notice_publisher.request_refresh(
                char_id,
                target=RefreshTargets.STATUS,
                reason="combat_finalized",
                domain="combat",
            )


async def _update_vital_if_present(
    character_sessions: Any,
    char_id: int,
    vital: str,
    cur: Any,
    max_value: Any,
) -> None:
    if cur is None and max_value is None:
        return
    await character_sessions.update_vital(char_id, vital, cur=_int_or_none(cur), max=_int_or_none(max_value))


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
