"""Anatomy activity measures natural HP regeneration actually committed in combat."""

import pytest

from src.backend.features.combat.dto import (
    ActorMetaDTO,
    ActorRawDTO,
    ActorSnapshot,
    InteractionResultDTO,
    PipelineContextDTO,
)
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
from src.backend.features.combat.runtime.services.experience_finalizer import CombatExperienceFinalizer


def regeneration_actor(hp=50):
    return ActorSnapshot(
        meta=ActorMetaDTO(id=1, name="Hero", type="player", team="a", hp=hp, max_hp=100),
        raw=ActorRawDTO(),
    )


@pytest.mark.parametrize(
    "hp,changes,expected_hp,regenerated",
    [
        (50, {"combat_regen": "+5"}, 55, 5),
        (98, {"combat_regen": "+5"}, 100, 2),
        (100, {"combat_regen": "+5"}, 100, 0),
        (50, {"cost": "-10", "combat_regen": "+5"}, 45, 5),
        (50, {"cost": "-5", "combat_regen": "+5"}, 50, 5),
        (2, {"cost": "-10", "combat_regen": "+5"}, 0, 0),
        (98, {"other": "+5", "combat_regen": "+5"}, 100, 0),
        (50, {"combat_regen": "+1.9"}, 51, 1),
        (50, {"combat_regen": "+0.5"}, 50, 0),
        (50, {"cost": "-0.6", "combat_regen": "+1"}, 50, 0),
        (50, {"cost": "-1.6", "combat_regen": "+1"}, 50, 1),
        (50, {"combat_regen": "-5"}, 45, 0),
        (50, {"heal": "+5"}, 55, 0),
        (50, {"lifesteal": "+5"}, 55, 0),
    ],
)
def test_anatomy_counts_only_committed_natural_hp_regeneration(hp, changes, expected_hp, regenerated):
    actor = regeneration_actor(hp)
    result = InteractionResultDTO(source_id=1, resource_changes={"hp": changes})

    MechanicsService().apply_interaction_result(PipelineContextDTO(), actor, None, result)

    assert actor.meta.hp == expected_hp
    assert actor.xp_buffer.get("combat_hp_regenerated", 0) == regenerated


@pytest.mark.parametrize("disabled_flag", ["pay_cost", "grant_xp"])
def test_anatomy_regeneration_activity_respects_mechanics_flags(disabled_flag):
    actor = regeneration_actor()
    ctx = PipelineContextDTO()
    setattr(ctx.flags.mechanics, disabled_flag, False)
    result = InteractionResultDTO(source_id=1, resource_changes={"hp": {"combat_regen": "+5"}})

    MechanicsService().apply_interaction_result(ctx, actor, None, result)

    assert actor.xp_buffer.get("combat_hp_regenerated", 0) == 0


def test_anatomy_accumulates_hp_only_across_turns_without_changing_skills():
    actor = regeneration_actor(96)
    mechanics = MechanicsService()
    for _ in range(3):
        result = InteractionResultDTO(
            source_id=1,
            resource_changes={
                "hp": {"combat_regen": "+3"},
                "en": {"combat_regen": "+10"},
                "stamina": {"combat_regen": "+10"},
            },
        )
        mechanics.apply_interaction_result(PipelineContextDTO(), actor, None, result)

    assert actor.meta.hp == 100
    assert actor.xp_buffer["combat_hp_regenerated"] == 4
    assert actor.skills == {}


@pytest.mark.parametrize("restored,expected", [(5, 0.001), (10, 0.002), (50, 0.01)])
def test_anatomy_converts_total_regeneration_using_attributes_after_combat(restored, expected):
    actor = {
        "raw": {"attributes": {key: {"base": 10} for key in ("intellect", "perception", "memory")}},
        "skills": {"skill_anatomy": 0},
        "xp_buffer": {"combat_hp_regenerated": restored},
    }

    assert CombatExperienceFinalizer().calculate_actor_rewards(actor) == {"skill_anatomy": expected}


def test_anatomy_no_longer_receives_experience_from_offensive_actions():
    actor = {
        "raw": {"attributes": {key: 10 for key in ("intellect", "perception", "memory")}},
        "xp_buffer": {"main_hand_hit": 4, "off_hand_crit": 1, "kill_generic": 2},
    }

    rewards = CombatExperienceFinalizer().calculate_actor_rewards(actor)

    assert "skill_anatomy" not in rewards
    assert rewards["skill_tactics"] > 0


def test_anatomy_regeneration_progression_retains_mastery_slowdown():
    actor = {
        "raw": {"attributes": {key: 10 for key in ("intellect", "perception", "memory")}},
        "skills": {"skill_anatomy": 0.5},
        "xp_buffer": {"combat_hp_regenerated": 100},
    }

    # 10 activity * 40 weighted attributes * .00005 / (1 + .5 * 100).
    assert CombatExperienceFinalizer().calculate_actor_rewards(actor) == {"skill_anatomy": 0.0004}


async def test_anatomy_regeneration_is_finalized_after_battle_once_via_progression_recorder():
    actor = regeneration_actor(86)
    actor.raw.attributes = {key: {"base": 10} for key in ("intellect", "perception", "memory")}
    for _ in range(3):
        MechanicsService().apply_interaction_result(
            PipelineContextDTO(),
            actor,
            None,
            InteractionResultDTO(source_id=1, resource_changes={"hp": {"combat_regen": "+5"}}),
        )
    assert actor.skills == {}
    assert actor.xp_buffer["combat_hp_regenerated"] == 14

    class Data:
        async def get_meta(self, session_id):
            return {"actor_ids": ["1"]}

        def actor_ids_from_meta(self, meta):
            return meta["actor_ids"]

        async def get_actors_batch(self, session_id, actor_ids):
            return {"1": actor.model_dump(mode="json", exclude={"stats"})}

    class Recorder:
        def __init__(self):
            self.calls = []

        async def apply_progress(self, char_id, rewards):
            self.calls.append((char_id, rewards))
            return True

    recorder = Recorder()
    results = await CombatExperienceFinalizer().finalize(
        Data(),
        "anatomy-regen-xp",
        "a",
        progression_recorder=recorder,
    )
    assert results["1"].rewards == {"skill_anatomy": 0.0028}
    assert recorder.calls == [(1, {"skill_anatomy": 0.0028})]
