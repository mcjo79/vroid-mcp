"""Planche de contact générique d'une catégorie de presets VRoid via le pont MCP.

Usage :
  python tools/preset_sheet.py <filtre> <categorie> <nom> [--crop x1,y1,x2,y2]
Ex. :
  python tools/preset_sheet.py AllHair VRoid/Hair allhair
  python tools/preset_sheet.py Clothing/Onepiece Clothing/Onepiece onepiece
"""
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import Client  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CROP = (840, 470, 1760, 1351)
TILE_W = 220


def call_json(client, name, args=None):
    res = client.call(name, args or {})
    for item in res.get("content") or []:
        if item.get("type") == "text":
            return json.loads(item["text"])
    raise RuntimeError(f"réponse sans texte : {res}")


def grab(client):
    import base64
    last = None
    for _ in range(4):
        res = client.call("vroid_screenshot")
        for item in res.get("content") or []:
            if item.get("type") == "image":
                return Image.open(io.BytesIO(base64.b64decode(item["data"]))).convert("RGB")
        last = res
        time.sleep(0.5)
    raise RuntimeError(f"pas d'image : {last}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    crop = list(CROP)
    for a in sys.argv[1:]:
        if a.startswith("--crop"):
            crop = [int(v) for v in a.split("=", 1)[1].split(",")]
    filt, category, name = args[0], args[1], args[2]
    outdir = os.path.join(ROOT, "out", "parts", name)
    os.makedirs(outdir, exist_ok=True)
    client = Client()
    try:
        data = call_json(client, "vroid_list_presets", {"filter": filt, "limit": 500})
        items = [p for p in data["presets"] if p["category"] == category]
        items.sort(key=lambda p: p["resource"])
        print(f"{len(items)} presets {category}", flush=True)
        tiles = []
        for i, p in enumerate(items):
            m = re.search(r"/(\d+)/", p["resource"])
            num = m.group(1) if m else f"{i:03d}"
            path = os.path.join(outdir, f"{num}.png")
            if not os.path.exists(path):
                client.call("vroid_apply_preset", {"id": p["id"]})
                time.sleep(0.35)
                img = grab(client).crop(tuple(crop))
                img = img.resize((TILE_W, int(TILE_W * img.height / img.width)), Image.LANCZOS)
                img.save(path)
                print("ok", num, flush=True)
            else:
                img = Image.open(path).convert("RGB")
            tiles.append((num, img))
        cols = 6
        tw, th = TILE_W, tiles[0][1].height + 22
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "white")
        d = ImageDraw.Draw(sheet)
        for i, (num, img) in enumerate(tiles):
            x, y = (i % cols) * tw, (i // cols) * th
            sheet.paste(img, (x, y + 22))
            d.text((x + 6, y + 4), num, fill="black")
        out = os.path.join(ROOT, "out", f"{name}_sheet.jpg")
        sheet.save(out, quality=90)
        print("PLANCHE", out, sheet.size)
    finally:
        client.close()


if __name__ == "__main__":
    main()
