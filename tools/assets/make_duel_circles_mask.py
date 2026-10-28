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


def draw_rune_glyph(
    draw_fns: list,
    cx: float,
    cy: float,
    r_mid: float,
    angle_deg: float,
    glyph_idx: int,
    color_prev: tuple[int, int, int],
    width: int = 3,
):
    """Draw a deterministic angular runic symbol oriented radially at angle_deg."""
    ang = math.radians(angle_deg)
    ux, uy = math.cos(ang), math.sin(ang)
    tx, ty = -math.sin(ang), math.cos(ang)

    h = 13.0
    w = 7.0

    def pt(r_off: float, t_off: float) -> tuple[float, float]:
        return (
            cx + (r_mid + r_off) * ux + t_off * tx,
            cy + (r_mid + r_off) * uy + t_off * ty,
        )

    stave = [pt(-h, 0), pt(h, 0)]
    strokes = [stave]

    pat = glyph_idx % 6
    if pat == 0:
        strokes.append([pt(0, 0), pt(h * 0.8, w)])
        strokes.append([pt(-h * 0.4, 0), pt(h * 0.4, w)])
    elif pat == 1:
        strokes.append([pt(h, 0), pt(h * 0.2, w), pt(0, 0)])
        strokes.append([pt(0, 0), pt(-h * 0.8, w)])
    elif pat == 2:
        strokes.append([pt(h * 0.3, -w), pt(h, 0), pt(h * 0.3, w)])
    elif pat == 3:
        strokes = [
            [pt(-h, -w), pt(h, w)],
            [pt(h, -w), pt(-h, w)],
            [pt(-h, -w), pt(h, -w)],
            [pt(-h, w), pt(h, w)],
        ]
    elif pat == 4:
        strokes = [
            [pt(-h, -w * 0.8), pt(0, w * 0.9), pt(h, 0), pt(0, -w * 0.9), pt(-h, w * 0.8)]
        ]
    else:
        strokes.append([pt(0, 0), pt(h * 0.85, -w)])
        strokes.append([pt(0, 0), pt(h * 0.85, w)])

    for s in strokes:
        for fn in draw_fns:
            fn(s, width, color_prev)


def generate_duel_circles_masks():
    brain_dir = r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9"
    os.makedirs(brain_dir, exist_ok=True)
    size = 2048

    # 1. Binary Solid Mask (pure #000000 background, 4 solid #FFFFFF circles)
    mask_img = Image.new("RGB", (size, size), (0, 0, 0))
    draw_mask = ImageDraw.Draw(mask_img)

    # 2. Rune-Ring-Only Mask (for locking stone floor & outer rim across all 4 frames)
    ring_mask_img = Image.new("RGB", (size, size), (0, 0, 0))
    draw_ring_mask = ImageDraw.Draw(ring_mask_img)

    # 3. Clean Lineart Reference (white/grey progressive lines on pure #000000 background, no text)
    line_b_img = Image.new("RGB", (size, size), (0, 0, 0))
    draw_line_b = ImageDraw.Draw(line_b_img)

    # 4. Visual Schema Preview (annotated dark-slate blueprint showing the 4 pulsation frames)
    prev_img = Image.new("RGB", (size, size), (22, 31, 38))
    draw_prev = ImageDraw.Draw(prev_img)

    pad = 64
    gap = 48
    cell_w = (size - 2 * pad - gap) // 2  # 936
    cell_h = cell_w  # 936

    def get_box(c: int, r: int) -> tuple[int, int, int, int]:
        x1 = pad + c * (cell_w + gap)
        y1 = pad + r * (cell_h + gap)
        return (x1, y1, x1 + cell_w, y1 + cell_h)

    # 4 progressive frames for a smooth 6-step yoyo loop in Phaser (1 -> 2 -> 3 -> 4 -> 3 -> 2)
    cells = [
        (
            1,
            get_box(0, 0),
            "КАДР 1 · ПОКОЙ (10% · ТЛЕЮЩИЕ РУНЫ)",
            "Руны глубоко в камне, почти погашены, кольцо спокойное",
            (70, 115, 125),   # Dim cyan-slate on preview
            140,              # Lineart brightness for runes (dimmer)
            2,                # Rune stroke width
        ),
        (
            2,
            get_box(1, 0),
            "КАДР 2 · ВДОХ (45% · РАЗГОРАНИЕ РУН)",
            "Загораются сами символы рун и тонкая внутренняя кромка",
            (64, 185, 195),   # Medium cyan glow
            195,
            3,
        ),
        (
            3,
            get_box(0, 1),
            "КАДР 3 · СВЕЧЕНИЕ (75% · ПОЛНОЕ КОЛЬЦО)",
            "Ярко светятся все 24 руны и оба бортика рунического жёлоба",
            (56, 228, 232),   # Bright cyan glow
            235,
            4,
        ),
        (
            4,
            get_box(1, 1),
            "КАДР 4 · ПИК ПУЛЬСАЦИИ (100% · ВСПЫШКА И ОРЕОЛ)",
            "Максимальное сияние рун + двойной энергетический ореол по кольцу",
            (145, 255, 255),  # Intense white-cyan peak bloom
            255,
            5,
        ),
    ]

    BOX_FILL = (32, 46, 56)
    BOX_BORDER = (118, 138, 148)
    SUB_TEXT = (165, 182, 192)
    GOLD = (210, 170, 105)

    font_title = load_font(23, bold=True)
    font_sub = load_font(17, bold=False)

    r_outer = 384
    r_filigree_in = 342
    r_rune_out = 330
    r_rune_mid = 304
    r_rune_in = 278
    r_floor = 264

    for frame_idx, b, title, sub, glow_col, line_lum, rune_w in cells:
        draw_prev.rounded_rectangle(b, radius=18, fill=BOX_FILL, outline=BOX_BORDER, width=3)
        draw_prev.text((b[0] + 26, b[1] + 20), title, fill=GOLD, font=font_title)
        draw_prev.text((b[0] + 26, b[1] + 52), sub, fill=SUB_TEXT, font=font_sub)

        cx = (b[0] + b[2]) / 2
        cy = (b[1] + b[3]) / 2 + 24

        def line_fn(pts, width, prev_col, lum=line_lum):
            draw_line_b.line(pts, fill=(lum, lum, lum), width=width)
            draw_prev.line(pts, fill=prev_col, width=width)

        def ellipse_fn(bbox, width, prev_col, lum=255):
            draw_line_b.ellipse(bbox, outline=(lum, lum, lum), width=width)
            draw_prev.ellipse(bbox, outline=prev_col, width=width)

        # 1. Binary solid mask: full circle
        bbox_outer = (cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer)
        draw_mask.ellipse(bbox_outer, fill=(255, 255, 255))

        # 2. Rune-ring-only mask (annulus between r_floor and r_filigree_in)
        bbox_ring_out = (cx - r_filigree_in, cy - r_filigree_in, cx + r_filigree_in, cy + r_filigree_in)
        bbox_ring_in = (cx - r_floor, cy - r_floor, cx + r_floor, cy + r_floor)
        draw_ring_mask.ellipse(bbox_ring_out, fill=(255, 255, 255))
        draw_ring_mask.ellipse(bbox_ring_in, fill=(0, 0, 0))

        # 3. Fixed structural metal/stone rings (identical across all 4 frames)
        ellipse_fn(bbox_outer, 6, GOLD, lum=220)
        ellipse_fn(bbox_ring_out, 4, GOLD, lum=200)
        ellipse_fn(bbox_ring_in, 5, GOLD, lum=220)

        # 4. Progressive glow rings inside the rune channel depending on frame_idx (1..4)
        ellipse_fn((cx - r_rune_out, cy - r_rune_out, cx + r_rune_out, cy + r_rune_out), frame_idx + 1, glow_col, lum=line_lum)
        ellipse_fn((cx - r_rune_in, cy - r_rune_in, cx + r_rune_in, cy + r_rune_in), frame_idx + 1, glow_col, lum=line_lum)

        if frame_idx >= 3:
            # Frame 3 & 4: inner energy halo rings flanking the runes
            for r_halo in (r_rune_out - 6, r_rune_in + 6):
                ellipse_fn((cx - r_halo, cy - r_halo, cx + r_halo, cy + r_halo), 2, glow_col, lum=line_lum)

        if frame_idx == 4:
            # Frame 4 (Peak): extra outer bloom ring
            for r_bloom in (r_rune_out + 6, r_rune_in - 6):
                ellipse_fn((cx - r_bloom, cy - r_bloom, cx + r_bloom, cy + r_bloom), 3, glow_col, lum=255)

        # 5. 8 symmetrical gothic filigree ribs in the outer bronze band
        for i in range(8):
            ang = math.radians(45 * i)
            p1 = (cx + r_filigree_in * math.cos(ang), cy + r_filigree_in * math.sin(ang))
            p2 = (cx + r_outer * math.cos(ang), cy + r_outer * math.sin(ang))
            line_fn([p1, p2], 4, GOLD, lum=200)

        # 6. 24 identical runic glyphs with progressive stroke width (2 -> 3 -> 4 -> 5) and brightness
        for i in range(24):
            ang_deg = i * 15.0
            draw_rune_glyph([line_fn], cx, cy, r_rune_mid, ang_deg, i, glow_col, width=rune_w)

    # --- PIXEL-LEVEL BOUNDARY VERIFICATION ---
    safe_margin = 36
    safe_zones = [
        (b[0] + safe_margin, b[1] + safe_margin, b[2] - safe_margin, b[3] - safe_margin)
        for _, b, *_ in cells
    ]

    def inside_any_safe_zone(x: int, y: int) -> bool:
        for sx1, sy1, sx2, sy2 in safe_zones:
            if sx1 <= x <= sx2 and sy1 <= y <= sy2:
                return True
        return False

    mask_px = mask_img.load()
    line_px = line_b_img.load()
    v_mask = 0
    v_line = 0
    for y in range(size):
        for x in range(size):
            if not inside_any_safe_zone(x, y):
                if mask_px[x, y] != (0, 0, 0):
                    v_mask += 1
                if line_px[x, y] != (0, 0, 0):
                    v_line += 1

    assert v_mask == 0, f"CRITICAL: {v_mask} mask pixels violated safe zones!"
    assert v_line == 0, f"CRITICAL: {v_line} lineart pixels violated safe zones!"

    mask_path = os.path.join(brain_dir, "duel_circles_solid_mask_2048.png")
    ring_mask_path = os.path.join(brain_dir, "duel_circles_rune_ring_mask_2048.png")
    line_path = os.path.join(brain_dir, "duel_circles_lineart_2048.png")
    prev_path = os.path.join(brain_dir, "duel_circles_preview_2048.png")

    mask_img.save(mask_path)
    ring_mask_img.save(ring_mask_path)
    line_b_img.save(line_path)
    prev_img.save(prev_path)

    mask_img.resize((4096, 4096), Image.Resampling.NEAREST).save(
        os.path.join(brain_dir, "duel_circles_solid_mask_4k.png")
    )
    line_b_img.resize((4096, 4096), Image.Resampling.LANCZOS).save(
        os.path.join(brain_dir, "duel_circles_lineart_4k.png")
    )
    prev_img.resize((4096, 4096), Image.Resampling.LANCZOS).save(
        os.path.join(brain_dir, "duel_circles_preview_4k.png")
    )

    print("SUCCESS: 4-frame pulsation masks & lineart generated with 0 boundary violations!")


if __name__ == "__main__":
    generate_duel_circles_masks()
