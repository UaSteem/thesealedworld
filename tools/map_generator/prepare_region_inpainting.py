import argparse
import os
from pathlib import Path
from PIL import Image, ImageDraw

def prepare_region_generation(
    rx: int,
    ry: int,
    schematics_dir: str,
    rendered_dir: str,
    output_dir: str,
    tile_size: int = 256,
    overlap_nodes: int = 2,
    nodes_count: int = 17
):
    """
    Prepares the initial image and inpainting mask for a 4K region (17x17 nodes)
    to align it seamlessly with its already generated neighbors in the 7x7 grid.

    - Overlap is 2 nodes (2 * 256 = 512 pixels).
    - If left region (rx-1, ry) exists, copies its rightmost 512px.
    - If top region (rx, ry-1) exists, copies its bottommost 512px.
    - If top-left region (rx-1, ry-1) exists, copies its bottom-right 512x512px corner.
    """
    schematics_path = Path(schematics_dir)
    rendered_path = Path(rendered_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    region_size_px = nodes_count * tile_size # 17 * 256 = 4352 px
    overlap_px = overlap_nodes * tile_size   # 2 * 256 = 512 px

    # 1. Load the schematic for current region
    schematic_file = schematics_path / f"region_{rx}_{ry}.png"
    if not schematic_file.exists():
        # Fallback to search any region schematic file or create placeholder
        print(f"Warning: Region schematic {schematic_file} not found. Creating a blank placeholder guide.")
        base_img = Image.new("RGB", (region_size_px, region_size_px), (124, 181, 114))
    else:
        base_img = Image.open(schematic_file).convert("RGB")
        if base_img.size != (region_size_px, region_size_px):
            base_img = base_img.resize((region_size_px, region_size_px), Image.Resampling.LANCZOS)

    # Create the mask: initially all white (255 = inpaint/generate everything)
    mask = Image.new("L", (region_size_px, region_size_px), 255)
    mask_draw = ImageDraw.Draw(mask)

    left_region = rendered_path / f"region_{rx-1}_{ry}.png"
    top_region = rendered_path / f"region_{rx}_{ry-1}.png"
    top_left_region = rendered_path / f"region_{rx-1}_{ry-1}.png"

    # 2. Paste left region's right border (512px)
    if rx > 0 and left_region.exists():
        print(f"Applying left region border lock from {left_region.name}")
        left_img = Image.open(left_region).convert("RGB")
        if left_img.size != (region_size_px, region_size_px):
            left_img = left_img.resize((region_size_px, region_size_px), Image.Resampling.LANCZOS)
        # Crop the rightmost 512px
        left_border = left_img.crop((region_size_px - overlap_px, 0, region_size_px, region_size_px))
        # Paste it to the leftmost 512px of base_img
        base_img.paste(left_border, (0, 0))
        # Mark in mask as black (0 = lock)
        mask_draw.rectangle([0, 0, overlap_px, region_size_px], fill=0)

    # 3. Paste top region's bottom border (512px)
    if ry > 0 and top_region.exists():
        print(f"Applying top region border lock from {top_region.name}")
        top_img = Image.open(top_region).convert("RGB")
        if top_img.size != (region_size_px, region_size_px):
            top_img = top_img.resize((region_size_px, region_size_px), Image.Resampling.LANCZOS)
        # Crop the bottommost 512px
        top_border = top_img.crop((0, region_size_px - overlap_px, region_size_px, region_size_px))
        # Paste it to the topmost 512px of base_img
        base_img.paste(top_border, (0, 0))
        # Mark in mask as black (0 = lock)
        mask_draw.rectangle([0, 0, region_size_px, overlap_px], fill=0)

    # 4. Paste top-left region's bottom-right corner (512x512px)
    if rx > 0 and ry > 0 and top_left_region.exists() and left_region.exists() and top_region.exists():
        print(f"Applying top-left corner lock from {top_left_region.name}")
        tl_img = Image.open(top_left_region).convert("RGB")
        if tl_img.size != (region_size_px, region_size_px):
            tl_img = tl_img.resize((region_size_px, region_size_px), Image.Resampling.LANCZOS)
        tl_corner = tl_img.crop((region_size_px - overlap_px, region_size_px - overlap_px, region_size_px, region_size_px))
        base_img.paste(tl_corner, (0, 0))
        mask_draw.rectangle([0, 0, overlap_px, overlap_px], fill=0)

    # Save prepared files
    init_out = out_path / f"init_region_{rx}_{ry}.png"
    mask_out = out_path / f"mask_region_{rx}_{ry}.png"

    base_img.save(init_out)
    mask.save(mask_out)

    print(f"Prepared files for region {rx}_{ry}:")
    print(f"  - Initial image (with locked borders): {init_out}")
    print(f"  - Inpaint mask (0=lock, 255=generate): {mask_out}")
    if schematic_file.exists():
        print(f"  - Guide schematic (ControlNet input): {schematic_file}")

    print("\n--- Stable Diffusion API Payload suggestion ---")
    print(f"Generate Region ({rx}, {ry}) in size {region_size_px}x{region_size_px} using:")
    print(f"  1. Input Image: {init_out.name}")
    print(f"  2. Inpainting Mask: {mask_out.name}")
    print(f"  3. Mask Mode: Inpaint masked")
    print(f"  4. ControlNet schematic input for structure alignment.")

def main():
    parser = argparse.ArgumentParser(description="Prepare seamless 4K region generation using inpainting border masks.")
    parser.add_argument("--rx", type=int, required=True, help="Region X index (0..6)")
    parser.add_argument("--ry", type=int, required=True, help="Region Y index (0..6)")
    parser.add_argument("--schematics", type=str, default="tools/output/schematics", help="Directory with region schematic files")
    parser.add_argument("--rendered", type=str, default="tools/output/rendered_regions", help="Directory where generated 4K region images are stored")
    parser.add_argument("--output", type=str, default="tools/output/prepared_regions", help="Output directory for generated masks/inits")
    parser.add_argument("--tile-size", type=int, default=256, help="Tile size in pixels (default: 256)")
    parser.add_argument("--overlap-nodes", type=int, default=2, help="Number of overlapping nodes at borders (default: 2)")
    parser.add_argument("--nodes", type=int, default=17, help="Number of nodes per region side (default: 17)")

    args = parser.parse_args()

    prepare_region_generation(
        rx=args.rx,
        ry=args.ry,
        schematics_dir=args.schematics,
        rendered_dir=args.rendered,
        output_dir=args.output,
        tile_size=args.tile_size,
        overlap_nodes=args.overlap_nodes,
        nodes_count=args.nodes
    )

if __name__ == "__main__":
    main()
