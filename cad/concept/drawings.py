"""2D drawings for every printed part (+ motor reference + assembly), A3 landscape SVG -> PDF.
Coordinates on the drawings = NX coordinates: X right, Y back, Z up (mm).
Run: python3 drawings.py OUTDIR
"""
import sys, os, math, runpy, datetime
from build123d import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/drawings"
os.makedirs(OUT, exist_ok=True)
_a = sys.argv; sys.argv = ["build.py", "/tmp/drwbuild"]
g = runpy.run_path("/home/claude/cad/build.py", run_name="drw"); sys.argv = _a   # builds the model (exports to /home/claude/site by default)
SHP = {p[0]: p[4] for p in g["parts"]}

# ---------- simple reference model of the S42C motor (what Aru measured)
def motor_ref():
    b = Pos(0, 0, -25) * Box(43, 43, 50)
    b = fillet(b.edges().filter_by(Axis.Z), 4) if False else chamfer(b.edges().filter_by(Axis.Z), 4)
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            b -= Pos(dx, dy, -2.25) * Cylinder(1.5, 4.5)
    b += Pos(0, 0, 1) * Cylinder(11, 2) + Pos(0, 0, 12.5) * Cylinder(2.5, 25)
    return b

W, H = 420, 297
TODAY = datetime.date(2026, 11, 25).strftime("%b %d, %Y")
VIEWS = {"top": ((0, 0, 1000), (0, 1, 0)), "front": ((0, -1000, 0), (0, 0, 1)), "right": ((1000, 0, 0), (0, 0, 1)),
         "iso": ((1000, -1000, 800), (0, 0, 1))}
LABEL = {"top": "TOP (looking down)", "front": "FRONT", "right": "RIGHT SIDE", "iso": "ISO (not to scale)"}

def project(shape, view):
    cam, up = VIEWS[view]
    vis, hid = shape.project_to_viewport(cam, viewport_up=up, look_at=(0, 0, 0))
    def pl(edges):
        out = []
        for e in edges:
            n = 2 if e.geom_type == GeomType.LINE else 28
            out.append([(p.X, p.Y) for p in (e.position_at(i / (n - 1)) for i in range(n))])
        return out
    v, h = pl(vis), pl(hid)
    pts = [p for L in v for p in L] or [(0, 0)]
    bb = (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts))
    return v, h, bb

def fmt(x):
    x = round(x, 2)
    return str(int(x)) if abs(x - int(x)) < 1e-6 else f"{x:g}"

class Sheet:
    def __init__(s): s.o = []
    def add(s, t): s.o.append(t)
    def line(s, x1, y1, x2, y2, cls="th"): s.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" class="{cls}"/>')
    def text(s, x, y, t, size=3, anchor="start", rot=0, bold=False):
        t = t.replace("&", "&amp;").replace("<", "&lt;")
        tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        s.add(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}"{" font-weight=\"bold\"" if bold else ""}{tr}>{t}</text>')
    def rect(s, x, y, w, h, cls="th"): s.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" class="{cls}" fill="none"/>')
    def arrow(s, x, y, dx, dy):
        L = math.hypot(dx, dy) or 1; ux, uy = dx / L, dy / L; a, w = 2.4, 0.8
        s.add(f'<path d="M{x:.2f} {y:.2f} L{x - ux * a - uy * w:.2f} {y - uy * a + ux * w:.2f} L{x - ux * a + uy * w:.2f} {y - uy * a - ux * w:.2f} Z" class="fill"/>')
    def svg(s):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
                '<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#000}.vis{stroke:#000;stroke-width:.45;fill:none}'
                '.hid{stroke:#000;stroke-width:.2;stroke-dasharray:1.6 .8;fill:none}.th{stroke:#000;stroke-width:.18;fill:none}'
                '.bd{stroke:#000;stroke-width:.6;fill:none}.fill{fill:#000}.cl{stroke:#000;stroke-width:.15;stroke-dasharray:6 1.2 1 1.2;fill:none}</style>'
                f'<rect width="{W}" height="{H}" fill="#fff"/>' + "".join(s.o) + "</svg>")

SCALES = [(5, "5:1"), (4, "4:1"), (3, "3:1"), (2, "2:1"), (1.5, "1.5:1"), (1, "1:1"), (0.75, "1:1.33"), (0.5, "1:2"), (0.4, "1:2.5"), (1/3, "1:3"), (0.25, "1:4")]

class Placed:
    def __init__(s, sheet, vis, hid, bb, px, py, sc):
        s.sh, s.vis, s.hid, s.bb, s.px, s.py, s.sc = sheet, vis, hid, bb, px, py, sc
    def P(s, h, v): return s.px + (h - s.bb[0]) * s.sc, s.py + (s.bb[3] - v) * s.sc
    @property
    def box(s):  # paper x1,y1,x2,y2
        x1, y1 = s.P(s.bb[0], s.bb[3]); x2, y2 = s.P(s.bb[1], s.bb[2]); return x1, y1, x2, y2
    def draw(s, label):
        for L in s.hid:
            s.sh.add('<path class="hid" d="M' + " L".join(f"{s.P(*p)[0]:.2f} {s.P(*p)[1]:.2f}" for p in L) + '"/>')
        for L in s.vis:
            s.sh.add('<path class="vis" d="M' + " L".join(f"{s.P(*p)[0]:.2f} {s.P(*p)[1]:.2f}" for p in L) + '"/>')
        x1, y1, x2, y2 = s.box
        s.sh.text((x1 + x2) / 2, y2 + 9 if label != LABEL["top"] else y1 - 3, label, 3.2, "middle", bold=True) if False else None
        s.label = label
    def origin(s, h=0, v=0):
        x, y = s.P(h, v); s.sh.line(x - 4, y, x + 4, y, "th"); s.sh.line(x, y - 4, x, y + 4, "th")
        s.sh.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.3" class="th"/>')
    def dim(s, axis, a, b, off, text=None):
        x1, y1, x2, y2 = s.box
        A, Bp = s.P(*a), s.P(*b)
        val = abs((b[0] - a[0]) if axis == "h" else (b[1] - a[1]))
        t = text if text is not None else fmt(val)
        sh = s.sh
        if axis == "h":
            yl = (y1 - off) if off > 0 else (y2 - off)
            s.low = max(getattr(s, 'low', y2), yl)
            for P_ in (A, Bp):
                sgn = 1 if yl > P_[1] else -1
                sh.line(P_[0], P_[1] + sgn * 1.0, P_[0], yl + sgn * 1.6)
            sh.line(A[0], yl, Bp[0], yl)
            d = 1 if Bp[0] > A[0] else -1
            if abs(Bp[0] - A[0]) > 7:
                sh.arrow(A[0], yl, -d, 0); sh.arrow(Bp[0], yl, d, 0)
            else:
                sh.arrow(A[0], yl, d, 0); sh.arrow(Bp[0], yl, -d, 0)
                sh.line(min(A[0], Bp[0]) - 5, yl, max(A[0], Bp[0]) + 5, yl)
            sh.text((A[0] + Bp[0]) / 2, yl - 0.9, t, 2.8, "middle")
        else:
            xl = (x2 + off) if off > 0 else (x1 + off)
            for P_ in (A, Bp):
                sgn = 1 if xl > P_[0] else -1
                sh.line(P_[0] + sgn * 1.0, P_[1], xl + sgn * 1.6, P_[1])
            sh.line(xl, A[1], xl, Bp[1])
            d = 1 if Bp[1] > A[1] else -1
            if abs(Bp[1] - A[1]) > 7:
                sh.arrow(xl, A[1], 0, -d); sh.arrow(xl, Bp[1], 0, d)
            else:
                sh.arrow(xl, A[1], 0, d); sh.arrow(xl, Bp[1], 0, -d)
                sh.line(xl, min(A[1], Bp[1]) - 5, xl, max(A[1], Bp[1]) + 5)
            sh.text(xl - 0.9, (A[1] + Bp[1]) / 2, t, 2.8, "middle", rot=-90)
    def note(s, p, text, dx, dy):
        x, y = s.P(*p); tx, ty = x + dx, y + dy
        s.sh.line(x, y, tx, ty); s.sh.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r=".5" class="fill"/>')
        lines = text.split("\n")
        anchor = "start" if dx >= 0 else "end"
        s.sh.line(tx, ty, tx + (12 if dx >= 0 else -12), ty)
        for i, L in enumerate(lines):
            s.sh.text(tx + (1 if dx >= 0 else -1), ty - 1 + i * 3.4, L, 2.7, anchor)
    def cline(s, axis, at, a, b):
        if axis == "h":
            p1, p2 = s.P(a, at), s.P(b, at)
        else:
            p1, p2 = s.P(at, a), s.P(at, b)
        s.sh.line(*p1, *p2, "cl")

def frame(sh, num, name, scale_txt, info, std):
    sh.rect(5, 5, W - 10, H - 10, "bd")
    tx, ty = 228, 246
    sh.rect(tx, ty, W - 5 - tx, H - 5 - ty, "bd")
    sh.line(tx, ty + 12, W - 5, ty + 12, "th"); sh.line(tx, ty + 24, W - 5, ty + 24, "th"); sh.line(tx, ty + 35, W - 5, ty + 35, "th")
    for xx in (tx + 60, tx + 120):
        sh.line(xx, ty + 12, xx, ty + 46, "th")
    sh.text(tx + 3, ty + 8.5, f"{num}  {name}", 5, bold=True)
    sh.text(W - 8, ty + 8.5, "STANDARD" if std else "DIMENSIONED", 3, "end", bold=True)
    cells = [("PROJECT", "C-UAS Turret"), ("MATERIAL", info.get("mat", "PETG or PLA, 3 walls, 25% infill")), ("QTY", info.get("qty", "1")),
             ("SCALE", scale_txt), ("UNITS", "mm   3rd-angle projection"), ("DATE", TODAY),
             ("DRAWN", "Claude (from build.py v5b)"), ("CAD", "Aru, Siemens NX"), ("REV", "A")]
    for i, (k, v) in enumerate(cells):
        cx = tx + (i % 3) * 60 + 2; cy = ty + 12 + (i // 3) * 11.5 + 4
        sh.text(cx, cy, k, 2.0); sh.text(cx, cy + 4.6, v, 2.8)

def layout(shape, sc_fixed=None, area=(12, 12, 284, 242), m=22):
    vs = {k: project(shape, k) for k in ("top", "front", "right")}
    wX = vs["top"][2][1] - vs["top"][2][0]; wY = vs["top"][2][3] - vs["top"][2][2]
    hZ = vs["front"][2][3] - vs["front"][2][2]
    ax1, ay1, ax2, ay2 = area
    if sc_fixed:
        sc, st = sc_fixed
    else:
        sc, st = next(((s, t) for s, t in SCALES if s * (wX + wY) + 3 * m <= ax2 - ax1 and s * (wY + hZ) + 3 * m <= ay2 - ay1), SCALES[-1])
    gx = ((ax2 - ax1) - sc * (wX + wY) - 3 * m) / 2; gy = ((ay2 - ay1) - sc * (wY + hZ) - 3 * m) / 2
    c1 = ax1 + m + gx; c2 = c1 + sc * wX + m
    r1 = ay1 + m + gy; r2 = r1 + sc * wY + m
    return vs, sc, st, {"top": (c1, r1), "front": (c1, r2), "right": (c2, r2)}

def iso_box(sh, shape, box, label=True):
    v, hd, bb = project(shape, "iso")
    x1, y1, x2, y2 = box
    sc = min((x2 - x1) / (bb[1] - bb[0] + 1e-9), (y2 - y1 - 6) / (bb[3] - bb[2] + 1e-9))
    px = x1 + ((x2 - x1) - sc * (bb[1] - bb[0])) / 2; py = y1 + ((y2 - y1 - 6) - sc * (bb[3] - bb[2])) / 2
    pv = Placed(sh, v, [], bb, px, py, sc); pv.draw("iso")
    if label:
        sh.text((x1 + x2) / 2, y2, LABEL["iso"], 2.8, "middle", bold=True)
    return pv

def make(part, std):
    sh = Sheet()
    shape = part["shape"]
    vs, sc, st, pos = layout(shape, part.get("scale"))
    placed = {}
    for k, (px, py) in pos.items():
        v, h, bb = vs[k]
        pv = Placed(sh, v, h, bb, px, py, sc); pv.draw(LABEL[k]); placed[k] = pv
    if std:
        for k, pv in placed.items():
            x1, y1, x2, y2 = pv.box; sh.text((x1 + x2) / 2, y2 + 8, LABEL[k], 3, "middle", bold=True)
        iso_box(sh, shape, (288, 18, 410, 200))
        notes = ["GENERAL NOTES", "1. Origin + = NX (0,0,0). X right, Y back, Z up.", f"2. {part['datum']}",
                 "3. Solid lines = visible edges, dashed = hidden edges.", "4. All dimensions on the DIMENSIONED sheet."]
        for i, L in enumerate(notes):
            sh.text(14, 252 + i * 5.5, L, 3.0 if i else 3.3, bold=(i == 0))
    else:
        for (vw, kind, *args) in part.get("dims", []):
            pv = placed[vw]
            if kind == "o":
                pv.origin(*args)
                h0, v0 = args if args else (0, 0)
                if pv.bb[0] - 1 < h0 < pv.bb[1] + 1: pv.cline("v", h0, pv.bb[2] - 4 / pv.sc, pv.bb[3] + 4 / pv.sc)
                if pv.bb[2] - 1 < v0 < pv.bb[3] + 1: pv.cline("h", v0, pv.bb[0] - 4 / pv.sc, pv.bb[1] + 4 / pv.sc)
            elif kind == "n": pv.note(*args)
            elif kind == "cl": pv.cline(*args)
            else: pv.dim(kind, *args)
        for k, pv in placed.items():
            x1, y1, x2, y2 = pv.box; sh.text((x1 + x2) / 2, max(y2, getattr(pv, 'low', y2)) + 7, LABEL[k], 3, "middle", bold=True)
        iso_box(sh, shape, (290, 16, 410, 92))
        sh.text(290, 104, "FEATURES (NX coords, mm)", 3.3, bold=True)
        y = 110
        for row in part["table"]:
            bold = row.startswith("#")
            r = row.lstrip("#").strip()
            words, line = r.split(" "), ""
            out = []
            for w_ in words:
                if len(line) + len(w_) + 1 > 62:
                    out.append(line); line = "   " + w_
                else:
                    line = (line + " " + w_).strip() if line.strip() or not line else line + " " + w_
            out.append(line)
            for L in out:
                sh.text(290, y, L, 2.45, bold=bold); y += 3.5
            y += 0.6
        notes = ["NOTES", f"1. {part['datum']}", "2. Printed holes come out ~0.2 small: test-print one hole first.",
                 "3. " + part.get("print", "Print flat side down. No supports unless noted.")]
        for i, L in enumerate(notes):
            sh.text(14, 252 + i * 5.5, L, 3.0 if i else 3.3, bold=(i == 0))
    frame(sh, part["num"], part["name"], st, part, std)
    if any(placed[k] for k in placed):
        for k in placed: placed[k].origin() if std else None
    return sh.svg()

def at(shape, x, y, z):
    return Pos(-x, -y, -z) * shape   # build coords == NX coords; just move the origin

C = lambda d: f"Ø{fmt(d)}"
PARTS = []
# ------------------------------------------------------------------ P01 floor plate
PARTS.append(dict(num="P01", name="Floor plate", shape=at(SHP["plate"], 0, 0, 0), qty="1",
    datum="Origin = turret pan axis (center of the top hole), Z0 = bottom face.",
    print="Print flat. Needs a bed at least 250 x 220.",
    dims=[("top", "o"), ("top", "h", (-125, -115), (125, -115), -10), ("top", "v", (125, -115), (125, 105), 10),
          ("top", "h", (-85, 50), (85, 50), 10), ("top", "h", (-114, 70), (114, 70), 18),
          ("top", "v", (125, 0), (125, 105), 20), ("top", "v", (125, 0), (125, -115), 20),
          ("top", "v", (-125, 0), (-85, 50), -8), ("top", "v", (-125, 0), (-85, -20), -8),
          ("top", "v", (-125, 0), (-114, 70), -16), ("top", "v", (-125, 0), (-114, -80), -16),
          ("top", "n", (85, -20), "4x Ø4.4 THRU (M4 rods)", 50, -18), ("top", "n", (114, -80), "4x Ø10.2 x 3.1 deep\nfrom TOP (magnets)", 28, 22),
          ("top", "n", (-118, -115 + 2), "4x chamfer 15 x 45°", -4, 10),
          ("front", "v", (125, 0), (125, 5), 8)],
    table=["# Outline", "Rectangle X -125 to 125, Y -115 to 105 (250 x 220). NOT centered in Y: 5 mm more to the front.",
           "4 corners chamfered 15 x 45°. Extrude 5 (Z 0 to 5).",
           "# Rod holes (4)", "Ø4.4 thru at X ±85, Y +50 and Y -20.",
           "# Magnet pockets (4)", "Ø10.2, 3.1 deep from the TOP face, at X ±114, Y +70 and Y -80.",
           "# NX steps", "Sketch on XY: rectangle + 4 chamfers -> Extrude 5. Sketch circles on top face -> Extrude cut (thru / 3.1)."]))
# ------------------------------------------------------------------ P02 cover
PARTS.append(dict(num="P02", name="Cover (one piece)", shape=at(SHP["cover"], 0, 0, 5),
    datum="Origin = turret pan axis, Z0 = bottom of the cover (it sits on the floor plate).",
    print="Print upside down (roof on the bed). Bed at least 256 x 226. Supports only under the J1 hole and vents if needed.",
    dims=[("top", "o"), ("top", "h", (-125, 105), (125, 105), 10), ("top", "h", (-128, -118), (128, -118), -10),
          ("top", "v", (128, -118), (128, 108), 10), ("top", "v", (125, -115), (125, 105), 18),
          ("top", "h", (40, 50), (121, 50), 26), ("top", "v", (121, -50), (121, 50), 26),
          ("top", "h", (0, 0), (40, 0), 18),
          ("top", "n", (-59.4, 59.4), "Ø168 THRU (top hole)", -20, -14), ("top", "n", (80, 30), "Hatch cutout THRU roof", 10, -30),
          ("front", "v", (-128, 0), (-128, 119), -8), ("front", "v", (-128, 0), (-128, 8), -16),
          ("front", "n", (-127, 4), "Skirt: 3 out, 8 tall", -6, 10),
          ("right", "h", (-5, 7), (11, 7), -10), ("right", "v", (11, 7), (11, 21), 10),
          ("right", "v", (11, 0), (11, 7), 18),
          ("right", "n", (11, 21), "J1 hole 16 x 14 THRU\n(right wall only)", 34, -22),
          ("right", "h", (-93, 75), (-45, 75), 8, "vent centers Y -48 -62 -76 -90"),
          ("right", "v", (-93, 25), (-93, 75), -8), ("right", "v", (-93, 0), (-93, 25), -16)],
    table=["# Shell", "Outer: X ±125, Y -115 to 105, corners chamfer 12, Z 0 to 119.",
           "Hollow inside: X ±121, Y -111 to 101, corners chamfer 10, open at the bottom, up to Z 116 (walls 4, roof 3).",
           "Skirt at the bottom: X ±128, Y -118 to 108, chamfer 16, Z 0 to 8.",
           "# Roof cuts", "Ø168 hole at (0,0). Hatch cutout X 40 to 121, Y -50 to 50.",
           "# Hatch magnet bosses (2)", "Blocks under the roof: X 105 to 121, Y 34 to 46 and Y -46 to -34, Z 110 to 116. Magnet pocket Ø10.2, 3.1 deep from the TOP face, at X 113, Y ±40.",
           "# Floor magnet blocks (4)", "Blocks inside the side walls: X 106 to 121 (and -121 to -106), Y 62 to 78 and Y -88 to -72, Z 0 to 11. Pocket Ø10.2, 3.1 deep from the BOTTOM, at X ±114, Y +70 / -80.",
           "# Right wall", "J1 opening thru: Y -5 to 11, Z 7 to 21.",
           "# Vents (both side walls)", "4 slots thru, 6 wide (Y), Z 25 to 75, centers at Y -48, -62, -76, -90.",
           "# NX steps", "Extrude outer -> Shell (remove bottom face, 4 thick) or extrude inner as cut -> skirt -> roof cuts -> bosses/blocks -> pockets -> pattern vents + Mirror."]))
# ------------------------------------------------------------------ P03 hatch
PARTS.append(dict(num="P03", name="Hatch lid", shape=at(SHP["hatch"], 0, 0, 124),
    datum="Origin = turret pan axis, Z0 = bottom of the hatch (sits on the cover roof).",
    print="Print top face down so the magnet pockets face up.",
    dims=[("top", "o"), ("top", "h", (34, -56), (125, -56), -10), ("top", "v", (125, -56), (125, 56), 10),
          ("top", "h", (0, 56), (34, 56), 18), ("top", "v", (113, 0), (113, 40), 18), ("top", "h", (0, 40), (113, 40), 10),
          ("top", "n", (59.4, 59.4 * 0 + 56 if False else 56), "R84 arc (same center as\nthe Ø168 top hole)", -8, -12) if False else ("top", "n", (84 * math.cos(math.radians(48)), 84 * math.sin(math.radians(48))), "R84 cut, centered on (0,0)", -6, -8),
          ("top", "n", (113, -40), "2x Ø10.2 x 3.1 deep\nfrom BOTTOM (0.9 skin)", 6, 14),
          ("front", "v", (125, 0), (125, 4), 8), ("front", "n", (80, 4), "top edges chamfer 1.5", 4, -8)],
    table=["# Plate", "Rectangle X 34 to 125, Y -56 to 56. Extrude 4 (Z 0 to 4).",
           "Cut a circle R84 at (0,0) (same as the cover's top hole).",
           "Chamfer the top straight edges 1.5.",
           "# Magnet pockets (2)", "Ø10.2, 3.1 deep from the BOTTOM face, at X 113, Y ±40. Leaves a 0.9 skin on top.",
           "# Fit", "Overlaps the cover cutout by 6 on 3 sides. Magnets hold it down."]))
# ------------------------------------------------------------------ P04 deck
PARTS.append(dict(num="P04", name="Deck (on 4 rods)", shape=at(SHP["deck"], 0, 0, 111),
    datum="Origin = turret pan axis, Z0 = bottom of the deck.",
    print="Print flat, bottom down. Lazy susan holes: mark and drill at assembly.",
    dims=[("top", "o"), ("top", "h", (-92, -88), (92, -88), -10), ("top", "v", (92, -88), (92, 90), 10),
          ("top", "h", (-85, 50), (85, 50), 12), ("top", "h", (-15.5, 15.5), (15.5, 15.5), 22),
          ("top", "v", (-92, 0), (-92, 90), -8), ("top", "v", (-92, 0), (-92, -88), -8),
          ("top", "v", (0, 0), (-85, 50), -16), ("top", "v", (0, 0), (-85, -20), -24),
          ("top", "v", (0, 0), (-8, 70), -32), ("top", "v", (0, 0), (-8, 82), -40),
          ("top", "h", (-8, 82), (8, 82), 30),
          ("top", "n", (-8.1, 8.1), "Ø23 THRU (motor boss)", -25, -30), ("top", "n", (15.5, -15.5), "4x Ø3.4 THRU\non 31 x 31 (motor)", 70, 52),
          ("top", "n", (-58, -58), "Groove Ø140 / Ø164\n4 deep from TOP", -22, 24), ("top", "n", (85, -20), "4x Ø4.4 THRU (rods)", 22, 34),
          ("front", "v", (92, 0), (92, 5), 8)],
    table=["# Plate", "Rectangle X ±92, Y -88 to 90, corners chamfer 8. Extrude 5.",
           "# Holes", "Ø23 thru at (0,0) for the pan motor's round boss.", "4x Ø3.4 thru at X ±15.5, Y ±15.5 (motor face screws).",
           "4x Ø4.4 thru at X ±85, Y +50 and -20 (rods).",
           "# Cable groove", "Ring: inner Ø140, outer Ø164 (12 wide), 4 deep from the top (1 mm floor left).",
           "# Wire slot", "X -8 to 8, Y 70 to 82, thru (inside the groove at the back).",
           "# NX steps", "Sketch + extrude plate -> holes -> groove = 2 circles, extrude cut 4 from top -> slot."]))
# ------------------------------------------------------------------ P05 U-bracket
PARTS.append(dict(num="P05", name="U-bracket (pan + tilt)", shape=at(SHP["ubracket"], 0, 0, 124),
    datum="Origin = pan axis, Z0 = bottom of the U (sits on the lazy susan). Tilt axis = Z 81.",
    print="Print base down. Arms are 8 thick: use 4 walls / 40% infill for stiffness.",
    dims=[("top", "o"), ("top", "v", (58, -42), (58, 42), 10),
          ("top", "n", (6.36, 6.36), "4x Ø3.4 THRU on R9 at 45°\n(hub flange, MEASURE hub)", 40, -30),
          ("top", "n", (0, -3), "Ø6 THRU (shaft)", -40, 30),
          ("front", "o"), ("top", "h", (-56, 25), (56, 25), 10), ("top", "h", (48, 25), (56, 25), 18), ("top", "h", (-58, 42), (58, 42), 26),
          ("front", "h", (-48, 22), (48, 22), -14, "96 inside"),
          ("front", "v", (56, 0), (56, 14), 8), ("front", "v", (56, 0), (56, 81), 16), ("front", "v", (56, 0), (56, 114), 24),
          ("front", "n", (-44, 18), "gusset 8 x 8", -18, -16),
          ("right", "h", (-25, 114), (25, 114), 8), ("right", "h", (-42, 0), (42, 0), -10),
          ("right", "n", (0, 92.5), "Right arm: Ø23 THRU\n+ 4x Ø3.4 on 31 x 31\nLeft arm: Ø22 THRU (608)", 24, -14),
          ("right", "n", (-25, 108), "top edges\nchamfer 6", -14, -10)],
    table=["# Base", "X ±58, Y ±42, corners chamfer 10, Z 0 to 14.", "Ø6 thru at (0,0) for the pan shaft.",
           "4x Ø3.4 thru on a R9 circle at 45°, 135°, 225°, 315° (hub flange screws; check your hub).",
           "# Arms (2)", "X 48 to 56 and -56 to -48, Y ±25, Z 14 to 114. Chamfer the 2 top edges of each arm 6.",
           "Gussets: X 40 to 48 and -48 to -40, Y ±25, Z 14 to 22.",
           "# Tilt axis Z 81 (Y 0)", "Right arm: Ø23 thru (motor boss) + 4x Ø3.4 thru at Y ±15.5, Z 81 ±15.5 (motor screws).",
           "Left arm: Ø22 thru for the 608 bearing (press fit, test print first).",
           "# NX steps", "Base -> one arm + gusset -> Mirror -> holes. Use the tilt axis as a datum."]))
# ------------------------------------------------------------------ P06 head
PARTS.append(dict(num="P06", name="Head (camera + laser)", shape=at(SHP["head"], 0, 0, 205),
    datum="Origin = tilt axis at the head's center plane (X0). Y- = front (camera side).",
    print="Print back-down (open back on the bed). Stub axle prints sideways: ok, or glue in an 8 mm pin.",
    dims=[("top", "o"), ("top", "h", (-40, 40), (40, 40), 10), ("top", "v", (40, -45), (40, 40), 10),
          ("top", "h", (-60, 0), (-40, 0), 18, "20"), ("top", "n", (-50, 4), "Ø8 stub axle (608)", -6, -14),
          ("top", "v", (40, 0), (40, -30), 18),
          ("top", "n", (0, -30), "M3 clamp hole Ø2.8\nfrom top into bore", -50, 14),
          ("front", "o"), ("front", "h", (-40, -35), (40, -35), -10), ("front", "v", (40, -35), (40, 35), 10),
          ("front", "v", (40, 0), (40, 22), 18), ("front", "v", (40, -7), (40, 0), 26),
          ("front", "n", (0, 18), "Ø8 THRU laser port\n(sleeve stops here)", -40, -14), ("front", "n", (6.4, -13.4), "Ø18 THRU camera window", 22, 18),
          ("right", "h", (-45, -35), (40, -35), -10), ("right", "v", (40, -35), (40, 35), 10),
          ("right", "n", (-45, 26), "front edges chamfer 9", -6, -10),
          ("right", "n", (-26, 14), "laser bore tube\nOD 16 / ID 12.4, Y -42 to -10", 10, -30),
          ("right", "n", (-34, -25), "camera pocket\n36.6 wide x 12.4 deep", -8, 30)],
    table=["# Shell", "Box X ±40, Y -45 to 40, Z ±35. Chamfer the 2 FRONT edges (along X) 9.",
           "Hollow: X ±37, Y -42 to 40 (open back), Z ±32, front inside edges chamfer 6. Walls 3.",
           "Back lip (inside frame): Y 35 to 37, 3 wide (opening X ±34, Z ±29).",
           "# Front wall", "Camera window Ø18 thru at X 0, Z -7. Laser port Ø8 thru at X 0, Z 22.",
           "# Laser bore", "Tube OD 16 / ID 12.4 at X 0, Z 22, from Y -42 (front wall) to Y -10.",
           "Boss Ø9 at X 0, Y -30 from tube top (Z 30) up to the roof. M3 hole Ø2.8 from the top face down into the bore.",
           "# Camera pocket", "Floor X ±22, Y -42 to -26, Z -32 to -25. Back lip X ±22, Y -29.6 to -26, up to Z -21.",
           "Side lips X 18.3 to 22 (and mirror), Y -42 to -26, up to Z -21. Camera sits on Z -25, pressed on the front wall.",
           "# Sides", "Right wall: Ø5.6 thru at (Y0,Z0) for the tilt shaft + 4x Ø2.8 on R9 at 45° (hub flange).",
           "Left: stub axle Ø8 from X -40 to -60 at (Y0,Z0), into the 608."]))
# ------------------------------------------------------------------ P07 back plate
PARTS.append(dict(num="P07", name="Head back plate", shape=at(SHP["head_back"], 0, 0, 205),
    datum="Origin = tilt axis (same as the head). Plate sits at Y 37 to 40.",
    print="Print flat, tab up.",
    dims=[("front", "o"), ("front", "h", (-36.8, -31.8), (36.8, -31.8), -18), ("front", "v", (36.8, -31.8), (36.8, 31.8), 10),
          ("front", "v", (36.8, 0), (36.8, 5), 18), ("front", "n", (6.4, 11.4), "Ø18 THRU (wire exit)", 20, -14),
          ("front", "h", (-10, -33), (10, -33), -10),
          ("right", "h", (37, -31.8), (40, -31.8), -10), ("right", "h", (40, -30), (45, -30), -18, "tab 5")],
    table=["# Plate", "X ±36.8, Z ±31.8, 3 thick (Y 37 to 40). 0.2 smaller than the head opening on every side.",
           "Wire hole Ø18 thru at X 0, Z 5.",
           "# Pull tab", "X ±10, Z -33 to -28, sticks out the back 5 (Y 40 to 45).",
           "# Fit", "Push in until it hits the head's inside lip. Sand the edges if too tight."]))
# ------------------------------------------------------------------ P08 laser sleeve
PARTS.append(dict(num="P08", name="Laser sleeve", shape=at(SHP["sleeve"], 0, -42, 227),
    datum="Origin = center of the sleeve's front face. Sleeve runs back along +Y.",
    print="Print standing on its front face. Change ID only for a different laser.",
    dims=[("front", "o"), ("front", "n", (4.24, 4.24), "OD 12", 14, -8), ("front", "n", (1.41, -1.41), "Ø4 beam hole", 16, 10),
          ("top", "h", (-6, 0), (6, 0), -10), ("top", "v", (6, 0), (6, 20), 10), ("top", "v", (6, 4), (6, 18), 18, "slot 14"),
          ("top", "h", (-1.7, 18), (1.7, 18), 8),
          ("right", "v", (20, -6), (20, 6), 10), ("right", "n", (10, 3.1), "bore Ø6.2 (laser)", 10, -10),
          ("right", "h", (0, -6), (1, -6), -10, "1 wall")],
    table=["# Tube", "OD 12, length 20 (Y 0 to 20). Bore Ø6.2 from the back, stops 1 short of the front.",
           "Front wall 1 thick with a Ø4 hole for the beam.",
           "# Clamp slot", "Top slot 3.4 wide, Y 4 to 18, cut through the top wall. The head's M3 screw goes through it and pinches the laser.",
           "# Fits", "Slides into the head's Ø12.4 bore, stops on the Ø8 lip. Laser: Ø6 x 14 brass (5 V red dot)."]))
# ------------------------------------------------------------------ P09 motor cover
PARTS.append(dict(num="P09", name="Motor cover (optional)", shape=at(SHP["motorcover"], 56.2, 0, 205),
    datum="Origin = center of the open end (against the right arm's outer face).",
    print="Print closed end down. Print LAST, it is optional.",
    dims=[("front", "o"), ("front", "h", (0, -29), (59.8, -29), -18), ("front", "v", (59.8, -29), (59.8, 29), 10),
          ("front", "h", (33.8, -29), (55.8, -29), -10, "slot 22"),
          ("top", "v", (59.8, -27), (59.8, 27), 10), ("right", "h", (-12, -13), (12, -13), -12), ("right", "v", (12, -13), (12, 13), 12),
          ("right", "n", (0, 0), "window 24 x 26 THRU\n(see the S42C screen)", 22, -26)],
    table=["# Box", "X 0 to 59.8, Y ±27, Z ±29. Hollow, walls 4, open at X 0 (closed end wall X 55.8 to 59.8).",
           "# Window", "In the end wall: Y ±12, Z ±13.", "# Cable slot", "Bottom wall: X 33.8 to 55.8, Y ±10.",
           "# Fit", "Slides over the tilt motor (inside 46 x 50) and touches the arm. Friction fit or tape."]))
# ------------------------------------------------------------------ P10 spacer
PARTS.append(dict(num="P10", name="Nucleo spacer", shape=at(SHP["spacer"], -65, -33, 13.6), qty="1 (print 2)",
    datum="Origin = center of the bottom face.",
    print="Print standing up. Or buy an 11 mm M3 standoff instead.",
    dims=[("front", "o"), ("front", "h", (-3, 0), (3, 0), -10, "Ø6"), ("front", "v", (3, 0), (3, 11), 10),
          ("top", "n", (1.2, 1.2), "Ø3.4 THRU (M3)", 10, -8)],
    table=["# Tube", "OD 6, ID 3.4 (M3 screw), 11 tall.", "# Where", "Under the Nucleo's free side (no PCB hole there), same height as the 11 mm standoffs."]))
# ------------------------------------------------------------------ R01 motor reference
PARTS.append(dict(num="R01", name="S42C motor (REFERENCE, bought)", shape=motor_ref(), qty="2 (bought)", mat="Bought part: model it for the assembly",
    datum="Origin = center of the motor's front face. Shaft points +Z. Sizes = Aru's ruler, Nov 25.",
    print="Not printed. Model as a simple block so brackets can be checked in NX.",
    dims=[("front", "o"), ("front", "h", (-21.5, -50), (21.5, -50), -10), ("front", "v", (21.5, -50), (21.5, 0), 10),
          ("front", "v", (21.5, 0), (21.5, 25), 10), ("front", "v", (21.5, 0), (21.5, 2), 18, "2"),
          ("top", "h", (-15.5, 15.5), (15.5, 15.5), 10), ("top", "n", (7.8, 7.8), "Ø22 boss", 20, -14), ("top", "n", (15.5, -15.5), "4x M3 (Ø3) x 4.5 deep\non 31 x 31", 18, 10),
          ("top", "n", (1.8, -1.8), "Ø5 shaft", -16, 16)],
    table=["# Body", "43 x 43, Z -50 to 0 (motor + S42C board + black cover). Corners chamfer 4.",
           "# Front face", "Round boss Ø22 x 2. 4x M3 holes on a 31 x 31 square, 4.5 deep.",
           "# Shaft", "Ø5 x 25 above the face (with a small flat). Total length 75.",
           "# Side plug", "6-pin S42C plug on one side, wires out sideways: leave ~15 mm room on that side."]))

def assembly():
    sh = Sheet()
    names = [n for n in SHP if not n.startswith("so_")]
    full = Compound(children=[SHP[n] for n in names])
    v, hd, bb = project(full, "front")
    sc = 0.5
    pv = Placed(sh, v, [], bb, 20, 40, sc); pv.draw("front")
    x1, y1, x2, y2 = pv.box
    sh.text((x1 + x2) / 2, y2 + 8, "FRONT (cover + hatch shown)", 3, "middle", bold=True)
    vr, hr, br = project(full, "right")
    pr = Placed(sh, vr, [], br, x2 + 16, 40, sc); pr.draw("right")
    a1, b1, a2, b2 = pr.box
    sh.text((a1 + a2) / 2, b2 + 8, "RIGHT SIDE", 3, "middle", bold=True)
    sh.text(20, 22, "Overall: base 256 x 226 (with skirt), about 245 tall. Pan ±150°, tilt -30° to +60°.", 3)
    rows = [("P01", "Floor plate", "print"), ("P02", "Cover", "print"), ("P03", "Hatch lid", "print"), ("P04", "Deck", "print"),
            ("P05", "U-bracket", "print"), ("P06", "Head", "print"), ("P07", "Head back plate", "print"), ("P08", "Laser sleeve", "print"),
            ("P09", "Motor cover (optional)", "print"), ("P10", "Nucleo spacer", "print"), ("R01", "S42C motor x2", "buy"),
            ("-", "Lazy susan 4C, 608 bearing, 2 flange hubs", "buy"), ("-", "4 M4 rods + nuts, 20 magnets 10x3", "buy"),
            ("-", "Carrier PCB, Nucleo, Pi 5, Arducam, laser", "have")]
    tx, ty = 290, 22
    sh.text(tx, ty, "PARTS LIST", 3.4, bold=True)
    for i, (n, d, k) in enumerate(rows):
        yy = ty + 7 + i * 5.2
        sh.text(tx, yy, n, 2.8, bold=True); sh.text(tx + 12, yy, d, 2.8); sh.text(408, yy, k, 2.6, "end")
        sh.line(tx, yy + 1.6, 410, yy + 1.6)
    iso = Compound(children=[SHP[n] for n in names if n not in ("cover", "hatch")] )
    iso_box(sh, iso, (290, 110, 410, 238), label=False)
    sh.text(350, 238, "ISO, cover off", 2.8, "middle", bold=True)
    notes = ["HOW IT GOES TOGETHER", "1. Floor plate -> PCB on standoffs, Pi, rods. 2. Pan motor under the deck, deck on rods.",
             "3. Lazy susan on deck, hub on shaft, U-bracket on hub. 4. Tilt motor on right arm, 608 in left arm, head between.",
             "5. Cover drops over everything onto the floor magnets, hatch on top."]
    for i, L in enumerate(notes):
        sh.text(14, 252 + i * 5.5, L, 3.0 if i else 3.3, bold=(i == 0))
    frame(sh, "A00", "Assembly", "1:2", {"mat": "-", "qty": "-"}, True)
    return sh.svg()

files = []
open(f"{OUT}/A00_assembly.svg", "w").write(assembly()); files.append("A00_assembly.svg")
for p in PARTS:
    base = f"{p['num']}_{p['name'].split(' (')[0].lower().replace(' ', '-')}"
    for std in (True, False):
        fn = f"{base}_{'a-standard' if std else 'b-dimensioned'}.svg"
        open(f"{OUT}/{fn}", "w").write(make(p, std)); files.append(fn)
        print("ok", fn)
open(f"{OUT}/order.txt", "w").write("\n".join(files))
