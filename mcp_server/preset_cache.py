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

import labeler

SCHEMA_VERSION = 1
SCHEMA = {
    "schema": SCHEMA_VERSION,
    "source": {"app": "VRoid Studio", "unity": "version Unity", "presetFingerprint": "sha1 des clés présentes",
               "session": "date de lancement du plugin au dernier scan", "lastScan": "date du dernier scan"},
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
            "kind": "preset (intégré) ou custom (objet personnalisé de l'utilisateur, clé 'custom:<ressource>')",
            "name": "custom : nom donné dans VRoid, relu à chaque scan",
            "status": "new | changed (custom renommé ou nouvelle révision) | absent si déjà vu",
            "removed": "true si absent de VRoid au dernier scan (annotations conservées)",
            "firstSeen / lastSeen": "dates de scan",
            "thumbnail": "chemin relatif de la vignette en situation (capture recadrée) ou null",
            "thumbnailKind / thumbnailAt": "type de vignette (situation) et date de génération",
            "thumbnailMeta": {
                "kind": "situation",
                "mannequin": "neutral (sans vêtements, sous-vêtements ni cheveux, sauf pièce testée)",
                "clothing": "tested-item-only",
                "underwear": "removed",
                "hair": "removed-except-base",
                "keptSlot": "emplacement conservé pendant la capture",
                "strippedSlots / underwearRemoved / hairRemoved": "listes de ce qui a été retiré",
                "camera": "cadrage utilisé (dont yaw)", "orientation": "front|profile|back|three-quarter",
                "pixels": "[largeur, hauteur]",
                "bytes / sha1": "taille et empreinte du fichier",
                "capturedAt / source": "date et origine de la capture"
            },
            "icon": "chemin relatif de l'icône native de VRoid (presets intégrés) ou null",
            "iconKind / iconAt": "icône native et date de récupération",
            "label": "libellé lisible (généré au scan/build, ou manuel)",
            "labelSource": "generated | manual",
            "labelGeneratedAt / labelVersion": "date et version du générateur de label",
            "generated": {
                "version": 1,
                "method": "structural | structural+thumbnail",
                "at": "date ISO",
                "colors": ["couleurs dominantes déduites de la vignette"],
                "tags": ["type + couleurs + plain|patterned"],
                "confidence": "0..1, faible par construction",
                "visual": {"colors": [], "brightness": "0..1", "pattern": "plain|patterned",
                           "edgeDensity": "0..1", "background": []}
            },
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


# Objets personnalisés : même zone que la catégorie de presets équivalente.
CUSTOM_EQUIV = {
    "Tops": "Clothing/Tops", "Bottoms": "Clothing/Bottoms", "Onepiece": "Clothing/Onepiece",
    "Socks": "Clothing/Socks", "Shoes": "Clothing/Shoes", "InnerTop": "Clothing/InnerTop",
    "InnerBottom": "Clothing/InnerBottom", "ArmAccessory": "Clothing/AccessoryArm",
    "NeckAccessory": "Clothing/AccessoryNeck", "AllHair": "Hair/AllHair", "HairFront": "Hair",
    "HairBack": "Hair/Back", "BaseHair": "Hair", "BodySkin": "VRoid/Body",
}


FRAMING_PATH = os.environ.get("VROID_FRAMING_CONFIG") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "framing.json")
FRAMING_OVERRIDES = os.environ.get("VROID_FRAMING_OVERRIDES") or os.path.join(ROOT, "framing_overrides.json")


def _default_framing_entry(key):
    base = REGIONS.get(key)
    if base is None:
        base = REGIONS.get(key.split("/")[0], (0.0, 1.0, None))
    top, bottom, half = base
    return {"top": top, "bottom": bottom, "half": half, "yaw": 0.0,
            "distance": 4.2 if key == "VRoid/ClothingSet" else 3.3,
            "fit": "full-body" if key in ("VRoid/ClothingSet", "VRoid/Body") else "region"}


def _framing_entry(entry, key):
    """Normalise une entrée JSON (dict, ou ancien triplet [top, bottom, half])."""
    if isinstance(entry, (list, tuple)) and len(entry) >= 3:
        return {"top": float(entry[0]), "bottom": float(entry[1]), "half": entry[2], "yaw": 0.0,
                "distance": 4.2 if key == "VRoid/ClothingSet" else 3.3,
                "fit": "full-body" if key in ("VRoid/ClothingSet", "VRoid/Body") else "region"}
    e = dict(entry or {})
    return {
        "top": float(e.get("top", 0.0)),
        "bottom": float(e.get("bottom", 1.0)),
        "half": e.get("half"),
        "distance": float(e.get("distance", 3.3)),
        "yaw": float(e.get("yaw", 0.0)),
        "fit": e.get("fit") or "region",
    }


def load_framing():
    """Charge les defaults commités (config/framing.json) et les overrides locaux.
    En cas d'absence des defaults, les valeurs de secours restent dans REGIONS."""
    try:
        with open(FRAMING_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    defaults = cfg.get("defaults") if isinstance(cfg.get("defaults"), dict) else {}
    # Les overrides sont locaux (preset_cache/framing_overrides.json) : une mise à jour
    # du paquet peut remplacer config/framing.json sans perdre les réglages de l'IA.
    overrides = {}
    try:
        with open(FRAMING_OVERRIDES, encoding="utf-8") as f:
            ov = json.load(f)
        if isinstance(ov.get("overrides"), dict):
            overrides.update(ov["overrides"])
    except (OSError, ValueError):
        pass
    return {"version": cfg.get("version", 1), "defaults": defaults, "overrides": overrides}


def _save_framing(cfg):
    """Écrit uniquement les overrides locaux, jamais les defaults commités."""
    os.makedirs(os.path.dirname(FRAMING_OVERRIDES), exist_ok=True)
    data = {"version": cfg.get("version", 1), "updated": now(),
            "comment": "Overrides de cadrage locaux ; defaults dans config/framing.json.",
            "overrides": cfg.get("overrides", {})}
    tmp = FRAMING_OVERRIDES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, FRAMING_OVERRIDES)


def _framing_key(category, strict=False):
    """Clé de cadrage = catégorie / partie du corps, jamais un preset individuel.
    Custom/<slot> est ramené à la catégorie de preset équivalente."""
    cfg = load_framing()
    known = set(REGIONS) | set(cfg["defaults"])
    if category in known:
        return category
    if category.startswith("Custom/"):
        slot = category.split("/", 1)[1]
        if slot in CUSTOM_EQUIV:
            return CUSTOM_EQUIV[slot]
    part = category.split("/")[0]
    if part in known:
        return part
    if strict:
        raise ValueError(
            f"clé de cadrage invalide : {category!r}. Utiliser une catégorie/partie du corps "
            "(ex. Clothing/Tops, Clothing/Shoes, Hair, Face, VRoid/ClothingSet), pas un preset individuel ; "
            "les informations par vêtement restent dans le cache.")
    return category


def framing_for(category):
    """Cadrage effectif d'une catégorie : override IA > default du projet > fallback code."""
    cfg = load_framing()
    key = _framing_key(category)
    source = "override"
    entry = cfg["overrides"].get(key)
    if entry is None:
        source = "default"
        entry = cfg["defaults"].get(key)
    if entry is None:
        source = "fallback"
        entry = _default_framing_entry(key)
    f = _framing_entry(entry, key)
    f.update({"category": category, "profileKey": key, "source": source})
    return f


def framing_all():
    cfg = load_framing()
    keys = sorted(set(cfg["defaults"]) | set(cfg["overrides"]))
    return {k: framing_for(k) for k in keys}


def framing_get(category=None):
    cfg = load_framing()
    if category:
        key = _framing_key(category, strict=True)
        default = cfg["defaults"].get(key) or _default_framing_entry(key)
        override = cfg["overrides"].get(key)
        return {
            "category": category,
            "profileKey": key,
            "effective": framing_for(category),
            "default": _framing_entry(default, key),
            "override": _framing_entry(override, key) if override else None,
        }
    return {
        "defaults": {k: _framing_entry(v, k) for k, v in cfg["defaults"].items()},
        "overrides": {k: _framing_entry(v, k) for k, v in cfg["overrides"].items()},
        "effective": framing_all(),
    }


def set_framing(category, updates):
    """Écrit un override local par catégorie/partie du corps ; les defaults ne sont pas modifiés."""
    key = _framing_key(category, strict=True)
    cfg = load_framing()
    current = cfg["overrides"].get(key) or cfg["defaults"].get(key) or _default_framing_entry(key)
    merged = _framing_entry(current, key)
    for name in ("top", "bottom", "half", "distance", "yaw", "fit"):
        if name not in updates:
            continue
        if name == "half" and updates[name] is None:
            merged["half"] = None
        elif updates[name] is not None:
            merged[name] = updates[name]
    merged["top"] = float(merged["top"])
    merged["bottom"] = float(merged["bottom"])
    if merged["half"] is not None:
        merged["half"] = float(merged["half"])
    merged["distance"] = float(merged["distance"])
    merged["yaw"] = float(merged["yaw"])
    if not (0 <= merged["top"] < merged["bottom"] <= 1):
        raise ValueError("top/bottom doivent vérifier 0 <= top < bottom <= 1")
    if merged["half"] is not None and not (0.01 <= merged["half"] <= 1):
        raise ValueError("half doit être null ou dans 0.01..1")
    if not (1 <= merged["distance"] <= 10):
        raise ValueError("distance doit être dans 1..10")
    if not (-180 <= merged["yaw"] <= 180):
        raise ValueError("yaw doit être dans -180..180 (0 = face, 90 = profil, 180 = dos)")
    if merged["fit"] not in ("region", "full-body"):
        raise ValueError("fit doit être region ou full-body")
    cfg["overrides"][key] = merged
    _save_framing(cfg)
    return framing_get(category)


def reset_framing(category=None):
    """Efface les overrides (tous, ou une catégorie) : retour aux defaults commités."""
    cfg = load_framing()
    if category:
        key = _framing_key(category, strict=True)
        cfg["overrides"].pop(key, None)
    else:
        cfg["overrides"] = {}
    _save_framing(cfg)
    return framing_get(category) if category else framing_get()


def region_for(category):
    f = framing_for(category)
    return f["top"], f["bottom"], f["half"]


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


def _new_entry(key, **kw):
    e = {"resource": key, "thumbnail": None, "icon": None, "description": "", "tags": [], "colors": [],
         "annotations": [], "firstSeen": now()}
    e.update(kw)
    return e


def scan(presets, customs=None, unity_version=None, session=None, customs_known=True):
    """Compare ce que VRoid propose maintenant (presets intégrés + objets personnalisés) avec le cache.

    - nouveau  : entrée créée (status "new") ;
    - modifié  : objet personnalisé renommé ou nouvelle révision (status "changed", vignette effacée) ;
    - retiré   : absent de VRoid (removed=true, annotations conservées ; réapparaît tel quel s'il revient).
    Les noms des objets personnalisés sont relus à chaque scan (ce sont ceux de l'utilisateur dans VRoid).
    Les presets intégrés n'ont pas de nom dans VRoid : leur description vient des annotations.

    customs_known=False signifie « la liste des objets personnalisés n'a pas pu être lue » :
    les objets déjà en cache sont alors laissés intacts au lieu d'être marqués retirés.
    """
    with _Lock():
        cat = load()
        seen, new, changed, back = set(), [], [], []
        for p in presets:
            key = p["resource"]
            seen.add(key)
            e = cat["presets"].get(key)
            if e is None:
                e = cat["presets"][key] = _new_entry(key, kind="preset", status="new")
                new.append(key)
            elif e.get("removed"):
                back.append(key)
            e.update(id=p["id"], usable=p.get("usable", True), price=p.get("price", 0), kind="preset", removed=False,
                     lastSeen=now())
        for c in customs or []:
            # Clé : ressource de l'objet + nom de son fichier (deux copies enregistrées d'un même objet coexistent).
            base = c.get("customItemResource") or c.get("resource") or ""
            fname = os.path.basename((c.get("file") or "").replace("\\", "/"))
            key = "custom:" + base + "#" + fname
            seen.add(key)
            short = (c.get("type") or "").split(".")[-1]
            e = cat["presets"].get(key)
            if e is None:
                e = cat["presets"][key] = _new_entry(key, kind="custom", status="new")
                new.append(key)
            else:
                if e.get("removed"):
                    back.append(key)
                if (e.get("revision"), e.get("name")) != (c.get("revision"), c.get("name")):
                    e.setdefault("history", []).append({"date": now(), "name": e.get("name"), "revision": e.get("revision")})
                    e["status"] = "changed"
                    e["thumbnail"] = None
                    changed.append(key)
            e.update(kind="custom", removed=False, lastSeen=now(), name=c.get("name"), id=c.get("id"),
                     revision=c.get("revision"), file=c.get("file"), registered=c.get("registered"),
                     category="Custom/" + short, number=c.get("name") or "", slot=short, usable=True, price=0,
                     groupResource=c.get("resource"))
            if not e.get("icon") or key in changed or not os.path.exists(os.path.join(ROOT, e["icon"])):
                e["icon"] = extract_custom_icon(e)
        for key in [k for k, e in cat["presets"].items()
                    if e.get("kind") == "custom" and "#" not in k and not e.get("annotations")]:
            del cat["presets"][key]
        removed = []
        for key, e in cat["presets"].items():
            if key not in seen and not e.get("removed"):
                if e.get("kind") == "custom" and not customs_known:
                    # Liste illisible : ne pas conclure que l'objet a disparu.
                    continue
                e["removed"] = True
                e["removedSince"] = now()
                removed.append(key)
            if e.get("kind", "preset") == "preset":
                e["category"], e["number"] = category_of(key)
                e["slot"] = slot_of(key)
            # Structural label immediately; when a thumbnail already exists, upgrade the
            # label with visual metadata (colors/brightness/pattern) during the same sync.
            if e.get("labelSource") != "manual":
                thumb = e.get("thumbnail")
                thumb_path = os.path.join(ROOT, thumb) if thumb else None
                has_visual = bool((e.get("generated") or {}).get("visual"))
                if thumb_path and os.path.exists(thumb_path) and not has_visual:
                    labeler.apply(e, thumb_path, force=True)
                elif not e.get("label") or key in changed:
                    labeler.apply(e, force=key in changed and not thumb)
        live = sorted(k for k, e in cat["presets"].items() if not e.get("removed"))
        fp = hashlib.sha1("\n".join(live).encode()).hexdigest()[:12]
        cat["source"] = {"app": "VRoid Studio", "unity": unity_version or cat.get("source", {}).get("unity"),
                         "presetFingerprint": fp, "session": session or cat.get("source", {}).get("session"),
                         "lastScan": now()}
        _save(cat)
        return {"total": len(live), "presets": len(presets), "customs": len(customs or []), "new": len(new),
                "changed": changed, "removed": removed, "returned": back, "fingerprint": fp,
                "newSample": new[:20]}


def sync(presets, unity_version=None):
    """Compatibilité : scan des seuls presets intégrés."""
    return scan(presets, None, unity_version)


def set_field(key, field, value):
    with _Lock():
        cat = load()
        _find(cat, key)[field] = value
        _save(cat)


def set_icon(key, rel_path):
    with _Lock():
        cat = load()
        e = _find(cat, key)
        e["icon"] = rel_path.replace("\\", "/")
        e["iconKind"] = "native"
        e["iconAt"] = now()
        _save(cat)
        return e


def annotate(key, author, description=None, tags=None, colors=None, replace=False, label=None):
    """key = chemin de ressource ou id VRoid. tags/colors sont ajoutés (ou remplacés si replace).
    label remplace le label généré et devient la référence humaine (labelSource=manual)."""
    with _Lock():
        cat = load()
        e = _find(cat, key)
        changed = []
        if label is not None:
            e["label"] = label.strip()
            e["labelSource"] = "manual"
            e["labelAt"] = now()
            changed.append("label")
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


def set_thumbnail(key, rel_path, meta=None):
    with _Lock():
        cat = load()
        e = _find(cat, key)
        e["thumbnail"] = rel_path.replace("\\", "/")
        e["thumbnailKind"] = "situation"
        e["thumbnailAt"] = now()
        if meta:
            e["thumbnailMeta"] = meta
        try:
            labeler.apply(e, os.path.join(ROOT, e["thumbnail"]))
        except Exception:
            pass  # a label is useful but must never make a thumbnail fail
        _save(cat)
        return e


def _find(cat, key):
    if key in cat["presets"]:
        return cat["presets"][key]
    for e in cat["presets"].values():
        if e.get("id") == key:
            return e
    raise KeyError(f"preset absent du cache : {key} (lancer une synchro)")


def search(query=None, category=None, usable_only=True, annotated_only=False, limit=50, kind=None,
           include_removed=False, status=None):
    """Recherche plein texte simple : tous les mots de la requête doivent apparaître (description, tags, couleurs,
    catégorie, numéro). Renvoie les entrées triées, les mieux annotées d'abord."""
    cat = load()
    words = [w.lower() for w in (query or "").split() if w]
    out = []
    for e in cat["presets"].values():
        if category and category.lower() not in e.get("category", "").lower():
            continue
        if kind and e.get("kind", "preset") != kind:
            continue
        if e.get("removed") and not include_removed:
            continue
        if status and e.get("status") != status:
            continue
        if usable_only and not e.get("usable", True):
            continue
        if annotated_only and not (e.get("description") or e.get("tags")):
            continue
        gen = e.get("generated") or {}
        hay = " ".join([e.get("label", ""), e.get("description", ""), " ".join(e.get("tags", [])),
                        " ".join(e.get("colors", [])), " ".join(gen.get("tags", [])),
                        " ".join(gen.get("colors", [])), e.get("category", ""), e.get("number") or "",
                        e.get("slot") or "", e.get("name") or "",
                        e.get("kind", "preset")]).lower()
        if all(w in hay for w in words):
            out.append(e)
    out.sort(key=lambda e: (-(len(e.get("tags", [])) + bool(e.get("description"))), e.get("category", ""),
                            e.get("number") or ""))
    return {"total": len(out), "cacheUpdated": cat.get("updated"), "source": cat.get("source"),
            "presets": out[:limit]}


def thumb_path(e):
    """Vignette en situation (capture recadrée) si elle existe, sinon icône native de VRoid."""
    for f in ("thumbnail", "icon"):
        if e.get(f) and os.path.exists(os.path.join(ROOT, e[f])):
            return os.path.join(ROOT, e[f])
    return None


def extract_custom_icon(e):
    """Icône d'un objet personnalisé : le fichier .vroidcustomitem est un zip qui contient thumbnails/thumbnail.png."""
    import zipfile
    f = e.get("file")
    if not f or not os.path.exists(f):
        return None
    try:
        with zipfile.ZipFile(f) as z:
            name = next((n for n in z.namelist() if n.lower().startswith("thumbnails/") and n.lower().endswith(".png")), None)
            if not name:
                return None
            data = z.read(name)
    except (zipfile.BadZipFile, OSError):
        return None
    rel = "icons/custom/" + hashlib.sha1(e["resource"].encode()).hexdigest()[:16] + ".png"
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as out:
        out.write(data)
    return rel


def icon_rel(e):
    return "icons/" + e["resource"].split("/TransferableGroupType.")[0].replace("/", "_") + ".png"


def get(key):
    return _find(load(), key)


def image_info(path):
    """Dimensions, taille et empreinte d'une vignette (pour tracer sa génération dans catalog.json)."""
    from PIL import Image
    with Image.open(path) as im:
        pixels = list(im.size)
    with open(path, "rb") as f:
        data = f.read()
    return {"pixels": pixels, "bytes": len(data), "sha1": hashlib.sha1(data).hexdigest()}


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


def crop_center(png_path, category, out_path, size=320):
    """Recadre le centre de la vue 3D (la caméra a été cadrée sur la zone de la catégorie)."""
    from PIL import Image
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    x0, x1, y0, y1 = int(w * 0.16), int(w * 0.87), int(h * 0.05), h   # vue 3D, sans les panneaux
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    ch = int((y1 - y0) * 0.92)
    _, _, half = region_for(category)
    cw = min(x1 - x0, int(ch * (1.25 if half is None else 1.0)))
    crop = im.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
    crop.thumbnail((size, size))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    crop.save(out_path, quality=88)
    return out_path


def thumb_rel(e):
    if e.get("kind") == "custom":
        # Plusieurs objets personnalisés portent souvent le même nom (« Shoes ») : nom de fichier unique.
        return f"thumbs/{e['category'].replace('/', '_')}/{hashlib.sha1(e['resource'].encode()).hexdigest()[:16]}.jpg"
    num = (e.get("number") or e.get("id") or "x")[:40]
    num = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in num)
    return f"thumbs/{e['category'].replace('/', '_')}/{num}.jpg"
