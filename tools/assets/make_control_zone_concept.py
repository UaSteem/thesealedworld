"""Generate:
1. In-scene preview on the user's actual battlefield screenshot (media_1792953112600_8f5a2738.png) matching sketch media_1792953558798_39a1a28c.png:
   - Top Horizontal Token Bar (Т Т Т) running across the top of the entire corner console (glued to the quarter-circle!)
   - Right-bottom Corner Quarter-Circle right below the right side of the Token Bar (decorative corner hub + 3 sector buttons: Атака, Итемы, Абилки)
   - Sliding Rectangular Backing Plate under the left side of the Token Bar, to the left of the Quarter-Circle, holding all 4 longitudinal rows (3 Feints + Basic Attack) completely visible inside the frame!
   - Separate Quick-Access row of Square Slots under the battlefield on the left
2. 2048x2048 (2K) 2x2 Blueprint & Binary Mask for ordering:
   - [1,1] Glued Complete Corner Console (exactly as in sketch: Top Token Bar + Right Quarter-Circle with 3 sectors & hub + Left Backing Plate glued together so it can be used as-is or sliced)
   - [1,2] Standalone Sliding Rectangular Backing Plate (clean obsidian slab in bronze/gold frame for the vertical slide animation)
   - [2,1] Longitudinal Row Button Frame (for Attack & Feints)
   - [2,2] Square Slot Frame (for Abilities / Items / Quick-bar) + Small Circular Token Socket
(NO API CALL - local blueprint and mask generation).
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


def arc_polygon(cx: float, cy: float, r_in: float, r_out: float, deg_start: float, deg_end: float, steps: int = 32) -> list[tuple[float, float]]:
    """Return a closed polygon for an annular sector between r_in and r_out from deg_start to deg_end."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(deg_start + (deg_end - deg_start) * i / steps)
        pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
    for i in range(steps, -1, -1):
        a = math.radians(deg_start + (deg_end - deg_start) * i / steps)
        pts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
    return pts


def build_in_scene_and_2k_masks():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    shot_path = brain_dir / ".user_uploaded" / "media_1792953112600_8f5a2738.png"
    shot = Image.open(shot_path).convert("RGB")
    sw, sh = shot.size

    # Clean red marker from bottom-right of screenshot without touching the hex at x<560, y<700
    clean_shot = shot.copy()
    cpx = clean_shot.load()
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

    try:
        font_h = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
        font_b = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 12)
        font_r = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 10)
    except Exception:
        font_h = font_b = font_r = font_sm = ImageFont.load_default()

    # =========================================================================
    # PART 1: In-Scene Preview matching user's sketch media_1792953558798_39a1a28c.png
    # =========================================================================
    scene_a = clean_shot.copy()
    da = ImageDraw.Draw(scene_a)

    # Fit cleanly inside the empty bottom-right pocket of (sw, sh) without touching any hexes:
    c_x1 = int(sw * 0.525)
    c_x2 = sw - 3
    tb_y1 = int(sh * 0.688)
    tb_y2 = tb_y1 + 36
    body_y1 = tb_y2
    body_y2 = sh - 3
    r_q_out = float(body_y2 - body_y1)  # Quarter-circle height matches backing plate height!
    r_q_hub = round(r_q_out * 0.38)
    q_cx, q_cy = float(c_x2), float(body_y2)

    # 1. Sliding Rectangular Backing Plate under the Token Bar
    da.polygon(chamfer_rect(c_x1, body_y1 - 3, c_x2 - 50, body_y2, 14), fill=(32, 26, 20), outline=(205, 168, 82), width=3)
    da.polygon(chamfer_rect(c_x1 + 6, body_y1 + 4, c_x2 - 56, body_y2 - 6, 10), fill=(18, 22, 29), outline=(130, 102, 48), width=2)

    # 4 Longitudinal Rows inside the Backing Plate (3 Feints + 1 Basic Attack) — ALL 4 fit inside body_y1..body_y2!
    rows_data = [
        ("Финт 1 (улучшение удара)", True),
        ("Финт 2 (улучшение удара)", False),
        ("Финт 3 (улучшение удара)", False),
        ("ОБЫЧНАЯ АТАКА (Удар)", False),
    ]
    inner_h = (body_y2 - 10) - (body_y1 + 10)
    rgap = 6
    rh = (inner_h - 3 * rgap) // 4
    for ri, (r_txt, r_act) in enumerate(rows_data):
        rx1 = c_x1 + 14
        ry1 = body_y1 + 10 + ri * (rh + rgap)
        ry2 = ry1 + rh
        mid_y = 0.5 * (ry1 + ry2)
        dy_q = q_cy - mid_y
        arc_x = q_cx - math.sqrt(max(0.0, (r_q_out + 8.0) ** 2 - dy_q ** 2))
        rx2 = int(arc_x)
        is_atk = (ri == 3)
        fill_c = (46, 33, 20) if is_atk else ((24, 44, 58) if r_act else (24, 29, 37))
        out_c = (255, 210, 85) if is_atk else ((0, 230, 255) if r_act else (175, 140, 68))
        da.polygon(chamfer_rect(rx1, ry1, rx2, ry2, 6), fill=fill_c, outline=out_c, width=2)
        da.text((rx1 + 10, ry1 + (rh - 14) // 2), r_txt, fill=(255, 240, 190) if is_atk else (230, 245, 255), font=font_b if is_atk else font_r)

    # 2. Fixed Top Token Bar (glued across the entire top of the console, x = c_x1 .. c_x2, y = tb_y1 .. tb_y2)
    da.polygon(chamfer_rect(c_x1, tb_y1, c_x2, tb_y2, 10), fill=(38, 30, 22), outline=(220, 180, 88), width=3)
    da.polygon(chamfer_rect(c_x1 + 5, tb_y1 + 5, c_x2 - 5, tb_y2 - 5, 7), fill=(20, 24, 32), outline=(145, 115, 55), width=2)
    da.text((c_x1 + 12, tb_y1 + 13), "ТОКЕНЫ:", fill=(215, 185, 115), font=font_sm)
    tok_start_x = c_x1 + 82
    tok_step = (c_x2 - 22 - tok_start_x) // 8
    for ti in range(9):
        tcx = tok_start_x + ti * tok_step
        tcy = (tb_y1 + tb_y2) // 2
        da.ellipse((tcx - 12, tcy - 12, tcx + 12, tcy + 12), fill=(24, 32, 42), outline=(0, 220, 250) if ti < 3 else (175, 140, 68), width=2)
        da.text((tcx - 6, tcy - 5), f"T{ti+1}", fill=(220, 240, 255), font=font_sm)

    # 3. Fixed Corner Quarter-Circle right under the right half of the Token Bar
    q_bg = arc_polygon(q_cx, q_cy, 0, r_q_out, 180.0, 270.0, steps=40)
    da.polygon(q_bg, fill=(36, 28, 20), outline=(225, 185, 90), width=3)

    sectors_info = [
        (182.0, 208.0, "АТАКА", True),
        (212.0, 238.0, "ИТЕМЫ", False),
        (242.0, 268.0, "АБИЛКИ", False),
    ]
    for d1, d2, s_lbl, s_act in sectors_info:
        spoly = arc_polygon(q_cx, q_cy, r_q_hub + 6, r_q_out - 8, d1, d2, steps=20)
        da.polygon(spoly, fill=(24, 46, 60) if s_act else (22, 27, 35), outline=(0, 230, 255) if s_act else (195, 155, 75), width=2)
        mid_a = math.radians(0.5 * (d1 + d2))
        mid_r = 0.52 * (r_q_hub + r_q_out)
        lx = q_cx + mid_r * math.cos(mid_a) - 22
        ly = q_cy + mid_r * math.sin(mid_a) - 6
        da.text((lx, ly), s_lbl, fill=(255, 245, 200) if s_act else (190, 205, 220), font=font_b)

    # Decorative Corner Hub in the bottom-right vertex
    hub_poly = arc_polygon(q_cx, q_cy, 0, r_q_hub, 180.0, 270.0, steps=24)
    da.polygon(hub_poly, fill=(42, 33, 22), outline=(235, 195, 95), width=3)
    hub_inner = arc_polygon(q_cx, q_cy, 0, r_q_hub - 12, 180.0, 270.0, steps=20)
    da.polygon(hub_inner, fill=(26, 22, 18), outline=(165, 130, 60), width=2)
    da.text((q_cx - 48, q_cy - 28), "Декор", fill=(185, 155, 95), font=font_sm)

    # 4. Separate Quick-Access Skill Bar on the bottom-left
    qb_x = 16
    qb_y = sh - 64
    for qi in range(6):
        sx = qb_x + qi * 62
        da.rectangle([sx, qb_y, sx + 54, qb_y + 54], fill=(22, 27, 36), outline=(210, 170, 82), width=2)
        da.rectangle([sx + 4, qb_y + 4, sx + 50, qb_y + 50], outline=(115, 90, 45), width=1)
        da.text((sx + 6, qb_y + 20), f"Быстр.{qi+1}", fill=(175, 195, 215), font=font_sm)

    scene_a.save(str(brain_dir / "control_zone_corner_in_scene.png"))

    # =========================================================================
    # PART 2: 2048x2048 (2K) 2x2 Sheet Blueprint & Masks for Ordering
    # =========================================================================
    sz = 2048
    mask_2k = Image.new("L", (sz, sz), 0)
    dm = ImageDraw.Draw(mask_2k)

    line_2k = Image.new("RGB", (sz, sz), (0, 0, 0))
    dl = ImageDraw.Draw(line_2k)

    # Cell [1,1] (0..1024, 0..1024): Complete Glued Corner Unit (exactly matching sketch media_1792953558798_39a1a28c.png:
    # Top Token Bar + Right Quarter-Circle with 3 sector buttons & decorative corner hub + Left Backing Plate glued together!)
    # Outer bounds inside [1,1]: x=90..934 (width 844), y=180..890 (height 710) -> generous margin on all 4 sides!
    u_x1, u_x2 = 90, 934
    u_tb_y1, u_tb_y2 = 180, 290
    u_body_y1, u_body_y2 = 290, 890
    rq_full = float(u_body_y2 - u_body_y1)  # 600 px radius
    rq_h = 225.0

    # Left Backing Plate part of the glued unit
    glued_plate = chamfer_rect(u_x1, u_body_y1 - 8, u_x2, u_body_y2, 34)
    dm.polygon(glued_plate, fill=255)
    dl.polygon(glued_plate, outline=(255, 255, 255), width=5)
    dl.polygon(chamfer_rect(u_x1 + 22, u_body_y1 + 14, u_x2 - 22, u_body_y2 - 22, 24), outline=(255, 255, 255), width=3)

    # Top Token Bar part of the glued unit (x=u_x1..u_x2, y=180..290)
    tb_poly = chamfer_rect(u_x1, u_tb_y1, u_x2, u_tb_y2, 26)
    dm.polygon(tb_poly, fill=255)
    dl.polygon(tb_poly, fill=(0, 0, 0), outline=(255, 255, 255), width=5)
    dl.polygon(chamfer_rect(u_x1 + 16, u_tb_y1 + 16, u_x2 - 16, u_tb_y2 - 16, 18), outline=(255, 255, 255), width=3)
    for ti in range(9):
        tcx = u_x1 + 82 + ti * 85
        tcy = (u_tb_y1 + u_tb_y2) // 2
        dl.ellipse((tcx - 24, tcy - 24, tcx + 24, tcy + 24), outline=(255, 255, 255), width=3)

    # Quarter-Circle on the right of the glued unit (center at u_x2, u_body_y2, radius 600)
    q_outer_poly = arc_polygon(u_x2, u_body_y2, 0, rq_full, 180.0, 270.0, steps=64)
    dm.polygon(q_outer_poly, fill=255)
    dl.polygon(q_outer_poly, fill=(0, 0, 0), outline=(255, 255, 255), width=6)
    dl.polygon(arc_polygon(u_x2, u_body_y2, rq_h, rq_full - 18, 180.0, 270.0, steps=64), outline=(255, 255, 255), width=4)
    for d1, d2 in [(182.0, 208.0), (212.0, 238.0), (242.0, 268.0)]:
        dl.polygon(arc_polygon(u_x2, u_body_y2, rq_h + 16, rq_full - 24, d1, d2, steps=32), outline=(255, 255, 255), width=4)
    # Decorative corner hub in bottom-right
    dl.polygon(arc_polygon(u_x2, u_body_y2, 0, rq_h, 180.0, 270.0, steps=36), outline=(255, 255, 255), width=5)
    dl.polygon(arc_polygon(u_x2, u_body_y2, 0, rq_h - 32, 180.0, 270.0, steps=32), outline=(255, 255, 255), width=3)

    # Cell [1,2] (1024..2048, 0..1024): Standalone Rectangular Sliding Backing Plate (with generous margin)
    plate_poly = chamfer_rect(1144, 180, 1928, 860, 42)
    dm.polygon(plate_poly, fill=255)
    dl.polygon(plate_poly, outline=(255, 255, 255), width=6)
    dl.polygon(chamfer_rect(1176, 212, 1896, 828, 30), outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(1196, 232, 1876, 808, 22), outline=(255, 255, 255), width=3)

    # Cell [2,1] (0..1024, 1024..2048): Longitudinal Row Button Frames (Top = Feint Row, Bottom = Attack Row)
    feint_poly = chamfer_rect(130, 1220, 894, 1430, 36)
    dm.polygon(feint_poly, fill=255)
    dl.polygon(feint_poly, outline=(255, 255, 255), width=6)
    dl.polygon(chamfer_rect(154, 1244, 870, 1406, 24), outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(170, 1260, 854, 1390, 18), outline=(255, 255, 255), width=3)

    atk_poly = chamfer_rect(130, 1580, 894, 1810, 42)
    dm.polygon(atk_poly, fill=255)
    dl.polygon(atk_poly, outline=(255, 255, 255), width=6)
    dl.polygon(chamfer_rect(158, 1608, 866, 1782, 28), outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(176, 1626, 848, 1764, 20), outline=(255, 255, 255), width=3)

    # Cell [2,2] (1024..2048, 1024..2048): Square Skill/Item Slot Frame (with 4 corner gems) + Small Circular Token Socket
    sq_x1, sq_y1, sq_x2, sq_y2 = 1260, 1160, 1812, 1712
    dm.rectangle([sq_x1, sq_y1, sq_x2, sq_y2], fill=255)
    dl.rectangle([sq_x1, sq_y1, sq_x2, sq_y2], outline=(255, 255, 255), width=6)
    dl.rectangle([sq_x1 + 34, sq_y1 + 34, sq_x2 - 34, sq_y2 - 34], outline=(255, 255, 255), width=4)
    dl.rectangle([sq_x1 + 56, sq_y1 + 56, sq_x2 - 56, sq_y2 - 56], outline=(255, 255, 255), width=5)
    for gx, gy in [(sq_x1 + 28, sq_y1 + 28), (sq_x2 - 28, sq_y1 + 28), (sq_x1 + 28, sq_y2 - 28), (sq_x2 - 28, sq_y2 - 28)]:
        gem_pts = [(gx, gy - 26), (gx + 26, gy), (gx, gy + 26), (gx - 26, gy)]
        dm.polygon(gem_pts, fill=255)
        dl.polygon(gem_pts, outline=(255, 255, 255), width=4)

    tcx, tcy, tr = 1536, 1870, 90
    dm.ellipse((tcx - tr, tcy - tr, tcx + tr, tcy + tr), fill=255)
    dl.ellipse((tcx - tr, tcy - tr, tcx + tr, tcy + tr), outline=(255, 255, 255), width=5)
    dl.ellipse((tcx - tr + 18, tcy - tr + 18, tcx + tr - 18, tcy + tr - 18), outline=(255, 255, 255), width=3)

    # Annotated Preview of the 2K Sheet
    prev_2k = Image.new("RGB", (sz, sz), (14, 18, 24))
    prev_2k = Image.composite(Image.new("RGB", (sz, sz), (36, 46, 60)), prev_2k, mask_2k)
    prev_2k = Image.composite(Image.new("RGB", (sz, sz), (90, 225, 255)), prev_2k, line_2k.convert("L"))
    dp = ImageDraw.Draw(prev_2k)
    for g in [0, 1024, 2047]:
        dp.line([(g, 0), (g, sz)], fill=(65, 85, 110), width=3)
        dp.line([(0, g), (sz, g)], fill=(65, 85, 110), width=3)

    labels_2k = [
        (28, 24, "[1,1] СКЛЕЕННЫЙ УГЛОВОЙ БЛОК (Балка токенов + Четверть-круг 3 кнопки + Подложка)"),
        (1052, 24, "[1,2] ОТДЕЛЬНАЯ ПРЯМОУГОЛЬНАЯ ПОДЛОЖКА (чистая выдвижная плита)"),
        (28, 1048, "[2,1] ПРОДОЛЬНЫЕ ПЛАШКИ (верхняя — Финт, нижняя — кнопка Атаки)"),
        (1052, 1048, "[2,2] КВАДРАТНЫЙ СЛОТ (Абилки / Итемы / Быстрый доступ) + ТОКЕН"),
    ]
    for lx, ly, ltxt in labels_2k:
        dp.text((lx, ly), ltxt, fill=(255, 215, 90), font=font_h)

    mask_2k.save(str(brain_dir / "control_zone_sheet_2x2_mask_2048.png"))
    line_2k.save(str(brain_dir / "control_zone_sheet_2x2_lineart_2048.png"))
    prev_2k.save(str(brain_dir / "control_zone_sheet_2x2_preview_2048.png"))
    print("Saved updated in-scene preview and 2K 2x2 control zone sheet blueprints.")


if __name__ == "__main__":
    build_in_scene_and_2k_masks()
