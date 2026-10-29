# MCP bridge for VRoid Studio

**English** | [Français](README-fr.md) | [日本語](README-ja.md) | [简体中文](README-zh.md)

Lets an AI (Claude Code, Claude Desktop…) read and edit the model open in VRoid Studio.

```
AI ──MCP (stdio)──> mcp_server/vroid_mcp.py ──HTTP 127.0.0.1:7811──> BepInEx plugin (inside VRoid) ──> VRoidCore.Editing.Context
```

## Installation (release)

1. Download `VRoidMcp-v<version>.zip` from the GitHub releases and unzip it.
2. Close VRoid Studio, then double-click `Installer.cmd`.

The installer:
- finds VRoid Studio in your Steam libraries (otherwise: `Installer.cmd -GameDir "<VRoid Studio folder>"`);
- installs BepInEx 6.0.0-be.791 (IL2CPP) if it is missing, after moving any other version (BepInEx 5…) to
  `BepInEx_sauvegarde_<date>`; an existing BepInEx 6 is kept (`-ForceBepInEx` to replace it).
  The archive is downloaded from builds.bepinex.dev and its SHA-256 checksum is verified;
- copies the plugin to `BepInEx\plugins\VRoidMcpBridge`;
- copies the MCP server, tools, documentation and default framing config to `%LOCALAPPDATA%\VRoidMcp` (the local
  preset cache and its framing overrides are never overwritten);
- registers the `vroid` server in Claude Code (`~/.claude.json`) and Claude Desktop, after backing up their
  configuration (`-NoClaude` to skip this).

Requirements: Windows 10/11. Python 3.12 is **bundled** in the release — nothing to install (numpy and Pillow are installed automatically when the network allows it).
Update: run the installer of a newer release. Uninstall: `Installer.cmd -Uninstall`.
First launch after installing BepInEx: one to two extra minutes (interop assemblies are generated).

## Components

| Item | Location |
|---|---|
| BepInEx 6 BE #791 (IL2CPP) | `<VRoid Studio folder>\BepInEx` |
| Plugin (source) | `VRoidMcpBridge/` → built into `BepInEx\plugins\VRoidMcpBridge` |
| MCP server | `mcp_server/vroid_mcp.py` (Python 3, no dependencies) |
| Framing defaults | `config/framing.json` (per category/body part; local overrides in the preset cache) |
| Installer | `installer/` (`build_release.py` builds the release package) |

## Building the plugin

```
cd VRoidMcpBridge
dotnet build -c Release -p:GameDir="<VRoid Studio folder>"
```
(VRoid must be closed, otherwise the DLL is locked. BepInEx 6 must have run once so that the
`BepInEx\interop` assemblies exist.)

## Registering the MCP server manually

The installer does this. Otherwise, in Claude Code:

```
claude mcp add vroid -- python <path>\mcp_server\vroid_mcp.py
```

Or in Claude Desktop (`claude_desktop_config.json`):

```json
{ "mcpServers": { "vroid": { "command": "python", "args": ["<path>\\mcp_server\\vroid_mcp.py"] } } }
```

## Full reference

`docs/REFERENCE.md` lists every MCP tool, the preset categories (with the part of the model each one replaces:
full hairstyle, bangs, back hair, sideburns, tied hair, lips, ears…), and every parameter of every group (body,
face…). Regenerate it with VRoid open:

```
python tools/gen_reference.py
```

The reference and `docs/TEXTURES.md` are written in French. Documentation is also available in Japanese and Simplified Chinese (see the language links at the top).

## Editing textures

`docs/TEXTURES.md`: where the textures are (clothing, hair, scalp, skin, eyes), the three ways to change them
(recolor, export/re-import, add a layer), how to locate a position on a texture, and pitfalls.
Helpers: `tools/texture_utils.py`, `tools/skin_detail.py`.

## Shared preset cache

`preset_cache/` (local, not versioned: `%LOCALAPPDATA%\VRoidMcp\preset_cache` after installation) is a normalized
catalog that several AIs (or sessions) can read and enrich, so they don't have to try presets in VRoid again:

- `catalog.json`: one entry per preset or custom item, keyed by resource path (stable across versions), with the
  VRoid id, category, replaced slot, price/ownership, thumbnail, description, tags, colors and annotation history
  (author, date). Generated thumbnails also carry `thumbnailMeta`: neutral mannequin, stripped slots, removed
  underwear/hair, camera framing (`fit: full-body` for complete outfits), pixels and SHA-1. Schema in
  `mcp_server/preset_cache.py`.
- A readable `label` is generated automatically: category + number at sync time, then dominant colors and a
  `plain`/`patterned` hint from the thumbnail at build time. `labelSource` distinguishes `generated` from `manual`;
  manual labels always win. Raw visual data is in `generated.visual` (colors, brightness, edge density).
- `thumbs/<Category>/<number>.jpg`: thumbnails cropped to the relevant area (top, bottom, legs, head…).
- Thumbnails are generated on a nude neutral mannequin: all clothing, accessories **and underwear** are removed
  (default underwear shows through swimwear), hair is removed except Base Hair / the tested hair, and the camera is
  reset to face the model, centered on its bounds. Complete outfits use a wider framing so shoes stay visible.
- Atomic writes with a lock: several AIs can annotate at the same time.

Tools: `vroid_preset_cache_search` (works without VRoid; each result carries `preview` with kind/mannequin/clothing/
underwear/hair/fit), `vroid_preset_thumbnail`, `vroid_preset_cache_annotate`, `vroid_preset_cache_sync` (new presets
and custom items, annotations kept), `vroid_preset_cache_build` (automatic thumbnails for a category, then the
original outfit is restored).

The cache fills up with use: `vroid_preset_cache_sync` lists the presets, `vroid_preset_cache_build` creates the
thumbnails. Old thumbnails generated before this metadata exists show `preview.mannequin = "unknown"` until rebuilt
with `refresh=true`.

## Camera framing profiles

Framing is configured **per category / body part**, never per individual garment: `config/framing.json` (committed)
holds the defaults for `Clothing/Tops`, `Clothing/Shoes`, `Hair`, `Face`, `VRoid/ClothingSet`, etc. Each profile has
`top`/`bottom` (fractions from the top of the model), `half` (half-width, `null` = full width), `distance` (zoom-out
factor), `yaw` (orientation: 0 = front, 90 = profile, 180 = back) and `fit` (`region` or `full-body`; complete outfits
are pulled back to keep shoes visible).

The AI can override a profile with `vroid_framing_set`; overrides are written to the local, non-versioned
`preset_cache/framing_overrides.json`. `vroid_framing_reset` clears them and returns to the committed defaults.
Per-item facts (thumbnail, description, tags, colors, mannequin/capture metadata) stay in `catalog.json`.

## Exposed tools

52 `vroid_*` tools (help, batch, lifecycle, **VRM export**, framing, parameters, colors, layers, hair, presets,
body size, camera, screenshots…): full list and descriptions in `docs/REFERENCE.md`. The lifecycle tools are
`vroid_create`, `vroid_open`, `vroid_save`, `vroid_main_menu` and `vroid_exit`; framing is configured by
`vroid_framing_get/set/reset`; `vroid_status` also reports the current file and the dirty flag.

### Help and languages

The MCP server exposes `vroid_help` (alias `/help` in client documentation), available without VRoid:

```text
vroid_help topic=overview lang=en       # default
vroid_help topic=tools lang=fr
vroid_help topic=lifecycle lang=ja
vroid_help topic=thumbnails lang=zh-CN
```

Tool names and arguments are English. The manual is available in English, French, Japanese and Simplified
Chinese; the tool index is generated from the live registry. `initialize.instructions` points new AI clients
to `vroid_help` and to the save/lifecycle rules.

### Batch

`vroid_batch` runs up to 200 operations sequentially in one MCP call, with `stop_on_error=true` by default,
no nested batches and no automatic rollback. It returns a text summary plus up to 8 images / 16 MiB in the
same response; extra images are reported by path only. Use it for preset sweeps, parameter sequences and
screenshot series. Save before destructive sequences.

Edits go through VRoid's command system: they appear in the history and can be undone with Ctrl+Z.

### VRM export

`vroid_export_vrm` drives VRoid's own exporter without clicks or a file dialog. It supports VRM 1.0/0.x,
VRoid's **Delete Transparent Meshes** (default), polygon-reduction sliders, material reduction (Default/2/8/12),
hair combination, texture shrinking/atlas size and hair-bone reduction:

```text
vroid_export_vrm path=D:\out\model.vrm version=1 delete_transparent=true \
  hair=50 hair_bones=50 material_mode=1 combine_hair=true
```

The open `.vroid` is not modified. The export takes 10-40 s, returns `warnings` for any option VRoid refused,
and leaves the export screen by default (`leave=false` keeps it open). Only one export runs at a time; wait for
the response before any other VRoid operation. `vroid_export_vrm_options` opens the same screen and returns its
current settings and available choices. See `vroid_help topic=export`.

## Key classes found in the dump

- `VRoidCore.Editing.Context`: the model being edited (parameter reads, `ExecuteSyncCommand`, `UndoAsync`…).
- `VRoid.Studio.Component.VRoidCoreModelUpdater` (MonoBehaviour): holds the active `Context` (`_context`).
- `VRoidCore.Editing.History.Command.*`: ~110 commands (hair, textures, materials, colors, bones, blendshapes…).

## Automated tests

The offline suite covers the MCP protocol, the four help languages, the live tool index, batch
semantics, generated labels, and framing defaults/overrides. It needs no VRoid instance:

```text
python -m unittest discover -s tests -v
```

CI runs the same suite on push/PR (`.github/workflows/tests.yml`). VRoid-specific smoke tests
(create/open/save, screenshot, preset build) remain manual because they need the editor and BepInEx.

## Minimized / background mode

Background execution is **always on**: the plugin keeps `Application.runInBackground` enabled.
There is no foreground toggle anymore; the tested mode is the one that works with VRoid minimized.

Tested on a minimized VRoid window: `/status`, `vroid_enter`/`vroid_set_param` and a clean
MSAA/SSAA `vroid_screenshot` worked. This avoids the trap where disabling background mode paused
VRoid and made MCP calls time out.

## 3D preview

`vroid_screenshot` now renders the avatar's 3D camera into its own RenderTexture (no UI panels),
with **MSAA 4x** and **SSAA 2x** by default. Use `width`/`height` to choose the output size,
`msaa`/`ssaa` to trade quality for speed, and `clean=false` for the legacy full-window capture.
The capture is used for visual QA; preset thumbnails keep the full-window path because they are
cropped with `crop_center`.

## Test status (VRoid on Unity 6000.0.62)

| Feature | Result |
|---|---|
| Reading groups and parameters | OK (36 groups on an N00 model) |
| Setting bones, shapes (blendshapes), colors | OK, values read back identical |
| Undo / redo | OK, in order; successive changes to the same slider merge into one step, like a slider drag |
| 3D preview (MSAA 4x / SSAA 2x) | OK, no UI panels, correct orientation |
| Hair color (0.3.0) | OK: hair materials listed (colors + textures); brown hair → pink by remapping the texture by luminance (gradient and highlights kept) |
| Presets (0.5.0) | OK: 1750 presets listed (50 categories), applied like a thumbnail click; contact sheets to choose (102 tops, 69 bottoms) |
| Height / weight (0.7.0) | OK: `vroid_set_body_size` 160 cm → 159.9; 152 cm/39 kg → 152.0 (slider 0.338, same as the manual setting 0.337) |
| VRM export | OK: `vroid_export_vrm` on `Konoha.vroid` → VRM 1.0, 16.6 MB, 10.1 s, no warning, VRoid still running after the export; VRM 0.x, reductions, material/atlas and texture modes tested via the same native exporter |
| Preset clothing (0.6.0) | `begin_clothing_edit` makes the texture editable, then recolor by layers; `clothing_colors` lists the colors (keys are not plain names yet) |
| Hair shape (0.4.0) | Reading groups OK. Lengthening a brush strand works technically, but scaling from the root makes the strand stick out (to be replaced by a downward extension). Duplicate + offset a group OK: 41 side/back groups duplicated 6 cm lower = longer hair (one undo step per point) |
| Texture layers: list, export/import PNG (0.2.0) | OK; export → import → export round trip is bit-identical |
| Recoloring clothing (0.2.0) | OK: white skirt → navy in multiply mode, folds and transparency kept |

`tools/skin_detail.py` generates a skin detail layer (grain, pores, tone, redness on cheeks, nose, elbows, knees,
fingers) to import as a new layer on the body and face skin (`vroid_import_layer` with `as_new_layer`).
UV positions were measured on the N00 body by temporarily importing a layer that encodes U/V as hue, then reading
the screenshot.

On a model built from presets, many colors are simple "overlay colors": `Level1BaseHair_OverlayColor` (scalp),
`Level3Iris_Left/RightOverlayColor` (eyes), `Level1Eyebrow_OverlayColor` (eyebrows), set with `vroid_set_color`;
the tint of a preset hairstyle is a `base:<id>` key from `vroid_list_hair_materials`.

Hair uses shared "hair materials" (`GetAllMaterialsQuery`, `GetHairMaterialQuery`, `SetMaterialColorCommand`);
their textures have `Base` as transferable and can be recolored with the layer tools.
The scalp is painted separately: the front at the top of the FaceSkin texture, the back (dome at the bottom) and
the nape (top) on the BodySkin texture. Recolor them too when changing the hair color.

Clothing has no color sliders: its color comes from its texture layers
(`vroid_list_layers` then `vroid_recolor_layer`, or export → retouch → import).

Good to know:
- Many sliders are stored as two halves (`…Mag`/`…Shrink`, `…Wide`/`…Narrow`). Setting one half resets the other,
  VRoid compensating for the difference.
- Colors use components from 0 to 1.
- `vroid_face_preview` opens the mouth (Fcl_MTH_A…) on the face mesh only: teeth (fangs
  `Level2Mouth_ToothFung1/2/3Upper/Lower`) do not show in this preview; use VRoid's expression editor to see them.
- `FigureHeight<Gender>` and `FigureSlender<Gender>` are the two halves of one silhouette slider: Height makes the
  model shorter while keeping proportions, Slender makes it taller and slimmer. Use it for height (not
  `WholeBodyScale`, which shrinks everything uniformly).
- The height shown by VRoid ≈ top of the model (m) × 100, which `/measure` (boundsMaxY) reproduces.
  `vroid_set_body_size` targets a height in cm (and converts weight into waist width via BMI). The label ignores
  thin upright strands (ahoge) while `/measure` counts them: with an ahoge, aim a few cm higher and check the label
  (Body tab). E.g. target 132.3 → label 130.0.

## License

MIT — see [`LICENSE`](LICENSE). Code adapted from `vroid-studio-mcp` is covered by its MIT
notice in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). VRoid Studio, BepInEx and their
assets are not distributed with this project.

## IL2CPP pitfalls

- VRoid pauses its loop when its window is not focused: the plugin forces `Application.runInBackground = true`.
- Building IL2CPP `KeyValuePair<,>` on the managed side crashes the runtime: use a native IL2CPP `Dictionary`.
- `ScreenCapture.CaptureScreenshot(string)` crashes in the interop: use `CaptureScreenshotAsTexture` + `EncodeToPNG`.

## Limitations

- VRoid Studio updates may rename these classes: the dump then has to be redone and the code adjusted.
- BepInEx 6 is "bleeding edge": stable here, but with no guarantee.
- Old BepInEx 5 plugins (e.g. VRoidXYTool) do not work with BepInEx 6 IL2CPP.
