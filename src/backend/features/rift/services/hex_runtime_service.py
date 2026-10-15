from __future__ import annotations

import uuid
from typing import Literal

from src.backend.features.rift.dto.screen import (
    RiftCombatPromptActionDTO,
    RiftCombatPromptDTO,
    RiftCombatPromptEnemyDTO,
)
from src.backend.features.rift.runtime.hex.generation.builder import (
    DEFAULT_LAYOUT_SCHEME_KEY,
    RANDOM_LAYOUT_SCHEME_KEY,
    HexNodeDTO,
    HexRiftStateDTO,
    build_hex_rift_state,
    get_hex_neighbors,
)

CLEARED_COMBAT_TILE_INDEX = 402
HEX_RIFT_INSTANCES: dict[str, HexRiftStateDTO] = {}


class HexRiftRuntimeError(RuntimeError):
    pass


class HexRiftInstanceNotFoundError(HexRiftRuntimeError):
    pass


class HexRiftInvalidActionError(HexRiftRuntimeError):
    pass


class HexRiftRuntimeService:
    """Temporary shared service for the new hex rift dev/runtime path."""

    def __init__(self, instances: dict[str, HexRiftStateDTO] | None = None) -> None:
        self.instances = instances if instances is not None else HEX_RIFT_INSTANCES

    def start(
        self,
        *,
        instance_id: str | None = None,
        seed: str | None = None,
        scale_key: str = "solo",
        difficulty_key: str = "easy",
        scheme_key: str | None = None,
    ) -> HexRiftStateDTO:
        resolved_instance_id = instance_id or f"hex-rift-{uuid.uuid4().hex[:8]}"
        resolved_scheme_key = (
            None if scheme_key == RANDOM_LAYOUT_SCHEME_KEY else scheme_key or DEFAULT_LAYOUT_SCHEME_KEY
        )
        seed_attempts = [seed] if seed is not None else [f"seed-{uuid.uuid4().hex[:6]}" for _ in range(8)]
        last_error: RuntimeError | None = None
        for resolved_seed in seed_attempts:
            try:
                state = build_hex_rift_state(
                    resolved_instance_id,
                    resolved_seed,
                    scale_key=scale_key,
                    difficulty_key=difficulty_key,
                    scheme_key=resolved_scheme_key,
                )
                break
            except RuntimeError as exc:
                last_error = exc
        else:
            if last_error is not None:
                raise last_error
            raise RuntimeError("Could not build hex rift state")

        state.floor = 1
        self.instances[resolved_instance_id] = state
        return state

    def get_or_create(self, instance_id: str) -> HexRiftStateDTO:
        if instance_id not in self.instances:
            self.start(instance_id=instance_id, seed=f"auto-{instance_id}")
        return self.instances[instance_id]

    def client_view(self, state: HexRiftStateDTO, *, show_all_map: bool = False) -> HexRiftStateDTO:
        if show_all_map:
            return state

        visible_coords = set(state.revealed)
        visible_coords.add((state.current_x, state.current_y))
        return state.model_copy(
            update={
                "nodes": [node for node in state.nodes if (node.x, node.y) in visible_coords],
            },
        )

    def get(self, instance_id: str) -> HexRiftStateDTO | None:
        return self.instances.get(instance_id)

    def require(self, instance_id: str) -> HexRiftStateDTO:
        try:
            return self.instances[instance_id]
        except KeyError as exc:
            raise HexRiftInstanceNotFoundError(f"Hex rift instance not found: {instance_id}") from exc

    def move(self, instance_id: str, *, target_x: int, target_y: int) -> HexRiftStateDTO:
        state = self.require(instance_id)
        if state.combat_prompt is not None:
            raise HexRiftInvalidActionError("Cannot move: resolve active encounter first")

        current = (state.current_x, state.current_y)
        target = (target_x, target_y)
        if target not in get_hex_neighbors(current[0], current[1], state.width, state.height):
            raise HexRiftInvalidActionError("Target node is not adjacent to current node")

        target_node = self._node_at(state, target_x, target_y)
        if target_node is None or not target_node.is_walkable:
            raise HexRiftInvalidActionError("Target node is not walkable (void/cosmos)")

        state.previous_x = current[0]
        state.previous_y = current[1]
        state.current_x = target_x
        state.current_y = target_y

        if target not in state.visited:
            state.visited.append(target)
        state.revealed = self._revealed_from_visited(state)

        if target_node.content_slot in {"guard_before_transition", "combat_room"}:
            state.combat_prompt = self.create_mock_combat_prompt(target_node.tile_index)

        self.instances[instance_id] = state
        return state

    def resolve_combat(self, instance_id: str, *, action: Literal["fight", "escape"]) -> HexRiftStateDTO:
        state = self.require(instance_id)
        if state.combat_prompt is None:
            raise HexRiftInvalidActionError("No active encounter to resolve")

        if action == "fight":
            self._resolve_fight(state)
        elif action == "escape":
            self._resolve_escape(state)

        self.instances[instance_id] = state
        return state

    def next_floor(self, instance_id: str) -> HexRiftStateDTO:
        state = self.require(instance_id)
        finish_node = self._node_at(state, state.finish_x, state.finish_y)
        if finish_node is None or finish_node.tile_index != CLEARED_COMBAT_TILE_INDEX:
            raise HexRiftInvalidActionError("Exit guard not defeated or exit tile not found")
        if state.current_x != state.finish_x or state.current_y != state.finish_y:
            raise HexRiftInvalidActionError("Player is not at the exit node")
        if state.floor >= 3:
            raise HexRiftInvalidActionError("Already on the maximum floor")

        next_floor = state.floor + 1
        new_state = build_hex_rift_state(instance_id, f"seed-{instance_id}-floor-{next_floor}")
        new_state.floor = next_floor
        self.instances[instance_id] = new_state
        return new_state

    @staticmethod
    def neighbors(x: int, y: int, width: int, height: int) -> list[tuple[int, int] | None]:
        return get_hex_neighbors(x, y, width, height)

    @staticmethod
    def create_mock_combat_prompt(tile_index: int) -> RiftCombatPromptDTO:
        if tile_index == 3:
            title = "Страж Разлома"
            description = "Путь на следующий уровень преграждает могущественный Страж Разлома! Вы можете отступить, чтобы подготовиться."
            enemies = [
                RiftCombatPromptEnemyDTO(
                    name="Хранитель Осколка",
                    member_tier=3,
                    hp_percent=100,
                    role="boss",
                    description="Древний кристаллический голем, защищающий переход.",
                )
            ]
            allow_escape = True
        elif tile_index == 15:
            title = "Охраняемый сундук"
            description = "Этот сундук запечатан магией и охраняется прислужниками! Побег невозможен!"
            enemies = [
                RiftCombatPromptEnemyDTO(
                    name="Древний Мимик",
                    member_tier=2,
                    hp_percent=100,
                    role="boss",
                    description="Сундук с зубами и жаждой золота.",
                )
            ]
            for index in range(1, 4):
                enemies.append(
                    RiftCombatPromptEnemyDTO(
                        name=f"Скелет-страж #{index}",
                        member_tier=1,
                        hp_percent=100,
                        role="minion",
                        description="Ржавый скелет.",
                    )
                )
            allow_escape = False
        elif tile_index == 10:
            title = "Заброшенный лагерь"
            description = "В лагере обосновались мародеры Пещеры Разлома! Вы не можете сбежать!"
            enemies = [
                RiftCombatPromptEnemyDTO(
                    name="Главарь мародеров",
                    member_tier=2,
                    hp_percent=100,
                    role="boss",
                    description="Опытный разбойник.",
                ),
                RiftCombatPromptEnemyDTO(
                    name="Мародер-лучник",
                    member_tier=1,
                    hp_percent=100,
                    role="damage",
                    description="Целится вам в колено.",
                ),
            ]
            allow_escape = False
        else:
            title = "Древний Магический Круг"
            description = "Руны вспыхнули фиолетовым огнем, призвав Призрака Разлома! Вы не можете сбежать!"
            enemies = [
                RiftCombatPromptEnemyDTO(
                    name="Призрак Разлома",
                    member_tier=3,
                    hp_percent=100,
                    role="boss",
                    description="Бесплотный дух, пожирающий энергию.",
                )
            ]
            allow_escape = False

        return RiftCombatPromptDTO(
            source="rift_transition",
            title=title,
            description=description,
            enemies=enemies,
            actions=[
                RiftCombatPromptActionDTO(
                    id="fight",
                    label="Вступить в бой",
                    action="attack",
                    style="danger",
                    is_active=True,
                )
            ],
            metadata={"travel_id": "mock-travel", "allow_escape": allow_escape},
        )

    def _resolve_fight(self, state: HexRiftStateDTO) -> None:
        state.combat_prompt = None
        current_node = self._node_at(state, state.current_x, state.current_y)
        if current_node is None:
            return
        current_node.tile_index = CLEARED_COMBAT_TILE_INDEX
        current_node.asset_path = "tiles/tile_402.png"
        current_node.title = "Очищенный каменный пол"
        current_node.description = "Опасность миновала. Ошметки поверженных врагов лежат на каменных плитах."

        if state.current_x == state.finish_x and state.current_y == state.finish_y and state.floor == 3:
            current_node.description = (
                "Вы очистили Сердце Разлома! Все уровни пройдены. Вы можете сгенерировать новый разлом."
            )

    def _resolve_escape(self, state: HexRiftStateDTO) -> None:
        if state.combat_prompt is None:
            return
        allow_escape = state.combat_prompt.metadata.get("allow_escape", True)
        if not allow_escape:
            raise HexRiftInvalidActionError("Cannot escape from this combat encounter!")

        state.combat_prompt = None
        if state.previous_x is not None and state.previous_y is not None:
            state.current_x = state.previous_x
            state.current_y = state.previous_y
            state.revealed = self._revealed_from_visited(state)

    @staticmethod
    def _node_at(state: HexRiftStateDTO, x: int, y: int) -> HexNodeDTO | None:
        return next((node for node in state.nodes if node.x == x and node.y == y), None)

    @staticmethod
    def _revealed_from_visited(state: HexRiftStateDTO) -> list[tuple[int, int]]:
        revealed = set(state.visited)
        for coord in state.visited:
            for neighbor in get_hex_neighbors(coord[0], coord[1], state.width, state.height):
                if neighbor is not None:
                    revealed.add(neighbor)
        return list(revealed)
