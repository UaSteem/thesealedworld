"""Order the 2048x2048 (2K) 2x2 Target / Monster Inspector UI Sheet via Gemini API:
- [1,1] Tall Target Inspector Frame (480x940 px) with thin double-beveled antique gold & dark bronze border and 4 horizontal section dividers
- [1,2] Clean Tall Target Inspector Backing Plate (480x940 px) with thin double-beveled antique gold & dark bronze border and smooth undivided obsidian interior
- [2,1] Internal UI Elements:
  * Top: Collapsible Section Header Button Frame (840x96 px, for '› Атака / › Защита / › Прочее')
  * Middle: Recessed Resource Bar Track Frame (840x52 px, for HP / Energy / Stamina bars)
  * Bottom: 3 Circular Monster Intent Medallion Badges (r=115 px: Attack Sword, Wait Hourglass, Defense Shield)
- [2,2] Cliff-Hugging Angled Tall Inspector Frame (560x940 px, with 60-degree chamfered bottom-right slope matching the broken hex cliff)
"""
import io
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw


PROMPT_TARGET_INSPECTOR_2K = """Create a high-detail 2048x2048 (2K) 2D game UI sprite sheet arranged in a strict 2x2 grid (four 1024x1024 cells) on a solid pure black (#000000) background, in pure 90-degree orthographic TOP-DOWN view.

CRITICAL GEOMETRY, THIN-BEVEL & UNIFIED STYLE RULES:
- Image 1 is the exact structural blueprint (warm bronze lines on black).
- Image 2 is the strict binary silhouette mask (white shapes on pure black #000000 background). Every UI element MUST stay strictly inside the white silhouette shapes of Image 2! All black areas of Image 2 MUST remain solid pure black (#000000) — NEVER use a white background!
- Image 3 is the exact in-game material and border-thickness reference: notice the THIN, SLEEK, CRISP double-beveled Antique Gold and Dark Bronze rims and smooth matte dark obsidian-slate (#141820) stone interiors.
- THIN REFINED BORDERS ONLY: All panels, bars, and medallions on this sheet MUST use those exact THIN, sleek, jewelry-grade double-beveled antique gold and dark bronze rims (NO thick, bloated frames, NO giant corner shields, and ZERO cyan crystals or gems!).
- ZERO TEXT / ZERO LETTERS anywhere on the sheet.

EXACT CONTENTS OF THE 4 CELLS (1024x1024 each, strictly inside the white shapes of Image 2):

1. Top-Left [1,1] (x: 0..1024, y: 0..1024) — TALL TARGET INSPECTOR PANEL WITH SECTION DIVIDERS (480x940 px):
   - A tall vertical rectangular matte dark obsidian-slate (#141820) stone panel framed by a THIN, sleek, chamfered double-beveled antique gold and dark bronze border.
   - Across the interior, at the 4 horizontal line positions marked in Image 1 (y=210, 420, 580, 740), draw thin, crisp double-beveled antique gold and dark bronze horizontal divider bars that cleanly partition the tall panel into 5 compartments (Header, Resources, Combat Stats, Active Effects, and Collapsible Tabs). All 5 compartments have smooth, empty matte dark obsidian-slate (#141820) interiors with no text.

2. Top-Right [1,2] (x: 1024..2048, y: 0..1024) — CLEAN TALL TARGET INSPECTOR BACKING PLATE (480x940 px, NO DIVIDERS):
   - The exact same tall vertical rectangular matte dark obsidian-slate (#141820) stone panel framed by the exact THIN, sleek, chamfered double-beveled antique gold and dark bronze border, with a completely open, smooth, undivided matte dark obsidian-slate (#141820) interior.

3. Bottom-Left [2,1] (x: 0..1024, y: 1024..2048) — COLLAPSIBLE TAB BAR + RESOURCE BAR TRACK + 3 MONSTER INTENT MEDALLIONS:
   - Top horizontal bar (840x96 px): a sleek elongated collapsible section button frame with a thin chamfered double-beveled antique gold and dark bronze rim and smooth matte dark obsidian-slate (#141820) interior.
   - Middle narrow horizontal bar (840x52 px): a thin, deeply recessed dark obsidian bar trough/track framed by a fine double-beveled antique gold and dark bronze lip (used as the empty frame for Health / Energy / Stamina progress bars).
   - Bottom row of 3 circular Monster Intent Medallions (radius 115 px each), each framed by a thin double-beveled antique gold and dark bronze ring over a recessed dark obsidian disc:
     * Left medallion: features a crisp, low-relief sculpted Antique Gold CROSSED SWORDS emblem in the center (Attack intent).
     * Middle medallion: features a crisp, low-relief sculpted Antique Gold HOURGLASS emblem in the center (Wait / Thinking intent).
     * Right medallion: features a crisp, low-relief sculpted Antique Gold HERALDIC SHIELD emblem in the center (Defense / Guard intent).

4. Bottom-Right [2,2] (x: 1024..2048, y: 1024..2048) — CLIFF-HUGGING ANGLED TALL INSPECTOR PANEL (560x940 px):
   - A tall vertical matte dark obsidian-slate (#141820) stone panel whose bottom-right corner is sliced at a long 60-degree diagonal bevel (strictly following the white silhouette of Image 2), framed all around by the exact THIN, sleek double-beveled antique gold and dark bronze border, with a smooth, empty matte dark obsidian-slate (#141820) interior.
"""


def make_tinted_lineart(brain_dir: Path) -> Image.Image:
    line_img = Image.open(brain_dir / "target_inspector_lineart_2048.png").convert("RGB")
    w, h = line_img.size
    d = ImageDraw.Draw(line_img)

    # Add subtle icon guide sketches inside the 3 medallions in [2,1] (y=1720, x=232, 512, 792)
    # 1. Crossed swords at (232, 1720)
    d.line([(232 - 42, 1720 + 42), (232 + 42, 1720 - 42)], fill=(195, 195, 195), width=3)
    d.line([(232 - 42, 1720 - 42), (232 + 42, 1720 + 42)], fill=(195, 195, 195), width=3)
    # 2. Hourglass at (512, 1720)
    d.polygon([(512 - 34, 1720 - 44), (512 + 34, 1720 - 44), (512 - 34, 1720 + 44), (512 + 34, 1720 + 44)], outline=(195, 195, 195), width=3)
    # 3. Shield at (792, 1720)
    d.polygon([(792, 1720 - 46), (792 + 38, 1720 - 28), (792 + 30, 1720 + 18), (792, 1720 + 48), (792 - 30, 1720 + 18), (792 - 38, 1720 - 28)], outline=(195, 195, 195), width=3)

    tinted = Image.new("RGB", (w, h), (0, 0, 0))
    lpx = line_img.load()
    tpx = tinted.load()
    for y in range(h):
        for x in range(w):
            v = lpx[x, y][0]
            if v > 0:
                tpx[x, y] = (int(v * 0.72), int(v * 0.58), int(v * 0.35))
    return tinted


def postprocess_target_inspector_sheet(raw_img: Image.Image, brain_dir: Path):
    import collections

    w, h = raw_img.size
    rpx = raw_img.load()

    def is_white_bg(r: int, g: int, b: int) -> bool:
        lum = (r + g + b) / 3.0
        warmth = max(r, g, b) - min(r, g, b)
        return lum > 225 and warmth < 24

    visited = bytearray(w * h)
    q = collections.deque()

    # Seed from image borders and grid center lines
    for x in range(w):
        for y in (0, 1, 1024, h - 2, h - 1):
            idx = y * w + x
            if not visited[idx] and is_white_bg(*rpx[x, y]):
                visited[idx] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, 1, 1024, w - 2, w - 1):
            idx = y * w + x
            if not visited[idx] and is_white_bg(*rpx[x, y]):
                visited[idx] = 1
                q.append((x, y))

    while q:
        cx, cy = q.popleft()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                nidx = ny * w + nx
                if not visited[nidx] and is_white_bg(*rpx[nx, ny]):
                    visited[nidx] = 1
                    q.append((nx, ny))

    rgba_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out_px = rgba_img.load()

    for y in range(h):
        row_off = y * w
        for x in range(w):
            if visited[row_off + x]:
                out_px[x, y] = (0, 0, 0, 0)
                continue
            r, g, b = rpx[x, y]
            # Check if within 2px of flood-filled background for smooth anti-aliased edge
            near_bg = False
            for d in (1, 2):
                if (
                    (x >= d and visited[row_off + x - d])
                    or (x + d < w and visited[row_off + x + d])
                    or (y >= d and visited[(y - d) * w + x])
                    or (y + d < h and visited[(y + d) * w + x])
                ):
                    near_bg = True
                    break
            if near_bg:
                lum = (r + g + b) / 3.0
                warmth = r - b
                if lum > 195 and warmth < 28:
                    out_px[x, y] = (0, 0, 0, 0)
                elif lum > 145 and warmth < 24:
                    out_px[x, y] = (int(r * 0.45), int(g * 0.40), int(b * 0.32), 170)
                else:
                    out_px[x, y] = (r, g, b, 235)
            else:
                out_px[x, y] = (r, g, b, 255)

    rgba_path = brain_dir / "target_inspector_sheet_2x2_rgba_2048.png"
    rgba_img.save(str(rgba_path))

    dark_bg = Image.new("RGBA", (w, h), (20, 24, 32, 255))
    dark_prev = Image.alpha_composite(dark_bg, rgba_img).convert("RGB")
    dark_prev.save(str(brain_dir / "target_inspector_sheet_2x2_dark_preview_2048.png"))
    print(f"Saved Target Inspector 2K RGBA sheet and dark preview to: {rgba_path}")


def main():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "target_inspector_sheet_2x2_raw_2048.png"

    if raw_path.exists() and "--re-order" not in sys.argv:
        print(f"Using existing raw 2K image: {raw_path}")
        raw_img = Image.open(raw_path).convert("RGB")
        postprocess_target_inspector_sheet(raw_img, brain_dir)
        return

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    tinted_line = make_tinted_lineart(brain_dir)
    mask_rgb = Image.open(brain_dir / "target_inspector_mask_2048.png").convert("RGB")
    style_scene = Image.open(brain_dir / "control_zone_v2_sheet_2x2_dark_preview_2048.png").convert("RGB")

    client = genai.Client(api_key=api_key)
    print("Ordering 2048x2048 (2K) 2x2 Target Inspector Sheet via gemini-3-pro-image-preview...")
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[tinted_line, mask_rgb, style_scene, PROMPT_TARGET_INSPECTOR_2K],
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

    print(f"Received Target Inspector 2K image of size: {raw_img.size}")
    if raw_img.size != (2048, 2048):
        raw_img = raw_img.resize((2048, 2048), Image.Resampling.LANCZOS)

    raw_img.save(str(raw_path))
    postprocess_target_inspector_sheet(raw_img, brain_dir)


if __name__ == "__main__":
    main()
