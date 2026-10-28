"""Build 2048x2048 (2K, four 1024x1024 cells) symmetrical FLAT-TOP Player, Monster, Boss frames (with 3 top bar slots and 6 unclipped Boss spikes) + Empty Tile from hex_3frames_1tile_raw_1024.png (ZERO API CALLS)."""
from collections import deque
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def flood_fill_mask(raw_img: Image.Image, seeds: list[tuple[int, int]], is_bg_fn, bbox: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    w, h = raw_img.size
    px = raw_img.load()
    visited = Image.new("L", (w, h), 0)
    vpx = visited.load()
    q = deque()

    for sx, sy in seeds:
        if x0 <= sx < x1 and y0 <= sy < y1 and vpx[sx, sy] == 0 and is_bg_fn(px[sx, sy]):
            vpx[sx, sy] = 255
            q.append((sx, sy))

    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if x0 <= nx < x1 and y0 <= ny < y1 and vpx[nx, ny] == 0:
                if is_bg_fn(px[nx, ny]):
                    vpx[nx, ny] = 255
                    q.append((nx, ny))

    return visited


def pad_and_rotate(cell_512: Image.Image, angle_deg: float, padded_size: int = 680) -> Image.Image:
    """Place a 512x512 cell in the center of a spacious `padded_size x padded_size` canvas BEFORE rotating so zero spikes are ever clipped by canvas edges!"""
    canvas = Image.new("RGBA", (padded_size, padded_size), (0, 0, 0, 0))
    off = (padded_size - 512) // 2
    canvas.paste(cell_512, (off, off))
    return canvas.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=False)


def mirror_left_to_right(img: Image.Image, blend_half_w: int = 5) -> Image.Image:
    w, h = img.size
    mid = w // 2
    out = img.copy()
    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    opx = out.load()
    lpx = img.load()
    fpx = flipped.load()

    for y in range(h):
        for x in range(mid - blend_half_w, w):
            if x > mid + blend_half_w:
                opx[x, y] = fpx[x, y]
            else:
                t = (x - (mid - blend_half_w)) / float(2 * blend_half_w)
                r1, g1, b1, a1 = lpx[x, y]
                r2, g2, b2, a2 = fpx[x, y]
                opx[x, y] = (
                    int(r1 * (1 - t) + r2 * t),
                    int(g1 * (1 - t) + g2 * t),
                    int(b1 * (1 - t) + b2 * t),
                    int(a1 * (1 - t) + a2 * t),
                )
    return out


def mirror_right_to_left(img: Image.Image, blend_half_w: int = 5) -> Image.Image:
    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return mirror_left_to_right(flipped, blend_half_w=blend_half_w)


def restore_boss_6_unclipped_spikes(boss_padded: Image.Image) -> Image.Image:
    """In `boss_padded` (rotated by -30 deg on a 680x680 canvas), the Top-Right spike (300 deg / -60 deg)
    and Bottom-Right spike (+60 deg) came from the raw 270-deg (top) and 30-deg (bottom-right) spikes,
    which were 100% inside the original 512x512 cell and completely unclipped!
    Let's copy the unclipped +60 deg (Bottom-Right) spike to all 6 corners (0, 60, 120, 180, 240, 300 deg)
    so every single one of the 6 Boss spikes has its full needle-sharp golden tip!"""
    w, h = boss_padded.size
    cx, cy = w / 2.0, h / 2.0
    out = boss_padded.copy()
    opx = out.load()

    # Source spike is at +60.0 degrees (Bottom-Right corner in PIL coords where +y is down)
    src_ang = 60.0

    # In boss_sym, the 4 diagonal spikes (60, 120, 240, 300 deg) are already 100% unclipped!
    # Only the 2 horizontal spikes (0 deg and 180 deg, k in (0, 3)) had their outermost tip clipped by the raw 512x512 top/bottom border.
    for k in (0, 5):
        target_ang = 60.0 * k
        rot_deg = src_ang - target_ang
        rot_src = boss_padded.rotate(rot_deg, resample=Image.Resampling.BICUBIC, center=(cx, cy))
        spx = rot_src.load()

        for y in range(h):
            for x in range(w):
                dx, dy = x - cx, y - cy
                dist = math.hypot(dx, dy)
                if dist < 208.0:
                    continue
                ang = math.degrees(math.atan2(dy, dx)) % 360.0
                diff = abs(((ang - target_ang + 180.0) % 360.0) - 180.0)
                if diff <= 7.8:
                    t_r = min(1.0, (dist - 208.0) / 8.0)
                    sr, sg, sb, sa = spx[x, y]
                    or_, og, ob, oa = opx[x, y]
                    opx[x, y] = (
                        int(or_ * (1 - t_r) + sr * t_r),
                        int(og * (1 - t_r) + sg * t_r),
                        int(ob * (1 - t_r) + sb * t_r),
                        int(oa * (1 - t_r) + sa * t_r),
                    )
    return mirror_right_to_left(out)


def flat_hex_pts(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    return [
        (cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i)))
        for i in range(6)
    ]


def make_chamfered_bar_slot(cx: float, cy: float, side_idx: int, r_mid: float, half_thickness: float, end_pad: float, tip_len: float) -> list[tuple[float, float]]:
    pts = flat_hex_pts(cx, cy, r_mid)
    p1 = pts[side_idx]
    p2 = pts[(side_idx + 1) % 6]
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    nx, ny = ty, -tx

    tip_start = (p1[0] + tx * end_pad, p1[1] + ty * end_pad)
    tip_end = (p2[0] - tx * end_pad, p2[1] - ty * end_pad)
    s1_x, s1_y = p1[0] + tx * (end_pad + tip_len), p1[1] + ty * (end_pad + tip_len)
    s2_x, s2_y = p2[0] - tx * (end_pad + tip_len), p2[1] - ty * (end_pad + tip_len)

    return [
        tip_start,
        (s1_x + nx * half_thickness, s1_y + ny * half_thickness),
        (s2_x + nx * half_thickness, s2_y + ny * half_thickness),
        tip_end,
        (s2_x - nx * half_thickness, s2_y - ny * half_thickness),
        (s1_x - nx * half_thickness, s1_y - ny * half_thickness),
    ]


def make_partial_slot_fill(cx: float, cy: float, side_idx: int, r_mid: float, half_thickness: float, end_pad: float, tip_len: float, fill_ratio: float):
    pts = flat_hex_pts(cx, cy, r_mid)
    p1 = pts[side_idx]
    p2 = pts[(side_idx + 1) % 6]
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    nx, ny = ty, -tx

    total_len = length - 2.0 * end_pad
    cur_len = max(tip_len * 1.2, total_len * fill_ratio)

    tip_start = (p1[0] + tx * end_pad, p1[1] + ty * end_pad)
    tip_end = (p1[0] + tx * (end_pad + cur_len), p1[1] + ty * (end_pad + cur_len))

    t_in = min(tip_len, cur_len * 0.45)
    s1_x, s1_y = p1[0] + tx * (end_pad + t_in), p1[1] + ty * (end_pad + t_in)
    s2_x, s2_y = p1[0] + tx * (end_pad + cur_len - t_in * 0.5), p1[1] + ty * (end_pad + cur_len - t_in * 0.5)

    return [
        tip_start,
        (s1_x + nx * half_thickness, s1_y + ny * half_thickness),
        (s2_x + nx * half_thickness, s2_y + ny * half_thickness),
        tip_end,
        (s2_x - nx * half_thickness, s2_y - ny * half_thickness),
        (s1_x - nx * half_thickness, s1_y - ny * half_thickness),
    ]


def extract_and_build_2k():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    raw_path = brain_dir / "hex_3frames_1tile_raw_1024.png"
    raw_img = Image.open(raw_path).convert("RGB")
    w, h = raw_img.size
    raw_px = raw_img.load()

    def is_white_bg(rgb):
        r, g, b = rgb
        return r > 220 and g > 220 and b > 218 and (max(r, g, b) - min(r, g, b) < 20)

    ext_seeds = []
    for pos in range(2, 1022, 8):
        ext_seeds.extend([
            (pos, 2), (pos, 510), (pos, 514), (pos, 1021),
            (2, pos), (510, pos), (514, pos), (1021, pos),
        ])
    # Also add seeds inside the small white notch of the Monster top-right claw (before rotation)
    for sy in range(10, 120, 6):
        for sx in range(880, 990, 6):
            if is_white_bg(raw_px[sx, sy]):
                ext_seeds.append((sx, sy))

    ext_bg = flood_fill_mask(raw_img, ext_seeds, is_white_bg, (0, 0, w, h))

    def is_black_hole(rgb):
        r, g, b = rgb
        return r < 28 and g < 28 and b < 28

    hole_centers = [
        ((256, 256), (0, 0, 512, 512)),
        ((768, 256), (512, 0, 1024, 512)),
        ((256, 768), (0, 512, 512, 1024)),
    ]
    int_holes = Image.new("L", (w, h), 0)
    for center_pt, bbox in hole_centers:
        hm = flood_fill_mask(raw_img, [center_pt], is_black_hole, bbox)
        int_holes = Image.composite(Image.new("L", (w, h), 255), int_holes, hm)

    ext_px = ext_bg.load()
    hole_px = int_holes.load()

    fg_mask = Image.new("L", (w, h), 255)
    fpx = fg_mask.load()
    for y in range(h):
        for x in range(w):
            if ext_px[x, y] > 0 or hole_px[x, y] > 0:
                fpx[x, y] = 0

    fg_eroded = fg_mask.filter(ImageFilter.MinFilter(3))
    fg_smooth = fg_eroded.filter(ImageFilter.GaussianBlur(radius=0.8))
    spx = fg_smooth.load()

    rgba_raw = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rpx = rgba_raw.load()
    for y in range(h):
        for x in range(w):
            a = spx[x, y]
            if a < 12:
                continue
            r, g, b = raw_px[x, y]
            if a < 220 and r > 190 and g > 190 and b > 190:
                continue
            rpx[x, y] = (r, g, b, a)

    # Pad each 512x512 cell to 640x640 BEFORE rotating by -30 deg so zero spikes touch the canvas border!
    pad_sz = 620
    player_rot = pad_and_rotate(rgba_raw.crop((0, 0, 512, 512)), -30.0, pad_sz)
    player_flat = mirror_left_to_right(player_rot)

    monster_rot = pad_and_rotate(rgba_raw.crop((512, 0, 1024, 512)), -30.0, pad_sz)
    monster_flat = mirror_left_to_right(monster_rot)

    boss_rot = pad_and_rotate(rgba_raw.crop((0, 512, 512, 1024)), -30.0, pad_sz)
    boss_sym = mirror_right_to_left(boss_rot)
    boss_flat = restore_boss_6_unclipped_spikes(boss_sym)

    tile_rot = pad_and_rotate(rgba_raw.crop((512, 512, 1024, 1024)), -30.0, pad_sz)
    tile_flat = mirror_left_to_right(tile_rot)

    # Scale each 620x620 padded cell cleanly to 1024x1024 for the 2048x2048 (2K) master sheet
    # (and also save a 1024x1024 sheet where each 620x620 cell is scaled to 512x512 with generous margin!)
    sheet_2k = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    cells_padded = [
        (player_flat, (0, 0)),
        (monster_flat, (1, 0)),
        (boss_flat, (0, 1)),
        (tile_flat, (1, 1)),
    ]
    for c_img, (gx, gy) in cells_padded:
        c_1024 = c_img.resize((1024, 1024), Image.Resampling.LANCZOS)
        sheet_2k.paste(c_1024, (gx * 1024, gy * 1024))

    sheet_2k.save(str(brain_dir / "hex_3frames_1tile_rgba_2048.png"))
    sheet_1k = sheet_2k.resize((1024, 1024), Image.Resampling.LANCZOS)
    sheet_1k.save(str(brain_dir / "hex_3frames_1tile_rgba_1024.png"))

    # Now punch the 3 top elongated pointed resource bar slots into the alpha channel
    # by flood-filling the actual dark obsidian interior of each of the 3 top slots (Sides 3, 4, 5)
    # inside the bounding polygon of each slot — so the cutout follows the AI's beveled slot frames with 100% pixel accuracy!
    scale_2k = 1024.0 / pad_sz
    r_slot_mid_2k = 196.0 * scale_2k
    half_th_2k = 11.5 * scale_2k
    end_pad_2k = 28.0 * scale_2k
    tip_len_2k = 12.0 * scale_2k

    bound_mask_2k = Image.new("L", (2048, 2048), 0)
    d_bound = ImageDraw.Draw(bound_mask_2k)
    slot_seeds = []

    for gx, gy in [(0, 0), (1, 0), (0, 1)]:
        cx = gx * 1024 + 512.0
        cy = gy * 1024 + 512.0
        pts_mid = flat_hex_pts(cx, cy, r_slot_mid_2k)
        for s_idx in (3, 4, 5):  # Top-Left, Top-Flat, Top-Right
            poly = make_chamfered_bar_slot(cx, cy, s_idx, r_slot_mid_2k, half_th_2k, end_pad_2k, tip_len_2k)
            d_bound.polygon(poly, fill=255)
            # Sample seed points along the middle 50% of the slot centerline
            p1 = pts_mid[s_idx]
            p2 = pts_mid[(s_idx + 1) % 6]
            for t in (0.3, 0.4, 0.5, 0.6, 0.7):
                sx = int(p1[0] + (p2[0] - p1[0]) * t)
                sy = int(p1[1] + (p2[1] - p1[1]) * t)
                slot_seeds.append((sx, sy))

    b_px = bound_mask_2k.load()
    s2k_px = sheet_2k.load()

    def is_slot_interior(x: int, y: int) -> bool:
        if b_px[x, y] == 0:
            return False
        r, g, b, a = s2k_px[x, y]
        if a < 200:
            return False
        # Dark slate/obsidian interior of the recessed bar slot (stops at bronze/gold/cyan rim!)
        return r < 48 and g < 54 and b < 64

    slot_mask_2k = Image.new("L", (2048, 2048), 0)
    sm_px = slot_mask_2k.load()
    q = deque()
    for sx, sy in slot_seeds:
        if sm_px[sx, sy] == 0 and is_slot_interior(sx, sy):
            sm_px[sx, sy] = 255
            q.append((sx, sy))

    while q:
        cx_i, cy_i = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx_i + dx, cy_i + dy
            if 0 <= nx < 2048 and 0 <= ny < 2048 and sm_px[nx, ny] == 0:
                if is_slot_interior(nx, ny):
                    sm_px[nx, ny] = 255
                    q.append((nx, ny))

    # Dilate by 1px and soften by 1px so the cutout meets the bevel wall cleanly
    slot_mask_2k = slot_mask_2k.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(radius=1.0))
    sm_px = slot_mask_2k.load()

    cutout_2k = sheet_2k.copy()
    cpx = cutout_2k.load()
    for y in range(2048):
        for x in range(2048):
            sv = sm_px[x, y]
            if sv > 0:
                r, g, b, a = cpx[x, y]
                new_a = max(0, int(a * (1.0 - (sv / 255.0) * 0.94)))
                cpx[x, y] = (14, 18, 24, new_a)

    cutout_2k.save(str(brain_dir / "hex_3frames_1tile_slot_cutout_rgba_2048.png"))
    cutout_1k = cutout_2k.resize((1024, 1024), Image.Resampling.LANCZOS)
    cutout_1k.save(str(brain_dir / "hex_3frames_1tile_slot_cutout_rgba_1024.png"))

    # Dark preview of the 2K sheet in native 2048x2048 (and 1024x1024)
    dark_2k = Image.new("RGB", (2048, 2048), (14, 18, 24))
    dark_2k.paste(sheet_2k, (0, 0), sheet_2k)
    dark_2k.save(str(brain_dir / "hex_3frames_1tile_dark_preview_2048.png"))
    dark_2k.resize((1024, 1024), Image.Resampling.LANCZOS).save(str(brain_dir / "hex_3frames_1tile_dark_preview_1024.png"))

    # Render live 3-Frame HP / Stamina / Mana fill demo!
    demo_w, demo_h = 1620, 560
    demo_img = Image.new("RGB", (demo_w, demo_h), (14, 18, 24))

    demo_specs = [
        (0, 0, 270, 0.85, 0.70, 0.60),     # Player Frame
        (1024, 0, 810, 0.65, 0.50, 0.35),  # Monster Frame
        (0, 1024, 1350, 0.92, 0.80, 0.75), # Boss Frame
    ]
    for cx_off, cy_off, paste_cx, hp_val, sta_val, mp_val in demo_specs:
        frame_crop = cutout_2k.crop((cx_off, cy_off, cx_off + 1024, cy_off + 1024))
        under = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        ud = ImageDraw.Draw(under)

        for s_idx in (3, 4, 5):
            bg_hole = make_chamfered_bar_slot(512.0, 512.0, s_idx, r_slot_mid_2k, half_th_2k + 1.5, end_pad_2k - 1.5, tip_len_2k)
            ud.polygon(bg_hole, fill=(16, 20, 28, 255))

        # Side 3 (Top-Left): HP (Ruby Crimson)
        hp_outer = make_partial_slot_fill(512.0, 512.0, 3, r_slot_mid_2k, half_th_2k, end_pad_2k, tip_len_2k, hp_val)
        hp_core = make_partial_slot_fill(512.0, 512.0, 3, r_slot_mid_2k, half_th_2k * 0.48, end_pad_2k + 3.0, tip_len_2k * 0.8, hp_val)
        ud.polygon(hp_outer, fill=(225, 35, 55, 255))
        ud.polygon(hp_core, fill=(255, 135, 145, 255))

        # Side 4 (Top-Flat): Stamina (Emerald / Gold)
        sta_outer = make_partial_slot_fill(512.0, 512.0, 4, r_slot_mid_2k, half_th_2k, end_pad_2k, tip_len_2k, sta_val)
        sta_core = make_partial_slot_fill(512.0, 512.0, 4, r_slot_mid_2k, half_th_2k * 0.48, end_pad_2k + 3.0, tip_len_2k * 0.8, sta_val)
        ud.polygon(sta_outer, fill=(40, 205, 95, 255))
        ud.polygon(sta_core, fill=(155, 255, 185, 255))

        # Side 5 (Top-Right): Mana (Arcane Sapphire Blue)
        mp_outer = make_partial_slot_fill(512.0, 512.0, 5, r_slot_mid_2k, half_th_2k, end_pad_2k, tip_len_2k, mp_val)
        mp_core = make_partial_slot_fill(512.0, 512.0, 5, r_slot_mid_2k, half_th_2k * 0.48, end_pad_2k + 3.0, tip_len_2k * 0.8, mp_val)
        ud.polygon(mp_outer, fill=(30, 135, 255, 255))
        ud.polygon(mp_core, fill=(145, 215, 255, 255))

        under = under.filter(ImageFilter.GaussianBlur(radius=2.0))
        comp = Image.alpha_composite(under, frame_crop).resize((500, 500), Image.Resampling.LANCZOS)
        demo_img.paste(comp, (paste_cx - 250, 280 - 250), comp)

    demo_img.save(str(brain_dir / "hex_3frames_1tile_bars_demo.png"))
    print("SUCCESS! Built unclipped 2048x2048 (2K) and 1024x1024 FLAT-TOP sheets and HP/STA/MP demo.")


if __name__ == "__main__":
    extract_and_build_2k()
