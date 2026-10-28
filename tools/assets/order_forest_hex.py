"""Order a 2048x2048 (2K) Top-Down Pointy-Topped Forest Hex Tile
via Gemini API (gemini-3-pro-image-preview) following the proven project pipeline:
- Image 1: Structural blueprint (cyan hex outline on black).
- Image 2: Strict binary silhouette mask (white pointy-topped hex on solid #000000 black).
- Image 3: Exact in-game style & species reference (forest-b.png).
"""
import io
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


PROMPT_FOREST_HEX_2K = """Create a high-detail 2048x2048 (2K) 2D game environment tile featuring a dense cluster of trees inside a vertical pointy-topped hexagonal footprint on a solid pure black (#000000) background, in orthographic 90-degree top-down / slightly tilted isometric view.

CRITICAL GEOMETRY, SILHOUETTE & STYLE RULES:
- Image 1 is the exact structural blueprint (cyan hex contour lines on pure black).
- Image 2 is the strict binary silhouette mask (pure white hexagon on pure black #000000 background). The entire forest cluster MUST strictly stay inside the white shape of Image 2! Every tree, branch, and leaf must naturally finish inside the white area. All black areas of Image 2 MUST remain solid pure black (#000000) — NEVER use any background textures, frames, or spillover!
- Image 3 is the exact in-game material, lighting, contrast, and tree species reference: notice the rich 2D hand-painted digital art style (Warcraft III / gouache matte painting), vibrant warm summer daylight, deep contrast shadows inside the foliage, and chunky readable shapes.

EXACT COMPOSITION & TREE SPECIES (MATCHING IMAGE 3 100%):
- Take the EXACT same tree species, textures, and contrast values from Image 3:
  1. Tall stylized spruce / fir conifers with sharp tiered needle branches and rich deep emerald-green foliage.
  2. Broadleaf oak / deciduous trees with voluminous, rounded canopies painted in warm sunny golden-green and olive-green brushwork.
  3. Dense low undergrowth bushes and ground foliage nestled at the base of the tree trunks.
- FRESH NATURAL RE-ARRANGEMENT:
  * Do NOT just clone the placement 1:1; naturally rearrange these same trees into a fresh, harmonious grouping inside the hex boundary.
  * The outer silhouette of the copse must consist of complete, whole tree canopies and bushes with natural foliage contours that touch the inner hex borders, NEVER cropped or sliced by an artificial straight line.
- PURE 2D HAND-PAINTED GAME ART: No miniature bonsai scale, no photorealism, no 3D CGI sheen, no glowing fantasy magic, no UI frames. Solid pure black (#000000) background outside the trees.
"""


def main():
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment or .env", file=sys.stderr)
        sys.exit(1)

    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    img1_path = brain_dir / "forest_hex_blueprint_2k.png"
    img2_path = brain_dir / "forest_hex_mask_2k.png"
    img3_path = brain_dir / "forest_hex_style_scene_2k.png"

    for p in [img1_path, img2_path, img3_path]:
        if not p.exists():
            print(f"ERROR: Missing input file: {p}", file=sys.stderr)
            sys.exit(1)

    print("[1/4] Loading input triad (Blueprint, Mask, Style Reference)...")
    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")
    img3 = Image.open(img3_path).convert("RGB")

    client = genai.Client(api_key=api_key)
    print("[2/4] Calling gemini-3-pro-image-preview with image_size='2K'...")

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[PROMPT_FOREST_HEX_2K, img1, img2, img3],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="2K",
            ),
        ),
    )

    print("[3/4] Parsing 2K image response...")
    raw_img = None
    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    raw_img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGBA")
                    break

    if not raw_img:
        print("ERROR: No image returned from model!", file=sys.stderr)
        sys.exit(1)

    print(f"Received native image resolution: {raw_img.size}")

    raw_path = brain_dir / "forest_hex_v2_raw_2k.png"
    raw_img.save(raw_path, format="PNG")
    print(f"-> Saved raw 2K result: {raw_path}")

    print("[4/4] Extracting natural transparency without knife-cropping...")
    # Convert exterior black background to alpha smoothly (proven runtime pattern from provenance.json)
    # We do NOT slice the trees by the hex boundary. We only key out the black exterior!
    w, h = raw_img.size
    rgba = raw_img.copy()
    raw_px = raw_img.load()
    alpha = Image.new("L", (w, h), 0)
    alpha_px = alpha.load()

    for y in range(h):
        for x in range(w):
            r, g, b, _ = raw_px[x, y]
            max_c = max(r, g, b)
            if max_c <= 12:
                alpha_px[x, y] = 0
            elif max_c <= 32:
                alpha_px[x, y] = int((max_c - 12) / 20.0 * 255)
            else:
                alpha_px[x, y] = 255

    rgba.putalpha(alpha)
    rgba_path = brain_dir / "forest_hex_v2_transparent_2k.png"
    rgba.save(rgba_path, format="PNG")
    print(f"-> Saved transparent RGBA PNG: {rgba_path}")

    # Save dark inspection preview
    preview_path = brain_dir / "forest_hex_v2_preview.jpg"
    preview_bg = Image.new("RGBA", (w, h), (20, 28, 38, 255))
    preview_bg.paste(rgba, (0, 0), rgba)
    preview_bg.convert("RGB").save(preview_path, format="JPEG", quality=92)
    print(f"-> Saved inspection preview: {preview_path}")

    print("\nSUCCESS! V2 Forest Hex generation completed.")


if __name__ == "__main__":
    main()
