from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert

from src.backend.features.items.models import ItemInstance, ItemPlacement, ItemTransaction, ResourceBalance
from src.backend.infrastructure.inventory.models import DurabilityApplication, ResourceWallet
from src.shared.schemas.inventory import InventoryRuntimeItemDTO, WalletDTO

# Two-int advisory lock key: "INVD" namespace + SQL character id.
# All durability writers and projection rebuilds use this order before row/receipt locks.
_DURABILITY_LOCK_NAMESPACE = 0x494E5644
_DURABILITY_LOCK_TIMEOUT_SECONDS = 5
_DURABILITY_PROJECTION_TIMEOUT_SECONDS = 10

_CURRENCY_PREFIXES = ("coin_", "currency_", "gold_", "silver_", "copper_")
_COMPONENT_PREFIXES = ("essence_", "flower_", "bark_", "supply_", "component_")


class InventoryItemRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def list_character_items(
        self,
        char_id: int,
        *,
        expedition_run_id: str | None = None,
    ) -> list[tuple[ItemInstance, ItemPlacement]]:
        holder_filters = [
            (ItemPlacement.holder_type == "character") & (ItemPlacement.holder_id == str(char_id)),
        ]
        if expedition_run_id:
            holder_filters.append(
                (ItemPlacement.holder_type == "expedition") & (ItemPlacement.holder_id == expedition_run_id)
            )
        holder_clause = or_(*holder_filters)
        result = await self.session.execute(
            select(ItemInstance, ItemPlacement)
            .join(ItemPlacement, ItemPlacement.item_id == ItemInstance.id)
            .where(holder_clause)
            .order_by(ItemPlacement.position_index.nulls_last(), ItemInstance.name, ItemInstance.id)
            .execution_options(populate_existing=True)
        )
        return list(result.all())

    async def get_wallet(self, char_id: int) -> WalletDTO:
        wallet = await self.session.scalar(select(ResourceWallet).where(ResourceWallet.character_id == char_id))
        if wallet is None:
            return WalletDTO()
        return WalletDTO(
            currency=dict(wallet.currency or {}),
            resources=dict(wallet.resources or {}),
            components=dict(wallet.components or {}),
        )

    async def get_expedition_wallet(self, run_id: str) -> WalletDTO:
        result = await self.session.execute(
            select(ResourceBalance.resource_key, ResourceBalance.amount).where(
                ResourceBalance.holder_type == "expedition",
                ResourceBalance.holder_id == run_id,
                ResourceBalance.storage_type == "carried",
                ResourceBalance.amount > 0,
            )
        )
        wallet = WalletDTO()
        for resource_key, amount in result.all():
            key = str(resource_key)
            value = int(amount or 0)
            if value <= 0:
                continue
            bucket = _wallet_bucket(wallet, key)
            bucket[key] = bucket.get(key, 0) + value
        return wallet

    async def save_placements(
        self,
        char_id: int,
        items: dict[str, InventoryRuntimeItemDTO],
        *,
        expedition_run_id: str | None = None,
    ) -> None:
        holder_filters = [
            (ItemPlacement.holder_type == "character") & (ItemPlacement.holder_id == str(char_id)),
        ]
        if expedition_run_id:
            holder_filters.append(
                (ItemPlacement.holder_type == "expedition") & (ItemPlacement.holder_id == expedition_run_id)
            )
        placements = {
            placement.item_id: placement
            for placement in await self.session.scalars(select(ItemPlacement).where(or_(*holder_filters)))
        }

        for item_id, item in items.items():
            placement = placements.get(item_id)
            if placement is None:
                continue
            placement.storage_type = item.placement
            placement.slot = item.slot
        await self.session.flush()

    async def save_item_mechanics(self, items: dict[str, InventoryRuntimeItemDTO]) -> None:
        if not items:
            return
        instances = {
            instance.id: instance
            for instance in await self.session.scalars(select(ItemInstance).where(ItemInstance.id.in_(items)))
        }
        for item_id, item in items.items():
            instance = instances.get(item_id)
            if instance is None:
                continue
            instance.mechanics = dict(item.mechanics)
        await self.session.flush()

    async def _lock_durability(self, char_id: int) -> None:
        # Bound a stalled publisher/writer; timeout is a retryable failure, never an ACK.
        async with asyncio.timeout(_DURABILITY_LOCK_TIMEOUT_SECONDS):
            await self.session.execute(select(func.pg_advisory_xact_lock(_DURABILITY_LOCK_NAMESPACE, char_id)))

    @asynccontextmanager
    async def durability_projection(self, char_id: int) -> AsyncIterator[None]:
        """Fence SQL reread through both Redis publications and receipt marker.

        A separate transaction starts after the authoritative damage commit. Failure
        rolls back only this projection transaction; committed damage remains durable.
        """
        try:
            await self._lock_durability(char_id)
            async with asyncio.timeout(_DURABILITY_PROJECTION_TIMEOUT_SECONDS):
                yield
                await self.session.commit()
        except BaseException:
            # Includes cancellation while waiting, publishing, or committing.
            await self.session.rollback()
            raise

    async def apply_durability_damage(
        self,
        *,
        char_id: int,
        idempotency_key: str,
        payload: dict[str, Any],
        item_ids: list[str],
        expedition_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Own the commit point; never publish cached damage before this returns."""
        try:
            await self._lock_durability(char_id)
            claimed = await self.session.scalar(
                insert(DurabilityApplication)
                .values(character_id=char_id, idempotency_key=idempotency_key, payload=payload, changed=[])
                .on_conflict_do_nothing(index_elements=["character_id", "idempotency_key"])
                .returning(DurabilityApplication.character_id)
            )
            receipt = await self.session.scalar(
                select(DurabilityApplication).where(
                    DurabilityApplication.character_id == char_id,
                    DurabilityApplication.idempotency_key == idempotency_key,
                )
            )
            if claimed is None:
                if receipt.payload != payload:
                    raise ValueError("Idempotency key payload conflict")
                await self.session.commit()
                return {"duplicate": True, "changed": []}

            holders = [(ItemPlacement.holder_type == "character") & (ItemPlacement.holder_id == str(char_id))]
            if expedition_run_id:
                holders.append(
                    (ItemPlacement.holder_type == "expedition") & (ItemPlacement.holder_id == expedition_run_id)
                )
            # Stable lock order prevents deadlocks when distinct events overlap.
            instances = await self.session.scalars(
                select(ItemInstance)
                .join(ItemPlacement, ItemPlacement.item_id == ItemInstance.id)
                .where(ItemInstance.id.in_(item_ids), or_(*holders))
                .order_by(ItemInstance.id)
                .with_for_update(of=ItemInstance)
                .execution_options(populate_existing=True)
            )
            changed: list[dict[str, Any]] = []
            for instance in instances:
                if payload["amount"] <= 0:
                    continue
                mechanics = dict(instance.mechanics or {})
                before = _optional_float(mechanics.get("durability_current"))
                maximum = _optional_float(mechanics.get("durability_max"))
                current = before if before is not None else maximum
                if current is None:
                    continue
                after = max(0.0, round(current - payload["amount"], 4))
                if after == before:
                    continue
                mechanics["durability_current"] = after
                if maximum is not None:
                    mechanics["durability_max"] = maximum
                instance.mechanics = mechanics
                changed.append({"item_id": str(instance.id), "before": current, "after": after})
            receipt.changed = changed
            await self.session.commit()
            return {"duplicate": False, "changed": changed}
        except BaseException:
            await self.session.rollback()
            raise

    async def discard_character_item(
        self,
        char_id: int,
        item_id: str,
        *,
        expedition_run_id: str | None = None,
        reason: str = "inventory_drop",
    ) -> bool:
        holder_filters = [
            (ItemPlacement.holder_type == "character") & (ItemPlacement.holder_id == str(char_id)),
        ]
        if expedition_run_id:
            holder_filters.append(
                (ItemPlacement.holder_type == "expedition") & (ItemPlacement.holder_id == expedition_run_id)
            )
        placement = await self.session.scalar(
            select(ItemPlacement).where(
                ItemPlacement.item_id == item_id,
                or_(*holder_filters),
            )
        )
        if placement is None:
            return False

        self.session.add(
            ItemTransaction(
                item_id=placement.item_id,
                from_holder_type=placement.holder_type,
                from_holder_id=placement.holder_id,
                from_storage_type=placement.storage_type,
                to_holder_type="system",
                to_holder_id=f"discarded:{char_id}",
                to_storage_type="discarded",
                reason=reason,
            )
        )
        placement.holder_type = "system"
        placement.holder_id = f"discarded:{char_id}"
        placement.storage_type = "discarded"
        placement.slot = None
        placement.position_index = None
        placement.locked_by = None
        await self.session.flush()
        return True

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def _wallet_bucket(wallet: WalletDTO, key: str) -> dict[str, int]:
    if key.startswith(_CURRENCY_PREFIXES):
        return wallet.currency
    if key.startswith(_COMPONENT_PREFIXES):
        return wallet.components
    return wallet.resources


def runtime_item_from_instance(instance: ItemInstance, placement: ItemPlacement) -> InventoryRuntimeItemDTO:
    mechanics = dict(instance.mechanics or {})
    metadata = {**dict(instance.metadata_ or {}), **dict(getattr(instance, "appearance", {}) or {})}
    slot = placement.slot or mechanics.get("slot")
    if slot:
        mechanics["slot"] = slot

    valid_slots = mechanics.get("valid_slots")
    if not isinstance(valid_slots, list):
        valid_slots = [slot] if slot else []

    is_unsecured = getattr(placement, "holder_type", "character") == "expedition"
    return InventoryRuntimeItemDTO(
        item_id=str(instance.id),
        base_id=instance.base_id,
        item_type=instance.item_type,
        slot=str(slot) if slot else None,
        valid_slots=[str(value) for value in valid_slots if value],
        placement=placement.storage_type,
        name=instance.name,
        description=instance.description,
        rarity=instance.rarity,
        rarity_tier=instance.rarity_tier,
        quantity=_quantity_from_item(metadata, mechanics),
        sync_state="unsecured" if is_unsecured else "secured",
        is_unsecured=is_unsecured,
        mechanics=mechanics,
        tags=list((instance.generation or {}).get("narrative_tags") or []),
        metadata=metadata,
    )


def _quantity_from_item(metadata: dict[str, Any], mechanics: dict[str, Any]) -> int:
    for raw in (
        metadata.get("quantity"),
        metadata.get("stack_count"),
        metadata.get("count"),
        mechanics.get("quantity"),
        mechanics.get("stack_count"),
        mechanics.get("charges"),
    ):
        if raw is not None:
            try:
                value = int(raw)
            except (TypeError, ValueError):
                continue
            if value > 0:
                return value
    return 1


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
