"""Recipient healing math, applied once before staging resource changes."""

from src.backend.features.combat.dto.actor import ActorStats


def received_healing_amount(amount: float, recipient: ActorStats | None) -> int:
    """Scale healing only; resource regeneration and damage use separate paths."""
    bonus = float(recipient.mods.received_healing_bonus or 0.0) if recipient else 0.0
    return int(max(0.0, amount) * max(0.0, 1.0 + bonus))
