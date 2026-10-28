"""API script to order the Dark Fantasy Arena Atlas using Google GenAI."""
import io
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

PROMPT = """Create a 1:1 pixel-aligned 2D game UI & battlefield sprite sheet in a dark fantasy tactical RPG style, viewed in pure 90-degree orthographic TOP-DOWN projection on a solid pure black (#000000) background.

CRITICAL GEOMETRY & MASK RULE:
- Image 1 is the exact structural lineart blueprint (white lines on black).
- Image 2 is the strict binary silhouette mask (solid white shapes on black).
- Image 3 is the material and color style reference (carved dark slate stone, antique weathered bronze filigree, turquoise gemstone cabochons, faint glowing cyan runes).
- Every single element MUST stay strictly inside its corresponding white silhouette from Image 2 and follow the internal structural lines of Image 1.
- Leave all black gutters between elements completely empty and pure black (#000000).
- DO NOT render any text, letters, numbers, or labels anywhere on the image.

EXACT CONTENTS OF THE 11 BLOCKS:
1. Top-Left (2x2 block): Grand circular duel arena platform (Encounter Circle / Clash Dais). Outer antique bronze filigree rim, recessed ring of glowing cyan runes, and a clean flat dark carved slate stone floor in the center (NO hexes inside the circle).
2. Row 0, Col 2 (1x1 block): Flat-topped hexagonal character frame (horizontal top and bottom edges). Ornate dark bronze frame with 3 recessed empty resource bar grooves along the 3 upper edges (top horizontal edge for HP, top-left edge for Mana/Energy, top-right edge for Stamina), a small circular status socket on the bottom-right edge, and a dark empty hexagonal interior window.
3. Row 0, Col 3 (1x1 block): Standalone flat-topped hexagonal dark carved slate stone floor tile with subtle beveled stone border.
4. Row 1, Col 2 (1x1 block): Circular combat control wheel (astrolabe style) with a central circular socket and an outer ring divided into 9 radial token sectors with bronze dividers and small turquoise rivets.
5. Rows 1..2, Col 3 (1x2 tall vertical block): Tall vertical monster stats board. Forged dark bronze outer frame with turquoise corner rivets, clean dark slate interior divided by thin horizontal bronze separator bars into 4 clean empty sections (header and 3 stat sections, NO text inside).
6. Row 2, Cols 0..1 (2x1 horizontal block): Rectangular ability bar frame housing 8 square skill sockets arranged in 2 rows of 4, crafted from dark stone and bronze rims.
7. Row 2, Col 2 (1x1 block): 3 horizontal rectangular slide-out backing plates stacked vertically, crafted from dark bronze and slate with a right-side overlap tab that tucks under the control wheel.
8. Row 3, Col 0 (1x1 block): Circular attack medallion insert featuring forged crossed swords in the center.
9. Row 3, Col 1 (1x1 block): Circular wait/timer medallion insert featuring an antique bronze and glass hourglass in the center.
10. Row 3, Col 2 (1x1 block): Single large standalone square skill slot frame in dark bronze and carved stone.
11. Row 3, Col 3 (1x1 block): 4 small circular enemy status token badges arranged in a 2x2 sub-grid: (top-left) crimson crossed blades, (top-right) golden hourglass timer, (bottom-left) three glowing amber waiting dots, (bottom-right) crimson exclamation mark danger symbol.
"""


def order_atlas():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    root_dir = Path(__file__).resolve().parents[2]
    ref_line_path = brain_dir / "layout_reference_black_2048.png"
    ref_mask_path = brain_dir / "solid_white_mask_2048.png"
    style_ref_path = root_dir / "game_ui_lab" / "static" / "assets" / "battle-stone-reference-v1.png"

    raw_output_path = brain_dir / "api_generated_dark_fantasy_atlas_raw.png"
    clamped_output_path = brain_dir / "api_generated_dark_fantasy_atlas.png"

    if not ref_line_path.exists() or not ref_mask_path.exists():
        print("ERROR: Reference or mask image missing.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    ref_line_pil = Image.open(ref_line_path)
    ref_mask_pil = Image.open(ref_mask_path)
    contents = [PROMPT, ref_line_pil, ref_mask_pil]
    if style_ref_path.exists():
        contents.append(Image.open(style_ref_path))

    models_to_try = [
        "gemini-3-pro-image-preview",
        "gemini-3.1-flash-image-preview",
        "gemini-2.5-flash-image",
    ]

    for model_name in models_to_try:
        print(f"Sending generation request to {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img_data = part.inline_data.data
                    out_img = Image.open(io.BytesIO(img_data)).convert("RGB")
                    out_img.save(str(raw_output_path))
                    print(f"SUCCESS with {model_name}! Raw image saved to: {raw_output_path} (size={out_img.size})")

                    # Also create a pixel-aligned 2048x2048 version clamped by the solid white mask
                    out_2k = out_img.resize((2048, 2048), Image.Resampling.LANCZOS)
                    mask_l = ref_mask_pil.convert("L")
                    black_bg = Image.new("RGB", (2048, 2048), (0, 0, 0))
                    clamped = Image.composite(out_2k, black_bg, mask_l)
                    clamped.save(str(clamped_output_path))
                    print(f"Saved mask-clamped 2048x2048 atlas to: {clamped_output_path}")
                    return
            print(f"No inline_data returned from {model_name}")
        except Exception as e:
            print(f"Model {model_name} failed: {e}")

    sys.exit(1)


if __name__ == "__main__":
    order_atlas()
