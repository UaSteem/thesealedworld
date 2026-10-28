"""Order the V2 2048x2048 (2K) 2x2 Player Control Zone Sheet via Gemini API:
- Thin, sleek double-beveled antique gold & dark bronze profile matching the Slim Duel Circle and Empty Hex Tiles (media_1792956936340_12dcdbb8.png)
- ZERO crystals/gems
- [1,1] Fused Top Token Bar + Right-Bottom Quarter-Circle (with Dragon relief medallion in corner hub + 3 sector buttons), fused through the top-right corner, with NO solid backing plate under the left arm of the Token Bar
- [1,2] Standalone Rectangular Sliding Backing Plate with thin hex-tile-style bevel rim
- [2,1] Two Longitudinal Row Button Frames (Feint + Basic Attack) with thin rims
- [2,2] Square Skill/Item Slot Frame with thin rim (~6.5% border thickness) and wide open obsidian interior
"""
import collections
import io
import math
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw


PROMPT_CONTROL_ZONE_V2_2K = """Create a high-detail 2048x2048 (2K) 2D game UI sprite sheet arranged in a strict 2x2 grid (four 1024x1024 cells) on a solid pure black (#000000) background, in pure 90-degree orthographic TOP-DOWN view.

CRITICAL GEOMETRY, THIN-BEVEL & STYLE RULES:
- Image 1 is the exact structural blueprint (warm bronze lines on black).
- Image 2 is the strict binary silhouette mask (white shapes on pure black #000000 background). Every element MUST stay strictly inside the white silhouette shapes of Image 2! All black areas of Image 2 MUST remain solid pure black (#000000) — NEVER use a white background!
- Image 3 is the exact in-game material and border-thickness reference: notice the THIN, SLEEK, CRISP double-beveled Antique Gold and Dark Bronze rims on the circular ring and the empty hexagonal tiles around smooth matte dark obsidian-slate stone (#141820).
- THIN REFINED BORDERS ONLY: All frames on this sheet MUST use those exact THIN, sleek, jewelry-grade double-beveled antique gold and dark bronze rims (NO thick, chunky, bloated frames, and NO giant corner shields!).
- ZERO CRYSTALS / ZERO GEMS: Do NOT place any cyan crystals or gemstones on any of the frames. Use pure dark bronze, sharp double-beveled antique gold, subtle low-relief gothic filigree inside the narrow bronze bands, and matte dark obsidian-slate (#141820) interiors.

EXACT CONTENTS OF THE 4 CELLS (1024x1024 each, strictly inside the white shapes of Image 2):

1. Top-Left [1,1] (x: 0..1024, y: 0..1024) — LOW & WIDE FUSED TOP TOKEN BAR + COMPACT CORNER QUARTER-CIRCLE (NO BACKING PLATE ON THE LEFT):
   - A sleek, low-profile monolithic corner console where:
     * Top Horizontal Token Bar (width 920 px, height 64 px) contains 9 HORIZONTAL RECTANGULAR chamfered pill-shaped recessed obsidian token cells in a single row, each framed by a thin antique gold rim.
     * Compact Right-Bottom Quarter-Circle (radius 286 px, centered at bottom-right of the shape) is seamlessly fused to the bottom edge of the right end of the Token Bar, with their right vertical edges strictly flush and NO sharp triangular beak protruding to the left.
   - Inside the Compact Quarter-Circle:
     * In the bottom-right corner vertex hub (radius 132 px): a purely decorative quarter-medallion featuring a refined, low-relief sculpted Antique Gold & Bronze DRAGON emblem.
     * Around the dragon corner hub: 3 compact curved sector tab buttons with thin double-beveled antique gold borders, matte dark obsidian-slate (#141820) interiors, and crisp, stylized diagonal embossed Antique Gold serif inscriptions tilted along each sector as shown in Image 1:
       - Bottom-left sector (tilted -15 degrees): "ATTACK"
       - Middle diagonal sector (tilted -45 degrees): "ITEM"
       - Top-right sector (tilted -75 degrees): "ABILITY"
   - CRITICAL: The entire area under the left overhanging arm of the Token Bar (to the left of the Quarter-Circle) MUST remain 100% EMPTY PURE BLACK (#000000) as shown in Image 2! Do NOT draw any backing plate there!

2. Top-Right [1,2] (x: 1024..2048, y: 0..1024) — LOW & WIDE STANDALONE RECTANGULAR SLIDING BACKING PLATE (3.2:1 WIDE RATIO, THIN RIM):
   - A wide, low-profile rectangular matte dark obsidian-slate (#141820) stone slab (920x286 px) framed by a THIN, sleek, chamfered double-beveled antique gold and dark bronze border (matching the exact border thickness and look of the empty hexagonal tiles in Image 3, with NO bulky corner brackets and completely empty smooth interior).

3. Bottom-Left [2,1] (x: 0..1024, y: 1024..2048) — TWO SLEEK LONGITUDINAL ROW BUTTON FRAMES (THIN RIMS):
   - Upper elongated horizontal button frame (Feint Row Frame): thin, sleek chamfered double-beveled antique gold and dark bronze rim around a wide, clean matte dark obsidian-slate (#141820) interior (no text inside).
   - Lower elongated horizontal button frame (Basic Attack Button Frame): thin, sleek chamfered double-beveled royal antique gold and dark bronze rim (slightly brighter gold bevel on the inner and outer lip, with subtle gothic engraving inside the narrow rim) around a wide, clean matte dark obsidian-slate (#141820) interior (no text inside).

4. Bottom-Right [2,2] (x: 1024..2048, y: 1024..2048) — UNIVERSAL SQUARE SLOT FRAME (THIN RIM, NO CRYSTALS):
   - A square slot frame with a THIN, crisp double-beveled antique gold and dark bronze border (only ~6% border thickness, matching the empty hexagonal tile rim in Image 3, with ZERO crystals and ZERO attachments) surrounding a large, completely open, flat matte dark obsidian-slate (#141820) square interior (~88% of the square's width, no text or icons inside).
"""


def make_tinted_v2_lineart(brain_dir: Path) -> Image.Image:
    """Tint control_zone_v2_lineart_2048.png to warm bronze/gold and add a subtle dragon-emblem
    sketch inside the bottom-right corner hub of [1,1].
    """
    line_img = Image.open(brain_dir / "control_zone_v2_lineart_2048.png").convert("RGB")
    w, h = line_img.size

    # Subtle dragon emblem contour inside the compact corner hub of [1,1] (center 972, 680, r=132)
    d = ImageDraw.Draw(line_img)
    hcx, hcy = 972, 680
    for r_orn in [96, 68, 42]:
        d.arc((hcx - r_orn, hcy - r_orn, hcx + r_orn, hcy + r_orn), start=186, end=264, fill=(190, 190, 190), width=2)

    tinted = Image.new("RGB", (w, h), (0, 0, 0))
    lpx = line_img.load()
    tpx = tinted.load()
    for y in range(h):
        for x in range(w):
            v = lpx[x, y][0]
            if v > 0:
                tpx[x, y] = (int(v * 0.72), int(v * 0.58), int(v * 0.35))
    return tinted


def postprocess_v2_sheet(raw_img: Image.Image, brain_dir: Path):
    """Apply clean anti-aliased silhouette mask from control_zone_v2_mask_2048.png (plus border
    flood-fill refinement) so all 4 elements have crisp transparent backgrounds and exact geometry.
    """
    w, h = raw_img.size
    mask_img = Image.open(brain_dir / "control_zone_v2_mask_2048.png").convert("L")
    if mask_img.size != (w, h):
        mask_img = mask_img.resize((w, h), Image.Resampling.LANCZOS)

    # Smooth 1px anti-aliased alpha from mask_img, combined with flood-fill of any dark/white outer background
    rpx = raw_img.load()
    mpx = mask_img.load()

    rgba_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out_px = rgba_img.load()

    # Strip any white/gray outer background pixel inside or near the mask boundary so edges are 100% fringe-free
    for y in range(h):
        for x in range(w):
            mv = mpx[x, y]
            if mv == 0:
                out_px[x, y] = (0, 0, 0, 0)
                continue
            r, g, b = rpx[x, y]
            # Check if within 4px of mask edge
            near_edge = False
            for d in (1, 2, 3, 4):
                if (
                    x - d < 0 or x + d >= w or y - d < 0 or y + d >= h
                    or mpx[x - d, y] == 0 or mpx[x + d, y] == 0
                    or mpx[x, y - d] == 0 or mpx[x, y + d] == 0
                ):
                    near_edge = True
                    break
            if near_edge:
                lum = (r + g + b) / 3.0
                warmth = r - b
                # Neutral white/gray background pixel inside the mask margin -> transparent!
                if lum > 175 and warmth < 28:
                    out_px[x, y] = (0, 0, 0, 0)
                elif lum > 135 and warmth < 20:
                    out_px[x, y] = (int(r * 0.45), int(g * 0.42), int(b * 0.35), 160)
                else:
                    adj_zero = (
                        (x > 0 and mpx[x - 1, y] == 0)
                        or (x + 1 < w and mpx[x + 1, y] == 0)
                        or (y > 0 and mpx[x, y - 1] == 0)
                        or (y + 1 < h and mpx[x, y + 1] == 0)
                    )
                    out_px[x, y] = (r, g, b, 215 if adj_zero else 255)
            else:
                out_px[x, y] = (r, g, b, 255)

    rgba_path = brain_dir / "control_zone_v2_sheet_2x2_rgba_2048.png"
    rgba_img.save(str(rgba_path))

    dark_bg = Image.new("RGBA", (w, h), (20, 24, 32, 255))
    dark_prev = Image.alpha_composite(dark_bg, rgba_img).convert("RGB")
    dark_prev.save(str(brain_dir / "control_zone_v2_sheet_2x2_dark_preview_2048.png"))
    print(f"Saved V2 2K RGBA sheet and dark preview to: {rgba_path}")


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "control_zone_v2_sheet_2x2_raw_2048.png"

    if raw_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing V2 raw 2K image: {raw_path}")
        raw_img = Image.open(raw_path).convert("RGB")
        postprocess_v2_sheet(raw_img, brain_dir)
        return

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    tinted_line = make_tinted_v2_lineart(brain_dir)
    mask_rgb = Image.open(brain_dir / "control_zone_v2_mask_2048.png").convert("RGB")
    # Style reference: user's actual battlefield scene with the Slim Duel Circle and thin-rimmed Empty Hex Tiles!
    style_scene = Image.open(brain_dir / ".user_uploaded" / "media_1792956936340_12dcdbb8.png").convert("RGB")

    client = genai.Client(api_key=api_key)
    print("Ordering V2 Thin-Bevel 2048x2048 (2K) 2x2 Control Zone Sheet via gemini-3-pro-image-preview...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[PROMPT_CONTROL_ZONE_V2_2K, tinted_line, mask_rgb, style_scene],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="2K",
            ),
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

    print(f"Received V2 image of size: {out_img.size}")
    if out_img.size != (2048, 2048):
        out_img = out_img.resize((2048, 2048), Image.Resampling.LANCZOS)

    out_img.save(str(raw_path))
    postprocess_v2_sheet(out_img, brain_dir)


if __name__ == "__main__":
    main()
