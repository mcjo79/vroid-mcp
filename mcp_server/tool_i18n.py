"""English tool metadata.

The MCP transport is international: tool names and argument descriptions are English.
French and Japanese are provided by the help layer (see help_i18n.py), not by duplicating
the tool schema in every language.
"""

EN_TOOL_DESCRIPTIONS = {
    "vroid_export_vrm": "Export the open model as a .vrm file with VRoid's own exporter, without clicks or file dialog "
                       "(same options as the 'Export as VRM' screen). Options left out use VRoid's defaults: "
                       "VRM 1.0, transparent meshes deleted, no reduction. Takes about 10-40 s. "
                       "Reduction sliders are 0..100. material_mode: 0 Default, 1 = 2 materials, 2 = 8, 3 = 12. "
                       "Texture size: with material_mode 0 use texture_mode 1 (Shrunk); with material reduction VRoid "
                       "uses the atlas instead, so use atlas_resolution 1 (2048) to shrink textures. "
                       "Any option VRoid refused is listed in 'warnings'. The model itself is not modified.",
    "vroid_export_vrm_options": "Open VRoid's export screen and return its current export settings and the available "
                       "material / texture / atlas choices. Close it again with vroid_export_vrm or by passing leave.",
    "vroid_batch": "Run several vroid_* operations sequentially in one MCP call and return a text summary plus "
                   "optional images. Up to 200 operations, no nested batches, no automatic rollback. stop_on_error "
                   "defaults to true. Images are capped (8 images / 16 MiB); excess images are reported by path only. "
                   "Save before destructive sequences.",
    "vroid_help": "Show the built-in manual. Topics: overview, tools, lifecycle, export, framing, thumbnails, colors, "
                  "outfit, sessions, errors, languages, batch. lang=en|fr|ja. Call this first when unsure.",
    "vroid_status": "Report whether VRoid Studio responds, whether a model is open, its current file, whether it "
                    "has unsaved changes (dirty) and whether the editor is ready.",
    "vroid_create": "Create a new model from the VRoid template (female or male), like the Create New Model dialog. "
                    "VRoid must be at the model-select screen (no model open). Blocks until the model is ready. "
                    "The new model has no file yet: use vroid_save with path to save it.",
    "vroid_open": "Open a .vroid file and wait until the model is ready. VRoid must be at the model-select screen "
                  "(no model open): save and call vroid_main_menu first if needed. path must be absolute.",
    "vroid_save": "Save the open model. With path: Save As (creates the file). Without path: save in place, only if "
                  "the model already has a .vroid file. A model created with vroid_create has no file yet: pass path.",
    "vroid_main_menu": "Return to the model-select screen without quitting VRoid, so another model can be opened or "
                       "created. Refuses when there are unsaved changes unless discard=true.",
    "vroid_exit": "Quit VRoid Studio gracefully. Refuses unsaved changes unless discard=true. The response is sent "
                  "before the process exits; use it after a generation sequence.",
    "vroid_framing_get": "Read thumbnail framing profiles per category/body part (e.g. Clothing/Tops, Clothing/Shoes, "
                         "Hair, Face, VRoid/ClothingSet), never per individual garment: garment facts stay in the "
                         "cache. top/bottom are fractions from the top of the model (0 = top, 1 = feet), half is the "
                         "half-width (null = full width), distance is the zoom-out factor, yaw is the orientation in "
                         "degrees (0 = front, 90 = profile, 180 = back), fit=region|full-body. Without category: all "
                         "known categories.",
    "vroid_framing_set": "Change the framing of a category/body part (e.g. Clothing/Tops, Clothing/Shoes, Hair, Face, "
                         "VRoid/ClothingSet), never an individual garment: the override is local and does not modify "
                         "committed defaults. top/bottom in 0..1, half null or 0.01..1, distance 1..10, yaw -180..180 "
                         "(0 = front, 90 = profile, 180 = back), fit=region|full-body. vroid_framing_reset restores "
                         "the defaults.",
    "vroid_framing_reset": "Clear framing overrides (all, or one category/body part) and return to the committed "
                           "defaults in config/framing.json. Local overrides live in "
                           "preset_cache/framing_overrides.json.",
    "vroid_list_groups": "List the editable groups of the open model (face, eyes, hair, body, outfits...). Each group "
                         "has an id to pass to the other tools.",
    "vroid_sections": "List editable sections and their categories (Face, Hairstyle, Body, Outfit, Accessories, "
                      "Look), with group counts. High-level companion to vroid_list_groups.",
    "vroid_categories": "List categories in a section (or all categories), with category key, label, section and "
                        "group count. Use with vroid_enter / vroid_set_param.",
    "vroid_enter": "Select a section/category by name and return its group and enriched parameters (labels + stable "
                   "section/category/key paths). Equivalent in spirit to enter(), without changing VRoid's UI tab.",
    "vroid_set_param": "Set a parameter by section/category and key or short label; dispatches to bone, blendshape "
                       "or color. Accepts numbers, #RRGGBB or r,g,b for colors. Unified counterpart of "
                       "vroid_set_bone / vroid_set_blendshape / vroid_set_color.",
    "vroid_get_params": "List the parameters of a group (blendshape sliders, bones, colors) with their current values.",
    "vroid_get_item_params": "List every adjustable parameter of the model's items, including the shape sliders VRoid shows under Customize > Parameters for clothing and accessories (skirt tighter/wider/shorter/longer, sleeve thickness, width, length, hood...), which vroid_get_params does not return. Each group has 'pars' (regular parameters) and 'sliders' (key, label, value). Clothing sliders range 0..100 (not 0..1); the last word of the label says what they do (Narrow = tighter, Spread = wider, Short, Long...). Set one with vroid_set_blendshape group=<group> key=<slider key> value=<0..100>; undoable. 'type' filters by group type, e.g. TransferableGroupType.N00.Level1.Bottoms.",
    "vroid_set_blendshape": "Set a shape slider (blendshape) of a group. Undoable in VRoid (Ctrl+Z). Also sets clothing/accessory preset sliders: pass a 'template:...' key from vroid_get_item_params (values 0..100). Returns the value read back from VRoid.",
    "vroid_set_bone": "Set a bone transform parameter (body proportions, size...).",
    "vroid_set_color": "Set a color (components 0..1). Undoable in VRoid.",
    "vroid_colorize": "Composite color pass: apply one color to both the global/material colors and the texture layers "
                      "of a group (clothing or hair). target=global|texture|both. Fine-grained vroid_set_color / "
                      "vroid_recolor_layer remain available. Undoable; hair textures may not be exposed, in which case "
                      "a warning is returned.",
    "vroid_list_layers": "List the editable textures of a group (e.g. skirt = Bottoms): items (transferable), images "
                         "and layers (node, name, opacity, visibility, blend mode). Clothes have no color sliders: "
                         "their color is changed through their texture layers.",
    "vroid_recolor_layer": "Recolor a texture layer in place, preserving transparency; undoable. mode 'multiply': light "
                           "fabric -> target color while keeping shadows and folds. mode 'colorize': keeps luminance, "
                           "forces the hue (for already colored fabric).",
    "vroid_export_layer": "Export a texture layer as PNG (RGBA) to edit it with another tool.",
    "vroid_import_layer": "Import a PNG into a layer (same size as the export) or as a new layer. Undoable.",
    "vroid_list_hair_materials": "List hair materials (hair color is not exposed by vroid_get_params): id, name, "
                                 "adjustable colors (key + value) and textures with their layers (transferable/image/"
                                 "node usable with vroid_recolor_layer).",
    "vroid_set_hair_color": "Set a color of a hair material (components 0..1). Undoable. 'base:<id>' keys are the "
                            "overlay hair tint of a preset: change that key to recolor a preset hairstyle (material "
                            "is optional in that case). For hair whose color is painted in the texture, recolor the "
                            "layers instead (mode colorize).",
    "vroid_list_hair_groups": "List hair groups: 'procedural' (adjustable length and strand count) or 'brush' (drawn "
                              "strands: strand count, average length).",
    "vroid_set_procedural_hair": "Set the length and/or strand count of a procedural hair group. Undoable.",
    "vroid_scale_brush_hair": "Lengthen (factor > 1) or shorten (factor < 1) all strands of a brush hair group from "
                              "their root. Undoable (one step per point).",
    "vroid_clone_brush_hair": "Duplicate a group of brush strands and offset the copy (in meters, model space) to add "
                              "strands.",
    "vroid_undo": "Undo the last change in VRoid Studio.",
    "vroid_redo": "Redo the last undone change.",
    "vroid_screenshot": "Capture a clean 3D preview of the avatar (no VRoid UI) and return the image. MSAA 4x and "
                        "SSAA 2x by default; width/height override the output size; clean=false captures the whole "
                        "window. Use it to inspect edits accurately.",
    "vroid_list_presets": "List VRoid presets (hairstyles, faces, outfits, bodies...). filter searches the resource "
                          "path (e.g. 'Hair', 'Tops', 'Bottoms', 'Onepiece', 'Shoes', 'Face'). Also returns the list "
                          "of categories. Only free or owned presets are listed unless include_locked.",
    "vroid_apply_preset": "Apply a preset (replaces the item in the same category, like clicking its thumbnail). "
                          "Undoable. Whole-set presets can replace several slots: verify with vroid_list_groups.",
    "vroid_clothing_colors": "List the adjustable colors of a clothing item (same preset): group + key to pass to "
                             "vroid_set_color.",
    "vroid_begin_clothing_edit": "Switch a preset clothing item to texture editing (like VRoid's Edit button): its "
                                 "layers become available to vroid_list_layers / vroid_recolor_layer. Undoable.",
    "vroid_measure": "Measure the current model height in cm (same as VRoid's size label) and its bounds.",
    "vroid_set_body_size": "Set the height (cm) directly through the gender silhouette slider (FigureHeight/"
                           "FigureSlender, proportions preserved), and optionally weight (kg), converted to waist width "
                           "via BMI (VRoid has no weight). gender: female, male or neutral. Undoable.",
    "vroid_preset_cache_search": "Search the shared preset and custom-item cache (no VRoid needed): labels, "
                                 "descriptions, tags and colors (manual and auto-generated), plus the thumbnail path. "
                                 "Each result has label/labelSource/generated and preview: {kind, mannequin, clothing, "
                                 "underwear, hair, keptSlot, orientation, yaw, capturedAt, pixels, source}. Situation "
                                 "thumbnails are captured on a nude mannequin and framed front-on. All query words must "
                                 "match (e.g. 'short pleated blue skirt').",
    "vroid_preset_cache_annotate": "Add or correct the label, description, tags and colors of a preset in the shared "
                                   "cache, for other AIs. A manual label overrides the generated one. Short lowercase "
                                   "tags (type, color, length, style).",
    "vroid_preset_thumbnail": "Return the thumbnail of a preset or custom item (image) to judge it without applying it: "
                              "situation capture if available, otherwise VRoid's native icon (fetched on demand). "
                              "Thumbnail metadata (mannequin, clothing, underwear, framing) is in the "
                              "vroid_preset_cache_search result under preview.",
    "vroid_preset_cache_sync": "Scan what VRoid currently exposes: built-in presets AND custom items (with the name "
                               "given in VRoid). Reports new, changed (renamed custom item or new revision) and removed "
                               "items without erasing annotations; generates structural labels for new entries. Runs "
                               "automatically on each VRoid start. icons=true also fetches native preset icons (fast, "
                               "nothing is applied).",
    "vroid_preset_cache_build": "Create situation thumbnails for a category (presets, or Custom/<slot> for custom "
                                "items). Removes ALL clothes, accessories, underwear (including default underwear, "
                                "which shows through swimwear) and hair except BaseHair/the tested item; frames the "
                                "character front-on and centered on its bounds; applies each item, checks that nothing "
                                "else remains, captures, crops, then restores the original outfit. Writes thumbnailMeta "
                                "(nude mannequin, clothing=tested-item-only, underwear=removed, strippedSlots, camera "
                                "with fit, pixels, sha1) into catalog.json. Also generates a label and visual metadata "
                                "(colors, brightness, plain/patterned) from the thumbnail; manual labels are never "
                                "overwritten. Whole outfits pull the camera back so shoes stay visible; orientation "
                                "(profile yaw: back for back hair, three-quarter for shoes/arm accessories) is applied. "
                                "Save the model first: restoration is not guaranteed to be identical. About 3 s per "
                                "preset; native icons (sync icons=true) are faster.",
    "vroid_camera": "Aim the VRoid 3D view at the model from another angle before a capture. action: get (state + "
                    "preset rotations), angles (x,y in degrees), rotate (dx,dy), zoom (d), pan (x,y), reset (initial "
                    "view), mode (VRoid preset rotation), projection (toggle perspective/orthographic), custom "
                    "(px,py,pz,cx,cy,cz).",
    "vroid_apply_custom": "Apply one of the user's custom items, like clicking it in VRoid's Custom tab: replaces the "
                          "item in the same category. key = cache key (vroid_preset_cache_search kind=custom) or file = "
                          "path to the .vroidcustomitem file. Undoable.",
    "vroid_remove_item": "Remove an item from the model (clothing, accessory, shoes...). group = group id, or a short "
                         "type to remove all groups of that type (Tops, Bottoms, Onepiece, Socks, Shoes, InnerTop, "
                         "ArmAccessory, NeckAccessory...). Useful to start from a model without clothes before creating "
                         "thumbnails.",
    "vroid_face_preview": "Expression preview for a capture (open mouth to show teeth, smile, wink...): set the weight "
                          "(0..100) of face blendshapes whose name ends with name (e.g. MTH_A, MTH_O, ALL_Joy, "
                          "EYE_Close). Without name: list names (optional filter). Display only, nothing is saved; "
                          "empty name with weight 0 resets everything.",
    "vroid_begin_hair_edit": "Switch a hair material to texture editing (VRoid's Edit button): its texture becomes "
                             "available to the layer tools. Useful for a preset hairstyle whose texture is not editable.",
}

EN_ARG_DESCRIPTIONS = {
    "clé du paramètre (voir vroid_get_params) ou clé 'template:...' d'un curseur de vêtement (voir vroid_get_item_params)":
        "parameter key (see vroid_get_params), or the 'template:...' key of a clothing slider (see vroid_get_item_params)",
    "nouvelle valeur (0..1 ; 0..100 pour un curseur de vêtement)": "new value (0..1; 0..100 for a clothing slider)",
    "0..100 (défaut 100)": "0..100 (default 100)",
    "abandonner les modifications non sauvegardées": "discard unsaved changes",
    "ajouter comme nouveau calque au lieu de remplacer": "add as a new layer instead of replacing",
    "alpha 0..1 (défaut 1)": "alpha 0..1 (default 1)",
    "angle ou décalage X": "angle or X offset",
    "angle ou décalage Y": "angle or Y offset",
    "bleu 0..1": "blue 0..1",
    "catégorie (ex. Clothing/Tops) ; vide = toutes": "category (e.g. Clothing/Tops); empty = all",
    "catégorie (ex. VRoid/ClothingSet)": "category (e.g. VRoid/ClothingSet)",
    "catégorie à réinitialiser ; vide = toutes": "category to reset; empty = all",
    "chemin absolu du .vroid à écrire (facultatif)": "absolute path of the .vroid file to write (optional)",
    "chemin absolu du fichier .vroid": "absolute path of the .vroid file",
    "chemin de ressource ou id": "resource path or id",
    "chemin de ressource ou id du preset": "preset resource path or id",
    "chemin du PNG": "PNG path",
    "chemin du PNG à écrire (facultatif)": "PNG output path (optional)",
    "chemin du fichier .vroidcustomitem": "path of the .vroidcustomitem file",
    "clé de la couleur": "color key",
    "clé du cache (custom:...)": "cache key (custom:...)",
    "clé du paramètre": "parameter key",
    "clé du paramètre (voir vroid_get_params)": "parameter key (see vroid_get_params)",
    "clé du paramètre couleur": "color parameter key",
    "demi-largeur en fraction de hauteur": "half-width as a fraction of height",
    "décalage X": "X offset",
    "décalage Y": "Y offset",
    "décalage Z": "Z offset",
    "défaut 50": "default 50",
    "défaut female": "default female",
    "ex. Clothing/Shoes": "e.g. Clothing/Shoes",
    "ex. Clothing/Tops (facultatif)": "e.g. Clothing/Tops (optional)",
    "facteur de recul (défaut 3.3 ; 4.2 tenue complète)": "zoom-out factor (default 3.3; 4.2 for a whole outfit)",
    "facteur, ex. 1.3": "factor, e.g. 1.3",
    "filtre pour lister les noms": "filter for listing names",
    "fin du nom du blendshape": "blendshape name suffix",
    "fraction depuis le haut (0 = sommet)": "fraction from the top (0 = top)",
    "fraction depuis le haut (1 = pieds)": "fraction from the top (1 = feet)",
    "garder le matériau actuel (couleurs) si possible": "keep the current material (colors) if possible",
    "libellé manuel (remplace le label généré)": "manual label (overrides the generated label)",
    "id de l'image": "image id",
    "id de l'élément": "item id",
    "id de l'élément (vroid_list_hair_groups)": "item id (vroid_list_hair_groups)",
    "id de l'élément (vroid_list_layers)": "item id (vroid_list_layers)",
    "id du calque": "layer id",
    "id du calque à remplacer (inutile si as_new_layer)": "layer id to replace (ignored if as_new_layer)",
    "id du groupe": "group id",
    "id du groupe du vêtement": "clothing group id",
    "id du matériau (vroid_list_hair_materials)": "material id (vroid_list_hair_materials)",
    "id du preset (vroid_list_presets)": "preset id (vroid_list_presets)",
    "id ou type court": "id or short type",
    "inclure les presets payants non possédés": "include paid presets that are not owned",
    "inclure les éléments absents de VRoid": "include items absent from VRoid",
    "intensité 0..1 (défaut 1)": "strength 0..1 (default 1)",
    "mots à chercher (facultatif)": "words to search for (optional)",
    "nom de rotation prédéfinie": "preset rotation name",
    "nombre de mèches (facultatif)": "strand count (optional)",
    "nombre maximal d'icônes à récupérer": "maximum number of icons to fetch",
    "nombre maximal de presets à traiter": "maximum number of presets to process",
    "nombre maximal de résultats (défaut 200)": "maximum number of results (default 200)",
    "nouveaux / modifiés au dernier scan": "new / changed in the last scan",
    "nouvelle longueur (facultatif)": "new length (optional)",
    "nouvelle valeur": "new value",
    "orientation en degrés : 0 face, 90 profil, 180 dos": "orientation in degrees: 0 front, 90 profile, 180 back",
    "poids visé en kg (facultatif)": "target weight in kg (optional)",
    "presets intégrés ou objets personnalisés": "built-in presets or custom items",
    "qui annote (ex. nom du modèle d'IA)": "who annotates (e.g. AI model name)",
    "refaire aussi les vignettes existantes": "also rebuild existing thumbnails",
    "remplacer les tags/couleurs au lieu d'ajouter": "replace tags/colors instead of adding",
    "rotation relative X": "relative X rotation",
    "rotation relative Y": "relative Y rotation",
    "rouge 0..1": "red 0..1",
    "récupérer les icônes natives manquantes": "fetch missing native icons",
    "seulement les presets déjà décrits": "only presets that already have a description",
    "taille visée en cm": "target height in cm",
    "template à créer": "template to create",
    "texte court": "short text",
    "texte à chercher (facultatif)": "text to search for (optional)",
    "vert 0..1": "green 0..1",
    "zoom": "zoom",
    "MSAA samples 1..8 (default 4)": "MSAA samples 1..8 (default 4)",
    "supersampling factor 1..3 (default 2)": "supersampling factor 1..3 (default 2)",
    "output width in pixels (0 = camera viewport)": "output width in pixels (0 = camera viewport)",
    "output height in pixels (0 = camera viewport)": "output height in pixels (0 = camera viewport)",
    "true = 3D preview only (default), false = full window": "true = 3D preview only (default), false = full window",
}


def _localize_schema(schema):
    for prop in (schema.get("properties") or {}).values():
        if isinstance(prop, dict) and prop.get("description") in EN_ARG_DESCRIPTIONS:
            prop["description"] = EN_ARG_DESCRIPTIONS[prop["description"]]


def localize_tools(tools):
    """Translate tool descriptions and argument descriptions in place."""
    missing = []
    for tool in tools:
        name = tool["name"]
        if name in EN_TOOL_DESCRIPTIONS:
            tool["description"] = EN_TOOL_DESCRIPTIONS[name]
        else:
            missing.append(name)
        _localize_schema(tool.get("inputSchema") or {})
    return missing
