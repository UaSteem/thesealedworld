"""Stage 1 of the Rift Portal System:
Generate and extract 4 standalone visual portal archetypes on a transparent RGBA background:
1. [1,1] Энергетические врата (Rift Gate) — ragged vertical oval/rhomboid tear with deep dark abyssal core and layered silver-white energy rim.
2. [1,2] Пространственная трещина (Fracture) — narrow jagged vertical-diagonal fissure in reality with sharp angular energy edges and dark core slit.
3. [2,1] Вихревой разлом (Vortex) — compact vertical-oval swirling anomaly with internal spiral energy streams twisting into a dark void center.
4. [2,2] Кристаллический разлом (Shattered Reality) — sharp faceted crystalline reality tear framed by clean geometric distortion facets around a dark core.

All 4 are rendered in neutral silver-white / ice-platinum luminance around a deep dark void core
(so Phaser 3 can dynamically recolor them via setTint / two-tone gradients into any difficulty color),
with NO ground cracks, NO wide outer glow halo, and NO stray outer lightning/particles baked in.
"""
import io
import math
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont


PROMPT_RIFT_PORTALS_STAGE1 = """Create a high-detail 2048x2048 (2K) concept & production sheet containing 4 standalone 2D game RIFT PORTAL ARCHETYPES arranged in a strict 2x2 grid (four 1024x1024 cells) on a solid pure black (#000000) background.

ARTISTIC & TECHNICAL REQUIREMENTS (CRITICAL):
- Image 1 and Image 2 are the artistic style references showing the desired ragged dimensional tear aesthetic, internal depth, and core structure.
- Image 3 is the structural proportion and placement guide (each portal must stay centered in its 1024x1024 cell with a vertical upright proportion so it fits cleanly above a single hexagonal map tile).
- NEUTRAL RECOLORABLE PALETTE (SILVER-WHITE / PLATINUM-ICE LUMINANCE + DEEP DARK VOID CORE):
  * Render the glowing energy edges, filaments, and inner streams in NEUTRAL BRIGHT WHITE, SILVER, and PALE ICE-PLATINUM (#D8E8FF to #FFFFFF) surrounding a deep, dark obsidian-indigo dimensional void core (#04060C to #0B1020).
  * Do NOT use heavy purple, red, green, or orange hues — keep the energy neutral white/silver/ice so the game engine (Phaser 3 WebGL) can dynamically tint each portal into any color palette!
- CLEAN STRUCTURAL BODY ONLY (FOR LAYERED ANIMATION):
  * Do NOT bake wide blurry outer glow halos that reach the edges of the cell.
  * Do NOT bake long stray outer lightning bolts or scattered distant spark particles far outside the portal contour (those will be animated as separate layers later).
  * Do NOT draw any ground, grass, rocks, pedestals, or ground cracks underneath the portals — each portal floats purely in space on a solid pure black (#000000) background.
  * ZERO TEXT, ZERO LABELS, ZERO UI FRAMES.

THE 4 PORTAL ARCHETYPES (one centered in each 1024x1024 quadrant):

1. Top-Left [1,1] (x: 0..1024, y: 0..1024) — ARCHETYPE 1: RIFT GATE (Энергетические врата):
   - A vertical ragged oval / diamond-shaped tear in reality with a deep, pitch-dark dimensional abyss inside and a rich, multi-layered ragged silver-white plasma/energy rim that looks unstable and alive.

2. Top-Right [1,2] (x: 1024..2048, y: 0..1024) — ARCHETYPE 2: SPATIAL FRACTURE (Пространственная трещина):
   - A narrower, vertical-diagonal jagged fissure / crack in space-time with a thin dark inner void slit and intense, sharp silver-white energetic fracture edges and short tight internal energy filaments bridging across the tear.

3. Bottom-Left [2,1] (x: 0..1024, y: 1024..2048) — ARCHETYPE 3: VORTEX RIFT (Вихревой разлом):
   - A vertical-elliptical swirling spatial anomaly where dense silver-white and pale-ice energy currents spiral inward around a deep dark central singularity/void, creating a strong sense of inward pull and depth.

4. Bottom-Right [2,2] (x: 1024..2048, y: 1024..2048) — ARCHETYPE 4: SHATTERED REALITY / CRYSTALLINE RIFT (Кристаллический разлом):
   - A sharp, angular diamond-shaped tear in reality whose rim fractures into crisp, refractive geometric shards and faceted reality fragments closely hugging the dark dimensional core.
"""


def build_proportion_guide(brain_dir: Path) -> Image.Image:
    """Create a clean 2048x2048 structural silhouette guide for the 4 portal archetypes."""
    sz = 2048
    guide = Image.new("RGB", (sz, sz), (0, 0, 0))
    d = ImageDraw.Draw(guide)

    # 1. [1,1] Rift Gate (vertical ragged oval/diamond, width ~380, height ~640, centered at 512, 512)
    cx, cy = 512, 512
    pts_gate = []
    for i in range(36):
        a = math.radians(i * 10)
        rx = 185 + 14 * math.sin(a * 5)
        ry = 310 + 18 * math.cos(a * 3)
        # Slightly pinched top and bottom tips like a ragged rift gate
        pinch = 0.78 + 0.22 * (math.sin(a) ** 2)
        pts_gate.append((cx + rx * pinch * math.cos(a), cy + ry * math.sin(a)))
    d.polygon(pts_gate, outline=(190, 215, 255), width=5)
    inner_gate = [(cx + (x - cx) * 0.72, cy + (y - cy) * 0.76) for x, y in pts_gate]
    d.polygon(inner_gate, outline=(110, 140, 190), width=3)

    # 2. [1,2] Spatial Fracture (narrow jagged vertical-diagonal fissure, centered at 1536, 512)
    cx, cy = 1536, 512
    spine = [
        (cx + 18, cy - 330),
        (cx - 28, cy - 210),
        (cx + 34, cy - 95),
        (cx - 32, cy + 25),
        (cx + 26, cy + 145),
        (cx - 18, cy + 255),
        (cx + 8,  cy + 335),
    ]
    left_edge = [(x - w, y) for (x, y), w in zip(spine, [8, 52, 78, 86, 68, 44, 6])]
    right_edge = [(x + w, y) for (x, y), w in zip(spine, [8, 48, 72, 84, 72, 40, 6])]
    d.polygon(left_edge + list(reversed(right_edge)), outline=(190, 215, 255), width=5)
    d.line(spine, fill=(120, 155, 215), width=4)

    # 3. [2,1] Vortex Rift (swirling vertical-oval anomaly, centered at 512, 1536)
    cx, cy = 512, 1536
    d.ellipse((cx - 230, cy - 295, cx + 230, cy + 295), outline=(180, 205, 245), width=4)
    d.ellipse((cx - 115, cy - 155, cx + 115, cy + 155), outline=(110, 140, 190), width=3)
    # Spiral guide arcs
    for arm in range(4):
        base_a = arm * (math.pi / 2.0)
        arm_pts = []
        for s in range(25):
            t = s / 24.0
            r_x = 105 + t * 125
            r_y = 140 + t * 155
            ang = base_a + t * 1.65
            arm_pts.append((cx + r_x * math.cos(ang), cy + r_y * math.sin(ang)))
        d.line(arm_pts, fill=(150, 180, 230), width=3)

    # 4. [2,2] Shattered Reality / Crystalline Rift (faceted diamond rift + close shards, centered at 1536, 1536)
    cx, cy = 1536, 1536
    cryst_outer = [
        (cx, cy - 335),
        (cx + 115, cy - 185),
        (cx + 195, cy - 45),
        (cx + 165, cy + 115),
        (cx + 85, cy + 235),
        (cx, cy + 335),
        (cx - 95, cy + 225),
        (cx - 175, cy + 95),
        (cx - 190, cy - 55),
        (cx - 110, cy - 195),
    ]
    d.polygon(cryst_outer, outline=(190, 215, 255), width=5)
    cryst_inner = [(cx + (x - cx) * 0.58, cy + (y - cy) * 0.64) for x, y in cryst_outer]
    d.polygon(cryst_inner, outline=(110, 140, 190), width=3)
    # Close faceted shard outlines around rim
    shards = [
        [(cx - 225, cy - 90), (cx - 195, cy - 145), (cx - 175, cy - 75)],
        [(cx + 205, cy - 110), (cx + 238, cy - 55), (cx + 195, cy - 25)],
        [(cx - 210, cy + 120), (cx - 175, cy + 175), (cx - 160, cy + 105)],
        [(cx + 185, cy + 135), (cx + 225, cy + 95), (cx + 170, cy + 70)],
    ]
    for sh in shards:
        d.polygon(sh, outline=(170, 200, 245), width=3)

    guide.save(str(brain_dir / "rift_portals_stage1_guide_2048.png"))
    return guide


def extract_portal_rgba(cell_rgb: Image.Image) -> Image.Image:
    """Extract portal to RGBA:
    1. Inner void core: flood-fill from (512, 512) through dark pixels (mc < 90) -> opaque alpha 255 (retains deep void).
    2. Outer wisps: luminance-based alpha un-premultiplied from black background -> smooth fading, zero halos.
    """
    import collections

    w, h = cell_rgb.size
    cell_clean = cell_rgb.copy()
    px = cell_clean.load()

    # Clear outer 26px frame
    border_m = 26
    for y in range(h):
        for x in range(w):
            if x < border_m or x >= w - border_m or y < border_m or y >= h - border_m:
                px[x, y] = (0, 0, 0)

    # Flood-fill inner core from center (512, 512)
    inner_core = bytearray(w * h)
    q = collections.deque()
    start_pts = [(512, 512), (512, 450), (512, 570), (480, 512), (544, 512)]
    for sx, sy in start_pts:
        if max(px[sx, sy]) < 100 and not inner_core[sy * w + sx]:
            inner_core[sy * w + sx] = 1
            q.append((sx, sy))

    while q:
        cx, cy = q.popleft()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if border_m <= nx < w - border_m and border_m <= ny < h - border_m:
                nidx = ny * w + nx
                if not inner_core[nidx] and max(px[nx, ny]) < 85:
                    inner_core[nidx] = 1
                    q.append((nx, ny))

    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out = rgba.load()

    for y in range(h):
        row_off = y * w
        for x in range(w):
            r, g, b = px[x, y]
            mc = max(r, g, b)

            if inner_core[row_off + x]:
                # Deep abyssal inner void: opaque
                out[x, y] = (r, g, b, 255)
            else:
                # Energy rim and outer wisps: un-premultiply from black
                if mc <= 10:
                    out[x, y] = (0, 0, 0, 0)
                else:
                    norm = min(1.0, (mc - 10) / 215.0)
                    alpha = int(min(255, max(0, round((norm ** 1.1) * 255.0))))
                    scale = 255.0 / max(1, mc)
                    ur = min(255, int(r * scale))
                    ug = min(255, int(g * scale))
                    ub = min(255, int(b * scale))
                    # Neutralize wisps to clean silver-white
                    lum_u = int(0.299 * ur + 0.587 * ug + 0.114 * ub)
                    ur = int(ur * 0.4 + lum_u * 0.6)
                    ug = int(ug * 0.4 + lum_u * 0.6)
                    ub = int(ub * 0.4 + lum_u * 0.6)
                    out[x, y] = (ur, ug, ub, alpha)

    return rgba


def build_stage1_comparisons(rgba_sheet: Image.Image, brain_dir: Path):
    """Build:
    1) Individual 512x512 runtime-ready PNGs for the 4 archetypes.
    2) A 2048x2048 comparison sheet on dark slate background with titles.
    3) An in-game scale & tint preview directly on top of the real rift_lab forest hexes (R=128, Y*0.65)!
    """
    cells = [
        ("01_rift_gate",        "1. Энергетические врата (Rift Gate)",        (0, 0, 1024, 1024)),
        ("02_spatial_fracture", "2. Пространственная трещина (Fracture)",     (1024, 0, 2048, 1024)),
        ("03_vortex_rift",      "3. Вихревой разлом (Vortex)",                (0, 1024, 1024, 2048)),
        ("04_shattered_rift",   "4. Кристаллический разлом (Shattered)",      (1024, 1024, 2048, 2048)),
    ]

    crops_512 = []
    for slug, title, box in cells:
        c1024 = rgba_sheet.crop(box)
        c512 = c1024.resize((512, 512), Image.Resampling.LANCZOS)
        c512.save(str(brain_dir / f"portal_archetype_{slug}_512_rgba.png"))
        crops_512.append((slug, title, c512))

    # Save 2048x2048 dark comparison preview
    dark_bg = Image.new("RGBA", (2048, 2048), (15, 19, 26, 255))
    comp = Image.alpha_composite(dark_bg, rgba_sheet).convert("RGB")
    dc = ImageDraw.Draw(comp)
    for g in [0, 1024, 2047]:
        dc.line([(g, 0), (g, 2048)], fill=(55, 70, 92), width=3)
        dc.line([(0, g), (2048, g)], fill=(55, 70, 92), width=3)
    try:
        f_lbl = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
        f_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    except Exception:
        f_lbl = f_sub = ImageFont.load_default()

    for (_, title, box) in cells:
        dc.text((box[0] + 28, box[1] + 24), title, fill=(235, 220, 175), font=f_lbl)

    comp.save(str(brain_dir / "rift_portals_stage1_4archetypes_dark_preview_2048.png"))

    # =========================================================================
    # Build an in-game hex scale + dynamic setTint preview on actual rift_lab hexes (R=128, Y*0.65)!
    # =========================================================================
    soil_path = Path("rift_lab/static/materials/r57/soil-pointy.png")
    board_w, board_h = 1600, 920
    board = Image.new("RGBA", (board_w, board_h), (12, 16, 22, 255))
    db = ImageDraw.Draw(board)

    # Row 1 (y = 260): The 4 archetypes at REAL 1:1 rift_lab hex scale (hex width = 256 px, height = 144 px)
    # in their neutral base state
    # Row 2 (y = 680): The exact same 4 archetypes dynamically tinted via Phaser-style setTint into
    # 4 difficulty palettes (Голубой / Фиолетовый / Красный / Золотой) to prove programmatic recoloring!
    hex_r = 128
    persp_y = 0.65
    hex_h_unproj = math.sqrt(3) * hex_r
    hex_h_proj = int(round(hex_h_unproj * persp_y))  # 144 px

    soil_tile = None
    if soil_path.exists():
        raw_soil = Image.open(soil_path).convert("RGBA")
        # Mask to hex and compress vertically by 0.65 exactly like terrain-projection.js
        unproj_h_int = int(round(hex_h_unproj))
        hex_mask = Image.new("L", (256, unproj_h_int), 0)
        dm = ImageDraw.Draw(hex_mask)
        h_pts = [
            (128 + hex_r * math.cos(math.radians(60 * i)), unproj_h_int / 2 + hex_r * math.sin(math.radians(60 * i)))
            for i in range(6)
        ]
        dm.polygon(h_pts, fill=255)
        s_resized = raw_soil.resize((256, 256), Image.Resampling.LANCZOS)
        top_y = (256 - unproj_h_int) // 2
        s_cropped = s_resized.crop((0, top_y, 256, top_y + unproj_h_int))
        s_masked = Image.new("RGBA", (256, unproj_h_int), (0, 0, 0, 0))
        s_masked.paste(s_cropped, (0, 0), hex_mask)
        soil_tile = s_masked.resize((256, hex_h_proj), Image.Resampling.LANCZOS)

    def tint_portal(src_rgba: Image.Image, core_rgb, outer_rgb) -> Image.Image:
        """Simulate Phaser two-tone tinting on a neutral portal sprite while keeping the dark abyss dark."""
        w, h = src_rgba.size
        spx = src_rgba.load()
        out_im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        opx = out_im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = spx[x, y]
                if a == 0:
                    continue
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                if lum < 0.16:
                    # Deep dark void interior stays dark with a subtle tint undertone
                    t_f = lum / 0.16
                    nr = int(r * 0.5 + outer_rgb[0] * 0.15 * t_f)
                    ng = int(g * 0.5 + outer_rgb[1] * 0.15 * t_f)
                    nb = int(b * 0.5 + outer_rgb[2] * 0.15 * t_f)
                    opx[x, y] = (nr, ng, nb, a)
                elif lum < 0.72:
                    # Mid energy rim -> saturated outer difficulty color
                    t = (lum - 0.16) / (0.72 - 0.16)
                    nr = min(255, int(outer_rgb[0] * (0.35 + 0.85 * t)))
                    ng = min(255, int(outer_rgb[1] * (0.35 + 0.85 * t)))
                    nb = min(255, int(outer_rgb[2] * (0.35 + 0.85 * t)))
                    opx[x, y] = (nr, ng, nb, a)
                else:
                    # Bright inner edge -> blends toward hot bright core_rgb / white
                    t = (lum - 0.72) / (1.0 - 0.72)
                    nr = min(255, int(outer_rgb[0] * (1.0 - t) + core_rgb[0] * t))
                    ng = min(255, int(outer_rgb[1] * (1.0 - t) + core_rgb[1] * t))
                    nb = min(255, int(outer_rgb[2] * (1.0 - t) + core_rgb[2] * t))
                    opx[x, y] = (nr, ng, nb, a)
        return out_im

    tints = [
        ("Средний (Голубой)",    (235, 252, 255), (35, 175, 255)),
        ("Высокий (Фиолетовый)", (245, 220, 255), (165, 55, 255)),
        ("Опасный (Красный)",    (255, 225, 210), (235, 45, 55)),
        ("Элитный (Золотой)",    (255, 250, 215), (245, 165, 35)),
    ]

    db.text((40, 22), "РЯД 1: Реальный масштаб на гексе карты (R=128, Y×0.65, гекс 256×144 px) — Нейтральные исходники (без окраски)", fill=(235, 220, 175), font=f_lbl)
    db.text((40, 472), "РЯД 2: Те же самые 4 исходника после программного перекрашивания (Phaser setTint / градиент сложности)", fill=(235, 220, 175), font=f_lbl)

    portal_disp_sz = 210  # Displayed at 210x210 frame (visible rift ~95x155 px) over a 256x144 hex!
    for i, (slug, title, c512) in enumerate(crops_512):
        col_cx = 220 + i * 385
        # Row 1: Neutral on hex
        hy1 = 290
        if soil_tile:
            board.alpha_composite(soil_tile, (col_cx - 128, hy1 - hex_h_proj // 2))
        p_neutral = c512.resize((portal_disp_sz, portal_disp_sz), Image.Resampling.LANCZOS)
        # Anchor at (0.5, 0.72) of the sprite frame so the portal stands upright over the hex center
        board.alpha_composite(p_neutral, (col_cx - portal_disp_sz // 2, hy1 - int(portal_disp_sz * 0.68)))
        db.text((col_cx - 140, hy1 + 88), title, fill=(210, 220, 235), font=f_sub)

        # Row 2: Tinted on hex
        hy2 = 740
        if soil_tile:
            board.alpha_composite(soil_tile, (col_cx - 128, hy2 - hex_h_proj // 2))
        t_name, core_c, out_c = tints[i]
        p_tinted = tint_portal(p_neutral, core_c, out_c)
        board.alpha_composite(p_tinted, (col_cx - portal_disp_sz // 2, hy2 - int(portal_disp_sz * 0.68)))
        db.text((col_cx - 110, hy2 + 88), t_name, fill=out_c, font=f_sub)

    board.convert("RGB").save(str(brain_dir / "rift_portals_stage1_hex_and_tint_preview.png"))


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "rift_portals_stage1_raw_2048.png"
    rgba_path = brain_dir / "rift_portals_stage1_4archetypes_rgba_2048.png"

    guide_img = build_proportion_guide(brain_dir)

    if raw_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing raw 2K image: {raw_path}")
        raw_img = Image.open(raw_path).convert("RGB")
    else:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY not found in .env")
            sys.exit(1)

        ref1 = Image.open(brain_dir / ".user_uploaded" / "media_1792968716046_d7df0303.jpg").convert("RGB")
        ref2 = Image.open(brain_dir / ".user_uploaded" / "media_1792968729296_b46779dc.jpg").convert("RGB")

        client = genai.Client(api_key=api_key)
        print("Ordering Stage 1 (4 Standalone Rift Portal Archetypes in Neutral Luminance, 2K) via gemini-3-pro-image-preview...")
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[ref1, ref2, guide_img, PROMPT_RIFT_PORTALS_STAGE1],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1",
                    image_size="2K",
                ),
            ),
        )

        raw_img = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                raw_img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                break

        if raw_img is None:
            print("ERROR: No image returned from Gemini API")
            sys.exit(1)

        print(f"Received Stage 1 Portals 2K image of size: {raw_img.size}")
        if raw_img.size != (2048, 2048):
            raw_img = raw_img.resize((2048, 2048), Image.Resampling.LANCZOS)
        raw_img.save(str(raw_path))

    # Extract each 1024x1024 cell to clean RGBA
    rgba_sheet = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    for cx, cy in [(0, 0), (1024, 0), (0, 1024), (1024, 1024)]:
        cell_rgb = raw_img.crop((cx, cy, cx + 1024, cy + 1024))
        cell_rgba = extract_portal_rgba(cell_rgb)
        rgba_sheet.paste(cell_rgba, (cx, cy))

    rgba_sheet.save(str(rgba_path))
    build_stage1_comparisons(rgba_sheet, brain_dir)
    print(f"Saved Stage 1 RGBA sheet and hex comparisons to: {rgba_path}")


if __name__ == "__main__":
    main()
