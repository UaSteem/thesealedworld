import os
from PIL import Image

def build_bw_references():
    src_path = r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9\.user_uploaded\media_1792937584503_e33e5eec.png"
    brain_dir = r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9"
    im = Image.open(src_path).convert("RGB")
    w, h = im.size

    # 1. Output canvas
    bw_black_bg = Image.new("RGB", (w, h), (0, 0, 0))
    bw_white_bg = Image.new("RGB", (w, h), (255, 255, 255))

    out_b_pix = bw_black_bg.load()
    out_w_pix = bw_white_bg.load()
    in_pix = im.load()

    # Text removal bounding boxes (x1, y1, x2, y2)
    text_regions = [
        # Top header
        (0, 0, w, 85),
        # Footer
        (0, 935, w, h),
        # Box 01 title
        (25, 85, 245, 140),
        # Box 02 title
        (245, 85, 465, 140),
        # Box 03 title
        (25, 300, 245, 350),
        # Box 04 title
        (245, 300, 465, 350),
        # Box 05 title
        (480, 85, 915, 140),
        # Box 05 center text: 'АТАКА / ЧАСЫ'
        (630, 290, 840, 345),
        # Box 06 title
        (25, 515, 465, 570),
        # Box 07 title
        (480, 515, 915, 570),
        # Box 08 title
        (25, 730, 245, 780),
        # Box 09 title
        (245, 730, 465, 780),
        # Box 10 title
        (480, 730, 700, 780),
        # Box 11 title
        (710, 730, 915, 780),
    ]

    def in_text_region(x, y):
        for x1, y1, x2, y2 in text_regions:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        return False

    for y in range(h):
        for x in range(w):
            if in_text_region(x, y):
                continue
            r, g, b = in_pix[x, y]

            # 1. Cyan geometry lines (elements)
            is_cyan = (g > 140 and b > 140 and (g - r) > 30 and (b - r) > 30)

            # 2. Gold geometry lines (elements)
            is_gold = (r > 160 and g > 130 and (r - b) > 30)

            # 3. Box container frame borders
            is_box_border = (abs(r - 38) < 12 and abs(g - 61) < 14 and abs(b - 72) < 16)

            if is_cyan or is_gold or is_box_border:
                out_b_pix[x, y] = (255, 255, 255)
                out_w_pix[x, y] = (0, 0, 0)

    # Save native resolution versions
    b_path = os.path.join(brain_dir, "bw_controlnet_reference_black.png")
    w_path = os.path.join(brain_dir, "bw_controlnet_reference_white.png")
    bw_black_bg.save(b_path)
    bw_white_bg.save(w_path)
    print(f"Saved native reference: {b_path}")
    print(f"Saved native reference: {w_path}")

    # Also create a square padded 1024x1024 standard version
    # Pad to center on 1024x1024
    sq_black = Image.new("RGB", (1024, 1024), (0, 0, 0))
    sq_white = Image.new("RGB", (1024, 1024), (255, 255, 255))
    offset_x = (1024 - w) // 2
    offset_y = (1024 - h) // 2
    sq_black.paste(bw_black_bg, (offset_x, offset_y))
    sq_white.paste(bw_white_bg, (offset_x, offset_y))

    sq_b_path = os.path.join(brain_dir, "bw_controlnet_1024_black.png")
    sq_w_path = os.path.join(brain_dir, "bw_controlnet_1024_white.png")
    sq_black.save(sq_b_path)
    sq_white.save(sq_w_path)
    print(f"Saved 1024x1024 square reference: {sq_b_path}")
    print(f"Saved 1024x1024 square reference: {sq_w_path}")

    # Also generate a crisp 4096x4096 4K upscale of the reference!
    k4_black = sq_black.resize((4096, 4096), Image.Resampling.NEAREST)
    k4_white = sq_white.resize((4096, 4096), Image.Resampling.NEAREST)
    k4_b_path = os.path.join(brain_dir, "bw_controlnet_4k_black.png")
    k4_w_path = os.path.join(brain_dir, "bw_controlnet_4k_white.png")
    k4_black.save(k4_b_path)
    k4_white.save(k4_w_path)
    print(f"Saved 4K reference: {k4_b_path}")
    print(f"Saved 4K reference: {k4_w_path}")

if __name__ == "__main__":
    build_bw_references()
