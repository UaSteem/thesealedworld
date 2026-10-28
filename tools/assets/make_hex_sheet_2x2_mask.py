"""Generate 2048x2048 (2K: 2x2 cells of 1024x1024 with generous empty space around each hex) Flat-Top Hex Sheet masks and lineart:
[1,1] Player Frame (3 bar slots + 6 diamond corner gems)
[1,2] Monster Frame (3 bar slots + 6 jagged claw/barb corner brackets)
[2,1] Boss Frame (3 bar slots + 6 large royal corner spikes + lower facet crests)
[2,2] Empty Arena Stone Hex Tile
(NO API CALL - local mask/blueprint generation only).
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def flat_hex_pts(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    """Return 6 vertices of a FLAT-TOP hexagon (0, 60, 120, 180, 240, 300 deg)."""
    return [
        (cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i)))
        for i in range(6)
    ]


def draw_hex_outline(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color, width: int = 5):
    pts = flat_hex_pts(cx, cy, r)
    draw.polygon(pts, outline=color, width=width)


def make_chamfered_bar_slot(cx: float, cy: float, side_idx: int, r_mid: float, half_thickness: float, end_pad: float, tip_len: float) -> list[tuple[float, float]]:
    """Return a 6-point elongated pointed-end slot (like in Style 1B) along side `side_idx` of the flat-top hexagon."""
    pts = flat_hex_pts(cx, cy, r_mid)
    p1 = pts[side_idx]
    p2 = pts[(side_idx + 1) % 6]

    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    nx, ny = ty, -tx

    tip_start = (p1[0] + tx * end_pad, p1[1] + ty * end_pad)
    tip_end = (p2[0] - tx * end_pad, p2[1] - ty * end_pad)

    s1_x, s1_y = p1[0] + tx * (end_pad + tip_len), p1[1] + ty * (end_pad + tip_len)
    s2_x, s2_y = p2[0] - tx * (end_pad + tip_len), p2[1] - ty * (end_pad + tip_len)

    return [
        tip_start,
        (s1_x + nx * half_thickness, s1_y + ny * half_thickness),
        (s2_x + nx * half_thickness, s2_y + ny * half_thickness),
        tip_end,
        (s2_x - nx * half_thickness, s2_y - ny * half_thickness),
        (s1_x - nx * half_thickness, s1_y - ny * half_thickness),
    ]


def draw_monster_corner_claws(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_hex: float, r_barb: float, edge_dist: float, fill_color, outline_color=None, width: int = 5):
    """Draw 6 angular iron-bracket / dual-barb corner bumpers for the Monster frame (distinct silhouette between Player and Boss)."""
    pts = flat_hex_pts(cx, cy, r_hex)
    in_pts = flat_hex_pts(cx, cy, r_hex - 22)
    for i in range(6):
        v = pts[i]
        v_prev = pts[(i - 1) % 6]
        v_next = pts[(i + 1) % 6]

        dx1, dy1 = v_prev[0] - v[0], v_prev[1] - v[1]
        l1 = math.hypot(dx1, dy1)
        p_l_base = (v[0] + dx1 / l1 * edge_dist, v[1] + dy1 / l1 * edge_dist)

        dx2, dy2 = v_next[0] - v[0], v_next[1] - v[1]
        l2 = math.hypot(dx2, dy2)
        p_r_base = (v[0] + dx2 / l2 * edge_dist, v[1] + dy2 / l2 * edge_dist)

        a_mid = math.radians(60.0 * i)
        a_b1 = math.radians(60.0 * i - 4.8)
        a_b2 = math.radians(60.0 * i + 4.8)

        p_barb1 = (cx + r_barb * math.cos(a_b1), cy + r_barb * math.sin(a_b1))
        p_notch = (cx + (r_hex + 7.0) * math.cos(a_mid), cy + (r_hex + 7.0) * math.sin(a_mid))
        p_barb2 = (cx + r_barb * math.cos(a_b2), cy + r_barb * math.sin(a_b2))
        p_root = in_pts[i]

        poly = [p_l_base, p_barb1, p_notch, p_barb2, p_r_base, p_root]
        draw.polygon(poly, fill=fill_color, outline=outline_color, width=width)


def draw_boss_corner_spikes(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_hex: float, r_tip: float, base_dist: float, fill_color, outline_color=None, width: int = 5):
    """Draw 6 large royal corner spikes at each vertex for the Boss frame."""
    pts = flat_hex_pts(cx, cy, r_hex)
    in_pts = flat_hex_pts(cx, cy, r_hex - 28)
    for i in range(6):
        v = pts[i]
        v_prev = pts[(i - 1) % 6]
        v_next = pts[(i + 1) % 6]

        dx1, dy1 = v_prev[0] - v[0], v_prev[1] - v[1]
        l1 = math.hypot(dx1, dy1)
        p_l = (v[0] + dx1 / l1 * base_dist, v[1] + dy1 / l1 * base_dist)

        dx2, dy2 = v_next[0] - v[0], v_next[1] - v[1]
        l2 = math.hypot(dx2, dy2)
        p_r = (v[0] + dx2 / l2 * base_dist, v[1] + dy2 / l2 * base_dist)

        a_tip = math.radians(60.0 * i)
        p_tip = (cx + r_tip * math.cos(a_tip), cy + r_tip * math.sin(a_tip))
        p_root = in_pts[i]

        draw.polygon([p_l, p_tip, p_r, p_root], fill=fill_color, outline=outline_color, width=width)
        if outline_color:
            draw.line([p_root, p_tip], fill=outline_color, width=width)


def build_hex_2x2_sheet_2k():
    size = 2048  # True 2K canvas (4 cells of 1024x1024 each)

    # Generous empty space around each hex inside its 1024x1024 cell (half-cell = 512 px):
    # Even the longest Boss spike tip (r_boss_tip = 396 px) stays 116+ px away from the cell border!
    r_outer = 340.0      # Flat-top hex outer radius (plenty of breathing room inside 512px half-cell)
    r_bevel_out = 320.0  # Inner edge of outer antique gold rim
    r_slot_mid = 286.0   # Centerline of the wide bronze facet
    r_bevel_in = 252.0   # Outer edge of inner antique gold rim
    r_window = 234.0     # Transparent portrait window (100% IDENTICAL across Player, Monster, and Boss!)
    r_tile_inner = 304.0 # Inner stone boundary for empty arena tile [2,2]
    r_monster_barb = 364.0  # Monster dual-barb corner extension
    r_boss_tip = 396.0      # Boss royal spike tip radius (116px margin to cell border!)

    BAR_SIDES = (3, 4, 5)  # The 3 TOP facets hold the elongated pointed resource bar slots (HP / Stamina / Mana)

    centers = {
        (0, 0): (512.0, 512.0),    # [1,1] Player / Ally Frame
        (1, 0): (1536.0, 512.0),   # [1,2] Monster / Regular Enemy Frame
        (0, 1): (512.0, 1536.0),   # [2,1] Boss / Elite Frame
        (1, 1): (1536.0, 1536.0),  # [2,2] Empty Stone Hex Tile
    }

    # 1. Solid Binary Mask (2048x2048)
    solid_mask = Image.new("L", (size, size), 0)
    d_mask = ImageDraw.Draw(solid_mask)

    bar_slots_mask = Image.new("L", (size, size), 0)
    d_bars = ImageDraw.Draw(bar_slots_mask)

    frame_specs = [
        ("player", (0, 0)),
        ("monster", (1, 0)),
        ("boss", (0, 1)),
    ]

    for kind, cell_key in frame_specs:
        cx, cy = centers[cell_key]
        d_mask.polygon(flat_hex_pts(cx, cy, r_outer), fill=255)
        if kind == "monster":
            draw_monster_corner_claws(d_mask, cx, cy, r_outer, r_monster_barb, edge_dist=42.0, fill_color=255)
        elif kind == "boss":
            draw_boss_corner_spikes(d_mask, cx, cy, r_outer, r_boss_tip, base_dist=48.0, fill_color=255)

        # Cut out inner portrait window
        d_mask.polygon(flat_hex_pts(cx, cy, r_window), fill=0)

        # Record the 3 resource bar slot cutouts (identical relative coordinates in all 3 frames!)
        for s_idx in BAR_SIDES:
            slot_hole = make_chamfered_bar_slot(cx, cy, s_idx, r_slot_mid, half_thickness=14.0, end_pad=38.0, tip_len=18.0)
            d_bars.polygon(slot_hole, fill=255)

    # [2,2] Empty Arena Hex Tile (solid flat-top hex)
    cx, cy = centers[(1, 1)]
    d_mask.polygon(flat_hex_pts(cx, cy, r_outer), fill=255)

    # 2. Structural Lineart Blueprint (white on black, 2048x2048)
    lineart = Image.new("RGB", (size, size), (0, 0, 0))
    d_line = ImageDraw.Draw(lineart)

    for kind, cell_key in frame_specs:
        cx, cy = centers[cell_key]
        for r, w in [(r_outer, 6), (r_bevel_out, 3), (r_bevel_in, 3), (r_window, 6)]:
            draw_hex_outline(d_line, cx, cy, r, (255, 255, 255), width=w)

        if kind == "monster":
            draw_monster_corner_claws(d_line, cx, cy, r_outer, r_monster_barb, edge_dist=42.0, fill_color=(0, 0, 0), outline_color=(255, 255, 255), width=5)
        elif kind == "boss":
            draw_boss_corner_spikes(d_line, cx, cy, r_outer, r_boss_tip, base_dist=48.0, fill_color=(0, 0, 0), outline_color=(255, 255, 255), width=5)

        # 6 straight corner bevel ribs (0, 60, 120, 180, 240, 300 deg)
        for v_idx in range(6):
            ang = math.radians(60.0 * v_idx)
            p1 = (cx + r_window * math.cos(ang), cy + r_window * math.sin(ang))
            p2 = (cx + r_outer * math.cos(ang), cy + r_outer * math.sin(ang))
            d_line.line([p1, p2], fill=(255, 255, 255), width=5)

        # 3 TOP facets: Elongated chamfered resource bar slots (outer bezel + inner recessed trough)
        for s_idx in BAR_SIDES:
            slot_outer = make_chamfered_bar_slot(cx, cy, s_idx, r_slot_mid, half_thickness=20.0, end_pad=30.0, tip_len=22.0)
            slot_inner = make_chamfered_bar_slot(cx, cy, s_idx, r_slot_mid, half_thickness=14.0, end_pad=38.0, tip_len=18.0)
            d_line.polygon(slot_outer, outline=(255, 255, 255), width=4)
            d_line.polygon(slot_inner, outline=(255, 255, 255), width=4)

    # [2,2] Empty Stone Hex Tile
    cx, cy = centers[(1, 1)]
    for r, w in [(r_outer, 6), (r_tile_inner, 4), (r_tile_inner - 16, 3)]:
        draw_hex_outline(d_line, cx, cy, r, (255, 255, 255), width=w)
    for i in range(6):
        ang = math.radians(60 * i)
        p1 = (cx + r_tile_inner * math.cos(ang), cy + r_tile_inner * math.sin(ang))
        p2 = (cx + r_outer * math.cos(ang), cy + r_outer * math.sin(ang))
        d_line.line([p1, p2], fill=(255, 255, 255), width=5)

    # 3. Visual Annotated Preview (2048x2048)
    preview = Image.new("RGB", (size, size), (14, 18, 24))
    mask_rgb = Image.new("RGB", (size, size), (38, 48, 62))
    preview = Image.composite(mask_rgb, preview, solid_mask)

    d_prev = ImageDraw.Draw(preview)
    slot_colors = {
        3: (185, 45, 65),   # Top-Left: HP slot
        4: (215, 165, 35),  # Top-Flat: Stamina slot
        5: (35, 135, 235),  # Top-Right: Mana slot
    }
    for _, cell_key in frame_specs:
        cx, cy = centers[cell_key]
        for s_idx, scol in slot_colors.items():
            slot_hole = make_chamfered_bar_slot(cx, cy, s_idx, r_slot_mid, half_thickness=14.0, end_pad=38.0, tip_len=18.0)
            d_prev.polygon(slot_hole, fill=scol)

    line_mask = lineart.convert("L")
    cyan_lines = Image.new("RGB", (size, size), (90, 225, 255))
    preview = Image.composite(cyan_lines, preview, line_mask)

    d_prev = ImageDraw.Draw(preview)
    for gx in [0, 1024, 2047]:
        d_prev.line([(gx, 0), (gx, size)], fill=(60, 80, 105), width=3)
    for gy in [0, 1024, 2047]:
        d_prev.line([(0, gy), (size, gy)], fill=(60, 80, 105), width=3)

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    labels = [
        (28, 24, "[1,1] РАМКА ИГРОКА (2K, широкие поля)", "3 капсулы HP / STA / MP + 6 угловых самоцветов"),
        (1052, 24, "[1,2] РАМКА МОНСТРА (2K, широкие поля)", "3 капсулы HP / STA / MP + 6 раздвоенных когтей на углах"),
        (28, 1048, "[2,1] РАМКА БОССА (2K, широкие поля)", "3 капсулы HP / STA / MP + 6 крупных золотых шипов (116px до края)"),
        (1052, 1048, "[2,2] ПУСТАЯ ПЛИТКА ПОЛЯ (2K, широкие поля)", "Тонкая бронзовая оправа + матовый тёмный камень"),
    ]
    for lx, ly, title, sub in labels:
        d_prev.text((lx, ly), title, fill=(255, 215, 90), font=font)
        d_prev.text((lx, ly + 38), sub, fill=(180, 215, 240), font=font_sm)

    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    solid_mask.save(str(brain_dir / "hex_sheet_2x2_solid_mask_2048.png"))
    bar_slots_mask.save(str(brain_dir / "hex_sheet_2x2_bar_slots_mask_2048.png"))
    lineart.save(str(brain_dir / "hex_sheet_2x2_lineart_2048.png"))
    preview.save(str(brain_dir / "hex_sheet_2x2_preview_2048.png"))
    print("Saved 2048x2048 (2K) 3-Frames + 1 Empty Tile 2x2 masks and preview with generous empty margins.")


if __name__ == "__main__":
    build_hex_2x2_sheet_2k()
