from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codex_platform.redis_service import RedisService

    from src.backend.features.rift.runtime.hex.generation.builder import HexNodeDTO, HexRiftStateDTO


class HexRiftWorldNotFoundError(RuntimeError):
    pass


class HexRiftWorldStore:
    """Temporary Redis owner for the server-side hex rift graph.

    The stored document is allowed to contain secret node content. Client views
    must be built through ``build_client_view`` so hidden rooms and finish nodes
    are not leaked to the frontend.
    """

    DEFAULT_TTL_SECONDS = 60 * 60
    KEY_PREFIX = "game:rift:hex_world:"
    SCHEMA_VERSION = 1

    def __init__(self, redis: RedisService, *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def build_world_key(self, instance_id: str) -> str:
        return f"{self.KEY_PREFIX}{instance_id}"

    async def save_world(self, state: HexRiftStateDTO, *, seed: str | None = None) -> dict[str, Any]:
        document = self._world_document(state, seed=seed)
        key = self.build_world_key(state.instance_id)
        await self.redis.json_module.set(key, "$", document)
        await self.redis.string.expire(key, self.ttl_seconds)
        return document

    async def get_world(self, instance_id: str) -> dict[str, Any] | None:
        result = await self.redis.json_module.get(self.build_world_key(instance_id), "$")
        doc = self._first(result)
        return dict(doc) if isinstance(doc, dict) else None

    async def require_world(self, instance_id: str) -> dict[str, Any]:
        document = await self.get_world(instance_id)
        if document is None:
            raise HexRiftWorldNotFoundError(f"Hex rift world not found: {instance_id}")
        return document

    async def delete_world(self, instance_id: str) -> None:
        await self.redis.string.delete(self.build_world_key(instance_id))

    async def record_player_position(
        self,
        instance_id: str,
        *,
        current: tuple[int, int],
        previous: tuple[int, int] | None = None,
        reveal: list[tuple[int, int]] | None = None,
    ) -> dict[str, Any]:
        document = await self.require_world(instance_id)
        current_coord = _coord(current)
        previous_coord = _coord(previous) if previous is not None else None
        visited = _unique_coords([*document["player"].get("visited", []), current_coord])
        revealed = _unique_coords([*document["player"].get("revealed", []), *(reveal or [])])
        history = [
            *list(document.get("history") or []),
            {
                "type": "node_entered",
                "coord": current_coord,
                "previous": previous_coord,
                "created_at": time.time(),
            },
        ]

        key = self.build_world_key(instance_id)
        await self.redis.json_module.set(key, "$.player.current", current_coord)
        await self.redis.json_module.set(key, "$.player.previous", previous_coord)
        await self.redis.json_module.set(key, "$.player.visited", visited)
        await self.redis.json_module.set(key, "$.player.revealed", revealed)
        await self.redis.json_module.set(key, "$.history", history)
        await self.redis.string.expire(key, self.ttl_seconds)
        document["player"]["current"] = current_coord
        document["player"]["previous"] = previous_coord
        document["player"]["visited"] = visited
        document["player"]["revealed"] = revealed
        document["history"] = history
        return document

    def build_client_view(self, document: dict[str, Any]) -> dict[str, Any]:
        player = dict(document.get("player") or {})
        revealed = _unique_coords(player.get("revealed") or [])
        visited = _unique_coords(player.get("visited") or [])
        visited_keys = {_coord_key_from_mapping(coord) for coord in visited}
        nodes_by_coord = dict(dict(document.get("world") or {}).get("nodes_by_coord") or {})

        nodes = []
        for coord in revealed:
            key = _coord_key_from_mapping(coord)
            node = nodes_by_coord.get(key)
            if isinstance(node, dict):
                nodes.append(_client_node(node, reveal_content=key in visited_keys))

        return {
            "schema_version": self.SCHEMA_VERSION,
            "instance_id": document["instance_id"],
            "theme": document.get("theme", ""),
            "scale_key": document.get("scale_key", ""),
            "difficulty_key": document.get("difficulty_key", ""),
            "scheme_key": document.get("scheme_key", ""),
            "available_scheme_keys": list(document.get("available_scheme_keys") or []),
            "layout_pattern_catalog": list(document.get("layout_pattern_catalog") or []),
            "layout_template_debug": dict(document.get("layout_template_debug") or {}),
            "layout_debug": dict(document.get("layout_debug") or {}),
            "grid": dict(dict(document.get("world") or {}).get("grid") or {}),
            "start": dict(document.get("start") or {}),
            "current": dict(player.get("current") or {}),
            "previous": dict(player.get("previous") or {}) if player.get("previous") else None,
            "floor": int(player.get("floor") or 1),
            "visited": visited,
            "revealed": revealed,
            "nodes": nodes,
            "combat_prompt": player.get("combat_prompt"),
        }

    def _world_document(self, state: HexRiftStateDTO, *, seed: str | None) -> dict[str, Any]:
        nodes_by_coord = {_coord_key((node.x, node.y)): _node_document(node) for node in state.nodes}
        return {
            "schema_version": self.SCHEMA_VERSION,
            "instance_id": state.instance_id,
            "theme": state.theme,
            "scale_key": state.scale_key,
            "difficulty_key": state.difficulty_key,
            "scheme_key": state.scheme_key,
            "seed": seed,
            "available_scheme_keys": list(state.available_scheme_keys),
            "layout_pattern_catalog": list(state.layout_pattern_catalog),
            "layout_template_debug": dict(state.layout_template_debug),
            "layout_debug": dict(state.layout_debug),
            "start": _coord((state.start_x, state.start_y)),
            "finish": _coord((state.finish_x, state.finish_y)),
            "world": {
                "grid": {"width": state.width, "height": state.height},
                "nodes_by_coord": nodes_by_coord,
            },
            "player": {
                "current": _coord((state.current_x, state.current_y)),
                "previous": _coord((state.previous_x, state.previous_y))
                if state.previous_x is not None and state.previous_y is not None
                else None,
                "floor": state.floor,
                "visited": [_coord(value) for value in state.visited],
                "revealed": [_coord(value) for value in state.revealed],
                "combat_prompt": state.combat_prompt.model_dump(mode="json") if state.combat_prompt else None,
            },
            "history": [],
        }

    @staticmethod
    def _first(result: Any) -> Any:
        if isinstance(result, list):
            return result[0] if result else None
        return result


def _node_document(node: HexNodeDTO) -> dict[str, Any]:
    return node.model_dump(mode="json")


def _client_node(node: dict[str, Any], *, reveal_content: bool) -> dict[str, Any]:
    if reveal_content:
        payload = dict(node)
        payload["visual_state"] = "revealed"
        return payload
    return {
        "x": int(node["x"]),
        "y": int(node["y"]),
        "tile_index": None,
        "asset_path": "",
        "edges": list(node.get("edges") or []),
        "is_walkable": bool(node.get("is_walkable")),
        "title": "Unknown rift shard" if bool(node.get("is_walkable")) else "Void",
        "description": "",
        "graph_role": "unknown" if bool(node.get("is_walkable")) else "void",
        "path_layer": "",
        "visibility": "known",
        "content_slot": "unknown",
        "content_subtype": "unknown",
        "overlay_key": "",
        "visual_state": "hidden_shell",
    }


def _coord(value: tuple[int, int] | list[int] | dict[str, Any]) -> dict[str, int]:
    if isinstance(value, dict):
        return {"x": int(value["x"]), "y": int(value["y"])}
    return {"x": int(value[0]), "y": int(value[1])}


def _unique_coords(values: list[tuple[int, int] | list[int] | dict[str, Any]]) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    seen: set[str] = set()
    for value in values:
        coord = _coord(value)
        key = _coord_key_from_mapping(coord)
        if key in seen:
            continue
        seen.add(key)
        result.append(coord)
    return result


def _coord_key(value: tuple[int, int]) -> str:
    return f"{int(value[0])}:{int(value[1])}"


def _coord_key_from_mapping(value: dict[str, Any]) -> str:
    return f"{int(value['x'])}:{int(value['y'])}"
