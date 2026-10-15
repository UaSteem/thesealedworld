import argparse
import json
import math
import os
import random
from pathlib import Path
from PIL import Image

# Optimized value noise grids
NOISE_GRID_SIZE = 256
random.seed(42)
noise_grid_height = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]
noise_grid_temp = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]
noise_grid_hum = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]

def fast_noise(x, y, grid):
    xi = int(x) % NOISE_GRID_SIZE
    yi = int(y) % NOISE_GRID_SIZE
    xi1 = (xi + 1) % NOISE_GRID_SIZE
    yi1 = (yi + 1) % NOISE_GRID_SIZE
    xf = x - int(x)
    yf = y - int(y)
    v00 = grid[yi][xi]
    v10 = grid[yi][xi1]
    v01 = grid[yi1][xi]
    v11 = grid[yi1][xi1]
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)
    return (1.0 - v) * ((1.0 - u) * v00 + u * v10) + v * ((1.0 - u) * v01 + u * v11)

def fbm(x, y, grid, octaves=4, lacunarity=2.0, gain=0.5):
    total = 0.0
    amplitude = 1.0
    frequency = 1.0
    max_value = 0.0
    for _ in range(octaves):
        total += fast_noise(x * frequency, y * frequency, grid) * amplitude
        max_value += amplitude
        amplitude *= gain
        frequency *= lacunarity
    return total / max_value

BIOMES_DEFINITION = {
    "snow": {"ideal_temp_c": -15.0, "ideal_humidity": 0.1, "color": (240, 248, 255), "ru_name": "Снежные пики"},
    "tundra": {"ideal_temp_c": -5.0, "ideal_humidity": 0.15, "color": (191, 199, 175), "ru_name": "Тундра"},
    "taiga": {"ideal_temp_c": 5.0, "ideal_humidity": 0.6, "color": (46, 89, 66), "ru_name": "Хвойная тайга"},
    "grassland": {"ideal_temp_c": 18.0, "ideal_humidity": 0.4, "color": (124, 181, 114), "ru_name": "Ветреные луга"},
    "temperate_deciduous_forest": {"ideal_temp_c": 15.0, "ideal_humidity": 0.7, "color": (52, 117, 72), "ru_name": "Густой лес"},
    "temperate_desert": {"ideal_temp_c": 25.0, "ideal_humidity": 0.1, "color": (230, 212, 158), "ru_name": "Бесплодная пустыня"}
}

def match_biome(temp, humidity):
    best_biome = "grassland"
    min_dist = float('inf')
    for biome_id, data in BIOMES_DEFINITION.items():
        temp_diff = temp - data["ideal_temp_c"]
        humidity_diff = (humidity - data["ideal_humidity"]) * 100
        dist_sq = temp_diff**2 + humidity_diff**2
        if dist_sq < min_dist:
            min_dist = dist_sq
            best_biome = biome_id
    return best_biome

def build_region(nodes_count=3, seed=42, scale=3.5, sea_level=0.22, beach_level=0.25, base_temp=12.0, output_dir="tools/output"):
    # Set seeds
    random.seed(seed)
    global noise_grid_height, noise_grid_temp, noise_grid_hum
    noise_grid_height = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]
    noise_grid_temp = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]
    noise_grid_hum = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]

    node_size = 1024
    global_size = nodes_count * node_size
    print(f"Generating global region heightmap {global_size}x{global_size} ({nodes_count}x{nodes_count} nodes)...")

    heightmap = [[0.0 for _ in range(global_size)] for _ in range(global_size)]
    walkable_grid = [[False for _ in range(global_size)] for _ in range(global_size)]
    tiermap = [[0 for _ in range(global_size)] for _ in range(global_size)]
    biomemap = [["" for _ in range(global_size)] for _ in range(global_size)]

    # 1. Compute global layout
    for y in range(global_size):
        for x in range(global_size):
            nx = (x / global_size) * scale
            ny = (y / global_size) * scale

            # Damp borders of the ENTIRE region (not individual nodes) to make ocean boundaries
            dx = (x - global_size / 2) / (global_size / 2)
            dy = (y - global_size / 2) / (global_size / 2)
            dist = math.sqrt(dx*dx + dy*dy)
            damp_val = max(0.0, 1.0 - dist * 0.7)  # Мягкое сглаживание к границам региона

            h = fbm(nx, ny, noise_grid_height, octaves=5)
            h = h * (0.3 + 0.7 * damp_val)
            heightmap[y][x] = h
            tiermap[y][x] = int(h * 12)

            if h < sea_level:
                walkable_grid[y][x] = False
                biomemap[y][x] = "water"
            elif h < beach_level:
                walkable_grid[y][x] = True
                biomemap[y][x] = "beach"
            else:
                walkable_grid[y][x] = True
                # Climate evaluation
                latitude_temp_mod = (1.0 - (y / global_size)) * 12.0 - 6.0
                t_noise = fbm(nx + 10.0, ny + 10.0, noise_grid_temp, octaves=3) * 14.0 - 7.0
                temp = base_temp + latitude_temp_mod + t_noise - (h * 20.0)

                h_noise = fbm(nx + 20.0, ny + 20.0, noise_grid_hum, octaves=3)
                humidity = max(0.0, min(1.0, h_noise * 0.6 + 0.1)) # simplified proximity

                biomemap[y][x] = match_biome(temp, humidity)

    # 2. Slice into node images & analyze boundaries
    region_dir = Path(output_dir) / f"region_{seed}"
    schematics_dir = region_dir / "schematics"
    schematics_dir.mkdir(parents=True, exist_ok=True)

    print("Slicing nodes and checking exits...")
    manifest = {}

    for ny_idx in range(nodes_count):
        for nx_idx in range(nodes_count):
            node_id = f"{nx_idx}_{ny_idx}"

            # Slice image
            node_img = Image.new("RGB", (node_size, node_size))
            pixels = node_img.load()

            y_start = ny_idx * node_size
            x_start = nx_idx * node_size

            biome_counts = {}

            # Populate node pixel colors
            for y_local in range(node_size):
                y_global = y_start + y_local
                for x_local in range(node_size):
                    x_global = x_start + x_local

                    b = biomemap[y_global][x_global]
                    biome_counts[b] = biome_counts.get(b, 0) + 1

                    # Determine color
                    if b == "water":
                        h = heightmap[y_global][x_global]
                        base_color = (29, 42, 68) if h < (sea_level * 0.7) else (44, 94, 138)
                    elif b == "beach":
                        base_color = (226, 195, 145)
                    else:
                        base_color = BIOMES_DEFINITION[b]["color"]

                    # Shading for cliffs
                    is_cliff = False
                    is_highlight = False
                    tier = tiermap[y_global][x_global]

                    if b != "water":
                        if x_local < node_size - 1:
                            right_tier = tiermap[y_global][x_global + 1]
                            if tier > right_tier: is_cliff = True
                            elif tier < right_tier: is_highlight = True
                        if y_local < node_size - 1:
                            bottom_tier = tiermap[y_global + 1][x_global]
                            if tier > bottom_tier: is_cliff = True
                            elif tier < bottom_tier: is_highlight = True

                    if is_cliff:
                        shadow = (17, 20, 25)
                        pixels[x_local, y_local] = (
                            int(base_color[0] * 0.55 + shadow[0] * 0.45),
                            int(base_color[1] * 0.55 + shadow[1] * 0.45),
                            int(base_color[2] * 0.55 + shadow[2] * 0.45)
                        )
                    elif is_highlight:
                        highlight = (255, 255, 255)
                        pixels[x_local, y_local] = (
                            int(base_color[0] * 0.75 + highlight[0] * 0.25),
                            int(base_color[1] * 0.75 + highlight[1] * 0.25),
                            int(base_color[2] * 0.75 + highlight[2] * 0.25)
                        )
                    else:
                        pixels[x_local, y_local] = base_color

            # Save schematic slice
            img_filename = f"node_{node_id}.png"
            node_img.save(schematics_dir / img_filename)

            # Analyze dominant biome
            dominant_biome = max(biome_counts, key=biome_counts.get)
            biome_name_ru = BIOMES_DEFINITION.get(dominant_biome, {}).get("ru_name", "Дикие земли") if dominant_biome != "water" else "Тихая гавань"

            # Check exits to adjacent nodes
            exits = {}

            # North (check top border of this node)
            if ny_idx > 0:
                y_border = y_start
                # Check if there is at least one walkable cell along the boundary segment
                walkable_segment = [walkable_grid[y_border][x] for x in range(x_start, x_start + node_size)]
                if any(walkable_segment):
                    exits[f"nav:{nx_idx}_{ny_idx - 1}"] = {"time_duration": 1.5, "desc_next_room": "Переход на Север"}

            # South (check bottom border of this node)
            if ny_idx < nodes_count - 1:
                y_border = y_start + node_size - 1
                walkable_segment = [walkable_grid[y_border][x] for x in range(x_start, x_start + node_size)]
                if any(walkable_segment):
                    exits[f"nav:{nx_idx}_{ny_idx + 1}"] = {"time_duration": 1.5, "desc_next_room": "Переход на Юг"}

            # West (check left border of this node)
            if nx_idx > 0:
                x_border = x_start
                walkable_segment = [walkable_grid[y][x_border] for y in range(y_start, y_start + node_size)]
                if any(walkable_segment):
                    exits[f"nav:{nx_idx - 1}_{ny_idx}"] = {"time_duration": 1.5, "desc_next_room": "Переход на Запад"}

            # East (check right border of this node)
            if nx_idx < nodes_count - 1:
                x_border = x_start + node_size - 1
                walkable_segment = [walkable_grid[y][x_border] for y in range(y_start, y_start + node_size)]
                if any(walkable_segment):
                    exits[f"nav:{nx_idx + 1}_{ny_idx}"] = {"time_duration": 1.5, "desc_next_room": "Переход на Восток"}

            # Write node description
            manifest[node_id] = {
                "loc_id": node_id,
                "x": nx_idx,
                "y": ny_idx,
                "name": f"{biome_name_ru} ({nx_idx}, {ny_idx})",
                "description": f"Местность, покрытая биомом: {dominant_biome}. Рельеф сформирован перепадами высот.",
                "biome_id": dominant_biome,
                "schematic_url": f"/tools/output/region_{seed}/schematics/{img_filename}",
                "exits": exits
            }

    # Save manifest JSON
    manifest_path = region_dir / "region_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Region generation complete! Files saved to {region_dir}")
    print(f"Manifest saved to {manifest_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate a seamless N x N grid of location nodes.")
    parser.add_argument("--nodes", type=int, default=3, help="Grid size (3 means 3x3=9 nodes)")
    parser.add_argument("--scale", type=float, default=2.2, help="Noise scale for the region (lower = larger land structures)")
    parser.add_argument("--sea-level", type=float, default=0.22, help="Sea level threshold")
    parser.add_argument("--temp", type=float, default=12.0, help="Base temperature")
    parser.add_argument("--seed", type=int, default=1337, help="Seed")
    parser.add_argument("--output", type=str, default="tools/output", help="Output directory")
    args = parser.parse_args()

    build_region(
        nodes_count=args.nodes,
        seed=args.seed,
        scale=args.scale,
        sea_level=args.sea_level,
        base_temp=args.temp,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()
