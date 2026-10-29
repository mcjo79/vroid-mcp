"""Automatic preset labels and visual metadata.

VRoid exposes no human-readable name for built-in presets. This module derives a stable,
low-confidence label at cache time:

1. structural part (category + number) on every sync;
2. visual part (dominant colors, brightness, plain/patterned) when a situation thumbnail is
   generated.

Generated data is stored apart from human annotations (description/tags/colors): a manual
label or annotation always wins, and `vroid_preset_cache_annotate` can replace the label.
"""
import datetime
import os

CATEGORY_LABELS = {
    "Clothing/Tops": "Tops",
    "Clothing/Bottoms": "Bottoms",
    "Clothing/Onepiece": "Onepiece",
    "Clothing/Shoes": "Shoes",
    "Clothing/Socks": "Socks",
    "Clothing/InnerTop": "Inner top",
    "Clothing/InnerBottom": "Inner bottom",
    "Clothing/AccessoryNeck": "Neck accessory",
    "Clothing/AccessoryArm": "Arm accessory",
    "VRoid/ClothingSet": "Outfit set",
    "Hair": "Hair",
    "Hair/AllHair": "Hair set",
    "Hair/Back": "Back hair",
    "Hair/Tied": "Tied hair",
    "VRoid/HairSet": "Hair set",
    "Face": "Face",
    "Overlay": "Face overlay",
    "VRoid/FaceSet": "Face set",
    "VRoid/EyeSet": "Eye set",
    "VRoid/EyeballSet": "Eyeball set",
    "VRoid/Body": "Body",
    "Attachment": "Attachment",
}

CATEGORY_TAGS = {
    "Clothing/Tops": "top", "Clothing/Bottoms": "bottom", "Clothing/Onepiece": "dress",
    "Clothing/Shoes": "shoes", "Clothing/Socks": "socks", "Clothing/InnerTop": "inner-top",
    "Clothing/InnerBottom": "inner-bottom", "Clothing/AccessoryNeck": "necklace",
    "Clothing/AccessoryArm": "arm-accessory", "VRoid/ClothingSet": "outfit",
    "Hair": "hair", "Hair/AllHair": "hair", "Hair/Back": "back-hair", "Hair/Tied": "tied-hair",
    "VRoid/HairSet": "hair", "Face": "face", "Overlay": "overlay", "VRoid/FaceSet": "face",
    "VRoid/EyeSet": "eyes", "VRoid/EyeballSet": "eyeball", "VRoid/Body": "body",
    "Attachment": "attachment",
}

# Small palette used to turn dominant RGB clusters into searchable words.
COLORS = [
    ("black", (20, 20, 20)), ("white", (242, 242, 242)), ("gray", (128, 128, 128)),
    ("beige", (220, 200, 170)), ("brown", (120, 78, 50)), ("red", (190, 45, 45)),
    ("orange", (225, 130, 40)), ("yellow", (225, 205, 60)), ("green", (55, 145, 75)),
    ("blue", (50, 95, 190)), ("purple", (125, 70, 165)), ("pink", (225, 135, 175)),
    ("cyan", (55, 175, 190)),
]


def _iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _short(text, limit=90):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _base(entry):
    custom = entry.get("kind") == "custom"
    if custom:
        return _short(entry.get("name") or entry.get("number") or "Custom item")
    category = entry.get("category") or ""
    base = CATEGORY_LABELS.get(category) or category.split("/")[-1] or entry.get("slot") or "Preset"
    number = str(entry.get("number") or "").strip()
    return _short((base + (" " + number if number else "")).strip())


def _color_name(rgb):
    r, g, b = (float(x) for x in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    sat = 0 if mx == 0 else (mx - mn) / mx
    if sat < 0.12:
        if mx >= 205:
            return "white"
        if mx <= 55:
            return "black"
        return "gray"
    best, dist = None, None
    for name, ref in COLORS:
        d = sum((a - b) ** 2 for a, b in zip((r, g, b), ref))
        if dist is None or d < dist:
            best, dist = name, d
    return best


def analyze_thumbnail(path, category=None):
    """Return {colors, brightness, pattern, confidence, background} or None if unreadable.

    The crop is category-aware: a hair thumbnail must not be labelled "beige" because the
    neck/skin dominates, and a shoe thumbnail must not be labelled from the legs.
    """
    if not path or not os.path.exists(path):
        return None
    try:
        import numpy as np
        from PIL import Image, ImageFilter
    except Exception:
        return None
    try:
        with Image.open(path).convert("RGB") as im:
            w, h = im.size
            cat = (category or "").lower()
            if cat.startswith("hair") or cat in ("custom/allhair", "custom/hairfront", "custom/hairback"):
                if "allhair" in cat or "tied" in cat or "hairset" in cat:
                    box = (int(w * 0.25), int(h * 0.02), int(w * 0.75), int(h * 0.62))
                else:
                    box = (int(w * 0.28), int(h * 0.02), int(w * 0.72), int(h * 0.38))
            elif cat.startswith("face") or cat.startswith("overlay") or "faceset" in cat or "ey" in cat:
                box = (int(w * 0.32), int(h * 0.02), int(w * 0.68), int(h * 0.30))
            elif "shoes" in cat:
                box = (int(w * 0.24), int(h * 0.55), int(w * 0.76), int(h * 0.99))
            elif "socks" in cat:
                box = (int(w * 0.24), int(h * 0.42), int(w * 0.76), int(h * 0.99))
            elif "bottoms" in cat or "innerbottom" in cat:
                box = (int(w * 0.24), int(h * 0.32), int(w * 0.76), int(h * 0.88))
            elif "tops" in cat or "innertop" in cat:
                box = (int(w * 0.22), int(h * 0.08), int(w * 0.78), int(h * 0.66))
            else:
                # Full outfit / onepiece / unknown: central frame, skip hands and background.
                box = (int(w * 0.18), int(h * 0.08), int(w * 0.82), int(h * 0.95))
            im = im.crop(box).resize((96, 96))
            a = np.asarray(im).astype(float)
            # Background = median of the four corners; mask it out.
            c = 8
            corners = np.concatenate([
                a[:c, :c].reshape(-1, 3), a[:c, -c:].reshape(-1, 3),
                a[-c:, :c].reshape(-1, 3), a[-c:, -c:].reshape(-1, 3),
            ])
            bg = np.median(corners, axis=0)
            mask = np.abs(a - bg).sum(-1) > 42
            mask[:3, :] = False
            mask[-3:, :] = False
            mask[:, :3] = False
            mask[:, -3:] = False
            pixels = a[mask]
            if len(pixels) < 80:
                return None
            # Quantize moderately to group texture/shading into one colour.
            q = (pixels // 28).astype(int)
            keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
            uniq, counts = np.unique(keys, return_counts=True)
            order = counts.argsort()[::-1][:3]
            colors = []
            for idx in order:
                sel = keys == uniq[idx]
                colors.append(_color_name(pixels[sel].mean(axis=0)))
            # De-duplicate while keeping order.
            colors = list(dict.fromkeys(colors))
            brightness = float(pixels.mean() / 255.0)
            edges = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES)).astype(float) / 255.0
            edge_density = float(edges.mean())
            pattern = "patterned" if edge_density > 0.12 else "plain"
            dominant_share = float(counts[order[0]] / counts.sum()) if len(order) else 0.0
            return {
                "colors": colors[:3],
                "brightness": round(brightness, 3),
                "pattern": pattern,
                "edgeDensity": round(edge_density, 3),
                "confidence": round(min(0.65, 0.25 + 0.35 * dominant_share), 2),
                "background": [_color_name(bg)],
            }
    except Exception:
        return None


def _tag(entry):
    category = entry.get("category") or ""
    if category.startswith("Custom/"):
        category = "Clothing/" + category.split("/", 1)[1]
    return CATEGORY_TAGS.get(category) or CATEGORY_TAGS.get(category.replace("Clothing/", "")) or "preset"


def generate(entry, thumbnail_path=None):
    """Build label + generated metadata for one cache entry."""
    label = _base(entry)
    data = {
        "version": 1,
        "method": "structural",
        "at": _iso(),
        "colors": [],
        "tags": [],
    }
    visual = analyze_thumbnail(thumbnail_path, entry.get("category")) if thumbnail_path else None
    if visual:
        colors = visual["colors"]
        if colors:
            label = _short(label + " — " + ", ".join(colors[:2]))
        data.update(method="structural+thumbnail", colors=colors, visual=visual,
                    confidence=visual.get("confidence"))
        data["tags"] = list(dict.fromkeys([_tag(entry)] + colors + [visual.get("pattern", "plain")]))
    else:
        data["tags"] = [_tag(entry)]
    return {
        "label": label,
        "labelSource": "generated",
        "labelGeneratedAt": data["at"],
        "labelVersion": 1,
        "generated": data,
    }


def apply(entry, thumbnail_path=None, force=False):
    """Set generated fields unless a human label already owns the entry."""
    if entry.get("labelSource") == "manual":
        return entry
    if entry.get("label") and not force and not thumbnail_path:
        return entry
    entry.update(generate(entry, thumbnail_path))
    return entry
