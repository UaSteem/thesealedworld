"""Order a single 1024x1024 Duel Circle (V2: Narrower Rim & Rune Channel, ZERO Spikes)
and generate its Alpha-Cutout Rune Stencil version + Hollow Ring version.
"""
import io
import math
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFilter


def draw_rune_glyph(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_mid: float, angle_deg: float, kind: int, width: int = 3):
    """Draw a sleeker, smaller angular elder-futhark-inspired rune glyph oriented radially at angle_deg."""
    rad = math.radians(angle_deg)
    ux, uy = math.cos(rad), math.sin(rad)
    tx, ty = -uy, ux

    def pt(dr: float, dt: float) -> tuple[float, float]:
        return (cx + (r_mid + dr) * ux + dt * tx, cy + (r_mid + dr) * uy + dt * ty)

    # Sleeker rune size (-10..+10 radial, -5..+5 tangential) for the narrower rune channel
    g = kind % 6
    if g == 0:
        draw.line([pt(-10, -4), pt(10, -4)], fill=(255, 255, 255), width=width)
        draw.line([pt(10, -4), pt(3, 5)], fill=(255, 255, 255), width=width)
        draw.line([pt(2, -4), pt(-5, 5)], fill=(255, 255, 255), width=width)
    elif g == 1:
        draw.line([pt(-10, -5), pt(10, -5)], fill=(255, 255, 255), width=width)
        draw.line([pt(-10, 5), pt(10, 5)], fill=(255, 255, 255), width=width)
        draw.line([pt(-10, -5), pt(10, 5)], fill=(255, 255, 255), width=width)
        draw.line([pt(10, -5), pt(-10, 5)], fill=(255, 255, 255), width=width)
    elif g == 2:
        draw.line([pt(-10, -4), pt(10, -4)], fill=(255, 255, 255), width=width)
        draw.line([pt(10, -4), pt(2, 5)], fill=(255, 255, 255), width=width)
        draw.line([pt(2, 5), pt(-2, -4)], fill=(255, 255, 255), width=width)
        draw.line([pt(-2, -4), pt(-10, 5)], fill=(255, 255, 255), width=width)
    elif g == 3:
        draw.line([pt(-10, 0), pt(10, 0)], fill=(255, 255, 255), width=width)
        draw.line([pt(0, 0), pt(10, -6)], fill=(255, 255, 255), width=width)
        draw.line([pt(0, 0), pt(10, 6)], fill=(255, 255, 255), width=width)
    elif g == 4:
        draw.line([pt(-10, 0), pt(-3, 0)], fill=(255, 255, 255), width=width)
        draw.polygon([pt(-3, 0), pt(3, -5), pt(10, 0), pt(3, 5)], outline=(255, 255, 255), width=width)
    else:
        draw.line([pt(-10, 0), pt(10, 0)], fill=(255, 255, 255), width=width)
        draw.line([pt(10, 0), pt(2, -6)], fill=(255, 255, 255), width=width)
        draw.line([pt(10, 0), pt(2, 6)], fill=(255, 255, 255), width=width)


def build_1024_masks_v2(brain_dir: Path) -> tuple[Image.Image, Image.Image]:
    """Build 1024x1024 binary mask and structural lineart for V2 Duel Circle:
    - Narrower outer rim and narrower rune channel (total ring thickness 82px instead of 140px!)
    - ZERO spikes, ZERO radial ribs that could trigger spikes!
    """
    size = 1024
    cx, cy = 512.0, 512.0

    # V2 Narrower ring geometry:
    r_outer = 430        # Smooth outer circular boundary (NO SPIKES)
    r_bevel_out = 420    # Inner edge of outer antique gold lip
    r_filigree_in = 394  # Narrow bronze filigree band (36px total outer band instead of 64px)
    r_rune_out = 384     # Outer edge of narrower rune groove
    r_rune_mid = 368     # Centerline of narrower rune groove (32px wide instead of 44/76px)
    r_rune_in = 352      # Inner edge of narrower rune groove
    r_floor = 342        # Large central obsidian stone floor (684px diameter instead of 616px)

    # 1. Binary solid mask (white circle on black, strictly smooth circle)
    mask_img = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask_img)
    draw_mask.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), fill=255)

    # 2. Structural lineart blueprint (white on black — NO radial spike lines!)
    line_img = Image.new("RGB", (size, size), (0, 0, 0))
    draw_line = ImageDraw.Draw(line_img)

    for r, w in [
        (r_outer, 5),
        (r_bevel_out, 2),
        (r_filigree_in, 4),
        (r_rune_out, 2),
        (r_rune_in, 2),
        (r_floor, 4),
    ]:
        draw_line.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255), width=w)

    # 32 sleek smaller runes in the narrower recessed channel
    num_runes = 32
    for i in range(num_runes):
        draw_rune_glyph(draw_line, cx, cy, r_rune_mid, i * (360.0 / num_runes), i, width=3)

    mask_path = brain_dir / "single_circle_v2_mask_1024.png"
    line_path = brain_dir / "single_circle_v2_lineart_1024.png"
    mask_img.save(str(mask_path))
    line_img.save(str(line_path))
    return mask_img, line_img


PROMPT_V2 = """Create a single high-detail 1024x1024 2D game battlefield asset: the Circular Duel Arena Platform (Encounter Circle) in pure 90-degree orthographic TOP-DOWN view on a solid pure black (#000000) background.

CRITICAL GEOMETRY & STYLE RULES:
- Image 1 is the exact structural lineart blueprint (white concentric circles and runes on black) with a NARROW, SLEEK outer ring and a large central stone floor.
- Image 2 is the strict circular binary mask (smooth white circle on black).
- Image 3 is the exact material and style reference: Aristocratic Gothic Dark Bronze, sharp double-beveled Antique Gold concentric rims, fine Gothic acanthus relief scrollwork inside the narrow outer bronze band, smaller recessed glowing cyan (#00E5FF) runes in the narrow rune channel, and a smooth matte dark obsidian-slate stone floor (#141820) in the center.
- STRICTLY NO SPIKES: The outer edge of the circle MUST be a completely smooth, round antique-gold/bronze circular rim with ZERO spikes, ZERO compass points, and ZERO protrusions outside the circle of Image 2.
- Do NOT paint any white outline around the outside of the circle; the background outside the bronze/gold rim must be solid pure black (#000000).
- The central stone floor MUST be clean dark matte obsidian-slate stone (NO hexagons, NO characters, NO text inside).
"""


def make_spikeless_style_ref(brain_dir: Path) -> Image.Image:
    """Create a spike-free material reference from duel_circle_1024_raw.png so the AI sees
    the exact same bronze/gold/cyan-rune/obsidian materials but with ZERO spikes on the outer edge!
    """
    v1_raw_path = brain_dir / "duel_circle_1024_raw.png"
    if v1_raw_path.exists():
        im = Image.open(v1_raw_path).convert("RGB")
        # Mask out everything outside r=426 (erasing both the 8 spikes and the white ring)
        mask = Image.new("L", im.size, 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((512 - 426, 512 - 426, 512 + 426, 512 + 426), fill=255)
        black = Image.new("RGB", im.size, (0, 0, 0))
        return Image.composite(im, black, mask)
    return Image.open(brain_dir / "style_1b_gothic_filigree_flathex_1792942867061.jpg").convert("RGB")


def postprocess_duel_circle_v2(out_img: Image.Image, brain_dir: Path):
    cx, cy = 512.0, 512.0
    raw_px = out_img.load()

    # Find the exact outer radius of the painted outer antique gold rim in duel_circle_v2_1024_raw.png
    rim_radii = []
    for k in range(32):
        ang = math.radians(k * 11.25)
        ux, uy = math.cos(ang), math.sin(ang)
        r_found = 480.0
        for r_test in range(508, 420, -1):
            x = int(round(cx + r_test * ux))
            y = int(round(cy + r_test * uy))
            r, g, b = raw_px[x, y]
            lum = (r + g + b) / 3.0
            warmth = r - b
            if lum > 22 and warmth >= 16 and not (r > 210 and g > 210 and b > 205):
                r_found = float(r_test)
                break
        rim_radii.append(r_found)

    rim_radii.sort()
    r_edge = rim_radii[len(rim_radii) // 2] - 0.5
    print(f"Detected clean circular antique-gold outer rim radius: r_edge = {r_edge:.1f} px")

    # 1. Build clean spike-free RGBA circle with anti-aliased circular outer edge
    rgba_circle = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    rpx = rgba_circle.load()

    for y in range(1024):
        for x in range(1024):
            dist = math.hypot(x - cx, y - cy)
            if dist <= r_edge - 1.0:
                r, g, b = raw_px[x, y]
                rpx[x, y] = (r, g, b, 255)
            elif dist < r_edge + 1.0:
                r, g, b = raw_px[x, y]
                alpha = int(255 * (r_edge + 1.0 - dist) / 2.0)
                rpx[x, y] = (r, g, b, max(0, min(255, alpha)))

    rgba_path = brain_dir / "duel_circle_v2_1024_rgba.png"
    rgba_circle.save(str(rgba_path))
    # Also overwrite the main duel_circle_1024_rgba.png so the latest clean version is at the standard name
    rgba_circle.save(str(brain_dir / "duel_circle_1024_rgba.png"))

    # 2. Build RUNE-FREE Smooth Recessed Channel versions (r = 352.8 .. 382.2):
    #    - `duel_circle_v2_no_runes_rgba.png`: clean dark obsidian recessed groove without runes (sampled from between-rune angles)
    #    - `duel_circle_v2_channel_cutout_rgba.png`: the entire groove (r = 353.0 .. 382.0) is punched into the alpha channel
    #      with soft bevel shading at the gold walls (r=353 and r=382) so Phaser can place any animated glow/shader underneath!
    no_runes_circle = rgba_circle.copy()
    nr_px = no_runes_circle.load()

    channel_cutout = rgba_circle.copy()
    cc_px = channel_cutout.load()

    # Sample the clean between-rune groove radial profile at angles halfway between the 32 runes (e.g. 5.625 + k*11.25 deg)
    clean_groove_profile = {}
    for r_int in range(351, 385):
        rs, gs, bs = [], [], []
        for k in range(32):
            ang = math.radians(5.625 + k * 11.25)
            sx = int(round(cx + r_int * math.cos(ang)))
            sy = int(round(cy + r_int * math.sin(ang)))
            pr, pg, pb = raw_px[sx, sy]
            # Exclude any slight cyan glow spillover
            if pg - pr < 12 and pb - pr < 16:
                rs.append(pr)
                gs.append(pg)
                bs.append(pb)
        if rs:
            rs.sort()
            gs.sort()
            bs.sort()
            m = len(rs) // 2
            clean_groove_profile[r_int] = (rs[m], gs[m], bs[m])
        else:
            clean_groove_profile[r_int] = (18, 22, 27)

    r_ch_in = 352.8
    r_ch_out = 382.2
    r_ch_mid = 0.5 * (r_ch_in + r_ch_out)
    r_ch_half = 0.5 * (r_ch_out - r_ch_in)

    for y in range(1024):
        for x in range(1024):
            r, g, b, a = nr_px[x, y]
            if a == 0:
                continue
            dist = math.hypot(x - cx, y - cy)
            if r_ch_in <= dist <= r_ch_out:
                # Normalized position across the groove width: -1.0 at inner gold wall, 0.0 at center, +1.0 at outer gold wall
                norm_d = abs(dist - r_ch_mid) / r_ch_half
                r_key = max(351, min(384, int(round(dist))))
                cr, cg, cb = clean_groove_profile[r_key]

                # Smoothly blend near the gold bevel walls (norm_d > 0.82)
                if norm_d > 0.82:
                    wall_t = (norm_d - 0.82) / 0.18
                    # Remove any cyan tint even near the wall
                    base_r, base_g, base_b = r, min(g, int(r * 1.05 + 8)), min(b, int(r * 0.95 + 10))
                    nr_r = int(cr * (1.0 - wall_t) + base_r * wall_t)
                    nr_g = int(cg * (1.0 - wall_t) + base_g * wall_t)
                    nr_b = int(cb * (1.0 - wall_t) + base_b * wall_t)
                else:
                    nr_r, nr_g, nr_b = cr, cg, cb

                nr_px[x, y] = (nr_r, nr_g, nr_b, a)

                # For the Alpha-Cutout Channel:
                # Center of the groove is 95% transparent (alpha ~ 12), curving smoothly up to opaque dark bevel shadow at the gold walls!
                cutout_Curve = math.pow(norm_d, 2.6)  # 0.0 across center, rising steeply near ±1.0 walls
                new_a = int(a * (0.04 + 0.96 * cutout_Curve))
                cc_px[x, y] = (14, 18, 24, max(0, min(255, new_a)))

    no_runes_circle.save(str(brain_dir / "duel_circle_v2_no_runes_rgba.png"))
    channel_cutout.save(str(brain_dir / "duel_circle_v2_channel_cutout_rgba.png"))

    # Also keep the rune-stencil version just in case
    cutout_circle = rgba_circle.copy()
    cpx = cutout_circle.load()
    glow_overlay = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    gpx = glow_overlay.load()
    for y in range(1024):
        for x in range(1024):
            r, g, b, a = cpx[x, y]
            if a == 0:
                continue
            dist = math.hypot(x - cx, y - cy)
            if 335.0 <= dist <= 398.0:
                cyan_ness = max(0, min(g, b) - r)
                if cyan_ness > 12:
                    rune_strength = min(255, int((cyan_ness - 12) * 2.2))
                    new_alpha = max(0, int(a * (1.0 - (rune_strength / 255.0) * 0.96)))
                    dark_stone = int(r * 0.55)
                    cpx[x, y] = (dark_stone, dark_stone, int(dark_stone * 1.05), new_alpha)
                    gpx[x, y] = (r, g, b, rune_strength)

    cutout_circle.save(str(brain_dir / "duel_circle_v2_1024_rune_cutout_rgba.png"))
    cutout_circle.save(str(brain_dir / "duel_circle_1024_rune_cutout_rgba.png"))
    glow_overlay.save(str(brain_dir / "duel_circle_v2_1024_rune_overlay_rgba.png"))
    glow_overlay.save(str(brain_dir / "duel_circle_1024_rune_overlay_rgba.png"))

    # 3. Also build HOLLOW RING (ring-only) versions where the central stone floor (r < 336) is transparent
    ring_only_rgba = no_runes_circle.copy()
    ring_only_cutout = channel_cutout.copy()
    ro_px = ring_only_rgba.load()
    rc_px = ring_only_cutout.load()
    r_inner_hole = 338.0
    for y in range(1024):
        for x in range(1024):
            dist = math.hypot(x - cx, y - cy)
            if dist < r_inner_hole - 1.5:
                ro_px[x, y] = (0, 0, 0, 0)
                rc_px[x, y] = (0, 0, 0, 0)
            elif dist < r_inner_hole:
                fade = (dist - (r_inner_hole - 1.5)) / 1.5
                r1, g1, b1, a1 = ro_px[x, y]
                r2, g2, b2, a2 = rc_px[x, y]
                ro_px[x, y] = (r1, g1, b1, int(a1 * fade))
                rc_px[x, y] = (r2, g2, b2, int(a2 * fade))

    ring_only_rgba.save(str(brain_dir / "duel_circle_v2_ring_only_1024_rgba.png"))
    ring_only_rgba.save(str(brain_dir / "duel_circle_ring_only_1024_rgba.png"))
    ring_only_cutout.save(str(brain_dir / "duel_circle_v2_channel_cutout_ring_only_rgba.png"))
    ring_only_cutout.save(str(brain_dir / "duel_circle_ring_only_1024_rune_cutout_rgba.png"))

    # 3b. Build the EXACT Gold-Bevel + Rune-Channel Circle (r <= 395.5, matching the top-left circle of Style 1B:
    #     outer double-beveled antique gold rim at r=383..395.5 + rune channel at r=353..383 + inner gold rim at r=340..352 + stone floor,
    #     with ZERO outer filigree band and ZERO deformation!)
    slim_rgba = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    slim_cutout = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    slim_channel_cutout = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    sl_px = slim_rgba.load()
    slc_px = slim_cutout.load()
    slcc_px = slim_channel_cutout.load()
    r_slim_out = 395.5
    for y in range(1024):
        for x in range(1024):
            dist = math.hypot(x - cx, y - cy)
            if dist <= r_slim_out - 1.2:
                sl_px[x, y] = rpx[x, y]
                slc_px[x, y] = cpx[x, y]
                slcc_px[x, y] = cc_px[x, y]
            elif dist < r_slim_out:
                fade = (r_slim_out - dist) / 1.2
                r1, g1, b1, a1 = rpx[x, y]
                r2, g2, b2, a2 = cpx[x, y]
                r3, g3, b3, a3 = cc_px[x, y]
                sl_px[x, y] = (r1, g1, b1, int(a1 * fade))
                slc_px[x, y] = (r2, g2, b2, int(a2 * fade))
                slcc_px[x, y] = (r3, g3, b3, int(a3 * fade))

    slim_rgba.save(str(brain_dir / "duel_circle_v2_slim_1024_rgba.png"))
    slim_cutout.save(str(brain_dir / "duel_circle_v2_slim_1024_rune_cutout_rgba.png"))
    slim_channel_cutout.save(str(brain_dir / "duel_circle_v2_slim_channel_cutout_rgba.png"))

    # 4. Dark preview + 3-color Underglow Demo
    dark_prev = Image.new("RGB", (1024, 1024), (14, 18, 24))
    dark_prev.paste(rgba_circle, (0, 0), rgba_circle)
    dark_prev.save(str(brain_dir / "duel_circle_v2_1024_dark_preview.png"))

    demo_w, demo_h = 1860, 640
    demo_img = Image.new("RGB", (demo_w, demo_h), (14, 18, 24))
    small_cutout = channel_cutout.resize((580, 580), Image.Resampling.LANCZOS)

    underglows = [
        (310, 320, (0, 215, 255), (195, 255, 255)),
        (930, 320, (255, 175, 25), (255, 245, 175)),
        (1550, 320, (235, 35, 65), (255, 165, 180)),
    ]
    for ucx, ucy, ucol_outer, ucol_core in underglows:
        under_layer = Image.new("RGBA", (580, 580), (0, 0, 0, 0))
        udraw = ImageDraw.Draw(under_layer)
        s_out = int(384 * 580 / 1024)
        s_mid1 = int(372 * 580 / 1024)
        s_mid2 = int(362 * 580 / 1024)
        s_in = int(350 * 580 / 1024)
        udraw.ellipse((290 - s_out, 290 - s_out, 290 + s_out, 290 + s_out), fill=(*ucol_outer, 255))
        udraw.ellipse((290 - s_mid1, 290 - s_mid1, 290 + s_mid1, 290 + s_mid1), fill=(*ucol_core, 255))
        udraw.ellipse((290 - s_mid2, 290 - s_mid2, 290 + s_mid2, 290 + s_mid2), fill=(*ucol_outer, 255))
        udraw.ellipse((290 - s_in, 290 - s_in, 290 + s_in, 290 + s_in), fill=(14, 18, 24, 255))
        under_layer = under_layer.filter(ImageFilter.GaussianBlur(radius=4))

        combined = Image.alpha_composite(under_layer, small_cutout)
        demo_img.paste(combined, (ucx - 290, ucy - 290), combined)

    demo_img.save(str(brain_dir / "duel_circle_v2_1024_underglow_demo.png"))
    demo_img.save(str(brain_dir / "duel_circle_1024_underglow_demo.png"))
    print("SUCCESS! Saved V2 narrow spike-free 1024x1024 duel circle assets and underglow demo.")


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_v2_path = brain_dir / "duel_circle_v2_1024_raw.png"

    if raw_v2_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing V2 raw API image: {raw_v2_path}")
        out_img = Image.open(raw_v2_path).convert("RGB")
        postprocess_duel_circle_v2(out_img, brain_dir)
        return

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    mask_img, line_img = build_1024_masks_v2(brain_dir)
    style_img = make_spikeless_style_ref(brain_dir)

    client = genai.Client(api_key=api_key)
    print("Sending V2 (Narrower Rim, ZERO Spikes) 1024x1024 Duel Circle generation request to gemini-3-pro-image-preview...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[PROMPT_V2, line_img, mask_img.convert("RGB"), style_img],
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

    out_img.save(str(raw_v2_path))
    postprocess_duel_circle_v2(out_img, brain_dir)


if __name__ == "__main__":
    main()
