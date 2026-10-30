"""Serveur MCP (stdio) pour piloter VRoid Studio via le plugin BepInEx VRoidMcpBridge.

Aucune dépendance externe : protocole JSON-RPC MCP implémenté à la main.
Le plugin doit tourner dans VRoid Studio (http://127.0.0.1:7811).
"""
import base64
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preset_cache  # noqa: E402
import help_i18n  # noqa: E402
import tool_i18n  # noqa: E402
import prompts  # noqa: E402

BRIDGE = os.environ.get("VROID_BRIDGE_URL", "http://127.0.0.1:7811")
PROTOCOL_VERSION = "2025-06-18"

# Agent-facing reference (docs/AGENT_REFERENCE_EN.md), exposed as MCP resources so
# Harness can load only the section it needs instead of injecting 80+ KiB at startup.
AGENT_REFERENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "AGENT_REFERENCE_EN.md",
)
AGENT_RESOURCE_GROUPS = (
    ("reference", "VRoid Agent Reference (full)",
     "Complete English reference: tools, all parameter categories, physical values, expressions and workflows.",
     None),
    ("start", "Agent Reference — Start, lifecycle and UI map",
     "Startup contract, lifecycle rules and the section/category access map.",
     ("What is available", "Start and lifecycle", "UI map and access modes")),
    ("face", "Agent Reference — Face parameters",
     "Face categories, sliders, colors and per-category parameter keys.",
     ("Face parameters",)),
    ("hairstyle", "Agent Reference — Hairstyle parameters",
     "Hair presets, procedural/brush groups, hair colors and textures.",
     ("Hairstyle parameters",)),
    ("body", "Agent Reference — Body parameters",
     "Body proportions, silhouette and material parameters.",
     ("Body parameters",)),
    ("outfit", "Agent Reference — Outfit parameters",
     "Clothing presets, simple colors and complex texture editing.",
     ("Outfit parameters",)),
    ("accessories", "Agent Reference — Accessories",
     "Accessory preset slots and how to remove or texture-edit them.",
     ("Accessories parameters",)),
    ("look", "Agent Reference — Look parameters",
     "Fixed preset, mouth line, nose lighting and overlay presets.",
     ("Look parameters",)),
    ("physical", "Agent Reference — Physical and face details",
     "Height/weight, iris size, ears, teeth, lips and the expression preview limits.",
     ("Physical parameters, iris, ears, teeth and mouth",)),
    ("presets", "Agent Reference — Preset categories",
     "Preset categories, replacement slots and whole-set behavior.",
     ("Preset categories and replacement slots",)),
    ("tools", "Agent Reference — All MCP tools",
     "All 53 tools with descriptions, argument schemas and constraints.",
     ("Complete MCP tool reference",)),
    ("workflows", "Agent Reference — Workflows and value rules",
     "Normalized 0..1 rules, paired sliders and agent workflows.",
     ("Normalized 0..1 and paired-slider rules", "Workflows an agent can follow")),
    ("troubleshooting", "Agent Reference — Errors and source of truth",
     "Failure modes, recovery and the drift-control contract.",
     ("Failure modes and recovery", "Source of truth and drift control")),
)


def _agent_reference_document():
    try:
        with open(AGENT_REFERENCE_PATH, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _agent_heading_blocks(text):
    blocks = {}
    for part in re.split(r"(?m)^## ", text)[1:]:
        title, _, body = part.partition("\n")
        # The generator may number its headings ("## 2. Start and lifecycle"): match without the number.
        blocks[re.sub(r"^\d+\.\s*", "", title.strip())] = "## " + part
    return blocks


def agent_resources():
    """MCP resources/list payload for the agent reference."""
    return {
        "resources": [
            {
                "uri": "vroid://agent/" + slug,
                "name": name,
                "description": description,
                "mimeType": "text/markdown",
            }
            for slug, name, description, _ in AGENT_RESOURCE_GROUPS
        ]
    }


def read_agent_resource(uri):
    """MCP resources/read payload; loads one section (or the whole reference)."""
    slug = (uri or "").strip()
    if slug.startswith("vroid://agent/"):
        slug = slug[len("vroid://agent/"):]
    group = next((g for g in AGENT_RESOURCE_GROUPS if g[0] == slug), None)
    if group is None:
        raise KeyError(uri)
    text = _agent_reference_document()
    if text is None:
        text = ("# VRoid Agent Reference not installed\n\n"
                "The MCP server is running, but docs/AGENT_REFERENCE_EN.md is missing. "
                "Reinstall the release package or read `vroid_help(topic='overview')`.\n")
    else:
        headings = group[3]
        if headings:
            blocks = _agent_heading_blocks(text)
            text = "\n\n".join(blocks[h] for h in headings if h in blocks)
            if not text:
                text = f"# {group[1]}\n\nThis section is not present in the installed reference.\n"
    return {
        "contents": [{
            "uri": "vroid://agent/" + slug,
            "mimeType": "text/markdown",
            "text": text,
        }]
    }


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
        raise RuntimeError(f"VRoid Studio unreachable at {BRIDGE}. Is the bridge plugin loaded? {e.reason}")


def _num(desc):
    return {"type": "number", "description": desc}


def _str(desc):
    return {"type": "string", "description": desc}


TOOLS = [
    {
        "name": "vroid_help",
        "description": "Show the built-in manual. Topics: overview, tools, lifecycle, export, framing, thumbnails, "
                       "colors, outfit, sessions, errors, languages, batch. lang=en|fr|ja|zh. "
                       "Call this first when unsure.",
        "inputSchema": {"type": "object", "properties": {
            "topic": {"type": "string", "description": "help topic (default overview)"},
            "lang": {"type": "string", "enum": ["en", "fr", "ja", "zh", "zh-CN"],
                     "description": "manual language: en (default), fr, ja, zh-CN"}}},
    },
    {
        "name": "vroid_batch",
        "description": "Run several vroid_* operations sequentially in one MCP call and return a text summary plus "
                       "optional images. Up to 200 operations, no nested batches, no automatic rollback. "
                       "stop_on_error defaults to true. Images are capped (8 images / 16 MiB); excess images are "
                       "reported by path only. Save before destructive sequences.",
        "inputSchema": {"type": "object", "properties": {
            "operations": {"type": "array", "minItems": 1, "maxItems": 200,
                           "items": {"type": "object", "properties": {
                               "tool": {"type": "string", "description": "vroid_* tool name"},
                               "args": {"type": "object", "description": "arguments for that tool"}},
                               "required": ["tool", "args"]}},
            "stop_on_error": {"type": "boolean", "description": "stop at the first error (default true)"},
            "include_images": {"type": "boolean", "description": "include returned images in the same response "
                                                                 "(default true, capped)"}},
            "required": ["operations"]},
    },
    {
        "name": "vroid_status",
        "description": "Indique si VRoid Studio répond, si un modèle est ouvert, son fichier courant, "
                       "s'il est modifié (dirty) et si l'éditeur est prêt.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_create",
        "description": "Crée un nouveau modèle depuis le template VRoid (female ou male), comme le dialogue "
                       "« Create New Model ». VRoid doit être au menu des modèles (aucun modèle ouvert). "
                       "Bloquant jusqu'à ce que le modèle soit prêt. Le modèle n'a pas encore de fichier : "
                       "utiliser vroid_save avec path pour l'enregistrer.",
        "inputSchema": {"type": "object", "properties": {
            "gender": {"type": "string", "enum": ["female", "male"], "description": "template à créer"}},
            "required": ["gender"]},
    },
    {
        "name": "vroid_open",
        "description": "Ouvre un fichier .vroid et attend que le modèle soit prêt. VRoid doit être au menu "
                       "des modèles (aucun modèle ouvert) : sauvegarder puis vroid_main_menu si nécessaire. "
                       "path est un chemin absolu.",
        "inputSchema": {"type": "object", "properties": {
            "path": _str("chemin absolu du fichier .vroid")}, "required": ["path"]},
    },
    {
        "name": "vroid_save",
        "description": "Sauvegarde le modèle ouvert. Avec path : enregistrement sous (crée le fichier). "
                       "Sans path : sauvegarde sur place, uniquement si le modèle a déjà un fichier .vroid. "
                       "Un modèle créé avec vroid_create n'a pas de fichier : passer path.",
        "inputSchema": {"type": "object", "properties": {
            "path": _str("chemin absolu du .vroid à écrire (facultatif)")}},
    },
    {
        "name": "vroid_export_vrm",
        "description": "Export the open model as a .vrm file with VRoid's own exporter, without clicks or file dialog "
                       "(same options as the 'Export as VRM' screen). Options left out use VRoid's defaults: "
                       "VRM 1.0, transparent meshes deleted, no reduction. Takes about 10-40 s. "
                       "Reduction sliders are 0..100. material_mode: 0 Default, 1 = 2 materials, 2 = 8, 3 = 12. "
                       "Texture size: with material_mode 0 use texture_mode 1 (Shrunk); with material reduction VRoid "
                       "uses the atlas instead, so use atlas_resolution 1 (2048) to shrink textures. "
                       "Any option VRoid refused is listed in 'warnings'. The model itself is not modified.",
        "inputSchema": {"type": "object", "properties": {
            "path": _str("absolute path of the .vrm to write"),
            "version": {"type": "string", "enum": ["1", "0"], "description": "1 = VRM 1.0 (default), 0 = VRM 0.x"},
            "title": _str("model name in the VRM meta (default: file name)"),
            "author": _str("author in the VRM meta"),
            "model_version": _str("model version in the VRM meta"),
            "delete_transparent": {"type": "boolean", "description": "Delete Transparent Meshes (default true)"},
            "hair_cross_section": {"type": "boolean", "description": "Edit Hair Cross-Section (default false)"},
            "hair_smoothness": _num("Hair Smoothness reduction 0..100"),
            "hair": _num("hair polygon reduction 0..100"),
            "face": _num("face polygon reduction 0..100"),
            "body": _num("body polygon reduction 0..100"),
            "outfit": _num("outfit polygon reduction 0..100"),
            "material_mode": _num("0 Default, 1 = 2 materials, 2 = 8 materials, 3 = 12 materials"),
            "combine_hair": {"type": "boolean", "description": "Combine Hair Mesh (default true)"},
            "texture_mode": _num("0 Original, 1 Shrunk (only without material reduction)"),
            "atlas_resolution": _num("with material reduction: 0 = 4096, 1 = 2048"),
            "hair_bones": _num("Reduce Bones: Hair 0..100"),
            "leave": {"type": "boolean", "description": "return to the editor after export (default true); false leaves the export screen open"}},
            "required": ["path"]},
    },
    {
        "name": "vroid_export_vrm_options",
        "description": "Open VRoid's export screen and return its current export settings and the available "
                       "material / texture / atlas choices. Close it again with vroid_export_vrm or by passing leave.",
        "inputSchema": {"type": "object", "properties": {
            "leave": {"type": "boolean", "description": "close the export screen after reading (default true)"}}},
    },
    {
        "name": "vroid_main_menu",
        "description": "Revient au menu des modèles sans quitter VRoid, pour pouvoir ouvrir ou créer un autre "
                       "modèle. Refuse si des modifications ne sont pas sauvegardées, sauf discard=true.",
        "inputSchema": {"type": "object", "properties": {
            "discard": {"type": "boolean", "description": "abandonner les modifications non sauvegardées"}}},
    },
    {
        "name": "vroid_exit",
        "description": "Quit VRoid Studio gracefully. Refuses unsaved changes unless discard=true. "
                       "The response is sent before the process exits; use it after a generation sequence.",
        "inputSchema": {"type": "object", "properties": {
            "discard": {"type": "boolean", "description": "discard unsaved changes before quitting"}}},
    },
    {
        "name": "vroid_framing_get",
        "description": "Lit les cadrages de vignettes par catégorie/partie du corps (ex. Clothing/Tops, "
                       "Clothing/Shoes, Hair, Face, VRoid/ClothingSet), pas par vêtement individuel : les infos d'un "
                       "vêtement précis restent dans le cache. top/bottom sont des fractions depuis le haut du modèle "
                       "(0 = sommet, 1 = pieds), half la demi-largeur (null = toute la largeur), distance le facteur de "
                       "recul, yaw l'orientation en degrés (0 = face, 90 = profil, 180 = dos), fit=region|full-body. "
                       "Sans category : toutes les catégories connues.",
        "inputSchema": {"type": "object", "properties": {
            "category": _str("catégorie (ex. Clothing/Tops) ; vide = toutes")}},
    },
    {
        "name": "vroid_framing_set",
        "description": "Modifie le cadrage d'une catégorie/partie du corps (ex. Clothing/Tops, Clothing/Shoes, Hair, "
                       "Face, VRoid/ClothingSet), jamais d'un vêtement individuel : l'override est local et ne touche "
                       "pas aux defaults commités. top/bottom dans 0..1, half null ou 0.01..1, distance 1..10, "
                       "yaw -180..180 (0 = face, 90 = profil, 180 = dos), fit=region|full-body. "
                       "vroid_framing_reset restaure les defaults.",
        "inputSchema": {"type": "object", "properties": {
            "category": _str("catégorie (ex. VRoid/ClothingSet)"),
            "top": _num("fraction depuis le haut (0 = sommet)"),
            "bottom": _num("fraction depuis le haut (1 = pieds)"),
            "half": _num("demi-largeur en fraction de hauteur"),
            "distance": _num("facteur de recul (défaut 3.3 ; 4.2 tenue complète)"),
            "yaw": _num("orientation en degrés : 0 face, 90 profil, 180 dos"),
            "fit": {"type": "string", "enum": ["region", "full-body"]}},
            "required": ["category"]},
    },
    {
        "name": "vroid_framing_reset",
        "description": "Efface les overrides de cadrage (tous, ou une catégorie/partie du corps) et revient aux "
                       "defaults commités dans config/framing.json. Les overrides locaux sont dans "
                       "preset_cache/framing_overrides.json.",
        "inputSchema": {"type": "object", "properties": {
            "category": _str("catégorie à réinitialiser ; vide = toutes")}},
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
        "name": "vroid_get_item_params",
        "description": "List every adjustable parameter of the model's items, including the shape sliders VRoid shows under Customize > Parameters for clothing and accessories (skirt tighter/wider/shorter/longer, sleeve thickness, width, length, hood...), which vroid_get_params does not return. Each group has 'pars' (regular parameters) and 'sliders' (key, label, value). Clothing sliders range 0..100 (not 0..1); the last word of the label says what they do (Narrow = tighter, Spread = wider, Short, Long...). Set one with vroid_set_blendshape group=<group> key=<slider key> value=<0..100>; undoable. 'type' filters by group type, e.g. TransferableGroupType.N00.Level1.Bottoms.",
        "inputSchema": {"type": "object", "properties": {
            "type": _str("optional group type filter, e.g. TransferableGroupType.N00.Level1.Bottoms")}},
    },
    {
        "name": "vroid_sections",
        "description": "List editable sections and their categories (Face, Hairstyle, Body, Outfit, "
                       "Accessories, Look), with group counts. High-level companion to vroid_list_groups.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vroid_categories",
        "description": "List categories in a section (or all categories), with the category key, label, "
                       "section and group count. Use with vroid_enter / vroid_set_param.",
        "inputSchema": {"type": "object", "properties": {
            "section": _str("section name (optional: Face, Hairstyle, Body, Outfit, Accessories, Look)")}},
    },
    {
        "name": "vroid_enter",
        "description": "Select a section/category by name and return its group and enriched parameters "
                       "(labels + stable section/category/key paths). Equivalent in spirit to enter(), "
                       "but does not change VRoid's UI tab.",
        "inputSchema": {"type": "object", "properties": {
            "section": _str("section, e.g. Face, Hairstyle, Body, Outfit"),
            "category": _str("category or human label from vroid_categories")},
            "required": ["section", "category"]},
    },
    {
        "name": "vroid_set_param",
        "description": "Set a parameter by section/category and key or short label. Dispatches to bone, "
                       "blendshape or color. Accepts numeric values, #RRGGBB or r,g,b for colors. This is the "
                       "unified counterpart of vroid_set_bone / vroid_set_blendshape / vroid_set_color.",
        "inputSchema": {"type": "object", "properties": {
            "section": _str("section, e.g. Face, Hairstyle, Body, Outfit"),
            "category": _str("category or human label from vroid_categories"),
            "param": _str("parameter key, path or short label from vroid_enter"),
            "value": {"type": ["number", "string"], "description": "numeric value, #RRGGBB or r,g,b"}},
            "required": ["section", "category", "param", "value"]},
    },
    {
        "name": "vroid_set_blendshape",
        "description": "Règle un curseur de forme (blendshape) d'un groupe. Annulable dans VRoid (Ctrl+Z).",
        "inputSchema": {"type": "object", "properties": {
            "group": _str("id du groupe"),
            "key": _str("clé du paramètre (voir vroid_get_params) ou clé 'template:...' d'un curseur de vêtement (voir vroid_get_item_params)"),
            "value": _num("nouvelle valeur (0..1 ; 0..100 pour un curseur de vêtement)")}, "required": ["group", "key", "value"]},
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
        "name": "vroid_colorize",
        "description": "Composite color pass: apply one color to both the global/material colors and the "
                       "texture layers of a group (clothing or hair). target=global|texture|both. Fine-grained "
                       "vroid_set_color / vroid_recolor_layer remain available. Undoable; hair textures may not "
                       "be exposed, in which case a warning is returned.",
        "inputSchema": {"type": "object", "properties": {
            "group": _str("group id"),
            "r": _num("red 0..1"), "g": _num("green 0..1"), "b": _num("blue 0..1"),
            "target": {"type": "string", "enum": ["global", "texture", "both"],
                       "description": "global colors, texture layers, or both (default)"},
            "mode": {"type": "string", "enum": ["multiply", "colorize"],
                     "description": "texture recolor mode (default multiply)"},
            "strength": _num("texture strength 0..1 (default 1)"),
            "material": _str("hair material id (optional; default all)"),
            "layer": _str("texture layer node (optional; default all)")},
            "required": ["group", "r", "g", "b"]},
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
        "description": "Capture a clean 3D preview of the avatar (no UI) and return the image. "
                       "MSAA is 4x and SSAA 2x by default; width/height override the output size. "
                       "clean=false captures the whole VRoid window instead.",
        "inputSchema": {"type": "object", "properties": {
            "msaa": _num("MSAA samples 1..8 (default 4)"),
            "ssaa": _num("supersampling factor 1..3 (default 2)"),
            "width": _num("output width in pixels (0 = camera viewport)"),
            "height": _num("output height in pixels (0 = camera viewport)"),
            "clean": {"type": "boolean", "description": "true = 3D preview only (default), false = full window"}}},
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
        "description": "Cherche dans le cache partagé des presets et objets personnalisés (sans VRoid) : descriptions, "
                       "tags et couleurs déjà notés par d'autres IA, avec le chemin de la vignette. Chaque résultat a "
                       "aussi preview : {kind: situation|native-icon, mannequin, clothing, underwear, hair, keptSlot, "
                       "orientation, yaw, capturedAt, pixels, source}. Les vignettes situation sont capturées sur un mannequin nu "
                       "(sans vêtements, sous-vêtements ni cheveux, sauf la pièce testée) et cadrées de face. "
                       "Tous les mots de query doivent correspondre (ex. 'jupe plissée courte bleu').",
        "inputSchema": {"type": "object", "properties": {
            "query": _str("mots à chercher (facultatif)"), "category": _str("ex. Clothing/Tops (facultatif)"),
            "annotated_only": {"type": "boolean", "description": "seulement les presets déjà décrits"},
            "include_locked": {"type": "boolean", "description": "inclure les presets payants non possédés"},
            "kind": {"type": "string", "enum": ["preset", "custom"], "description": "presets intégrés ou objets personnalisés"},
            "status": {"type": "string", "enum": ["new", "changed"], "description": "nouveaux / modifiés au dernier scan"},
            "include_removed": {"type": "boolean", "description": "inclure les éléments absents de VRoid"},
            "limit": _num("défaut 50")}},
    },
    {
        "name": "vroid_preset_cache_annotate",
        "description": "Ajoute ou corrige la description, les tags et les couleurs d'un preset dans le cache partagé, "
                       "pour les autres IA. Tags courts en minuscules (type, couleur, longueur, style).",
        "inputSchema": {"type": "object", "properties": {
            "key": _str("chemin de ressource ou id du preset"), "label": _str("libellé manuel (remplace le label généré)"),
            "description": _str("texte court"),
            "tags": {"type": "array", "items": {"type": "string"}}, "colors": {"type": "array", "items": {"type": "string"}},
            "author": _str("qui annote (ex. nom du modèle d'IA)"),
            "replace": {"type": "boolean", "description": "remplacer les tags/couleurs au lieu d'ajouter"}},
            "required": ["key", "author"]},
    },
    {
        "name": "vroid_preset_thumbnail",
        "description": "Renvoie la vignette d'un preset ou objet personnalisé (image) pour juger sans l'appliquer : "
                       "capture en situation si elle existe, sinon icône native de VRoid (récupérée à la demande). "
                       "Les métadonnées de la vignette (mannequin, vêtements, sous-vêtements, cadrage) sont dans "
                       "le résultat de vroid_preset_cache_search (champ preview).",
        "inputSchema": {"type": "object", "properties": {"key": _str("chemin de ressource ou id")}, "required": ["key"]},
    },
    {
        "name": "vroid_preset_cache_sync",
        "description": "Scanne ce que VRoid propose maintenant : presets intégrés ET objets personnalisés (custom items, "
                       "avec le nom donné dans VRoid). Signale les nouveaux, les modifiés (custom renommé ou nouvelle "
                       "révision) et les retirés, sans effacer les annotations. Fait automatiquement à chaque lancement "
                       "de VRoid. icons=true récupère aussi les icônes natives des presets (rapide, rien n'est appliqué).",
        "inputSchema": {"type": "object", "properties": {
            "icons": {"type": "boolean", "description": "récupérer les icônes natives manquantes"},
            "icon_limit": _num("nombre maximal d'icônes à récupérer")}},
    },
    {
        "name": "vroid_preset_cache_build",
        "description": "Crée les vignettes en situation d'une catégorie (presets, ou Custom/<emplacement> pour les "
                       "objets personnalisés). Retire TOUS les vêtements, accessoires, sous-vêtements (même ceux par "
                       "défaut, qui dépassent sur les maillots de bain) et les cheveux sauf BaseHair/pièce testée ; "
                       "cadre le personnage de face, centré sur ses bounds ; applique chaque élément, vérifie qu'il ne "
                       "reste rien d'autre, capture, recadre, puis remet la tenue d'origine. Renseigne thumbnailMeta "
                       "(mannequin nu, clothing=tested-item-only, underwear=removed, strippedSlots, caméra avec fit, "
                       "pixels, sha1) dans catalog.json. Les tenues complètes reculent la caméra pour montrer les "
                       "chaussures ; l'orientation (yaw du profil : dos pour les cheveux arrière, trois-quarts pour "
                       "les chaussures/accessoires de bras) est appliquée. Enregistrer le modèle avant : la restauration "
                       "n'est pas garantie à l'identique. "
                       "Environ 3 s par preset ; les icônes natives (sync icons=true) sont plus rapides.",
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
        "name": "vroid_apply_custom",
        "description": "Applique un objet personnalisé (custom item) de l'utilisateur, comme un clic dans l'onglet Custom de "
                       "VRoid : remplace l'élément de la même catégorie. key = clé du cache (vroid_preset_cache_search "
                       "kind=custom) ou file = chemin du fichier .vroidcustomitem. Annulable.",
        "inputSchema": {"type": "object", "properties": {
            "key": _str("clé du cache (custom:...)"), "file": _str("chemin du fichier .vroidcustomitem")}},
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

# Tool names/arguments stay English for every client; FR/JA/ZH are in vroid_help.
_MISSING_EN = tool_i18n.localize_tools(TOOLS)


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

def fetch_icon(e):
    """Icône native d'un preset intégré (lue dans les données de VRoid, rien n'est appliqué)."""
    rel = preset_cache.icon_rel(e)
    path = os.path.join(preset_cache.ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = call_bridge("/preset_thumbnail", body={"resource": e["resource"], "path": path})
    if r.get("ok"):
        preset_cache.set_icon(e["resource"], rel)
        return True
    # Quelques presets (casquettes, chapeaux, queues...) n'ont pas d'icône dans les données de VRoid :
    # on le note pour ne pas réessayer à chaque scan (vignette en situation possible avec vroid_preset_cache_build).
    preset_cache.set_field(e["resource"], "iconMissing", True)
    return False


def cache_sync(icons=False, icon_limit=None):
    """Scan de ce que VRoid propose (presets intégrés + objets personnalisés) et mise à jour du cache."""
    live = call_bridge("/presets", query={"limit": 100000, "include_locked": "true"})
    st = call_bridge("/status")
    customs_known = True
    try:
        customs = call_bridge("/custom_items").get("items")
        if customs is None:
            customs, customs_known = [], False
    except Exception:  # plugin antérieur à 0.11, ou lecture impossible
        customs, customs_known = [], False
    items = live.get("presets") if isinstance(live, dict) else None
    if items is None and isinstance(live, dict):
        items = live.get("items") or live.get("all")
    if not items:
        # Ne jamais scanner une liste vide : cela marquerait tout le cache comme retiré.
        return {"total": 0, "customs": 0, "new": 0, "changed": [], "removed": [],
                "skipped": "aucun preset renvoyé par VRoid (modèle non ouvert ?)"}
    res = preset_cache.scan(items, customs, st.get("unity"), st.get("startedUtc"),
                            customs_known=customs_known)
    if icons:
        done = 0
        for e in list(preset_cache.load()["presets"].values()):
            if icon_limit and done >= int(icon_limit):
                break
            if e.get("kind", "preset") == "preset" and not e.get("removed") and not e.get("icon")                     and not e.get("iconMissing"):
                if fetch_icon(e):
                    done += 1
        res["iconsFetched"] = done
    return res


_scan_session = None


def maybe_scan():
    """Scan automatique quand VRoid a été (re)lancé depuis le dernier scan : renvoie un résumé, sinon None."""
    global _scan_session
    try:
        st = call_bridge("/status", timeout=5)
    except Exception:
        return None
    if not st.get("modelOpen") or not st.get("ready"):
        # Le catalogue n'est lisible qu'avec un modèle ouvert : sinon VRoid renvoie une liste
        # vide et le scan conclurait à tort que tous les presets ont été retirés.
        return None
    session = st.get("startedUtc")
    if not session or session == _scan_session:
        return None
    _scan_session = session
    if preset_cache.load().get("source", {}).get("session") == session:
        return None
    try:
        r = cache_sync()
    except Exception as e:
        return f"Scan automatique du catalogue impossible : {e}"
    return (f"Catalogue VRoid scanné (nouveau lancement de VRoid) : {r['total']} éléments dont {r['customs']} "
            f"objets personnalisés ; {r['new']} nouveaux, {len(r['changed'])} modifiés, {len(r['removed'])} retirés.")


def _with_paths(res):
    for e in res["presets"]:
        e["thumbnailPath"] = preset_cache.thumb_path(e)
        meta = e.get("thumbnailMeta") or {}
        if e.get("thumbnail"):
            kind = "situation"
        elif e.get("icon"):
            kind = "native-icon"
        else:
            kind = None
        cam = meta.get("camera") or {}
        yaw = cam.get("yaw")
        orientation = meta.get("orientation")
        if not orientation:
            if yaw is None and cam.get("front") is True:
                orientation = "front"
            else:
                orientation = _orientation_label(yaw)
        e["preview"] = {
            "kind": kind,
            "path": e["thumbnailPath"],
            "label": e.get("label"),
            "labelSource": e.get("labelSource"),
            "mannequin": (meta.get("mannequin") or "unknown") if kind == "situation" else "n/a",
            "clothing": (meta.get("clothing") or "unknown") if kind == "situation" else "n/a",
            "underwear": (meta.get("underwear") or "unknown") if kind == "situation" else "n/a",
            "hair": (meta.get("hair") or "unknown") if kind == "situation" else "n/a",
            "keptSlot": meta.get("keptSlot"),
            "orientation": orientation,
            "yaw": yaw,
            "capturedAt": meta.get("capturedAt"),
            "pixels": meta.get("pixels"),
            "camera": cam,
            "fit": cam.get("fit"),
            "source": meta.get("source") if kind == "situation" else ("vroid-bundle" if kind else None),
        }
    return res


# Vêtements, accessoires, sous-vêtements et cheveux retirés avant les captures : le mannequin (anatomie neutre)
# ne porte que l'élément testé. Tout est remis ensuite.
OUTFIT_SLOTS = ["Tops", "Bottoms", "Onepiece", "Socks", "Shoes", "ArmAccessory", "NeckAccessory",
                "Hat", "AnimalEar", "Tail", "Glasses"]
UNDERWEAR_SLOTS = ["InnerTop", "InnerBottom"]


def _active_slots():
    """Type court -> liste des groupes actifs {id, resource} (vêtements, accessoires, sous-vêtements)."""
    out = {}
    for g in call_bridge("/groups"):
        short = (g.get("type") or "").split(".")[-1]
        if short in OUTFIT_SLOTS + UNDERWEAR_SLOTS:
            out.setdefault(short, []).append({"id": g["id"], "resource": g.get("resource")})
    return out


def _default_underwear(slot):
    """Premier preset de sous-vêtement disponible (ex. InnerTop 001)."""
    live = call_bridge("/presets", query={"limit": 100000, "filter": slot})["presets"]
    live = sorted((x for x in live if x["resource"].split("/TransferableGroupType.")[-1].endswith(slot + ".transferablegroup")),
                  key=lambda x: x["resource"])
    return live[0]["id"] if live else None


HAIR_SLOTS = ["AllHair", "HairFront", "HairBack", "HairTied", "HairSideburns", "HairHanege", "HairAhoge", "BaseHair"]


def _slot_groups(slots):
    """Groupes actifs des emplacements donnés (tous types : vêtements, cheveux, visage, peau...)."""
    out = []
    for g in call_bridge("/groups"):
        short = (g.get("type") or "").split(".")[-1]
        if short in slots:
            out.append({"id": g["id"], "resource": g.get("resource"), "slot": short})
    return out


def _orientation_label(yaw):
    if yaw is None:
        return "unknown"
    yaw = float(yaw)
    if abs(yaw) < 1:
        return "front"
    if abs(abs(yaw) - 180) < 1:
        return "back"
    if abs(abs(yaw) - 90) < 1:
        return "profile"
    return "three-quarter"


FACE_SLOTS = ["FaceSkin", "Eye", "Eyes", "Iris", "Eyeball", "Eyebrow", "Eyelash", "Eyeline",
              "Mouth", "Nose", "Ear", "Ears", "Cheek", "Highlight", "Shadow"]
BODY_SLOTS = ["Arm", "Chest", "Hand", "Head", "Leg", "Neck", "Shoulder", "Torso", "Waist", "WholeBody"]
SECTION_ORDER = ["Face", "Hairstyle", "Body", "Outfit", "Accessories", "Look"]

CATEGORY_LABELS = {
    "FaceSkin": "Face skin", "Eye": "Eyes", "Eyes": "Eyes", "Iris": "Irises",
    "Eyeball": "Eyeballs", "Eyebrow": "Eyebrows", "Eyelash": "Eyelashes", "Eyeline": "Eyeline",
    "Mouth": "Mouth", "Nose": "Nose", "Ear": "Ears", "Ears": "Ears", "Cheek": "Cheek",
    "Highlight": "Highlight", "Shadow": "Shadow",
    "AllHair": "All hair", "HairFront": "Front hair", "HairBack": "Back hair",
    "HairTied": "Tied hair", "HairSideburns": "Sideburns", "HairHanege": "Hanege",
    "HairAhoge": "Ahoge", "BaseHair": "Base hair",
    "Tops": "Tops", "Bottoms": "Bottoms", "Onepiece": "Onepiece", "Shoes": "Shoes",
    "Socks": "Socks", "InnerTop": "Inner top", "InnerBottom": "Inner bottom",
    "AccessoryNeck": "Neck accessory", "AccessoryArm": "Arm accessory",
    "ClothingSet": "Outfit set", "Attachment": "Attachment",
}


def _group_section(g):
    short = (g.get("type") or "").split(".")[-1]
    r = (g.get("resource") or "").lower()
    if short in HAIR_SLOTS or "/hair/" in r:
        return "Hairstyle"
    if "accessory" in short.lower() or "accessory" in r:
        return "Accessories"
    if short in OUTFIT_SLOTS + UNDERWEAR_SLOTS or "/clothing/" in r or short == "ClothingSet":
        return "Outfit"
    if short in FACE_SLOTS or "/face/" in r or "/eye/" in r or "/mouth/" in r:
        return "Face"
    if short in BODY_SLOTS or "/body/" in r:
        return "Body"
    return "Look"


def _humanize(text):
    text = re.sub(r"^Level\d+", "", text or "")
    text = text.replace("_", " ")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return " ".join(text.split()).strip()


def _category_label(short):
    return CATEGORY_LABELS.get(short) or _humanize(short) or short


def _group_records():
    rows = []
    for g in call_bridge("/groups"):
        short = (g.get("type") or "").split(".")[-1]
        section = _group_section(g)
        rows.append({
            "group": g.get("id"),
            "type": g.get("type"),
            "resource": g.get("resource"),
            "section": section,
            "category": short,
            "label": _category_label(short),
        })
    return rows


def _param_label(key):
    return _humanize(key)


def _enrich_param(p, section, category):
    key = p.get("key") or p.get("paramKey")
    return {**p, "label": _param_label(key), "path": f"{section}/{category}/{key}"}


def _resolve_group(section, category):
    sec = (section or "").strip().lower()
    cat = (category or "").strip().lower()
    if not sec or not cat:
        raise ValueError("missing parameter: section and category")
    rows = _group_records()
    match = [g for g in rows if g["section"].lower() == sec and
             (g["category"].lower() == cat or g["label"].lower() == cat)]
    if not match:
        sections = ", ".join(SECTION_ORDER)
        raise ValueError(f"unknown section/category: {section}/{category} (sections: {sections})")
    return match[0]


def _sections():
    groups = _group_records()
    out = []
    for name in SECTION_ORDER:
        rows = [g for g in groups if g["section"] == name]
        if not rows:
            continue
        cats = {}
        for g in rows:
            cats.setdefault(g["category"], {"category": g["category"], "label": g["label"],
                                            "groups": 0})
            cats[g["category"]]["groups"] += 1
        out.append({"section": name, "label": name, "groups": len(rows),
                    "categories": sorted(cats.values(), key=lambda c: c["label"])})
    return {"sections": out}


def _categories(section=None):
    groups = _group_records()
    if section:
        groups = [g for g in groups if g["section"].lower() == section.strip().lower()]
    out = {}
    for g in groups:
        item = out.setdefault(g["category"], {"category": g["category"], "label": g["label"],
                                              "section": g["section"], "groups": 0})
        item["groups"] += 1
    return {"section": section, "categories": sorted(out.values(), key=lambda c: (c["section"], c["label"]))}


def _enter(section, category):
    g = _resolve_group(section, category)
    params = [_enrich_param(p, g["section"], g["category"])
              for p in call_bridge("/params", query={"group": g["group"]})]
    return {**g, "pathPrefix": f"{g['section']}/{g['category']}", "params": params}


def _parse_param_value(kind, value):
    if kind == "color":
        s = str(value).strip()
        if s.startswith("#") and len(s) == 7:
            return {"r": int(s[1:3], 16) / 255, "g": int(s[3:5], 16) / 255, "b": int(s[5:7], 16) / 255}
        parts = [x for x in re.split(r"[, ]+", s) if x]
        if len(parts) >= 3:
            return {"r": float(parts[0]), "g": float(parts[1]), "b": float(parts[2])}
        raise ValueError("color value must be #RRGGBB or r,g,b (0..1)")
    return float(value)


def _set_param(section, category, param, value):
    g = _resolve_group(section, category)
    params = call_bridge("/params", query={"group": g["group"]})
    wanted = (param or "").strip().lower()
    exact = [p for p in params if str(p.get("key")).lower() == wanted or
             str(p.get("paramKey")).lower() == wanted]
    if exact:
        chosen = exact[0]
    else:
        matches = [p for p in params
                   if wanted in _humanize(p.get("key")).lower() or wanted in str(p.get("key")).lower()]
        if not matches:
            raise ValueError(f"unknown parameter: {param} (use vroid_enter to list keys/labels)")
        if len(matches) > 1:
            names = ", ".join(p.get("key") for p in matches[:8])
            raise ValueError(f"ambiguous parameter {param!r}; matches: {names}")
        chosen = matches[0]
    kind = chosen.get("kind")
    key = chosen.get("key") or chosen.get("paramKey")
    if kind == "color":
        rgb = _parse_param_value("color", value)
        result = call_bridge("/set_color", body={"group": g["group"], "key": key, **rgb})
    elif kind == "bone":
        result = call_bridge("/set_bone", body={"group": g["group"], "key": key,
                                                 "value": float(value)})
    elif kind == "blendshape":
        result = call_bridge("/set_blendshape", body={"group": g["group"], "key": key,
                                                       "value": float(value)})
    else:
        raise ValueError(f"unsupported parameter kind: {kind}")
    return {"ok": True, "group": g["group"], "section": g["section"], "category": g["category"],
            "param": key, "kind": kind, "value": value,
            "path": f"{g['section']}/{g['category']}/{key}", "result": result}


def frame_region(category):
    """Cadre le personnage entier / la zone utile, de face et centré.

    Le centre du modèle n'est pas supposé être à x=0, z=0 : on lit ses bounds et on place
    la caméra devant ce centre, après un reset qui remet l'orientation de face. C'est ce qui
    garantit que la pièce testée est au milieu de la vignette, même après un preset qui a
    déplacé la caméra."""
    m = call_bridge("/measure")
    h = m["boundsMaxY"]
    cx = m.get("centerX", 0.0)
    cz = m.get("centerZ", 0.0)
    profile = preset_cache.framing_for(category)
    top, bottom = h * (1 - profile["top"]), h * (1 - profile["bottom"])
    span = max(top - bottom, 0.14 * h) * 1.1
    cy = (top + bottom) / 2

    # Une tenue complète (ClothingSet) inclut les chaussures : distance plus grande dans
    # la conf (fit=full-body), pour que les pieds restent dans le cadre.
    full_outfit = profile.get("fit") == "full-body"
    distance = float(profile.get("distance") or 3.3) * span
    yaw = float(profile.get("yaw") or 0)
    # Repère : caméra de face à +Z ; yaw > 0 tourne autour du modèle (90 = profil, 180 = dos).
    rad = math.radians(yaw)
    px = cx + distance * math.sin(rad)
    pz = cz + distance * math.cos(rad)

    call_bridge("/camera", body={"action": "reset"})
    time.sleep(0.6)
    call_bridge("/camera", body={
        "action": "custom",
        "px": px, "py": cy, "pz": pz,
        "cx": cx, "cy": cy, "cz": cz,
    })
    time.sleep(1.3)  # la caméra se déplace en douceur : attendre la fin avant de capturer
    return {
        "region": category,
        "front": yaw == 0,
        "yaw": yaw,
        "fit": "full-body" if full_outfit else "region",
        "profileSource": profile.get("source"),
        "profileKey": profile.get("profileKey"),
        "center": [round(cx, 4), round(cy, 4), round(cz, 4)],
        "position": [round(px, 4), round(cy, 4), round(pz, 4)],
        "span": round(span, 4),
        "boundsMaxY": round(h, 4),
    }


def strip_mannequin(keep_slot=None):
    """Retire tous les vêtements, accessoires, sous-vêtements (sauf keep_slot) et les cheveux
    (sauf BaseHair et la partie capturée). Vérifie qu'il ne reste rien avant de capturer.

    Les sous-vêtements par défaut sont retirés aussi : sur un maillot de bain ou une pièce
    près du corps, ils dépassent et faussent la vignette. Le modèle est nu, seule la pièce
    testée reste."""
    before = _active_slots()
    removed = []
    seen = set()

    def remove_slot(slot):
        groups = before.get(slot) or []
        if not groups:
            groups = [g for g in _slot_groups([slot])]
        r = call_bridge("/remove_group", body={"group": slot}, timeout=120)
        if not r.get("ok"):
            return False
        for g in groups:
            if g["id"] not in seen:
                seen.add(g["id"])
                removed.append(dict(g, slot=slot))
        return True

    # Les groupes actifs sont retirés, puis on refait un passage : VRoid peut recréer un
    # sous-vêtement par défaut après le retrait d'un vêtement.
    for slot in OUTFIT_SLOTS + UNDERWEAR_SLOTS:
        if slot == keep_slot or slot not in before:
            continue
        remove_slot(slot)
    for slot in list(_active_slots()):
        if slot != keep_slot and slot in OUTFIT_SLOTS + UNDERWEAR_SLOTS:
            remove_slot(slot)

    # Cheveux retirés aussi (ils cachent buste, dos et visage) : seuls restent les cheveux de base
    # (calotte) et, pour une capture de cheveux, la partie capturée. Une coiffure complète (AllHair)
    # remplace tout.
    hair_removed = []
    if keep_slot != "AllHair":
        for hair in _slot_groups([s for s in HAIR_SLOTS if s not in ("BaseHair", keep_slot)]):
            r = call_bridge("/remove_group", body={"group": hair["id"]}, timeout=120)
            if r.get("ok"):
                removed.append(hair)
                hair_removed.append(hair["slot"])

    left_slots = _active_slots()
    left = [s for s in left_slots if s in OUTFIT_SLOTS + UNDERWEAR_SLOTS and s != keep_slot]
    underwear_removed = [g["slot"] for g in removed if g.get("slot") in UNDERWEAR_SLOTS]
    return {"before": before, "removed": removed, "stillWorn": left,
            "underwearRemoved": sorted(set(underwear_removed)),
            "hairRemoved": sorted(set(hair_removed))}


def dress_back(state, built_slot):
    """Remet exactement la tenue d'origine.

    On retire d'abord tout ce qui est porté (vêtements, sous-vêtements, cheveux sauf
    BaseHair), y compris ce que le preset testé a pu ajouter, puis on recharge les groupes
    d'origine mémorisés par strip_mannequin. Cela évite qu'un sous-vêtement par défaut ou
    une pièce du preset reste après la génération."""
    failed = []
    for slot in OUTFIT_SLOTS + UNDERWEAR_SLOTS:
        try:
            call_bridge("/remove_group", body={"group": slot}, timeout=120)
        except Exception:
            pass
    for hair in _slot_groups([s for s in HAIR_SLOTS if s != "BaseHair"]):
        try:
            call_bridge("/remove_group", body={"group": hair["id"]}, timeout=120)
        except Exception:
            pass
    # L'emplacement testé était conservé par strip_mannequin : il n'est pas dans "removed",
    # mais le preset/custom l'a remplacé. Il faut donc le remettre aussi.
    for g in state.get("slotOrig", []):
        if not _put_back(g):
            failed.append(g)
    for g in state.get("removed", []):
        if not _put_back(g):
            failed.append(g)
    return failed


def _custom_file_for(resource, gid=None):
    """Fichier .vroidcustomitem d'un groupe porté, retrouvé dans le cache par sa ressource ou son id de groupe."""
    for e in preset_cache.load()["presets"].values():
        if e.get("kind") == "custom" and not e.get("removed") and                 ((resource and e.get("groupResource") == resource) or (gid and e.get("id") == gid)):
            return e.get("file")
    return None


def _put_back(g):
    """Remet un groupe retiré. Objet personnalisé : TOUJOURS depuis son fichier (recharger son id bloque VRoid,
    car il n'est pas dans ses données). Preset : par son id."""
    if (g.get("resource") or "").startswith("user/") or g["id"].startswith("user_"):
        f = _custom_file_for(g.get("resource"), g.get("id"))
        return bool(f) and call_bridge("/apply_custom", body={"file": f}, timeout=180).get("ok", False)
    try:
        return bool(call_bridge("/load_group", body={"id": g["id"]}, timeout=120).get("ok"))
    except Exception:
        return False


def cache_build(category, refresh=False, limit=None):
    """Captures en situation d'une catégorie sur un mannequin nu (sans vêtements, sous-vêtements
    ni cheveux, sauf la pièce testée), caméra de face centrée, puis remise de la tenue d'origine.
    Les tenues complètes sont cadrées plus large pour que les chaussures restent visibles.
    Enregistrer le modèle avant : la restauration n'est pas garantie à l'identique."""
    cache_sync()
    custom = category.startswith("Custom/")
    if custom:
        live = [{"key": k, "file": e["file"], "resource": k} for k, e in preset_cache.load()["presets"].items()
                if e.get("kind") == "custom" and e.get("category") == category and not e.get("removed")]
        slot = category.split("/", 1)[1]
    else:
        live = call_bridge("/presets", query={"limit": 100000, "filter": category.split("/")[-1]})["presets"]
        live = [x for x in live if preset_cache.category_of(x["resource"])[0] == category]
        slot = preset_cache.slot_of(live[0]["resource"]) if live else None
    if not live:
        return {"category": category, "error": "rien dans cette catégorie"}
    try:
        st = call_bridge("/context_state")
        if not st.get("commandExecutable") or st.get("modifyingEditingModel"):
            return {"category": category, "error": "VRoid n'est pas prêt (modification en cours ou contexte bloqué)",
                    "state": st}
    except Exception:
        pass  # plugin antérieur à 0.12
    # Élément(s) d'origine de l'emplacement capturé (cheveux : toutes les parties de la coiffure).
    slot_orig = [g for g in _slot_groups(HAIR_SLOTS if slot in HAIR_SLOTS else [slot])
                 if g.get("slot") != "BaseHair"]
    state = strip_mannequin(keep_slot=slot)
    state["slotOrig"] = slot_orig
    camera_info = None
    try:
        camera_info = frame_region(category)
    except Exception:
        pass
    done, skipped, failed = 0, 0, []
    stripped_all = {g.get("slot") for g in state["removed"] if g.get("slot")}
    underwear_all = set(state.get("underwearRemoved", []))
    hair_all = set(state.get("hairRemoved", []))
    tmp = os.path.join(preset_cache.ROOT, "_capture.png")
    try:
        if state["stillWorn"]:
            return {"category": category, "error": f"impossible de retirer : {state['stillWorn']}"}
        for x in live:
            if limit and done >= int(limit):
                break
            e = preset_cache.get(x["resource"])
            if e.get("thumbnail") and not refresh and os.path.exists(os.path.join(preset_cache.ROOT, e["thumbnail"])):
                skipped += 1
                continue
            if custom:
                r = call_bridge("/apply_custom", body={"file": x["file"]}, timeout=180)
            else:
                r = call_bridge("/apply_preset", body={"id": x["id"]}, timeout=120)
            if not r.get("ok"):
                # Arrêt à la première erreur : continuer sur un VRoid en mauvais état empire les choses.
                failed.append({"item": x["resource"], "error": r.get("message") or r.get("error")})
                break

            # Le preset peut ajouter un sous-vêtement par défaut ou d'autres pièces.
            # On retire toujours les sous-vêtements (sauf si c'est la pièce testée) et les
            # autres emplacements de vêtements. Sans ça, un maillot de bain est capturé
            # avec une culotte/soutien-gorge qui dépasse.
            for s in UNDERWEAR_SLOTS:
                if s == slot:
                    continue
                try:
                    rr = call_bridge("/remove_group", body={"group": s}, timeout=120)
                    if rr.get("ok"):
                        stripped_all.add(s)
                        underwear_all.add(s)
                except Exception:
                    pass
            if slot in OUTFIT_SLOTS:
                for s in [k for k in _active_slots() if k in OUTFIT_SLOTS and k != slot]:
                    try:
                        rr = call_bridge("/remove_group", body={"group": s}, timeout=120)
                        if rr.get("ok"):
                            stripped_all.add(s)
                    except Exception:
                        pass

            # Une tenue complète garde Tops/Bottoms/Shoes du set : on ne vérifie que
            # l'absence de sous-vêtements. Pour une pièce seule, tout le reste doit être nu.
            forbidden = UNDERWEAR_SLOTS if category == "VRoid/ClothingSet" else OUTFIT_SLOTS + UNDERWEAR_SLOTS
            left = [s for s in _active_slots() if s in forbidden and s != slot]
            if left:
                failed.append({"item": x["resource"], "error": f"vêtements restants : {left}"})
                break

            # Certains éléments (robes, hauts, peau) font recadrer VRoid : on recadre avant chaque capture.
            try:
                camera_info = frame_region(category)
            except Exception:
                time.sleep(1.5)
            # Thumbnails are cropped from the full window: keep the UI panels for crop_center.
            call_bridge("/screenshot", body={"path": tmp, "clean": False})
            rel = preset_cache.thumb_rel(e)
            out = os.path.join(preset_cache.ROOT, rel)
            try:
                preset_cache.crop_center(tmp, category, out)
                info = preset_cache.image_info(out)
                meta = {
                    "kind": "situation",
                    "capturedAt": preset_cache.now(),
                    "mannequin": "neutral",
                    "clothing": ("tested-set-only" if category == "VRoid/ClothingSet"
                                 else ("tested-item-only" if slot in OUTFIT_SLOTS + UNDERWEAR_SLOTS else "none")),
                    "underwear": "tested-item-only" if slot in UNDERWEAR_SLOTS else "removed",
                    "hair": "tested-item-only" if slot in HAIR_SLOTS else "removed-except-base",
                    "orientation": _orientation_label((camera_info or {}).get("yaw")),
                    "keptSlot": slot,
                    "category": category,
                    "custom": bool(custom),
                    "strippedSlots": sorted(stripped_all),
                    "underwearRemoved": sorted(underwear_all),
                    "hairRemoved": sorted(hair_all),
                    "camera": camera_info,
                    "pixels": info["pixels"],
                    "bytes": info["bytes"],
                    "sha1": info["sha1"],
                    "source": "vroid-screenshot-crop",
                }
                preset_cache.set_thumbnail(x["resource"], rel, meta)
                done += 1
            except Exception as ex:  # capture inexploitable : on continue
                failed.append(f"{x['resource']}: {ex}")
    finally:
        not_restored = dress_back(state, slot)
        try:
            call_bridge("/camera", body={"action": "reset"})
        except Exception:
            pass
        if os.path.exists(tmp):
            os.remove(tmp)
    return {"category": category, "created": done, "skipped": skipped, "failed": failed,
            "mannequin": "neutral", "stripped": sorted(stripped_all),
            "underwearRemoved": sorted(underwear_all), "hairRemoved": sorted(hair_all),
            "camera": camera_info, "notRestored": not_restored}


def _colorize(args):
    """Apply one color to both the global/material colors and the texture layers.

    This is the composite counterpart of vroid_set_color + vroid_recolor_layer: fine-grained
    tools remain available, while this one does the common "make this item this colour" pass.
    """
    group = args.get("group")
    if not group:
        raise ValueError("missing parameter: group")
    r, g, b = float(args.get("r", 0)), float(args.get("g", 0)), float(args.get("b", 0))
    target = (args.get("target") or "both").lower()
    if target not in ("global", "texture", "both"):
        raise ValueError("target must be global, texture or both")
    mode = (args.get("mode") or "multiply").lower()
    strength = float(args.get("strength", 1))
    only_layer = args.get("layer")
    only_material = args.get("material")
    warnings, global_changed, texture_changed = [], [], []

    group_type = ""
    try:
        for item in call_bridge("/groups"):
            if item.get("id") == group:
                group_type = (item.get("type") or "").split(".")[-1]
                break
    except Exception as e:
        warnings.append(f"groups: {e}")
    is_hair = "Hair" in group_type

    if target in ("global", "both"):
        if is_hair:
            try:
                mats = call_bridge("/hair_materials")
                for mat in mats:
                    if only_material and mat.get("material") != only_material:
                        continue
                    for color in mat.get("colors") or []:
                        key = color.get("key")
                        if not key:
                            continue
                        try:
                            call_bridge("/set_hair_color", body={
                                "material": mat["material"], "key": key, "r": r, "g": g, "b": b},
                                timeout=60)
                            global_changed.append({"material": mat["material"], "key": key,
                                                   "label": color.get("label")})
                        except Exception as e:
                            warnings.append(f"hair {key}: {e}")
            except Exception as e:
                warnings.append(f"hair materials: {e}")
        else:
            try:
                data = call_bridge("/clothing_colors", body={"group": group}, timeout=60)
                for color in data.get("colors") or []:
                    key = color.get("key")
                    if not key:
                        warnings.append(f"global color without key: {color.get('label')}")
                        continue
                    try:
                        call_bridge("/set_color", body={
                            "group": color.get("group") or group, "key": key,
                            "r": r, "g": g, "b": b}, timeout=60)
                        global_changed.append({"group": color.get("group") or group, "key": key,
                                               "label": color.get("label")})
                    except Exception as e:
                        warnings.append(f"global {key}: {e}")
            except Exception as e:
                # Not every group is a clothing item; texture-only is still useful.
                warnings.append(f"global colors: {e}")

    if target in ("texture", "both"):
        try:
            if is_hair:
                # Hair textures live under hair materials, not under /layers(group). They only
                # become editable after begin_hair_edit.
                mats = call_bridge("/hair_materials", timeout=60)
                for mat in mats:
                    if only_material and mat.get("material") != only_material:
                        continue
                    try:
                        call_bridge("/begin_hair_edit", body={"material": mat["material"]}, timeout=180)
                    except Exception as e:
                        warnings.append(f"begin hair edit: {e}")
                mats = call_bridge("/hair_materials", timeout=60)
                for mat in mats:
                    if only_material and mat.get("material") != only_material:
                        continue
                    for tex in mat.get("textures") or []:
                        layers = tex.get("layers")
                        if not isinstance(layers, list):
                            continue
                        for layer in layers:
                            node = layer.get("node")
                            if only_layer and node != only_layer:
                                continue
                            try:
                                call_bridge("/recolor_layer", body={
                                    "transferable": tex.get("transferable"), "image": tex.get("image"),
                                    "node": node, "r": r, "g": g, "b": b, "mode": mode,
                                    "strength": strength}, timeout=180)
                                texture_changed.append({"transferable": tex.get("transferable"),
                                                        "image": tex.get("image"), "node": node})
                            except Exception as e:
                                warnings.append(f"hair texture {node}: {e}")
                if not texture_changed:
                    warnings.append("hair texture layers are not exposed; global hair colors were used")
            else:
                layers = call_bridge("/layers", body={"group": group}, timeout=60)
                has_images = any((item.get("images") or []) for item in layers)
                if not has_images:
                    call_bridge("/begin_clothing_edit", body={"group": group}, timeout=180)
                    layers = call_bridge("/layers", body={"group": group}, timeout=60)
                for item in layers:
                    for image in item.get("images") or []:
                        for layer in image.get("layers") or []:
                            node = layer.get("node")
                            if only_layer and node != only_layer:
                                continue
                            try:
                                call_bridge("/recolor_layer", body={
                                    "transferable": item.get("transferable"), "image": image.get("image"),
                                    "node": node, "r": r, "g": g, "b": b, "mode": mode,
                                    "strength": strength}, timeout=180)
                                texture_changed.append({"transferable": item.get("transferable"),
                                                        "image": image.get("image"), "node": node})
                            except Exception as e:
                                warnings.append(f"texture {node}: {e}")
        except Exception as e:
            warnings.append(f"texture layers: {e}")

    return {
        "ok": bool(global_changed or texture_changed),
        "group": group,
        "target": target,
        "globalChanged": len(global_changed),
        "textureChanged": len(texture_changed),
        "global": global_changed,
        "textures": texture_changed,
        "warnings": warnings,
    }


def _run_batch(args):
    """Sequential batch executor. Images are returned as MCP content, not duplicated as base64 text."""
    ops = args.get("operations")
    if not isinstance(ops, list) or not ops:
        raise ValueError("operations must be a non-empty array")
    if len(ops) > 200:
        raise ValueError("at most 200 operations per batch")
    stop_on_error = args.get("stop_on_error", True)
    if isinstance(stop_on_error, str):
        stop_on_error = stop_on_error.lower() not in ("false", "0", "no")
    include_images = args.get("include_images", True)
    if isinstance(include_images, str):
        include_images = include_images.lower() not in ("false", "0", "no")

    max_images, max_bytes = 8, 16 * 1024 * 1024
    results, images = [], []
    image_bytes = 0
    failed = 0
    stopped_at = None
    for index, op in enumerate(ops):
        if not isinstance(op, dict) or not op.get("tool"):
            results.append({"index": index, "ok": False, "error": "operation must have a tool name"})
            failed += 1
            if stop_on_error:
                stopped_at = index
                break
            continue
        tool = str(op["tool"])
        if tool in ("vroid_batch", "vroid_help", "vroid_exit"):
            results.append({"index": index, "tool": tool, "ok": False,
                            "error": "nested batches, help and quit are not allowed inside a batch"})
            failed += 1
            if stop_on_error:
                stopped_at = index
                break
            continue
        op_args = op.get("args") or {}
        if not isinstance(op_args, dict):
            results.append({"index": index, "tool": tool, "ok": False, "error": "args must be an object"})
            failed += 1
            if stop_on_error:
                stopped_at = index
                break
            continue
        try:
            out = run_tool(tool, op_args)
            is_error = isinstance(out, dict) and (out.get("error") or out.get("http_status", 200) >= 400)
            clean = {}
            image = None
            if isinstance(out, dict):
                for k, v in out.items():
                    if k == "__image__":
                        image = v
                    elif k not in ("__mime__", "__text__"):
                        clean[k] = v
            else:
                clean = out
            if isinstance(clean, dict) and "error" in clean:
                is_error = True
            if is_error:
                failed += 1
            entry = {"index": index, "tool": tool, "ok": not is_error, "result": clean}
            results.append(entry)
            if image and include_images:
                approx = len(image) * 3 // 4
                if len(images) >= max_images or image_bytes + approx > max_bytes:
                    entry["imageOmitted"] = "batch image cap reached (8 images / 16 MiB)"
                else:
                    images.append({"index": index, "tool": tool, "mimeType": out.get("__mime__", "image/png"),
                                   "data": image})
                    entry["image"] = len(images)
                    image_bytes += approx
            if is_error and stop_on_error:
                stopped_at = index
                break
        except Exception as e:
            failed += 1
            results.append({"index": index, "tool": tool, "ok": False, "error": str(e)})
            if stop_on_error:
                stopped_at = index
                break
    summary = {
        "ok": failed == 0,
        "requested": len(ops),
        "executed": len(results),
        "failed": failed,
        "stopped_at": stopped_at,
        "images": len(images),
        "results": results,
    }
    if stopped_at is not None:
        summary["hint"] = "Execution stopped at the first error. Fix it, or pass stop_on_error=false to continue."
    return {"__batch__": summary, "__images__": images}


def run_tool(name, args):
    if name == "vroid_batch":
        return _run_batch(args)
    if name == "vroid_help":
        lang = help_i18n.normalize_lang(args.get("lang"))
        topic = args.get("topic") or "overview"
        return {"__text__": help_i18n.help_text(topic, lang, TOOLS), "topic": topic, "lang": lang}
    if name == "vroid_status":
        return call_bridge("/status")
    if name == "vroid_create":
        return call_bridge("/create", body={"gender": args["gender"]}, timeout=180)
    if name == "vroid_open":
        return call_bridge("/open", body={"path": args["path"]}, timeout=180)
    if name == "vroid_save":
        body = {"path": args["path"]} if args.get("path") else {}
        return call_bridge("/save", body=body, timeout=180)
    if name == "vroid_export_vrm":
        keys = ("path", "version", "title", "author", "model_version", "delete_transparent", "hair_cross_section",
                "hair_smoothness", "hair", "face", "body", "outfit", "material_mode", "combine_hair",
                "texture_mode", "atlas_resolution", "hair_bones", "leave")
        body = {k: (("true" if args[k] else "false") if isinstance(args[k], bool) else args[k])
                for k in keys if k in args and args[k] is not None}
        return call_bridge("/vrm_export", body=body, timeout=900)
    if name == "vroid_export_vrm_options":
        res = call_bridge("/vrm_export_options", timeout=180)
        if args.get("leave", True):
            call_bridge("/vrm_export_leave", timeout=60)
        return res
    if name == "vroid_main_menu":
        return call_bridge("/main_menu", body={"discard": "true" if args.get("discard") else "false"}, timeout=60)
    if name == "vroid_exit":
        return call_bridge("/exit", body={"discard": "true" if args.get("discard") else "false"}, timeout=30)
    if name == "vroid_framing_get":
        return preset_cache.framing_get(args.get("category"))
    if name == "vroid_framing_set":
        updates = {k: args[k] for k in ("top", "bottom", "half", "distance", "yaw", "fit") if k in args}
        return preset_cache.set_framing(args["category"], updates)
    if name == "vroid_framing_reset":
        return preset_cache.reset_framing(args.get("category"))
    if name == "vroid_preset_cache_search":
        return _with_paths(preset_cache.search(args.get("query"), args.get("category"),
                                               not args.get("include_locked"), bool(args.get("annotated_only")),
                                               int(args.get("limit") or 50), args.get("kind"),
                                               bool(args.get("include_removed")), args.get("status")))
    if name == "vroid_preset_cache_annotate":
        return preset_cache.annotate(args["key"], args["author"], args.get("description"), args.get("tags"),
                                     args.get("colors"), bool(args.get("replace")), args.get("label"))
    if name == "vroid_preset_thumbnail":
        e = preset_cache.get(args["key"])
        path = preset_cache.thumb_path(e)
        if not path and e.get("kind", "preset") == "preset" and not e.get("iconMissing"):
            fetch_icon(e)
            path = preset_cache.thumb_path(preset_cache.get(args["key"]))
        if not path or not os.path.exists(path):
            return {"error": "pas de vignette pour cet élément"}
        with open(path, "rb") as f:
            mime = "image/png" if path.endswith(".png") else "image/jpeg"
            return {"__image__": base64.b64encode(f.read()).decode("ascii"), "__mime__": mime}
    if name == "vroid_preset_cache_sync":
        return cache_sync(bool(args.get("icons")), args.get("icon_limit"))
    if name == "vroid_preset_cache_build":
        return cache_build(args["category"], bool(args.get("refresh")), args.get("limit"))
    if name == "vroid_begin_hair_edit":
        return call_bridge("/begin_hair_edit", body={"material": args["material"]})
    if name == "vroid_face_preview":
        if "name" not in args and "weight" not in args:
            return call_bridge("/face_blendshapes", query={"filter": args.get("filter", "")})
        return call_bridge("/face_preview", body={"name": args.get("name", ""), "weight": args.get("weight", 100)})
    if name == "vroid_apply_custom":
        f = args.get("file") or preset_cache.get(args["key"]).get("file")
        return call_bridge("/apply_custom", body={"file": f}, timeout=180)
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
    if name == "vroid_get_item_params":
        q = {"type": args["type"]} if args.get("type") else {}
        return call_bridge("/item_params", query=q)
    if name == "vroid_sections":
        return _sections()
    if name == "vroid_categories":
        return _categories(args.get("section"))
    if name == "vroid_enter":
        return _enter(args["section"], args["category"])
    if name == "vroid_set_param":
        return _set_param(args["section"], args["category"], args["param"], args["value"])
    if name == "vroid_set_blendshape":
        return call_bridge("/set_blendshape", body=args)
    if name == "vroid_set_bone":
        return call_bridge("/set_bone", body=args)
    if name == "vroid_set_color":
        return call_bridge("/set_color", body=args)
    if name == "vroid_colorize":
        return _colorize(args)
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
        body = {k: args[k] for k in ("msaa", "ssaa", "width", "height", "clean") if k in args}
        res = call_bridge("/screenshot", body=body, timeout=120)
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
            "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
            "serverInfo": {"name": "vroid-studio", "version": "0.14.0"},
            "instructions": help_i18n.INITIALIZE_INSTRUCTIONS,
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "resources/list":
        return agent_resources()
    if method == "resources/read":
        return read_agent_resource(params.get("uri"))
    if method == "prompts/list":
        return {"prompts": prompts.PROMPTS}
    if method == "prompts/get":
        return prompts.get(params.get("name"), params.get("arguments"), TOOLS)
    if method == "tools/call":
        try:
            name = params["name"]
            # Help must work even when VRoid is closed: no cache scan, no bridge call.
            notice = None if name == "vroid_help" else maybe_scan()
            out = run_tool(name, params.get("arguments") or {})
            if isinstance(out, dict) and "__batch__" in out:
                content = [{"type": "text", "text": json.dumps(out["__batch__"], ensure_ascii=False, indent=1)}]
                for img in out.get("__images__", []):
                    content.append({"type": "image", "data": img["data"],
                                    "mimeType": img.get("mimeType", "image/png")})
            elif isinstance(out, dict) and "__image__" in out:
                content = [{"type": "image", "data": out["__image__"], "mimeType": out.get("__mime__", "image/png")}]
            elif isinstance(out, dict) and "__text__" in out:
                content = [{"type": "text", "text": out["__text__"]}]
            else:
                content = [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=1)}]
            if notice:
                content.insert(0, {"type": "text", "text": notice})
            if isinstance(out, dict) and "__batch__" in out:
                is_err = not out["__batch__"].get("ok", False)
            else:
                is_err = isinstance(out, dict) and "error" in out
            return {"content": content, "isError": is_err}
        except Exception as e:  # error returned to the AI instead of crashing the server
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
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
                     "error": {"code": -32601, "message": f"unknown method: {msg.get('method')}"}}
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
