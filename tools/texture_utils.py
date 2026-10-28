"""Aides pour éditer les textures de VRoid via le pont HTTP (plugin VRoidMcpBridge).

export / imp : exporter et réimporter un calque ; ramp_recolor : remappe la luminosité sur une rampe de couleurs
(voir docs/TEXTURES.md) ; shot : capture de VRoid (PNG + aperçu JPG). Fichiers écrits dans le dossier courant.
"""
import json, os, time, urllib.request
import numpy as np
from PIL import Image
B = "http://127.0.0.1:7811"
S = os.path.abspath(os.getcwd())
def post(path, body, timeout=120):
    r = urllib.request.Request(B + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(r, timeout=timeout))
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")
def get(path):
    return json.load(urllib.request.urlopen(B + path, timeout=120))
def export(t, img, node, name):
    p = os.path.join(S, name); post("/export_layer", {"transferable": t, "image": img, "node": node, "path": p}); return p
def ramp_recolor(src, dst, stops, lo=0.05, hi=0.70, mask=None):
    """Remappe la luminosité sur une rampe de couleurs [(t,r,g,b),...]."""
    a = np.asarray(Image.open(src).convert("RGBA")).astype(float) / 255
    st = np.array(stops)
    lum = a[..., :3] @ [0.299, 0.587, 0.114]
    t = np.clip((lum - lo) / (hi - lo), 0, 1)
    rgb = np.stack([np.interp(t, st[:, 0], st[:, k]) for k in (1, 2, 3)], -1)
    out = a.copy()
    sel = np.ones(a.shape[:2], bool) if mask is None else mask
    out[sel, :3] = rgb[sel]
    Image.fromarray((out * 255).round().astype(np.uint8), "RGBA").save(dst)
    return dst
def imp(t, img, node, path):
    return post("/import_layer", {"transferable": t, "image": img, "node": node, "path": path})
def shot(name, wait=3):
    time.sleep(wait); p = os.path.join(S, name + ".png"); post("/screenshot", {"path": p})
    Image.open(p).convert("RGB").resize((1271, 675)).save(os.path.join(S, name + ".jpg"), quality=85); return p
