"""Create in-scene mockups on media_1792965627888_3d008c70.png and a 2048x2048 blueprint + mask
for the Tall Target / Monster Inspector Panel in the top-left corner of the combat scene.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def chamfer_rect(x1: float, y1: float, x2: float, y2: float, ch: float):
    return [
        (x1 + ch, y1),
        (x2 - ch, y1),
        (x2, y1 + ch),
        (x2, y2 - ch),
        (x2 - ch, y2),
        (x1 + ch, y2),
        (x1, y2 - ch),
        (x1, y1 + ch),
    ]


def draw_inspector_content(d, x1, y1, x2, y2, f_sub, f_title, f_body, f_val):
    """Draw the exact monster/opponent inspector fields inside (x1, y1, x2, y2)."""
    pad = 16
    lx = x1 + pad
    rx = x2 - pad

    # 1. Header
    d.text((lx, y1 + 12), "ВЫБРАННЫЙ ПРОТИВНИК", fill=(195, 165, 100), font=f_sub)
    d.text((lx, y1 + 28), "Налётчик", fill=(242, 232, 210), font=f_title)
    d.text((lx, y1 + 54), "Воин · Сила 32", fill=(155, 168, 185), font=f_sub)

    # Divider 1 (double thin gold line)
    y_div1 = y1 + 76
    d.line([(x1 + 8, y_div1), (x2 - 8, y_div1)], fill=(185, 150, 75), width=2)
    d.line([(x1 + 14, y_div1 + 3), (x2 - 14, y_div1 + 3)], fill=(110, 88, 45), width=1)

    # 2. Resources (Здоровье / Энергия / Стамина) with thin recessed bar tracks
    bars = [
        ("Здоровье", "74 / 100", 0.74, (175, 42, 42)),
        ("Энергия",  "28 / 40",  0.70, (48, 115, 185)),
        ("Стамина",  "35 / 50",  0.70, (195, 145, 45)),
    ]
    cy = y_div1 + 12
    for name, val_txt, ratio, bar_col in bars:
        d.text((lx, cy), name, fill=(210, 218, 228), font=f_body)
        tw = d.textbbox((0, 0), val_txt, font=f_val)[2]
        d.text((rx - tw, cy), val_txt, fill=(235, 215, 160), font=f_val)
        # Thin sleek obsidian bar track with gold rim underneath
        by1 = cy + 16
        by2 = by1 + 6
        d.rectangle([lx, by1, rx, by2], fill=(12, 15, 20), outline=(140, 112, 58), width=1)
        fill_w = int((rx - lx - 2) * ratio)
        d.rectangle([lx + 1, by1 + 1, lx + 1 + fill_w, by2 - 1], fill=bar_col)
        cy += 30

    # Divider 2
    y_div2 = cy + 4
    d.line([(x1 + 10, y_div2), (x2 - 10, y_div2)], fill=(165, 132, 66), width=1)

    # 3. Combat stats (Урон / Точность / Защита)
    cy = y_div2 + 10
    for s_name, s_val in [("Урон", "18 — 26"), ("Точность", "78%"), ("Броня / Уворот", "14 / 12%")]:
        d.text((lx, cy), s_name, fill=(210, 218, 228), font=f_body)
        tw = d.textbbox((0, 0), s_val, font=f_val)[2]
        d.text((rx - tw, cy), s_val, fill=(240, 210, 140), font=f_val)
        cy += 22

    # Divider 3
    y_div3 = cy + 5
    d.line([(x1 + 10, y_div3), (x2 - 10, y_div3)], fill=(165, 132, 66), width=1)

    # 4. Intent & Active Effects (5 mini square slots in a row)
    cy = y_div3 + 9
    d.text((lx, cy), "Намерение: Готовит удар", fill=(215, 185, 115), font=f_sub)
    cy += 18
    d.text((lx, cy), "Активные эффекты:", fill=(155, 168, 185), font=f_sub)
    cy += 16
    slot_sz = 34
    slot_gap = 8
    for si in range(5):
        sx = lx + si * (slot_sz + slot_gap)
        if sx + slot_sz <= rx:
            d.polygon(chamfer_rect(sx, cy, sx + slot_sz, cy + slot_sz, 3), fill=(16, 20, 27), outline=(175, 140, 68), width=1)
    cy += slot_sz + 10

    # Divider 4
    d.line([(x1 + 8, cy), (x2 - 8, cy)], fill=(185, 150, 75), width=2)
    cy += 10

    # 5. Three collapsible category rows (› Атака, › Защита, › Прочее)
    for idx_t, tab_lbl in enumerate(["›  Атака", "›  Защита", "›  Прочее"]):
        row_rx = rx - (idx_t * 16 if (x2 - x1) > 280 else 0)
        if cy + 26 <= y2 - 10:
            d.polygon(chamfer_rect(lx, cy, row_rx, cy + 26, 4), fill=(22, 27, 36), outline=(165, 132, 66), width=1)
            d.text((lx + 10, cy + 6), tab_lbl, fill=(225, 205, 150), font=f_body)
            cy += 31


def build_target_inspector_mockups():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    shot_path = brain_dir / ".user_uploaded" / "media_1792965627888_3d008c70.png"
    shot = Image.open(shot_path).convert("RGBA")
    sw, sh = shot.size

    try:
        f_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 11)
        f_title = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 20)
        f_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
        f_val = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 12)
    except Exception:
        f_sub = f_title = f_body = f_val = ImageFont.load_default()

    # In-scene mockup on media_1792965627888_3d008c70.png (565x660):
    # Tall sleek vertical panel at x=16..268 (width=252 px), y=18..518 (height=500 px)
    # Wait: at y=518, the broken hex cliff is around x=260, so x=16..256 (width 240 px, height 485 px, y=16..501)
    # clears the broken hex cliff completely with breathing room!
    ov1 = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(ov1)
    px1, py1, px2, py2 = 16, 16, 258, 502  # 242 x 486 px (approx 1 : 2.0 tall ratio!)
    # Outer obsidian slab + thin double-beveled antique gold & bronze rim
    d1.polygon(chamfer_rect(px1, py1, px2, py2, 10), fill=(20, 24, 32, 242), outline=(215, 175, 88, 255), width=2)
    d1.polygon(chamfer_rect(px1 + 4, py1 + 4, px2 - 4, py2 - 4, 8), fill=(18, 22, 29, 245), outline=(135, 105, 52, 255), width=1)
    draw_inspector_content(d1, px1, py1, px2, py2, f_sub, f_title, f_body, f_val)

    scene_mock1 = Image.alpha_composite(shot, ov1).convert("RGB")
    scene_mock1.save(str(brain_dir / "target_inspector_in_scene_preview.png"))

    # =========================================================================
    # Now build the 2048x2048 (2K) 2x2 Blueprint & Binary Mask for the Target Inspector Sheet!
    # What do we pack into the 4 cells (1024x1024 each) so the panel is 100% modular & complete?
    # - Left half [1,1] + [2,1] or Top-Left [1,1]:
    #   Wait: if we put the Tall Inspector Frame inside a 1024x2048 vertical column OR inside [1,1] at 484 x 960 px:
    #   Wait — if the Tall Inspector Frame spans [1,1] (or [1,1]+[2,1] full height 860 x 1720 px? No, on screen it is only 242 x 486 px, so 484 x 960 px inside a single 1024x1024 cell [1,1] is already 2X supersampled retina resolution!).
    #   Let's check what else we can put in [1,2], [2,1], [2,2] if [1,1] holds the Tall Inspector Frame (480 x 940 px):
    #   - [1,1] (x: 272..752, y: 42..982 -> 480 x 940 px): Main Tall Target Inspector Panel Frame (with thin double-beveled gold/bronze rim, recessed header compartment, and subtle horizontal divider grooves).
    #   - [1,2] (x: 1024..2048, y: 0..1024): Expanded / Sliding Detail Plate (480 x 940 px clean tall backing plate without internal dividers, used when expanding Attack/Defense/Other stats or as a second modular tall panel!)
    #   - [2,1] (x: 0..1024, y: 1024..2048):
    #     * Top: Accordion / Category Header Bar Frame (▸ Атака / ▸ Защита / ▸ Прочее, 820 x 96 px)
    #     * Middle: Recessed Resource Bar Frame (HP / Energy / Stamina track frame, 820 x 56 px)
    #     * Bottom: 3 Circular Monster Intent / Status Medallion Frames above battlefield hexes (Attack / Wait / Alert badges, r = 110 px each)!
    #   - [2,2] (x: 1024..2048, y: 1024..2048):
    #     * Active Effect / Buff / Debuff Mini-Slot Frame + 9 Combat Token Icons (or 4 Status/Intent Medallions with engraved icons: Crossed Swords, Hourglass, Shield, Skull/Boss)!
    # =========================================================================
    sz = 2048
    mask_img = Image.new("L", (sz, sz), 0)
    line_img = Image.new("RGB", (sz, sz), (0, 0, 0))
    dm = ImageDraw.Draw(mask_img)
    dl = ImageDraw.Draw(line_img)

    # CELL [1,1]: Main Tall Target Inspector Frame (480 x 940 px, ratio 1 : 1.96)
    ix1, iy1, ix2, iy2 = 272, 42, 752, 982
    p_main = chamfer_rect(ix1, iy1, ix2, iy2, 18)
    dm.polygon(p_main, fill=255)
    dl.polygon(p_main, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(ix1 + 10, iy1 + 10, ix2 - 10, iy2 - 10, 13), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(ix1 + 20, iy1 + 20, ix2 - 20, iy2 - 20, 9), outline=(255, 255, 255), width=3)
    # Header divider groove (y = 42 + 168 = 210)
    for dy_div in [210, 420, 580, 740]:
        dl.line([(ix1 + 20, dy_div), (ix2 - 20, dy_div)], fill=(255, 255, 255), width=3)
        dl.line([(ix1 + 28, dy_div + 6), (ix2 - 28, dy_div + 6)], fill=(190, 190, 190), width=2)

    # CELL [1,2]: Clean Tall Backing / Extension Plate (480 x 940 px, no internal dividers — universal tall frame!)
    bx1, by1, bx2, by2 = 1296, 42, 1776, 982
    p_back = chamfer_rect(bx1, by1, bx2, by2, 18)
    dm.polygon(p_back, fill=255)
    dl.polygon(p_back, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(bx1 + 10, by1 + 10, bx2 - 10, by2 - 10, 13), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(bx1 + 20, by1 + 20, bx2 - 20, by2 - 20, 9), outline=(255, 255, 255), width=3)

    # CELL [2,1]: Internal Bar Frames (Accordion Tab Bar + Resource Track Bar + Stat Row Highlight Frame)
    # 1) Accordion Section Button Frame (▸ Атака / ▸ Защита / ▸ Прочее): 840 x 96 px
    s1_x1, s1_y1, s1_x2, s1_y2 = 92, 1140, 932, 1236
    p_s1 = chamfer_rect(s1_x1, s1_y1, s1_x2, s1_y2, 12)
    dm.polygon(p_s1, fill=255)
    dl.polygon(p_s1, outline=(255, 255, 255), width=4)
    dl.polygon(chamfer_rect(s1_x1 + 8, s1_y1 + 8, s1_x2 - 8, s1_y2 - 8, 8), outline=(255, 255, 255), width=2)
    dl.polygon(chamfer_rect(s1_x1 + 15, s1_y1 + 15, s1_x2 - 15, s1_y2 - 15, 5), outline=(255, 255, 255), width=2)

    # 2) Sleek Recessed Resource Bar Track (for Здоровье / Энергия / Стамина): 840 x 52 px
    s2_x1, s2_y1, s2_x2, s2_y2 = 92, 1360, 932, 1412
    p_s2 = chamfer_rect(s2_x1, s2_y1, s2_x2, s2_y2, 8)
    dm.polygon(p_s2, fill=255)
    dl.polygon(p_s2, outline=(255, 255, 255), width=3)
    dl.polygon(chamfer_rect(s2_x1 + 6, s2_y1 + 6, s2_x2 - 6, s2_y2 - 6, 5), outline=(255, 255, 255), width=2)

    # 3) 3 Circular Monster Intent / Status Medallions above hexes (Attack, Wait, Defense/Alert)
    for idx_m, mcx in enumerate([232, 512, 792]):
        mcy = 1720
        mr = 115
        dm.ellipse((mcx - mr, mcy - mr, mcx + mr, mcy + mr), fill=255)
        dl.ellipse((mcx - mr, mcy - mr, mcx + mr, mcy + mr), outline=(255, 255, 255), width=4)
        dl.ellipse((mcx - mr + 10, mcy - mr + 10, mcx + mr - 10, mcy + mr - 10), outline=(255, 255, 255), width=2)
        dl.ellipse((mcx - mr + 20, mcy - mr + 20, mcx + mr - 20, mcy + mr - 20), outline=(255, 255, 255), width=3)

    # CELL [2,2]: Angled / Cliff-Hugging Variant of the Tall Target Inspector Frame (560 x 940 px)
    # Wide at the top (560 px) and chamfered along the bottom-right at 60 degrees to hug the broken hex cliff!
    ax1, ay1, ax2, ay2 = 1256, 1066, 1816, 2006
    cut_w = 220  # bottom-right diagonal cut width
    cut_h = 360  # bottom-right diagonal cut height (follows the ~60° slope of the broken hex cliff!)
    ch = 18
    p_angled = [
        (ax1 + ch, ay1),
        (ax2 - ch, ay1),
        (ax2, ay1 + ch),
        (ax2, ay2 - cut_h),
        (ax2 - cut_w, ay2),
        (ax1 + ch, ay2),
        (ax1, ay2 - ch),
        (ax1, ay1 + ch),
    ]
    dm.polygon(p_angled, fill=255)
    dl.polygon(p_angled, outline=(255, 255, 255), width=4)
    # Inner bevels of angled frame
    for inset, lw in [(10, 2), (20, 3)]:
        pi = [
            (ax1 + ch + inset * 0.5, ay1 + inset),
            (ax2 - ch - inset * 0.5, ay1 + inset),
            (ax2 - inset, ay1 + ch + inset * 0.5),
            (ax2 - inset, ay2 - cut_h - inset * 0.4),
            (ax2 - cut_w - inset * 0.4, ay2 - inset),
            (ax1 + ch + inset * 0.5, ay2 - inset),
            (ax1 + inset, ay2 - ch - inset * 0.5),
            (ax1 + inset, ay1 + ch + inset * 0.5),
        ]
        dl.polygon(pi, outline=(255, 255, 255), width=lw)

    # Save preview
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
        (24, 12, "[1,1] ВЫСОКАЯ ПАНЕЛЬ ПРОТИВНИКА (с секциями под Имя, Бары, Урон, Эффекты)"),
        (1048, 12, "[1,2] ЧИСТАЯ ВЫСОКАЯ ПЛИТА-ПОДЛОЖКА (без перегородок — для раскрытия статов)"),
        (24, 1040, "[2,1] ПЛАШКА ВКЛАДКИ (Атака/Защита/Прочее) + РАМКА БАРА + 3 МЕДАЛЬОНА НАМЕРЕНИЙ"),
        (1048, 1040, "[2,2] ВАРИАНТ ПАНЕЛИ СО СКОСОМ ПОД УГОЛ ОБЛОМАННЫХ ГЕКСОВ АРЕНЫ"),
    ]
    for lx, ly, ltxt in labels:
        dp.text((lx, ly), ltxt, fill=(255, 215, 90), font=font_h)

    mask_img.save(str(brain_dir / "target_inspector_mask_2048.png"))
    line_img.save(str(brain_dir / "target_inspector_lineart_2048.png"))
    prev_img.save(str(brain_dir / "target_inspector_preview_2048.png"))
    print("Saved target_inspector_in_scene_preview.png and 2048x2048 blueprint.")


if __name__ == "__main__":
    build_target_inspector_mockups()
