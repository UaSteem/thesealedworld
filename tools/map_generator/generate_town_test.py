import os
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

def draw_town_schematic(output_path: str):
    """
    Generates a 7x7 node schematic map where each node is exactly 256x256 px.
    Total size: 1792x1792 px.
    The center node (3, 3) is a flat, square medieval fort with irregular blocks.
    """
    node_size = 256
    nodes_count = 7
    size = node_size * nodes_count # 1792 px

    # Base: meadow green
    img = Image.new("RGB", (size, size), (124, 181, 114))
    draw = ImageDraw.Draw(img)

    # 1. Forests (dark green patches in the corners)
    draw.rectangle([0, 0, 2 * node_size, 2 * node_size], fill=(52, 117, 72))
    draw.rectangle([5 * node_size, 0, size, 2 * node_size], fill=(52, 117, 72))
    draw.rectangle([0, 5 * node_size, 2 * node_size, size], fill=(52, 117, 72))
    draw.rectangle([5 * node_size, 5 * node_size, size, size], fill=(52, 117, 72))

    # 2. Winding River (blue line, width=20px)
    river_points = [
        (0, int(2.5 * node_size)),
        (int(1.5 * node_size), int(2.5 * node_size)),
        (int(2.2 * node_size), int(1.8 * node_size)),
        (int(2.2 * node_size), int(0.8 * node_size)),
        (int(3.2 * node_size), int(0.5 * node_size)),
        (int(4.5 * node_size), int(0.5 * node_size)),
        (size, int(0.5 * node_size))
    ]
    for i in range(len(river_points) - 1):
        draw.line([river_points[i], river_points[i+1]], fill=(44, 94, 138), width=20)

    # 3. Roads branching from the borders of the center node (3, 3)
    cx_start = 3 * node_size # 768
    cy_start = 3 * node_size # 768
    cx_center = cx_start + node_size // 2 # 896
    cy_center = cy_start + node_size // 2 # 896
    margin = 48
    town_w = node_size - 2 * margin # 160 px

    road_width = 12
    draw.line([(cx_center, cy_start + margin), (cx_center, 0)], fill=(120, 120, 120), width=road_width)
    draw.line([(cx_center, cy_start + node_size - margin), (cx_center, size)], fill=(120, 120, 120), width=road_width)
    draw.line([(cx_start + margin, cy_center), (0, cy_center)], fill=(120, 120, 120), width=road_width)
    draw.line([(cx_start + node_size - margin, cy_center), (size, cy_center)], fill=(120, 120, 120), width=road_width)

    # 4. Center City Node (3, 3) - A flat square/irregular fort
    # Bounding box: [768..1024, 768..1024].
    # We make a square town with a margin of 48 px.
    cx = cx_start + margin
    cy = cy_start + margin

    # Square outer fortified walls
    draw.rectangle([cx, cy, cx + town_w, cy + town_w], fill=(130, 130, 130), outline=(60, 60, 60), width=6)
    # Paved courtyard
    draw.rectangle([cx + 6, cy + 6, cx + town_w - 6, cy + town_w - 6], fill=(160, 160, 160))

    # Tiny rectangular houses (representing blocks)
    house_color = (190, 80, 60)
    # Block 1 (top-left)
    draw.rectangle([cx + 20, cy + 20, cx + 60, cy + 45], fill=house_color, outline=(100, 40, 30))
    # Block 2 (top-right)
    draw.rectangle([cx + town_w - 60, cy + 20, cx + town_w - 20, cy + 45], fill=house_color, outline=(100, 40, 30))
    # Block 3 (bottom-left)
    draw.rectangle([cx + 20, cy + town_w - 45, cx + 60, cy + town_w - 20], fill=house_color, outline=(100, 40, 30))
    # Block 4 (bottom-right)
    draw.rectangle([cx + town_w - 60, cy + town_w - 45, cx + town_w - 20, cy + town_w - 20], fill=house_color, outline=(100, 40, 30))

    # Central Keep (flat square with inner square roof, 30x30 px)
    draw.rectangle([cx + town_w//2 - 15, cy + town_w//2 - 15, cx + town_w//2 + 15, cy + town_w//2 + 15], fill=(100, 100, 100), outline=(50, 50, 50), width=3)
    draw.rectangle([cx + town_w//2 - 10, cy + town_w//2 - 10, cx + town_w//2 + 10, cy + town_w//2 + 10], fill=(210, 70, 60))

    # Save schematic
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Square town schematic saved to {output_path} (1792x1792 px)")

def slice_town_map(rendered_image_path: str, output_dir: str):
    """
    Slices the 1792x1792 px rendered image into 7x7 tiles of 256x256 px.
    """
    rendered_img = Image.open(rendered_image_path).convert("RGB")

    if rendered_img.size != (1792, 1792):
        print(f"Warning: Image size is {rendered_img.size}, resizing to 1792x1792 px...")
        rendered_img = rendered_img.resize((1792, 1792), Image.Resampling.LANCZOS)

    out_path = Path(output_dir)
    out_tiles = out_path / "tiles"
    out_tiles.mkdir(parents=True, exist_ok=True)

    tile_size = 256
    nodes_count = 7

    for y in range(nodes_count):
        for x in range(nodes_count):
            left = x * tile_size
            top = y * tile_size
            right = left + tile_size
            bottom = top + tile_size

            tile = rendered_img.crop((left, top, right, bottom))
            tile.save(out_tiles / f"tile_{x}_{y}.webp", "WEBP", quality=90)

    print("Slicing complete!")
    print(f"Saved tiles to {out_tiles}")
    print(f"City tile (node 3_3) saved to {out_tiles / 'tile_3_3.webp'}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_town_test.py schematic <output_path>")
        print("  python generate_town_test.py slice <rendered_path> <output_dir>")
    elif sys.argv[1] == "schematic":
        draw_town_schematic(sys.argv[2])
    elif sys.argv[1] == "slice":
        slice_town_map(sys.argv[2], sys.argv[3])
