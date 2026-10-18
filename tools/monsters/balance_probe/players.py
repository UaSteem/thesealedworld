"""Resolve actual starter builds or explicitly preserved saved actor snapshots."""

from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import ProbeConfig


def _known_feints(payload: dict[str, Any], *, name: str) -> list[str]:
    """Preserve explicit runtime arsenals across the narrower loadout DTO."""
    sources = []
    for label, document, key in (
        ("known_feints", payload, "known_feints"),
        ("loadout.known_feints", payload.get("loadout", {}), "known_feints"),
        ("meta.feints.arsenal", payload.get("meta", {}).get("feints", {}), "arsenal"),
    ):
        if key not in document:
            continue
        value = document[key]
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise ValueError(f"{name}: {label} must be a list of feint IDs")
        sources.append((label, list(dict.fromkeys(value))))
    if sources and any(set(value) != set(sources[0][1]) for _, value in sources[1:]):
        raise ValueError(f"{name}: conflicting explicit feint arsenals")
    return sources[0][1] if sources else []


def _validate_payload(payload: dict[str, Any], *, name: str) -> dict[str, Any]:
    from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
    from src.backend.features.character.runtime.experimental_gear_score import ExperimentalGearScoreCalculator
    from src.backend.features.combat.dto import ActorLoadoutDTO, ActorRawDTO

    result = deepcopy(payload)
    known_feints = _known_feints(result, name=name)
    if not isinstance(result.get("skills"), dict):
        raise ValueError(f"{name}: snapshot requires explicit skills")
    result["raw"] = ActorRawDTO.model_validate(result["raw"]).model_dump(mode="json")
    result["loadout"] = ActorLoadoutDTO.model_validate(result["loadout"]).model_dump(mode="json")
    result["loadout"]["known_feints"] = known_feints
    if any(
        not isinstance(v, (float, int)) or isinstance(v, bool) or not 0 <= v <= 1 for v in result["skills"].values()
    ):
        raise ValueError(f"{name}: skills must be finite values between zero and one")
    result["name"] = result.get("name") or name
    result["gear_score_breakdown"] = ExperimentalGearScoreCalculator().calculate_from_raw(
        result["raw"], skills=result["skills"], loadout=result["loadout"]
    )
    result["gear_score"] = result["gear_score_breakdown"]["total"]
    values, _ = StatsWaterfallCalculator.calculate_waterfall(result["raw"])
    result["preview_values"] = values
    equipment = result.get("equipment", {})
    result["equipment_count"] = (
        len(equipment.get("layout", {}).get("equipment", {})) if isinstance(equipment, dict) else len(equipment)
    )
    result["regen"] = {
        "combat": {
            resource: values.get(key, 0)
            for resource, key in [
                ("hp", "combat_hp_regen"),
                ("en", "combat_en_regen"),
                ("stamina", "combat_stamina_regen"),
            ]
        },
        "outside": {
            resource: values.get(key, 0)
            for resource, key in [("hp", "hp_regen"), ("en", "en_regen"), ("stamina", "stamina_regen")]
        },
    }
    return result


def _override_mastery(payload: dict, mastery: float | None, *, name: str) -> dict:
    if mastery is None:
        return payload
    from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
    from src.backend.features.character.runtime.combat_math_model import CharacterCombatMathModelBuilder

    context = payload.get("input_context")
    if not context:
        raise ValueError(
            f"{name}: --mastery needs saved input_context (attributes, items and symbiote); a raw snapshot cannot safely rebuild skill-dependent item math"
        )
    skills = {key: mastery for key in payload["skills"]}
    result = deepcopy(payload)
    result["skills"] = skills
    result["raw"] = CharacterCombatMathModelBuilder().build_raw(
        attributes=context["attributes"], items=context["items"], skills=skills, symbiote=context["symbiote"]
    )
    result["loadout"] = CharacterCombatActorInputBuilder._loadout(context["items"], skills, context["symbiote"])
    # Mastery rebuild owns the new arsenal; do not retain stale saved aliases.
    result.pop("known_feints", None)
    if "feints" in result.get("meta", {}):
        result["meta"]["feints"].pop("arsenal", None)
    result["source"]["mastery_override"] = mastery
    return result


def _live_player(identity: str, config: ProbeConfig) -> dict:
    from src.backend.features.combat.runtime.simulation.starting_imprint_actors import (
        StartingImprintSimulationActorBuilder,
    )

    class CapturingBuilder(StartingImprintSimulationActorBuilder):
        document: dict

        def _active_character(self, *args, **kwargs):
            self.document = super()._active_character(*args, **kwargs)
            return self.document

    builder = CapturingBuilder()
    previous = random.getstate()
    try:
        random.seed(0)
        built = builder.build_actor(
            identity, actor_id="probe_player", team="player", ai_archetype="balanced", ai_behavior_profile="balanced"
        )
    finally:
        random.setstate(previous)
    actor = built.actor
    context = {key: deepcopy(builder.document[key]) for key in ("attributes", "symbiote")}
    context["items"] = deepcopy(builder.document["items"])
    payload = {
        "name": actor.meta.name,
        "raw": actor.raw.model_dump(mode="json"),
        "skills": dict(actor.skills),
        "loadout": actor.loadout.model_dump(mode="json"),
        "known_feints": list(actor.meta.feints.arsenal),
        "equipment": context["items"],
        "input_context": context,
        "source": {
            "mode": "live_starting_imprint",
            "imprint_id": identity,
            "tier": 0,
            "meaning": "Current actual starting imprint; no tier upgrade; empty initial combat hands/tokens in probe.",
        },
    }
    return _validate_payload(_override_mastery(payload, config.mastery, name=identity), name=identity)


def _saved_players(config: ProbeConfig) -> dict[str, dict]:
    assert config.player_input is not None
    data = json.loads(config.player_input.read_text(encoding="utf-8-sig"))
    if config.player_tier is not None:
        declared = data.get("tier", data.get("player_tier"))
        if declared is not None and declared != config.player_tier:
            raise ValueError("Saved player tier differs from --player-tier")
    if all(key in data for key in ("raw", "skills", "loadout")):
        available = {"player": data}
    elif "resolved_players" in data:
        available = data["resolved_players"]
    else:
        available = {
            key: value
            for key, value in data.items()
            if isinstance(value, dict) and all(field in value for field in ("raw", "skills", "loadout"))
        }
    keys = config.player_keys
    if not keys:
        if len(available) != 1:
            raise ValueError("Saved input is ambiguous; select one or more --player-key values")
        keys = tuple(available)
    if any(key not in available for key in keys):
        raise ValueError(f"Unknown saved player key; available keys: {sorted(available)}")
    digest = hashlib.sha256(config.player_input.read_bytes()).hexdigest()
    result = {}
    for key in keys:
        payload = deepcopy(available[key])
        payload["source"] = {
            "mode": "saved_snapshot",
            "path": str(config.player_input.resolve()),
            "sha256": digest,
            "key": key,
            "tier": config.player_tier if config.player_tier is not None else data.get("tier", data.get("player_tier")),
            "meaning": "Preserved saved raw/loadout/skills; current waterfall/resolver, not rebuilt item catalog.",
        }
        result[key] = _validate_payload(_override_mastery(payload, config.mastery, name=key), name=key)
    return result


def resolve_players(config: ProbeConfig) -> dict[str, dict]:
    if config.player_input is not None:
        return _saved_players(config)
    return {identity: _live_player(identity, config) for identity in config.players}
