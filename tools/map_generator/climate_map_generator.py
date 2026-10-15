import argparse
import math
import random
from PIL import Image, ImageDraw

# Precomputed noise grid for fast execution
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

# Biome definitions (temperature in C, humidity in range [0.0, 1.0])
BIOMES_DEFINITION = {
    "snow": {
        "ideal_temp_c": -15.0,
        "ideal_humidity": 0.1,
        "color": (240, 248, 255) # Ice White / Alice Blue
    },
    "tundra": {
        "ideal_temp_c": -5.0,
        "ideal_humidity": 0.15,
        "color": (191, 199, 175) # Muted Olive / Tundra Grey-Green
    },
    "taiga": {
        "ideal_temp_c": 5.0,
        "ideal_humidity": 0.6,
        "color": (46, 89, 66) # Spruce Green
    },
    "grassland": {
        "ideal_temp_c": 18.0,
        "ideal_humidity": 0.4,
        "color": (124, 181, 114) # Meadow Green
    },
    "temperate_deciduous_forest": {
        "ideal_temp_c": 15.0,
        "ideal_humidity": 0.7,
        "color": (52, 117, 72) # Rich Forest Green
    },
    "temperate_desert": {
        "ideal_temp_c": 25.0,
        "ideal_humidity": 0.1,
        "color": (230, 212, 158) # Sandy Yellow
    }
}

WATER_COLORS = {
    "deep": (29, 42, 68),      # Dark Blue
    "shallow": (44, 94, 138),  # Muted Light Blue
    "beach": (226, 195, 145)   # Sand/Beach
}

def match_biome(temp, humidity):
    """Euclidean distance matcher to classify biomes based on temp/humidity."""
    best_biome = "grassland"
    min_dist = float('inf')

    for biome_id, data in BIOMES_DEFINITION.items():
        # Match humidity scale (0..1) with temp scale using a 100x multiplier
        temp_diff = temp - data["ideal_temp_c"]
        humidity_diff = (humidity - data["ideal_humidity"]) * 100
        dist_sq = temp_diff**2 + humidity_diff**2
        if dist_sq < min_dist:
            min_dist = dist_sq
            best_biome = biome_id

    return best_biome

def get_distance_transform_128(water_mask_1024):
    """Calculate distance to nearest water pixel on a 128x128 grid (fast)."""
    ds_size = 128
    water_ds = [[False] * ds_size for _ in range(ds_size)]
    for y in range(ds_size):
        for x in range(ds_size):
            px = x * 8 + 4
            py = y * 8 + 4
            water_ds[y][x] = water_mask_1024[py][px]

    dist = [[999.0] * ds_size for _ in range(ds_size)]
    for y in range(ds_size):
        for x in range(ds_size):
            if water_ds[y][x]:
                dist[y][x] = 0.0

    # Pass 1: Top-to-bottom
    for y in range(ds_size):
        for x in range(ds_size):
            d = dist[y][x]
            if y > 0:
                d = min(d, dist[y - 1][x] + 1.0)
                if x > 0: d = min(d, dist[y - 1][x - 1] + 1.414)
                if x < ds_size - 1: d = min(d, dist[y - 1][x + 1] + 1.414)
            if x > 0:
                d = min(d, dist[y][x - 1] + 1.0)
            dist[y][x] = d

    # Pass 2: Bottom-to-top
    for y in range(ds_size - 1, -1, -1):
        for x in range(ds_size - 1, -1, -1):
            d = dist[y][x]
            if y < ds_size - 1:
                d = min(d, dist[y + 1][x] + 1.0)
                if x > 0: d = min(d, dist[y + 1][x - 1] + 1.414)
                if x < ds_size - 1: d = min(d, dist[y + 1][x + 1] + 1.414)
            if x < ds_size - 1:
                d = min(d, dist[y][x + 1] + 1.0)
            dist[y][x] = d

    return dist

def generate_climate_map(size=1024, scale=4.0, seed=42, damp=0.8, base_temp=10.0, sea_level=0.35, beach_level=0.38):
    random.seed(seed)
    global noise_grid_height, noise_grid_temp, noise_grid_hum
    noise_grid_height = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]
    noise_grid_temp = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]
    noise_grid_hum = [[random.random() for _ in range(NOISE_GRID_SIZE)] for _ in range(NOISE_GRID_SIZE)]

    print("Generating heightmap...")
    heightmap = [[0.0 for _ in range(size)] for _ in range(size)]
    water_mask = [[False for _ in range(size)] for _ in range(size)]

    # sea_level and beach_level are passed as arguments

    for y in range(size):
        for x in range(size):
            nx = (x / size) * scale
            ny = (y / size) * scale

            # Central island gradient
            dx = (x - size / 2) / (size / 2)
            dy = (y - size / 2) / (size / 2)
            dist = math.sqrt(dx*dx + dy*dy)
            damp_val = max(0.0, 1.0 - dist * damp)

            h = fbm(nx, ny, noise_grid_height, octaves=5)
            h = h * (0.3 + 0.7 * damp_val)
            heightmap[y][x] = h
            water_mask[y][x] = h < sea_level

    print("Computing water distance transform...")
    dist_ds = get_distance_transform_128(water_mask)

    # Upscale distance transform using Pillow bilinear resizing
    dist_img = Image.new("F", (128, 128))
    pixels_ds = dist_img.load()
    for y in range(128):
        for x in range(128):
            pixels_ds[x, y] = dist_ds[y][x]

    dist_img_large = dist_img.resize((size, size), Image.Resampling.BILINEAR)
    dist_pixels = dist_img_large.load()

    print("Generating temperature, humidity, and biomes...")
    img = Image.new("RGB", (size, size))
    pixels = img.load()

    # Discrete height tiers for cliff shading
    tiermap = [[0 for _ in range(size)] for _ in range(size)]
    for y in range(size):
        for x in range(size):
            # Map heights to 8 discrete tiers
            tiermap[y][x] = int(heightmap[y][x] * 12)

    for y in range(size):
        for x in range(size):
            h = heightmap[y][x]

            if h < sea_level:
                # Water biomes
                if h < 0.25:
                    base_color = WATER_COLORS["deep"]
                else:
                    base_color = WATER_COLORS["shallow"]
            elif h < beach_level:
                # Sand / beach biome
                base_color = WATER_COLORS["beach"]
            else:
                # Land biomes
                nx = (x / size) * (scale * 0.8)
                ny = (y / size) * (scale * 0.8)

                # Temperature: latitude/altitude gradient + noise offset
                # Altitude decreases temperature (-25C decrease at max height 1.0)
                # Latitude decreases temperature from South (bottom) to North (top)
                latitude_temp_mod = (1.0 - (y / size)) * 12.0 - 6.0  # -6C to +6C
                t_noise = fbm(nx + 10.0, ny + 10.0, noise_grid_temp, octaves=3) * 14.0 - 7.0
                temp = base_temp + latitude_temp_mod + t_noise - (h * 20.0)

                # Humidity: proximity to water + noise offset
                dist_meters = dist_pixels[x, y] * 8.0  # 128 grid scaled by 8
                proximity_bonus = math.exp(-dist_meters / 150.0) * 0.5  # Decay over 150m
                h_noise = fbm(nx + 20.0, ny + 20.0, noise_grid_hum, octaves=3)
                humidity = np_clip(h_noise * 0.6 + proximity_bonus, 0.0, 1.0)

                biome = match_biome(temp, humidity)
                base_color = BIOMES_DEFINITION[biome]["color"]

            # Shading for cliff edges (vertical height drops)
            is_cliff = False
            is_highlight = False
            tier = tiermap[y][x]

            if h >= sea_level:
                if x < size - 1:
                    right_tier = tiermap[y][x + 1]
                    if tier > right_tier:
                        is_cliff = True
                    elif tier < right_tier:
                        is_highlight = True
                if y < size - 1:
                    bottom_tier = tiermap[y + 1][x]
                    if tier > bottom_tier:
                        is_cliff = True
                    elif tier < bottom_tier:
                        is_highlight = True

            if is_cliff:
                shadow = (17, 20, 25)
                pixels[x, y] = (
                    int(base_color[0] * 0.55 + shadow[0] * 0.45),
                    int(base_color[1] * 0.55 + shadow[1] * 0.45),
                    int(base_color[2] * 0.55 + shadow[2] * 0.45)
                )
            elif is_highlight:
                highlight = (255, 255, 255)
                pixels[x, y] = (
                    int(base_color[0] * 0.75 + highlight[0] * 0.25),
                    int(base_color[1] * 0.75 + highlight[1] * 0.25),
                    int(base_color[2] * 0.75 + highlight[2] * 0.25)
                )
            else:
                pixels[x, y] = base_color

    return img

def np_clip(val, lo, hi):
    return max(lo, min(val, hi))

def main():
    parser = argparse.ArgumentParser(description="Generate climate-based biome maps.")
    parser.add_argument("--size", type=int, default=1024, help="Size of the image")
    parser.add_argument("--scale", type=float, default=4.0, help="Noise frequency scale")
    parser.add_argument("--damp", type=float, default=0.8, help="Island dampening")
    parser.add_argument("--temp", type=float, default=12.0, help="Base temperature in degrees C")
    parser.add_argument("--seed", type=int, default=42, help="Seed")
    parser.add_argument("--sea-level", type=float, default=0.35, help="Sea level threshold")
    parser.add_argument("--beach-level", type=float, default=0.38, help="Beach level threshold")
    parser.add_argument("--output", type=str, default="tools/climate_map_output.png", help="Output filepath")
    args = parser.parse_args()

    img = generate_climate_map(size=args.size, scale=args.scale, seed=args.seed, damp=args.damp, base_temp=args.temp, sea_level=args.sea_level, beach_level=args.beach_level)
    img.save(args.output)
    print(f"Climate-based biome map saved to {args.output}")

if __name__ == "__main__":
    main()
