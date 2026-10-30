---
name: vroid-studio
description: Work in VRoid Studio through the `vroid` MCP server - create, open, edit and save VRoid characters (face, hair, body, outfits, accessories, colors, textures, presets), take screenshots and export VRM. Use whenever the user mentions VRoid, a .vroid file, a VRM avatar or a VRoid character, or asks to design, dress, recolor, capture or export one.
whenToUse: The user wants something done in VRoid Studio, on a .vroid model or a VRM export, and the vroid_* (mcp__vroid__*) tools are available.
---

# Working in VRoid Studio

The `vroid` MCP server drives a running VRoid Studio through a plugin. Every edit is a real VRoid
edit: it appears in VRoid's history and can be undone. Tools are named `vroid_*` (in DeepSeek
Harness: `mcp__vroid__vroid_*`). Reply to the user in their language; tool names and arguments
stay English.

## Before anything

1. `vroid_status`. It tells you whether VRoid answers, whether a model is open (`modelOpen`,
   `ready`), the current file and unsaved changes (`dirty`).
   - Unreachable: ask the user to start VRoid Studio. The first launch after an install takes
     1-2 extra minutes. Never try to start or kill VRoid yourself.
   - No model open: `vroid_open path=...` or `vroid_create gender=female|male`.
2. For a task you have not done before in this session, read only the section you need:
   - MCP resources `vroid://agent/start`, `face`, `hairstyle`, `body`, `outfit`, `accessories`,
     `look`, `physical`, `presets`, `tools`, `workflows`, `troubleshooting`
     (`vroid://agent/reference` is the whole 85 KB reference: avoid it);
   - or `vroid_help topic=<overview|lifecycle|export|colors|outfit|framing|thumbnails|batch|errors>`
     (works even when VRoid is closed; `lang=fr|ja|zh-CN` available).

## Rules that prevent damage

- **One model at a time.** `vroid_create`, `vroid_open` and `vroid_main_menu` leave the current
  model: save first (`vroid_save`, or `vroid_save path=...` for a model that has no file yet).
  Use `discard=true` only when the user explicitly accepts losing changes.
- **Do not overwrite the user's file without asking.** For experiments, save under a new name.
- **Group ids are per model.** Read them with `vroid_list_groups` / `vroid_enter`; read them again
  after opening another model or applying an outfit.
- **Presets can replace several slots** (a one-piece replaces top and bottom; `*Set` presets replace
  a whole look). After applying one, check with `vroid_list_groups`.
- **Values are normalized.** Sliders are generally 0..1; colors are RGBA 0..1 (`vroid_set_param` also
  takes `#RRGGBB`). Paired sliders (`...Long`/`...Short`, `...Up`/`...Down`, ...) are two halves of
  one control: setting one resets the other.
- **One VRoid operation at a time.** Wait for each answer, especially exports and batches.
- **Undo is cheap.** `vroid_undo` / `vroid_redo` after a bad change, rather than compensating.

## Working loop

Inspect, change one thing, look, continue:

1. Find the control: `vroid_sections`, `vroid_categories section=...`, `vroid_enter section=... category=...`,
   `vroid_get_params group=...`. Clothing groups only expose their colors: `vroid_get_item_params` lists every
   parameter VRoid actually exposes, including groups `vroid_list_groups` hides (preset-template sliders such as
   skirt length or sleeve length are not exposed; do not promise them).
2. Change it: `vroid_set_param` (sliders and colors by section/category/param), or the lower-level
   `vroid_set_bone`, `vroid_set_blendshape`, `vroid_set_color`.
3. Look: `vroid_screenshot` (clean 3D view). Frame first with `vroid_camera` for face or detail work.
4. Show the user the image when the change is visual, and ask before large redesigns.

## Common tasks

- **Find and apply a preset** (hair, clothes, shoes, accessories...): `vroid_preset_cache_search`
  (works offline, with thumbnails and the user's notes), then `vroid_apply_preset id=...` or, for a
  custom item, `vroid_apply_custom file=...`; remove with `vroid_remove_item`.
- **Recolor**: hair with `vroid_list_hair_materials` + `vroid_set_hair_color`; clothes with
  `vroid_clothing_colors` + `vroid_set_color`. For a texture-level edit, enter edit mode first
  (`vroid_begin_clothing_edit` / `vroid_begin_hair_edit`), then `vroid_list_layers`,
  `vroid_recolor_layer`, or `vroid_export_layer` / `vroid_import_layer` to repaint a PNG.
- **Hair shape**: `vroid_list_hair_groups`, `vroid_set_procedural_hair`, `vroid_scale_brush_hair`,
  `vroid_clone_brush_hair`.
- **Expressions**: `vroid_face_preview filter=Fcl_` lists them; `vroid_face_preview name=... weight=80`
  previews one; reset with `name='' weight=0` before exporting or capturing a neutral face.
- **Many steps or variants**: `vroid_batch` (up to 200 sequential operations, no rollback, at most
  8 images returned). Save before a destructive batch.
- **Export VRM**: `vroid_export_vrm path=...` (VRM 1.0 by default, `version=0` for VRM 0.x).
  Options left out use VRoid's defaults: transparent meshes deleted, no reduction. Reduction sliders
  `hair|face|body|outfit` 0..100, `material_mode` 0 Default / 1 = 2 / 2 = 8 / 3 = 12 materials,
  `hair_bones` 0..100. Smaller textures: `texture_mode=1` without material reduction,
  `atlas_resolution=1` (2048) with it. Takes 20-40 s; read `warnings` (options VRoid refused) and
  report the file size. The `.vroid` itself is not modified.

## When something fails

- Error text says VRoid is unreachable: VRoid closed or still loading; ask the user, then `vroid_status`.
- `unsaved changes` / `dirty`: save, or ask whether to discard.
- Group or key not found: ids changed or the model type lacks that control; re-read with
  `vroid_list_groups` / `vroid_get_params`.
- Anything else: `vroid_help topic=errors` and the `vroid://agent/troubleshooting` resource.
  Report the exact error to the user rather than retrying blindly.
