import os
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

def draw_global_schematic(output_path: str):
    """
    Draws a 17x17 node schematic map of the global region.
    Total size: 2176x2176 px (17 nodes * 128 px per node).
    The center node (8, 8) is the fortified city.
    """
    node_size = 128
    nodes_count = 17
    size = node_size * nodes_count # 2176 px

    # Base: meadow green
    img = Image.new("RGB", (size, size), (124, 181, 114))
    draw = ImageDraw.Draw(img)

    # 1. Forests (dark green patches) - keeping them far away from the center node
    draw.rectangle([0, 0, 5 * node_size, 5 * node_size], fill=(52, 117, 72))
    draw.rectangle([12 * node_size, 0, size, 5 * node_size], fill=(52, 117, 72))
    draw.rectangle([0, 12 * node_size, 5 * node_size, size], fill=(52, 117, 72))
    draw.rectangle([12 * node_size, 12 * node_size, size, size], fill=(52, 117, 72))

    # 2. Winding River (blue line) - keeping it away from center node (8,8)
    river_points = [
        (0, 5 * node_size),
        (3 * node_size, 5 * node_size),
        (4 * node_size, 6 * node_size),
        (4 * node_size, 10 * node_size),
        (6 * node_size, 11 * node_size),
        (11 * node_size, 11 * node_size),
        (13 * node_size, 11 * node_size),
        (size, 11 * node_size)
    ]
    for i in range(len(river_points) - 1):
        draw.line([river_points[i], river_points[i+1]], fill=(44, 94, 138), width=24)

    # 3. Roads branching from the borders of the center node (8, 8)
    cx_start = 8 * node_size # 1024
    cy_start = 8 * node_size # 1024
    cx_center = cx_start + node_size // 2 # 1088
    cy_center = cy_start + node_size // 2 # 1088

    # Roads only start outside the 1-node city cell to connect it to the world
    draw.line([(cx_center, cy_start), (cx_center, 0)], fill=(120, 120, 120), width=10)
    draw.line([(cx_center, cy_start + node_size), (cx_center, size)], fill=(120, 120, 120), width=10)
    draw.line([(cx_start, cy_center), (0, cx_center)], fill=(120, 120, 120), width=10)
    draw.line([(cx_start + node_size, cy_center), (size, cy_center)], fill=(120, 120, 120), width=10)

    # 4. Center City Node (8, 8) - A single tiny castle icon (50x50 px)
    # This represents a single location on the global map.
    margin = 39 # (128 - 50) // 2 = 39
    cx = cx_start + margin
    cy = cy_start + margin
    city_width = 50

    # Draw a distinct small grey castle keep
    draw.rectangle([cx, cy, cx + city_width, cy + city_width], fill=(120, 120, 120), outline=(60, 60, 60), width=4)
    # Red roof peak
    draw.polygon([
        (cx, cy),
        (cx + city_width // 2, cy - 15),
        (cx + city_width, cy)
    ], fill=(180, 60, 50))
    # Little yellow gate/door
    draw.rectangle([cx + 18, cy + 30, cx + 32, cy + 50], fill=(220, 180, 80))

    # Save schematic
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Global region schematic saved to {output_path} (2176x2176 px)")

def slice_and_upscale_map(rendered_image_path: str, output_dir: str):
    """
    Takes the rendered 2176x2176 px image, upscales it 2x to 4352x4352 px
    (so each node becomes 256x256 px), and slices it into 17x17 tiles.
    """
    rendered_img = Image.open(rendered_image_path).convert("RGB")

    print("Upscaling image to 4352x4352 px...")
    large_img = rendered_img.resize((4352, 4352), Image.Resampling.LANCZOS)

    out_path = Path(output_dir)
    out_tiles = out_path / "tiles"
    out_tiles.mkdir(parents=True, exist_ok=True)

    large_img.save(out_path / "upscaled_global_map.png")

    print("Slicing into 17x17 tiles of size 256x256...")
    tile_size = 256
    nodes_count = 17

    for y in range(nodes_count):
        for x in range(nodes_count):
            left = x * tile_size
            top = y * tile_size
            right = left + tile_size
            bottom = top + tile_size

            tile = large_img.crop((left, top, right, bottom))
            tile.save(out_tiles / f"tile_{x}_{y}.webp", "WEBP", quality=90)

    print("Slicing complete!")
    print(f"Saved tiles to {out_tiles}")
    print(f"City tile (node 8_8) saved to {out_tiles / 'tile_8_8.webp'}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_global_test.py schematic <output_path>")
        print("  python generate_global_test.py slice <rendered_path> <output_dir>")
    elif sys.argv[1] == "schematic":
        draw_global_schematic(sys.argv[2])
    elif sys.argv[1] == "slice":
        slice_and_upscale_map(sys.argv[2], sys.argv[3])
