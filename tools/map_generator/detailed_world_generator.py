import os
import math
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Pure Python A* pathfinder and Perlin noise generator for detailed schematics

class SimpleNoise:
    def __init__(self, seed=42):
        random.seed(seed)
        self.p = list(range(256))
        random.shuffle(self.p)
        self.p += self.p

    def noise(self, x, y):
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        x -= math.floor(x)
        y -= math.floor(y)
        fade_x = x * x * x * (x * (x * 6 - 15) + 10)
        fade_y = y * y * y * (y * (y * 6 - 15) + 10)
        u = self.p[X]
        v = self.p[X + 1]
        a = self.p[u + Y]
        b = self.p[u + Y + 1]
        c = self.p[v + Y]
        d = self.p[v + Y + 1]

        # Gradients
        g00 = self.grad(a, x, y)
        g10 = self.grad(c, x - 1, y)
        g01 = self.grad(b, x, y - 1)
        g11 = self.grad(d, x - 1, y - 1)

        # Interpolations
        x1 = g00 + fade_x * (g10 - g00)
        x2 = g01 + fade_x * (g11 - g01)
        return x1 + fade_y * (x2 - x1)

    def grad(self, hash_code, x, y):
        h = hash_code & 7
        u = x if h < 4 else y
        v = y if h < 4 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v * 2.0)

    def fbm(self, x, y, octaves=4, lacunarity=2.0, gain=0.5):
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_val = 0.0
        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_val += amplitude
            amplitude *= gain
            frequency *= lacunarity
        return (total / max_val + 1.0) / 2.0  # normalize to 0..1

def astar_path(start, end, cost_grid, width, height):
    """Classic A* pathfinder on a grid."""
    open_set = {start}
    came_from = {}
    g_score = {start: 0.0}
    f_score = {start: heuristic(start, end)}

    while open_set:
        current = min(open_set, key=lambda p: f_score.get(p, float('inf')))
        if current == end:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        open_set.remove(current)
        cx, cy = current

        # 4 directions
        neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
        for nx, ny in neighbors:
            if 0 <= nx < width and 0 <= ny < height:
                neighbor = (nx, ny)
                tentative_g = g_score[current] + cost_grid[ny][nx]
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    open_set.add(neighbor)
    return []

def heuristic(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def generate_detailed_schematic(
    output_path: str,
    nodes_count: int = 17,
    node_size: int = 128,
    seed: int = 1337
):
    size = nodes_count * node_size  # 2176 px
    grid_w, grid_h = nodes_count * 8, nodes_count * 8 # downsampled grid for pathfinding
    cell_px = size / grid_w # 16 pixels per grid cell

    print(f"Generating detailed world schematic ({size}x{size} px)...")

    noise = SimpleNoise(seed)

    # 1. Initialize maps
    heightmap = [[0.0 for _ in range(grid_w)] for _ in range(grid_h)]
    moisture = [[0.0 for _ in range(grid_w)] for _ in range(grid_h)]
    cost_grid = [[1.0 for _ in range(grid_w)] for _ in range(grid_h)]

    # Generate terrain heights and moisture
    for y in range(grid_h):
        for x in range(grid_w):
            nx = (x / grid_w) * 4.0
            ny = (y / grid_h) * 4.0

            # Height
            h = noise.fbm(nx, ny, octaves=4)
            heightmap[y][x] = h

            # Moisture
            m = noise.fbm(nx + 15.0, ny + 15.0, octaves=3)
            moisture[y][x] = m

            # Determine base pathfinding cost
            if h < 0.35: # Water
                cost_grid[y][x] = 100.0 # very expensive to cross water
            elif h > 0.75: # Mountain
                cost_grid[y][x] = 25.0  # expensive to scale mountains
            else:
                cost_grid[y][x] = 1.0 + (m * 2.0) # slightly prefer dry meadows over forests

    # 2. Draw high-res base image
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)

    # Classify and draw pixels
    print("Drawing organic terrain...")
    for y in range(size):
        for x in range(size):
            # Map pixel to grid coord
            gx = int(x / cell_px)
            gy = int(y / cell_px)
            gx = min(grid_w - 1, max(0, gx))
            gy = min(grid_h - 1, max(0, gy))

            h = heightmap[gy][gx]
            m = moisture[gy][gx]

            if h < 0.35:
                # Water
                color = (44, 94, 138)
            elif h < 0.38:
                # Beach/Sand
                color = (226, 195, 145)
            elif h > 0.78:
                # Mountains (grey)
                color = (130, 130, 130)
            else:
                # Land biomes based on moisture
                if m > 0.6:
                    # Forest (dark green)
                    color = (52, 117, 72)
                else:
                    # Meadow (light green)
                    color = (124, 181, 114)
            img.putpixel((x, y), color)

    # 3. Generate Winding River (using gradient descent from high altitude to sea)
    print("Generating winding rivers...")
    # Find a mountain peak
    peak_y, peak_x = 0, 0
    max_h = 0.0
    for y in range(grid_h // 3):
        for x in range(grid_w):
            if heightmap[y][x] > max_h:
                max_h = heightmap[y][x]
                peak_x, peak_y = x, y

    # Flow downhill
    river_path = []
    cy, cx = peak_y, peak_x
    visited = set()
    while len(river_path) < 100:
        river_path.append((cx, cy))
        visited.add((cx, cy))

        # Check neighbors for lowest height
        neighbors = [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]
        best_n = None
        min_h = heightmap[cy][cx]
        for nx, ny in neighbors:
            if 0 <= nx < grid_w and 0 <= ny < grid_h and (nx, ny) not in visited:
                if heightmap[ny][nx] < min_h:
                    min_h = heightmap[ny][nx]
                    best_n = (nx, ny)
        if not best_n:
            break
        cx, cy = best_n
        if heightmap[cy][cx] < 0.35: # Reached water
            river_path.append((cx, cy))
            break

    # Draw the winding river on high-res image
    for i in range(len(river_path) - 1):
        p1 = (int(river_path[i][0] * cell_px + cell_px/2), int(river_path[i][1] * cell_px + cell_px/2))
        p2 = (int(river_path[i+1][0] * cell_px + cell_px/2), int(river_path[i+1][1] * cell_px + cell_px/2))
        draw.line([p1, p2], fill=(44, 94, 138), width=24)

    # 4. Generate Winding Roads using A* Pathfinding
    # Target points: center node (8,8) to the four borders
    print("Calculating smart winding roads (A*)...")
    center_node = (nodes_count // 2, nodes_count // 2) # (8, 8)
    center_grid = (center_node[0] * 8 + 4, center_node[1] * 8 + 4)

    borders_grid = {
        "north": (center_grid[0], 0),
        "south": (center_grid[0], grid_h - 1),
        "west": (0, center_grid[1]),
        "east": (grid_w - 1, center_grid[1])
    }

    # Temporarily lower the cost of the starting point
    cost_grid[center_grid[1]][center_grid[0]] = 1.0

    # Calculate roads
    roads = []
    for border_name, target in borders_grid.items():
        # A* pathfinding
        path = astar_path(center_grid, target, cost_grid, grid_w, grid_h)
        if path:
            roads.append(path)
            # Mark road in cost grid so other roads can reuse it (creates merges)
            for rx, ry in path:
                cost_grid[ry][rx] = 0.5

    # Draw roads
    for path in roads:
        for i in range(len(path) - 1):
            p1 = (int(path[i][0] * cell_px + cell_px/2), int(path[i][1] * cell_px + cell_px/2))
            p2 = (int(path[i+1][0] * cell_px + cell_px/2), int(path[i+1][1] * cell_px + cell_px/2))
            draw.line([p1, p2], fill=(120, 120, 120), width=10) # Grey road

    # 5. Stamp Castle Icon strictly inside center node (8, 8)
    # The center node boundary is [1024..1152, 1024..1152]
    cx_start = center_node[0] * node_size # 1024
    cy_start = center_node[1] * node_size # 1024
    margin = 44 # 128 - 40 = 88 / 2 = 44px margin for a very small 40px icon
    cx = cx_start + margin
    cy = cy_start + margin
    icon_w = node_size - 2 * margin

    # Clean up the center node area by drawing a small meadow circle under the castle
    draw.ellipse([cx_start + 16, cy_start + 16, cx_start + node_size - 16, cy_start + node_size - 16], fill=(124, 181, 114))

    # Draw castle keep
    draw.rectangle([cx, cy, cx + icon_w, cy + icon_w], fill=(120, 120, 120), outline=(60, 60, 60), width=3)
    # Red roof
    draw.polygon([(cx, cy), (cx + icon_w//2, cy - 12), (cx + icon_w, cy)], fill=(180, 60, 50))
    # Castle gate
    draw.rectangle([cx + 14, cy + 24, cx + 26, cy + icon_w], fill=(220, 180, 80))

    # Save the file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Successfully generated detailed schematic at: {output_path}")

if __name__ == "__main__":
    out_file = "tools/output/global_test/schematic.png"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]

    generate_detailed_schematic(out_file)
