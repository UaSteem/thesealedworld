import argparse
import os
from pathlib import Path
from PIL import Image, ImageDraw

def prepare_node_generation(
    node_x: int,
    node_y: int,
    schematics_dir: str,
    rendered_dir: str,
    output_dir: str,
    border_width: int = 128,
    node_size: int = 1024
):
    """
    Prepares the input image and inpainting mask for Stable Diffusion (img2img inpaint)
    to generate a seamless adjacent node.

    - If left neighbor (x-1, y) is already rendered, copies its right border.
    - If top neighbor (x, y-1) is already rendered, copies its bottom border.
    - If top-left neighbor (x-1, y-1) is already rendered, copies its bottom-right corner.
    - Generates a black/white mask (0/black = keep original borders, 255/white = generate new content).
    - Uses the schematic map as the base guide.
    """
    schematics_path = Path(schematics_dir)
    rendered_path = Path(rendered_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load the schematic for current node
    schematic_file = schematics_path / f"node_{node_x}_{node_y}.png"
    if not schematic_file.exists():
        raise FileNotFoundError(f"Schematic not found: {schematic_file}")

    # We start with the schematic as the base initial image
    base_img = Image.open(schematic_file).convert("RGB")
    if base_img.size != (node_size, node_size):
        base_img = base_img.resize((node_size, node_size), Image.Resampling.LANCZOS)

    # Create the mask: initially all white (255 = inpaint everything)
    mask = Image.new("L", (node_size, node_size), 255)
    mask_draw = ImageDraw.Draw(mask)

    left_neighbor = rendered_path / f"rendered_{node_x-1}_{node_y}.png"
    top_neighbor = rendered_path / f"rendered_{node_x}_{node_y-1}.png"
    top_left_neighbor = rendered_path / f"rendered_{node_x-1}_{node_y-1}.png"

    # 2. Paste left neighbor's right border
    if left_neighbor.exists():
        print(f"Applying left border lock from {left_neighbor.name}")
        left_img = Image.open(left_neighbor).convert("RGB")
        # Crop the rightmost border_width columns
        left_border = left_img.crop((node_size - border_width, 0, node_size, node_size))
        # Paste it to the leftmost border_width columns of base_img
        base_img.paste(left_border, (0, 0))
        # Mark in mask as black (0 = do not change)
        mask_draw.rectangle([0, 0, border_width, node_size], fill=0)

    # 3. Paste top neighbor's bottom border
    if top_neighbor.exists():
        print(f"Applying top border lock from {top_neighbor.name}")
        top_img = Image.open(top_neighbor).convert("RGB")
        # Crop the bottommost border_width rows
        top_border = top_img.crop((0, node_size - border_width, node_size, node_size))
        # Paste it to the topmost border_width rows of base_img
        base_img.paste(top_border, (0, 0))
        # Mark in mask as black (0 = do not change)
        mask_draw.rectangle([0, 0, node_size, border_width], fill=0)

    # 4. Paste top-left neighbor's bottom-right corner to resolve overlapping corner
    if top_left_neighbor.exists() and left_neighbor.exists() and top_neighbor.exists():
        print(f"Applying top-left corner lock from {top_left_neighbor.name}")
        tl_img = Image.open(top_left_neighbor).convert("RGB")
        tl_corner = tl_img.crop((node_size - border_width, node_size - border_width, node_size, node_size))
        base_img.paste(tl_corner, (0, 0))
        mask_draw.rectangle([0, 0, border_width, border_width], fill=0)

    # Save prepared files
    init_out = out_path / f"init_{node_x}_{node_y}.png"
    mask_out = out_path / f"mask_{node_x}_{node_y}.png"

    base_img.save(init_out)
    mask.save(mask_out)

    print(f"Prepared files for node {node_x}_{node_y}:")
    print(f"  - Initial image (with locked borders): {init_out}")
    print(f"  - Inpaint mask (0=lock, 255=generate): {mask_out}")
    print(f"  - Guide schematic (ControlNet input): {schematic_file}")

    # Generate API payload snippet for Stable Diffusion (Automatic1111)
    print("\n--- Automatic1111 API Payload suggestion ---")
    payload = {
        "init_images": ["<base64_encoded_init_image>"],
        "mask": "<base64_encoded_mask_image>",
        "mask_blur": 4,
        "inpainting_fill": 1, # latent noise (generates new content based on prompt)
        "inpaint_full_res": False,
        "inpainting_mask_invert": 0, # Inpaint masked
        "prompt": "top-down RPG map, highly detailed, matching the biomes...",
        "negative_prompt": "blurry, low quality, 3d, perspectives, shadows",
        "width": node_size,
        "height": node_size,
        "alwayson_scripts": {
            "ControlNet": {
                "args": [
                    {
                        "input_image": "<base64_encoded_schematic_image>",
                        "module": "none",
                        "model": "control_v11p_sd15_scribble [docker]", # or seg/lineart
                        "weight": 1.0
                    }
                ]
            }
        }
    }
    print("Use these prepared images with SD inpaint to generate a seamless transition!")

def main():
    parser = argparse.ArgumentParser(description="Prepare seamless node generation using inpainting border masks.")
    parser.add_argument("--x", type=int, required=True, help="Node X coordinate")
    parser.add_argument("--y", type=int, required=True, help="Node Y coordinate")
    parser.add_argument("--schematics", type=str, default="tools/output/region_1337/schematics", help="Directory with schematic files")
    parser.add_argument("--rendered", type=str, default="tools/output/region_1337/rendered", help="Directory where generated HD nodes are stored")
    parser.add_argument("--output", type=str, default="tools/output/region_1337/prepared", help="Output directory for generated masks/inits")
    parser.add_argument("--border", type=int, default=128, help="Width of the overlapping seam to lock")
    parser.add_argument("--size", type=int, default=1024, help="Size of the node image")

    args = parser.parse_args()

    prepare_node_generation(
        node_x=args.x,
        node_y=args.y,
        schematics_dir=args.schematics,
        rendered_dir=args.rendered,
        output_dir=args.output,
        border_width=args.border,
        node_size=args.size
    )

if __name__ == "__main__":
    main()
