"""Planche de contact des coiffures VRoid (HairSet) via le pont MCP.

Applique chaque preset HairSet, capture la fenêtre, découpe le personnage et assemble
une planche numérotée pour choisir visuellement.
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
OUT = os.path.join(ROOT, "out", "hairsets")
CROP = (840, 470, 1760, 1351)  # personnage, hors panneaux UI
TILE_W = 220


def grab(client):
    """Récupère une capture et renvoie une image PIL (avec reprises)."""
    import base64
    last = None
    for attempt in range(4):
        res = client.call("vroid_screenshot")
        for item in res.get("content") or []:
            if item.get("type") == "image":
                return Image.open(io.BytesIO(base64.b64decode(item["data"]))).convert("RGB")
        last = res
        time.sleep(0.5)
    raise RuntimeError(f"pas d'image : {last}")


def call_json(client, name, args=None):
    """Appelle un outil MCP et renvoie l'objet JSON contenu dans le texte."""
    res = client.call(name, args or {})
    for item in res.get("content") or []:
        if item.get("type") == "text":
            return json.loads(item["text"])
    raise RuntimeError(f"réponse sans texte : {res}")


def main():
    os.makedirs(OUT, exist_ok=True)
    client = Client()
    try:
        presets = call_json(client, "vroid_list_presets", {"filter": "HairSet", "limit": 400})
        sets = [p for p in presets["presets"] if p["category"] == "VRoid/HairSet"]
        sets.sort(key=lambda p: int(re.search(r"/(\d+)/", p["resource"]).group(1)))
        print(f"{len(sets)} coiffures", flush=True)
        tiles = []
        for p in sets:
            num = re.search(r"/(\d+)/", p["resource"]).group(1)
            path = os.path.join(OUT, f"hairset_{num}.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGB")
                tiles.append((num, img))
                continue
            client.call("vroid_apply_preset", {"id": p["id"]})
            time.sleep(0.35)
            img = grab(client).crop(CROP)
            img = img.resize((TILE_W, int(TILE_W * img.height / img.width)), Image.LANCZOS)
            img.save(path)
            tiles.append((num, img))
            print("ok", num, flush=True)
        cols = 6
        tw, th = TILE_W, tiles[0][1].height + 22
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), "white")
        d = ImageDraw.Draw(sheet)
        for i, (num, img) in enumerate(tiles):
            x, y = (i % cols) * tw, (i // cols) * th
            sheet.paste(img, (x, y + 22))
            d.text((x + 6, y + 4), num, fill="black")
        path = os.path.join(ROOT, "out", "hairset_sheet.jpg")
        sheet.save(path, quality=90)
        print("PLANCHE", path, sheet.size)
    finally:
        client.close()


if __name__ == "__main__":
    main()
