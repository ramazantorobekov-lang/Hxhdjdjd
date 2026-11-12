#!/usr/bin/env python3
"""Generates the elemental sword: Blockbench project, Bedrock geometry/animation, textures, preview."""
import base64, io, json, math, os, random, uuid
import numpy as np
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
TEX, D = 64, 2  # texture size, pixels per model unit
THEMES = ["fire", "water", "earth", "air"]
rng = random.Random(7)


def uid():
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


# ---------------------------------------------------------------- model
BONES = [  # name, parent, pivot
    ("root", None, [0, 0, 0]),
    ("pommel", "root", [0, 2.5, 0]),
    ("orb", "pommel", [0, 2.5, 0]),
    ("handle", "root", [0, 5, 0]),
    ("guard", "root", [0, 12, 0]),
    ("guard_fire", "guard", [1.25, 12, 0]),
    ("guard_water", "guard", [-1.25, 12, 0]),
    ("guard_earth", "guard", [0, 12, 1.25]),
    ("guard_air", "guard", [0, 12, -1.75]),
    ("blade", "root", [0, 13, 0]),
]
CUBES, LOCATORS = [], []


def cube(name, bone, f, t, mat, rot=(0, 0, 0), origin=None, **kw):
    if origin is None:
        origin = [(a + b) / 2 for a, b in zip(f, t)]
    CUBES.append(dict(name=name, bone=bone, f=list(f), t=list(t), mat=mat, rot=list(rot),
                      origin=list(origin), kw=kw, uuid=uid()))


def locator(name, bone, pos):
    LOCATORS.append(dict(name=name, bone=bone, pos=list(pos), uuid=uid()))


# pommel: crystal shell with the spinning orb inside
cube("pommel_crystal", "pommel", [-2, 0.5, -2], [2, 4.5, 2], "crystal", rot=(0, 45, 0))
cube("pommel_cap_top", "pommel", [-1, 4.5, -1], [1, 5, 1], "ring", rot=(0, 45, 0))
cube("pommel_cap_bottom", "pommel", [-1, 0, -1], [1, 0.5, 1], "ring", rot=(0, 45, 0))
cube("orb_core", "orb", [-0.8, 1.7, -0.8], [0.8, 3.3, 0.8], "orb")
cube("orb_shell_x", "orb", [-0.8, 1.7, -0.8], [0.8, 3.3, 0.8], "orb", rot=(45, 0, 0))
cube("orb_shell_z", "orb", [-0.8, 1.7, -0.8], [0.8, 3.3, 0.8], "orb", rot=(0, 0, 45))
# handle
cube("grip", "handle", [-0.75, 5, -0.75], [0.75, 11.1, 0.75], "grip")
for i, y in enumerate((5.25, 7, 8.75)):
    cube(f"ring_{i + 1}", "handle", [-1, y, -1], [1, y + 0.5, 1], "ring")
cube("earth_inlay_left", "handle", [-1.15, 9.8, -0.35], [-0.6, 10.8, 0.35], "inlay", rot=(0, 0, 15))
cube("earth_inlay_front", "handle", [-0.3, 9.9, 0.6], [0.4, 10.7, 1.1], "inlay", rot=(-15, 0, 0))
# guard: glowing core visible through the 0.5 gaps between the four segments
cube("guard_core", "guard", [-0.75, 11.1, -0.75], [0.75, 12.9, 0.75], "core")
cube("fire_base", "guard_fire", [1.25, 11, -1], [4, 13, 1], "g_fire")
cube("fire_spike", "guard_fire", [4, 11.25, -0.75], [5.6, 12.5, 0.75], "g_fire", rot=(0, 0, 20), origin=[4, 12, 0])
cube("fire_flame_1", "guard_fire", [1.6, 13, -0.5], [2.6, 15, 0.5], "flame", rot=(0, 0, -10), origin=[2.1, 13, 0])
cube("fire_flame_2", "guard_fire", [3, 13, -0.4], [3.8, 14.3, 0.4], "flame", rot=(0, 0, -22), origin=[3.4, 13, 0])
cube("water_base", "guard_water", [-3.75, 11, -1], [-1.25, 13, 1], "g_water")
cube("water_curl", "guard_water", [-4.75, 11.4, -0.75], [-3.75, 12.6, 0.75], "g_water")
cube("water_drop", "guard_water", [-5.25, 11.75, -0.5], [-4.75, 12.25, 0.5], "g_water")
cube("water_crest", "guard_water", [-3.5, 13, -0.75], [-2, 13.5, 0.75], "g_water")
cube("earth_slab_mid", "guard_earth", [-1, 10.75, 1.25], [1, 12.25, 2.75], "g_earth")
cube("earth_slab_top", "guard_earth", [-0.75, 12.25, 1.25], [1.25, 12.9, 2.5], "g_earth")
cube("earth_slab_bottom", "guard_earth", [-1.25, 10.4, 1.5], [0.5, 10.75, 2.4], "g_earth")
cube("air_arc", "guard_air", [-1, 11.5, -2.75], [1, 12.5, -1.75], "g_air")
cube("air_wisp_top", "guard_air", [-1.75, 12.9, -3], [0.25, 13.3, -2.2], "g_air", rot=(0, 20, 0))
cube("air_wisp_bottom", "guard_air", [0, 10.6, -3.2], [1.75, 11, -2.4], "g_air", rot=(0, -20, 0))
# blade: a chain of segments, each tilted a little more, gives the slight curve
x, y, acc = 0.0, 13.0, 0.0
SEGS = [(3.0, 3.5, 0), (3.0, 3.5, 3), (2.6, 3.5, 6), (2.2, 3.5, 9), (1.4, 1.2, 12), (0.7, 0.8, 15)]
TOTAL = sum(s[1] for s in SEGS)
for i, (w, L, a) in enumerate(SEGS):
    kw = dict(rot=(0, 0, a), origin=[x, y, 0], t0=acc / TOTAL, t1=(acc + L) / TOTAL)
    cube(f"blade_seg_{i + 1}" if i < 4 else f"blade_tip_{i - 3}", "blade",
         [x - w / 2, y, -0.4], [x + w / 2, y + L + 0.15, 0.4], "blade", **kw)
    if i < 4:
        cube(f"blade_ridge_{i + 1}", "blade", [x - 0.25, y, -0.6], [x + 0.25, y + L + 0.15, 0.6], "ridge", **kw)
    r = math.radians(a)
    x, y, acc = x - math.sin(r) * L, y + math.cos(r) * L, acc + L

locator("particles_blade", "blade", [-0.4, 21, 0])
locator("particles_fire", "guard_fire", [3, 14.5, 0])
locator("particles_water", "guard_water", [-4.75, 11.5, 0])
locator("particles_earth", "guard_earth", [0, 11.5, 2.75])
locator("particles_air", "guard_air", [0, 12, -3])
locator("particles_orb", "pommel", [0, 2.5, 0])

# ---------------------------------------------------------------- UV packing
FACES = ["north", "south", "east", "west", "up", "down"]


def face_dims(c, face):
    dx, dy, dz = (c["t"][k] - c["f"][k] for k in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy)}.get(face, (dx, dz))


def pack():
    items = []
    for ci, c in enumerate(CUBES):
        for face in FACES:
            lu, lv = face_dims(c, face)
            items.append((max(1, math.ceil(lu * D - 1e-6)), max(1, math.ceil(lv * D - 1e-6)), ci, face))
    items.sort(key=lambda it: (-it[1], -it[0]))
    px = py = shelf = 0
    for w, h, ci, face in items:
        if px + w > TEX:
            px, py, shelf = 0, py + shelf, 0
        shelf = max(shelf, h)
        assert py + h <= TEX, "atlas overflow"
        CUBES[ci].setdefault("uv", {})[face] = (px, py, w, h)
        px += w


pack()

# ---------------------------------------------------------------- texture painting
PAL = {
    "fire": dict(a=(150, 20, 25), b=(255, 170, 40), glow=(255, 120, 20)),
    "water": dict(a=(25, 80, 190), b=(60, 220, 215), glow=(90, 230, 255)),
    "earth": dict(a=(110, 75, 40), b=(90, 150, 60), glow=(120, 230, 90)),
    "air": dict(a=(150, 165, 185), b=(235, 245, 255), glow=(200, 235, 255)),
}
STEEL = (196, 206, 222)
LIGHT = {"up": 1.08, "south": 1.0, "north": 0.94, "east": 0.9, "west": 0.86, "down": 0.78}


def hsh(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 982451653) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535


def mix(a, b, t):
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


def lit(c, f):
    return tuple(min(255, v * f) for v in c)


def paint(c, theme, face, i, j, w, h, X, Y):
    """Returns (rgb, alpha, emissive rgba or None) for one texel."""
    mat, p = c["mat"], PAL[theme]
    u, v = (i + 0.5) / w, (j + 0.5) / h
    n = hsh(X, Y)
    main = face in ("north", "south")
    if mat in ("blade", "ridge"):
        t0, t1 = c["kw"]["t0"], c["kw"]["t1"]
        t = t1 if face == "up" else t0 if face == "down" else t1 - v * (t1 - t0)
        edge = main and mat == "blade" and (i == 0 or i == w - 1)
        col, alpha, em = STEEL, 255, None
        if theme == "fire":
            col = mix(STEEL, mix(p["a"], p["b"], t), 0.78)
            crack = abs((u - 0.5) - 0.32 * math.sin(t * 40 + (face == "north"))) < 0.1 or n < 0.14 * (1 - t / 0.4)
            if t < 0.4 and crack:
                col = mix((255, 110, 20), (255, 215, 70), hsh(X, Y, 2))
                em = col + (255,)
        elif theme == "water":
            col, alpha = mix(STEEL, mix(p["a"], p["b"], 0.5 + 0.5 * math.sin(t * 6)), 0.62), 190
            if math.sin(t * 28 + u * 5) > 0.72:
                col, alpha, em = (200, 245, 255), 230, p["glow"] + (255,)
            elif n < 0.05:
                col = (245, 252, 255)
        elif theme == "earth":
            col = mix(STEEL, mix(p["a"], p["b"], hsh(X // 2, Y // 2, 1)), 0.35 + 0.4 * (1 - t))
            col = lit(col, 0.85 + 0.3 * n)
            if hsh(X, Y, 3) < 0.35 * (1 - t * 2):
                col = lit((70, 130, 50), 0.85 + 0.3 * n)
            elif hsh(X, Y, 5) < 0.06:
                col = (50, 40, 30)
            elif hsh(X, Y, 9) < 0.05:
                col, em = p["glow"], p["glow"] + (255,)
        else:  # air
            col = mix(p["a"], p["b"], t * 0.7 + 0.3 * u)
            if main and mat == "blade" and w >= 5 and i in (1, w - 2) and math.sin(t * 22) > -0.2:
                col, alpha, em = (210, 235, 255), 70, p["glow"] + (140,)
        if mat == "ridge":
            col, alpha = lit(col, 1.18), max(alpha, 235)
            if em is None and math.sin(t * 30) > 0.8:
                em = p["glow"] + (255,)
                col = mix(col, p["glow"], 0.7)
        elif edge and alpha > 100:
            col = lit(mix(col, (255, 255, 255), 0.35), 1.0)
        return col, alpha, em
    if mat == "crystal":
        border = i in (0, w - 1) or j in (0, h - 1)
        col = mix((230, 240, 255), p["glow"], 0.4)
        if border:
            return lit(col, 1.05), 235, None
        return col, 150 if (i + j) % 5 == 0 else 90, None
    if mat == "orb":
        q = "fire water earth air".split()[(u > 0.5) + 2 * (v > 0.5)]
        col = mix(PAL[q]["glow"], (255, 255, 255), 0.35 * n)
        return col, 255, col + (255,)
    if mat == "core":
        col = mix(p["glow"], (255, 255, 255), 0.5 * n)
        return col, 255, col + (255,)
    if mat == "grip":
        col = lit((62, 43, 34), 0.8 + 0.35 * n)
        if (i + j) % 3 == 0:
            col = lit(col, 0.6)
        return col, 255, None
    if mat == "ring":
        col = (236, 190, 70) if abs(u - 0.3) < 0.15 else (205, 155, 45)
        return (lit(col, 0.7) if j == h - 1 and h > 1 else col), 255, None
    if mat == "inlay":
        if n < 0.6:
            col = lit((90, 205, 115), 0.85 + 0.3 * hsh(X, Y, 4))
            return col, 255, (col + (255,) if theme == "earth" else None)
        return lit((120, 118, 108), 0.8 + 0.3 * n), 255, None
    if mat == "flame":
        col = mix((255, 85, 20), (255, 225, 90), 1 - v)
        return col, 255, col + (255,)
    # guard segments keep their own element; the active one is brighter and glows more
    e = {"g_fire": "fire", "g_water": "water", "g_earth": "earth", "g_air": "air"}[mat]
    q, active = PAL[e], e == theme
    spark = 0.2 if active else 0.06
    dim = 1.0 if active else 0.78
    alpha, em = 255, None
    if e == "fire":
        col = mix((70, 25, 20), q["a"], 0.6)
        if n < spark:
            col = q["b"]
            em = col + (255,)
    elif e == "water":
        col, alpha = mix(q["a"], q["b"], (math.sin((u + v) * 6) + 1) / 2), 215
        if n < spark * 0.6:
            col, em = (220, 250, 255), q["glow"] + (255,)
    elif e == "earth":
        col = lit(mix((95, 65, 40), (140, 105, 70), hsh(0, Y, 6)), 0.85 + 0.3 * n)
        if face == "up" or (j == 0 and hsh(X, Y, 7) < 0.5):
            col = lit((80, 140, 55), 0.85 + 0.3 * n)
        if hsh(X, Y, 8) < spark * 0.4:
            col, em = q["glow"], q["glow"] + (255,)
    else:
        col, alpha = mix((170, 185, 205), (240, 248, 255), u), 205
        if abs(v - 0.5 - 0.3 * math.sin(u * 6)) < 0.2:
            col, alpha = (255, 255, 255), 235
            if active:
                em = q["glow"] + (220,)
    return (col if em else lit(col, dim)), alpha, em


def make_textures(theme):
    base = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    emis = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    for c in CUBES:
        for face, (px, py, w, h) in c["uv"].items():
            for j in range(h):
                for i in range(w):
                    col, alpha, em = paint(c, theme, face, i, j, w, h, px + i, py + j)
                    if em is None:
                        col = lit(col, LIGHT[face])
                    base.putpixel((px + i, py + j), tuple(int(v) for v in col) + (int(alpha),))
                    if em:
                        emis.putpixel((px + i, py + j), tuple(int(v) for v in em))
    return base, emis


# ---------------------------------------------------------------- exporters
def data_uri(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


IDLE = "animation.elemental_sword.idle"
ANIM = {  # bone -> channel -> molang vector (loops seamlessly over 8 s)
    "orb": {"rotation": ["math.sin(query.anim_time * 45) * 12", "query.anim_time * 45", "0"]},
    "blade": {"rotation": ["0", "0", "math.sin(query.anim_time * 45) * 1.5"]},
    "guard_air": {"position": ["0", "math.sin(query.anim_time * 90) * 0.25", "0"]},
}
ANIM_LEN = 8


def build_bbmodel(textures):
    bone_uuid = {b[0]: uid() for b in BONES}
    elements = []
    for c in CUBES:
        faces = {f: {"uv": [px, py, px + w, py + h], "texture": 0} for f, (px, py, w, h) in c["uv"].items()}
        elements.append({"name": c["name"], "box_uv": False, "rescale": False, "locked": False,
                         "render_order": "default", "allow_mirror_modeling": True, "from": c["f"], "to": c["t"],
                         "autouv": 0, "color": 0, "origin": c["origin"], "rotation": c["rot"], "faces": faces,
                         "type": "cube", "uuid": c["uuid"]})
    for l in LOCATORS:
        elements.append({"name": l["name"], "position": l["pos"], "rotation": [0, 0, 0], "locked": False,
                         "type": "locator", "uuid": l["uuid"]})

    def group(name):
        _, _, pivot = next(b for b in BONES if b[0] == name)
        kids = [group(b[0]) for b in BONES if b[1] == name]
        kids += [e["uuid"] for e in CUBES + LOCATORS if e["bone"] == name]
        return {"name": name, "origin": pivot, "rotation": [0, 0, 0], "color": 0, "uuid": bone_uuid[name],
                "export": True, "mirror_uv": False, "isOpen": True, "locked": False, "visibility": True,
                "autouv": 0, "children": kids}

    tex = []
    for idx, (name, img, emissive) in enumerate(textures):
        tex.append({"path": "", "name": name, "folder": "", "namespace": "", "id": str(idx), "width": TEX,
                    "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False, "layers_enabled": False,
                    "render_mode": "emissive" if emissive else "default", "render_sides": "auto", "frame_time": 1,
                    "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False, "visible": True,
                    "internal": True, "saved": False, "uuid": uid(), "source": data_uri(img)})
    animators = {}
    for bone, chans in ANIM.items():
        animators[bone_uuid[bone]] = {"name": bone, "type": "bone", "keyframes": [
            {"channel": ch, "data_points": [dict(zip("xyz", vec))], "uuid": uid(), "time": 0, "color": -1,
             "interpolation": "linear"} for ch, vec in chans.items()]}
    return {
        "meta": {"format_version": "4.10", "model_format": "bedrock", "box_uv": False},
        "name": "elemental_sword", "model_identifier": "elemental_sword",
        "visible_box": [3, 3, 1], "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": TEX, "height": TEX},
        "elements": elements, "outliner": [group("root")], "textures": tex,
        "animations": [{"uuid": uid(), "name": IDLE, "loop": "loop", "override": False, "length": ANIM_LEN,
                        "snapping": 24, "selected": True, "anim_time_update": "", "blend_weight": "",
                        "start_delay": "", "loop_delay": "", "animators": animators}],
    }


def build_geo():
    bones = []
    for name, parent, pivot in BONES:
        b = {"name": name}
        if parent:
            b["parent"] = parent
        b["pivot"] = [-pivot[0], pivot[1], pivot[2]]
        cubes = []
        for c in (c for c in CUBES if c["bone"] == name):
            size = [c["t"][k] - c["f"][k] for k in range(3)]
            g = {"origin": [-c["t"][0], c["f"][1], c["f"][2]], "size": size}
            if any(c["rot"]):
                g["pivot"] = [-c["origin"][0], c["origin"][1], c["origin"][2]]
                g["rotation"] = [-c["rot"][0], -c["rot"][1], c["rot"][2]]
            uv = {}
            for f, (px, py, w, h) in c["uv"].items():
                # Bedrock stores up/down faces flipped relative to Blockbench
                uv[f] = ({"uv": [px + w, py + h], "uv_size": [-w, -h]} if f in ("up", "down")
                         else {"uv": [px, py], "uv_size": [w, h]})
            g["uv"] = uv
            cubes.append(g)
        if cubes:
            b["cubes"] = cubes
        locs = {l["name"]: [-l["pos"][0], l["pos"][1], l["pos"][2]] for l in LOCATORS if l["bone"] == name}
        if locs:
            b["locators"] = locs
        bones.append(b)
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.elemental_sword", "texture_width": TEX, "texture_height": TEX,
                        "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
        "bones": bones}]}


def build_anim():
    def num(s):
        try:
            return float(s) if "." in s else int(s)
        except ValueError:
            return s
    return {"format_version": "1.8.0", "animations": {IDLE: {
        "loop": True, "animation_length": ANIM_LEN,
        "bones": {b: {ch: [num(v) for v in vec] for ch, vec in chans.items()} for b, chans in ANIM.items()}}}}


# ---------------------------------------------------------------- software preview
def rot(rx, ry, rz):
    rx, ry, rz = (math.radians(a) for a in (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def render(tex, yaw, pitch, S=14, W=16, H=32):
    tex = np.asarray(tex).astype(float)
    img = np.zeros((H * S, W * S, 3)) + (24, 26, 34)
    zbuf = np.full((H * S, W * S), -1e9)
    V = rot(pitch, 0, 0) @ rot(0, yaw, 0)
    L = lambda a, b, q: a + (b - a) * q
    for translucent in (False, True):
        for c in CUBES:
            (x0, y0, z0), (x1, y1, z1) = c["f"], c["t"]
            R, o = rot(*c["rot"]), np.array(c["origin"])
            for face, (px, py, w, h) in c["uv"].items():
                lu, lv = face_dims(c, face)
                ns, nt = max(2, math.ceil(lu * S * 1.6)), max(2, math.ceil(lv * S * 1.6))
                s, t = np.meshgrid((np.arange(ns) + 0.5) / ns, (np.arange(nt) + 0.5) / nt)
                s, t = s.ravel(), t.ravel()
                k = np.ones_like(s)
                P = {"north": (L(x1, x0, s), L(y1, y0, t), z0 * k), "south": (L(x0, x1, s), L(y1, y0, t), z1 * k),
                     "east": (x1 * k, L(y1, y0, t), L(z1, z0, s)), "west": (x0 * k, L(y1, y0, t), L(z0, z1, s)),
                     "up": (L(x0, x1, s), y1 * k, L(z0, z1, t)), "down": (L(x0, x1, s), y0 * k, L(z1, z0, t))}[face]
                P = ((np.stack(P, -1) - o) @ R.T + o) @ V.T
                rgba = tex[py + np.minimum((t * h).astype(int), h - 1), px + np.minimum((s * w).astype(int), w - 1)]
                sx = ((P[:, 0] + W / 2) * S).astype(int)
                sy = ((H - 1.5 - P[:, 1]) * S).astype(int)
                a = rgba[:, 3]
                ok = (sx >= 0) & (sx < W * S) & (sy >= 0) & (sy < H * S)
                ok &= ((a > 10) & (a < 250)) if translucent else (a >= 250)
                idx = sy[ok] * W * S + sx[ok]
                idx, first = np.unique(idx, return_index=True)
                d, col, a = P[ok][first, 2], rgba[ok][first, :3], a[ok][first, None] / 255
                yy, xx = idx // (W * S), idx % (W * S)
                m = d > zbuf[yy, xx]
                yy, xx = yy[m], xx[m]
                img[yy, xx] = img[yy, xx] * (1 - a[m]) + col[m] * a[m]
                if not translucent:
                    zbuf[yy, xx] = d[m]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def main():
    os.makedirs(f"{OUT}/textures", exist_ok=True)
    os.makedirs(f"{OUT}/bedrock", exist_ok=True)
    textures, views = [], []
    for th in THEMES:
        base, emis = make_textures(th)
        base.save(f"{OUT}/textures/elemental_sword_{th}.png")
        emis.save(f"{OUT}/textures/elemental_sword_{th}_emissive.png")
        textures += [(f"elemental_sword_{th}.png", base, False), (f"elemental_sword_{th}_emissive.png", emis, True)]
        views += [render(base, 0, 0), render(base, -40, 18), render(emis, -40, 18)]
    textures.sort(key=lambda t: t[2])  # base textures first, emissive layers after
    bb = build_bbmodel(textures)
    with open(f"{OUT}/elemental_sword.bbmodel", "w") as f:
        json.dump(bb, f, separators=(",", ":"))
    with open(f"{OUT}/bedrock/elemental_sword.geo.json", "w") as f:
        json.dump(build_geo(), f, indent=1)
    with open(f"{OUT}/bedrock/elemental_sword.animation.json", "w") as f:
        json.dump(build_anim(), f, indent=1)
    w, h = views[0].size
    sheet = Image.new("RGB", (w * len(views), h))
    for i, v in enumerate(views):
        sheet.paste(v, (i * w, 0))
    sheet.save(f"{OUT}/preview.png")

    ids = {e["uuid"] for e in bb["elements"]}

    def walk(g, d=0):
        leaves = [c for c in g["children"] if isinstance(c, str)]
        assert all(c in ids for c in leaves)
        print("  " * d + f"{g['name']} ({len(leaves)})")
        for c in g["children"]:
            if isinstance(c, dict):
                walk(c, d + 1)

    walk(bb["outliner"][0])
    used = max(py + h for c in CUBES for (px, py, w, h) in c["uv"].values())
    print(f"cubes={len(CUBES)} bones={len(BONES)} locators={len(LOCATORS)} atlas rows used={used}/{TEX} blade length={TOTAL}")
    print([t["name"] + ":" + t["render_mode"] for t in bb["textures"]])


if __name__ == "__main__":
    main()
