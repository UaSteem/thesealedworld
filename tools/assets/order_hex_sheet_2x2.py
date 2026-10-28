"""Order the 1024x1024 (2x2 cells of 512x512) Flat-Top Hex Sheet (Player Frame, Monster Frame, Boss Frame, Empty Tile) via Gemini API in Style 1B and build Alpha-Cutout Resource Slot versions."""
import io
import math
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFilter

from make_hex_sheet_2x2_mask import (
    flat_hex_pts,
    make_chamfered_bar_slot,
    draw_monster_corner_claws,
    draw_boss_corner_spikes,
)


PROMPT = """Create a 1024x1024 2D game UI & battlefield sprite sheet arranged in a strict 2x2 grid (four 512x512 cells) on a solid pure black (#000000) background, in pure 90-degree orthographic TOP-DOWN view.

CRITICAL GEOMETRY & ORIENTATION RULES:
- ALL 4 HEXAGONS MUST BE STRICTLY FLAT-TOP HEXAGONS (horizontal flat top edge, horizontal flat bottom edge, pointed vertices on the far left and far right — NEVER pointy-top!).
- Image 1 is the exact structural blueprint of the 4 FLAT-TOP hexagons.
- Image 2 is the strict binary silhouette mask of the 4 FLAT-TOP hexagons.
- Image 3 and Image 4 are the exact FLAT-TOP hexagon material & style references: notice how every hexagon in Image 3 and Image 4 has a horizontal flat top edge and horizontal flat bottom edge!
- On the 3 frames ([1,1] Player, [1,2] Monster, [2,1] Boss), the 3 elongated pointed recessed resource bar slots are located on the 3 TOP edges: Top-Left diagonal edge, Top-Flat horizontal edge, and Top-Right diagonal edge.
- Do NOT draw any white outlines around the outer borders. Stay strictly inside the white shapes of Image 2.

EXACT CONTENTS OF THE 4 CELLS (512x512 each):
1. Top-Left [1,1] (center 256,256) — PLAYER CHARACTER HEX FRAME (FLAT-TOP hexagon):
   - Directly matches the central hexagon of Image 3: noble weathered dark bronze and sharp double-beveled antique gold rims, 6 faceted cyan diamond gems at the 6 corners, 3 elongated pointed recessed resource bar slots on the 3 TOP edges (with dark obsidian interior and thin glowing cyan filigree trim), gothic acanthus scrollwork on the 3 bottom edges, and a completely EMPTY PURE BLACK (#000000) inner hexagon window.
2. Top-Right [1,2] (center 768,256) — MONSTER / ENEMY HEX FRAME (FLAT-TOP hexagon):
   - Same inner pure black (#000000) portrait window and the exact same 3 elongated pointed recessed resource bar slots on the 3 TOP edges, but forged in darker battle-worn bronze with 6 twin-barbed angular claw brackets protruding from the 6 corners (as shown in Image 1 and Image 2) and sharper aggressive gothic relief on the 3 bottom edges.
3. Bottom-Left [2,1] (center 256,768) — BOSS / ELITE HEX FRAME (FLAT-TOP hexagon):
   - Same inner pure black (#000000) portrait window and the exact same 3 elongated pointed recessed resource bar slots on the 3 TOP edges, but forged in opulent royal antique gold and dark bronze with 6 large sharp beveled golden spikes protruding from the 6 corners (as shown in Image 1 and Image 2).
4. Bottom-Right [2,2] (center 768,768) — EMPTY BATTLEFIELD HEX TILE (FLAT-TOP hexagon):
   - Thin beveled dark bronze and antique gold outer rim surrounding a solid, clean, matte dark obsidian-slate stone floor (no hole inside).
"""


def build_clean_masks():
    """Return 4x supersampled anti-aliased silhouette mask and the 3-slot cutout mask."""
    size = 1024
    ss = 4
    big = size * ss

    r_outer = 211.0
    r_slot_mid = 179.0
    r_window = 147.0
    r_monster_barb = 222.5
    r_boss_tip = 237.5

    centers = {
        (0, 0): (256.0, 256.0),  # [1,1] Player
        (1, 0): (768.0, 256.0),  # [1,2] Monster
        (0, 1): (256.0, 768.0),  # [2,1] Boss
        (1, 1): (768.0, 768.0),  # [2,2] Empty Tile
    }

    mask_big = Image.new("L", (big, big), 0)
    d_big = ImageDraw.Draw(mask_big)

    slots_big = Image.new("L", (big, big), 0)
    d_slots = ImageDraw.Draw(slots_big)

    for kind, cell_key in [("player", (0, 0)), ("monster", (1, 0)), ("boss", (0, 1))]:
        cx, cy = centers[cell_key]
        d_big.polygon(flat_hex_pts(cx * ss, cy * ss, r_outer * ss), fill=255)
        if kind == "monster":
            draw_monster_corner_claws(d_big, cx * ss, cy * ss, r_outer * ss, r_monster_barb * ss, edge_dist=26.0 * ss, fill_color=255)
        elif kind == "boss":
            draw_boss_corner_spikes(d_big, cx * ss, cy * ss, r_outer * ss, r_boss_tip * ss, base_dist=30.0 * ss, fill_color=255)
        d_big.polygon(flat_hex_pts(cx * ss, cy * ss, r_window * ss), fill=0)

        # 3 top resource bar slots (Side 3 = Top-Left, Side 4 = Top-Flat, Side 5 = Top-Right)
        for s_idx in (3, 4, 5):
            hole = make_chamfered_bar_slot(cx * ss, cy * ss, s_idx, r_slot_mid * ss, half_thickness=8.0 * ss, end_pad=24.5 * ss, tip_len=10.5 * ss)
            d_slots.polygon(hole, fill=255)

    # [2,2] Solid Empty Hex Tile
    cx, cy = centers[(1, 1)]
    d_big.polygon(flat_hex_pts(cx * ss, cy * ss, r_outer * ss), fill=255)

    alpha_mask = mask_big.resize((size, size), Image.Resampling.LANCZOS)
    slots_mask = slots_big.resize((size, size), Image.Resampling.LANCZOS)
    return alpha_mask, slots_mask


def make_partial_slot_fill(cx: float, cy: float, side_idx: int, r_mid: float, half_thickness: float, end_pad: float, tip_len: float, fill_ratio: float):
    """Build a polygon clipped to `fill_ratio` (0.0..1.0) along the axis of `side_idx`."""
    pts = flat_hex_pts(cx, cy, r_mid)
    p1 = pts[side_idx]
    p2 = pts[(side_idx + 1) % 6]
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    nx, ny = ty, -tx

    total_len = length - 2.0 * end_pad
    cur_len = max(tip_len * 1.2, total_len * fill_ratio)

    tip_start = (p1[0] + tx * end_pad, p1[1] + ty * end_pad)
    tip_end = (p1[0] + tx * (end_pad + cur_len), p1[1] + ty * (end_pad + cur_len))

    t_in = min(tip_len, cur_len * 0.45)
    s1_x, s1_y = p1[0] + tx * (end_pad + t_in), p1[1] + ty * (end_pad + t_in)
    s2_x, s2_y = p1[0] + tx * (end_pad + cur_len - t_in * 0.5), p1[1] + ty * (end_pad + cur_len - t_in * 0.5)

    return [
        tip_start,
        (s1_x + nx * half_thickness, s1_y + ny * half_thickness),
        (s2_x + nx * half_thickness, s2_y + ny * half_thickness),
        tip_end,
        (s2_x - nx * half_thickness, s2_y - ny * half_thickness),
        (s1_x - nx * half_thickness, s1_y - ny * half_thickness),
    ]


def postprocess_hex_sheet(raw_img: Image.Image, brain_dir: Path):
    alpha_mask, slots_mask = build_clean_masks()

    raw_px = raw_img.load()
    mask_px = alpha_mask.load()
    slot_px = slots_mask.load()

    rgba_sheet = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    rpx = rgba_sheet.load()

    for y in range(1024):
        for x in range(1024):
            a = mask_px[x, y]
            if a == 0:
                continue
            r, g, b = raw_px[x, y]
            lum = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if a < 245 and lum > 175 and sat < 35:
                continue
            if lum < 10 and a < 200:
                continue
            rpx[x, y] = (r, g, b, a)

    rgba_path = brain_dir / "hex_3frames_1tile_rgba_1024.png"
    rgba_sheet.save(str(rgba_path))

    # 2. Cut out the 3 elongated pointed resource bar slots into the alpha channel!
    cutout_sheet = rgba_sheet.copy()
    cpx = cutout_sheet.load()

    for y in range(1024):
        for x in range(1024):
            sv = slot_px[x, y]
            if sv > 0:
                r, g, b, a = cpx[x, y]
                # Punch smooth transparency into the interior of the 3 bar slots (leaving ~8% smoked glass tint)
                new_a = max(0, int(a * (1.0 - (sv / 255.0) * 0.94)))
                cpx[x, y] = (14, 18, 24, new_a)

    cutout_path = brain_dir / "hex_3frames_1tile_slot_cutout_rgba_1024.png"
    cutout_sheet.save(str(cutout_path))

    # 3. Render a visual demo of all 3 frames (Player, Monster, Boss) with HP, Stamina, and Mana bars filled inside the 3 top slots!
    demo_w, demo_h = 1560, 560
    demo_img = Image.new("RGB", (demo_w, demo_h), (14, 18, 24))

    crops = [
        (0, 0, 260, 0.85, 0.70, 0.60),     # Player Frame
        (512, 0, 780, 0.65, 0.50, 0.35),   # Monster Frame
        (0, 512, 1300, 0.92, 0.80, 0.75),  # Boss Frame
    ]

    for cx_off, cy_off, paste_cx, hp_val, sta_val, mp_val in crops:
        frame_crop = cutout_sheet.crop((cx_off, cy_off, cx_off + 512, cy_off + 512))
        under = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        ud = ImageDraw.Draw(under)

        # Dark empty trough background for all 3 slots
        for s_idx in (3, 4, 5):
            bg_hole = make_chamfered_bar_slot(256.0, 256.0, s_idx, 179.0, half_thickness=9.0, end_pad=23.5, tip_len=10.5)
            ud.polygon(bg_hole, fill=(16, 20, 28, 255))

        # Side 3 (Top-Left): HP (Ruby Crimson)
        hp_outer = make_partial_slot_fill(256.0, 256.0, 3, 179.0, 8.2, 24.5, 10.5, hp_val)
        hp_core = make_partial_slot_fill(256.0, 256.0, 3, 179.0, 4.0, 26.5, 8.5, hp_val)
        ud.polygon(hp_outer, fill=(225, 35, 55, 255))
        ud.polygon(hp_core, fill=(255, 130, 140, 255))

        # Side 4 (Top-Flat): Stamina (Emerald / Gold)
        sta_outer = make_partial_slot_fill(256.0, 256.0, 4, 179.0, 8.2, 24.5, 10.5, sta_val)
        sta_core = make_partial_slot_fill(256.0, 256.0, 4, 179.0, 4.0, 26.5, 8.5, sta_val)
        ud.polygon(sta_outer, fill=(40, 200, 95, 255))
        ud.polygon(sta_core, fill=(150, 255, 180, 255))

        # Side 5 (Top-Right): Mana (Arcane Sapphire Blue)
        mp_outer = make_partial_slot_fill(256.0, 256.0, 5, 179.0, 8.2, 24.5, 10.5, mp_val)
        mp_core = make_partial_slot_fill(256.0, 256.0, 5, 179.0, 4.0, 26.5, 8.5, mp_val)
        ud.polygon(mp_outer, fill=(30, 135, 255, 255))
        ud.polygon(mp_core, fill=(140, 215, 255, 255))

        under = under.filter(ImageFilter.GaussianBlur(radius=1.2))
        comp = Image.alpha_composite(under, frame_crop).resize((460, 460), Image.Resampling.LANCZOS)
        demo_img.paste(comp, (paste_cx - 230, 280 - 230), comp)

    demo_path = brain_dir / "hex_3frames_1tile_bars_demo.png"
    demo_img.save(str(demo_path))
    print("SUCCESS! Saved hex_3frames_1tile_rgba_1024.png, slot cutout, and 3-frame HP/STA/MP demo.")


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "hex_3frames_1tile_raw_1024.png"

    if raw_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing raw API image: {raw_path}")
        raw_img = Image.open(raw_path).convert("RGB")
        postprocess_hex_sheet(raw_img, brain_dir)
        return

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    line_img = Image.open(brain_dir / "hex_sheet_2x2_lineart_1024.png").convert("RGB")
    mask_img = Image.open(brain_dir / "hex_sheet_2x2_solid_mask_1024.png").convert("RGB")
    style_img_1 = Image.open(brain_dir / "style_1b_gothic_filigree_flathex_1792942867061.jpg").convert("RGB")
    style_img_2 = Image.open(brain_dir / "hex_sheet_2x2_raw_1024.png").convert("RGB")

    # Tint the white lineart to warm bronze/gold so the AI never leaves white lineart pixels on borders
    tinted_line = Image.new("RGB", line_img.size, (0, 0, 0))
    lpx = line_img.load()
    tpx = tinted_line.load()
    for y in range(1024):
        for x in range(1024):
            v = lpx[x, y][0]
            if v > 0:
                tpx[x, y] = (int(v * 0.72), int(v * 0.58), int(v * 0.36))

    client = genai.Client(api_key=api_key)
    print("Sending 3-Frames + 1-Tile Flat-Top Hex Sheet (1024x1024) request to gemini-3-pro-image-preview...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[PROMPT, tinted_line, mask_img, style_img_1, style_img_2],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    out_img = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            out_img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
            break

    if out_img is None:
        print("ERROR: No image returned from API.")
        sys.exit(1)

    if out_img.size != (1024, 1024):
        out_img = out_img.resize((1024, 1024), Image.Resampling.LANCZOS)

    out_img.save(str(raw_path))
    postprocess_hex_sheet(out_img, brain_dir)


if __name__ == "__main__":
    main()
