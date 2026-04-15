#!/usr/bin/env python3
"""Generate WorkAdventure .tmj maps from rooms.json.

One map per floor. Rooms are laid out as rectangular zones in a grid.
Each room gets a website zone linked to its Nextcloud Collective page.
Inter-floor stairs connect via exitUrl zones.

Manually tune in Tiled afterwards — this is the scaffolding, not the final layout.
"""
import json
from pathlib import Path
from copy import deepcopy

BASE = Path(__file__).parent
ROOMS_JSON = BASE / "rooms.json"
OUT = BASE / "maps"
OUT.mkdir(exist_ok=True)
# Path from a generated .tmj (in ./maps/) back to the repo-level tilesets folder.
TILESET_PREFIX = "../../tilesets/"

TILE_SIZE = 32
ROOM_W = 8    # tiles per room
ROOM_H = 6
GUTTER = 1    # wall thickness between rooms
COLS = 4      # rooms per row in the grid

# Tileset references — must match embedded tilesets below
TS = {
    "zones":       {"firstgid": 1,    "png": "WA_Special_Zones.png",     "cols": 6,  "tiles": 12,  "w": 192,  "h": 64},
    "decoration":  {"firstgid": 13,   "png": "WA_Decoration.png",        "cols": 12, "tiles": 96,  "w": 384,  "h": 256},
    "room":        {"firstgid": 109,  "png": "WA_Room_Builder.png",      "cols": 25, "tiles": 1000,"w": 800,  "h": 1280},
    "furniture":   {"firstgid": 1109, "png": "WA_Other_Furniture.png",   "cols": 12, "tiles": 156, "w": 384,  "h": 416},
    "seats":       {"firstgid": 1265, "png": "WA_Seats.png",             "cols": 13, "tiles": 182, "w": 416,  "h": 448},
    "tables":      {"firstgid": 1447, "png": "WA_Tables.png",            "cols": 10, "tiles": 270, "w": 320,  "h": 864},
    "exterior":    {"firstgid": 1717, "png": "WA_Exterior.png",          "cols": 25, "tiles": 850, "w": 800,  "h": 1088},
    "misc":        {"firstgid": 2567, "png": "WA_Miscellaneous.png",     "cols": 10, "tiles": 110, "w": 320,  "h": 352},
}

# Tile IDs within WA_Room_Builder (firstgid + offset)
RB = TS["room"]["firstgid"]
FLOOR_WOOD     = RB + 27   # a wood floor tile
FLOOR_STONE    = RB + 30
WALL_TOP       = RB + 2
WALL_BOTTOM    = RB + 52
WALL_LEFT      = RB + 25
WALL_RIGHT     = RB + 26
WALL_CORNER_TL = RB + 1
WALL_CORNER_TR = RB + 3
WALL_CORNER_BL = RB + 51
WALL_CORNER_BR = RB + 53
DOOR_TILE      = RB + 77

# Special_Zones tile 0 is "start" marker, tile 2 is generic collides
ZONE_START    = 1   # (firstgid=1, offset 0)
ZONE_COLLIDE  = 3   # (firstgid=1, offset 2)

# ---------- helpers ----------

def embedded_tileset(name, info):
    return {
        "firstgid": info["firstgid"],
        "columns": info["cols"],
        "image": f"{TILESET_PREFIX}{info['png']}",
        "imageheight": info["h"],
        "imagewidth": info["w"],
        "margin": 0,
        "spacing": 0,
        "name": name,
        "tilecount": info["tiles"],
        "tileheight": TILE_SIZE,
        "tilewidth": TILE_SIZE,
    }

def empty_layer(name, width, height, visible=True):
    return {
        "data": [0] * (width * height),
        "height": height,
        "width": width,
        "name": name,
        "opacity": 1,
        "type": "tilelayer",
        "visible": visible,
        "x": 0,
        "y": 0,
    }

def draw_rect(layer, w_map, x, y, w, h, floor_tile, wall_border=True):
    """Paint a rectangle of floor tiles with optional wall border."""
    for j in range(h):
        for i in range(w):
            idx = (y + j) * w_map + (x + i)
            if 0 <= idx < len(layer["data"]):
                layer["data"][idx] = floor_tile
    if not wall_border:
        return
    # Not drawing borders on this layer — walls go on a separate layer

def draw_walls(layer, w_map, x, y, w, h, door_side=None):
    """Paint walls around a rectangle. door_side: 'N','S','E','W' opening."""
    # Top & bottom
    for i in range(w):
        if door_side != "N" or i not in (w//2, w//2 - 1):
            layer["data"][y * w_map + (x + i)] = WALL_TOP
        if door_side != "S" or i not in (w//2, w//2 - 1):
            layer["data"][(y + h - 1) * w_map + (x + i)] = WALL_BOTTOM
    # Left & right
    for j in range(h):
        if door_side != "W" or j != h // 2:
            layer["data"][(y + j) * w_map + x] = WALL_LEFT
        if door_side != "E" or j != h // 2:
            layer["data"][(y + j) * w_map + (x + w - 1)] = WALL_RIGHT
    # Corners
    layer["data"][y * w_map + x] = WALL_CORNER_TL
    layer["data"][y * w_map + (x + w - 1)] = WALL_CORNER_TR
    layer["data"][(y + h - 1) * w_map + x] = WALL_CORNER_BL
    layer["data"][(y + h - 1) * w_map + (x + w - 1)] = WALL_CORNER_BR

def draw_collisions(layer, w_map, x, y, w, h, door_side=None):
    """Mark wall tiles as collides in the collision layer."""
    for i in range(w):
        if door_side != "N" or i not in (w//2, w//2 - 1):
            layer["data"][y * w_map + (x + i)] = ZONE_COLLIDE
        if door_side != "S" or i not in (w//2, w//2 - 1):
            layer["data"][(y + h - 1) * w_map + (x + i)] = ZONE_COLLIDE
    for j in range(h):
        if door_side != "W" or j != h // 2:
            layer["data"][(y + j) * w_map + x] = ZONE_COLLIDE
        if door_side != "E" or j != h // 2:
            layer["data"][(y + j) * w_map + (x + w - 1)] = ZONE_COLLIDE

def make_website_zone(room, x_px, y_px, w_px, h_px, obj_id):
    """Object zone that opens the collective page."""
    return {
        "id": obj_id,
        "name": f"site_{room['id']}",
        "type": "website",
        "x": x_px, "y": y_px, "width": w_px, "height": h_px,
        "rotation": 0, "visible": True,
        "properties": [
            {"name": "openWebsite", "type": "string", "value": room["collective_url"]},
            {"name": "openWebsiteTrigger", "type": "string", "value": "onaction"},
            {"name": "openWebsiteTriggerMessage", "type": "string", "value": f"Drück SPACE um {room['name']} zu öffnen"},
        ],
    }

def make_area(room, x_px, y_px, w_px, h_px, obj_id):
    """Named area for the floor label."""
    label = room["name"]
    if room.get("alt_name") and room["alt_name"] != "Alternativnamen":
        label += f" ({room['alt_name']})"
    return {
        "id": obj_id,
        "name": room["id"],
        "type": "area",
        "x": x_px, "y": y_px, "width": w_px, "height": h_px,
        "rotation": 0, "visible": True,
        "properties": [
            {"name": "name", "type": "string", "value": label},
        ],
    }

def make_exit(x_px, y_px, w_px, h_px, target_map, obj_id):
    """Exit zone to another map."""
    return {
        "id": obj_id,
        "name": f"exit_to_{target_map}",
        "type": "",
        "x": x_px, "y": y_px, "width": w_px, "height": h_px,
        "rotation": 0, "visible": True,
        "properties": [
            {"name": "exitUrl", "type": "string", "value": f"{target_map}.tmj#spawn"},
        ],
    }

# ---------- map builder ----------

def build_floor_map(floor_name, rooms, floor_index, all_floors):
    n = len(rooms)
    if n == 0:
        return None

    rows = (n + COLS - 1) // COLS
    width = COLS * (ROOM_W + GUTTER) + GUTTER + 4   # + padding for stairs column
    height = rows * (ROOM_H + GUTTER) + GUTTER + 6  # + padding for corridor/stairs
    # Round to something reasonable
    width = max(width, 30)
    height = max(height, 20)

    # Layers (WA expects specific names)
    ground = empty_layer("ground", width, height)       # floor
    walls = empty_layer("walls", width, height)         # wall tiles (visual)
    collisions = empty_layer("collisions", width, height, visible=False)  # collision mask
    start = empty_layer("start", width, height, visible=False)            # start spawn

    # Website/area objects
    website_objs = []
    area_objs = []
    exit_objs = []
    obj_id = 1

    # Fill full map with a background "street" tile
    BG_TILE = TS["exterior"]["firstgid"] + 24  # grass/outside approximation
    for i in range(width * height):
        ground["data"][i] = BG_TILE

    # Lay out rooms in grid
    for idx, room in enumerate(rooms):
        col = idx % COLS
        row = idx // COLS
        x = GUTTER + col * (ROOM_W + GUTTER)
        y = GUTTER + row * (ROOM_H + GUTTER) + 3  # +3 for top corridor

        # Alternate floor tile per room to show variety
        ftile = FLOOR_WOOD if (idx % 2 == 0) else FLOOR_STONE
        draw_rect(ground, width, x, y, ROOM_W, ROOM_H, ftile, wall_border=False)

        # Door opening - all rooms open south onto the corridor
        draw_walls(walls, width, x, y, ROOM_W, ROOM_H, door_side="S")
        draw_collisions(collisions, width, x, y, ROOM_W, ROOM_H, door_side="S")

        # Door floor tile visible
        door_x = x + ROOM_W // 2
        ground["data"][(y + ROOM_H - 1) * width + door_x] = DOOR_TILE

        # Website zone: inside the room (interior only)
        x_px = (x + 1) * TILE_SIZE
        y_px = (y + 1) * TILE_SIZE
        w_px = (ROOM_W - 2) * TILE_SIZE
        h_px = (ROOM_H - 2) * TILE_SIZE
        website_objs.append(make_website_zone(room, x_px, y_px, w_px, h_px, obj_id))
        obj_id += 1

        # Named area (covers whole room)
        area_objs.append(make_area(
            room, x * TILE_SIZE, y * TILE_SIZE,
            ROOM_W * TILE_SIZE, ROOM_H * TILE_SIZE, obj_id,
        ))
        obj_id += 1

    # Spawn point at top center
    spawn_x = width // 2
    spawn_y = 1
    start["data"][spawn_y * width + spawn_x] = ZONE_START

    # Inter-floor stair exits (top corridor)
    # Prev floor exit (left), next floor exit (right)
    if floor_index > 0:
        prev = all_floors[floor_index - 1]
        exit_objs.append(make_exit(
            TILE_SIZE, TILE_SIZE,
            TILE_SIZE * 2, TILE_SIZE * 2,
            slugify(prev), obj_id,
        ))
        obj_id += 1
    if floor_index < len(all_floors) - 1:
        nxt = all_floors[floor_index + 1]
        exit_objs.append(make_exit(
            (width - 3) * TILE_SIZE, TILE_SIZE,
            TILE_SIZE * 2, TILE_SIZE * 2,
            slugify(nxt), obj_id,
        ))
        obj_id += 1

    # Compose map
    m = {
        "compressionlevel": -1,
        "height": height,
        "infinite": False,
        "width": width,
        "tileheight": TILE_SIZE,
        "tilewidth": TILE_SIZE,
        "nextlayerid": 100,
        "nextobjectid": obj_id + 1,
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "tiledversion": "1.10.0",
        "type": "map",
        "version": "1.10",
        "properties": [
            {"name": "mapName", "type": "string", "value": f"Karpischek — {floor_name}"},
            {"name": "mapDescription", "type": "string", "value": f"{n} Räume · Geschoss {floor_index+1}/{len(all_floors)}"},
            {"name": "mapCopyright", "type": "string", "value": "Laserscan TD Haider · WA Tileset Assets"},
        ],
        "tilesets": [embedded_tileset(k, v) for k, v in TS.items()],
        "layers": [
            start,
            ground,
            walls,
            collisions,
            {
                "id": 50,
                "name": "floorLayer",
                "type": "objectgroup",
                "draworder": "topdown",
                "objects": area_objs,
                "opacity": 1,
                "visible": True,
                "x": 0, "y": 0,
            },
            {
                "id": 51,
                "name": "websites",
                "type": "objectgroup",
                "draworder": "topdown",
                "objects": website_objs,
                "opacity": 1,
                "visible": True,
                "x": 0, "y": 0,
            },
            {
                "id": 52,
                "name": "exits",
                "type": "objectgroup",
                "draworder": "topdown",
                "objects": exit_objs,
                "opacity": 1,
                "visible": True,
                "x": 0, "y": 0,
            },
        ],
    }
    return m

def slugify(s):
    for a, b in [("ä","ae"),("ö","oe"),("ü","ue"),("ß","ss"),(" ", "_"),(".", "")]:
        s = s.replace(a, b)
    return s.lower()

# ---------- main ----------

def main():
    data = json.loads(ROOMS_JSON.read_text(encoding="utf-8"))
    by_floor = {}
    for r in data["rooms"]:
        by_floor.setdefault(r["floor"], []).append(r)

    # Keep floor order from original JSON
    floors = [f for f in data["floors"] if f in by_floor]

    stats = []
    for i, fname in enumerate(floors):
        rooms = by_floor[fname]
        m = build_floor_map(fname, rooms, i, floors)
        if not m:
            continue
        slug = slugify(fname)
        path = OUT / f"{slug}.tmj"
        path.write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
        stats.append((fname, slug, len(rooms), path.stat().st_size // 1024))

    print(f"{'Floor':<25} {'File':<30} {'Rooms':>6} {'Size KB':>8}")
    for f, s, n, kb in stats:
        print(f"{f:<25} maps/{s}.tmj{'':<{18-len(s)}} {n:>6} {kb:>8}")
    print(f"\nStart map: maps/{stats[0][1]}.tmj")
    print(f"Inter-floor stairs connect sequentially.")

if __name__ == "__main__":
    main()
