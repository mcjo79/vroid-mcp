"""Génère un calque de détails de peau pour VRoid (modèle N00) : grain, pores fins, teint irrégulier, rougeurs.

Entrées : les calques de peau exportés (body_l3.png 2048², face_l3.png 1024²) dans le dossier courant.
Sorties : body_detail.png, face_detail.png, à importer comme calque par-dessus la peau.
Positions UV mesurées sur le corps N00 (rendu avec un calque codant U/V en teinte).
"""
import numpy as np
from PIL import Image, ImageFilter

rng = np.random.default_rng(7)

# Intensités (augmenter pour un effet plus visible)
GRAIN = 0.02      # grain fin
PORES = 0.09      # petits points sombres (rares, 1 px)
MOTTLE_RED = 0.08 # zones rosées
MOTTLE_LIGHT = 0.06
BLUSH = 0.22      # rougeurs localisées


def field(size, sigma):
    """Bruit lissé, centré, écart-type 1."""
    im = Image.fromarray((rng.random((size, size)) * 255).astype(np.uint8))
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(sigma)), dtype=np.float32)
    a -= a.mean()
    return a / (a.std() + 1e-6)


def blob(size, cx, cy, rx, ry):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    return np.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))


def band(size, u0, u1, cy, ry):
    """Bande horizontale (tout le tour d'un membre) entre u0 et u1."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    inside = ((x >= u0) & (x <= u1)).astype(np.float32)
    return inside * np.exp(-((y - cy) / ry) ** 2)


def make(src, out, blush=None):
    base = np.asarray(Image.open(src).convert("RGBA"), dtype=np.float32) / 255
    n = base.shape[0]
    s = n / 1024
    mask = (base[..., 3] > 0.5).astype(np.float32)
    mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)), dtype=np.float32) / 255

    mott = 0.6 * field(n, 40 * s) + 0.4 * field(n, 12 * s)
    grain = field(n, 0.7)
    pores = np.clip(field(n, 0.6) - 2.0, 0, None)

    red = np.clip(mott, 0, None) * MOTTLE_RED
    light = np.clip(-mott, 0, None) * MOTTLE_LIGHT
    dark = np.abs(grain) * GRAIN + pores * PORES
    if blush is not None:
        red = red + blush * BLUSH

    col_red, col_light, col_dark = np.array([0.88, 0.42, 0.40]), np.array([1.0, 0.97, 0.93]), np.array([0.55, 0.33, 0.27])
    wsum = red + light + dark + 1e-6
    rgb = (red[..., None] * col_red + light[..., None] * col_light + dark[..., None] * col_dark) / wsum[..., None]
    alpha = np.clip(wsum, 0, 0.5) * mask
    Image.fromarray((np.clip(np.dstack([rgb, alpha]), 0, 1) * 255).astype(np.uint8), "RGBA").save(out)
    print(out, "alpha moyen", round(float(alpha[mask > 0].mean()), 3))


# Corps (2048²) : colonnes des bras à gauche (u 0-480) et à droite (u 1568-2048), épaule en haut, poignet vers v≈950 ;
# jambes en dessous (genou avant vers v≈1490, u≈350 et u≈1690) ; doigts en bas (u 480-780 et 1270-1570, v≥1460).
n = 2048
b = 0.55 * (band(n, 0, 480, 500, 70) + band(n, 1568, 2048, 500, 70))          # coudes
b += blob(n, 350, 1490, 120, 95) + blob(n, 1690, 1490, 120, 95)                # genoux
fingers = np.zeros((n, n), np.float32)
fingers[1460:, 480:780] = 1
fingers[1460:, 1270:1570] = 1
b += 0.6 * np.asarray(Image.fromarray((fingers * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12)), np.float32) / 255
make("body_l3.png", "body_detail.png", blush=np.clip(b, 0, 1))

# Visage (1024²) : joues et bout du nez.
n = 1024
f = blob(n, 330, 690, 95, 60) + blob(n, 694, 690, 95, 60) + 0.7 * blob(n, 512, 640, 40, 35)
make("face_l3.png", "face_detail.png", blush=np.clip(f, 0, 1))
