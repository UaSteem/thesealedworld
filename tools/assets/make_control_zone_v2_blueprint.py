"""Build the V2 thin-line 2048x2048 (2K) 2x2 Blueprint & Binary Mask for the Player Control Zone:
- [1,1] Fused Corner Frame WITHOUT the solid backing plate ("убрать плотную часть, но чтобы балка токенов и четверть-круг были слитны через угол"):
        Top Horizontal Token Bar seamlessly fused at its right end into the top of the Corner Quarter-Circle (3 sector buttons + Dragon corner hub),
        with a graceful concave corner bracket where the horizontal bar meets the arc, and PURE EMPTY SPACE under the left arm of the Token Bar!
- [1,2] Standalone Rectangular Sliding Backing Plate with THIN, sleek double-beveled gold/bronze rim (matching the Empty Hex Tile rim in media_1792956936340_12dcdbb8.png, NO bulky corner shields).
- [2,1] Two Longitudinal Row Button Frames (Feint Row + Basic Attack Row) with THIN, crisp gold/bronze bevels so text has maximum room.
- [2,2] Square Skill/Item Slot Frame with THIN gold/bronze bevel (~7% border width) and 4 small crisp cyan corner gems (matching the Player Hex Frame in media_1792956936340_12dcdbb8.png), leaving ~86% open interior for the skill icon when scaled down 5-6x!
(NO API CALL).
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def chamfer_rect(x1: float, y1: float, x2: float, y2: float, c: float) -> list[tuple[float, float]]:
    return [
        (x1 + c, y1),
        (x2 - c, y1),
        (x2, y1 + c),
        (x2, y2 - c),
        (x2 - c, y2),
        (x1 + c, y2),
        (x1, y2 - c),
        (x1, y1 + c),
    ]


def arc_polygon(cx: float, cy: float, r_in: float, r_out: float, deg_start: float, deg_end: float, steps: int = 48) -> list[tuple[float, float]]:
    pts = []
    for i in range(steps + 1):
        a = math.radians(deg_start + (deg_end - deg_start) * i / steps)
        pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
    for i in range(steps, -1, -1):
        a = math.radians(deg_start + (deg_end - deg_start) * i / steps)
        pts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
    return pts


def draw_rotated_text(base_img: Image.Image, cx: float, cy: float, text: str, angle_deg: float, font: ImageFont.FreeTypeFont, fill: tuple[int, int, int]):
    """Draw text centered at (cx, cy) rotated by angle_deg (positive = counter-clockwise)."""
    tmp = Image.new("RGBA", (320, 100), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tmp)
    bbox = dt.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    dt.text((160 - tw // 2 - bbox[0], 50 - th // 2 - bbox[1]), text, font=font, fill=(*fill, 255))
    rot = tmp.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=True)
    rw, rh = rot.size
    base_img.paste(rot, (int(round(cx - rw / 2)), int(round(cy - rh / 2))), rot)


def build_v2_blueprint():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    sz = 2048

    mask_img = Image.new("L", (sz, sz), 0)
    dm = ImageDraw.Draw(mask_img)

    line_img = Image.new("RGB", (sz, sz), (0, 0, 0))
    dl = ImageDraw.Draw(line_img)

    # =========================================================================
    # CELL [1,1] (0..1024, 0..1024):
    # LOW & WIDE Fused Top Token Bar (with HORIZONTAL RECTANGULAR token slots [icon | number]!)
    # + Compact Right-Bottom Quarter-Circle with smaller, narrower sector buttons!
    # Width = 920 px (x=52..972), Total Height = 350 px (y=330..680) -> wide 2.63:1 ratio!
    # =========================================================================
    u_x1, u_x2 = 52, 972
    tb_y1, tb_y2 = 330, 394          # Sleek LOW horizontal Token Bar (920px wide x 64px tall!)
    r_q_out = 286.0                  # Compact Quarter-Circle radius (286px instead of 700px!) -> fits cleanly in bottom-right!
    r_q_hub = 132.0                  # Compact Corner Hub radius -> sector buttons are 126px deep (neat arc tabs, NOT giant pie wedges!)
    q_cx = float(u_x2)               # Right edge aligns 100% with Token Bar right edge (x=972)
    q_cy = float(tb_y2 + int(r_q_out))  # y=680 -> top of Quarter-Circle (270 deg) meets bottom of Token Bar (y=394) cleanly with ZERO sharp spike!

    # Small vertical/rounded transition only in the last 36px at the right edge (NO sharp left beak!)
    fillet_pts = [(u_x2 - 42, tb_y2 - 3), (u_x2, tb_y2 - 3), (u_x2, tb_y2 + 36), (u_x2 - 32, tb_y2 + 6)]
    dm.polygon(fillet_pts, fill=255)

    # 1A. Compact Quarter-Circle (center at q_cx=972, q_cy=680, radius r_q_out=286)
    q_outer = arc_polygon(q_cx, q_cy, 0, r_q_out, 180.0, 270.0, steps=64)
    dm.polygon(q_outer, fill=255)
    dl.polygon(q_outer, fill=(0, 0, 0), outline=(255, 255, 255), width=4)

    # Thin outer double-bevel rim of the Quarter-Circle
    dl.polygon(arc_polygon(q_cx, q_cy, r_q_out - 10, r_q_out, 180.0, 270.0, steps=64), outline=(255, 255, 255), width=2)
    dl.polygon(arc_polygon(q_cx, q_cy, r_q_hub, r_q_hub + 9, 180.0, 270.0, steps=48), outline=(255, 255, 255), width=3)

    # 3 compact, smaller Sector Buttons along the arc (r = 148..268 -> only 120px radial width!)
    try:
        font_sector = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 21)
    except Exception:
        font_sector = ImageFont.load_default()

    sector_defs = [
        (182.5, 207.5, "ATTACK", -15.0),
        (211.5, 236.5, "ITEM", -45.0),
        (240.5, 265.5, "ABILITY", -75.0),
    ]
    for d1, d2, s_lbl, rot_deg in sector_defs:
        dl.polygon(arc_polygon(q_cx, q_cy, r_q_hub + 16, r_q_out - 18, d1, d2, steps=32), outline=(255, 255, 255), width=3)
        dl.polygon(arc_polygon(q_cx, q_cy, r_q_hub + 22, r_q_out - 24, d1 + 1.0, d2 - 1.0, steps=32), outline=(255, 255, 255), width=2)
        mid_a = math.radians(0.5 * (d1 + d2))
        mid_r = 0.5 * (r_q_hub + 16 + r_q_out - 18)
        scx = q_cx + mid_r * math.cos(mid_a)
        scy = q_cy + mid_r * math.sin(mid_a)
        # Diagonal inscription along the sector
        draw_rotated_text(line_img, scx, scy, s_lbl, rot_deg, font_sector, (255, 255, 255))

    # Compact Corner Hub in bottom-right vertex
    dl.polygon(arc_polygon(q_cx, q_cy, 0, r_q_hub, 180.0, 270.0, steps=40), outline=(255, 255, 255), width=4)
    dl.polygon(arc_polygon(q_cx, q_cy, 0, r_q_hub - 10, 180.0, 270.0, steps=36), outline=(255, 255, 255), width=2)

    # 1B. Top Horizontal Token Bar drawn cleanly across the top (x=52..972, y=330..394, height=64px)
    tb_outer = chamfer_rect(u_x1, tb_y1, u_x2, tb_y2, 10)
    dm.polygon(tb_outer, fill=255)
    dl.polygon(tb_outer, fill=(0, 0, 0), outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(u_x1 + 6, tb_y1 + 6, u_x2 - 6, tb_y2 - 6, 7), outline=(255, 255, 255), width=2)

    # 9 HORIZONTAL RECTANGULAR token slots inside the Token Bar (so [icon | count] sit side-by-side in a row!)
    tok_w = 88
    tok_h = 40
    tok_gap = 10
    tok_start_x = u_x1 + 24
    tok_y1 = tb_y1 + (tb_y2 - tb_y1 - tok_h) // 2
    tok_y2 = tok_y1 + tok_h
    for ti in range(9):
        tx1 = tok_start_x + ti * (tok_w + tok_gap)
        tx2 = tx1 + tok_w
        dl.polygon(chamfer_rect(tx1, tok_y1, tx2, tok_y2, 6), outline=(255, 255, 255), width=2)

    # =========================================================================
    # CELL [1,2] (1024..2048, 0..1024):
    # LOW & WIDE Standalone Rectangular Sliding Backing Plate!
    # Width = 920 px (1076..1996), Height = 286 px (394..680) -> exact 286px height matching Quarter-Circle, 3.2:1 wide ratio!
    # =========================================================================
    p_x1, p_y1, p_x2, p_y2 = 1076, 394, 1996, 680
    p_outer = chamfer_rect(p_x1, p_y1, p_x2, p_y2, 12)
    dm.polygon(p_outer, fill=255)
    dl.polygon(p_outer, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(p_x1 + 8, p_y1 + 8, p_x2 - 8, p_y2 - 8, 9), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(p_x1 + 16, p_y1 + 16, p_x2 - 16, p_y2 - 16, 6), outline=(255, 255, 255), width=3)

    # =========================================================================
    # CELL [2,1] (0..1024, 1024..2048):
    # Two Sleek Longitudinal Row Button Frames (840 px wide x 104 / 114 px tall — low & wide!)
    # =========================================================================
    f_x1, f_y1, f_x2, f_y2 = 92, 1290, 932, 1396
    f_outer = chamfer_rect(f_x1, f_y1, f_x2, f_y2, 14)
    dm.polygon(f_outer, fill=255)
    dl.polygon(f_outer, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(f_x1 + 8, f_y1 + 8, f_x2 - 8, f_y2 - 8, 9), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(f_x1 + 15, f_y1 + 15, f_x2 - 15, f_y2 - 15, 6), outline=(255, 255, 255), width=2)

    a_x1, a_y1, a_x2, a_y2 = 92, 1580, 932, 1696
    a_outer = chamfer_rect(a_x1, a_y1, a_x2, a_y2, 16)
    dm.polygon(a_outer, fill=255)
    dl.polygon(a_outer, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(a_x1 + 8, a_y1 + 8, a_x2 - 8, a_y2 - 8, 11), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(a_x1 + 16, a_y1 + 16, a_x2 - 16, a_y2 - 16, 7), outline=(255, 255, 255), width=3)

    # =========================================================================
    # CELL [2,2] (1024..2048, 1024..2048):
    # Universal Square Skill/Item Slot Frame — THIN clean gold/bronze double-bevel rim (NO corner crystals!)
    # matching the Empty Battlefield Hex Tile rim! ~90% open interior for skill/item icons!
    # =========================================================================
    sq_x1, sq_y1, sq_x2, sq_y2 = 1216, 1216, 1856, 1856
    sq_outer = chamfer_rect(sq_x1, sq_y1, sq_x2, sq_y2, 14)
    dm.polygon(sq_outer, fill=255)
    dl.polygon(sq_outer, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(sq_x1 + 12, sq_y1 + 12, sq_x2 - 12, sq_y2 - 12, 10), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(sq_x1 + 26, sq_y1 + 26, sq_x2 - 26, sq_y2 - 26, 6), outline=(255, 255, 255), width=3)

    # Save mask, lineart, and annotated preview
    prev_img = Image.new("RGB", (sz, sz), (14, 18, 24))
    prev_img = Image.composite(Image.new("RGB", (sz, sz), (32, 42, 56)), prev_img, mask_img)
    prev_img = Image.composite(Image.new("RGB", (sz, sz), (95, 225, 255)), prev_img, line_img.convert("L"))
    dp = ImageDraw.Draw(prev_img)
    for g in [0, 1024, 2047]:
        dp.line([(g, 0), (g, sz)], fill=(65, 85, 110), width=3)
        dp.line([(0, g), (sz, g)], fill=(65, 85, 110), width=3)

    try:
        font_h = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 21)
    except Exception:
        font_h = ImageFont.load_default()

    labels = [
        (24, 24, "[1,1] НИЗКАЯ ШИРОКАЯ БАЛКА ТОКЕНОВ (прямоугольники в ряд) + КОМПАКТНЫЙ ЧЕТВЕРТЬ-КРУГ"),
        (1048, 24, "[1,2] ШИРОКАЯ И УЗКАЯ ВЫДВИЖНАЯ ПЛИТА (3.2:1, тонкая фаска как у пустого гекса)"),
        (24, 1048, "[2,1] ПРОДОЛЬНЫЕ ПЛАШКИ (тонкая окантовка: сверху Финт, снизу Обычная атака)"),
        (1048, 1048, "[2,2] КВАДРАТНЫЙ СЛОТ АБИЛОК / ИТЕМОВ (тонкая фаска как у пустого гекса, БЕЗ кристаллов)"),
    ]
    for lx, ly, ltxt in labels:
        dp.text((lx, ly), ltxt, fill=(255, 215, 90), font=font_h)

    mask_img.save(str(brain_dir / "control_zone_v2_mask_2048.png"))
    line_img.save(str(brain_dir / "control_zone_v2_lineart_2048.png"))
    prev_img.save(str(brain_dir / "control_zone_v2_preview_2048.png"))

    # Also build an in-scene comparison on media_1792953112600_8f5a2738.png
    shot_path = brain_dir / ".user_uploaded" / "media_1792953112600_8f5a2738.png"
    if shot_path.exists():
        shot = Image.open(shot_path).convert("RGB")
        sw, sh = shot.size
        cpx = shot.load()
        bg_col = cpx[sw - 20, int(sh * 0.58)]
        for y in range(int(sh * 0.55), sh):
            for x in range(int(sw * 0.40), sw):
                if x < int(sw * 0.565) and y < int(sh * 0.845):
                    r, g, b = cpx[x, y]
                    if r - g > 42 and r > 120:
                        cpx[x, y] = bg_col
                else:
                    r, g, b = cpx[x, y]
                    if r - g > 8 or abs(r - bg_col[0]) > 14:
                        cpx[x, y] = bg_col

        ds = ImageDraw.Draw(shot)
        try:
            f_b = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 11)
            f_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 10)
        except Exception:
            f_b = f_sm = ImageFont.load_default()

        sc = 490.0 / 920.0
        cx2 = sw - 4
        cx1 = cx2 - 490
        cy2 = sh - 4
        rq_s = int(round(286 * sc))      # 152 px compact quarter-circle height!
        rq_hub_s = int(round(132 * sc))  # 70 px compact hub!
        tb_h_s = int(round(64 * sc))     # 34 px sleek low token bar!
        body_y1 = cy2 - rq_s
        tb_y1_s = body_y1 - tb_h_s

        # 1. Wide & Low Sliding Backing Plate (490 x 152 px)
        ds.polygon(chamfer_rect(cx1, body_y1, cx2 - 20, cy2, 7), fill=(20, 24, 32), outline=(195, 160, 82), width=2)
        ds.polygon(chamfer_rect(cx1 + 4, body_y1 + 4, cx2 - 24, cy2 - 4, 5), fill=(16, 20, 27), outline=(125, 100, 50), width=1)

        # Ability slots (2 rows of 5 slots = 10 ABILITY slots easily fit to the left of the compact quarter-circle!)
        for row_i in range(2):
            for col_i in range(5):
                sx = cx1 + 14 + col_i * 58
                sy = body_y1 + 12 + row_i * 54
                ds.rectangle([sx, sy, sx + 48, sy + 48], fill=(24, 30, 40), outline=(185, 150, 75), width=2)
                ds.text((sx + 12, sy + 17), f"Аб.{row_i*5+col_i+1}", fill=(210, 225, 240), font=f_sm)
        ds.text((cx1 + 115, cy2 - 22), "‹   1 / 3   ›", fill=(215, 190, 120), font=f_b)

        # 2. Sleek Low Token Bar with 9 Horizontal Rectangular cells [icon | num]
        ds.polygon(chamfer_rect(cx1, tb_y1_s, cx2, body_y1, 6), fill=(26, 22, 18), outline=(215, 175, 88), width=2)
        tw_s = 47
        th_s = 22
        tgap_s = 6
        for ti in range(9):
            tx1 = cx1 + 10 + ti * (tw_s + tgap_s)
            ty1 = tb_y1_s + (tb_h_s - th_s) // 2
            ds.polygon(chamfer_rect(tx1, ty1, tx1 + tw_s, ty1 + th_s, 4), fill=(18, 22, 30), outline=(175, 140, 68), width=1)
            ds.text((tx1 + 6, ty1 + 5), f"⚔ {ti+1}", fill=(235, 220, 175), font=f_sm)

        # 3. Compact Quarter-Circle with diagonal stylized inscriptions (ATTACK / ITEM / ABILITY)
        ds.polygon(arc_polygon(cx2, cy2, 0, rq_s, 180.0, 270.0, steps=40), fill=(30, 24, 18), outline=(215, 175, 88), width=2)
        for d1, d2, lbl, rdeg in [(182.5, 207.5, "ATTACK", -15.0), (211.5, 236.5, "ITEM", -45.0), (240.5, 265.5, "ABILITY", -75.0)]:
            ds.polygon(arc_polygon(cx2, cy2, rq_hub_s + 8, rq_s - 9, d1, d2, steps=20), fill=(20, 25, 34), outline=(185, 150, 75), width=2)
            ma = math.radians(0.5 * (d1 + d2))
            mr = 0.50 * (rq_hub_s + 8 + rq_s - 9)
            draw_rotated_text(shot, cx2 + mr * math.cos(ma), cy2 + mr * math.sin(ma), lbl, rdeg, f_b, (240, 215, 145))
        ds.polygon(arc_polygon(cx2, cy2, 0, rq_hub_s, 180.0, 270.0, steps=24), fill=(38, 30, 20), outline=(225, 185, 90), width=2)
        ds.text((cx2 - 46, cy2 - 26), "Дракон", fill=(195, 165, 100), font=f_sm)

        shot.save(str(brain_dir / "control_zone_v2_low_wide_in_scene.png"))

    print("Saved V2 thin-line 2048x2048 blueprint and masks.")


if __name__ == "__main__":
    build_v2_blueprint()
