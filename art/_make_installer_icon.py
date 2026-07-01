#!/usr/bin/env python3
"""Composite a gold 'setup' gear badge onto the Star Alliance shield
to produce art/logo-installer.png — the Finder icon for the installer .command.

Reads only:  art/logo-transparent.png (the source shield)
Writes only: art/logo-installer.png
"""
from PIL import Image, ImageDraw
import math

SRC = "/Users/attaselim/Documents/Claude/Projects/star-alliance/art/logo-transparent.png"
DST = "/Users/attaselim/Documents/Claude/Projects/star-alliance/art/logo-installer.png"
SIZE = 1024

# Brand colors (matching the existing gold shield)
GOLD_LIGHT = (212, 175, 55, 255)   # #D4AF37
GOLD_DARK  = (139, 105, 20, 255)  # #8B6914
GOLD_HI    = (245, 215, 110, 255) # highlight (lighter gold)
NAVY       = (11, 31, 58, 255)    # #0B1F3A
NAVY_DEEP  = (6,  18, 35, 255)
RING_LIGHT = (255, 230, 160, 220) # soft outer highlight on the navy ring


def draw_radial_gradient(size, center, radius, inner, outer):
    """Return an RGBA image filled with a radial gradient inner->outer."""
    w, h = size
    cx, cy = center
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    rmax = max(1, radius)
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            d = math.sqrt(dx * dx + dy * dy)
            if d > rmax:
                continue
            t = min(1.0, max(0.0, d / rmax))
            # bias the gradient toward the inner color
            t = t ** 1.6
            r = int(inner[0] * (1 - t) + outer[0] * t)
            g = int(inner[1] * (1 - t) + outer[1] * t)
            b = int(inner[2] * (1 - t) + outer[2] * t)
            a = int(inner[3] * (1 - t) + outer[3] * t)
            px[x, y] = (r, g, b, a)
    return img


def gear_polygon(cx, cy, outer_r, inner_r, teeth, tooth_depth):
    """Build a polygon for a gear/cog: alternating outer_r and
    (outer_r - tooth_depth) points around a circle, with inner_r
    forming the valleys between teeth tips.

    Actually: the valleys between teeth are at inner_r and the tooth
    TIPS extend to outer_r + tooth_depth. Each tooth spans a sector and
    has 4 corners (2 at valley, 2 at tip) to give it a trapezoid look.
    """
    pts = []
    n = teeth
    # each tooth occupies (2*pi / n); half is tip, half is valley
    # tooth angular width at the tip vs valley
    tip_half = (math.pi / n) * 0.40   # tip width (top of tooth)
    val_half = (math.pi / n) * 0.60   # valley width (bottom, between teeth)
    for i in range(n):
        a_center = (2 * math.pi * i) / n - math.pi / 2  # start at top
        # valley left, tip left, tip right, valley right
        a_vl = a_center - val_half / 2 - tip_half / 2
        a_tl = a_center - tip_half / 2
        a_tr = a_center + tip_half / 2
        a_vr = a_center + val_half / 2 + tip_half / 2
        angles = [a_vl, a_tl, a_tr, a_vr]
        radii  = [outer_r - tooth_depth, outer_r, outer_r, outer_r - tooth_depth]
        for a, r in zip(angles, radii):
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def main():
    # 1. Load source shield (RGBA, transparent background)
    shield = Image.open(SRC).convert("RGBA")
    assert shield.size == (SIZE, SIZE), f"unexpected shield size {shield.size}"

    # 2. Build the badge layer
    # Badge center: lower-right of shield, sized ~40% of canvas diameter.
    cx = int(SIZE * 0.72)  # 737
    cy = int(SIZE * 0.72)  # 737
    diameter = int(SIZE * 0.42)  # 430
    outer_r = diameter // 2       # 215

    badge = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # 2a. Outer navy ring (the 'coin' edge) — drawn as a thick ring
    ring_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring_layer)
    rd.ellipse(
        [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
        fill=NAVY,
    )
    # inner cutout of the ring is the gold face
    face_r = outer_r - int(outer_r * 0.14)
    rd.ellipse(
        [cx - face_r, cy - face_r, cx + face_r, cy + face_r],
        fill=(0, 0, 0, 0),
    )
    # soft outer highlight on the navy ring (a thin lighter arc on top)
    rd.arc(
        [cx - outer_r + 6, cy - outer_r + 6, cx + outer_r - 6, cy + outer_r - 6],
        start=200, end=340, fill=RING_LIGHT, width=4,
    )
    badge = Image.alpha_composite(badge, ring_layer)

    # 2b. Gear teeth around the navy ring's outer edge — sit ON the ring,
    # slightly proud so they read as a cog. Teeth are gold with navy outline.
    teeth = 10
    tooth_depth = int(outer_r * 0.18)        # how far teeth stick out
    teeth_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    td = ImageDraw.Draw(teeth_layer)
    teeth_poly = gear_polygon(cx, cy, outer_r, outer_r - tooth_depth, teeth, tooth_depth)
    td.polygon(teeth_poly, fill=GOLD_LIGHT)
    # navy outline around the gear silhouette so teeth pop against any bg
    td.line(teeth_poly + [teeth_poly[0]], fill=NAVY, width=6)
    # then 'punch in' the inner gold face by drawing the face circle on top
    # (this hides the valleys and leaves only the tooth tips visible as teeth).
    td.ellipse(
        [cx - outer_r + tooth_depth, cy - outer_r + tooth_depth,
         cx + outer_r - tooth_depth, cy + outer_r - tooth_depth],
        fill=(0, 0, 0, 0),
    )
    # Re-draw the gear polygon outline only along the OUTER tooth edge so the
    # navy outline traces just the cog silhouette, not the inner circle we
    # just carved. Easier: redraw the polygon outline, then carve a thinner
    # inner circle that hides the lower portion of the outline.
    td.polygon(teeth_poly, outline=NAVY, width=6)
    # Carve out the body of the gear between the teeth — leaves teeth tips.
    body_r = outer_r - tooth_depth + 4
    td.ellipse(
        [cx - body_r, cy - body_r, cx + body_r, cy + body_r],
        fill=(0, 0, 0, 0),
    )
    # Re-trace just the cog silhouette (outer hull) so navy outline is clean.
    td.line(teeth_poly + [teeth_poly[0]], fill=NAVY, width=6)

    badge = Image.alpha_composite(badge, teeth_layer)

    # 2c. Gold face fill (radial gradient gold) — drawn into the face circle.
    face_layer = draw_radial_gradient(
        (SIZE, SIZE), (cx, cy), face_r - 2,
        inner=GOLD_HI, outer=GOLD_DARK,
    )
    # mask the gradient to a circle
    mask = Image.new("L", (SIZE, SIZE), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - face_r + 2, cy - face_r + 2, cx + face_r - 2, cy + face_r - 2], fill=255)
    face_layer.putalpha(Image.eval(mask, lambda v: v))
    badge = Image.alpha_composite(badge, face_layer)

    # 2d. Downward "install" arrow in navy on the gold face.
    # Arrow occupies the middle ~55% of the face diameter, well clear of the rim.
    arrow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arrow_layer)
    arr_w = int(face_r * 0.55)        # shaft half-width
    arr_h = int(face_r * 0.95)        # total height of the arrow
    # shaft rectangle (top portion)
    shaft_top = cy - arr_h // 2
    shaft_bot = cy + int(arr_h * 0.10)  # leave room for the head
    ad.rectangle(
        [cx - arr_w // 2, shaft_top, cx + arr_w // 2, shaft_bot],
        fill=NAVY,
    )
    # arrowhead triangle (downward)
    head_h = int(arr_h * 0.45)
    head_half = int(face_r * 0.95)
    ad.polygon(
        [
            (cx - head_half // 2, shaft_bot - 4),
            (cx + head_half // 2, shaft_bot - 4),
            (cx,               shaft_bot - 4 + head_h),
        ],
        fill=NAVY,
    )
    # small navy hub circle in the center of the arrow (visual anchor)
    hub_r = int(face_r * 0.10)
    ad.ellipse(
        [cx - hub_r, cy - int(face_r * 0.40) - hub_r,
         cx + hub_r, cy - int(face_r * 0.40) + hub_r],
        fill=NAVY,
    )
    badge = Image.alpha_composite(badge, arrow_layer)

    # 2e. A subtle inner navy rim line on the gold face for crispness
    rim = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd2 = ImageDraw.Draw(rim)
    rd2.ellipse(
        [cx - face_r + 2, cy - face_r + 2, cx + face_r - 2, cy + face_r - 2],
        outline=NAVY, width=4,
    )
    badge = Image.alpha_composite(badge, rim)

    # 3. Composite the badge onto the shield, preserving the shield's alpha
    final = Image.alpha_composite(shield, badge)

    # 4. Save as RGBA PNG (do NOT flatten)
    final.save(DST, format="PNG", optimize=True)
    print(f"wrote {DST}")
    print(f"size={final.size} mode={final.mode}")

    # quick alpha-variance sanity check
    a = final.getchannel("A")
    uniq = len(set(a.getdata()))
    print(f"unique alpha values: {uniq}")


if __name__ == "__main__":
    main()