"""Order the 20-tile (5x4) Rift Island Hex & Cliff Tileset Sheet via Gemini API (gemini-3-pro-image-preview):
- [Row 0, Col 0]: Full Walkable Ground Base Tile (clean summer grass and forest soil)
- Other 19 cells: 19 mathematical outer cliff/border configurations strictly matching the solid mask and lineart:
  * 6 single-edge cliff borders (SE, S, SW, NW, N, NE)
  * 6 double-edge corner cliff borders
  * 6 triple-edge cape cliff borders
  * 1 internal border
- Output: Raw PNG -> Transparent RGBA PNG (lossless transparent background) + Dark Preview + 20 individual sliced tiles.
"""
import io
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw


PROMPT_RIFT_TILESET_5X4 = """Create a high-detail 2048x2048 (2K) 2D game environment tile sprite sheet arranged in a strict 5x4 grid (twenty distinct cells: 5 columns x 4 rows) on a solid pure black (#000000) background, in high tactical orthographic view.

CRITICAL MASK, GEOMETRY & STYLE CONSTRAINTS:
- Image 1 is the exact structural lineart blueprint (cyan hex outlines, magenta void/cliff break lines, and violet cliff depth vectors).
- Image 2 is the strict binary silhouette mask (white shapes on pure black #000000 background). Every single tile and cliff face MUST stay strictly inside the white silhouette areas of Image 2! All black areas of Image 2 MUST remain solid pure black (#000000) so they can be made 100% transparent alpha.
- Image 3 is the exact artistic style and brushwork reference: notice the rich 2D hand-painted digital gouache / matte painting style, warm sunlit ochre-green meadow tones, soft layered brushwork, and chiseled granite rock facets.
- 100% UNIFIED TERRAIN MATERIAL ACROSS ALL 20 CELLS:
  * Every cell's upper walking surface MUST share the exact same lush summer grass, soft emerald moss, and warm forest dirt tone, illuminated by soft warm daylight from the upper-left.
  * On cells with cliffs (where Image 1 indicates void edges): render solid vertical chiseled granite rock cliff walls dropping down into the black void, with natural rock strata, facets, and cracks.
  * ZERO TEXT, ZERO NUMBERS, ZERO UI ELEMENTS, ZERO GLOWING PURPLE NEON, ZERO COSMIC DUST.

CONTENTS OF THE 20 CELLS (5 columns x 4 rows):
- Cell [Row 0, Col 0] (Top-Left): FULL BASE GROUND TILE — flat, intact, walkable summer grass and soil filling the entire hex polygon.
- Cells 2 through 20: The 19 distinct island cliff edge configurations strictly following the corresponding white shapes in Image 2. Where the edge breaks off into black void, show the rugged vertical granite cliff drop-off with rock strata and cracks.
"""


def postprocess_rift_tileset(raw_img: Image.Image, brain_dir: Path):
    w, h = raw_img.size
    mask_path = brain_dir / "rift_tileset_5x4_solid_mask_4k.png"
    mask_img = Image.open(mask_path).convert("L")
    if mask_img.size != (w, h):
        mask_img = mask_img.resize((w, h), Image.Resampling.LANCZOS)

    rpx = raw_img.load()
    mpx = mask_img.load()
    rgba_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out_px = rgba_img.load()

    # Apply mask with clean edge anti-aliasing (no black halo)
    for y in range(h):
        for x in range(w):
            mv = mpx[x, y]
            if mv == 0:
                out_px[x, y] = (0, 0, 0, 0)
                continue
            r, g, b = rpx[x, y]
            # Near boundary smoothing
            near_edge = False
            for d in (1, 2, 3):
                if (
                    x - d < 0 or x + d >= w or y - d < 0 or y + d >= h
                    or mpx[x - d, y] == 0 or mpx[x + d, y] == 0
                    or mpx[x, y - d] == 0 or mpx[x, y + d] == 0
                ):
                    near_edge = True
                    break

            if near_edge:
                # If dark black background bled into edge pixel, suppress it
                lum = (r + g + b) / 3.0
                if lum < 25:
                    out_px[x, y] = (0, 0, 0, 0)
                elif lum < 50:
                    out_px[x, y] = (r, g, b, 120)
                else:
                    out_px[x, y] = (r, g, b, 255)
            else:
                out_px[x, y] = (r, g, b, 255)

    rgba_path = brain_dir / "rift_tileset_5x4_rgba_2048.png"
    rgba_img.save(str(rgba_path))

    dark_bg = Image.new("RGBA", (w, h), (16, 20, 28, 255))
    dark_prev = Image.alpha_composite(dark_bg, rgba_img).convert("RGB")
    dark_prev_path = brain_dir / "rift_tileset_5x4_dark_preview_2048.png"
    dark_prev.save(str(dark_prev_path))

    print(f"Saved Transparent RGBA sheet: {rgba_path}")
    print(f"Saved Dark Preview: {dark_prev_path}")

    # Slice into 20 individual tiles (5 columns x 4 rows)
    slices_dir = brain_dir / "rift_tileset_slices"
    slices_dir.mkdir(exist_ok=True)
    cw, ch = w // 5, h // 4
    for idx in range(20):
        c = idx % 5
        r = idx // 5
        tile_crop = rgba_img.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
        tile_crop.save(str(slices_dir / f"tile_{idx:02d}.png"))
    print(f"Saved 20 individual sliced tiles into: {slices_dir}")


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "rift_tileset_5x4_raw_2048.png"

    if raw_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing raw image: {raw_path}")
        raw_img = Image.open(raw_path).convert("RGB")
        postprocess_rift_tileset(raw_img, brain_dir)
        return

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    lineart_path = brain_dir / "rift_tileset_5x4_lineart_4k.png"
    mask_path = brain_dir / "rift_tileset_5x4_solid_mask_4k.png"
    style_path = brain_dir / "tactical_map_concept_fullscreen_1793059391138.jpg"

    lineart_img = Image.open(lineart_path).convert("RGB")
    mask_img = Image.open(mask_path).convert("RGB")
    style_img = Image.open(style_path).convert("RGB")

    # Resize input guides to 2048x2048 for optimal Gemini 2K processing
    if lineart_img.size != (2048, 2048):
        lineart_img = lineart_img.resize((2048, 2048), Image.Resampling.LANCZOS)
    if mask_img.size != (2048, 2048):
        mask_img = mask_img.resize((2048, 2048), Image.Resampling.LANCZOS)

    client = genai.Client(api_key=api_key)
    print("Ordering 2048x2048 (2K) 5x4 Rift Tileset Sheet via gemini-3-pro-image-preview...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[lineart_img, mask_img, style_img, PROMPT_RIFT_TILESET_5X4],
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

    print(f"Received Rift Tileset 2K image of size: {raw_img.size}")
    if raw_img.size != (2048, 2048):
        raw_img = raw_img.resize((2048, 2048), Image.Resampling.LANCZOS)

    raw_img.save(str(raw_path))
    postprocess_rift_tileset(raw_img, brain_dir)


if __name__ == "__main__":
    main()
