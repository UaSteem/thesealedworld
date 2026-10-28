import math
import os
from PIL import Image, ImageDraw, ImageFont


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ]
    )
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def flat_hex_points(cx: float, cy: float, radius: float) -> list[tuple[float, float]]:
    """Flat-topped hexagon: horizontal top and bottom edges."""
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return pts


def edge_slot_polygon(
    p1: tuple[float, float],
    p2: tuple[float, float],
    cx: float,
    cy: float,
    t_start: float = 0.16,
    t_end: float = 0.84,
    inward_offset: float = 10.0,
    thickness: float = 12.0,
) -> list[tuple[float, float]]:
    """Create a recessed bar groove polygon parallel to a hex edge."""
    ax = p1[0] + (p2[0] - p1[0]) * t_start
    ay = p1[1] + (p2[1] - p1[1]) * t_start
    bx = p1[0] + (p2[0] - p1[0]) * t_end
    by = p1[1] + (p2[1] - p1[1]) * t_end

    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2
    vx = cx - mx
    vy = cy - my
    vlen = math.hypot(vx, vy)
    ux, uy = vx / vlen, vy / vlen

    o1x, o1y = ax + ux * inward_offset, ay + uy * inward_offset
    o2x, o2y = bx + ux * inward_offset, by + uy * inward_offset
    i2x, i2y = bx + ux * (inward_offset + thickness), by + uy * (inward_offset + thickness)
    i1x, i1y = ax + ux * (inward_offset + thickness), ay + uy * (inward_offset + thickness)
    return [(o1x, o1y), (o2x, o2y), (i2x, i2y), (i1x, i1y)]


def generate_all():
    brain_dir = r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9"
    os.makedirs(brain_dir, exist_ok=True)
    size = 2048

    # 1. Binary Solid Mask (pure #000000 background, pure #FFFFFF filled silhouettes)
    mask_img = Image.new("RGB", (size, size), (0, 0, 0))
    draw_mask = ImageDraw.Draw(mask_img)

    # 2. Clean Lineart / Canny Reference (pure #000000 background, white structural lines, no text)
    line_b_img = Image.new("RGB", (size, size), (0, 0, 0))
    draw_line_b = ImageDraw.Draw(line_b_img)

    # 3. Clean Lineart Inverted (pure #FFFFFF background, black structural lines, no text)
    line_w_img = Image.new("RGB", (size, size), (255, 255, 255))
    draw_line_w = ImageDraw.Draw(line_w_img)

    # 4. Visual Schema Preview (annotated dark-slate blueprint)
    prev_img = Image.new("RGB", (size, size), (22, 31, 38))
    draw_prev = ImageDraw.Draw(prev_img)

    # Exact integer grid math on 2048x2048:
    # pad = 64, gap = 32 -> cell_w = (2048 - 128 - 96) / 4 = 456
    pad = 64
    gap = 32
    cell_w = (size - 2 * pad - 3 * gap) // 4  # 456
    cell_h = cell_w  # 456

    def get_box(c: int, r: int, sx: int = 1, sy: int = 1) -> tuple[int, int, int, int]:
        x1 = pad + c * (cell_w + gap)
        y1 = pad + r * (cell_h + gap)
        x2 = x1 + sx * cell_w + (sx - 1) * gap
        y2 = y1 + sy * cell_h + (sy - 1) * gap
        return (x1, y1, x2, y2)

    # 16 unit cells partitioned into 11 non-overlapping compartments:
    # - 03: (0,0, 2x2) [4 cells] Круг встречи (7 hexes daisy size)
    # - 01: (2,0, 1x1) [1 cell]  Рамка участника (Гекс + 3 верхних паза + кружок)
    # - 02: (3,0, 1x1) [1 cell]  Плитка поля (Гекс с плоской верхней гранью)
    # - 05: (2,1, 1x1) [1 cell]  Круг управления (Центр + 9 секторов)
    # - 04: (3,1, 1x2) [2 cells] Вертикальная панель статов монстра (высокая 1x2!)
    # - 06: (0,2, 2x1) [2 cells] Готовая панель способностей на 8 ячеек (2 ряда по 4)
    # - 07: (2,2, 1x1) [1 cell]  Выдвижные прямоугольные панели-подложки под круг (3 шт.)
    # - 08: (0,3, 1x1) [1 cell]  Вставка центра: Атака (мечи)
    # - 09: (1,3, 1x1) [1 cell]  Вставка центра: Ожидание (часы)
    # - 10: (2,3, 1x1) [1 cell]  Отдельная ячейка навыка (крупный модуль)
    # - 11: (3,3, 1x1) [1 cell]  Круглые жетоны состояний врага (4 шт.)
    boxes = {
        "03": get_box(0, 0, 2, 2),
        "01": get_box(2, 0, 1, 1),
        "02": get_box(3, 0, 1, 1),
        "05": get_box(2, 1, 1, 1),
        "04": get_box(3, 1, 1, 2),
        "06": get_box(0, 2, 2, 1),
        "07": get_box(2, 2, 1, 1),
        "08": get_box(0, 3, 1, 1),
        "09": get_box(1, 3, 1, 1),
        "10": get_box(2, 3, 1, 1),
        "11": get_box(3, 3, 1, 1),
    }

    labels = {
        "03": ("03  КРУГ ВСТРЕЧИ · 2 × 2", "Чистая круглая арена (размер ромашки из 7 гексов)"),
        "01": ("01  РАМКА УЧАСТНИКА", "HP сверху · Энергия слева · Стамина справа"),
        "02": ("02  ПЛИТКА ПОЛЯ", "Каменный гекс · плоский верх"),
        "05": ("05  КРУГ УПРАВЛЕНИЯ", "Верхний слой: центр + 9 секторов"),
        "04": ("04  ПАНЕЛЬ СТАТОВ · 1 × 2", "Вертикальная доска монстра"),
        "06": ("06  ПАНЕЛЬ СПОСОБНОСТЕЙ · 2 × 1", "Готовая панель на 8 ячеек (2 ряда по 4)"),
        "07": ("07  ПОДЛОЖКИ ПОД КРУГ", "Выдвижные плашки (подмена слоем ниже)"),
        "08": ("08  АТАКА", "Вставка в круг: мечи"),
        "09": ("09  ОЖИДАНИЕ", "Вставка в круг: часы"),
        "10": ("10  ЯЧЕЙКА НАВЫКА", "Отдельный крупный слот"),
        "11": ("11  ТОКЕНЫ СОСТОЯНИЯ", "Атакует · таймер · ждёт · опасность"),
    }

    TEAL = (107, 210, 199)
    GOLD = (220, 177, 109)
    CRIMSON = (232, 108, 108)
    SAPPHIRE = (98, 174, 239)
    AMBER = (229, 192, 123)
    BOX_FILL = (32, 46, 56)
    BOX_BORDER = (118, 138, 148)
    SUB_TEXT = (165, 182, 192)

    font_title = load_font(20, bold=True)
    font_sub = load_font(15, bold=False)

    # Draw cell containers and labels on Visual Preview
    for key, b in boxes.items():
        draw_prev.rounded_rectangle(b, radius=14, fill=BOX_FILL, outline=BOX_BORDER, width=3)
        title, sub = labels[key]
        draw_prev.text((b[0] + 20, b[1] + 16), title, fill=GOLD, font=font_title)
        draw_prev.text((b[0] + 20, b[1] + 44), sub, fill=SUB_TEXT, font=font_sub)

    def dual_line(pts, width=4, prev_color=TEAL):
        draw_line_b.line(pts, fill=(255, 255, 255), width=width)
        draw_line_w.line(pts, fill=(0, 0, 0), width=width)
        draw_prev.line(pts, fill=prev_color, width=width)

    def dual_poly(pts, width=4, prev_color=TEAL):
        draw_line_b.polygon(pts, outline=(255, 255, 255), width=width)
        draw_line_w.polygon(pts, outline=(0, 0, 0), width=width)
        draw_prev.polygon(pts, outline=prev_color, width=width)

    def dual_ellipse(bbox, width=4, prev_color=TEAL):
        draw_line_b.ellipse(bbox, outline=(255, 255, 255), width=width)
        draw_line_w.ellipse(bbox, outline=(0, 0, 0), width=width)
        draw_prev.ellipse(bbox, outline=prev_color, width=width)

    def dual_rect(bbox, radius=14, width=4, prev_color=TEAL):
        draw_line_b.rounded_rectangle(bbox, radius=radius, outline=(255, 255, 255), width=width)
        draw_line_w.rounded_rectangle(bbox, radius=radius, outline=(0, 0, 0), width=width)
        draw_prev.rounded_rectangle(bbox, radius=radius, outline=prev_color, width=width)

    y_off = 22

    # --- 03: КРУГ ВСТРЕЧИ · 2 × 2 (cols 0..1, rows 0..1) ---
    b03 = boxes["03"]
    cx03 = (b03[0] + b03[2]) / 2
    cy03 = (b03[1] + b03[3]) / 2 + 18
    r03_outer = 376  # diameter = 752 inside 944x944 box -> ~96px margin on all sides
    r03_mid = 332
    r03_inner = 286
    bbox03_out = (cx03 - r03_outer, cy03 - r03_outer, cx03 + r03_outer, cy03 + r03_outer)
    bbox03_mid = (cx03 - r03_mid, cy03 - r03_mid, cx03 + r03_mid, cy03 + r03_mid)
    bbox03_in = (cx03 - r03_inner, cy03 - r03_inner, cx03 + r03_inner, cy03 + r03_inner)
    draw_mask.ellipse(bbox03_out, fill=(255, 255, 255))
    dual_ellipse(bbox03_out, width=6, prev_color=TEAL)
    dual_ellipse(bbox03_mid, width=3, prev_color=GOLD)
    dual_ellipse(bbox03_in, width=4, prev_color=TEAL)

    # --- 01: РАМКА УЧАСТНИКА (1x1 at col 2, row 0) ---
    b01 = boxes["01"]
    cx01 = (b01[0] + b01[2]) / 2
    cy01 = (b01[1] + b01[3]) / 2 + y_off
    r01 = 152
    hex01_outer = flat_hex_points(cx01, cy01, r01)
    hex01_inner = flat_hex_points(cx01, cy01, r01 * 0.74)
    # Vertices of flat_hex_points:
    # v0: (0 deg, right)
    # v1: (60 deg, bottom-right)
    # v2: (120 deg, bottom-left)
    # v3: (180 deg, left)
    # v4: (240 deg, top-left)
    # v5: (300 deg, top-right)
    # Top horizontal edge (HP): v4 -> v5
    # Top-left edge (Energy/Mana): v3 -> v4
    # Top-right edge (Stamina): v5 -> v0
    slot_hp = edge_slot_polygon(hex01_outer[4], hex01_outer[5], cx01, cy01)
    slot_en = edge_slot_polygon(hex01_outer[3], hex01_outer[4], cx01, cy01)
    slot_st = edge_slot_polygon(hex01_outer[5], hex01_outer[0], cx01, cy01)

    badge_cx = cx01 + r01 * 0.62
    badge_cy = cy01 + r01 * 0.56
    badge_r = 30
    badge_bbox = (badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r)

    draw_mask.polygon(hex01_outer, fill=(255, 255, 255))
    draw_mask.ellipse(badge_bbox, fill=(255, 255, 255))

    dual_poly(hex01_outer, width=5, prev_color=TEAL)
    dual_poly(hex01_inner, width=3, prev_color=TEAL)
    # 3 upper resource grooves: HP (top), Energy (top-left), Stamina (top-right)
    dual_poly(slot_hp, width=3, prev_color=CRIMSON)
    dual_poly(slot_en, width=3, prev_color=SAPPHIRE)
    dual_poly(slot_st, width=3, prev_color=AMBER)

    draw_prev.ellipse(badge_bbox, fill=BOX_FILL, outline=GOLD, width=4)
    draw_line_b.ellipse(badge_bbox, fill=(0, 0, 0), outline=(255, 255, 255), width=4)
    draw_line_w.ellipse(badge_bbox, fill=(255, 255, 255), outline=(0, 0, 0), width=4)

    # --- 02: ПЛИТКА ПОЛЯ (1x1 at col 3, row 0) ---
    b02 = boxes["02"]
    cx02 = (b02[0] + b02[2]) / 2
    cy02 = (b02[1] + b02[3]) / 2 + y_off
    r02 = 152
    hex02_outer = flat_hex_points(cx02, cy02, r02)
    hex02_bevel = flat_hex_points(cx02, cy02, r02 * 0.85)
    draw_mask.polygon(hex02_outer, fill=(255, 255, 255))
    dual_poly(hex02_outer, width=5, prev_color=TEAL)
    dual_poly(hex02_bevel, width=2, prev_color=TEAL)

    # --- 05: КРУГ УПРАВЛЕНИЯ (1x1 at col 2, row 1) ---
    b05 = boxes["05"]
    cx05 = (b05[0] + b05[2]) / 2
    cy05 = (b05[1] + b05[3]) / 2 + y_off
    r05_outer = 148
    r05_inner = 78
    bbox05_out = (cx05 - r05_outer, cy05 - r05_outer, cx05 + r05_outer, cy05 + r05_outer)
    bbox05_in = (cx05 - r05_inner, cy05 - r05_inner, cx05 + r05_inner, cy05 + r05_inner)
    draw_mask.ellipse(bbox05_out, fill=(255, 255, 255))
    dual_ellipse(bbox05_out, width=5, prev_color=TEAL)
    dual_ellipse(bbox05_in, width=4, prev_color=GOLD)
    for i in range(9):
        ang = math.radians(360 / 9 * i - 90)
        p1 = (cx05 + r05_inner * math.cos(ang), cy05 + r05_inner * math.sin(ang))
        p2 = (cx05 + r05_outer * math.cos(ang), cy05 + r05_outer * math.sin(ang))
        dual_line([p1, p2], width=3, prev_color=TEAL)

    # --- 04: ВЕРТИКАЛЬНАЯ ПАНЕЛЬ СТАТОВ МОНСТРА · 1 × 2 (col 3, rows 1..2) ---
    b04 = boxes["04"]
    cx04 = (b04[0] + b04[2]) / 2
    cy04 = (b04[1] + b04[3]) / 2 + 18
    pw04 = 328  # inside 456px width -> 64px margin left/right
    ph04 = 760  # inside 944px height -> comfortable top/bottom margin
    bbox04 = (cx04 - pw04 / 2, cy04 - ph04 / 2, cx04 + pw04 / 2, cy04 + ph04 / 2)
    bbox04_in = (cx04 - pw04 / 2 + 14, cy04 - ph04 / 2 + 14, cx04 + pw04 / 2 - 14, cy04 + ph04 / 2 - 14)
    draw_mask.rounded_rectangle(bbox04, radius=18, fill=(255, 255, 255))
    dual_rect(bbox04, radius=18, width=5, prev_color=TEAL)
    dual_rect(bbox04_in, radius=12, width=2, prev_color=GOLD)
    # Section dividers inside monster stat board (Header / Offense / Defense / Effects)
    for dy_frac in [0.16, 0.44, 0.72]:
        sep_y = bbox04_in[1] + (bbox04_in[3] - bbox04_in[1]) * dy_frac
        dual_line([(bbox04_in[0] + 16, sep_y), (bbox04_in[2] - 16, sep_y)], width=2, prev_color=GOLD)

    # --- 06: ГОТОВАЯ ПАНЕЛЬ СПОСОБНОСТЕЙ · 2 × 1 (cols 0..1, row 2) ---
    # Outer ornate backing frame + 8 square sockets (2 rows of 4, matching user's concept)
    b06 = boxes["06"]
    cx06 = (b06[0] + b06[2]) / 2
    cy06 = (b06[1] + b06[3]) / 2 + y_off
    panel_w06 = 760  # inside 944px width -> 92px margin left/right
    panel_h06 = 296  # inside 456px height -> comfortable margin top/bottom
    bbox06_frame = (
        cx06 - panel_w06 / 2,
        cy06 - panel_h06 / 2,
        cx06 + panel_w06 / 2,
        cy06 + panel_h06 / 2,
    )
    draw_mask.rounded_rectangle(bbox06_frame, radius=18, fill=(255, 255, 255))
    dual_rect(bbox06_frame, radius=18, width=5, prev_color=TEAL)

    slot_sz = 112
    slot_gap_x = 32
    slot_gap_y = 20
    grid_w06 = 4 * slot_sz + 3 * slot_gap_x  # 448 + 96 = 544
    grid_h06 = 2 * slot_sz + slot_gap_y      # 224 + 20 = 244
    sx06_start = cx06 - grid_w06 / 2
    sy06_start = cy06 - grid_h06 / 2
    for row_i in range(2):
        for col_i in range(4):
            sx1 = sx06_start + col_i * (slot_sz + slot_gap_x)
            sy1 = sy06_start + row_i * (slot_sz + slot_gap_y)
            sb = (sx1, sy1, sx1 + slot_sz, sy1 + slot_sz)
            dual_rect(sb, radius=10, width=3, prev_color=GOLD)

    # --- 07: ВЫДВИЖНЫЕ ПРЯМОУГОЛЬНЫЕ ПАНЕЛИ-ПОДЛОЖКИ ПОД КРУГ (1x1 at col 2, row 2) ---
    # 3 rectangular slide-out backing plates stacked cleanly inside b07:
    # Right side goes under the control circle, left side protrudes with slots/grooves
    b07 = boxes["07"]
    cx07 = (b07[0] + b07[2]) / 2
    cy07 = (b07[1] + b07[3]) / 2 + y_off
    plate_w = 340
    plate_h = 74
    plate_gap = 20
    total_h07 = 3 * plate_h + 2 * plate_gap  # 222 + 40 = 262 inside 456px height
    start_y07 = cy07 - total_h07 / 2
    for i in range(3):
        py1 = start_y07 + i * (plate_h + plate_gap)
        pb = (cx07 - plate_w / 2, py1, cx07 + plate_w / 2, py1 + plate_h)
        draw_mask.rounded_rectangle(pb, radius=12, fill=(255, 255, 255))
        dual_rect(pb, radius=12, width=4, prev_color=TEAL if i != 1 else GOLD)
        # Vertical mark on the right showing the overlap zone that tucks under the circle
        tuck_x = pb[2] - 68
        dual_line([(tuck_x, pb[1] + 10), (tuck_x, pb[3] - 10)], width=2, prev_color=GOLD)

    # --- 08: АТАКА (1x1 at col 0, row 3) ---
    b08 = boxes["08"]
    cx08 = (b08[0] + b08[2]) / 2
    cy08 = (b08[1] + b08[3]) / 2 + y_off
    r08 = 140
    bbox08 = (cx08 - r08, cy08 - r08, cx08 + r08, cy08 + r08)
    draw_mask.ellipse(bbox08, fill=(255, 255, 255))
    dual_ellipse(bbox08, width=5, prev_color=TEAL)
    sw = r08 * 0.52
    dual_line([(cx08 - sw, cy08 - sw), (cx08 + sw, cy08 + sw)], width=8, prev_color=GOLD)
    dual_line([(cx08 - sw, cy08 + sw), (cx08 + sw, cy08 - sw)], width=8, prev_color=GOLD)

    # --- 09: ОЖИДАНИЕ (1x1 at col 1, row 3) ---
    b09 = boxes["09"]
    cx09 = (b09[0] + b09[2]) / 2
    cy09 = (b09[1] + b09[3]) / 2 + y_off
    r09 = 140
    bbox09 = (cx09 - r09, cy09 - r09, cx09 + r09, cy09 + r09)
    draw_mask.ellipse(bbox09, fill=(255, 255, 255))
    dual_ellipse(bbox09, width=5, prev_color=TEAL)
    hw, hh = r09 * 0.45, r09 * 0.62
    dual_line([(cx09 - hw, cy09 - hh), (cx09 + hw, cy09 - hh)], width=5, prev_color=GOLD)
    dual_line([(cx09 - hw, cy09 + hh), (cx09 + hw, cy09 + hh)], width=5, prev_color=GOLD)
    dual_line([(cx09 - hw, cy09 - hh), (cx09 + hw, cy09 + hh)], width=5, prev_color=GOLD)
    dual_line([(cx09 + hw, cy09 - hh), (cx09 - hw, cy09 + hh)], width=5, prev_color=GOLD)

    # --- 10: ОТДЕЛЬНАЯ ЯЧЕЙКА НАВЫКА (1x1 at col 2, row 3) ---
    b10 = boxes["10"]
    cx10 = (b10[0] + b10[2]) / 2
    cy10 = (b10[1] + b10[3]) / 2 + y_off
    sz10 = 236
    bbox10 = (cx10 - sz10 / 2, cy10 - sz10 / 2, cx10 + sz10 / 2, cy10 + sz10 / 2)
    bbox10_in = (cx10 - sz10 / 2 + 18, cy10 - sz10 / 2 + 18, cx10 + sz10 / 2 - 18, cy10 + sz10 / 2 - 18)
    draw_mask.rounded_rectangle(bbox10, radius=16, fill=(255, 255, 255))
    dual_rect(bbox10, radius=16, width=5, prev_color=TEAL)
    dual_rect(bbox10_in, radius=10, width=3, prev_color=GOLD)

    # --- 11: КРУГЛЫЕ ТОКЕНЫ СОСТОЯНИЯ ВРАГОВ (1x1 at col 3, row 3) ---
    # 4 circular badges in a clean 2x2 sub-grid inside b11 so each badge is large and crisp:
    # (0) Crossed blades (already attacking us)
    # (1) Timer / hourglass (timer ticking)
    # (2) Waiting '...' (has not acted yet)
    # (3) Danger '!' (imminent strike)
    b11 = boxes["11"]
    cx11 = (b11[0] + b11[2]) / 2
    cy11 = (b11[1] + b11[3]) / 2 + y_off
    sr11 = 56
    offset11 = 76
    badge_centers = [
        (cx11 - offset11, cy11 - offset11),
        (cx11 + offset11, cy11 - offset11),
        (cx11 - offset11, cy11 + offset11),
        (cx11 + offset11, cy11 + offset11),
    ]
    for idx, (scx, scy) in enumerate(badge_centers):
        sbbox = (scx - sr11, scy - sr11, scx + sr11, scy + sr11)
        draw_mask.ellipse(sbbox, fill=(255, 255, 255))
        dual_ellipse(sbbox, width=4, prev_color=TEAL)
        if idx == 0:
            # Crossed swords (attacking us)
            d = 22
            dual_line([(scx - d, scy - d), (scx + d, scy + d)], width=4, prev_color=CRIMSON)
            dual_line([(scx - d, scy + d), (scx + d, scy - d)], width=4, prev_color=CRIMSON)
        elif idx == 1:
            # Timer / hourglass
            w, h = 16, 22
            dual_line([(scx - w, scy - h), (scx + w, scy - h)], width=3, prev_color=GOLD)
            dual_line([(scx - w, scy + h), (scx + w, scy + h)], width=3, prev_color=GOLD)
            dual_line([(scx - w, scy - h), (scx + w, scy + h)], width=3, prev_color=GOLD)
            dual_line([(scx + w, scy - h), (scx - w, scy + h)], width=3, prev_color=GOLD)
        elif idx == 2:
            # Waiting '...'
            for dot_dx in [-18, 0, 18]:
                dot_box = (scx + dot_dx - 4, scy - 4, scx + dot_dx + 4, scy + 4)
                draw_prev.ellipse(dot_box, fill=GOLD)
                draw_line_b.ellipse(dot_box, fill=(255, 255, 255))
                draw_line_w.ellipse(dot_box, fill=(0, 0, 0))
        elif idx == 3:
            # Danger '!'
            dual_line([(scx, scy - 22), (scx, scy + 6)], width=5, prev_color=CRIMSON)
            dot_box = (scx - 4, scy + 16, scx + 4, scy + 24)
            draw_prev.ellipse(dot_box, fill=CRIMSON)
            draw_line_b.ellipse(dot_box, fill=(255, 255, 255))
            draw_line_w.ellipse(dot_box, fill=(0, 0, 0))

    # --- PIXEL-LEVEL BOUNDARY VERIFICATION ---
    safe_margin = 28
    safe_zones = [
        (b[0] + safe_margin, b[1] + safe_margin, b[2] - safe_margin, b[3] - safe_margin)
        for b in boxes.values()
    ]

    def inside_any_safe_zone(x: int, y: int) -> bool:
        for sx1, sy1, sx2, sy2 in safe_zones:
            if sx1 <= x <= sx2 and sy1 <= y <= sy2:
                return True
        return False

    mask_pixels = mask_img.load()
    line_pixels = line_b_img.load()
    violations_mask = 0
    violations_line = 0
    for y in range(size):
        for x in range(size):
            if not inside_any_safe_zone(x, y):
                if mask_pixels[x, y] != (0, 0, 0):
                    violations_mask += 1
                if line_pixels[x, y] != (0, 0, 0):
                    violations_line += 1

    assert violations_mask == 0, f"CRITICAL: {violations_mask} pixels on solid_white_mask violated cell safe zones!"
    assert violations_line == 0, f"CRITICAL: {violations_line} pixels on layout_reference violated cell safe zones!"

    # Save 2048x2048 files
    mask_2k_path = os.path.join(brain_dir, "solid_white_mask_2048.png")
    prev_2k_path = os.path.join(brain_dir, "mask_visual_preview_2048.png")
    line_b_2k_path = os.path.join(brain_dir, "layout_reference_black_2048.png")
    line_w_2k_path = os.path.join(brain_dir, "layout_reference_white_2048.png")

    mask_img.save(mask_2k_path)
    prev_img.save(prev_2k_path)
    line_b_img.save(line_b_2k_path)
    line_w_img.save(line_w_2k_path)

    # Save 4096x4096 4K files
    mask_img.resize((4096, 4096), Image.Resampling.NEAREST).save(
        os.path.join(brain_dir, "solid_white_mask_4k.png")
    )
    prev_img.resize((4096, 4096), Image.Resampling.LANCZOS).save(
        os.path.join(brain_dir, "mask_visual_preview_4k.png")
    )
    line_b_img.resize((4096, 4096), Image.Resampling.LANCZOS).save(
        os.path.join(brain_dir, "layout_reference_black_4k.png")
    )
    line_w_img.resize((4096, 4096), Image.Resampling.LANCZOS).save(
        os.path.join(brain_dir, "layout_reference_white_4k.png")
    )

    print("SUCCESS: 0 boundary violations across all 4,194,304 pixels!")


if __name__ == "__main__":
    generate_all()
