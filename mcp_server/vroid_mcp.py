"""Serveur MCP (stdio) pour piloter VRoid Studio via le plugin BepInEx VRoidMcpBridge.

Aucune dépendance externe : protocole JSON-RPC MCP implémenté à la main.
Le plugin doit tourner dans VRoid Studio (http://127.0.0.1:7811).
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.environ.get("VROID_BRIDGE_URL", "http://127.0.0.1:7811")
PROTOCOL_VERSION = "2025-06-18"


def call_bridge(path, body=None, query=None, timeout=30):
    url = BRIDGE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8") or "{}") | {"http_status": e.code}
    except urllib.error.URLError as e:
        raise RuntimeError(f"VRoid Studio injoignable ({BRIDGE}). Le plugin est-il chargé ? {e.reason}")


def _num(desc):
    return {"type": "number", "description": desc}


def _str(desc):
    return {"type": "string", "description": desc}


TOOLS = [
    {
        "name": "vroid_status",
        "description": "Indique si VRoid Studio répond et si un modèle est ouvert.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_list_groups",
        "description": "Liste les groupes éditables du modèle ouvert (visage, yeux, cheveux, corps, tenues...). "
                       "Chaque groupe a un id à passer aux autres outils.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_get_params",
        "description": "Liste les paramètres d'un groupe (curseurs blendshape, os, couleurs) avec leur valeur actuelle.",
        "inputSchema": {"type": "object", "properties": {"group": _str("id du groupe")}, "required": ["group"]},
    },
    {
        "name": "vroid_set_blendshape",
        "description": "Règle un curseur de forme (blendshape) d'un groupe. Annulable dans VRoid (Ctrl+Z).",
        "inputSchema": {"type": "object", "properties": {
            "group": _str("id du groupe"), "key": _str("clé du paramètre (voir vroid_get_params)"),
            "value": _num("nouvelle valeur")}, "required": ["group", "key", "value"]},
    },
    {
        "name": "vroid_set_bone",
        "description": "Règle un paramètre de transformation d'os (proportions du corps, taille...).",
        "inputSchema": {"type": "object", "properties": {
            "group": _str("id du groupe"), "key": _str("clé du paramètre"),
            "value": _num("nouvelle valeur")}, "required": ["group", "key", "value"]},
    },
    {
        "name": "vroid_set_color",
        "description": "Règle une couleur (composantes 0..1). Annulable dans VRoid.",
        "inputSchema": {"type": "object", "properties": {
            "group": _str("id du groupe"), "key": _str("clé du paramètre couleur"),
            "r": _num("rouge 0..1"), "g": _num("vert 0..1"), "b": _num("bleu 0..1"), "a": _num("alpha 0..1 (défaut 1)")},
            "required": ["group", "key", "r", "g", "b"]},
    },
    {
        "name": "vroid_list_layers",
        "description": "Liste les textures éditables d'un groupe (ex. jupe = Bottoms) : éléments (transferable), images et calques "
                       "(node, nom, opacité, visibilité, mode de fusion). Les vêtements n'ont pas de curseurs de couleur : "
                       "leur couleur se change par leurs calques de texture.",
        "inputSchema": {"type": "object", "properties": {"group": _str("id du groupe")}, "required": ["group"]},
    },
    {
        "name": "vroid_recolor_layer",
        "description": "Recolore un calque de texture sur place, transparence conservée, annulable. "
                       "mode 'multiply' : tissu clair -> couleur cible en gardant ombres et plis. "
                       "mode 'colorize' : garde la luminosité, impose la teinte (pour un tissu déjà coloré).",
        "inputSchema": {"type": "object", "properties": {
            "transferable": _str("id de l'élément (vroid_list_layers)"), "image": _str("id de l'image"),
            "node": _str("id du calque"), "r": _num("rouge 0..1"), "g": _num("vert 0..1"), "b": _num("bleu 0..1"),
            "mode": {"type": "string", "enum": ["multiply", "colorize"]},
            "strength": _num("intensité 0..1 (défaut 1)")},
            "required": ["transferable", "image", "node", "r", "g", "b"]},
    },
    {
        "name": "vroid_export_layer",
        "description": "Exporte un calque de texture en PNG (RGBA) pour le retoucher avec un autre outil.",
        "inputSchema": {"type": "object", "properties": {
            "transferable": _str("id de l'élément"), "image": _str("id de l'image"), "node": _str("id du calque"),
            "path": _str("chemin du PNG à écrire (facultatif)")}, "required": ["transferable", "image", "node"]},
    },
    {
        "name": "vroid_import_layer",
        "description": "Réimporte un PNG dans un calque (même taille que l'export) ou comme nouveau calque. Annulable.",
        "inputSchema": {"type": "object", "properties": {
            "transferable": _str("id de l'élément"), "image": _str("id de l'image"),
            "node": _str("id du calque à remplacer (inutile si as_new_layer)"), "path": _str("chemin du PNG"),
            "as_new_layer": {"type": "boolean", "description": "ajouter comme nouveau calque au lieu de remplacer"}},
            "required": ["transferable", "image", "path"]},
    },
    {
        "name": "vroid_list_hair_materials",
        "description": "Liste les matériaux de cheveux (la couleur des cheveux ne passe pas par vroid_get_params) : "
                       "id, nom, couleurs réglables (key + valeur) et textures avec leurs calques "
                       "(transferable/image/node utilisables avec vroid_recolor_layer).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_set_hair_color",
        "description": "Règle une couleur d'un matériau de cheveux (composantes 0..1). Annulable. Les clés 'base:<id>' "
                       "sont la teinte des cheveux d'un preset (couleur de superposition) : c'est elle qu'il faut changer "
                       "pour recolorer une coiffure preset (material facultatif dans ce cas). "
                       "Pour des cheveux dont la couleur est peinte dans la texture, recolorer plutôt les calques (mode colorize).",
        "inputSchema": {"type": "object", "properties": {
            "material": _str("id du matériau (vroid_list_hair_materials)"), "key": _str("clé de la couleur"),
            "r": _num("rouge 0..1"), "g": _num("vert 0..1"), "b": _num("bleu 0..1"), "a": _num("alpha 0..1 (défaut 1)")},
            "required": ["material", "key", "r", "g", "b"]},
    },
    {
        "name": "vroid_list_hair_groups",
        "description": "Liste les groupes de cheveux : 'procedural' (longueur, nombre de mèches réglables) ou 'brush' "
                       "(mèches dessinées : nombre de mèches, longueur moyenne).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_set_procedural_hair",
        "description": "Règle la longueur et/ou le nombre de mèches d'un groupe de cheveux procédural. Annulable.",
        "inputSchema": {"type": "object", "properties": {
            "transferable": _str("id de l'élément (vroid_list_hair_groups)"), "group": _str("id du groupe"),
            "length": _num("nouvelle longueur (facultatif)"), "hair_count": _num("nombre de mèches (facultatif)")},
            "required": ["transferable", "group"]},
    },
    {
        "name": "vroid_scale_brush_hair",
        "description": "Allonge (factor > 1) ou raccourcit (factor < 1) toutes les mèches d'un groupe dessiné au pinceau, "
                       "à partir de leur racine. Annulable (une étape par point).",
        "inputSchema": {"type": "object", "properties": {
            "transferable": _str("id de l'élément"), "group": _str("id du groupe"), "factor": _num("facteur, ex. 1.3")},
            "required": ["transferable", "group", "factor"]},
    },
    {
        "name": "vroid_clone_brush_hair",
        "description": "Duplique un groupe de mèches dessinées et décale la copie (en mètres, repère du modèle) "
                       "pour ajouter des mèches.",
        "inputSchema": {"type": "object", "properties": {
            "transferable": _str("id de l'élément"), "group": _str("id du groupe"),
            "dx": _num("décalage X"), "dy": _num("décalage Y"), "dz": _num("décalage Z")},
            "required": ["transferable", "group"]},
    },
    {
        "name": "vroid_undo",
        "description": "Annule la dernière modification dans VRoid Studio.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_redo",
        "description": "Rétablit la dernière modification annulée.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_screenshot",
        "description": "Capture la fenêtre de VRoid Studio et renvoie l'image, pour voir le résultat des modifications.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_list_presets",
        "description": "Liste les presets de VRoid (coiffures, visages, tenues, corps...). filter cherche dans le chemin "
                       "de ressource (ex. 'Hair', 'Tops', 'Bottoms', 'Onepiece', 'Shoes', 'Face'). Renvoie aussi la liste des "
                       "catégories. Seuls les presets gratuits ou possédés sont listés, sauf include_locked.",
        "inputSchema": {"type": "object", "properties": {
            "filter": _str("texte à chercher (facultatif)"),
            "include_locked": {"type": "boolean", "description": "inclure les presets payants non possédés"},
            "limit": _num("nombre maximal de résultats (défaut 200)")}},
    },
    {
        "name": "vroid_apply_preset",
        "description": "Applique un preset (remplace l'élément de la même catégorie, comme un clic sur sa vignette). Annulable.",
        "inputSchema": {"type": "object", "properties": {
            "id": _str("id du preset (vroid_list_presets)"),
            "preserve_material": {"type": "boolean", "description": "garder le matériau actuel (couleurs) si possible"}},
            "required": ["id"]},
    },
    {
        "name": "vroid_clothing_colors",
        "description": "Liste les couleurs réglables d'un vêtement (même preset) : group + key à passer à vroid_set_color.",
        "inputSchema": {"type": "object", "properties": {"group": _str("id du groupe du vêtement")}, "required": ["group"]},
    },
    {
        "name": "vroid_begin_clothing_edit",
        "description": "Passe un vêtement preset en édition de texture (comme le bouton Éditer de VRoid) : "
                       "ses calques deviennent accessibles à vroid_list_layers / vroid_recolor_layer. Annulable.",
        "inputSchema": {"type": "object", "properties": {"group": _str("id du groupe du vêtement")}, "required": ["group"]},
    },
    {
        "name": "vroid_measure",
        "description": "Mesure la taille actuelle du modèle en cm (identique à l'étiquette de taille de VRoid).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_set_body_size",
        "description": "Règle directement la taille (cm) via le curseur de silhouette du genre (FigureHeight/FigureSlender, "
                       "proportions gardées), et si donné le poids (kg), converti en largeur de taille via l'IMC "
                       "(VRoid n'a pas de poids). gender : female, male ou neutral. Annulable.",
        "inputSchema": {"type": "object", "properties": {
            "height_cm": _num("taille visée en cm"), "weight_kg": _num("poids visé en kg (facultatif)"),
            "gender": {"type": "string", "enum": ["female", "male", "neutral"], "description": "défaut female"}},
            "required": ["height_cm"]},
    },
    {
        "name": "vroid_preset_cache_search",
        "description": "Cherche dans le cache partagé des presets (sans VRoid) : descriptions, tags et couleurs déjà notés "
                       "par d'autres IA, avec le chemin de la vignette. Tous les mots de query doivent correspondre "
                       "(ex. 'jupe plissée courte bleu', 'hoodie yellow'). Utiliser avant d'essayer des presets un par un.",
        "inputSchema": {"type": "object", "properties": {
            "query": _str("mots à chercher (facultatif)"), "category": _str("ex. Clothing/Tops (facultatif)"),
            "annotated_only": {"type": "boolean", "description": "seulement les presets déjà décrits"},
            "include_locked": {"type": "boolean", "description": "inclure les presets payants non possédés"},
            "limit": _num("défaut 50")}},
    },
    {
        "name": "vroid_preset_cache_annotate",
        "description": "Ajoute ou corrige la description, les tags et les couleurs d'un preset dans le cache partagé, "
                       "pour les autres IA. Tags courts en minuscules (type, couleur, longueur, style).",
        "inputSchema": {"type": "object", "properties": {
            "key": _str("chemin de ressource ou id du preset"), "description": _str("texte court"),
            "tags": {"type": "array", "items": {"type": "string"}}, "colors": {"type": "array", "items": {"type": "string"}},
            "author": _str("qui annote (ex. nom du modèle d'IA)"),
            "replace": {"type": "boolean", "description": "remplacer les tags/couleurs au lieu d'ajouter"}},
            "required": ["key", "author"]},
    },
    {
        "name": "vroid_preset_thumbnail",
        "description": "Renvoie la vignette en cache d'un preset (image), pour juger sans l'appliquer.",
        "inputSchema": {"type": "object", "properties": {"key": _str("chemin de ressource ou id")}, "required": ["key"]},
    },
    {
        "name": "vroid_preset_cache_sync",
        "description": "Met à jour la liste des presets du cache depuis VRoid (nouveaux presets, prix, possession) "
                       "sans effacer les annotations.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_preset_cache_build",
        "description": "Crée les vignettes manquantes d'une catégorie : applique chaque preset dans VRoid, capture, "
                       "recadre sur la zone utile, puis remet le preset d'origine. Long (environ 2 s par preset).",
        "inputSchema": {"type": "object", "properties": {
            "category": _str("ex. Clothing/Shoes"), "refresh": {"type": "boolean", "description": "refaire aussi les vignettes existantes"},
            "limit": _num("nombre maximal de presets à traiter")}, "required": ["category"]},
    },
    {
        "name": "vroid_camera",
        "description": "Oriente la vue 3D de VRoid pour regarder le modèle sous un autre angle avant une capture. "
                       "action : get (état + liste des rotations prédéfinies), angles (x,y en degrés), rotate (dx,dy), "
                       "zoom (d), pan (x,y), reset (vue initiale), mode (rotation prédéfinie de VRoid), "
                       "projection (bascule perspective/orthographique), custom (px,py,pz,cx,cy,cz).",
        "inputSchema": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["get", "angles", "rotate", "zoom", "pan", "reset", "mode", "projection", "custom"]},
            "x": _num("angle ou décalage X"), "y": _num("angle ou décalage Y"), "dx": _num("rotation relative X"),
            "dy": _num("rotation relative Y"), "d": _num("zoom"), "mode": _str("nom de rotation prédéfinie"),
            "px": _num(""), "py": _num(""), "pz": _num(""), "cx": _num(""), "cy": _num(""), "cz": _num("")},
            "required": ["action"]},
    },
    {
        "name": "vroid_remove_item",
        "description": "Retire un élément du modèle (vêtement, accessoire, chaussures...). group = id de groupe, ou type "
                       "court pour retirer tous les groupes de ce type (Tops, Bottoms, Onepiece, Socks, Shoes, InnerTop, "
                       "ArmAccessory, NeckAccessory...). Utile pour partir d'un modèle sans vêtements avant de créer des vignettes.",
        "inputSchema": {"type": "object", "properties": {"group": _str("id ou type court")}, "required": ["group"]},
    },
    {
        "name": "vroid_face_preview",
        "description": "Aperçu d'expression pour une capture (bouche ouverte pour voir les dents, sourire, clin d'œil...) : "
                       "règle le poids (0..100) des blendshapes du visage dont le nom se termine par name "
                       "(ex. MTH_A, MTH_O, ALL_Joy, EYE_Close). Sans name : liste les noms (filtre facultatif). "
                       "Affichage seulement, rien n'est enregistré ; name vide et weight 0 remet tout à zéro.",
        "inputSchema": {"type": "object", "properties": {
            "name": _str("fin du nom du blendshape"), "weight": _num("0..100 (défaut 100)"),
            "filter": _str("filtre pour lister les noms")}},
    },
    {
        "name": "vroid_begin_hair_edit",
        "description": "Passe un matériau de cheveux en édition de texture (bouton Éditer de VRoid) : sa texture devient "
                       "accessible aux outils de calques. Utile pour une coiffure preset dont la texture n'est pas éditable.",
        "inputSchema": {"type": "object", "properties": {"material": _str("id du matériau (vroid_list_hair_materials)")},
                        "required": ["material"]},
    },
]


# ---------- Taille et poids ----------
# Étalonnage : l'étiquette de taille de VRoid = sommet du modèle (m) x 100 (vérifié : 152,1 cm).
WHOLE_BODY_TYPE = "TransferableGroupType.N00.Level1.WholeBody"
WAIST_TYPE = "TransferableGroupType.N00.Level1.Waist"


def measure_cm():
    m = call_bridge("/measure")
    if "boundsMaxY" not in m:
        raise RuntimeError(f"mesure impossible : {m}")
    return m["boundsMaxY"] * 100.0, m


def _group(type_name):
    for g in call_bridge("/groups"):
        if g.get("type") == type_name:
            return g["id"]
    raise RuntimeError(f"groupe {type_name} introuvable")


def _set_figure(group, g, x):
    """Curseur de silhouette du genre g : x > 0 = FigureHeight (plus petit, proportions gardées),
    x < 0 = FigureSlender (plus grand et plus fin). Les deux moitiés s'excluent."""
    key = f"Level2WholeBody_FigureHeight{g}" if x >= 0 else f"Level2WholeBody_FigureSlender{g}"
    call_bridge("/set_bone", body={"group": group, "key": key, "value": abs(x)})
    time.sleep(0.4)


def set_body_size(height_cm, weight_kg=None, gender="female"):
    group = _group(WHOLE_BODY_TYPE)
    g = {"female": "Female", "male": "Male", "neutral": "Neutral"}.get(gender or "female", "Female")
    out = {"gender": g.lower()}
    # Taille : recherche par sécante sur le curseur de silhouette du genre (l'échelle globale reste à 0).
    for k in ("Level2WholeBody_WholeBodyScaleShrink", "Level2WholeBody_WholeBodyScaleMag"):
        call_bridge("/set_bone", body={"group": group, "key": k, "value": 0.0})
    x0 = 0.0
    _set_figure(group, g, x0); h0, _ = measure_cm()
    x1 = 0.3 if h0 > height_cm else -0.3
    _set_figure(group, g, x1); h1, _ = measure_cm()
    for _ in range(10):
        if abs(h1 - height_cm) < 0.15 or h1 == h0:
            break
        x2 = max(-1.0, min(1.0, x1 + (height_cm - h1) * (x1 - x0) / (h1 - h0)))
        x0, h0, x1 = x1, h1, x2
        _set_figure(group, g, x1); h1, _ = measure_cm()
    out.update(height_cm=round(h1, 1), target_cm=height_cm, figure=round(x1, 4))
    if abs(h1 - height_cm) > 0.5:
        out["note"] = "taille hors de portée du curseur de silhouette (limites -1..1)"
    # Poids : pas de curseur dans VRoid ; converti en largeur de taille via l'IMC (21 = neutre).
    if weight_kg:
        bmi = weight_kg / (height_cm / 100) ** 2
        w = max(-1.0, min(1.0, (bmi - 21.0) / 8.0))
        waist = _group(WAIST_TYPE)
        key = "Level2Waist_WaistScaleMag" if w >= 0 else "Level2Waist_WaistScaleShrink"
        call_bridge("/set_bone", body={"group": waist, "key": key, "value": abs(w)})
        out.update(bmi=round(bmi, 1), waist=round(w, 3))
    return out

# ---------- Cache partagé des presets ----------
import preset_cache  # noqa: E402


def cache_sync():
    live = call_bridge("/presets", query={"limit": 100000, "include_locked": "true"})
    st = call_bridge("/status")
    return preset_cache.sync(live["presets"], st.get("unity"))


def _with_paths(res):
    for e in res["presets"]:
        e["thumbnailPath"] = preset_cache.thumb_path(e)
    return res


def cache_build(category, refresh=False, limit=None):
    cache_sync()
    live = call_bridge("/presets", query={"limit": 100000, "filter": category.split("/")[-1]})["presets"]
    live = [p for p in live if p["category"] == category]
    original = [p["id"] for p in live if p["active"]]
    done, skipped, failed = 0, 0, []
    tmp = os.path.join(preset_cache.ROOT, "_capture.png")
    for p in live:
        if limit and done >= limit:
            break
        e = preset_cache.get(p["resource"])
        if e.get("thumbnail") and not refresh and os.path.exists(preset_cache.thumb_path(e)):
            skipped += 1
            continue
        r = call_bridge("/apply_preset", body={"id": p["id"]}, timeout=120)
        if not r.get("ok"):
            failed.append(p["resource"]); continue
        time.sleep(1.5)
        call_bridge("/screenshot", body={"path": tmp})
        rel = preset_cache.thumb_rel(e)
        try:
            preset_cache.crop_model(tmp, category, os.path.join(preset_cache.ROOT, rel))
            preset_cache.set_thumbnail(p["resource"], rel)
            done += 1
        except Exception as ex:  # capture inexploitable : on continue
            failed.append(f"{p['resource']}: {ex}")
    for pid in original:
        call_bridge("/apply_preset", body={"id": pid}, timeout=120)
    if os.path.exists(tmp):
        os.remove(tmp)
    return {"category": category, "created": done, "skipped": skipped, "failed": failed, "restored": original}


def run_tool(name, args):
    if name == "vroid_status":
        return call_bridge("/status")
    if name == "vroid_preset_cache_search":
        return _with_paths(preset_cache.search(args.get("query"), args.get("category"),
                                               not args.get("include_locked"), bool(args.get("annotated_only")),
                                               int(args.get("limit") or 50)))
    if name == "vroid_preset_cache_annotate":
        return preset_cache.annotate(args["key"], args["author"], args.get("description"), args.get("tags"),
                                     args.get("colors"), bool(args.get("replace")))
    if name == "vroid_preset_thumbnail":
        path = preset_cache.thumb_path(preset_cache.get(args["key"]))
        if not path or not os.path.exists(path):
            return {"error": "pas de vignette en cache (vroid_preset_cache_build)"}
        with open(path, "rb") as f:
            return {"__image__": base64.b64encode(f.read()).decode("ascii"), "__mime__": "image/jpeg"}
    if name == "vroid_preset_cache_sync":
        return cache_sync()
    if name == "vroid_preset_cache_build":
        return cache_build(args["category"], bool(args.get("refresh")), args.get("limit"))
    if name == "vroid_begin_hair_edit":
        return call_bridge("/begin_hair_edit", body={"material": args["material"]})
    if name == "vroid_face_preview":
        if "name" not in args and "weight" not in args:
            return call_bridge("/face_blendshapes", query={"filter": args.get("filter", "")})
        return call_bridge("/face_preview", body={"name": args.get("name", ""), "weight": args.get("weight", 100)})
    if name == "vroid_remove_item":
        return call_bridge("/remove_group", body={"group": args["group"]}, timeout=120)
    if name == "vroid_camera":
        return call_bridge("/camera", body=args)
    if name == "vroid_measure":
        h, raw = measure_cm()
        return {"height_cm": round(h, 1), "raw": raw}
    if name == "vroid_set_body_size":
        return set_body_size(args["height_cm"], args.get("weight_kg"), args.get("gender", "female"))
    if name == "vroid_clothing_colors":
        return call_bridge("/clothing_colors", query={"group": args["group"]})
    if name == "vroid_begin_clothing_edit":
        return call_bridge("/begin_clothing_edit", body={"group": args["group"]})
    if name == "vroid_list_presets":
        q = {k: v for k, v in args.items() if k in ("filter", "limit")}
        if args.get("include_locked"):
            q["include_locked"] = "true"
        return call_bridge("/presets", query=q)
    if name == "vroid_apply_preset":
        body = {"id": args["id"], "preserve_material": "true" if args.get("preserve_material") else "false"}
        return call_bridge("/apply_preset", body=body, timeout=120)
    if name == "vroid_list_groups":
        return call_bridge("/groups")
    if name == "vroid_get_params":
        return call_bridge("/params", query={"group": args["group"]})
    if name == "vroid_set_blendshape":
        return call_bridge("/set_blendshape", body=args)
    if name == "vroid_set_bone":
        return call_bridge("/set_bone", body=args)
    if name == "vroid_set_color":
        return call_bridge("/set_color", body=args)
    if name == "vroid_list_layers":
        return call_bridge("/layers", query={"group": args["group"]})
    if name == "vroid_recolor_layer":
        return call_bridge("/recolor_layer", body=args, timeout=120)
    if name == "vroid_export_layer":
        return call_bridge("/export_layer", body=args, timeout=120)
    if name == "vroid_import_layer":
        body = dict(args)
        if "as_new_layer" in body:
            body["as_new_layer"] = "true" if body["as_new_layer"] else "false"
        return call_bridge("/import_layer", body=body, timeout=120)
    if name == "vroid_list_hair_materials":
        return call_bridge("/hair_materials")
    if name == "vroid_set_hair_color":
        return call_bridge("/set_hair_color", body=args)
    if name == "vroid_list_hair_groups":
        return call_bridge("/hair_groups")
    if name == "vroid_set_procedural_hair":
        return call_bridge("/set_procedural_hair", body=args)
    if name == "vroid_scale_brush_hair":
        return call_bridge("/scale_brush_hair", body=args, timeout=120)
    if name == "vroid_clone_brush_hair":
        return call_bridge("/clone_brush_hair", body=args, timeout=120)
    if name == "vroid_undo":
        return call_bridge("/undo", body={})
    if name == "vroid_redo":
        return call_bridge("/redo", body={})
    if name == "vroid_screenshot":
        res = call_bridge("/screenshot", body={})
        if res.get("ok") and os.path.exists(res["path"]):
            with open(res["path"], "rb") as f:
                img = base64.b64encode(f.read()).decode("ascii")
            try:
                os.remove(res["path"])
            except OSError:
                pass
            return {"__image__": img}
        return res
    raise ValueError(f"outil inconnu : {name}")


def handle(msg):
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "vroid-studio", "version": "0.10.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        try:
            out = run_tool(params["name"], params.get("arguments") or {})
            if isinstance(out, dict) and "__image__" in out:
                content = [{"type": "image", "data": out["__image__"], "mimeType": out.get("__mime__", "image/png")}]
            else:
                content = [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=1)}]
            is_err = isinstance(out, dict) and "error" in out
            return {"content": content, "isError": is_err}
        except Exception as e:  # erreur renvoyée à l'IA plutôt que de faire planter le serveur
            return {"content": [{"type": "text", "text": f"Erreur : {e}"}], "isError": True}
    raise KeyError(method)


def main():
    # Sous Windows, stdin/stdout ne sont pas en UTF-8 par défaut.
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if "id" not in msg:  # notification (ex. notifications/initialized)
            continue
        try:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg)}
        except KeyError:
            reply = {"jsonrpc": "2.0", "id": msg["id"],
                     "error": {"code": -32601, "message": f"méthode inconnue : {msg.get('method')}"}}
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
