"""Runtime ownership of selected intents, activations and concrete strikes.

Transport moves describe user choices. A generated strike may refer to that
choice, but only the primary strike activates it. Counter reactions have an
owner and a cause, without inventing a selected intent for that actor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from src.backend.features.combat.dto.action import CombatMoveDTO
from src.backend.features.combat.dto.payloads import ExchangePayload

if TYPE_CHECKING:
    from src.backend.features.combat.dto.ids import ActorId
    from src.backend.features.combat.dto.pipeline import InteractionResultDTO

StrikeOrigin = Literal["primary", "offhand", "counter", "secondary"]
FeintMode = Literal["activate", "project", "none"]


@dataclass(frozen=True)
class CombatIntent:
    move: CombatMoveDTO

    @property
    def owner_id(self) -> ActorId:
        return self.move.char_id


@dataclass(frozen=True)
class FeintActivation:
    owner_id: ActorId
    intent_id: str
    feint_id: str

    def applied_to(self, result: InteractionResultDTO) -> bool:
        """Only an actual owned activation enables cooldown and area projection."""
        outcome = result.feint_activation
        return outcome is not None and (
            outcome.owner_id == self.owner_id
            and outcome.intent_id == self.intent_id
            and outcome.feint_id == self.feint_id
            and outcome.state == "activated"
        )


@dataclass(frozen=True)
class StrikeExecution:
    owner_id: ActorId
    target_id: ActorId | None
    origin: StrikeOrigin
    strike_id: str
    parent_id: str | None = None
    intent: CombatIntent | None = None

    def __post_init__(self) -> None:
        if self.intent is not None and self.intent.owner_id != self.owner_id:
            raise ValueError("Strike owner must match intent owner")
        if self.origin in {"primary", "secondary"} and self.intent is None:
            raise ValueError("Selected strikes require an owned intent")

    @classmethod
    def primary(cls, move: CombatMoveDTO, target_id: ActorId | None) -> StrikeExecution:
        return cls(move.char_id, target_id, "primary", f"{move.move_id}:primary", intent=CombatIntent(move))

    def child(self, origin: StrikeOrigin, *, owner_id: ActorId, target_id: ActorId | None) -> StrikeExecution:
        return StrikeExecution(
            owner_id,
            target_id,
            origin,
            f"{self.strike_id}:{origin}:{target_id}",
            self.strike_id,
            self.intent if origin in {"offhand", "secondary"} else None,
        )

    @property
    def feint_mode(self) -> FeintMode:
        if self.origin == "primary":
            return "activate"
        return "project" if self.origin == "secondary" else "none"

    @property
    def activation(self) -> FeintActivation | None:
        feint_id = (
            self.payload.get("feint_id") if isinstance(self.payload, dict) else getattr(self.payload, "feint_id", None)
        )
        if self.feint_mode != "activate" or not feint_id or self.intent is None:
            return None
        return FeintActivation(self.owner_id, self.intent.move.move_id, str(feint_id))

    @property
    def strategy(self):
        return self.intent.move.strategy if self.intent else "exchange"

    @property
    def payload(self):
        return self.intent.move.payload if self.intent else {}

    def provenance(self) -> dict[str, Any]:
        return {
            "strike_id": self.strike_id,
            "owner_id": self.owner_id,
            "origin": self.origin,
            "parent_id": self.parent_id,
            "intent_id": self.intent.move.move_id if self.intent else None,
            "feint_mode": self.feint_mode,
        }

    def context_mods(self, external_mods: dict[str, Any] | None = None) -> dict[str, Any]:
        """Origin is authoritative for hand, counter and projection semantics."""
        mods = dict(external_mods or {})
        for key in ("is_counter_attack", "feint_role", "hand", "source_type", "pay_cost", "generate_feints"):
            mods.pop(key, None)
        if self.origin == "counter":
            mods.update(is_counter_attack=True, hand="main", action_mode="exchange")
        elif self.origin == "offhand":
            mods.update(hand="off", action_mode="exchange")
        elif self.origin == "secondary":
            mods.update(feint_role="secondary", pay_cost=False, generate_feints=False, action_mode="unidirectional")
        return mods

    def log_move(self) -> CombatMoveDTO:
        """Adapt a concrete strike to the existing support/log transport schema."""
        if self.intent:
            move = self.intent.move.model_copy(
                deep=True, update={"targets": [self.target_id] if self.target_id else []}
            )
            if isinstance(move.payload, dict):
                move.payload["target_id"] = self.target_id
            elif hasattr(move.payload, "target_id"):
                move.payload.target_id = self.target_id
            if self.origin == "offhand":
                # The selected intent remains intact; the public action view
                # describes a plain generated strike.
                if self.target_id is None:
                    raise ValueError("Generated strike requires a target")
                move.payload = ExchangePayload(target_id=self.target_id)
            return move
        if self.target_id is None:
            raise ValueError("Generated strike requires a target")
        return CombatMoveDTO(
            move_id=self.strike_id,
            char_id=self.owner_id,
            strategy="exchange",
            payload=ExchangePayload(target_id=self.target_id),
            targets=[self.target_id] if self.target_id else [],
        )


def normalize_execution(
    move: CombatMoveDTO | StrikeExecution,
    *,
    source_id: ActorId,
    target_id: ActorId | None,
    external_mods: dict[str, Any] | None,
) -> StrikeExecution:
    if isinstance(move, StrikeExecution):
        execution = move
    else:
        execution = StrikeExecution.primary(move, target_id)
        mods = external_mods or {}
        if mods.get("is_counter_attack"):
            execution = execution.child("counter", owner_id=source_id, target_id=target_id)
            # Direct transport callers still must supply their own move.
            if move.char_id != source_id:
                raise ValueError("Pipeline source must match intent owner")
        elif mods.get("feint_role") == "secondary":
            execution = execution.child("secondary", owner_id=source_id, target_id=target_id)
        elif mods.get("hand") == "off" or mods.get("source_type") == "off_hand":
            execution = execution.child("offhand", owner_id=source_id, target_id=target_id)
    if execution.owner_id != source_id or execution.target_id != target_id:
        raise ValueError("Pipeline participants must match strike owner and target")
    if execution.intent and execution.intent.owner_id != source_id:
        raise ValueError("Pipeline source must match intent owner")
    return execution
