import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.tileset_builder.rift_template import (  # noqa: E402
    CELL_SIZE,
    GRID_SIZE,
    SLICE_HEX_H,
    SLICE_HEX_W,
    build_tile_specs,
    build_tileset_data,
    get_hex_vertices,
)


def slice_tileset(
    image_path: Path,
    output_dir: Path,
    *,
    theme_name: str | None = None,
    write_runtime: bool = True,
):
    print(f"Loading generated image: {image_path.name}")
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    if img.size != (4096, 4096):
        print("Image must be exactly 4096x4096!")
        return

    print("Generating perfect mathematical hex mask...")
    img_size = GRID_SIZE * CELL_SIZE

    # Create a pure alpha mask mathematically
    mask_layer = Image.new("L", (img_size, img_size), 0)
    mask_draw = ImageDraw.Draw(mask_layer)

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cx = c * CELL_SIZE + CELL_SIZE / 2.0
            cy = r * CELL_SIZE + CELL_SIZE / 2.0

            outer_v = get_hex_vertices(cx, cy, SLICE_HEX_W, SLICE_HEX_H)
            mask_draw.polygon(outer_v, fill=255)

    print("Applying mask...")
    img.putalpha(mask_layer)

    theme_name = theme_name or output_dir.parent.name
    assets_dir = ROOT / "assets" / "tilesets" / theme_name / "tiles"
    backend_resource_dir = (
        ROOT
        / "src"
        / "backend"
        / "features"
        / "rift"
        / "resources"
        / "json"
        / "tile_sets"
        / theme_name
    )
    image_output_dirs = [assets_dir]
    metadata_output_dirs = [assets_dir]
    if write_runtime:
        image_output_dirs.insert(0, output_dir)
        metadata_output_dirs.insert(0, backend_resource_dir)

    print(f"Saving 64 tiles to {', '.join(str(path) for path in image_output_dirs)}...")
    for image_output_dir in image_output_dirs:
        image_output_dir.mkdir(parents=True, exist_ok=True)
    for metadata_output_dir in metadata_output_dirs:
        metadata_output_dir.mkdir(parents=True, exist_ok=True)

    tile_specs = build_tile_specs()
    tileset_data = build_tileset_data(theme_name)

    for tile_spec in tile_specs:
        left = tile_spec.col * CELL_SIZE
        top = tile_spec.row * CELL_SIZE
        right = left + CELL_SIZE
        bottom = top + CELL_SIZE

        tile = img.crop((left, top, right, bottom))
        tile_filename = tile_spec.file
        for image_output_dir in image_output_dirs:
            tile.save(image_output_dir / tile_filename)

    for metadata_dir in metadata_output_dirs:
        with open(metadata_dir / "tileset_data.json", "w", encoding="utf-8") as f:
            json.dump(tileset_data, f, indent=2)

    print(
        "Successfully sliced 64 tiles. "
        f"Images: {', '.join(str(path) for path in image_output_dirs)}. "
        f"Metadata: {', '.join(str(path / 'tileset_data.json') for path in metadata_output_dirs)}"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", type=str, help="Path to the 4K generated image")
    parser.add_argument("--theme", type=str, required=True, help="Theme name (e.g., void_temple)")
    parser.add_argument("--asset-key", type=str, help="Assets folder name. Defaults to --theme.")
    parser.add_argument("--assets-only", action="store_true", help="Only write assets/tilesets output.")
    args = parser.parse_args()

    image_path = Path(args.image_path)
    output_dir = ROOT / "src" / "frontend" / "static" / "images" / "rift" / args.theme / "tiles"

    slice_tileset(
        image_path,
        output_dir,
        theme_name=args.asset_key or args.theme,
        write_runtime=not args.assets_only,
    )

if __name__ == "__main__":
    main()
