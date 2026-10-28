import math
import os
from PIL import Image, ImageDraw

def draw_flat_hex(draw, cx, cy, radius, outline, width=3):
    # Flat-topped hexagon: flat horizontal edges at top and bottom
    # Angles: 0, 60, 120, 180, 240, 300 degrees from vertical, so vertices at 30, 90, 150, 210, 270, 330
    points = []
    for i in range(6):
        angle = math.radians(60 * i)
        # vertex with 60*i gives flat-topped when angle has cos(0)=1 horizontal or vertical
        # In standard hex: angle = 60*i gives pointy-topped.
        # angle = 60*i + 30 gives FLAT-TOPPED (top edge horizontal at y = cy - r*sin(60))
        # Let's verify: i=1: 90 deg -> (cx, cy+r). Top is i=4: 270 deg -> (cx, cy-r)? That's pointy!
        # For FLAT-TOPPED: vertices are at (cx + r*cos(a), cy + r*sin(a)) where a = 60*i
        # Let's check a=0: (cx+r, cy), a=60: (cx+r/2, cy+r*sqrt(3)/2), a=120: (cx-r/2, cy+r*sqrt(3)/2)
        # Top edge is between a=240 and a=300!
        # Both have y = cy - r*sqrt(3)/2 -> EXACT FLAT HORIZONTAL EDGE AT TOP!
        # And a=60 to a=120 have y = cy + r*sqrt(3)/2 -> EXACT FLAT HORIZONTAL EDGE AT BOTTOM!
        a = math.radians(60 * i)
        px = cx + radius * math.cos(a)
        py = cy + radius * math.sin(a)
        points.append((px, py))
    draw.polygon(points, outline=outline, width=width)
    return points

def create_layout_reference():
    size = 2048
    brain_dir = r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9"
    os.makedirs(brain_dir, exist_ok=True)

    # Images for Black-BG (white lines) and White-BG (black lines)
    img_b = Image.new("RGB", (size, size), (0, 0, 0))
    img_w = Image.new("RGB", (size, size), (255, 255, 255))

    draw_b = ImageDraw.Draw(img_b)
    draw_w = ImageDraw.Draw(img_w)

    def draw_line(pts, width=4):
        draw_b.line(pts, fill=(255, 255, 255), width=width)
        draw_w.line(pts, fill=(0, 0, 0), width=width)

    def draw_poly(pts, width=4):
        draw_b.polygon(pts, outline=(255, 255, 255), width=width)
        draw_w.polygon(pts, outline=(0, 0, 0), width=width)

    def draw_ellipse(bbox, width=4):
        draw_b.ellipse(bbox, outline=(255, 255, 255), width=width)
        draw_w.ellipse(bbox, outline=(0, 0, 0), width=width)

    def draw_rect(bbox, radius=16, width=4):
        draw_b.rounded_rectangle(bbox, radius=radius, outline=(255, 255, 255), width=width)
        draw_w.rounded_rectangle(bbox, radius=radius, outline=(0, 0, 0), width=width)

    # 4x4 Grid geometry setup
    pad = 64
    gap = 24
    grid_w = (size - 2 * pad - 3 * gap) / 4
    grid_h = grid_w # square grid cells

    # Compute bounding box for cell (col, row, span_x, span_y)
    def cell_box(c, r, sx=1, sy=1):
        x1 = pad + c * (grid_w + gap)
        y1 = pad + r * (grid_h + gap)
        x2 = x1 + sx * grid_w + (sx - 1) * gap
        y2 = y1 + sy * grid_h + (sy - 1) * gap
        return (x1, y1, x2, y2)

    # Helper: draw container frame (compartment border)
    def make_box(c, r, sx=1, sy=1):
        b = cell_box(c, r, sx, sy)
        draw_rect(b, radius=24, width=3)
        return b

    # --- 1. ROW 0 ---
    # Col 0: 01. РАМКА УЧАСТНИКА (1x1)
    b01 = make_box(0, 0)
    cx01, cy01 = (b01[0] + b01[2]) / 2, (b01[1] + b01[3]) / 2
    r01 = grid_w * 0.38
    # Outer flat-topped hex
    hex_pts = []
    for i in range(6):
        a = math.radians(60 * i)
        hex_pts.append((cx01 + r01 * math.cos(a), cy01 + r01 * math.sin(a)))
    draw_poly(hex_pts, width=5)
    # Inner cutout hex (window)
    inner_r01 = r01 * 0.72
    inner_pts = []
    for i in range(6):
        a = math.radians(60 * i)
        inner_pts.append((cx01 + inner_r01 * math.cos(a), cy01 + inner_r01 * math.sin(a)))
    draw_poly(inner_pts, width=4)
    # Badge at bottom-right corner of hex
    badge_x = cx01 + r01 * 0.55
    badge_y = cy01 + r01 * 0.75
    draw_ellipse((badge_x - 36, badge_y - 36, badge_x + 36, badge_y + 36), width=4)

    # Col 1: 02. ПЛИТКА ПОЛЯ (1x1)
    b02 = make_box(1, 0)
    cx02, cy02 = (b02[0] + b02[2]) / 2, (b02[1] + b02[3]) / 2
    r02 = grid_w * 0.38
    hex02_pts = []
    for i in range(6):
        a = math.radians(60 * i)
        hex02_pts.append((cx02 + r02 * math.cos(a), cy02 + r02 * math.sin(a)))
    draw_poly(hex02_pts, width=5)
    # Inner subtle bevel line
    bevel_r = r02 * 0.84
    bevel_pts = []
    for i in range(6):
        a = math.radians(60 * i)
        bevel_pts.append((cx02 + bevel_r * math.cos(a), cy02 + bevel_r * math.sin(a)))
    draw_poly(bevel_pts, width=3)

    # Col 2: 05. КРУГ УПРАВЛЕНИЯ (СТАНДАРТНЫЙ 1x1!)
    b05 = make_box(2, 0)
    cx05, cy05 = (b05[0] + b05[2]) / 2, (b05[1] + b05[3]) / 2
    r05_outer = grid_w * 0.40
    r05_inner = grid_w * 0.22
    # Outer ring
    draw_ellipse((cx05 - r05_outer, cy05 - r05_outer, cx05 + r05_outer, cy05 + r05_outer), width=5)
    # Inner center circle
    draw_ellipse((cx05 - r05_inner, cy05 - r05_inner, cx05 + r05_inner, cy05 + r05_inner), width=4)
    # 9 radial sectors in the outer ring
    for i in range(9):
        ang = math.radians(360 / 9 * i - 90)
        x_in = cx05 + r05_inner * math.cos(ang)
        y_in = cy05 + r05_inner * math.sin(ang)
        x_out = cx05 + r05_outer * math.cos(ang)
        y_out = cy05 + r05_outer * math.sin(ang)
        draw_line([(x_in, y_in), (x_out, y_out)], width=3)

    # Col 3: 04. ПАНЕЛЬ СВЕДЕНИЙ (1x1)
    b04 = make_box(3, 0)
    cx04, cy04 = (b04[0] + b04[2]) / 2, (b04[1] + b04[3]) / 2
    pw, ph = grid_w * 0.65, grid_h * 0.82
    draw_rect((cx04 - pw/2, cy04 - ph/2, cx04 + pw/2, cy04 + ph/2), radius=18, width=5)
    # Inner header separator
    draw_line([(cx04 - pw/2 + 15, cy04 - ph/2 + 60), (cx04 + pw/2 - 15, cy04 - ph/2 + 60)], width=3)

    # --- 2. ROW 1 & 2: КРУГ ВСТРЕЧИ (2x2!) ---
    # Cols 0..1, Rows 1..2: 03. КРУГ ВСТРЕЧИ · 2 × 2
    b03 = make_box(0, 1, sx=2, sy=2)
    cx03, cy03 = (b03[0] + b03[2]) / 2, (b03[1] + b03[3]) / 2
    r03_outer = (b03[2] - b03[0]) * 0.42
    r03_rune_ring = r03_outer * 0.88
    r03_inner_dais = r03_outer * 0.74
    # Outermost rim
    draw_ellipse((cx03 - r03_outer, cy03 - r03_outer, cx03 + r03_outer, cy03 + r03_outer), width=6)
    # Rune band ring
    draw_ellipse((cx03 - r03_rune_ring, cy03 - r03_rune_ring, cx03 + r03_rune_ring, cy03 + r03_rune_ring), width=4)
    # Inner duel arena floor
    draw_ellipse((cx03 - r03_inner_dais, cy03 - r03_inner_dais, cx03 + r03_inner_dais, cy03 + r03_inner_dais), width=5)
    # 12 rune tick marks around the ring
    for i in range(12):
        ang = math.radians(30 * i)
        x1 = cx03 + r03_inner_dais * math.cos(ang)
        y1 = cy03 + r03_inner_dais * math.sin(ang)
        x2 = cx03 + r03_rune_ring * math.cos(ang)
        y2 = cy03 + r03_rune_ring * math.sin(ang)
        draw_line([(x1, y1), (x2, y2)], width=3)

    # Right side of Row 1: Cols 2..3, Row 1 (2x1): 06. ПОЛОСА СПОСОБНОСТЕЙ
    b06 = make_box(2, 1, sx=2, sy=1)
    cx06, cy06 = (b06[0] + b06[2]) / 2, (b06[1] + b06[3]) / 2
    # 5 square ability buttons
    btn_sz = grid_h * 0.58
    total_btns_w = 5 * btn_sz + 4 * 24
    start_x06 = cx06 - total_btns_w / 2
    for i in range(5):
        bx1 = start_x06 + i * (btn_sz + 24)
        by1 = cy06 - btn_sz / 2
        draw_rect((bx1, by1, bx1 + btn_sz, by1 + btn_sz), radius=14, width=5)
        # Inner button rim
        draw_rect((bx1 + 10, by1 + 10, bx1 + btn_sz - 10, by1 + btn_sz - 10), radius=8, width=2)

    # Right side of Row 2: Cols 2..3, Row 2 (2x1): 07. ПЛАШКА ФИНТА / ПОДСКАЗКИ
    b07 = make_box(2, 2, sx=2, sy=1)
    cx07, cy07 = (b07[0] + b07[2]) / 2, (b07[1] + b07[3]) / 2
    bar_w = (b07[2] - b07[0]) * 0.88
    bar_h = grid_h * 0.36
    draw_rect((cx07 - bar_w/2, cy07 - bar_h/2, cx07 + bar_w/2, cy07 + bar_h/2), radius=18, width=5)
    draw_rect((cx07 - bar_w/2 + 10, cy07 - bar_h/2 + 8, cx07 + bar_w/2 - 10, cy07 + bar_h/2 - 8), radius=12, width=2)

    # --- 3. ROW 3 (BOTTOM ROW): 4 MODULES ---
    # Col 0: 08. АТАКА (мечи)
    b08 = make_box(0, 3)
    cx08, cy08 = (b08[0] + b08[2]) / 2, (b08[1] + b08[3]) / 2
    r08 = grid_w * 0.38
    draw_ellipse((cx08 - r08, cy08 - r08, cx08 + r08, cy08 + r08), width=5)
    # Crossed swords 'X'
    sw_len = r08 * 0.65
    draw_line([(cx08 - sw_len, cy08 - sw_len), (cx08 + sw_len, cy08 + sw_len)], width=6)
    draw_line([(cx08 - sw_len, cy08 + sw_len), (cx08 + sw_len, cy08 - sw_len)], width=6)

    # Col 1: 09. ОЖИДАНИЕ (песочные часы)
    b09 = make_box(1, 3)
    cx09, cy09 = (b09[0] + b09[2]) / 2, (b09[1] + b09[3]) / 2
    r09 = grid_w * 0.38
    draw_ellipse((cx09 - r09, cy09 - r09, cx09 + r09, cy09 + r09), width=5)
    # Hourglass shape
    hg_w = r09 * 0.55
    hg_h = r09 * 0.65
    draw_line([(cx09 - hg_w, cy09 - hg_h), (cx09 + hg_w, cy09 - hg_h)], width=6) # top
    draw_line([(cx09 - hg_w, cy09 + hg_h), (cx09 + hg_w, cy09 + hg_h)], width=6) # bottom
    draw_line([(cx09 - hg_w, cy09 - hg_h), (cx09 + hg_w, cy09 + hg_h)], width=5) # diagonal 1
    draw_line([(cx09 + hg_w, cy09 - hg_h), (cx09 - hg_w, cy09 + hg_h)], width=5) # diagonal 2

    # Col 2: 10. КНОПКА НАВЫКА (квадрат)
    b10 = make_box(2, 3)
    cx10, cy10 = (b10[0] + b10[2]) / 2, (b10[1] + b10[3]) / 2
    sz10 = grid_w * 0.68
    draw_rect((cx10 - sz10/2, cy10 - sz10/2, cx10 + sz10/2, cy10 + sz10/2), radius=18, width=5)
    draw_rect((cx10 - sz10/2 + 12, cy10 - sz10/2 + 12, cx10 + sz10/2 - 12, cy10 + sz10/2 - 12), radius=10, width=3)

    # Col 3: 11. ЗНАЧКИ СОСТОЯНИЯ (3 кружка)
    b11 = make_box(3, 3)
    cx11, cy11 = (b11[0] + b11[2]) / 2, (b11[1] + b11[3]) / 2
    sub_r = grid_w * 0.12
    step11 = grid_w * 0.28
    # 3 status circles horizontally
    for i, s_cx in enumerate([cx11 - step11, cx11, cx11 + step11]):
        draw_ellipse((s_cx - sub_r, cy11 - sub_r, s_cx + sub_r, cy11 + sub_r), width=4)
        if i == 0:
            # Checkmark / shield icon
            draw_line([(s_cx - sub_r*0.4, cy11), (s_cx - sub_r*0.1, cy11 + sub_r*0.35), (s_cx + sub_r*0.45, cy11 - sub_r*0.35)], width=4)
        elif i == 1:
            # 3 dots
            for dx in [-sub_r*0.4, 0, sub_r*0.4]:
                draw_ellipse((s_cx + dx - 4, cy11 - 4, s_cx + dx + 4, cy11 + 4), width=4)
        elif i == 2:
            # Exclamation mark
            draw_line([(s_cx, cy11 - sub_r*0.5), (s_cx, cy11 + sub_r*0.15)], width=4)
            draw_ellipse((s_cx - 3, cy11 + sub_r*0.4 - 3, s_cx + 3, cy11 + sub_r*0.4 + 3), width=4)

    # Save 2048x2048
    out_b_path = os.path.join(brain_dir, "layout_reference_black_2048.png")
    out_w_path = os.path.join(brain_dir, "layout_reference_white_2048.png")
    img_b.save(out_b_path)
    img_w.save(out_w_path)
    print("Saved 2048x2048:", out_b_path, out_w_path)

    # Save 4096x4096 4K
    img_b_4k = img_b.resize((4096, 4096), Image.Resampling.LANCZOS)
    img_w_4k = img_w.resize((4096, 4096), Image.Resampling.LANCZOS)
    out_b_4k_path = os.path.join(brain_dir, "layout_reference_black_4k.png")
    out_w_4k_path = os.path.join(brain_dir, "layout_reference_white_4k.png")
    img_b_4k.save(out_b_4k_path)
    img_w_4k.save(out_w_4k_path)
    print("Saved 4096x4096 4K:", out_b_4k_path, out_w_4k_path)

if __name__ == "__main__":
    create_layout_reference()
