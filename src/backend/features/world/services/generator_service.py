from typing import Any

from loguru import logger as log

from src.backend.features.world.integrations import WorldDataIntegration
from src.backend.features.world.loaders.village_loader import VillageLoader
from src.backend.features.world.resources.static.d4_city_map import build_d4_city_map_node_metadata
from src.backend.features.world.resources.static.start_village import STATIC_LOCATIONS
from src.backend.features.world.runtime.config import HUB_CENTER, REGION_ROWS, REGION_SIZE, ZONE_SIZE
from src.backend.features.world.runtime.geography import WorldGeographyService
from src.backend.features.world.runtime.profiles import (
    build_habitat_population_profile_payload,
    build_region_profile,
    build_zone_profile,
)
from src.backend.features.world.runtime.theme import WorldThemeService
from src.backend.features.world.runtime.threat import ThreatService
from src.backend.features.world.services.navigation_service import WorldNavigationService

D4_FALLBACK_TITLE = "Руины Старой Столицы"
D4_FALLBACK_DESCRIPTION = (
    "Мертвый квартал древней столицы. Координата описывает не размер, а отдельную "
    "навигационную область: улицу, площадь, двор или фрагмент квартала."
)


D4_NARRATIVE_CONTEXT = (
    "D4 is the ruined former capital around the protected city hub. Treat city_ruins here as old capital outskirts, "
    "collapsed districts, sealed roads, monolith walls, and scavenged streets around a safe portal-shielded center."
)
D4_DISTRICT_PROFILES: dict[str, dict[str, Any]] = {
    "D4_0_0": {
        "name": "Северо-западный бастионный квартал",
        "role": "outer wall, old guard walks, broken defensive yards",
        "tags": ["bastion", "outer_wall", "guard_ruins", "stasis_pressure"],
    },
    "D4_1_0": {
        "name": "Северный тракт и ворота",
        "role": "main road to the sealed northern gate, processional ruins",
        "tags": ["north_gate", "ancient_highway", "processional_road", "stasis_pressure"],
    },
    "D4_2_0": {
        "name": "Северо-восточные обсерватории",
        "role": "collapsed towers, sightlines over the city, silent signal stones",
        "tags": ["observatory_ruins", "signal_stones", "high_vistas", "biomass_creep"],
    },
    "D4_0_1": {
        "name": "Западный рынок обломков",
        "role": "scavenged stalls, gravity-twisted plazas, side streets",
        "tags": ["broken_market", "scavenger_marks", "gravity_shear", "side_streets"],
    },
    "D4_2_1": {
        "name": "Восточный жилой разлом",
        "role": "collapsed residences, overgrown courtyards, mutation pressure",
        "tags": ["residential_ruins", "overgrown_courtyards", "biomass_pressure", "cracked_halls"],
    },
    "D4_0_2": {
        "name": "Юго-западные мастерские",
        "role": "dead workshops, cracked conduits, heavy stone workrooms",
        "tags": ["artisan_ruins", "dead_workshops", "gravity_shear", "crystal_conduits"],
    },
    "D4_1_2": {
        "name": "Южный тракт и врата",
        "role": "main road to the sealed southern gate, heated stone and dust",
        "tags": ["south_gate", "ancient_highway", "plasma_pressure", "sealed_road"],
    },
    "D4_2_2": {
        "name": "Юго-восточные святилища",
        "role": "broken shrines, old civic ritual spaces, fire-lit mineral scars",
        "tags": ["shrine_ruins", "ritual_plazas", "plasma_pressure", "gold_veins"],
    },
}
D4_RIFT_PROFILES: dict[tuple[int, int], dict[str, Any]] = {
    (47, 47): {
        "id": "d4_rift_rat_king",
        "family_id": "rat_swarm",
        "title": "Разлом Крысиного Короля",
        "background_key": "d4_rift_rat_king",
        "boss_archetype": "rat_king",
        "context_tags": [
            "d4_city_rift",
            "d4_rift_rat_king",
            "rat_king_pressure",
            "undercity_seep",
        ],
        "description": (
            "В северо-западном квартале разлом сидит в круглом провале старого двора. К нему ведут "
            "треснувшие плиты и низкие арки, а из нижних щелей тянет влажным камнем. Мусор, кости "
            "и сорванные знаки вокруг провала складываются в грубую корону Крысиного Короля."
        ),
    },
    (57, 48): {
        "id": "d4_rift_wolf_breach",
        "family_id": "wolf_pack",
        "title": "Волчий Пролом",
        "background_key": "d4_rift_wolf_breach",
        "boss_archetype": "alpha_wolf",
        "context_tags": [
            "d4_city_rift",
            "d4_rift_wolf_breach",
            "wolf_breach_pressure",
            "overgrown_kennel",
        ],
        "description": (
            "На северо-востоке пролом открылся в чаше бывшего зрительного двора. Ступени и "
            "сломанные ложи образуют охотничий круг, где эхо шагов отвечает коротким воем. "
            "С востока к месту подходят узкие проходы между башенными руинами."
        ),
    },
    (47, 57): {
        "id": "d4_rift_bandit_barricade",
        "family_id": "bandit_gang",
        "title": "Разлом Баррикады",
        "background_key": "d4_rift_bandit_barricade",
        "boss_archetype": "bandit_warlord",
        "context_tags": [
            "d4_city_rift",
            "d4_rift_bandit_barricade",
            "bandit_barricade_pressure",
            "scavenger_barricade",
        ],
        "description": (
            "В юго-западных мастерских черная шахта разорвала каменную площадку между рухнувшими "
            "корпусами. Вокруг нее собраны щиты, трофейные знаки и грубые баррикады. Это не крепость, "
            "а удерживаемый узел давления, из которого бандиты контролируют ближайшие проходы."
        ),
    },
    (57, 58): {
        "id": "d4_rift_goblin_scrapyard",
        "family_id": "goblin_tribe",
        "title": "Разлом Свалки",
        "background_key": "d4_rift_goblin_scrapyard",
        "boss_archetype": "scrap_king",
        "context_tags": [
            "d4_city_rift",
            "d4_rift_goblin_scrapyard",
            "goblin_scrapyard_pressure",
            "collapsed_workshop",
        ],
        "description": (
            "В юго-восточном святилищном блоке разлом дрожит между двумя синими колодцами старого "
            "механизма. Вокруг копятся железо, битое стекло, провода и кривые тотемы, будто сама "
            "трещина выбрасывает хлам наружу. Гоблины держат здесь свалку и сторожевой двор."
        ),
    },
}
D4_CORNER_ZONE_TAGS: dict[str, list[str]] = {
    "D4_0_0": ["d4_corner_pressure", "d4_rift_rat_king", "rat_king_pressure", "undercity_seep"],
    "D4_2_0": ["d4_corner_pressure", "d4_rift_wolf_breach", "wolf_breach_pressure", "overgrown_kennel"],
    "D4_0_2": ["d4_corner_pressure", "d4_rift_bandit_barricade", "bandit_barricade_pressure", "scavenger_barricade"],
    "D4_2_2": ["d4_corner_pressure", "d4_rift_goblin_scrapyard", "goblin_scrapyard_pressure", "collapsed_workshop"],
}


class WorldGenerator:
    """Builds deterministic world geometry and loads prepared static content."""

    def __init__(self, data: WorldDataIntegration) -> None:
        self.data = data
        self.village_loader = VillageLoader(data)

    async def run(self, mode: str = "test") -> None:
        """Refresh static content, optionally creating the complete world shell."""
        if mode not in {"test", "full"}:
            raise ValueError(f"Unsupported world generation mode: {mode}")
        log.bind(mode=mode).info("WorldGenerationStarted")
        if mode == "full":
            await self._generate_world_shell()
        await self.village_loader.load_village(STATIC_LOCATIONS)

    async def _generate_d4_capital(self) -> None:
        """Generate D4 city gameplay nodes: playable 15x15 inside a loadable 17x17 visual map."""
        region_id = "D4"
        d4_row_idx = REGION_ROWS.index("D")
        min_x = (4 - 1) * REGION_SIZE
        min_y = d4_row_idx * REGION_SIZE
        max_x = min_x + REGION_SIZE - 1
        max_y = min_y + REGION_SIZE - 1
        mid_x = min_x + REGION_SIZE // 2
        mid_y = min_y + REGION_SIZE // 2

        region_influence = ThreatService.describe(mid_x, mid_y)
        region_geography = WorldGeographyService.describe_zone(mid_x, mid_y)
        region_profile = build_region_profile(
            region_id=region_id,
            center_x=mid_x,
            center_y=mid_y,
            geography=region_geography,
            influence=region_influence,
        )

        await self.data.upsert_region(
            region_id,
            climate_tags=list(region_profile.region_tags),
            context={"region_profile": region_profile.model_dump()},
            biome_id=region_profile.biome_id,
            biome_mix=region_profile.biome_mix,
            region_archetype=region_profile.region_archetype,
            tier_min=region_profile.tier_band[0],
            tier_max=region_profile.tier_band[1],
            navigation_profile_id=region_profile.navigation_profile_id,
            population_profile=build_habitat_population_profile_payload(region_profile),
            anchor_influence=region_profile.anchor_influence,
            is_locked_frontier=region_profile.is_locked_frontier,
        )

        zones_per_region = REGION_SIZE // ZONE_SIZE
        for zx in range(zones_per_region):
            for zy in range(zones_per_region):
                is_hub_zone = zx == 1 and zy == 1
                zone_id = f"{region_id}_{zx}_{zy}"
                zone_center_x = min_x + zx * ZONE_SIZE + ZONE_SIZE // 2
                zone_center_y = min_y + zy * ZONE_SIZE + ZONE_SIZE // 2
                zone_influence = ThreatService.describe(zone_center_x, zone_center_y)
                zone_tier = self._d4_zone_tier(zone_id, is_hub_zone=is_hub_zone)
                district_profile = None if is_hub_zone else D4_DISTRICT_PROFILES.get(zone_id)
                context_tags = [] if is_hub_zone else self._d4_zone_context_tags(zone_id)
                zone_profile = build_zone_profile(region_profile=region_profile, zone_id=zone_id, zx=zx, zy=zy)
                await self.data.upsert_zone(
                    zone_id,
                    region_id=region_id,
                    biome_id=region_profile.biome_id,
                    tier=zone_tier,
                    zone_archetype=zone_profile.zone_archetype,
                    navigation_profile_id=zone_profile.navigation_profile_id,
                    landmark_profile=zone_profile.landmark_profile,
                    population_tags=list(zone_profile.population_tags),
                    flags={
                        "is_safe_zone": is_hub_zone,
                        "system_connect": is_hub_zone,
                        "is_hub": is_hub_zone,
                        "portal_shield": is_hub_zone,
                        "is_old_capital": True,
                        "narrative_context": D4_NARRATIVE_CONTEXT,
                        "district_profile": district_profile,
                        "context_tags": context_tags,
                        "threat_tier": zone_tier,
                        "anchor_influence": {
                            "threat": zone_influence.threat,
                            "tier": zone_influence.tier,
                            "dominant_anchor": zone_influence.dominant_anchor,
                            "tags": zone_influence.tags,
                            "is_inside_city_shield": zone_influence.is_inside_city_shield,
                        },
                    },
                )

        await self.data.flush()

        nodes: list[dict[str, Any]] = []
        road_cells = self._build_d4_road_cells(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
        existing_nodes = await self.data.get_nodes_in_rect(min_x, min_y, REGION_SIZE, REGION_SIZE)
        existing_by_coord = {(node.x, node.y): node for node in existing_nodes}
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                node = self._build_d4_node(
                    x=x,
                    y=y,
                    min_x=min_x,
                    min_y=min_y,
                    max_x=max_x,
                    max_y=max_y,
                    mid_x=mid_x,
                    mid_y=mid_y,
                    road_cells=road_cells,
                    region_profile=region_profile,
                )
                self._preserve_existing_d4_content(node, existing_by_coord.get((x, y)))
                nodes.append(node)

        await self.data.bulk_upsert_nodes(nodes)
        log.bind(node_count=len(nodes)).info("WorldD4CapitalGenerated")

    def _build_d4_node(
        self,
        *,
        x: int,
        y: int,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        mid_x: int,
        mid_y: int,
        road_cells: set[tuple[int, int]],
        region_profile: Any,
    ) -> dict[str, Any]:
        local_x = x - min_x
        local_y = y - min_y
        zone_id = f"D4_{local_x // ZONE_SIZE}_{local_y // ZONE_SIZE}"
        zx = local_x // ZONE_SIZE
        zy = local_y // ZONE_SIZE
        zone_profile = build_zone_profile(region_profile=region_profile, zone_id=zone_id, zx=zx, zy=zy)
        is_hub = self._is_d4_hub_node(x, y)
        is_boundary = x in (min_x, max_x) or y in (min_y, max_y)
        is_outer_gate = is_boundary and (x == mid_x or y == mid_y)
        is_outer_wall = is_boundary and not is_outer_gate
        has_road = (x, y) in road_cells
        travel_cost = 1.0 if is_hub else 1.25
        gated_exits: dict[str, Any] = {}
        route: dict[str, Any] | None = None

        terrain_type = "city_ruins"
        tags = ["ancient_city", "city_ruins"]
        title = D4_FALLBACK_TITLE
        description = D4_FALLBACK_DESCRIPTION
        flags: dict[str, Any] = {
            "is_active": True,
            "is_safe_zone": is_hub,
            "system_connect": is_hub,
            "is_old_capital": True,
            "is_passable": True,
            "threat_tier": 0 if is_hub else self._d4_node_tier(x, y, zone_id=zone_id, has_road=has_road),
        }
        context_tags = [] if is_hub else self._d4_node_context_tags(x, y, zone_id=zone_id, has_road=has_road)

        if is_hub:
            terrain_type = "ancient_pavement"
            tags.extend(["hub_district", "safe_zone"])
            title = "Внутренний район Цитадели"
            description = "Безопасный внутренний район старой столицы под защитой портального щита."
            travel_cost = 1.0

        if is_outer_wall:
            blocked_exits = self._d4_boundary_blocked_exits(
                x=x, y=y, min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y
            )
            terrain_type = "outer_monolith_wall_walk"
            tags.extend(["outer_monolith_wall", "wall_walk", "region_boundary"])
            title = "Ход внешней монолитной стены"
            description = (
                "Край старой столицы здесь занят широкой монолитной стеной. По каменному ходу можно "
                "двигаться вдоль периметра, но наружная сторона закрыта неприступным обрывом кладки."
            )
            flags.update(
                {
                    "boundary_features": self._d4_boundary_features(
                        blocked_exits,
                        kind="outer_monolith_wall",
                        state="sealed",
                        tags=["monolithic_wall", "old_capital_outer_wall", "wall_walk"],
                    ),
                }
            )
            travel_cost = 1.0

        if is_outer_gate:
            direction = self._d4_gate_direction(x=x, y=y, min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
            gated_exits = {
                direction: {
                    "kind": "outer_city_gate",
                    "state": "locked",
                    "unlock_condition": "world_gate_unlock",
                    "tags": ["city_gate", "sealed_gate", "old_capital_outer_wall"],
                }
            }
            terrain_type = "city_gate_outer"
            tags.extend(["gate", "road", "locked_exit"])
            title = f"{self._ru_direction(direction)} внешние ворота D4"
            description = "Ворота в стене старой столицы. Проход существует, но на старте заблокирован."
            flags.update(
                {
                    "is_gate": True,
                    "gate_direction": direction,
                    "exit_locked": True,
                    "unlock_condition": "world_gate_unlock",
                    "boundary_features": {
                        direction: {
                            "kind": "outer_city_gate",
                            "state": "locked",
                            "tags": ["city_gate", "sealed_gate", "old_capital_outer_wall"],
                        }
                    },
                }
            )
            travel_cost = 1.0

        if has_road:
            terrain_type = "ruin_road_main" if terrain_type == "city_ruins" else terrain_type
            tags.extend(["road", "ancient_highway"])
            route = {
                "type": "ancient_highway",
                "role": "hub_to_outer_gate",
                "tags": ["road", "ancient_highway", "main_route"],
            }

        influence = ThreatService.describe(x, y)
        district_profile = None if is_hub else D4_DISTRICT_PROFILES.get(zone_id)
        rift_profile = None if is_hub else D4_RIFT_PROFILES.get((x, y))
        if rift_profile:
            title = str(rift_profile["title"])
            description = str(rift_profile["description"])
            terrain_type = "city_rift"
            tags.extend(["rift", "pressure_source", *rift_profile["context_tags"]])
            flags.update(
                {
                    "is_rift": True,
                    "rift_profile": rift_profile,
                    "gate_lock_source": True,
                    "background_key": rift_profile["background_key"],
                }
            )
            travel_cost = 1.5
        flags["anchor_influence"] = {
            "threat": influence.threat,
            "tier": influence.tier,
            "dominant_anchor": influence.dominant_anchor,
            "tags": influence.tags,
            "is_inside_city_shield": influence.is_inside_city_shield,
        }
        flags["narrative_context"] = D4_NARRATIVE_CONTEXT
        flags["context_tags"] = context_tags
        flags["world_theme"] = WorldThemeService.build(x, y, loc_id=f"{x}_{y}").model_dump(mode="json")
        flags["city_map"] = build_d4_city_map_node_metadata(x, y)
        if district_profile:
            flags["district_key"] = zone_id
            flags["district_profile"] = district_profile

        node_type = self._d4_node_type(
            x=x,
            y=y,
            is_hub=is_hub,
            is_rift=bool(rift_profile),
            is_outer_gate=is_outer_gate,
            is_outer_wall=is_outer_wall,
            has_road=has_road,
            zone_archetype=zone_profile.zone_archetype,
        )
        if node_type == "buildable_plot":
            flags["buildable"] = True
            flags["buildable_kind"] = "house_plot"
            flags["construction_tags"] = ["ruin_foundation", "old_capital_quarter"]
        blocked_exits = self._d4_movement_blocked_exits(
            x=x,
            y=y,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            mid_x=mid_x,
            mid_y=mid_y,
            road_cells=road_cells,
            is_outer_gate=is_outer_gate,
        )
        movement_profile = self._build_node_movement_profile(
            navigation_profile_id=zone_profile.navigation_profile_id,
            zone_archetype=zone_profile.zone_archetype,
            node_type=node_type,
            is_passable=bool(flags.get("is_passable", True)),
            has_road=has_road,
            travel_cost=travel_cost,
            blocked_exits=blocked_exits,
            gated_exits=gated_exits,
            route=route,
        )

        return {
            "x": x,
            "y": y,
            "zone_id": zone_id,
            "biome_id": "city_ruins",
            "node_type": node_type,
            "terrain_type": terrain_type,
            "navigation_profile_id": zone_profile.navigation_profile_id,
            "buildable_kind": flags.get("buildable_kind"),
            "landmark_profile": zone_profile.landmark_profile if rift_profile or is_outer_gate else None,
            "movement_profile": movement_profile,
            "background_key": rift_profile["background_key"] if rift_profile else None,
            "background_pool_key": "d4_city_rift" if rift_profile else "d4_city_ruins",
            "visual_overrides": {},
            "services": [],
            "content": {
                "title": title,
                "description": description,
                "environment_tags": list(dict.fromkeys([*tags, *context_tags, "former_capital_ruins"])),
            },
            "is_active": True,
            "flags": flags,
        }

    @staticmethod
    def _preserve_existing_d4_content(node: dict[str, Any], existing_node: Any | None) -> None:
        if existing_node is None:
            return
        if (node.get("flags") or {}).get("is_rift"):
            return
        if (node["x"], node["y"]) in STATIC_LOCATIONS:
            return

        existing_content = existing_node.content if isinstance(existing_node.content, dict) else {}
        if not existing_content:
            return

        existing_title = existing_content.get("title")
        existing_description = existing_content.get("description")
        is_fallback = existing_title == D4_FALLBACK_TITLE and existing_description == D4_FALLBACK_DESCRIPTION
        if is_fallback:
            return

        content = dict(node.get("content") or {})
        content.update(existing_content)
        node["content"] = content

    @staticmethod
    def _build_d4_road_cells(*, min_x: int, min_y: int, max_x: int, max_y: int) -> set[tuple[int, int]]:
        hub_x = HUB_CENTER["x"]
        hub_y = HUB_CENTER["y"]
        return {
            *((x, hub_y) for x in range(min_x, max_x + 1)),
            *((hub_x, y) for y in range(min_y, max_y + 1)),
        }

    @staticmethod
    def _is_d4_hub_node(x: int, y: int) -> bool:
        return 50 <= x <= 54 and 50 <= y <= 54

    @staticmethod
    def _d4_zone_tier(zone_id: str, *, is_hub_zone: bool) -> int:
        if is_hub_zone:
            return 0
        return 1

    @staticmethod
    def _d4_zone_context_tags(zone_id: str) -> list[str]:
        tags = ["d4_city_ruins"]
        tags.extend(D4_CORNER_ZONE_TAGS.get(zone_id, []))
        if zone_id not in D4_CORNER_ZONE_TAGS:
            tags.append("d4_tier0_ruined_streets")
        return list(dict.fromkeys(tags))

    @staticmethod
    def _d4_node_tier(x: int, y: int, *, zone_id: str, has_road: bool) -> int:
        if (x, y) in D4_RIFT_PROFILES:
            return 2
        return 1

    @staticmethod
    def _d4_node_context_tags(x: int, y: int, *, zone_id: str, has_road: bool) -> list[str]:
        tags = ["d4_city_ruins"]
        rift_profile = D4_RIFT_PROFILES.get((x, y))
        if rift_profile:
            tags.extend(rift_profile["context_tags"])
            return list(dict.fromkeys(tags))
        if has_road:
            tags.append("d4_tier0_gate_cross")
        elif zone_id in D4_CORNER_ZONE_TAGS:
            tags.extend(D4_CORNER_ZONE_TAGS[zone_id])
        else:
            tags.extend(["d4_tier0_ruined_streets", "d4_tier0_scavenger_route"])
        return list(dict.fromkeys(tags))

    @staticmethod
    def _d4_node_type(
        *,
        x: int,
        y: int,
        is_hub: bool,
        is_rift: bool,
        is_outer_gate: bool,
        is_outer_wall: bool,
        has_road: bool,
        zone_archetype: str,
    ) -> str:
        if is_rift:
            return "rift"
        if is_hub:
            return "hub"
        if is_outer_gate:
            return "sealed_gate"
        if is_outer_wall:
            return "outer_wall_walk"
        if has_road:
            return "main_road"
        if zone_archetype == "corner_rift_district":
            return "ruined_quarter"
        if x % 2 == 0 and y % 2 == 0:
            return "buildable_plot"
        return "side_street"

    @staticmethod
    def _build_node_movement_profile(
        *,
        navigation_profile_id: str,
        zone_archetype: str,
        node_type: str,
        is_passable: bool,
        has_road: bool,
        travel_cost: float,
        blocked_exits: Any = None,
        gated_exits: Any = None,
        route: Any = None,
    ) -> dict[str, Any]:
        return {
            "navigation_profile_id": navigation_profile_id,
            "zone_archetype": zone_archetype,
            "node_type": node_type,
            "is_passable": is_passable,
            "has_road": has_road,
            "travel_cost": max(1.0, travel_cost),
            "blocked_exits": list(blocked_exits) if isinstance(blocked_exits, list) else [],
            "gated_exits": dict(gated_exits) if isinstance(gated_exits, dict) else {},
            "route": dict(route) if isinstance(route, dict) else {},
        }

    @staticmethod
    def _d4_gate_direction(*, x: int, y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> str:
        if y == min_y:
            return "north"
        if y == max_y:
            return "south"
        if x == min_x:
            return "west"
        if x == max_x:
            return "east"
        raise ValueError(f"D4 gate coordinate is not on boundary: {x}_{y}")

    @staticmethod
    def _ru_direction(direction: str) -> str:
        return {"north": "Северные", "south": "Южные", "west": "Западные", "east": "Восточные"}[direction]

    @staticmethod
    def _d4_boundary_blocked_exits(*, x: int, y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> list[str]:
        blocked = []
        if y == min_y:
            blocked.append("north")
        if y == max_y:
            blocked.append("south")
        if x == min_x:
            blocked.append("west")
        if x == max_x:
            blocked.append("east")
        return blocked

    def _d4_movement_blocked_exits(
        self,
        *,
        x: int,
        y: int,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        mid_x: int,
        mid_y: int,
        road_cells: set[tuple[int, int]],
        is_outer_gate: bool,
    ) -> list[str]:
        allowed: set[str] = set()
        for direction, (dx, dy) in WorldNavigationService.DIRECTIONS.items():
            nx = x + dx
            ny = y + dy
            if nx < min_x or nx > max_x or ny < min_y or ny > max_y:
                if (
                    is_outer_gate
                    and self._d4_gate_direction(x=x, y=y, min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
                    == direction
                ):
                    allowed.add(direction)
                continue

            if self._d4_edge_is_open(
                x=x,
                y=y,
                nx=nx,
                ny=ny,
                direction=direction,
                min_x=min_x,
                min_y=min_y,
                max_x=max_x,
                max_y=max_y,
                mid_x=mid_x,
                mid_y=mid_y,
                road_cells=road_cells,
            ):
                allowed.add(direction)

        if not is_outer_gate and not self._is_d4_hub_node(x, y):
            allowed = self._d4_limit_allowed_directions(
                x=x,
                y=y,
                mid_x=mid_x,
                mid_y=mid_y,
                road_cells=road_cells,
                allowed=allowed,
            )

        return [direction for direction in WorldNavigationService.DIRECTIONS if direction not in allowed]

    @staticmethod
    def _d4_limit_allowed_directions(
        *,
        x: int,
        y: int,
        mid_x: int,
        mid_y: int,
        road_cells: set[tuple[int, int]],
        allowed: set[str],
    ) -> set[str]:
        if len(allowed) <= 3:
            return allowed

        protected: set[str] = set()
        is_road = (x, y) in road_cells
        if is_road and x == mid_x:
            protected.update({"north", "south"} & allowed)
        if is_road and y == mid_y:
            protected.update({"west", "east"} & allowed)

        if is_road and x == mid_x:
            drop_order = ("west", "east") if y % 2 else ("east", "west")
        elif is_road and y == mid_y:
            drop_order = ("north", "south") if x % 2 else ("south", "north")
        elif x % 3 == 1:
            drop_order = ("west", "east") if y % 2 else ("east", "west")
        else:
            drop_order = ("north", "south") if x % 2 else ("south", "north")

        for direction in (*drop_order, "north", "south", "west", "east"):
            if len(allowed) <= 3:
                break
            if direction in allowed and direction not in protected:
                allowed.remove(direction)

        if len(allowed) > 3:
            for direction in ("north", "south", "west", "east"):
                if len(allowed) <= 3:
                    break
                allowed.discard(direction)
        return allowed

    @staticmethod
    def _d4_edge_is_open(
        *,
        x: int,
        y: int,
        nx: int,
        ny: int,
        direction: str,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        mid_x: int,
        mid_y: int,
        road_cells: set[tuple[int, int]],
    ) -> bool:
        if x in (min_x, max_x) and nx == x:
            return True
        if y in (min_y, max_y) and ny == y:
            return True

        current_road = (x, y) in road_cells
        neighbor_road = (nx, ny) in road_cells
        if current_road and neighbor_road:
            return True

        if direction in {"east", "west"}:
            return True

        if x % 3 == 1 and nx % 3 == 1:
            return True

        if current_road or neighbor_road:
            return (x == mid_x and y % 2 == 0) or (y == mid_y and x % 3 == 1)

        return False

    @staticmethod
    def _d4_boundary_features(
        directions: list[str], *, kind: str, state: str, tags: list[str]
    ) -> dict[str, dict[str, Any]]:
        return {direction: {"kind": kind, "state": state, "tags": tags} for direction in directions}

    async def _generate_world_shell(self) -> None:
        """Generates the skeleton of regions and zones using anchor influence."""
        for r_idx, row_char in enumerate(REGION_ROWS):
            for col_idx in range(1, len(REGION_ROWS) + 1):
                region_id = f"{row_char}{col_idx}"
                region_influence = ThreatService.describe(
                    (col_idx - 1) * REGION_SIZE + REGION_SIZE // 2,
                    r_idx * REGION_SIZE + REGION_SIZE // 2,
                )
                region_geo = WorldGeographyService.describe_zone(
                    (col_idx - 1) * REGION_SIZE + REGION_SIZE // 2,
                    r_idx * REGION_SIZE + REGION_SIZE // 2,
                )
                region_profile = build_region_profile(
                    region_id=region_id,
                    center_x=(col_idx - 1) * REGION_SIZE + REGION_SIZE // 2,
                    center_y=r_idx * REGION_SIZE + REGION_SIZE // 2,
                    geography=region_geo,
                    influence=region_influence,
                )
                await self.data.upsert_region(
                    region_id,
                    climate_tags=list(dict.fromkeys(region_profile.region_tags)),
                    context={"region_profile": region_profile.model_dump()},
                    biome_id=region_profile.biome_id,
                    biome_mix=region_profile.biome_mix,
                    region_archetype=region_profile.region_archetype,
                    tier_min=region_profile.tier_band[0],
                    tier_max=region_profile.tier_band[1],
                    navigation_profile_id=region_profile.navigation_profile_id,
                    population_profile=build_habitat_population_profile_payload(region_profile),
                    anchor_influence=region_profile.anchor_influence,
                    is_locked_frontier=region_profile.is_locked_frontier,
                )

                # Create 3x3 zones per region (simplified)
                zones_per_region = REGION_SIZE // ZONE_SIZE
                for zx in range(zones_per_region):
                    for zy in range(zones_per_region):
                        zone_id = f"{region_id}_{zx}_{zy}"
                        center_x = (col_idx - 1) * REGION_SIZE + zx * ZONE_SIZE + ZONE_SIZE // 2
                        center_y = r_idx * REGION_SIZE + zy * ZONE_SIZE + ZONE_SIZE // 2
                        influence = ThreatService.describe(center_x, center_y)
                        world_theme = WorldThemeService.build(center_x, center_y, loc_id=zone_id)
                        zone_profile = build_zone_profile(
                            region_profile=region_profile,
                            zone_id=zone_id,
                            zx=zx,
                            zy=zy,
                        )

                        await self.data.upsert_zone(
                            zone_id,
                            region_id=region_id,
                            biome_id=region_profile.biome_id,
                            tier=influence.tier,
                            zone_archetype=zone_profile.zone_archetype,
                            navigation_profile_id=zone_profile.navigation_profile_id,
                            landmark_profile=zone_profile.landmark_profile,
                            population_tags=list(zone_profile.population_tags),
                            flags={
                                "is_safe_zone": False,
                                "threat": influence.threat,
                                "threat_tier": influence.tier,
                                "dominant_anchor": influence.dominant_anchor,
                                "anomaly_id": influence.anomaly_id,
                                "anchor_tags": influence.tags,
                                "is_inside_city_shield": influence.is_inside_city_shield,
                                "is_locked_frontier": region_profile.is_locked_frontier,
                                "world_theme": world_theme.model_dump(mode="json"),
                            },
                        )
        log.info("WorldShellGenerated")
