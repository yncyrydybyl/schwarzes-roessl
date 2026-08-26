#!/usr/bin/env python3
"""Generate three Garagenhof draft maps (hof-a/b/c.tmj), linked by portals.

A — grundrisstreu: wedge yard as in the TD-Haider laserscan, west garage row
    (Garage 1-7), north block (HofCafé + Lager), big east boxes (Holz-/
    Metallwerkstatt), Überdachung strip, PKW stalls.
B — cozy: compact yard, walk-in garages with props, café terrace, greenery.
C — schematisch: floor-plan poster style, rooms as colored zones.

All maps share the office.tmj tileset table (same firstgids), reuse its wall
vocabulary and link back to office.tmj#hof-entrance.
"""
import json
from copy import deepcopy
from pathlib import Path

BASE = Path(__file__).parent.parent
OFFICE = json.loads((BASE / "office.tmj").read_text())
ROOMS = {r["id"]: r for r in json.loads(
    (BASE / "karpischek/rooms.json").read_text())["rooms"]}

T = 32
# wall vocabulary (Room_Builder fg=375)
V, HW = 477, 479
FACE_IN, FACE_OUT = 603, 685
TL, TR, BL, BR = 403, 404, 425, 426
XJ = 512
CAPB, CAPT = 431, 406
WIN = 535
# floors
STONE, GRASS, GRASS2, WOOD = 2483, 2461, 2460, 725
GRAY, WHITE, YELLOW, BLUE, RED = 730, 580, 575, 735, 760
COLLIDE = 3

# ---------------------------------------------------------------- helpers
class MapBuilder:
    LAYERS = ["floor1", "floor2", "walls1", "furniture1", "furniture2",
              "collisions", "above1"]

    def __init__(self, name, w, h, description=""):
        self.name, self.W, self.H = name, w, h
        self.description = description
        self.data = {n: [0]*(w*h) for n in self.LAYERS}
        self.extra_layers = []   # exit/start tile layers + object groups
        self.areas, self.sites = [], []
        self.oid = 1

    def idx(self, x, y):
        return y*self.W + x

    def put(self, layer, x, y, gid):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.data[layer][self.idx(x, y)] = gid

    def fill(self, layer, x0, y0, x1, y1, gid):
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                self.put(layer, x, y, gid)

    def wall(self, x, y, gid):
        self.put("walls1", x, y, gid)
        self.put("collisions", x, y, COLLIDE)

    def clear_wall(self, x, y):
        self.put("walls1", x, y, 0)
        self.put("collisions", x, y, 0)

    def hwall(self, x0, x1, y):
        for x in range(x0, x1+1):
            self.wall(x, y, HW)

    def box(self, x0, y0, x1, y1, face=FACE_IN, windows=False):
        """Rectangular building: top wall pair, sides, bottom wall."""
        self.wall(x0, y0, TL); self.wall(x1, y0, TR)
        for x in range(x0+1, x1):
            self.wall(x, y0, WIN if windows and x % 3 == 0 else HW)
        self.wall(x0, y0+1, V); self.wall(x1, y0+1, V)
        for x in range(x0+1, x1):
            self.wall(x, y0+1, face)
        for y in range(y0+2, y1):
            self.wall(x0, y, V); self.wall(x1, y, V)
        self.wall(x0, y1, BL); self.wall(x1, y1, BR)
        for x in range(x0+1, x1):
            self.wall(x, y1, HW)

    def door_e(self, x, y0, y1):
        """Opening in an east wall, rows y0..y1."""
        for y in range(y0, y1+1):
            self.clear_wall(x, y)
        self.wall(x, y0-1, CAPB)
        self.wall(x, y1+1, CAPT)

    def door_w(self, x, y0, y1):
        self.door_e(x, y0, y1)

    def door_s(self, y_wall, x0, x1, face_row=None):
        """Opening in a south (bottom) wall row, cols x0..x1."""
        for x in range(x0, x1+1):
            self.clear_wall(x, y_wall)
            if face_row is not None:
                self.clear_wall(x, face_row)

    def tree(self, x, y, kind=0):
        """2x3 tree from WA_Exterior; (x,y) = trunk bottom-left tile."""
        base = 1833 + kind
        for r in range(3):
            for c in range(2):
                gid = base + r*25 + c
                layer = "above1" if r < 2 else "furniture1"
                self.put(layer, x+c, y-2+r, gid)
        self.put("collisions", x, y, COLLIDE)
        self.put("collisions", x+1, y, COLLIDE)

    def bush(self, x, y):
        self.put("furniture1", x, y, 1833+450)   # bush tile
        self.put("collisions", x, y, COLLIDE)

    def flowers(self, x, y, kind=0):
        self.put("floor2", x, y, 1833+525+kind)

    def label(self, name, text, x, y, w, h):
        self.areas.append({
            "id": self.oid, "name": name, "type": "area",
            "x": x*T, "y": y*T, "width": w*T, "height": h*T,
            "rotation": 0, "visible": True,
            "properties": [{"name": "name", "type": "string", "value": text}]})
        self.oid += 1

    def website(self, rid, x, y, w, h):
        r = ROOMS[rid]
        self.sites.append({
            "id": self.oid, "name": f"site_{rid}", "type": "area",
            "x": x*T, "y": y*T, "width": w*T, "height": h*T,
            "rotation": 0, "visible": True,
            "properties": [
                {"name": "openWebsite", "type": "string",
                 "value": r["collective_url"]},
                {"name": "openWebsiteTrigger", "type": "string",
                 "value": "onaction"},
                {"name": "openWebsiteTriggerMessage", "type": "string",
                 "value": f"Drück SPACE für Infos: {r['name']}"},
                {"name": "openWebsiteNewTab", "type": "bool", "value": True},
            ]})
        self.oid += 1

    def room_zone(self, rid, text, x, y, w, h):
        self.label(f"area_{rid}", text, x, y, w, h)
        self.website(rid, x, y, w, h)

    def portal(self, slug, url, text, x, y, w=2, h=2, pad_gid=YELLOW):
        """Visible pad + invisible exit layer + label."""
        self.fill("floor2", x, y, x+w-1, y+h-1, pad_gid)
        data = [0]*(self.W*self.H)
        for yy in range(y, y+h):
            for xx in range(x, x+w):
                data[self.idx(xx, yy)] = 5   # special zones EXIT marker
        self.extra_layers.append({
            "data": data, "height": self.H, "width": self.W,
            "id": 200+len(self.extra_layers), "name": f"exit_{slug}",
            "opacity": 1, "type": "tilelayer", "visible": False,
            "x": 0, "y": 0,
            "properties": [{"name": "exitUrl", "type": "string", "value": url}]})
        self.label(f"portal_{slug}", text, x-1, y-1, w+2, h+2)

    def start_layer(self, name, cells, default=False):
        data = [0]*(self.W*self.H)
        for (x, y) in cells:
            data[self.idx(x, y)] = 1     # special zones START marker
        props = [] if default else [
            {"name": "startLayer", "type": "bool", "value": True}]
        layer = {"data": data, "height": self.H, "width": self.W,
                 "id": 220+len(self.extra_layers), "name": name,
                 "opacity": 1, "type": "tilelayer", "visible": False,
                 "x": 0, "y": 0}
        if props:
            layer["properties"] = props
        self.extra_layers.append(layer)

    def build(self):
        layers = []
        lid = 1
        def tl(name, visible=True):
            nonlocal lid
            l = {"data": self.data[name], "height": self.H, "width": self.W,
                 "id": lid, "name": name, "opacity": 1, "type": "tilelayer",
                 "visible": visible, "x": 0, "y": 0}
            lid += 1
            return l
        layers.append(tl("floor1"))
        layers.append(tl("floor2"))
        layers.append(tl("walls1"))
        layers.append(tl("furniture1"))
        layers.append(tl("furniture2"))
        coll = tl("collisions", visible=False)
        coll["properties"] = [{"name": "collides", "type": "bool", "value": True}]
        layers.append(coll)
        for l in self.extra_layers:
            l["id"] = lid; lid += 1
            layers.append(l)
        layers.append({"draworder": "topdown", "id": lid, "name": "floorLayer",
                       "objects": self.areas + self.sites, "opacity": 1,
                       "type": "objectgroup", "visible": True, "x": 0, "y": 0})
        lid += 1
        layers.append(tl("above1"))
        m = {
            "compressionlevel": -1, "height": self.H, "width": self.W,
            "infinite": False, "orientation": "orthogonal",
            "renderorder": "right-down", "tiledversion": "1.10.0",
            "type": "map", "version": "1.10",
            "tilewidth": T, "tileheight": T,
            "nextlayerid": lid + 1, "nextobjectid": self.oid + 1,
            "properties": [
                {"name": "mapName", "type": "string", "value": self.name},
                {"name": "mapDescription", "type": "string",
                 "value": self.description},
                {"name": "mapCopyright", "type": "string",
                 "value": "L7 / WA tilesets CC-BY-SA"},
                {"name": "script", "type": "string", "value": "src/main.ts"},
            ],
            "tilesets": deepcopy(OFFICE["tilesets"]),
        }
        m["layers"] = layers
        return m

WEST_ROW = [
    ("1-hof-garage-1", "Garage 1 — Kpi / Hauslager"),
    ("1-hof-garage-2", "Garage 2 — Georgs Garage"),
    ("1-hof-garage-3", "Garage 3 — Töpferei"),
    ("1-hof-garage-4", "Garage 4 — Druckwerkstatt"),
    ("1-hof-garage-5", "Garage 5 — Druckwerkstatt"),
    ("1-hof-garage-6", "Garage 6 — Studio B (Podcast)"),
    ("1-hof-garage-7", "Garage 7 — Proberaum"),
]

# ================================================================ Entwurf A
def build_a():
    b = MapBuilder("1. Hof — Entwurf A (grundrisstreu)", 46, 48,
                   "Keilform nach Laserscan: Garagenzeile West, "
                   "Werkstätten Ost, PKW-Stellplätze")
    W, H = b.W, b.H
    # yard ground
    b.fill("floor1", 0, 0, W-1, H-1, STONE)

    # --- south: house facade with the Hof gate ---
    b.hwall(0, W-1, 45)
    for x in range(0, W):
        b.wall(x, 46, FACE_OUT)
        b.put("floor1", x, 47, 0)
    for x in range(2, W-2, 5):
        b.put("walls1", x, 45, WIN)
    b.door_s(45, 20, 23, face_row=46)
    b.fill("floor1", 20, 46, 23, 47, STONE)
    b.label("lbl_haus", "Rössl — Haupthaus", 14, 45, 16, 3)

    # --- west garage row (deep boxes, doors east = wide fronts) ---
    gx0, gx1 = 0, 8
    y = 43                       # bottom wall of the lowest box
    boxes = []
    for rid, txt in WEST_ROW:
        boxes.append((rid, txt, y-3, y-1))   # 3 interior rows, pitch 5
        y -= 5
    top = boxes[-1][2] - 2
    b.wall(gx0, top, TL); b.wall(gx1, top, TR)
    for x in range(gx0+1, gx1):
        b.wall(x, top, HW)
    b.wall(gx0, top+1, V); b.wall(gx1, top+1, V)
    for x in range(gx0+1, gx1):
        b.wall(x, top+1, FACE_IN)
    for yy in range(top+2, 43):
        b.wall(gx0, yy, V); b.wall(gx1, yy, V)
    b.wall(gx0, 43, BL); b.wall(gx1, 43, BR)
    for x in range(gx0+1, gx1):
        b.wall(x, 43, HW)
    for rid, txt, iy0, iy1 in boxes[:-1]:
        ya, yb = iy0-2, iy0-1
        b.wall(gx0, ya, XJ); b.wall(gx1, ya, XJ)
        for x in range(gx0+1, gx1):
            b.wall(x, ya, HW)
        b.wall(gx0, yb, V); b.wall(gx1, yb, V)
        for x in range(gx0+1, gx1):
            b.wall(x, yb, FACE_IN)
    for rid, txt, iy0, iy1 in boxes:
        b.fill("floor1", gx0+1, iy0, gx1-1, iy1, GRAY)
        b.door_e(gx1, iy0+1, iy1)          # 2-row garage door
        b.room_zone(rid, txt, gx0+1, iy0, gx1-gx0-1, iy1-iy0+1)

    # --- north block: HofCafé + Lager, doors south ---
    b.box(0, 2, 10, 7, windows=True)
    b.box(10, 2, 20, 7, windows=True)
    b.door_s(7, 4, 5)
    b.door_s(7, 14, 15)
    b.fill("floor1", 1, 4, 9, 6, WOOD)
    b.fill("floor1", 11, 4, 19, 6, GRAY)
    b.room_zone("1-hof-hofcafé-hofladen", "HofCafé — Hofladen", 1, 3, 9, 4)
    b.label("lbl_lager", "Lager (Abstellräume)", 11, 3, 9, 4)
    b.fill("floor1", 0, 0, 20, 1, 0)   # void above the block

    # --- east wedge boundary, stepping in northwards ---
    steps = [(45, 36, 44), (43, 28, 36), (40, 20, 28), (36, 14, 20),
             (32, 11, 14)]
    for (x, y0, y1) in steps:
        for yy in range(y0, y1+1):
            b.wall(x, yy, V)
    b.hwall(43, 45, 36); b.hwall(40, 43, 28); b.hwall(36, 40, 20)
    b.hwall(32, 36, 14)
    b.hwall(21, 32, 11)   # north closing wall towards the tip
    # blank the outside of the wedge
    for (x, y0, y1) in steps:
        b.fill("floor1", x+1, y0, W-1, y1, 0)
    b.fill("floor1", 44, 36, W-1, 36, 0)
    b.fill("floor1", 33, 0, W-1, 13, 0)
    b.fill("floor1", 21, 0, 32, 10, 0)
    b.fill("floor1", 41, 20, W-1, 27, 0)
    b.fill("floor1", 44, 28, W-1, 35, 0)
    b.fill("floor1", 37, 14, W-1, 19, 0)

    # --- big east boxes: Metallwerkstatt & Holzwerkstatt, doors west ---
    b.box(36, 35, 44, 43)
    b.door_w(36, 38, 40)
    b.fill("floor1", 37, 37, 43, 42, GRAY)
    b.room_zone("1-hof-metalwerkstatt", "Metallwerkstatt (Schwarze Kuchl)",
                37, 37, 7, 6)
    b.box(31, 23, 39, 32)
    b.door_w(31, 26, 28)
    b.fill("floor1", 32, 25, 38, 31, WOOD)
    b.room_zone("1-hof-holzwerkstatt", "Holzwerkstatt", 32, 25, 7, 7)

    # --- Überdachung: shaded strip between the two east boxes ---
    b.fill("floor2", 33, 33, 42, 34, GRAY)
    b.label("lbl_ueberdachung", "Überdachung", 33, 33, 9, 2)

    # --- PKW-Stellplätze ---
    for i in range(4):
        x = 13 + i*4
        b.fill("floor2", x, 36, x+2, 40, WHITE)
    b.label("lbl_pkw", "PKW-Stellplätze", 13, 36, 15, 5)

    # --- greenery at the wedge tip ---
    b.tree(24, 15); b.tree(28, 18, kind=3)
    b.bush(22, 13); b.bush(30, 15)
    b.flowers(23, 17); b.flowers(26, 19, 1)

    # --- portals ---
    b.portal("roessl", "office.tmj#hof-entrance", "→ Rössl (Haupthaus)",
             20, 42, 4, 2)
    b.portal("b", "hof-b.tmj#from-a", "→ Entwurf B (cozy)", 22, 12, 3, 2)
    b.label("lbl_hof", "1. Hof — Garagenhof (Entwurf A)", 12, 21, 18, 6)
    b.label("lbl_2hof", "Richtung 2. Hof / Garten", 21, 11, 10, 1)

    b.start_layer("start", [(21, 40), (22, 40)], default=True)
    b.start_layer("from-roessl", [(21, 40), (22, 40)])
    b.start_layer("from-b", [(23, 15), (24, 15)])
    return b.build()

# ================================================================ Entwurf B
def build_b():
    b = MapBuilder("1. Hof — Entwurf B (cozy)", 40, 36,
                   "Kompakter Hof: begehbare Garagen, Café-Terrasse, Grün")
    W, H = b.W, b.H
    b.fill("floor1", 0, 0, W-1, H-1, STONE)
    # grass fringe
    b.fill("floor1", 0, 0, W-1, 2, GRASS)
    b.fill("floor1", 0, H-3, W-1, H-1, GRASS)

    # boundary
    b.hwall(0, W-1, 0)
    for x in range(0, W):
        b.wall(x, 1, FACE_OUT)
    b.hwall(0, W-1, H-1)
    for y in range(1, H-1):
        b.wall(0, y, V); b.wall(W-1, y, V)

    # --- west garage row: open walk-in boxes with props ---
    gx0, gx1 = 1, 9
    y = 32
    boxes = []
    for rid, txt in WEST_ROW:
        boxes.append((rid, txt, y-2, y-1))   # 2 interior rows, pitch 4
        y -= 4
    top = boxes[-1][2] - 2
    b.wall(gx0, top, TL); b.wall(gx1, top, TR)
    for x in range(gx0+1, gx1):
        b.wall(x, top, HW)
    b.wall(gx0, top+1, V); b.wall(gx1, top+1, V)
    for x in range(gx0+1, gx1):
        b.wall(x, top+1, FACE_IN)
    for yy in range(top+2, 32):
        b.wall(gx0, yy, V); b.wall(gx1, yy, V)
    b.wall(gx0, 32, BL); b.wall(gx1, 32, BR)
    for x in range(gx0+1, gx1):
        b.wall(x, 32, HW)
    for rid, txt, iy0, iy1 in boxes[:-1]:
        ya, yb = iy0-2, iy0-1
        b.wall(gx0, ya, XJ); b.wall(gx1, ya, XJ)
        for x in range(gx0+1, gx1):
            b.wall(x, ya, HW)
        b.wall(gx0, yb, V); b.wall(gx1, yb, V)
        for x in range(gx0+1, gx1):
            b.wall(x, yb, FACE_IN)
    props = [WOOD, GRAY, WOOD, BLUE, BLUE, RED, GRAY]
    for i, (rid, txt, iy0, iy1) in enumerate(boxes):
        b.fill("floor1", gx0+1, iy0, gx1-1, iy1, props[i])
        b.door_e(gx1, iy0+1, iy1)
        # a prop table in each garage
        b.put("furniture1", gx0+2, iy0+1, 1557+30)
        b.put("collisions", gx0+2, iy0+1, COLLIDE)
        b.room_zone(rid, txt, gx0+1, iy0, gx1-gx0-1, iy1-iy0+1)

    # --- east: workshops as one building with two big doors ---
    b.box(30, 4, 38, 16)
    b.wall(30, 10, XJ); b.wall(38, 10, XJ)
    for x in range(31, 38):
        b.wall(x, 10, HW)
    b.wall(30, 11, V); b.wall(38, 11, V)
    for x in range(31, 38):
        b.wall(x, 11, FACE_IN)
    b.door_w(30, 7, 8)
    b.door_w(30, 13, 14)
    b.fill("floor1", 31, 6, 37, 9, WOOD)
    b.fill("floor1", 31, 12, 37, 15, GRAY)
    b.room_zone("1-hof-holzwerkstatt", "Holzwerkstatt", 31, 6, 7, 4)
    b.room_zone("1-hof-metalwerkstatt", "Metallwerkstatt", 31, 12, 7, 4)

    # --- HofCafé terrace bottom-right ---
    b.box(30, 20, 38, 26, windows=True)
    b.door_s(26, 33, 34)  # door in bottom wall towards terrace? no: north door
    b.door_s(20, 33, 34, face_row=21)
    b.fill("floor1", 31, 22, 37, 25, WOOD)
    b.room_zone("1-hof-hofcafé-hofladen", "HofCafé — Hofladen", 31, 22, 7, 4)
    # terrace: tables with stools in front (north) of the café
    for tx in (28, 33):
        b.put("furniture1", tx, 18, 1557+30)
        b.put("collisions", tx, 18, COLLIDE)
        for (sx, sy) in ((tx-1, 18), (tx+1, 18), (tx, 17)):
            b.put("furniture1", sx, sy, 1375+13)
    b.label("lbl_terrasse", "Café-Terrasse", 26, 16, 10, 4)

    # --- middle: Diskokugel & greenery ---
    b.put("furniture2", 19, 12, 13+95)      # balloons as disco stand-in
    b.label("lbl_disco", "Diskokugel", 17, 10, 6, 4)
    b.tree(13, 7); b.tree(24, 6, kind=3); b.tree(16, 34)
    b.tree(26, 35, kind=3)
    b.bush(12, 21); b.bush(22, 24); b.bush(27, 30)
    for i, (fx, fy) in enumerate([(14, 20), (21, 8), (25, 22), (12, 9)]):
        b.flowers(fx, fy, i % 4)

    # --- portals ---
    b.portal("roessl", "office.tmj#hof-entrance", "→ Rössl (Haupthaus)",
             18, 32, 4, 2)
    b.portal("a", "hof-a.tmj#from-b", "→ Entwurf A (grundrisstreu)",
             11, 2, 2, 2, pad_gid=WHITE)
    b.portal("c", "hof-c.tmj#from-b", "→ Entwurf C (schematisch)",
             26, 2, 2, 2, pad_gid=WHITE)
    b.label("lbl_hof", "1. Hof — Garagenhof (Entwurf B)", 14, 14, 14, 4)

    b.start_layer("start", [(19, 30), (20, 30)], default=True)
    b.start_layer("from-roessl", [(19, 30), (20, 30)])
    b.start_layer("from-a", [(11, 4), (12, 4)])
    b.start_layer("from-c", [(26, 4), (27, 4)])
    return b.build()

# ================================================================ Entwurf C
def build_c():
    b = MapBuilder("1. Hof — Entwurf C (schematisch)", 36, 28,
                   "Lageplan-Stil: Räume als farbige Zonen mit Links")
    W, H = b.W, b.H
    b.fill("floor1", 0, 0, W-1, H-1, WHITE)
    b.hwall(0, W-1, 0)
    b.hwall(0, W-1, H-1)
    for y in range(1, H-1):
        b.wall(0, y, V); b.wall(W-1, y, V)

    # west column: 7 garage zones as colored cards
    palette = [BLUE, WOOD, GRAY, RED, RED, BLUE, GRAY]
    for i, (rid, txt) in enumerate(WEST_ROW):
        y = 2 + i*3
        b.fill("floor2", 2, y, 12, y+1, palette[i])
        b.room_zone(rid, txt, 2, y, 11, 2)
    # east column: workshops + café + info
    b.fill("floor2", 20, 2, 33, 6, GRAY)
    b.room_zone("1-hof-metalwerkstatt", "Metallwerkstatt (59 m²)", 20, 2, 14, 5)
    b.fill("floor2", 20, 8, 33, 12, WOOD)
    b.room_zone("1-hof-holzwerkstatt", "Holzwerkstatt (72 m²)", 20, 8, 14, 5)
    b.fill("floor2", 20, 14, 33, 18, YELLOW)
    b.room_zone("1-hof-hofcafé-hofladen", "HofCafé — Hofladen", 20, 14, 14, 5)
    b.fill("floor2", 20, 20, 33, 23, BLUE)
    b.website("1-hof-einfahrt", 20, 20, 14, 4)
    b.label("lbl_einfahrt", "Einfahrt — Bar/Heurigen-Space", 20, 20, 14, 4)

    b.label("lbl_title", "1. HOF — ÜBERSICHT (Entwurf C)", 8, 24, 20, 3)

    # portals
    b.portal("roessl", "office.tmj#hof-entrance", "→ Rössl (Haupthaus)",
             15, 25, 3, 2, pad_gid=YELLOW)
    b.portal("b", "hof-b.tmj#from-c", "→ Entwurf B (cozy)",
             15, 1, 3, 2, pad_gid=GRAY)

    b.start_layer("start", [(16, 23), (17, 23)], default=True)
    b.start_layer("from-roessl", [(16, 23), (17, 23)])
    b.start_layer("from-b", [(16, 4), (17, 4)])
    return b.build()

# ================================================================ write
def main():
    for name, builder in (("hof-a", build_a), ("hof-b", build_b),
                          ("hof-c", build_c)):
        m = builder()
        out = BASE / f"{name}.tmj"
        out.write_text(json.dumps(m, indent=1, ensure_ascii=False))
        print(f"{out.name}: {m['width']}x{m['height']}, "
              f"{len(m['layers'])} layers")

if __name__ == "__main__":
    main()
