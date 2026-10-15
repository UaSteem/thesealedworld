import os
import math
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw

def generate_test_schematics():
    """
    Generates two overlapping region schematics (A and B) representing adjacent regions.
    Region A covers columns 0..9, Region B covers columns 8..17.
    Overlap is 2 columns (nodes 8 and 9).
    Node size is 64x64 px, so region image size is 640x640 px.
    Total width is 18 nodes (1152 px).
    """
    out_dir = Path("tools/output/test_seamless")
    out_dir.mkdir(parents=True, exist_ok=True)

    node_size = 64
    nodes_x = 18 # 0..17
    nodes_y = 10
    width = nodes_x * node_size  # 1152 px
    height = nodes_y * node_size # 640 px

    # Simple procedurally drawn landscape
    img = Image.new("RGB", (width, height), (124, 181, 114)) # Meadow green base
    draw = ImageDraw.Draw(img)

    # 1. Forest at the top (dark green)
    draw.rectangle([0, 0, width, 3 * node_size], fill=(52, 117, 72))

    # 2. Water at the bottom (blue)
    draw.rectangle([0, 8 * node_size, width, height], fill=(44, 94, 138))
    # Sand beach
    draw.rectangle([0, 7 * node_size, width, 8 * node_size], fill=(226, 195, 145))

    # 3. Horizontal winding road in the middle
    road_points = []
    random.seed(42)
    current_y = 5 * node_size
    for x in range(0, width + 50, 50):
        current_y += random.randint(-40, 40)
        current_y = max(3.5 * node_size, min(6.5 * node_size, current_y))
        road_points.append((x, int(current_y)))

    # Draw road (grey)
    for i in range(len(road_points) - 1):
        p1 = road_points[i]
        p2 = road_points[i+1]
        draw.line([p1, p2], fill=(120, 120, 120), width=18)

    # Save the global test map
    img.save(out_dir / "global_schematic.png")

    # Slice Region A (0..10 nodes -> 0..640 px)
    region_A = img.crop((0, 0, 10 * node_size, 10 * node_size))
    region_A.save(out_dir / "schematic_A.png")

    # Slice Region B (8..18 nodes -> 512..1152 px)
    region_B = img.crop((8 * node_size, 0, 18 * node_size, 10 * node_size))
    region_B.save(out_dir / "schematic_B.png")

    print("Generated test schematics:")
    print(f"  - Region A: {out_dir / 'schematic_A.png'} (640x640)")
    print(f"  - Region B: {out_dir / 'schematic_B.png'} (640x640)")
    print(f"  - Overlap is columns 8 and 9 (pixel range [512..640] in A and [0..128] in B)")

def prepare_composite_B(rendered_A_path: str):
    """
    Takes the rendered Region A, crops its rightmost 128px,
    pastes it onto Region B's schematic, and saves it as init_B.png.
    Also creates a mask where the left 128px is black (locked) and the rest is white.
    """
    out_dir = Path("tools/output/test_seamless")
    schematic_B_path = out_dir / "schematic_B.png"

    if not schematic_B_path.exists():
        raise FileNotFoundError("Run phase 1 first to generate schematics.")

    img_A = Image.open(rendered_A_path).convert("RGB")
    schematic_B = Image.open(schematic_B_path).convert("RGB")

    img_A = img_A.resize((640, 640), Image.Resampling.LANCZOS)

    border = img_A.crop((640 - 128, 0, 640, 640))

    init_B = schematic_B.copy()
    init_B.paste(border, (0, 0))
    init_B.save(out_dir / "init_B.png")

    mask = Image.new("L", (640, 640), 255)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle([0, 0, 128, 640], fill=0)
    mask.save(out_dir / "mask_B.png")

    print("Prepared Region B composite:")
    print(f"  - Initial image for B (with A border): {out_dir / 'init_B.png'}")
    print(f"  - Mask for B (0=lock, 255=generate): {out_dir / 'mask_B.png'}")

def analyze_boundary():
    """
    Analyzes the boundary column (x = 640 in global schematic, which corresponds to the
    border between Node A and Node B) to determine if it is walkable, blocked by water/cliffs,
    or has a road/bridge.
    """
    out_dir = Path("tools/output/test_seamless")
    global_schematic_path = out_dir / "global_schematic.png"

    if not global_schematic_path.exists():
        raise FileNotFoundError(f"Global schematic not found: {global_schematic_path}")

    img = Image.open(global_schematic_path).convert("RGB")
    width, height = img.size

    # We analyze the vertical line at x = 640 (which is the start of Region B, matching index 8 of A)
    border_x = 640

    # Define colors
    COLOR_WATER = (44, 94, 138)
    COLOR_ROAD = (120, 120, 120)
    COLOR_FOREST = (52, 117, 72)
    COLOR_MEADOW = (124, 181, 114)
    COLOR_BEACH = (226, 195, 145)

    # Classify each pixel along the boundary
    pixel_classes = []
    for y in range(height):
        color = img.getpixel((border_x, y))

        # Color match with a small tolerance
        if color == COLOR_ROAD:
            cls = "road"
        elif color == COLOR_WATER:
            cls = "water"
        else:
            cls = "walkable"
        pixel_classes.append((y, cls, color))

    # Group into contiguous segments
    segments = []
    current_cls = pixel_classes[0][1]
    start_y = 0
    for y in range(1, height):
        cls = pixel_classes[y][1]
        if cls != current_cls:
            segments.append({
                "class": current_cls,
                "start": start_y,
                "end": y - 1,
                "length": y - start_y
            })
            current_cls = cls
            start_y = y
    segments.append({
        "class": current_cls,
        "start": start_y,
        "end": height - 1,
        "length": height - start_y
    })

    print("=== BOUNDARY ANALYZER RESULTS ===")
    print(f"Analyzing vertical boundary at x={border_x} px...")
    print("Detected segments:")

    can_cross = False
    reasons = []

    for seg in segments:
        print(f"  y: {seg['start']:03d}..{seg['end']:03d} | Class: {seg['class']:<8} | Size: {seg['length']}px")
        if seg['class'] == "road":
            can_cross = True
            reasons.append(f"Road/Bridge at y={seg['start']}-{seg['end']}")
        elif seg['class'] == "walkable" and seg['length'] >= 20:
            can_cross = True
            reasons.append(f"Walkable meadow/forest opening of size {seg['length']}px at y={seg['start']}-{seg['end']}")

    print("-" * 34)
    if can_cross:
        print(f"STATUS: OPEN (Passage between Node A and Node B exists)")
        print("Reasons:")
        for r in reasons:
            print(f"  - {r}")
    else:
        print(f"STATUS: BLOCKED (No walkable passages found between Node A and Node B)")
        print("  - Water or cliffs block the entire border with no bridge/road.")

    # Let's generate a visual visualization of the boundary classification
    visual_img = img.copy()
    draw = ImageDraw.Draw(visual_img)
    # Draw vertical analysis line
    for seg in segments:
        color = (255, 0, 0) if seg['class'] == "water" else ((0, 255, 0) if seg['class'] == "road" else (255, 255, 0))
        draw.line([border_x, seg['start'], border_x, seg['end']], fill=color, width=5)
        # Draw text label
        draw.text((border_x + 10, seg['start'] + 2), f"{seg['class']} ({seg['length']}px)", fill=color)

    visual_img.save(out_dir / "boundary_analysis_viz.png")
    print(f"Saved boundary analysis visualization to {out_dir / 'boundary_analysis_viz.png'}")

def stitch_results(rendered_A_path: str, rendered_B_path: str):
    """
    Stitches the rendered Region A and Region B side-by-side.
    """
    out_dir = Path("tools/output/test_seamless")
    img_A = Image.open(rendered_A_path).convert("RGB").resize((640, 640), Image.Resampling.LANCZOS)
    img_B = Image.open(rendered_B_path).convert("RGB").resize((640, 640), Image.Resampling.LANCZOS)

    stitched = Image.new("RGB", (1152, 640))
    stitched.paste(img_A, (0, 0))
    img_B_cropped = img_B.crop((128, 0, 640, 640))
    stitched.paste(img_B_cropped, (640, 0))

    result_path = out_dir / "stitched_test_result.png"
    stitched.save(result_path)
    print(f"Stitched result saved to {result_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_seamless_regions.py schematics")
        print("  python test_seamless_regions.py prepare <rendered_A_path>")
        print("  python test_seamless_regions.py analyze")
        print("  python test_seamless_regions.py stitch <rendered_A_path> <rendered_B_path>")
    elif sys.argv[1] == "schematics":
        generate_test_schematics()
    elif sys.argv[1] == "prepare":
        prepare_composite_B(sys.argv[2])
    elif sys.argv[1] == "analyze":
        analyze_boundary()
    elif sys.argv[1] == "stitch":
        stitch_results(sys.argv[2], sys.argv[3])
