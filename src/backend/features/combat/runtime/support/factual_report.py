"""Compact presentation of resolved facts, independent of narrative variants."""

from typing import Any


def result_template(builder, *, ctx, result, action, action_id, event_name, source_id, target_id) -> dict[str, Any]:
    from src.backend.features.combat.integrations import CombatCatalogIntegrator

    execution = result.action_facts.get("execution") or {}
    generated = execution.get("origin") in {"offhand", "counter", "secondary"} or result.is_counter
    resource_type, resource_id = "basic_exchange", "attack"
    if builder._has_event(result, "TICK"):
        resource_type, resource_id = "effect", builder._result_action_id(result) or "tick"
    elif action.action_type == "exchange":
        if not generated and builder._feint_id(action):
            resource_type, resource_id = "feint", builder._feint_id(action)
    elif action.action_type == "item":
        resource_type, resource_id = "item", action_id or "item"
    elif action.action_type == "instant":
        resource_type = "gift" if action_id and CombatCatalogIntegrator.get_gift_catalog_entry(action_id) else "ability"
        resource_id = action_id or "ability"
    label = (
        builder._resource_label(resource_type, resource_id)
        if resource_type != "basic_exchange"
        else {
            "counter": "Контратака",
            "offhand": "Вторая рука",
            "secondary": "Дополнительная цель",
        }.get(execution.get("origin"), "Атака")
    )
    if builder._has_event(result, "TICK"):
        outcome = "периодический эффект · {value} {resource}"
    elif result.skip_reason:
        outcome = {
            "no_resource": "недостаточно ресурса",
            "controlled": "действие прервано контролем",
            "stunned": "действие прервано контролем",
        }.get(result.skip_reason.lower(), "действие не выполнено")
    elif result.is_miss:
        outcome = "промах"
    elif result.is_dodged:
        outcome = "цель уклонилась"
    elif result.is_parried:
        outcome = "цель парировала"
    elif result.is_blocked:
        outcome = "цель блокировала · урон {damage}"
    elif result.healing_final > 0:
        outcome = "лечение {healing} HP"
    elif result.is_hit or result.damage_final > 0:
        outcome = ("критическое попадание" if result.is_crit else "попадание") + " · урон {damage}"
    elif builder._has_event(result, "APPLY_EFFECT") or result.applied_effects:
        outcome = "эффект «{effect}»"
    else:
        outcome = "действие выполнено"
    if builder._has_event(result, "DEATH"):
        outcome += " · цель погибла"
    return {
        "key": f"combat.fact.{resource_type}.{resource_id}.{event_name}",
        "outcome": event_name,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "body_pair": "factual",
        "action_label": label,
        "template": "{source} → {target}: " + label.replace("{", "{{").replace("}", "}}") + " · " + outcome,
    }


def result_numbers(result) -> dict[str, int | float]:
    trace = result.damage_trace
    details = trace.details if trace else {}
    shield = float(details.get("shield_absorb", 0) or 0)
    other = float(details.get("incoming_damage_absorbed", 0) or 0)
    return {
        "damage": result.damage_final,
        "healing": result.healing_final,
        "absorbed": round(shield + other, 2),
        "reflected": result.reflected_damage,
    }


def trigger_actor_ids(result, trigger_id):
    fact = next((f for f in result.trigger_facts if f.trigger_id == trigger_id), None)
    defensive = fact is not None and fact.event in {
        "ON_PRE_EVASION",
        "ON_DODGE",
        "ON_DODGE_FAIL",
        "ON_PRE_PARRY",
        "ON_PARRY",
        "ON_PARRY_FAIL",
        "ON_PRE_BLOCK",
        "ON_BLOCK",
        "ON_BLOCK_FAIL",
    }
    return (result.target_id, result.source_id) if defensive else (result.source_id, result.target_id)


def transition_entries(builder, *, ctx, result, wave, timestamp):
    entries = []
    turn = ctx.meta.step_counter + 1
    names = {
        "normal": "обычное",
        "advantage": "выгодное",
        "far": "дальняя дистанция",
        "mid": "средняя дистанция",
        "close": "ближняя дистанция",
    }
    for fact in getattr(result, "tactical_transitions", []):
        actor = builder._actor_ref(ctx, fact.actor_id)
        name = (actor or {}).get("name") or str(fact.actor_id)
        transition = fact.model_dump(mode="json")
        label = builder._resource_label("feint", fact.source_feint_id) if fact.source_feint_id else None
        if label:
            transition["source_feint_label"] = label
        entries.append(
            {
                "id": f"{turn}:{wave}:tactical:{fact.actor_id}:{len(entries)}",
                "type": "LOG",
                "kind": "tactical_transition",
                "format": "factual-v1",
                "global_turn": turn,
                "wave": wave,
                "timestamp": timestamp,
                "source": actor,
                "target": None,
                "outcome": "tactical_transition",
                "text": f"{name}: {names.get(fact.before, fact.before)} → {names.get(fact.after, fact.after)}",
                "tactical_transitions": [transition],
                "action": {"id": fact.source_feint_id or fact.source_action_id, "label": label, "mode": "exchange"},
                "result": {"resources": [], "tokens": [], "effects": []},
                "effects": [],
                "resources": [],
                "flags": {},
                "tags": ["runtime", "tactical_transition"],
            }
        )
    return entries
