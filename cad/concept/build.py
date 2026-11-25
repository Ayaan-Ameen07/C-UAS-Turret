"""C-UAS turret concept v3 - parametric model (build123d).
Direct-drive pan (motor centered, under a hollow spoked tube), grey, rectangular base,
compact chamfered head, wires out the back of the head and down the middle.
Coordinates written in viewer frame: x right, y UP, z FRONT (mm). build123d is Z-up:
three (x,y,z) -> build (x, -z, y).
"""
import json, math, os, sys
from build123d import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/site"
os.makedirs(f"{OUT}/models", exist_ok=True)

def B(x1, x2, y1, y2, z1, z2):
    return Pos((x1 + x2) / 2, -(z1 + z2) / 2, (y1 + y2) / 2) * Box(x2 - x1, z2 - z1, y2 - y1)

def CY(axis, c, r, h, sides=None):
    x, y, z = c
    p = Pos(x, -z, y)
    cyl = Cylinder(r, h) if sides is None else extrude(RegularPolygon(r, sides), h / 2, both=True)
    return p * (cyl if axis == "y" else Rot(0, 90, 0) * cyl if axis == "x" else Rot(90, 0, 0) * cyl)

def RING(axis, c, ro, ri, h):
    return CY(axis, c, ro, h) - CY(axis, c, ri, h + 2)

def crect(x1, x2, z1, z2, c, y):
    """chamfered-corner rectangle face at height y (three coords)."""
    pts = [(x1 + c, z1), (x2 - c, z1), (x2, z1 + c), (x2, z2 - c), (x2 - c, z2), (x1 + c, z2), (x1, z2 - c), (x1, z1 + c)]
    return Pos(0, 0, y) * Polygon(*[(x, -z) for x, z in pts], align=None)

def CBOX(x1, x2, z1, z2, c, y1, y2):
    return extrude(crect(x1, x2, z1, z2, c, y1), y2 - y1, dir=(0, 0, 1))

def safe_chamfer(shape, edges, d):
    try:
        return chamfer(edges, d)
    except Exception as e:
        print("chamfer skipped:", e)
        return shape

parts = []
def P(name, group, kind, color, shape):
    parts.append((name, group, kind, color, shape))

# ---------------------------------------------------------------- BASE (rectangle 300 x 354 x 114)
X1, X2, Z1, Z2 = -125, 125, -105, 115                 # v5: shrunk base, 250 x 220
plate_shape = CBOX(X1, X2, Z1, Z2, 15, 0, 5)

outer = CBOX(X1, X2, Z1, Z2, 12, 5, 124)                     # plain box, chamfered corners, flat top
inner = CBOX(X1 + 4, X2 - 4, Z1 + 4, Z2 - 4, 10, 4, 121)
cover = outer - inner
cover -= CY("y", (0, 122, 0), 84, 12)                        # Ø168 hole (Ø150 before; wider so the slack cable at r 76 clears the roof): lazy susan sits in it, wires drop through the gap
cover -= B(X2 - 6, X2 + 2, 12, 26, -11, 5)                     # J1 barrel jack opening (right wall, in line with J1)
for s in (-1, 1):                                            # vents: 4 slots per side wall, beside the Pi
    for i in range(4):
        z = 48 + i * 14
        cover -= B(s * 125 - 8, s * 125 + 8, 30, 80, z - 3, z + 3)
cover += CBOX(X1 - 3, X2 + 3, Z1 - 3, Z2 + 3, 16, 5, 13) - CBOX(X1 + 4, X2 - 4, Z1 + 4, Z2 - 4, 13, 4, 14)  # skirt
cover -= B(40, X2 - 4, 110, 130, -50, 50)                     # rectangular cutout under the tilt motor (to the inner wall)
for z in (-40, 40):
    cover += B(105, 121.5, 115, 121, z - 6, z + 6)              # boss under the top, against the right wall
    cover -= CY("y", (113, 122.5, z), 5.1, 3.2)                 # magnet pocket, opens on the top surface
hatch = B(34, X2, 124, 128, -56, 56) - CY("y", (0, 126, 0), 84, 8)    # lid on top, out to the right wall   # flat lid ON TOP: overlaps the cutout by 6 mm on 3 sides
hatch -= CY("y", (113, 125.5, -40), 5.1, 3.2) + CY("y", (113, 125.5, 40), 5.1, 3.2)   # blind magnet pockets from underneath (1 mm skin on top)
hatch = safe_chamfer(hatch, hatch.edges().group_by(Axis.Z)[-1].filter_by(GeomType.LINE), 1.5)
for z in (-40, 40):
    P(f"magnet_hatch_lo_{z}", "base", "buy", "metal", CY("y", (113, 122.5, z), 5, 3))
    P(f"magnet_hatch_hi_{z}", "base", "buy", "metal", CY("y", (113, 125.5, z), 5, 3))
MAGS = [(-114, -70), (114, -70), (-114, 80), (114, 80)]
for (x, z) in MAGS:
    xa, xb = (106, 121.5) if x > 0 else (-121.5, -106)          # block is built INTO the side wall (touches it)
    cover += B(xa, xb, 5, 16, z - 8, z + 8)
    cover -= CY("y", (x, 6.5, z), 5.1, 3.2)                      # magnet pocket in the block's bottom face
P("cover", "base", "print", "grey", cover)
P("hatch", "base", "print", "grey2", hatch)


for (x, z) in [(-114, -70), (114, -70), (-114, 80), (114, 80)]:
    plate_shape -= CY("y", (x, 3.5, z), 5.1, 3.2)              # magnet pockets in the floor plate
    P(f"magnet_lo_{x}_{z}", "base", "buy", "metal", CY("y", (x, 3.5, z), 5, 3))
    P(f"magnet_hi_{x}_{z}", "base", "buy", "metal", CY("y", (x, 6.5, z), 5, 3))
RODS = [(85, -50), (-85, -50), (85, 20), (-85, 20)]           # 4x M4 rods; front pair at z 20 so they don't block the Pi USB ports
for (x, z) in RODS:
    plate_shape -= CY("y", (x, 2.5, z), 2.2, 7)              # rod holes
P("plate", "base", "print", "grey2", plate_shape)

# ---- deck on rods
deck = CBOX(-92, 92, -90, 88, 8, 111, 116) - CY("y", (0, 113.5, 0), 11.5, 8)    # deck bridges over the PCB, motor hangs under it
deck -= RING("y", (0, 115, 0), 82, 70, 6)                    # cable groove r 76, 12 wide, 4 deep (y 112-116): slack cable rides here when the turret pans
deck -= B(-8, 8, 106, 121, -82, -70)                         # wire slot at the back of the groove, drops to J4-J7
for dx in (-15.5, 15.5):
    for dz in (-15.5, 15.5):
        deck -= CY("y", (dx, 113.5, dz), 1.7, 8)              # motor face screws
for (x, z) in RODS:
    deck -= CY("y", (x, 113.5, z), 2.2, 8)
P("deck", "base", "print", "print", deck)
sb = Part()
for dx in (-15.5, 15.5):
    for dz in (-15.5, 15.5):
        sb += CY("y", (dx, 112, dz), 1.5, 10) + CY("y", (dx, 116.85, dz), 2.75, 1.7)    # pan motor face screws (heads sit in the lazy susan center)
P("screws_base", "base", "buy", "steel", sb)
rods = Part()
for (x, z) in RODS:
    rods += CY("y", (x, 58, z), 2, 116)
    for y in (6.7, 109.3, 117.7):
        rods += CY("y", (x, y, z), 3.5, 3.2, sides=6)
P("rods", "base", "buy", "steel", rods)
ls_lo = CBOX(-50.8, 50.8, -50.8, 50.8, 4, 116, 117.2) - CY("y", (0, 116.6, 0), 30, 4)
ls_ring = RING("y", (0, 120, 0), 34, 30, 6)
P("lazysusan", "base", "buy", "metal", ls_lo + ls_ring)
P("lazysusan_top", "pan", "buy", "metal", CBOX(-50.8, 50.8, -50.8, 50.8, 4, 122.8, 124) - CY("y", (0, 123.4, 0), 30, 4))

# electronics (PCB at the front, rotated 180 so its connector edge faces the center)
P("pcb", "base", "buy", "pcb", B(-75, 75, 12, 13.6, -95, 5))   # KiCad X27..177, Y64..164 -> x = 102 - X, z = 69 - Y
pcbp = (B(55.5, 69.5, 13.6, 24.6, -12, 6)                       # J1 barrel jack (X39.5 Y72), opening faces +x (right wall)
        + B(63.5, 78.5, 13.6, 21, -95, -83) + B(42.5, 57.5, 13.6, 21, -95, -83)   # J6 (X31) J7 (X52), back edge
        + B(25, 33, 13.6, 21, -95, -83) + B(11, 23, 13.6, 21, -95, -83)           # J5 (X73) J4 (X85)
        + CY("y", (40, 24, -40), 9, 21) + B(45, 65, 13.6, 30, -60, -40))         # bulk cap, fuse holder (approx)
P("pcb_parts", "base", "buy", "black", pcbp)
P("pololu", "base", "buy", "blue", B(1, 26, 20, 30, -26, -6) + B(0, 3, 13.6, 20, -22, -10))   # J3 (X101 Y85), module points +x
P("nucleo", "base", "buy", "white", B(-75, -5, 24.6, 26.2, -95, 38) + B(-45, -33, 26.2, 30, 33, 39) + B(-55, -30, 26.2, 28, 5, 25))   # overhangs the J1 end by ~33
for (x, z) in [(-71, -91), (71, -91), (-71, 1), (71, 1)]:
    P(f"so_pcb_{x}_{z}", "base", "buy", "brass", CY("y", (x, 8.5, z), 2.5, 7))
# ---- S42C (local build coords: shaft +Z, face z=0, 6-pin side plug on +X edge) from BTT manual drawing
def s42c():
    sq = 43.0                                      # Aru ruler Nov 25: face 43 x 43, body+cover 50, shaft 25
    def blk(z1, z2):
        b = Pos(0, 0, (z1 + z2) / 2) * Box(sq, sq, z2 - z1)
        return safe_chamfer(b, b.edges().filter_by(Axis.Z), 4.2)
    body = blk(-9, 0) + blk(-31, -9.5) + blk(-40, -31)
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            body -= Pos(dx, dy, -2) * Cylinder(1.5, 4.5)
    shaft = Pos(0, 0, 1) * Cylinder(11, 2) + Pos(0, 0, 12.5) * Cylinder(2.5, 25) - Pos(2.6, 0, 16.5) * Box(1.0, 6, 17)
    board = Pos(0, 0, -44.2) * Box(40, 40, 1.6)
    board = safe_chamfer(board, board.edges().filter_by(Axis.Z), 3.5)
    board += Pos(0, 17.5, -41) * Box(12.5, 5, 4) + Pos(-18.5, 0, -46) * Box(2.5, 25, 2.5)
    oled = Pos(0, -2, -46.5) * Box(27, 16, 3) + sum([Pos(x, -16, -46) * Box(5, 4, 2) for x in (-10, 0, 10)], Part())
    plug = Pos(17.5, 0, -48.5) * Box(5, 15.5, 7) + Pos(23, 0, -48.5) * Box(6, 14.5, 6)
    return {"body": body, "shaft": shaft, "board": board, "oled": oled, "plug": plug}

def place_motor(name, group, loc):
    m = s42c()
    for k, col in (("body", "motor"), ("shaft", "steel"), ("board", "pcb"), ("oled", "black"), ("plug", "white")):
        P(f"{name}_{k}", group, "buy", col, loc * m[k])

place_motor("panmot", "base", Pos(0, 0, 111))                 # hangs under the pedestal motor plate, shaft up, plug +x
TY = 205                                                     # tilt axis height
place_motor("tiltmot", "pan", Pos(56, 0, TY) * Rot(0, -90, 0) * Rot(0, 0, 180))

# ---- Raspberry Pi 5 + Active Cooler (official drawing, +-1 mm); ports face the back door
def pi5():
    brd = Pos(42.5, 28, 0.8) * Box(85, 56, 1.6)
    brd = safe_chamfer(brd, brd.edges().filter_by(Axis.Z), 3)
    for (x, y) in [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]:
        brd -= Pos(x, y, 0.8) * Cylinder(1.35, 3)
    conn = (Pos(32.5, 52.5, 5.85) * Box(50.8, 5.1, 8.5) + Pos(78.75, 9, 9.6) * Box(17.5, 13.1, 16)
            + Pos(78.75, 27, 9.6) * Box(17.5, 13.1, 16) + Pos(76.75, 45.75, 8.4) * Box(21.5, 16, 13.6)
            + Pos(11.2, 2.5, 3.2) * Box(9, 7.5, 3.2) + Pos(25.8, 2.6, 3.35) * Box(7.5, 7, 3.5)
            + Pos(39.2, 2.6, 3.35) * Box(7.5, 7, 3.5) + Pos(4, 28, -0.7) * Box(14, 12, 1.4))
    chips = Pos(30, 26, 2.3) * Box(17, 17, 1.4) + Pos(56, 26, 2.2) * Box(11, 11, 1.2)
    hs = Pos(34, 28, 10.1) * Box(56, 44, 9)
    for i in range(9):
        hs -= Pos(10 + i * 4.6, 28, 13.1) * Box(2.2, 46, 7)
    return {"board": brd, "conn": conn, "chips": chips, "cooler": hs + Pos(56, 16, 12.1) * Cylinder(14, 6)}
pi_loc = Pos(5, -52, 10) * Rot(0, 0, 180)                   # Pi: x -80..5, z 40..96, USB end faces the left wall
pm = pi5()
for k, col in (("board", "pi"), ("conn", "metal"), ("chips", "black"), ("cooler", "alu")):
    P(f"pi_{k}", "base", "buy", col, pi_loc * pm[k])
for (x, y) in [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]:
    P(f"so_pi_{x}_{y}", "base", "buy", "brass", Pos(5 - x, -(40 + y), 7.5) * Cylinder(2.5, 5))

# ---------------------------------------------------------------- PAN GROUP
P("panhub", "pan", "buy", "steel", RING("y", (0, 120.5, 0), 9, 2.5, 7))   # 5 mm flange hub, bolted under the U-bracket
ubr = CBOX(-58, 58, -42, 42, 10, 124, 138) - CY("y", (0, 131, 0), 3, 16)    # base of the U (14 thick), shaft hole
for a in (45, 135, 225, 315):
    r = math.radians(a)
    ubr -= CY("y", (9 * math.cos(r) * 1.0, 131, 9 * math.sin(r)), 1.7, 16)   # hub flange screws
for s_ in (-1, 1):
    arm = B(48, 56, 138, 238, -25, 25) if s_ > 0 else B(-56, -48, 138, 238, -25, 25)
    arm = safe_chamfer(arm, arm.edges().filter_by(Axis.X).filter_by(lambda e: e.center().Z > 200), 6)
    ubr += arm + (B(40, 48, 138, 146, -25, 25) if s_ > 0 else B(-48, -40, 138, 146, -25, 25))   # inside fillet blocks
ubr -= CY("x", (52, TY, 0), 11.5, 10)
for dy in (-15.5, 15.5):
    for dz in (-15.5, 15.5):
        ubr -= CY("x", (52, TY + dy, dz), 1.7, 10)
ubr -= CY("x", (-52, TY, 0), 11, 10)
P("ubracket", "pan", "print", "grey", ubr)
sp = Part()
for dy in (-15.5, 15.5):
    for dz in (-15.5, 15.5):
        sp += CY("x", (53, TY + dy, dz), 1.5, 12) + CY("x", (47.15, TY + dy, dz), 2.75, 1.7)   # tilt motor face screws (heads inside the arm)
P("screws_pan", "pan", "buy", "steel", sp)
P("brg608", "pan", "buy", "metal", RING("x", (-52.5, TY, 0), 11, 4, 7))
mc = B(56.2, 116, TY - 29, TY + 29, -27, 27) - B(55, 112, TY - 25, TY + 25, -23, 23)   # starts at the arm's outer face
mc = safe_chamfer(mc, mc.edges().filter_by(Axis.X).filter_by(lambda e: e.center().X > 100), 4)
mc -= B(111, 118, TY - 13, TY + 13, -12, 12)                         # screen window
mc -= B(90, 112, TY - 33, TY - 24, -10, 10)                          # cable slot at the bottom
P("motorcover", "pan", "print", "grey2", mc)

# ---------------------------------------------------------------- TILT GROUP (compact head)
HX, HY1, HY2, HZ1, HZ2 = 40, TY - 35, TY + 35, -40, 45
head = B(-HX, HX, HY1, HY2, HZ1, HZ2)
head = safe_chamfer(head, head.edges().filter_by(Axis.X).filter_by(lambda e: e.center().Y < 0), 9)   # chamfer the 2 FRONT edges only; back stays square so the back plate fits
cav = B(-HX + 3, HX - 3, HY1 + 3, HY2 - 3, HZ1 - 5, HZ2 - 3)
cav = safe_chamfer(cav, cav.edges().filter_by(Axis.X).filter_by(lambda e: e.center().Y < 0), 6)     # inside follows the outside chamfer: 3 mm wall everywhere (no slit)
head -= cav
head += B(-HX + 3, HX - 3, HY1 + 3, HY2 - 3, HZ1 + 3, HZ1 + 5) - B(-HX + 6, HX - 6, HY1 + 6, HY2 - 6, HZ1 + 2, HZ1 + 6)   # inside lip the back plate presses against
head -= CY("z", (0, TY - 7, 43.5), 9, 8)                        # camera window
head -= CY("z", (0, TY + 22, 43.5), 4, 8)                        # laser port: Ø8 < Ø12 laser = front stop
head += RING("z", (0, TY + 22, 26), 8, 6.2, 32)  # sleeve bore Ø12.4, tube z 10..42
head += CY("y", (0, TY + 31.5, 30), 4.5, 3)                   # boss joining the slot to the top wall
head -= CY("y", (0, TY + 30, 30), 1.4, 16)                    # M3 clamp screw hole, reached from the TOP of the head
head += B(-22, 22, TY - 32, TY - 25, 26, 42) + B(-22, 22, TY - 29, TY - 21, 26, 29.6) + B(-22, -18.3, TY - 29, TY - 21, 26, 42) + B(18.3, 22, TY - 29, TY - 21, 26, 42)   # camera shelf: floor + back lip + side lips = pocket 36.6 wide, 10.4 deep
head -= CY("x", (38.5, TY, 0), 2.8, 6)                       # shaft hole, right wall
for a in (45, 135, 225, 315):
    head -= CY("x", (38.5, TY + 9 * math.sin(math.radians(a)), 9 * math.cos(math.radians(a))), 1.4, 6)   # 4x M3 self-tap holes for the tilt hub flange (r9, MEASURE hub)
head += CY("x", (-50, TY, 0), 4, 20)                         # left stub axle into the 608
P("head", "tilt", "print", "grey3", head)
back = B(-HX + 3.2, HX - 3.2, HY1 + 3.2, HY2 - 3.2, HZ1, HZ1 + 3)
back -= CY("z", (0, TY + 5, HZ1 + 1.5), 9, 6)                   # wire exit (Ø18 + grommet)
back += B(-10, 10, TY - 33, TY - 28, HZ1 - 5, HZ1)            # pull tab   # slide rails
P("head_back", "tilt", "print", "grey2", back)
P("camera", "tilt", "buy", "black", B(-18, 18, TY - 25, TY + 11, 30, 40) + B(-12, 12, TY - 19, TY + 5, 40, 42) + CY("z", (0, TY - 7, 42.375), 7, 0.75))
P("lens", "tilt", "buy", "glass", CY("z", (0, TY - 7, 42.8), 3, 0.2))
P("laser", "tilt", "buy", "alu", CY("z", (0, TY + 22, 34), 3, 14))   # Ø6 x 14 brass, z 27..41, nose on the sleeve's front wall
sleeve = CY("z", (0, TY + 22, 32), 6, 20) - CY("z", (0, TY + 22, 31), 3.1, 20) - CY("z", (0, TY + 22, 41.5), 2, 2)   # OD 12, ID 6.2, 1 mm front wall with Ø4 beam hole
sleeve -= B(-1.7, 1.7, TY + 26, TY + 29, 24, 38)              # top slot: the M3 clamp screw goes through it and pinches the laser
P("sleeve", "tilt", "print", "grey2", sleeve)
P("spacer", "base", "print", "grey2", RING("y", (-65, 19.1, 33), 3, 1.7, 11))   # 11 mm spacer under the Nucleo free corner (approx spot)
P("tilthub", "tilt", "buy", "steel", CY("x", (44, TY, 0), 9, 6))   # x 41..47, between head and arm

# ---------------------------------------------------------------- EXPORT
manifest = []
for name, group, kind, color, shp in parts:
    fn = f"models/{name}.stl"
    export_stl(shp, f"{OUT}/{fn}", tolerance=0.15, angular_tolerance=0.25)
    manifest.append({"name": name, "group": group, "kind": kind, "color": color, "file": fn})
json.dump(manifest, open(f"{OUT}/manifest.json", "w"))
for name, group, kind, color, shp in parts:
    shp.label = name
export_step(Compound(children=[p[4] for p in parts], label="cuas_turret_concept_v3"), f"{OUT}/turret-concept-v3.step")

def face_paths(face, mapf):
    out = []
    for w in [face.outer_wire()] + list(face.inner_wires()):
        try:
            es = w.order_edges()
        except Exception:
            es = w.edges()
        pts = []
        for e in es:
            n = 2 if e.geom_type == GeomType.LINE else 24
            pts += [mapf(e.position_at(i / (n - 1))) for i in range(n)]
        if pts:
            out.append("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z")
    return " ".join(out)

def do_section(plane, mapf):
    res = []
    for name, group, kind, color, shp in parts:
        try:
            sk = section(shp, section_by=plane)
        except Exception:
            continue
        for f in (sk.faces() if sk is not None else []):
            if f.area >= 0.05:
                res.append({"n": name, "k": kind, "d": face_paths(f, mapf)})
    return res
json.dump({"front": do_section(Plane.XZ, lambda v: (v.X, -v.Z)),
           "side": do_section(Plane.YZ, lambda v: (-v.Y, -v.Z))}, open(f"{OUT}/sections.json", "w"))

base_parts = [p[4] for p in parts if p[1] == "base" and p[0] not in ("cover", "door", "plate")]
vis, hid = Compound(children=base_parts).project_to_viewport((0, 0, 1000), viewport_up=(0, 1, 0), look_at=(0, 0, 0))
def e2p(edges):
    out = []
    for e in edges:
        n = 2 if e.geom_type == GeomType.LINE else 20
        out.append("M" + " L".join(f"{p.X:.2f} {-p.Y:.2f}" for p in (e.position_at(i / (n - 1)) for i in range(n))))
    return out
json.dump({"vis": e2p(vis), "hid": e2p(hid)}, open(f"{OUT}/topview.json", "w"))
print("parts", len(parts))
