"""Create a 2048x2048 (2x2 grid) blueprint + binary mask for 4 Fractured / Broken Perimeter Hex Tiles:
- [1,1] 2/3 Hex (3 contiguous intact framed edges: e5, e0, e1 + short broken stubs on e4, e2) -> for 3-neighbor pockets (cells 25, 45, 4, 32)
- [1,2] 1/2 Hex (2 contiguous intact framed edges: e0, e1 + short broken stubs on e5, e2) -> for 2-neighbor steps (cells 24, 5, 7, 42, 58, 59)
- [2,1] 1/3 - 1/4 Hex (1 intact framed edge: e0 + short broken stubs on e5, e1) -> for 1-neighbor outer ledges (cells 14, 34, 22, 33)
- [2,2] 3/4 Cracked Ruin Hex (3 intact framed edges: e5, e0, e1 + longer broken shoulders on e4, e2 + deep crack) -> for heavy ruin corners

All 4 share the exact r=450 flat-top hex geometry centered at (512, 512) of each 1024x1024 cell so they
snap 1:1 to intact battlefield hexes and can be rotated in 60-degree increments (0, 60, 120, 180, 240, 300).
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def hex_vertices(cx: float, cy: float, r: float):
    """Flat-top hexagon vertices at 0, 60, 120, 180, 240, 300 degrees:
    v0=(right, 0°), v1=(bottom-right, 60°), v2=(bottom-left, 120°),
    v3=(left, 180°), v4=(top-left, 240°), v5=(top-right, 300°).
    Edges:
      e0: v0->v1 (bottom-right)
      e1: v1->v2 (bottom flat)
      e2: v2->v3 (bottom-left)
      e3: v3->v4 (top-left)
      e4: v4->v5 (top flat)
      e5: v5->v0 (top-right)
    """
    return [
        (cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i)))
        for i in range(6)
    ]


def lerp_pt(p1, p2, t: float):
    return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


def build_edge_chain(verts, edge_indices, start_t: float, end_t: float):
    """Build polyline along contiguous hex edges, trimming the first edge by start_t and last by end_t."""
    pts = []
    for idx_pos, e_idx in enumerate(edge_indices):
        v_start = verts[e_idx]
        v_end = verts[(e_idx + 1) % 6]
        p1 = lerp_pt(v_start, v_end, start_t) if idx_pos == 0 else v_start
        p2 = lerp_pt(v_start, v_end, end_t) if idx_pos == len(edge_indices) - 1 else v_end
        if not pts:
            pts.append(p1)
        pts.append(p2)
    return pts


def build_fractured_hex(cx: float, cy: float, r_out: float, edge_indices, start_t: float, end_t: float, fracture_rel_pts):
    """Build full closed polygon and fracture cliff polyline.
    fracture_rel_pts are (dx_norm, dy_norm) relative to (cx, cy) scaled by r_out, going from the
    END of the intact edge chain back to the START of the intact edge chain.
    """
    vo = hex_vertices(cx, cy, r_out)
    rim_outer = build_edge_chain(vo, edge_indices, start_t, end_t)
    fracture_pts = [rim_outer[-1]]
    for rx, ry in fracture_rel_pts:
        fracture_pts.append((cx + rx * r_out, cy + ry * r_out))
    fracture_pts.append(rim_outer[0])
    full_poly = rim_outer + fracture_pts[1:-1]
    return full_poly, rim_outer, fracture_pts


def draw_variant_on_blueprint(dm, dl, cx, cy, r_out, r_mid, r_in, edge_indices, start_t, end_t, fracture_rel_pts, crack_rel_lines=None):
    full_poly, _, fracture_pts = build_fractured_hex(cx, cy, r_out, edge_indices, start_t, end_t, fracture_rel_pts)
    dm.polygon(full_poly, fill=255)

    # Draw intact double-bevel rim ONLY along the intact edge chain
    vo = hex_vertices(cx, cy, r_out)
    vm = hex_vertices(cx, cy, r_mid)
    vi = hex_vertices(cx, cy, r_in)
    chain_o = build_edge_chain(vo, edge_indices, start_t, end_t)
    chain_m = build_edge_chain(vm, edge_indices, start_t, end_t)
    chain_i = build_edge_chain(vi, edge_indices, start_t, end_t)

    dl.line(chain_o, fill=(255, 255, 255), width=4)
    dl.line(chain_m, fill=(255, 255, 255), width=2)
    dl.line(chain_i, fill=(255, 255, 255), width=3)
    # Broken cross-section caps at the two ends of the gold/bronze frame
    dl.line([chain_o[0], chain_i[0]], fill=(255, 255, 255), width=3)
    dl.line([chain_o[-1], chain_i[-1]], fill=(255, 255, 255), width=3)

    # Draw jagged stone fracture cliff edge + stepped inner stone ledge
    dl.line(fracture_pts, fill=(255, 255, 255), width=4)
    step_pts = [chain_i[-1]]
    for px, py in fracture_pts[1:-1]:
        # Pull slightly toward the intact side (right/bottom-right) to represent the beveled stone thickness
        step_pts.append((px + 22, py + 12))
    step_pts.append(chain_i[0])
    dl.line(step_pts, fill=(185, 185, 185), width=2)

    # Optional internal surface cracks extending from the fracture
    if crack_rel_lines:
        for c_line in crack_rel_lines:
            c_pts = [(cx + rx * r_out, cy + ry * r_out) for rx, ry in c_line]
            dl.line(c_pts, fill=(170, 170, 170), width=2)


def build_broken_hexes_blueprint():
    brain_dir = Path(r"C:\Users\prime\.gemini\antigravity\brain\85a5ed96-ae61-4c9e-872a-c5d7be1c07d9")
    sz = 2048
    mask_img = Image.new("L", (sz, sz), 0)
    line_img = Image.new("RGB", (sz, sz), (0, 0, 0))
    dm = ImageDraw.Draw(mask_img)
    dl = ImageDraw.Draw(line_img)

    r_out = 450.0
    r_mid = 438.0
    r_in = 422.0

    # =========================================================================
    # UNIVERSAL CLIFF-JUNCTION RULE:
    # Every broken stub edge starts at start_t = 0.55 (which is 45% from the arena vertex)
    # and ends at end_t = 0.45 (which is ALSO 45% from the arena vertex)!
    # That guarantees any two adjacent broken hexes meet at the EXACT same point (45%)
    # on their shared edge, forming a continuous unbroken cliff around the arena!
    # =========================================================================

    # VARIANT 1 [1,1] (center 512, 512): 2/3 HEX (3 full intact edges: e5, e0, e1 + 45% stubs on e4, e2)
    v1_edges = [4, 5, 0, 1, 2]
    v1_st, v1_et = 0.55, 0.45
    v1_fracture = [
        (-0.56, +0.34),
        (-0.62, +0.16),
        (-0.38, +0.02),
        (-0.48, -0.18),
        (-0.26, -0.34),
        (-0.34, -0.56),
        (-0.10, -0.70),
    ]
    v1_cracks = [
        [(-0.38, +0.02), (-0.12, +0.10), (+0.05, +0.22)],
        [(-0.26, -0.34), (-0.02, -0.26)],
    ]
    draw_variant_on_blueprint(dm, dl, 512.0, 512.0, r_out, r_mid, r_in, v1_edges, v1_st, v1_et, v1_fracture, v1_cracks)

    # =========================================================================
    # VARIANT 2 [1,2] (center 1536, 512): 1/2 HEX (2 full intact edges: e0, e1 + 45% stubs on e5, e2)
    # Ideal for 2-neighbor steps like cell 24 (touches 36 on e0 and 35 on e1)!
    # =========================================================================
    v2_edges = [5, 0, 1, 2]
    v2_st, v2_et = 0.55, 0.45
    v2_fracture = [
        (-0.52, +0.36),
        (-0.40, +0.16),
        (-0.14, +0.08),
        (-0.08, -0.10),
        (+0.18, -0.16),
        (+0.30, -0.34),
        (+0.56, -0.32),
    ]
    v2_cracks = [
        [(-0.08, -0.10), (+0.18, +0.12), (+0.32, +0.28)],
    ]
    draw_variant_on_blueprint(dm, dl, 1536.0, 512.0, r_out, r_mid, r_in, v2_edges, v2_st, v2_et, v2_fracture, v2_cracks)

    # =========================================================================
    # VARIANT 3 [2,1] (center 512, 1536): 1/3 - 1/4 HEX (1 full intact edge: e0 + 45% stubs on e5, e1)
    # Ideal for 1-neighbor ledges like cells 14 and 34 (touching e0 bottom-right)!
    # =========================================================================
    v3_edges = [5, 0, 1]
    v3_st, v3_et = 0.55, 0.45
    v3_fracture = [
        (+0.02, +0.66),
        (+0.20, +0.46),
        (+0.14, +0.24),
        (+0.34, +0.08),
        (+0.30, -0.12),
        (+0.54, -0.24),
    ]
    v3_cracks = [
        [(+0.34, +0.08), (+0.58, +0.22)],
    ]
    draw_variant_on_blueprint(dm, dl, 512.0, 1536.0, r_out, r_mid, r_in, v3_edges, v3_st, v3_et, v3_fracture, v3_cracks)

    # =========================================================================
    # VARIANT 4 [2,2] (center 1536, 1536): FULL INTACT HEX TILE (all 6 edges framed!)
    # Having the full intact hex on the exact same 2K generation guarantees 100% identical
    # obsidian stone texture, bevel profile, and gold/bronze shading across intact & broken tiles!
    # =========================================================================
    vo_22 = hex_vertices(1536.0, 1536.0, r_out)
    vm_22 = hex_vertices(1536.0, 1536.0, r_mid)
    vi_22 = hex_vertices(1536.0, 1536.0, r_in)
    dm.polygon(vo_22, fill=255)
    dl.polygon(vo_22, outline=(255, 255, 255), width=4)
    dl.polygon(vm_22, outline=(255, 255, 255), width=2)
    dl.polygon(vi_22, outline=(255, 255, 255), width=3)

    # Save annotated preview
    prev_img = Image.new("RGB", (sz, sz), (14, 18, 24))
    prev_img = Image.composite(Image.new("RGB", (sz, sz), (32, 42, 56)), prev_img, mask_img)
    prev_img = Image.composite(Image.new("RGB", (sz, sz), (95, 225, 255)), prev_img, line_img.convert("L"))
    dp = ImageDraw.Draw(prev_img)
    for g in [0, 1024, 2047]:
        dp.line([(g, 0), (g, sz)], fill=(65, 85, 110), width=3)
        dp.line([(0, g), (sz, g)], fill=(65, 85, 110), width=3)

    # Dashed full-hex reference ghost on preview so user sees exact 1:1 alignment with full hexes
    for cx, cy in [(512, 512), (1536, 512), (512, 1536), (1536, 1536)]:
        fv = hex_vertices(cx, cy, r_out)
        for i in range(6):
            p1, p2 = fv[i], fv[(i + 1) % 6]
            for s in range(0, 10, 2):
                dp.line([lerp_pt(p1, p2, s / 10.0), lerp_pt(p1, p2, (s + 1) / 10.0)], fill=(120, 100, 65), width=2)

    try:
        font_h = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 21)
    except Exception:
        font_h = ImageFont.load_default()

    labels = [
        (24, 24, "[1,1] 2/3 ГЕКСА С ОБЛОМАННЫМ КРАЕМ (3 целые грани + усы 45% -> ячейки 25, 45, 4, 32)"),
        (1048, 24, "[1,2] ПОЛОВИНКА 1/2 ГЕКСА С РАСКОЛОМ (2 целые грани + усы 45% -> ячейки 24, 5, 7, 42)"),
        (24, 1048, "[2,1] ЧЕТВЕРТИНКА / 1/3 ГЕКСА (1 целая грань + усы 45% -> ячейки 14, 34, 22, 33)"),
        (1048, 1048, "[2,2] ЦЕЛЬНЫЙ ГЕКС ПОЛЯ (все 6 граней в тонкой рамке — единый стиль камня и фаски!)"),
    ]
    for lx, ly, ltxt in labels:
        dp.text((lx, ly), ltxt, fill=(255, 215, 90), font=font_h)

    mask_img.save(str(brain_dir / "broken_hexes_mask_2048.png"))
    line_img.save(str(brain_dir / "broken_hexes_lineart_2048.png"))
    prev_img.save(str(brain_dir / "broken_hexes_preview_2048.png"))

    # =========================================================================
    # In-scene mockup on media_1792963285328_53384eb7.png (close-up of cells 14, 25, 24, 34, 45)
    # =========================================================================
    crop_path = brain_dir / ".user_uploaded" / "media_1792963285328_53384eb7.png"
    if crop_path.exists():
        scene = Image.open(crop_path).convert("RGBA")
        sw, sh = scene.size
        overlay = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        do = ImageDraw.Draw(overlay)

        # In media_1792963285328_53384eb7.png (587x669):
        # Col 0 (34, 45): x = 92; Col 1 (13, 24, 35, 46): x = 230; Col 2 (14, 25, 36, 47): x = 368
        # Vertical step = 158.5 px, half-step = 79.25 px, r_s = 88.5 px
        r_s = 88.5
        placements = [
            (368.0, 54.0,  v3_edges, v3_st, v3_et, v3_fracture, v3_cracks),  # Cell 14: 1/3 hex touching 15
            (368.0, 212.5, v1_edges, v1_st, v1_et, v1_fracture, v1_cracks),  # Cell 25: 2/3 hex touching 15, 26, 36
            (230.0, 291.8, v2_edges, v2_st, v2_et, v2_fracture, v2_cracks),  # Cell 24: 1/2 hex touching 36, 35
            (92.0,  371.0, v3_edges, v3_st, v3_et, v3_fracture, v3_cracks),  # Cell 34: 1/3 hex touching 35
            (92.0,  529.5, v1_edges, v1_st, v1_et, v1_fracture, v1_cracks),  # Cell 45: 2/3 hex touching 35, 46, 56
        ]
        for bcx, bcy, edges, st, et, frac_rel, cracks_rel in placements:
            poly_s, _, frac_pts_s = build_fractured_hex(bcx, bcy, r_s, edges, st, et, frac_rel)
            do.polygon(poly_s, fill=(24, 29, 38, 235))
            # Inner dark obsidian surface
            vo = hex_vertices(bcx, bcy, r_s)
            vm = hex_vertices(bcx, bcy, r_s - 2.5)
            vi = hex_vertices(bcx, bcy, r_s - 5.5)
            ch_o = build_edge_chain(vo, edges, st, et)
            ch_m = build_edge_chain(vm, edges, st, et)
            ch_i = build_edge_chain(vi, edges, st, et)
            # Jagged cliff edge
            step_s = [ch_i[-1]] + [(px + 4, py + 2) for px, py in frac_pts_s[1:-1]] + [ch_i[0]]
            do.line(frac_pts_s, fill=(10, 12, 16, 255), width=3)
            do.line(step_s, fill=(62, 72, 88, 220), width=2)
            # Cracks
            for cl in cracks_rel:
                c_pts = [(bcx + rx * r_s, bcy + ry * r_s) for rx, ry in cl]
                do.line(c_pts, fill=(12, 15, 20, 220), width=1)
            # Intact bronze/gold double-bevel rim ONLY on the arena-facing edges
            do.line(ch_o, fill=(135, 102, 52, 255), width=2)
            do.line(ch_m, fill=(225, 185, 96, 255), width=2)
            do.line(ch_i, fill=(150, 115, 58, 255), width=1)
            do.line([ch_o[0], ch_i[0]], fill=(195, 155, 78, 255), width=2)
            do.line([ch_o[-1], ch_i[-1]], fill=(195, 155, 78, 255), width=2)

        out_scene = Image.alpha_composite(scene, overlay).convert("RGB")
        out_scene.save(str(brain_dir / "broken_hexes_in_scene_preview.png"))

    print("Saved updated broken_hexes_preview_2048.png and broken_hexes_in_scene_preview.png")


if __name__ == "__main__":
    build_broken_hexes_blueprint()
