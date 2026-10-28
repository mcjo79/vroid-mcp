"""Cache normalisé des presets VRoid, partageable entre IA (et entre sessions).

Disposition sur disque (par défaut D:\\divers\\vroid\\preset_cache, ou variable VROID_PRESET_CACHE) :
    catalog.json                  catalogue normalisé (voir SCHEMA ci-dessous)
    thumbs/<Partie>_<Categorie>/<numero>.jpg   vignettes, recadrées sur la zone utile de la catégorie

Principes :
- Clé stable = chemin de ressource (pixiv/VRoid/<Partie>/<Categorie>/N00/<numero>/...), l'id VRoid est gardé à côté.
- Les annotations (description, tags, couleurs...) viennent de n'importe quelle IA ou d'un humain, avec auteur et
  date ; une synchro de la liste des presets ne les efface jamais.
- Écritures atomiques (fichier temporaire puis remplacement) et verrou par fichier pour les accès concurrents.
"""
import datetime
import hashlib
import json
import os
import tempfile
import time

SCHEMA_VERSION = 1
SCHEMA = {
    "schema": SCHEMA_VERSION,
    "source": {"app": "VRoid Studio", "unity": "version Unity", "presetFingerprint": "sha1 des chemins de ressource"},
    "updated": "date ISO de la dernière écriture",
    "presets": {
        "<resource>": {
            "id": "id VRoid (transferableGroupId)",
            "resource": "chemin de ressource (clé)",
            "category": "<Partie>/<Categorie>, ex. Clothing/Tops, Hair/Front, Overlay/Lip",
            "slot": "emplacement remplacé (type de groupe), ex. Tops, HairFront, Lip",
            "number": "numéro dans la catégorie (texte, ex. '013' ou 'Initial_001')",
            "usable": "gratuit ou possédé",
            "price": "prix en pièces",
            "thumbnail": "chemin relatif de la vignette ou null",
            "description": "texte libre court, en français ou en anglais",
            "tags": ["mots-clés en minuscules : type, couleur, longueur, style..."],
            "colors": ["couleurs dominantes en mots simples"],
            "annotations": [{"author": "qui", "date": "quand", "fields": ["champs modifiés"]}],
        }
    },
}

ROOT = os.environ.get("VROID_PRESET_CACHE") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preset_cache")
CATALOG = os.path.join(ROOT, "catalog.json")
LOCK = CATALOG + ".lock"

# Zone utile de chaque catégorie dans la silhouette du modèle (fractions de la hauteur, de haut en bas)
# et demi-largeur autour de l'axe (fraction de la hauteur ; None = toute la largeur, bras compris).
REGIONS = {
    "Clothing/Tops": (0.12, 0.62, None), "Clothing/Onepiece": (0.12, 0.85, None),
    "VRoid/ClothingSet": (0.0, 1.0, None), "Clothing/InnerTop": (0.12, 0.45, 0.2),
    "Clothing/Bottoms": (0.40, 0.80, 0.22), "Clothing/InnerBottom": (0.40, 0.65, 0.22),
    "Clothing/Socks": (0.50, 1.0, 0.22), "Clothing/Shoes": (0.80, 1.0, 0.22),
    "Clothing/AccessoryNeck": (0.10, 0.35, 0.18), "Clothing/AccessoryArm": (0.15, 0.50, None),
    "Attachment": (0.0, 0.40, 0.25), "Hair": (0.0, 0.32, 0.20), "Hair/AllHair": (0.0, 0.75, 0.30), "Hair/Back": (0.0, 0.75, 0.30),
    "Hair/Tied": (0.0, 0.75, 0.30), "VRoid/HairSet": (0.0, 0.75, 0.30), "VRoid/Body": (0.0, 1.0, None),
    "Face": (0.02, 0.20, 0.12), "Overlay": (0.02, 0.20, 0.12), "VRoid/FaceSet": (0.02, 0.20, 0.12),
    "VRoid/EyeSet": (0.06, 0.16, 0.10), "VRoid/EyeballSet": (0.06, 0.16, 0.10),
}


def region_for(category):
    if category in REGIONS:
        return REGIONS[category]
    part = category.split("/")[0]
    return REGIONS.get(part, (0.0, 1.0, None))


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def category_of(resource):
    """(catégorie, numéro). Les cheveux ont une sous-partie après N00 :
    pixiv/VRoid/Hair/N00/Front/012/... -> ('Hair/Front', '012')."""
    parts = resource.split("/")
    if "N00" in parts:
        i = parts.index("N00")
        if parts[i - 1] == "Hair" and i + 2 < len(parts):
            return "Hair/" + parts[i + 1], parts[i + 2]
        return parts[i - 2] + "/" + parts[i - 1], parts[i + 1] if i + 1 < len(parts) else ""
    return (parts[2] + "/" + parts[3] if len(parts) > 3 else resource), ""


def slot_of(resource):
    """Emplacement remplacé dans le modèle, d'après le type de groupe en fin de chemin
    (ex. HairFront, Lip, Ear, Tops ; un preset de corps 'VRoid/Body' a un fichier par partie)."""
    last = resource.rsplit("/", 1)[-1]
    if last.startswith("TransferableGroupType.") and last.endswith(".transferablegroup"):
        return last[len("TransferableGroupType."):-len(".transferablegroup")].split(".")[-1]
    return None


class _Lock:
    """Verrou par fichier (création exclusive), suffisant pour quelques IA sur la même machine."""

    def __enter__(self):
        os.makedirs(ROOT, exist_ok=True)
        for _ in range(200):
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.time() - os.path.getmtime(LOCK) > 60:  # verrou abandonné
                    os.remove(LOCK)
                time.sleep(0.05)
        raise TimeoutError("cache des presets verrouillé")

    def __exit__(self, *a):
        os.close(self.fd)
        os.remove(LOCK)


def load():
    try:
        with open(CATALOG, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {"schema": SCHEMA_VERSION, "source": {}, "updated": None, "presets": {}}


def _save(cat):
    cat["updated"] = now()
    os.makedirs(ROOT, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=ROOT, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, CATALOG)


def sync(presets, unity_version=None):
    """Fusionne la liste vivante (/presets) dans le cache sans toucher aux annotations."""
    with _Lock():
        cat = load()
        added = 0
        for p in presets:
            res = p["resource"]
            e = cat["presets"].get(res)
            if e is None:
                cat_, num = category_of(res)
                e = {"resource": res, "category": cat_, "number": num, "thumbnail": None,
                     "description": "", "tags": [], "colors": [], "annotations": []}
                cat["presets"][res] = e
                added += 1
            e.update(id=p["id"], usable=p.get("usable", True), price=p.get("price", 0))
        # Recalcule les champs dérivés du chemin pour toutes les entrées (migration sans perte d'annotations).
        for res, e in cat["presets"].items():
            e["category"], e["number"] = category_of(res)
            e["slot"] = slot_of(res)
        fp = hashlib.sha1("\n".join(sorted(cat["presets"])).encode()).hexdigest()[:12]
        cat["source"] = {"app": "VRoid Studio", "unity": unity_version or cat["source"].get("unity"),
                         "presetFingerprint": fp}
        _save(cat)
        return {"total": len(cat["presets"]), "added": added, "fingerprint": fp}


def annotate(key, author, description=None, tags=None, colors=None, replace=False):
    """key = chemin de ressource ou id VRoid. tags/colors sont ajoutés (ou remplacés si replace)."""
    with _Lock():
        cat = load()
        e = _find(cat, key)
        changed = []
        if description is not None:
            e["description"] = description.strip(); changed.append("description")
        for field, vals in (("tags", tags), ("colors", colors)):
            if vals:
                vals = [v.strip().lower() for v in vals if v.strip()]
                e[field] = vals if replace else sorted(set(e.get(field, [])) | set(vals))
                changed.append(field)
        if changed:
            e.setdefault("annotations", []).append({"author": author or "inconnu", "date": now(), "fields": changed})
            _save(cat)
        return e


def set_thumbnail(key, rel_path):
    with _Lock():
        cat = load()
        e = _find(cat, key)
        e["thumbnail"] = rel_path.replace("\\", "/")
        _save(cat)
        return e


def _find(cat, key):
    if key in cat["presets"]:
        return cat["presets"][key]
    for e in cat["presets"].values():
        if e.get("id") == key:
            return e
    raise KeyError(f"preset absent du cache : {key} (lancer une synchro)")


def search(query=None, category=None, usable_only=True, annotated_only=False, limit=50):
    """Recherche plein texte simple : tous les mots de la requête doivent apparaître (description, tags, couleurs,
    catégorie, numéro). Renvoie les entrées triées, les mieux annotées d'abord."""
    cat = load()
    words = [w.lower() for w in (query or "").split() if w]
    out = []
    for e in cat["presets"].values():
        if category and category.lower() not in e["category"].lower():
            continue
        if usable_only and not e.get("usable", True):
            continue
        if annotated_only and not (e.get("description") or e.get("tags")):
            continue
        hay = " ".join([e.get("description", ""), " ".join(e.get("tags", [])), " ".join(e.get("colors", [])),
                        e["category"], e.get("number", ""), e.get("slot") or ""]).lower()
        if all(w in hay for w in words):
            out.append(e)
    out.sort(key=lambda e: (-(len(e.get("tags", [])) + bool(e.get("description"))), e["category"], e.get("number", "")))
    return {"total": len(out), "cacheUpdated": cat.get("updated"), "source": cat.get("source"),
            "presets": out[:limit]}


def thumb_path(e):
    return os.path.join(ROOT, e["thumbnail"]) if e.get("thumbnail") else None


def get(key):
    return _find(load(), key)


def crop_model(png_path, category, out_path, size=256):
    """Recadre une capture sur la zone utile de la catégorie, d'après la silhouette du modèle."""
    import numpy as np
    from PIL import Image
    im = Image.open(png_path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w = a.shape[:2]
    x0, x1, y0 = int(w * 0.16), int(w * 0.87), int(h * 0.05)  # zone 3D, sans les panneaux latéraux
    view = a[y0:, x0:x1]
    bg = np.median(np.concatenate([view[:20, :20].reshape(-1, 3), view[:20, -20:].reshape(-1, 3)]), axis=0)
    mask = np.abs(view - bg).sum(-1) > 45
    blue = (view[..., 2] > 200) & (view[..., 0] < 120)  # barre de taille de l'onglet Corps
    mask &= ~blue
    ys, xs = np.where(mask)
    if len(ys) == 0:
        raise RuntimeError("modèle introuvable dans la capture")
    top, bot = ys.min(), ys.max()
    H = bot - top
    cx = int(np.median(xs))
    f0, f1, half = region_for(category)
    ry0, ry1 = top + int(f0 * H), top + int(f1 * H)
    if half is None:
        rx0, rx1 = xs.min(), xs.max()
    else:
        rx0, rx1 = cx - int(half * H), cx + int(half * H)
    crop = im.crop((x0 + rx0, y0 + ry0, x0 + rx1, y0 + ry1))
    crop.thumbnail((size, size))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    crop.save(out_path, quality=85)
    return out_path


def thumb_rel(e):
    return f"thumbs/{e['category'].replace('/', '_')}/{e.get('number') or e['id'][:12]}.jpg"
