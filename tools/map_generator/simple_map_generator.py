import argparse
import heapq
import math
import random
from PIL import Image, ImageDraw

# Grid size for precomputed noise (makes generation fast in pure Python)
NOISE_GRID_SIZE = 256
random.seed(1337)
noise_grid = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]

def fast_noise(x, y):
    """Bilinear value noise from precomputed table."""
    xi = int(x) % NOISE_GRID_SIZE
    yi = int(y) % NOISE_GRID_SIZE
    xi1 = (xi + 1) % NOISE_GRID_SIZE
    yi1 = (yi + 1) % NOISE_GRID_SIZE

    xf = x - int(x)
    yf = y - int(y)

    v00 = noise_grid[yi][xi]
    v10 = noise_grid[yi][xi1]
    v01 = noise_grid[yi1][xi]
    v11 = noise_grid[yi1][xi1]

    # Smoothstep interpolation
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)

    return (1.0 - v) * ((1.0 - u) * v00 + u * v10) + v * ((1.0 - u) * v01 + u * v11)

def fbm(x, y, octaves=4, lacunarity=2.0, gain=0.5):
    """Fractal Brownian Motion using the fast noise source."""
    total = 0.0
    amplitude = 1.0
    frequency = 1.0
    max_value = 0.0
    for _ in range(octaves):
        total += fast_noise(x * frequency, y * frequency) * amplitude
        max_value += amplitude
        amplitude *= gain
        frequency *= lacunarity
    return total / max_value

# Height tiers (0 to 5)
TIER_DEEP_WATER = 0
TIER_SHALLOW_WATER = 1
TIER_SAND = 2
TIER_MEADOW = 3
TIER_FOREST = 4
TIER_MOUNTAIN = 5

# Muted, easily distinguishable schematic colors
COLOR_PALETTE = {
    TIER_DEEP_WATER: (29, 42, 68),       # Dark Blue
    TIER_SHALLOW_WATER: (44, 94, 138),   # Muted Blue
    TIER_SAND: (226, 195, 145),          # Beige/Sand
    TIER_MEADOW: (90, 158, 110),         # Meadow Green
    TIER_FOREST: (44, 94, 59),           # Forest Green
    TIER_MOUNTAIN: (117, 125, 138),      # Stone Grey
    "road": (139, 90, 43),               # Brown Road
    "cliff_shadow": (17, 20, 25),        # Near Black
    "cliff_highlight": (255, 255, 255),  # White
}

def get_height_tier(height_val):
    """Maps normalized height [0.0, 1.0] to a height tier."""
    if height_val < 0.32:
        return TIER_DEEP_WATER
    elif height_val < 0.40:
        return TIER_SHALLOW_WATER
    elif height_val < 0.45:
        return TIER_SAND
    elif height_val < 0.70:
        return TIER_MEADOW
    elif height_val < 0.88:
        return TIER_FOREST
    else:
        return TIER_MOUNTAIN

def generate_map(size=1024, scale=5.0, seed=None, no_roads=False, damp_factor=1.2):
    if seed is not None:
        random.seed(seed)
        global noise_grid
        noise_grid = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]

    print(f"Generating {size}x{size} heightmap...")
    # 1. Generate heightmap array
    heightmap = [[0.0 for _ in range(size)] for _ in range(size)]
    tiermap = [[0 for _ in range(size)] for _ in range(size)]

    for y in range(size):
        for x in range(size):
            nx = (x / size) * scale
            ny = (y / size) * scale
            # Add a bit of centering/island dampening to make water at edges
            dx = (x - size / 2) / (size / 2)
            dy = (y - size / 2) / (size / 2)
            dist = math.sqrt(dx*dx + dy*dy)
            damp = max(0.0, 1.0 - dist * damp_factor)  # Fade out at borders

            h = fbm(nx, ny, octaves=5)
            h = h * (0.3 + 0.7 * damp)  # Apply island mask
            heightmap[y][x] = h
            tiermap[y][x] = get_height_tier(h)

    print("Shading cliffs...")
    # 2. Render initial colors with cliff shading
    # Create an RGB image
    img = Image.new("RGB", (size, size))
    pixels = img.load()

    for y in range(size):
        for x in range(size):
            tier = tiermap[y][x]
            base_color = COLOR_PALETTE[tier]

            # Shading for cliff edges
            # Check neighbors to the right and bottom
            is_cliff = False
            is_highlight = False

            if x < size - 1:
                right_tier = tiermap[y][x + 1]
                if tier > right_tier and tier >= TIER_MEADOW:
                    is_cliff = True
                elif tier < right_tier and right_tier >= TIER_MEADOW:
                    is_highlight = True

            if y < size - 1:
                bottom_tier = tiermap[y + 1][x]
                if tier > bottom_tier and tier >= TIER_MEADOW:
                    is_cliff = True
                elif tier < bottom_tier and bottom_tier >= TIER_MEADOW:
                    is_highlight = True

            if is_cliff:
                # Blend base color with dark shadow
                shadow = COLOR_PALETTE["cliff_shadow"]
                pixels[x, y] = (
                    int(base_color[0] * 0.4 + shadow[0] * 0.6),
                    int(base_color[1] * 0.4 + shadow[1] * 0.6),
                    int(base_color[2] * 0.4 + shadow[2] * 0.6)
                )
            elif is_highlight:
                # Blend base color with light highlight
                highlight = COLOR_PALETTE["cliff_highlight"]
                pixels[x, y] = (
                    int(base_color[0] * 0.7 + highlight[0] * 0.3),
                    int(base_color[1] * 0.7 + highlight[1] * 0.3),
                    int(base_color[2] * 0.7 + highlight[2] * 0.3)
                )
            else:
                pixels[x, y] = base_color

    print("Generating roads using A* on a downsampled grid...")
    # 3. Road pathfinding on a downsampled grid (128x128)
    ds_factor = 8
    ds_size = size // ds_factor

    # Helper function to get cost for A*
    def get_cell_cost(cx, cy):
        if cx < 0 or cx >= ds_size or cy < 0 or cy >= ds_size:
            return 99999
        # Get tier of center pixel in the block
        px = cx * ds_factor + ds_factor // 2
        py = cy * ds_factor + ds_factor // 2
        tier = tiermap[py][px]

        if tier == TIER_DEEP_WATER:
            return 500  # Avoid deep water at almost all costs
        elif tier == TIER_SHALLOW_WATER:
            return 120  # Bridges are expensive
        elif tier == TIER_SAND:
            return 3    # Sand is easy
        elif tier == TIER_MEADOW:
            return 1    # Meadows are easiest
        elif tier == TIER_FOREST:
            return 6    # Forests are harder to clear
        elif tier == TIER_MOUNTAIN:
            return 25   # Mountains are steep
        return 1

    def a_star(start, end):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: abs(start[0] - end[0]) + abs(start[1] - end[1])}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            cx, cy = current
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (cx + dx, cy + dy)
                cost = get_cell_cost(neighbor[0], neighbor[1])

                # Height transition penalty (cliff cost)
                px_curr = cx * ds_factor + ds_factor // 2
                py_curr = cy * ds_factor + ds_factor // 2
                px_neigh = neighbor[0] * ds_factor + ds_factor // 2
                py_neigh = neighbor[1] * ds_factor + ds_factor // 2
                if 0 <= px_neigh < size and 0 <= py_neigh < size:
                    height_diff = abs(tiermap[py_curr][px_curr] - tiermap[py_neigh][px_neigh])
                    cost += height_diff * 40

                tentative_g = g_score[current] + cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + abs(neighbor[0] - end[0]) + abs(neighbor[1] - end[1])
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []

    # Find candidate starting points for road nodes (villages) on land
    candidates = []
    for cy in range(15, ds_size - 15, 5):
        for cx in range(15, ds_size - 15, 5):
            px = cx * ds_factor + ds_factor // 2
            py = cy * ds_factor + ds_factor // 2
            if tiermap[py][px] == TIER_MEADOW:
                candidates.append((cx, cy))

    if not no_roads and len(candidates) >= 4:
        # Pick 4 random towns spread across quadrants
        towns = []
        # Q1 (top-left)
        q1 = [c for c in candidates if c[0] < ds_size//2 and c[1] < ds_size//2]
        if q1: towns.append(random.choice(q1))
        # Q2 (top-right)
        q2 = [c for c in candidates if c[0] >= ds_size//2 and c[1] < ds_size//2]
        if q2: towns.append(random.choice(q2))
        # Q3 (bottom-left)
        q3 = [c for c in candidates if c[0] < ds_size//2 and c[1] >= ds_size//2]
        if q3: towns.append(random.choice(q3))
        # Q4 (bottom-right)
        q4 = [c for c in candidates if c[0] >= ds_size//2 and c[1] >= ds_size//2]
        if q4: towns.append(random.choice(q4))

        print(f"Connecting towns at {towns} with roads...")
        draw = ImageDraw.Draw(img)
        # Connect towns in a loop/network
        for i in range(len(towns)):
            t1 = towns[i]
            t2 = towns[(i + 1) % len(towns)]
            path = a_star(t1, t2)
            if path:
                # Convert path back to 1024x1024 coords
                scaled_path = []
                for p in path:
                    px = p[0] * ds_factor + ds_factor // 2
                    py = p[1] * ds_factor + ds_factor // 2
                    scaled_path.append((px, py))
                # Draw thick brown line for road
                draw.line(scaled_path, fill=COLOR_PALETTE["road"], width=4, joint="round")

                # Draw a small settlement circle at each town center
                for t in towns:
                    tx = t[0] * ds_factor + ds_factor // 2
                    ty = t[1] * ds_factor + ds_factor // 2
                    draw.ellipse([tx-6, ty-6, tx+6, ty+6], fill=COLOR_PALETTE["road"], outline=(255, 255, 255))

    return img

def main():
    parser = argparse.ArgumentParser(description="Generate schematic pixel maps.")
    parser.add_argument("--size", type=int, default=1024, help="Size of the image")
    parser.add_argument("--scale", type=float, default=6.5, help="Noise frequency scale")
    parser.add_argument("--seed", type=int, default=42, help="Seed for generation")
    parser.add_argument("--output", type=str, default="tools/map_generator_output.png", help="Output filepath")
    parser.add_argument("--no-roads", action="store_true", help="Do not generate roads or settlements")
    parser.add_argument("--damp", type=float, default=1.2, help="Island dampening factor (lower = larger island)")
    args = parser.parse_args()

    img = generate_map(size=args.size, scale=args.scale, seed=args.seed, no_roads=args.no_roads, damp_factor=args.damp)
    img.save(args.output)
    print(f"Map saved to {args.output}")

if __name__ == "__main__":
    main()
