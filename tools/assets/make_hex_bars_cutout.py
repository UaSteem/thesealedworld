"""Build 3-edge HP / Mana / Stamina trough cutout version of the 2x2 Flat-Top Hex Frames and render a live fill demo (NO API CALL)."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

from make_hex_sheet_2x2_mask import flat_hex_pts


def make_edge_wedge_polygon(cx: float, cy: float, side_idx: int, r_in: float, r_out: float, pad_px: float = 8.0) -> list[tuple[float, float]]:
    """Return a 4-point trapezoid for the recessed channel along hex side `side_idx` (0..5), inset from corners by `pad_px`."""
    pts_in = flat_hex_pts(cx, cy, r_in)
    pts_out = flat_hex_pts(cx, cy, r_out)

    p1_in, p2_in = pts_in[side_idx], pts_in[(side_idx + 1) % 6]
    p1_out, p2_out = pts_out[side_idx], pts_out[(side_idx + 1) % 6]

    def inset_seg(a, b, pad):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        return (a[0] + ux * pad, a[1] + uy * pad), (b[0] - ux * pad, b[1] - uy * pad)

    q1_in, q2_in = inset_seg(p1_in, p2_in, pad_px)
    q1_out, q2_out = inset_seg(p1_out, p2_out, pad_px)
    return [q1_in, q2_in, q2_out, q1_out]


def make_partial_edge_bar(cx: float, cy: float, side_idx: int, r_in: float, r_out: float, pad_px: float, fill_ratio: float) -> list[tuple[float, float]]:
    """Return a 4-point trapezoid filled to `fill_ratio` (0.0 .. 1.0) along hex side `side_idx`."""
    q1_in, q2_in, q2_out, q1_out = make_edge_wedge_polygon(cx, cy, side_idx, r_in, r_out, pad_px)
    # For bottom sides (side 0: BR, side 1: Bottom-Flat, side 2: BL), let's fill from left-to-right or bottom-up consistently
    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    m_in = lerp(q2_in, q1_in, fill_ratio)
    m_out = lerp(q2_out, q1_out, fill_ratio)
    return [q2_in, m_in, m_out, q2_out]


def build_hp_mana_stamina_cutout():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    cutout_sheet = Image.open(brain_dir / "hex_sheet_2x2_rune_cutout_rgba_1024.png").convert("RGBA")

    # In flat_hex_pts(cx, cy, r):
    # Vertex 0 = (0 deg, Right), Vertex 1 = (60 deg, Bottom-Right), Vertex 2 = (120 deg, Bottom-Left),
    # Vertex 3 = (180 deg, Left), Vertex 4 = (240 deg, Top-Left), Vertex 5 = (300 deg, Top-Right).
    # Therefore the 6 sides are:
    # Side 0 (0 -> 60 deg): Bottom-Right diagonal edge
    # Side 1 (60 -> 120 deg): Bottom-Flat horizontal edge
    # Side 2 (120 -> 180 deg): Bottom-Left diagonal edge
    # Side 3 (180 -> 240 deg): Top-Left diagonal edge
    # Side 4 (240 -> 300 deg): Top-Flat horizontal edge
    # Side 5 (300 -> 0 deg): Top-Right diagonal edge

    # Let's carve clean recessed gauge slots (alpha = 35 with dark obsidian glass tint & 3 tick marks)
    # on the 3 BOTTOM sides (Side 2 = Bottom-Left [HP], Side 1 = Bottom-Flat [Stamina], Side 0 = Bottom-Right [Mana])
    # while keeping the 3 TOP sides (Sides 3, 4, 5) with their glowing runes!
    r_slot_in = 161.5
    r_slot_out = 178.5

    slot_mask = Image.new("L", (1024, 1024), 0)
    d_slot = ImageDraw.Draw(slot_mask)

    bevel_rim = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    d_rim = ImageDraw.Draw(bevel_rim)

    for cx, cy in [(256.0, 256.0), (768.0, 256.0)]:
        for side_idx in (0, 1, 2):  # Bottom-Right, Bottom-Flat, Bottom-Left
            poly = make_edge_wedge_polygon(cx, cy, side_idx, r_slot_in, r_slot_out, pad_px=7.0)
            d_slot.polygon(poly, fill=230)  # Deep alpha cutout for the resource bar trough
            # Thin antique bronze/gold frame around the resource slot + 3 quarter tick dividers (25%, 50%, 75%)
            d_rim.polygon(poly, outline=(155, 125, 72, 240), width=2)
            q1_in, q2_in, q2_out, q1_out = poly
            for tick in (0.25, 0.5, 0.75):
                tx_in = q1_in[0] + (q2_in[0] - q1_in[0]) * tick
                ty_in = q1_in[1] + (q2_in[1] - q1_in[1]) * tick
                tx_out = q1_out[0] + (q2_out[0] - q1_out[0]) * tick
                ty_out = q1_out[1] + (q2_out[1] - q1_out[1]) * tick
                d_rim.line([(tx_in, ty_in), (tx_out, ty_out)], fill=(95, 78, 48, 210), width=2)

    slot_mask = slot_mask.filter(ImageFilter.GaussianBlur(radius=0.7))
    s_px = slot_mask.load()
    c_px = cutout_sheet.load()

    for y in range(512):
        for x in range(1024):
            sv = s_px[x, y]
            if sv > 0:
                r, g, b, a = c_px[x, y]
                # Dark smoked glass transparency inside the 3 resource bar troughs
                new_a = max(18, int(a * (1.0 - sv / 255.0 * 0.88)))
                c_px[x, y] = (18, 22, 28, new_a)

    # Composite the antique gold slot borders & tick marks on top
    bars_sheet = Image.alpha_composite(cutout_sheet, bevel_rim)
    bars_sheet_path = brain_dir / "hex_sheet_2x2_bars_and_runes_rgba_1024.png"
    bars_sheet.save(str(bars_sheet_path))

    # Build a demonstration showing Standard Frame and Elite/Boss Frame with:
    # - Top 3 sides: glowing runes (Cyan / Gold / Crimson)
    # - Bottom-Left side (Side 2): HP Bar (Crimson Red, e.g. 80% full)
    # - Bottom-Flat side (Side 1): Stamina Bar (Emerald/Amber, e.g. 65% full)
    # - Bottom-Right side (Side 0): Mana Bar (Sapphire Blue, e.g. 50% full)
    demo = Image.new("RGB", (1120, 560), (14, 18, 24))

    for idx, (crop_x, paste_x, rune_col, hp_r, sta_r, mp_r) in enumerate([
        (0, 60, (0, 235, 255), 0.82, 0.65, 0.50),
        (512, 580, (255, 185, 30), 0.90, 0.75, 0.40),
    ]):
        frame_crop = bars_sheet.crop((crop_x, 0, crop_x + 512, 512))
        under = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        ud = ImageDraw.Draw(under)

        # 1. Dark backing for all 3 resource troughs (empty portion of bars)
        for side_idx in (0, 1, 2):
            poly_bg = make_edge_wedge_polygon(256, 256, side_idx, r_slot_in - 1, r_slot_out + 1, pad_px=6.5)
            ud.polygon(poly_bg, fill=(16, 20, 26, 255))

        # 2. Filled resource bars on the 3 bottom edges:
        # Side 2 (Bottom-Left): HP (Ruby Red)
        hp_poly = make_partial_edge_bar(256, 256, 2, r_slot_in, r_slot_out, pad_px=7.0, fill_ratio=hp_r)
        ud.polygon(hp_poly, fill=(235, 40, 55, 255))
        hp_core = make_partial_edge_bar(256, 256, 2, r_slot_in + 4, r_slot_out - 4, pad_px=7.0, fill_ratio=hp_r)
        ud.polygon(hp_core, fill=(255, 120, 130, 255))

        # Side 1 (Bottom-Flat): Stamina (Emerald Green / Gold)
        sta_poly = make_partial_edge_bar(256, 256, 1, r_slot_in, r_slot_out, pad_px=7.0, fill_ratio=sta_r)
        ud.polygon(sta_poly, fill=(45, 205, 95, 255))
        sta_core = make_partial_edge_bar(256, 256, 1, r_slot_in + 4, r_slot_out - 4, pad_px=7.0, fill_ratio=sta_r)
        ud.polygon(sta_core, fill=(140, 255, 175, 255))

        # Side 0 (Bottom-Right): Mana (Sapphire / Arcane Blue)
        mp_poly = make_partial_edge_bar(256, 256, 0, r_slot_in, r_slot_out, pad_px=7.0, fill_ratio=mp_r)
        ud.polygon(mp_poly, fill=(35, 135, 255, 255))
        mp_core = make_partial_edge_bar(256, 256, 0, r_slot_in + 4, r_slot_out - 4, pad_px=7.0, fill_ratio=mp_r)
        ud.polygon(mp_core, fill=(135, 210, 255, 255))

        # 3. Top 3 sides (Sides 3, 4, 5): Underglow for the runes
        for side_idx in (3, 4, 5):
            r_poly = make_edge_wedge_polygon(256, 256, side_idx, 158, 182, pad_px=2.0)
            ud.polygon(r_poly, fill=(*rune_col, 255))

        under_blur = under.filter(ImageFilter.GaussianBlur(radius=2.2))
        comp = Image.alpha_composite(under_blur, frame_crop).resize((480, 480), Image.Resampling.LANCZOS)
        demo.paste(comp, (paste_x, 40), comp)

    demo_path = brain_dir / "hex_frames_hp_mp_sta_demo.png"
    demo.save(str(demo_path))
    print("Saved 3-edge HP/Mana/Stamina hex frame cutout and demo.")


if __name__ == "__main__":
    build_hp_mana_stamina_cutout()
