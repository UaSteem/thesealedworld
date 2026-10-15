from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_TEMPLATE_PATH = ROOT / "ai_master_template.png"
DEFAULT_MANIFEST_PATH = ROOT / "assets" / "ai_templates" / "rift_template_spec.json"

GRID_SIZE = 8
CELL_SIZE = 512
TILE_COUNT = GRID_SIZE * GRID_SIZE
BLOCKER_TILE_COUNT = 30
MOVEMENT_TILE_COUNT = 11
LEVEL_TRANSITION_TILE_COUNT = 4
EVENT_TILE_COUNT = 12
MOOD_TILE_COUNT = TILE_COUNT - BLOCKER_TILE_COUNT - MOVEMENT_TILE_COUNT - LEVEL_TRANSITION_TILE_COUNT - EVENT_TILE_COUNT

HEX_H = 440.0
HEX_W = 380.0
SLICE_HEX_H = 438.0
SLICE_HEX_W = 378.0
EDGE_ORDER = ("NE", "E", "SE", "SW", "W", "NW")

BACKGROUND_COLOR = (255, 255, 255)
GRID_COLOR = (205, 205, 205)
OUTLINE_COLOR = (0, 0, 0)
VOID_COLOR = (0, 0, 0)
BLOCKER_COLOR = (216, 44, 48)
WALKABLE_COLOR = (42, 202, 47)

BLOCKER_DEPTH_BY_CLOSED_COUNT = {
    1: 0.30,
    2: 0.40,
    3: 0.54,
    4: 0.68,
    5: 0.82,
}


@dataclass(frozen=True)
class RiftTileSpec:
    id: int
    row: int
    col: int
    role: str
    file: str
    walkable: bool
    closed_edges: tuple[int, ...]
    edges: tuple[int, ...]
    variant: str


def get_hex_vertices(cx: float, cy: float, hex_w: float = HEX_W, hex_h: float = HEX_H) -> list[tuple[float, float]]:
    return [
        (cx, cy - hex_h / 2.0),
        (cx + hex_w / 2.0, cy - hex_h / 4.0),
        (cx + hex_w / 2.0, cy + hex_h / 4.0),
        (cx, cy + hex_h / 2.0),
        (cx - hex_w / 2.0, cy + hex_h / 4.0),
        (cx - hex_w / 2.0, cy - hex_h / 4.0),
    ]


def blocker_edge_configs() -> list[tuple[int, ...]]:
    configs: list[tuple[int, ...]] = []
    for closed_count in range(1, 6):
        for start in range(6):
            configs.append(tuple((start + step) % 6 for step in range(closed_count)))
    return configs


def movement_edge_configs() -> list[tuple[int, ...]]:
    return [
        (0, 3),
        (1, 4),
        (2, 5),
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 0),
        (0, 2, 4),
        (1, 3, 5),
    ]


def build_tile_specs() -> list[RiftTileSpec]:
    specs: list[RiftTileSpec] = []
    blocker_configs = blocker_edge_configs()
    movement_configs = movement_edge_configs()

    for index in range(TILE_COUNT):
        tile_id = index + 1
        row = index // GRID_SIZE
        col = index % GRID_SIZE
        file_name = f"tile_{tile_id:02d}.png"

        if index < BLOCKER_TILE_COUNT:
            closed_edges = blocker_configs[index]
            edges = tuple(0 if edge in closed_edges else 1 for edge in range(6))
            variant = (
                f"blocker_closed_{len(closed_edges)}_variant_{index - 30}"
                if len(closed_edges) == 6
                else f"blocker_closed_{len(closed_edges)}_start_{closed_edges[0]}"
            )
            specs.append(
                RiftTileSpec(
                    id=tile_id,
                    row=row,
                    col=col,
                    role="blocker",
                    file=file_name,
                    walkable=False,
                    closed_edges=closed_edges,
                    edges=edges,
                    variant=variant,
                )
            )
            continue

        movement_index = index - BLOCKER_TILE_COUNT
        if movement_index < MOVEMENT_TILE_COUNT:
            open_edges = movement_configs[movement_index]
            edges = tuple(1 if edge in open_edges else 0 for edge in range(6))
            specs.append(
                RiftTileSpec(
                    id=tile_id,
                    row=row,
                    col=col,
                    role="movement",
                    file=file_name,
                    walkable=True,
                    closed_edges=tuple(edge for edge in range(6) if edge not in open_edges),
                    edges=edges,
                    variant=f"movement_{'-'.join(str(edge + 1) for edge in open_edges)}",
                )
            )
            continue

        transition_index = movement_index - MOVEMENT_TILE_COUNT
        if transition_index < LEVEL_TRANSITION_TILE_COUNT:
            specs.append(
                RiftTileSpec(
                    id=tile_id,
                    row=row,
                    col=col,
                    role="level_transition",
                    file=file_name,
                    walkable=True,
                    closed_edges=(),
                    edges=(1, 1, 1, 1, 1, 1),
                    variant=f"level_transition_{transition_index + 1:02d}",
                )
            )
            continue

        event_index = transition_index - LEVEL_TRANSITION_TILE_COUNT
        if event_index < EVENT_TILE_COUNT:
            specs.append(
                RiftTileSpec(
                    id=tile_id,
                    row=row,
                    col=col,
                    role="event",
                    file=file_name,
                    walkable=True,
                    closed_edges=(),
                    edges=(1, 1, 1, 1, 1, 1),
                    variant=f"event_placeholder_{event_index + 1:02d}",
                )
            )
            continue

        mood_index = event_index - EVENT_TILE_COUNT
        specs.append(
            RiftTileSpec(
                id=tile_id,
                row=row,
                col=col,
                role="mood",
                file=file_name,
                walkable=True,
                closed_edges=(),
                edges=(1, 1, 1, 1, 1, 1),
                variant=f"mood_variant_{mood_index + 1:02d}",
            )
        )

    return specs


def build_tileset_data(theme: str) -> dict[str, list[dict[str, object]]]:
    return {
        "tiles": [
            {
                "id": spec.id,
                "file": spec.file,
                "walkable": 1 if spec.walkable else 0,
                "biome": theme,
                "edges": list(spec.edges),
                "event": "",
            }
            for spec in build_tile_specs()
        ]
    }


def edge_bitmask(edges: tuple[int, ...]) -> list[int]:
    return [1 if edge in edges else 0 for edge in range(6)]


def _center(vertices: list[tuple[float, float]]) -> tuple[float, float]:
    return (
        sum(point[0] for point in vertices) / len(vertices),
        sum(point[1] for point in vertices) / len(vertices),
    )


def _lerp(point: tuple[float, float], target: tuple[float, float], factor: float) -> tuple[float, float]:
    return (
        point[0] + (target[0] - point[0]) * factor,
        point[1] + (target[1] - point[1]) * factor,
    )


def draw_blocker_tile(
    draw: ImageDraw.ImageDraw,
    vertices: list[tuple[float, float]],
    closed_edges: tuple[int, ...],
) -> None:
    draw.polygon(vertices, fill=VOID_COLOR)

    closed_count = len(closed_edges)
    if closed_count == 6:
        draw.polygon(vertices, fill=BLOCKER_COLOR)
        return

    center = _center(vertices)
    depth = BLOCKER_DEPTH_BY_CLOSED_COUNT[closed_count]
    for edge in closed_edges:
        start = vertices[edge]
        end = vertices[(edge + 1) % 6]
        inner_end = _lerp(end, center, depth)
        inner_start = _lerp(start, center, depth)
        draw.polygon([start, end, inner_end, inner_start], fill=BLOCKER_COLOR)


def edge_midpoint(vertices: list[tuple[float, float]], edge: int) -> tuple[float, float]:
    start = vertices[edge]
    end = vertices[(edge + 1) % 6]
    return ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)


def draw_walkable_tile(
    draw: ImageDraw.ImageDraw,
    vertices: list[tuple[float, float]],
    open_edges: tuple[int, ...],
    *,
    event: bool = False,
) -> None:
    draw.polygon(vertices, fill=WALKABLE_COLOR)
    closed_edges = tuple(edge for edge in range(6) if edge not in open_edges)
    draw_closed_edge_strips(draw, vertices, closed_edges)


def draw_closed_edge_strips(
    draw: ImageDraw.ImageDraw,
    vertices: list[tuple[float, float]],
    closed_edges: tuple[int, ...],
) -> None:
    center = _center(vertices)
    depth = 0.30
    for edge in closed_edges:
        start = vertices[edge]
        end = vertices[(edge + 1) % 6]
        inner_end = _lerp(end, center, depth)
        inner_start = _lerp(start, center, depth)
        draw.polygon([start, end, inner_end, inner_start], fill=BLOCKER_COLOR)


def draw_plain_walkable_tile(draw: ImageDraw.ImageDraw, vertices: list[tuple[float, float]]) -> None:
    draw.polygon(vertices, fill=WALKABLE_COLOR)


def generate_template(
    output_path: Path = DEFAULT_TEMPLATE_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> None:
    img_size = GRID_SIZE * CELL_SIZE
    image = Image.new("RGB", (img_size, img_size), BACKGROUND_COLOR)
    draw_main = ImageDraw.Draw(image)
    specs = build_tile_specs()

    for i in range(0, img_size + 1, CELL_SIZE):
        draw_main.line([(i, 0), (i, img_size)], fill=GRID_COLOR, width=2)
        draw_main.line([(0, i), (img_size, i)], fill=GRID_COLOR, width=2)

    manifest_tiles = []
    for spec in specs:
        cx = spec.col * CELL_SIZE + CELL_SIZE / 2.0
        cy = spec.row * CELL_SIZE + CELL_SIZE / 2.0
        vertices = get_hex_vertices(cx, cy)

        tile_layer = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        tile_draw = ImageDraw.Draw(tile_layer)

        mask_layer = Image.new("L", (img_size, img_size), 0)
        mask_draw = ImageDraw.Draw(mask_layer)
        mask_draw.polygon(vertices, fill=255)

        if spec.role == "blocker":
            draw_blocker_tile(tile_draw, vertices, spec.closed_edges)
        elif spec.role == "movement":
            open_edges = tuple(edge for edge, value in enumerate(spec.edges) if value == 1)
            draw_walkable_tile(tile_draw, vertices, open_edges)
        else:
            draw_plain_walkable_tile(tile_draw, vertices)

        image.paste(tile_layer, (0, 0), mask_layer)
        draw_main.polygon(vertices, outline=OUTLINE_COLOR, width=4)
        manifest_tiles.append(
            {
                "id": spec.id,
                "row": spec.row,
                "col": spec.col,
                "role": spec.role,
                "variant": spec.variant,
                "walkable": spec.walkable,
                "closed_edges": list(spec.closed_edges),
                "closed_edge_bits": edge_bitmask(spec.closed_edges),
                "edges": list(spec.edges),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "turnbasedmmorpg.rift.ai_master_template.v1",
                "grid": GRID_SIZE,
                "cell": CELL_SIZE,
                "hex_w": HEX_W,
                "hex_h": HEX_H,
                "edge_order": list(EDGE_ORDER),
                "blocker_tile_count": BLOCKER_TILE_COUNT,
                "movement_tile_count": MOVEMENT_TILE_COUNT,
                "level_transition_tile_count": LEVEL_TRANSITION_TILE_COUNT,
                "event_tile_count": EVENT_TILE_COUNT,
                "mood_tile_count": MOOD_TILE_COUNT,
                "tiles": manifest_tiles,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Rift master template saved to {output_path}")
    print(f"Rift template manifest saved to {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the 8x8 rift AI master template.")
    parser.add_argument("--output", type=Path, default=DEFAULT_TEMPLATE_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()

    generate_template(args.output, args.manifest)


if __name__ == "__main__":
    main()
