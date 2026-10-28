"""Order the 2048x2048 (2K) 2x2 Battlefield Hex Tiles Sheet (3 Fractured Perimeter Hexes + 1 Full Intact Hex Tile)
via Gemini API (gemini-3-pro-image-preview):
- [1,1] 2/3 Fractured Hex Tile (3 full intact gold/bronze-rimmed edges on the right/bottom + jagged broken stone cliff on top-left)
- [1,2] 1/2 Fractured Hex Tile (2 full intact gold/bronze-rimmed edges on the bottom-right/bottom + diagonal jagged broken stone cliff)
- [2,1] 1/3 Fractured Hex Tile (1 full intact gold/bronze-rimmed edge on bottom-right + narrow jagged broken stone cliff)
- [2,2] Full Intact Flat-Top Hex Tile (all 6 edges framed by thin double-beveled antique gold & dark bronze rim around smooth dark obsidian stone)
"""
import io
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


PROMPT_BROKEN_HEXES_2K = """Create a high-detail 2048x2048 (2K) 2D game battlefield tile sprite sheet arranged in a strict 2x2 grid (four 1024x1024 cells) on a solid pure black (#000000) background, in pure 90-degree orthographic TOP-DOWN view.

CRITICAL GEOMETRY, THIN-BEVEL & UNIFIED MATERIAL RULES:
- Image 1 is the exact structural blueprint (warm bronze lines on black).
- Image 2 is the strict binary silhouette mask (white shapes on pure black #000000 background). Every tile and tile fragment MUST stay strictly inside the white silhouette shapes of Image 2! All black areas of Image 2 MUST remain solid pure black (#000000) — NEVER use a white background!
- Image 3 is the exact in-game material and border-thickness reference: notice the empty flat-topped hexagonal stone tiles with THIN, SLEEK, CRISP double-beveled Antique Gold and Dark Bronze outer rims and smooth matte dark obsidian-slate (#141820) stone interiors.
- 100% IDENTICAL MATERIAL ACROSS ALL 4 CELLS: All 4 cells (the 3 fractured perimeter hex fragments and the 1 full intact hex tile in [2,2]) MUST share the exact same matte dark obsidian-slate (#141820) stone surface texture, lighting, and the exact same thin, sleek double-beveled antique gold and dark bronze border profile so they blend seamlessly when placed side-by-side on a hexagonal grid!
- ZERO CRYSTALS / ZERO GEMS / ZERO TEXT / ZERO SYMBOLS on the stone floor.

EXACT CONTENTS OF THE 4 CELLS (1024x1024 each, strictly inside the white shapes of Image 2):

1. Top-Left [1,1] (x: 0..1024, y: 0..1024) — 2/3 FRACTURED HEXAGON TILE (3 INTACT FRAMED EDGES + BROKEN STONE CLIFF EDGE):
   - Two-thirds of a flat-topped hexagonal stone tile.
   - Along the intact straight outer edges on the top-right, bottom-right, and bottom (as marked by the double-bevel lines in Image 1): draw the exact THIN, sleek double-beveled antique gold and dark bronze border rim. At the two points where the metal rim ends, show a clean broken metal cross-section.
   - Along the jagged diagonal left/top-left edge (where there is NO gold frame): render a realistic, sharp, ancient fractured dark obsidian-slate stone cliff/break edge with stepped chipped stone facets and subtle fine hairline cracks extending slightly into the matte dark obsidian (#141820) slab.

2. Top-Right [1,2] (x: 1024..2048, y: 0..1024) — 1/2 FRACTURED HEXAGON TILE (2 INTACT FRAMED EDGES + DIAGONAL BROKEN STONE CLIFF):
   - Half of a flat-topped hexagonal stone tile.
   - Along the intact straight outer edges on the bottom-right and bottom (and the short side stubs marked in Image 1): draw the exact THIN, sleek double-beveled antique gold and dark bronze border rim, terminating cleanly at the fracture points.
   - Along the jagged diagonal upper-left break line: render a realistic chipped, fractured dark obsidian-slate stone edge with stepped rock facets and a subtle hairline crack, matching [1,1] and [2,2].

3. Bottom-Left [2,1] (x: 0..1024, y: 1024..2048) — 1/3 FRACTURED HEXAGON TILE (1 INTACT FRAMED EDGE + NARROW BROKEN STONE LEDGE):
   - One-third / quarter fragment of a flat-topped hexagonal stone tile.
   - Along the intact straight bottom-right edge (and the short side stubs marked in Image 1): draw the exact THIN, sleek double-beveled antique gold and dark bronze border rim.
   - Along the jagged inner-left break line: render a realistic chipped, fractured dark obsidian-slate stone cliff edge with stepped stone facets.

4. Bottom-Right [2,2] (x: 1024..2048, y: 1024..2048) — FULL INTACT FLAT-TOP HEXAGON TILE (ALL 6 EDGES FRAMED):
   - A complete, intact flat-topped regular hexagon tile (flat horizontal top and bottom edges) framed on all 6 sides by the exact THIN, sleek, crisp double-beveled antique gold and dark bronze border rim surrounding a smooth, flat matte dark obsidian-slate (#141820) stone interior.
"""


def make_tinted_lineart(brain_dir: Path) -> Image.Image:
    line_img = Image.open(brain_dir / "broken_hexes_lineart_2048.png").convert("RGB")
    w, h = line_img.size
    tinted = Image.new("RGB", (w, h), (0, 0, 0))
    lpx = line_img.load()
    tpx = tinted.load()
    for y in range(h):
        for x in range(w):
            v = lpx[x, y][0]
            if v > 0:
                tpx[x, y] = (int(v * 0.72), int(v * 0.58), int(v * 0.35))
    return tinted


def postprocess_broken_hexes_sheet(raw_img: Image.Image, brain_dir: Path):
    w, h = raw_img.size
    mask_img = Image.open(brain_dir / "broken_hexes_mask_2048.png").convert("L")
    if mask_img.size != (w, h):
        mask_img = mask_img.resize((w, h), Image.Resampling.LANCZOS)

    rpx = raw_img.load()
    mpx = mask_img.load()
    rgba_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out_px = rgba_img.load()

    for y in range(h):
        for x in range(w):
            mv = mpx[x, y]
            if mv == 0:
                out_px[x, y] = (0, 0, 0, 0)
                continue
            r, g, b = rpx[x, y]
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

    rgba_path = brain_dir / "broken_hexes_sheet_2x2_rgba_2048.png"
    rgba_img.save(str(rgba_path))

    dark_bg = Image.new("RGBA", (w, h), (20, 24, 32, 255))
    dark_prev = Image.alpha_composite(dark_bg, rgba_img).convert("RGB")
    dark_prev.save(str(brain_dir / "broken_hexes_sheet_2x2_dark_preview_2048.png"))
    print(f"Saved Broken + Full Hexes 2K RGBA sheet and dark preview to: {rgba_path}")


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "broken_hexes_sheet_2x2_raw_2048.png"

    if raw_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing raw 2K image: {raw_path}")
        raw_img = Image.open(raw_path).convert("RGB")
        postprocess_broken_hexes_sheet(raw_img, brain_dir)
        return

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    tinted_line = make_tinted_lineart(brain_dir)
    mask_rgb = Image.open(brain_dir / "broken_hexes_mask_2048.png").convert("RGB")
    style_scene = Image.open(brain_dir / ".user_uploaded" / "media_1792956936340_12dcdbb8.png").convert("RGB")

    client = genai.Client(api_key=api_key)
    print("Ordering 2048x2048 (2K) 2x2 Broken + Full Hex Tiles Sheet via gemini-3-pro-image-preview...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[tinted_line, mask_rgb, style_scene, PROMPT_BROKEN_HEXES_2K],
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

    print(f"Received Broken Hexes 2K image of size: {raw_img.size}")
    if raw_img.size != (2048, 2048):
        raw_img = raw_img.resize((2048, 2048), Image.Resampling.LANCZOS)

    raw_img.save(str(raw_path))
    postprocess_broken_hexes_sheet(raw_img, brain_dir)


if __name__ == "__main__":
    main()
