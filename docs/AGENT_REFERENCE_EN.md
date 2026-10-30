# VRoid MCP Bridge — Agent Reference (English)

Version 0.14.0 · generated from the live MCP tool registry and a model-open N00 session.

Audience: an AI agent using the **`vroid`** MCP server through DeepSeek Harness (or any MCP client). It assumes no access to the VRoid Studio or VRoid MCP source code. The server, plugin, Python runtime and client integration are already installed.

## What is available

- **53 MCP tools** named `vroid_*`; names, arguments and JSON schemas are available from the client's `tools/list`.
- **One open model at a time**. Edits are real VRoid edits, undoable with Ctrl+Z / `vroid_undo`.
- **`vroid_help`** works without VRoid and supports `en`, `fr`, `ja`, `zh-CN`; topics: `overview`, `tools`, `lifecycle`, `export`, `framing`, `thumbnails`, `colors`, `outfit`, `sessions`, `errors`, `languages`, `batch`.
- **Preset cache tools** can search without VRoid; `vroid_preset_cache_*` does not require an open model.
- The HTTP bridge listens on `127.0.0.1:7811`; the MCP server runs over stdio.

The same reference is exposed as MCP **resources**, so an agent can load one section without injecting the whole file: `vroid://agent/reference` (full), `vroid://agent/start`, `face`, `hairstyle`, `body`, `outfit`, `accessories`, `look`, `physical`, `presets`, `tools`, `workflows`, `troubleshooting`. `initialize.instructions` carries the short contract and the resource list; `tools/list` remains the authoritative JSON-schema source. MCP prompts `start`, `character`, `export_vrm` and `help` open ready-made workflows, and the installer adds a `vroid-studio` skill (one-page working guide) for Claude Code (`~/.claude/skills`) and DeepSeek Harness (`~/.dsh/skills`).

## Start and lifecycle

Always start with:

```text
vroid_help(topic='overview')
vroid_status()
```

`vroid_status` returns: `plugin`, `unity`, `modelOpen`, `modelType`, `isEditing`, `canUndo`, `canRedo`, `ready`, `currentFile`, `dirty`, `canSave`.

Rules:

1. `vroid_create` / `vroid_open` are only valid at the model-select screen (no model open).
2. A new model has no file: use `vroid_save(path=...)` before leaving it.
3. `vroid_main_menu` refuses unsaved changes unless `discard=true`; `vroid_exit` does the same.
4. Save before a destructive batch or an export sequence.
5. Only one model is open; finish with the current one before opening another.

## UI map and access modes

This is the current section/category map. It is read with `vroid_sections` / `vroid_categories`; `category` is the stable name used by `vroid_enter`, `vroid_set_param` and preset filters. A group id is model-specific: get it at runtime with `vroid_list_groups` or `vroid_enter`.

| Section | Category | Groups | Access mode |
|---|---|---:|---|
| Face | `Cheek` | 1 | color/overlay |
| Face | `Ear` | 1 | sliders (bone/blendshape) |
| Face | `EyeHighlight` | 1 | color parameters only |
| Face | `EyeSurrounding` | 1 | sliders (bone/blendshape) |
| Face | `EyeWhite` | 1 | color parameters only |
| Face | `Eyebrow` | 1 | sliders + colors |
| Face | `Eyelash` | 1 | color parameters only |
| Face | `Eyelid` | 1 | color parameters only |
| Face | `Eyeline` | 1 | color parameters only |
| Face | `FaceShape` | 1 | sliders (bone/blendshape) |
| Face | `FaceSkin` | 1 | color parameters only |
| Face | `Iris` | 1 | sliders + colors |
| Face | `Mouth` | 1 | sliders + colors |
| Face | `Nose` | 1 | sliders (bone/blendshape) |
| Hairstyle | `AllHair` | 1 | hair preset/procedural + material colors/textures |
| Hairstyle | `BaseHair` | 1 | hair preset/procedural + material colors/textures |
| Body | `Arm` | 1 | sliders (bone/blendshape) |
| Body | `BodySkin` | 1 | color parameters only |
| Body | `Chest` | 1 | sliders (bone/blendshape) |
| Body | `Hand` | 1 | sliders (bone/blendshape) |
| Body | `Head` | 1 | sliders (bone/blendshape) |
| Body | `Leg` | 1 | sliders (bone/blendshape) |
| Body | `Neck` | 1 | sliders (bone/blendshape) |
| Body | `Shoulder` | 1 | sliders (bone/blendshape) |
| Body | `Torso` | 1 | sliders (bone/blendshape) |
| Body | `Waist` | 1 | sliders (bone/blendshape) |
| Body | `WholeBody` | 1 | sliders (bone/blendshape) |
| Outfit | `Bottoms` | 1 | preset + color/texture layers (complex) |
| Outfit | `InnerBottom` | 1 | preset + color/texture layers (complex) |
| Outfit | `InnerTop` | 1 | preset + color/texture layers (complex) |
| Outfit | `Shoes` | 1 | preset + color/texture layers (complex) |
| Outfit | `Socks` | 1 | preset + color/texture layers (complex) |
| Outfit | `Tops` | 1 | preset + color/texture layers (complex) |
| Look | `FixedPreset` | 1 | preset choice |
| Look | `MouthLine` | 1 | color/overlay |
| Look | `NoseLighting` | 1 | color/overlay |

**Accessories** is absent from `vroid_sections` when the model has no accessory group. It is preset-driven: `Attachment/*` (Hat, AnimalEar, Tail, Glasses) and `Clothing/AccessoryArm` / `Clothing/AccessoryNeck`. Apply them with `vroid_apply_preset` or `vroid_apply_custom`, remove them with `vroid_remove_item`, then inspect `vroid_list_groups` if a layer edit is needed.

`vroid_enter` is data-level: it does not switch VRoid's visible tab. Use it to read the group and its parameters, then write with `vroid_set_param`. The visible VRoid tab is only a UI; the section/category names below are the API names.

## Face parameters

Direct groups. Most entries are normalized 0..1 bone or blendshape sliders; colors are RGBA 0..1. Some entries are overlays/textures rather than sliders.

Each category below is addressed with `vroid_enter(section, category)`. The returned `params` are the keys accepted by `vroid_set_param` (or by `vroid_set_bone` / `vroid_set_blendshape` / `vroid_set_color`).

### Face / Cheek — Cheek

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1Cheek_OverlayColor` | color | Cheek Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Ear — Ears

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Ear_EarScaleMag` | bone | Ear Ear Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarScaleShrink` | bone | Ear Ear Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarTipUp` | bone | Ear Ear Tip Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarTipWide` | bone | Ear Ear Tip Wide | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarTipDown` | bone | Ear Ear Tip Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarStandUp` | bone | Ear Ear Stand Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarLieDown` | bone | Ear Ear Lie Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarRound` | bone | Ear Ear Round | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Ear_EarOff` | blendshape | Ear Ear Off | 0..1 normalized (VRoid may clamp); shape slider |

### Face / EyeHighlight — Eye Highlight

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level3EyeHighlight_MaterialColor` | color | Eye Highlight Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeHighlight_MaterialShadeColor` | color | Eye Highlight Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeHighlight_MaterialEmissionColor` | color | Eye Highlight Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeHighlight_MaterialOutlineColor` | color | Eye Highlight Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeHighlight_OverlayColor` | color | Eye Highlight Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / EyeSurrounding — Eye Surrounding

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Eye_EyePosUp` | bone | Eye Eye Pos Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyePosDown` | bone | Eye Eye Pos Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyePosIn` | bone | Eye Eye Pos In | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyePosOut` | bone | Eye Eye Pos Out | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyeSizeX` | bone | Eye Eye Size X | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyeSizeXShrink` | bone | Eye Eye Size XShrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyeSizeY` | bone | Eye Eye Size Y | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyeSizeYShrink` | bone | Eye Eye Size YShrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyeRotateInner` | bone | Eye Eye Rotate Inner | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Eye_EyeRotateOuter` | bone | Eye Eye Rotate Outer | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeOutsideDown` | bone | Eye Surrounding Eye Outside Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeOutsideUp` | bone | Eye Surrounding Eye Outside Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeCenterDown` | bone | Eye Surrounding Eye Center Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeCenterUp` | bone | Eye Surrounding Eye Center Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeInsideDown` | bone | Eye Surrounding Eye Inside Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeInsideUp` | bone | Eye Surrounding Eye Inside Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeShapeFemale` | bone | Eye Surrounding Eye Shape Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeShapeMale` | bone | Eye Surrounding Eye Shape Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyelidStraightUpper` | bone | Eye Surrounding Eyelid Straight Upper | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyelidStraightLower` | bone | Eye Surrounding Eyelid Straight Lower | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeJitome` | bone | Eye Surrounding Eye Jitome | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeInsideSuppressCurve` | bone | Eye Surrounding Eye Inside Suppress Curve | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyeDrooping` | bone | Eye Surrounding Eye Drooping | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2EyeSurrounding_EyelashLow` | blendshape | Eye Surrounding Eyelash Low | 0..1 normalized (VRoid may clamp); shape slider |

### Face / EyeWhite — Eye White

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level3EyeWhite_MaterialColor` | color | Eye White Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeWhite_MaterialShadeColor` | color | Eye White Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeWhite_MaterialEmissionColor` | color | Eye White Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeWhite_MaterialOutlineColor` | color | Eye White Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3EyeWhite_OverlayColor` | color | Eye White Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Eyebrow — Eyebrows

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1Eyebrow_EyebrowUp` | bone | Eyebrow Eyebrow Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowDown` | bone | Eyebrow Eyebrow Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowGather` | bone | Eyebrow Eyebrow Gather | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowSeparate` | bone | Eyebrow Eyebrow Separate | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowRise` | bone | Eyebrow Eyebrow Rise | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowDrooping` | bone | Eyebrow Eyebrow Drooping | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowShapeFemale` | bone | Eyebrow Eyebrow Shape Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowShapeMale` | bone | Eyebrow Eyebrow Shape Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowForward` | bone | Eyebrow Eyebrow Forward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowBackward` | bone | Eyebrow Eyebrow Backward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowRotateInner` | bone | Eyebrow Eyebrow Rotate Inner | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowRotateOuter` | bone | Eyebrow Eyebrow Rotate Outer | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowSizeYShrink` | bone | Eyebrow Eyebrow Size YShrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowSizeY` | bone | Eyebrow Eyebrow Size Y | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowSizeXShrink` | bone | Eyebrow Eyebrow Size XShrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_EyebrowSizeX` | bone | Eyebrow Eyebrow Size X | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Eyebrow_MaterialColor` | color | Eyebrow Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Eyebrow_MaterialShadeColor` | color | Eyebrow Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Eyebrow_MaterialEmissionColor` | color | Eyebrow Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Eyebrow_MaterialOutlineColor` | color | Eyebrow Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Eyebrow_OverlayColor` | color | Eyebrow Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Eyelash — Eyelashes

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Eyelash_MaterialColor` | color | Eyelash Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyelash_MaterialShadeColor` | color | Eyelash Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyelash_MaterialEmissionColor` | color | Eyelash Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyelash_MaterialOutlineColor` | color | Eyelash Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyelash_OverlayColor` | color | Eyelash Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Eyelid — Eyelid

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Eyelid_ShadowColor` | color | Eyelid Shadow Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyelid_MainColor` | color | Eyelid Main Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyelid_HighlightColor` | color | Eyelid Highlight Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Eyeline — Eyeline

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Eyeline_MaterialColor` | color | Eyeline Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyeline_MaterialShadeColor` | color | Eyeline Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyeline_MaterialEmissionColor` | color | Eyeline Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyeline_MaterialOutlineColor` | color | Eyeline Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Eyeline_OverlayColor` | color | Eyeline Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / FaceShape — Face Shape

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2FaceContour_FacelineDown` | bone | Face Contour Faceline Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_FacelineUp` | bone | Face Contour Faceline Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_MandibleSize` | bone | Face Contour Mandible Size | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_FacelineForward` | bone | Face Contour Faceline Forward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_FacelineBackward` | bone | Face Contour Faceline Backward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinSlim` | bone | Face Contour Chin Slim | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinUp` | bone | Face Contour Chin Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinRoundness` | bone | Face Contour Chin Roundness | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinSharp` | bone | Face Contour Chin Sharp | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_SinciputDown` | bone | Face Contour Sinciput Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_SinciputUp` | bone | Face Contour Sinciput Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_FaceMale` | bone | Face Contour Face Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_FaceFemale` | bone | Face Contour Face Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinOutlineFemale` | bone | Face Contour Chin Outline Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinOutlineMale` | bone | Face Contour Chin Outline Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinFullCheeked` | bone | Face Contour Chin Full Cheeked | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinJawBackward` | bone | Face Contour Chin Jaw Backward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinJawForward` | bone | Face Contour Chin Jaw Forward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinRound` | bone | Face Contour Chin Round | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_HeadShapeFemale` | bone | Face Contour Head Shape Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_HeadShapeMale` | bone | Face Contour Head Shape Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_ChinDown` | bone | Face Contour Chin Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2FaceContour_FaceRound` | blendshape | Face Contour Face Round | 0..1 normalized (VRoid may clamp); shape slider |

### Face / FaceSkin — Face skin

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1FaceSkin_MaterialColor` | color | Face Skin Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1FaceSkin_MaterialShadeColor` | color | Face Skin Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1FaceSkin_MaterialEmissionColor` | color | Face Skin Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1FaceSkin_MaterialOutlineColor` | color | Face Skin Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1FaceSkin_ShadowColor` | color | Face Skin Shadow Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1FaceSkin_MainColor` | color | Face Skin Main Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1FaceSkin_HighlightColor` | color | Face Skin Highlight Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Iris — Irises

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level3Iris_EyeIrisScaleXMag` | bone | Iris Eye Iris Scale XMag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_EyeIrisScaleXShrink` | bone | Iris Eye Iris Scale XShrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_EyeIrisScaleYMag` | bone | Iris Eye Iris Scale YMag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_EyeIrisScaleYShrink` | bone | Iris Eye Iris Scale YShrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_GazeUpward` | bone | Iris Gaze Upward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_GazeDownward` | bone | Iris Gaze Downward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_GazeInside` | bone | Iris Gaze Inside | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_GazeOutside` | bone | Iris Gaze Outside | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level3Iris_MaterialColor` | color | Iris Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3Iris_MaterialShadeColor` | color | Iris Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3Iris_MaterialEmissionColor` | color | Iris Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3Iris_MaterialOutlineColor` | color | Iris Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3Iris_LeftOverlayColor` | color | Iris Left Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level3Iris_RightOverlayColor` | color | Iris Right Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Face / Mouth — Mouth

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Mouth_MouthDown` | bone | Mouth Mouth Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthUp` | bone | Mouth Mouth Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthNarrow` | bone | Mouth Mouth Narrow | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthWide` | bone | Mouth Mouth Wide | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthCornerUp` | bone | Mouth Mouth Corner Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthCornerDown` | bone | Mouth Mouth Corner Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthShapeFemale` | bone | Mouth Mouth Shape Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthShapeMale` | bone | Mouth Mouth Shape Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthBackward` | bone | Mouth Mouth Backward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Mouth_MouthForward` | bone | Mouth Mouth Forward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level1Mouth_MaterialColor` | color | Mouth Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Mouth_MaterialShadeColor` | color | Mouth Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Mouth_MaterialEmissionColor` | color | Mouth Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Mouth_MaterialOutlineColor` | color | Mouth Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1Mouth_OverlayColor` | color | Mouth Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level2Mouth_MouthSkinFung` | blendshape | Mouth Mouth Skin Fung | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_MouthSkinFungR` | blendshape | Mouth Mouth Skin Fung R | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_MouthSkinFungL` | blendshape | Mouth Mouth Skin Fung L | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothHide` | blendshape | Mouth Tooth Hide | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothHideLower` | blendshape | Mouth Tooth Hide Lower | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothHideUpper` | blendshape | Mouth Tooth Hide Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung1` | blendshape | Mouth Tooth Fung1 | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung1Lower` | blendshape | Mouth Tooth Fung1 Lower | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung1Upper` | blendshape | Mouth Tooth Fung1 Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung2` | blendshape | Mouth Tooth Fung2 | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung2Lower` | blendshape | Mouth Tooth Fung2 Lower | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung2Upper` | blendshape | Mouth Tooth Fung2 Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung3` | blendshape | Mouth Tooth Fung3 | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung3Lower` | blendshape | Mouth Tooth Fung3 Lower | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothFung3Upper` | blendshape | Mouth Tooth Fung3 Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothShort` | blendshape | Mouth Tooth Short | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothShortLower` | blendshape | Mouth Tooth Short Lower | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_ToothShortUpper` | blendshape | Mouth Tooth Short Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_LipsFlat` | blendshape | Mouth Lips Flat | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_LipsThick1Upper` | blendshape | Mouth Lips Thick1 Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_LipsThick1Lower` | blendshape | Mouth Lips Thick1 Lower | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_LipsThick2Upper` | blendshape | Mouth Lips Thick2 Upper | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Mouth_LipsThick2Lower` | blendshape | Mouth Lips Thick2 Lower | 0..1 normalized (VRoid may clamp); shape slider |

### Face / Nose — Nose

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Nose_NoseDown` | bone | Nose Nose Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseUp` | bone | Nose Nose Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseWide` | bone | Nose Nose Wide | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBig` | bone | Nose Nose Big | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseSmall` | bone | Nose Nose Small | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseShapeFemale` | bone | Nose Nose Shape Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseShapeMale` | bone | Nose Nose Shape Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseRootLow` | bone | Nose Nose Root Low | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseCurve` | bone | Nose Nose Curve | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBridgeNarrow` | bone | Nose Nose Bridge Narrow | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBridgeWide` | bone | Nose Nose Bridge Wide | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseWingNarrow` | bone | Nose Nose Wing Narrow | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseWingWide` | bone | Nose Nose Wing Wide | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBottomUp` | bone | Nose Nose Bottom Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBottomDown` | bone | Nose Nose Bottom Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBottomForward` | bone | Nose Nose Bottom Forward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseBottomBackward` | bone | Nose Nose Bottom Backward | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseWholeUp` | bone | Nose Nose Whole Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Nose_NoseWholeDown` | bone | Nose Nose Whole Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |

## Hairstyle parameters

Preset sub-slots plus procedural/brush hair. Base hair exposes material colors; front/back/side/ahoge/tied/hanege are replaced by presets and can be texture-edited.

Each category below is addressed with `vroid_enter(section, category)`. The returned `params` are the keys accepted by `vroid_set_param` (or by `vroid_set_bone` / `vroid_set_blendshape` / `vroid_set_color`).

### Hairstyle / AllHair — All hair

_No numeric or color parameter is exposed for this category._

### Hairstyle / BaseHair — Base hair

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1BaseHair_OverlayColor` | color | Base Hair Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BaseHair_MaterialColor` | color | Base Hair Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BaseHair_MaterialShadeColor` | color | Base Hair Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BaseHair_MaterialEmissionColor` | color | Base Hair Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BaseHair_MaterialOutlineColor` | color | Base Hair Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Hair controls beyond group parameters

The hairstyle section has two levels: preset sub-slots and procedural/brush groups. The commands below replace what the VRoid hair tabs expose.

| Need | Tool / keys |
|---|---|
| Replace bangs, back, sideburns, ahoge, tied or whole hair | `vroid_list_presets(filter='Hair')`, `vroid_apply_preset(id=...)` |
| Read procedural/brush groups | `vroid_list_hair_groups` |
| Procedural length / strand count | `vroid_set_procedural_hair(transferable=..., group=..., length=..., hair_count=...)` |
| Lengthen/shorten drawn strands | `vroid_scale_brush_hair(transferable=..., group=..., factor=...)` |
| Duplicate drawn strands | `vroid_clone_brush_hair(transferable=..., group=..., dx,dy,dz)` |
| Hair material colors | `vroid_list_hair_materials`, `vroid_set_hair_color(material=..., key=..., r,g,b)` |
| Make a preset texture editable | `vroid_begin_hair_edit(material=...)`, then `vroid_list_layers` / `vroid_recolor_layer` |

Hair colors are not in `vroid_get_params`. Preset hair tint is often the `base:<id>` key; if the hairstyle paints its color into the texture, recolor the layer in `colorize` mode instead. `Hair/Ahoge`, `Hair/Front`, `Hair/Back`, `Hair/Sideburns`, `Hair/Tied` and `Hair/Hanege` are preset sub-slots, not numeric groups.

## Body parameters

Direct groups. Bone and blendshape sliders for proportions; skin material colors. Paired sliders are mutually exclusive.

Each category below is addressed with `vroid_enter(section, category)`. The returned `params` are the keys accepted by `vroid_set_param` (or by `vroid_set_bone` / `vroid_set_blendshape` / `vroid_set_color`).

### Body / Arm — Arm

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Arm_ArmShort` | bone | Arm Arm Short | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Arm_ArmLong` | bone | Arm Arm Long | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / BodySkin — Body Skin

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1BodySkin_MaterialColor` | color | Body Skin Material Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BodySkin_MaterialShadeColor` | color | Body Skin Material Shade Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BodySkin_MaterialEmissionColor` | color | Body Skin Material Emission Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BodySkin_MaterialOutlineColor` | color | Body Skin Material Outline Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BodySkin_ShadowColor` | color | Body Skin Shadow Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BodySkin_MainColor` | color | Body Skin Main Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1BodySkin_HighlightColor` | color | Body Skin Highlight Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Body / Chest — Chest

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Breast_BustDown` | bone | Breast Bust Down | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Breast_BustUp` | bone | Breast Bust Up | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Breast_BustOpen` | bone | Breast Bust Open | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Breast_BustClose` | bone | Breast Bust Close | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Breast_BustScaleMag` | bone | Breast Bust Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Breast_BustScaleShrink` | bone | Breast Bust Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Breast_BustScaleShrink2` | bone | Breast Bust Scale Shrink2 | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / Hand — Hand

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Hand_HandScaleMag` | bone | Hand Hand Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Hand_HandScaleShrink` | bone | Hand Hand Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Hand_FingerThin` | bone | Hand Finger Thin | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Hand_FingerThick` | bone | Hand Finger Thick | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / Head — Head

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Head_HeadScaleMag` | bone | Head Head Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Head_HeadScaleShrink` | bone | Head Head Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Head_HeadNarrow` | bone | Head Head Narrow | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Head_HeadWide` | bone | Head Head Wide | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / Leg — Leg

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Leg_LegShort` | bone | Leg Leg Short | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Leg_LegLong` | bone | Leg Leg Long | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Foot_FootScaleMag` | bone | Foot Foot Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Foot_FootScaleShrink` | bone | Foot Foot Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / Neck — Neck

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Head_NeckShort` | bone | Head Neck Short | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Head_NeckLong` | bone | Head Neck Long | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Head_NeckAdamsApple` | blendshape | Head Neck Adams Apple | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Head_NeckNarrowX` | blendshape | Head Neck Narrow X | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Head_NeckSpreadX` | blendshape | Head Neck Spread X | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Head_NeckNarrowZ` | blendshape | Head Neck Narrow Z | 0..1 normalized (VRoid may clamp); shape slider |
| `Level2Head_NeckSpreadZ` | blendshape | Head Neck Spread Z | 0..1 normalized (VRoid may clamp); shape slider |

### Body / Shoulder — Shoulder

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Shoulder_ShoulderBroad` | bone | Shoulder Shoulder Broad | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Shoulder_ShoulderNarrow` | bone | Shoulder Shoulder Narrow | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Shoulder_ClavicleLow` | blendshape | Shoulder Clavicle Low | 0..1 normalized (VRoid may clamp); shape slider |

### Body / Torso — Torso

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Torso_WaistShort` | bone | Torso Waist Short | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Torso_WaistLong` | bone | Torso Waist Long | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / Waist — Waist

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2Waist_WaistScaleMag` | bone | Waist Waist Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2Waist_WaistScaleShrink` | bone | Waist Waist Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Body / WholeBody — Whole Body

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2WholeBody_WholeBodyScaleMag` | bone | Whole Body Whole Body Scale Mag | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_WholeBodyScaleShrink` | bone | Whole Body Whole Body Scale Shrink | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_FigureHeightNeutral` | bone | Whole Body Figure Height Neutral | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_FigureHeightFemale` | bone | Whole Body Figure Height Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_FigureHeightMale` | bone | Whole Body Figure Height Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_FigureSlenderNeutral` | bone | Whole Body Figure Slender Neutral | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_FigureSlenderFemale` | bone | Whole Body Figure Slender Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_FigureSlenderMale` | bone | Whole Body Figure Slender Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |

## Outfit parameters

No numeric sliders. Items are presets occupying a slot. Simple colors use `vroid_clothing_colors`; complex edits use `vroid_begin_clothing_edit` then layers.

Each category below is addressed with `vroid_enter(section, category)`. The returned `params` are the keys accepted by `vroid_set_param` (or by `vroid_set_bone` / `vroid_set_blendshape` / `vroid_set_color`).

### Outfit / Bottoms — Bottoms

_No numeric or color parameter is exposed for this category._

### Outfit / InnerBottom — Inner bottom

_No numeric or color parameter is exposed for this category._

### Outfit / InnerTop — Inner top

_No numeric or color parameter is exposed for this category._

### Outfit / Shoes — Shoes

_No numeric or color parameter is exposed for this category._

### Outfit / Socks — Socks

_No numeric or color parameter is exposed for this category._

### Outfit / Tops — Tops

_No numeric or color parameter is exposed for this category._

### Outfit controls and simple/complex access

Clothes have **no numeric slider group** in VRoid. The VRoid `Outfit` tab is a set of preset slots; the Edit button opens textures. This is the main simple/complex distinction:

| Access | Use | Tools |
|---|---|---|
| Simple preset | change the garment / shoes / socks | `vroid_list_presets(filter='Tops'|'Bottoms'|'Onepiece'|'Shoes'|'Socks')`, `vroid_apply_preset`, `vroid_apply_custom`, `vroid_remove_item` |
| Simple color | change a preset's exposed color slots | `vroid_clothing_colors(group=...)`, `vroid_set_color(group=..., key=..., r,g,b)` |
| Complex texture | recolor a layer, export/import a PNG | `vroid_begin_clothing_edit(group=...)`, `vroid_list_layers`, `vroid_recolor_layer`, `vroid_export_layer`, `vroid_import_layer` |
| Shape sliders | skirt tighter/wider/shorter/longer, sleeves, width, length... (Customize > Parameters) | `vroid_get_item_params(type=...)` then `vroid_set_blendshape(group, key='template:...', value=0..100)` |

Clothing and accessory presets also show **Parameters** in VRoid's Customize panel (skirt tighter/wider/shorter/longer, sleeve thickness, width, length, hood...). They are template blendshapes of the item's group, so `vroid_get_params` (colors only for clothing) does not return them. `vroid_get_item_params(type='TransferableGroupType.N00.Level1.Bottoms')` lists them in `sliders`: each has a `key` such as `template:Template_0030...|BlendShape_BlendShape.N00_001_03_Bottoms.Long`, a `label` such as `Model.N00.UniformSkirt.BlendShape.Long` (its last word says what it does: `Narrow` = tighter, `Spread` = wider, `Short`, `Long`, `SleeveThick`, `WidthWide`, `HeightLong`...) and a `value` from **0 to 100** (not 0..1). Set one with `vroid_set_blendshape(group=<group id>, key=<slider key>, value=50)`; it is undoable and returns `readBack`. Each slider is independent (unlike paired body sliders). Keys depend on the preset: read them again after applying another garment.

`Onepiece` replaces Tops and Bottoms; `ClothingSet` can replace the whole outfit. After any whole-set apply, call `vroid_list_groups` because the number and ids of clothing groups can change. `InnerTop` / `InnerBottom` are separate layers, not underwear color sliders.

## Accessories parameters

A head/body accessory is a preset in a slot, not a numeric group. There is no dedicated `vroid_set_*` parameter group for a hat, glasses, ears or tail. The workflow is:

1. `vroid_list_presets(filter='Attachment')` or `filter='Accessory'`, then `vroid_apply_preset`.
2. For a user item: `vroid_apply_custom(key=...|file=...)`.
3. `vroid_list_groups` to see the resulting group. If the item exposes layers, use `vroid_list_layers` and the layer tools; otherwise it is preset-only.
4. `vroid_remove_item(group=...)` to remove it; a short slot name removes every group of that type.

| Preset category | Slot | Access |
|---|---|---|
| `Attachment/BaseballCap`, `SilkHat`, `StrawHat`, `WitchHat`, `WorkCap` | `Hat` | preset |
| `Attachment/CatEar`, `RabbitEar` | `AnimalEar` | preset |
| `Attachment/CatTail`, `FoxTail`, `RabbitTail` | `Tail` | preset |
| `Attachment/GlassesHi`, `GlassesLow` | `Glasses` | preset |
| `Clothing/AccessoryArm` | `ArmAccessory` | preset, optional texture layers |
| `Clothing/AccessoryNeck` | `NeckAccessory` | preset, optional texture layers |

The current model's `vroid_sections` has no Accessories group because it has no accessory applied. This is expected; the preset categories above are still available.

## Look parameters

Overlay presets and a few color/parameter groups. FixedPreset selects the base model; MouthLine/NoseLighting are colors; Cheek/FacePaint/Lip are presets.

Each category below is addressed with `vroid_enter(section, category)`. The returned `params` are the keys accepted by `vroid_set_param` (or by `vroid_set_bone` / `vroid_set_blendshape` / `vroid_set_color`).

### Look / FixedPreset — Fixed Preset

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level2WholeBody_BaseFemale` | bone | Whole Body Base Female | 0..1 normalized (VRoid may clamp); bone/proportion slider |
| `Level2WholeBody_BaseMale` | bone | Whole Body Base Male | 0..1 normalized (VRoid may clamp); bone/proportion slider |

### Look / MouthLine — Mouth Line

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1MouthLine_OverlayColor` | color | Mouth Line Overlay Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

### Look / NoseLighting — Nose Lighting

| Key | Kind | UI label | Range / notes |
|---|---|---|---|
| `Level1NoseLighting_ShadowColor` | color | Nose Lighting Shadow Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1NoseLighting_MainColor` | color | Nose Lighting Main Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |
| `Level1NoseLighting_HighlightColor` | color | Nose Lighting Highlight Color | RGBA components 0..1; `vroid_set_color` / `vroid_set_param` |

## Physical parameters, iris, ears, teeth and mouth

All slider values are **normalized 0..1**; the AI should not try to interpret them as centimetres. Use `vroid_measure` and `vroid_set_body_size` for height. Group ids are obtained with `vroid_list_groups` or `vroid_enter`; keys below are stable across N00 models.

### Height, weight and silhouette

| Key | Effect |
|---|---|
| `Level2WholeBody_FigureHeightFemale/Male/Neutral` | shrink the figure while preserving proportions |
| `Level2WholeBody_FigureSlenderFemale/Male/Neutral` | make the figure taller and thinner |
| `Level2WholeBody_WholeBodyScaleMag/Shrink` | global scale |
| `Level2Waist_WaistScaleMag/Shrink` | waist width; `vroid_set_body_size` converts weight to this |
| `Level2Breast_Bust*` | chest shape (bust up/down/open/close/scale) |

`vroid_set_body_size(height_cm, weight_kg?, gender?)` runs a search on the silhouette slider and reports the actual height; the VRoid slider is limited to -1..1, so an extreme target can be reported as unreachable. Weight is not a VRoid slider: it is approximated as BMI and mapped to waist width.

### Iris / eye size

| Key | Effect |
|---|---|
| `Level3Iris_EyeIrisScaleXMag` / `Shrink` | iris width |
| `Level3Iris_EyeIrisScaleYMag` / `Shrink` | iris height |
| `Level2Eye_EyeSizeX` / `Shrink` | eye width |
| `Level2Eye_EyeSizeY` / `Shrink` | eye height |
| `Level3Iris_GazeUpward/Downward/Inside/Outside` | gaze direction |
| `Level3Iris_MaterialColor` / `LeftOverlayColor` / `RightOverlayColor` | iris colors (RGBA) |

### Ears

| Key | Effect |
|---|---|
| `Level2Ear_EarScaleMag` / `Shrink` | ear size |
| `Level2Ear_EarTipUp/Wide/Down` | ear tip direction |
| `Level2Ear_EarStandUp` / `LieDown` | ear rotation |
| `Level2Ear_EarRound` | roundness |
| `Level2Ear_EarOff` | blendshape that removes/hides the ear mesh |

### Teeth, lips and mouth

| Key | Effect |
|---|---|
| `Level2Mouth_ToothFung1/2/3` (+ `Lower`, `Upper`) | fang/tooth shape |
| `Level2Mouth_ToothShort` (+ `Lower`, `Upper`) | tooth length |
| `Level2Mouth_ToothHide` (+ `Lower`, `Upper`) | hide teeth |
| `Level2Mouth_LipsFlat` | flatten lips |
| `Level2Mouth_LipsThick1Upper/Lower`, `LipsThick2Upper/Lower` | lip thickness |
| `Level2Mouth_MouthUp/Down/Narrow/Wide/CornerUp/CornerDown` | mouth placement |

### Facial expression preview (vowels and emotions)

`vroid_face_preview` is a **display-only** expression preview for captures. It is not a saved model parameter and should not be used with `vroid_set_blendshape`.

| Name suffix | Meaning |
|---|---|
| `MTH_A`, `MTH_I`, `MTH_U`, `MTH_E`, `MTH_O` | Japanese vowel mouth shapes |
| `ALL_Neutral`, `ALL_Angry`, `ALL_Fun`, `ALL_Joy`, `ALL_Sorrow`, `ALL_Surprised` | full-face emotions |
| `EYE_Close`, `EYE_Close_L`, `EYE_Close_R` | both eyes / left / right |
| `EYE_Extra` | extra eye expression exposed by VRoid |

The tool sets the weight of every Face blendshape whose name ends with `name`, 0..100 (default 100). Call it with no `name` to list names; add `filter` to narrow the list. Use an empty name and weight 0 to reset. This is for a screenshot, not for the persistent model. The available names are VRoid's Face renderer names; this is the complete set exposed by the current VRoid 2.16 build.

## Preset categories and replacement slots

A preset is a resource path, not a group id. Applying a preset replaces the item in its slot; whole-set presets such as `ClothingSet`, `HairSet` or `FaceSet` can replace several slots at once. Always verify the result with `vroid_list_groups` after a whole-set apply.

| Section | Preset category | Slot(s) | What it replaces | Presets |
|---|---|---|---|---:|
| Accessories | `Attachment/BaseballCap` | Hat | head wear | 1 |
| Accessories | `Attachment/CatEar` | AnimalEar | animal ears | 1 |
| Accessories | `Attachment/CatTail` | Tail | tail | 1 |
| Accessories | `Attachment/FoxTail` | Tail | tail | 1 |
| Accessories | `Attachment/GlassesHi` | Glasses | glasses | 1 |
| Accessories | `Attachment/GlassesLow` | Glasses | glasses | 1 |
| Accessories | `Attachment/RabbitEar` | AnimalEar | animal ears | 1 |
| Accessories | `Attachment/RabbitTail` | Tail | tail | 1 |
| Accessories | `Attachment/SilkHat` | Hat | head wear | 1 |
| Accessories | `Attachment/StrawHat` | Hat | head wear | 1 |
| Accessories | `Attachment/WitchHat` | Hat | head wear | 1 |
| Accessories | `Attachment/WorkCap` | Hat | head wear | 1 |
| Accessories | `Clothing/AccessoryArm` | ArmAccessory | arm accessory | 20 |
| Accessories | `Clothing/AccessoryNeck` | NeckAccessory | neck accessory | 22 |
| Outfit | `Clothing/Bottoms` | Bottoms | bottom (skirt, trousers, shorts...) | 69 |
| Outfit | `Clothing/InnerBottom` | InnerBottom | inner bottom | 3 |
| Outfit | `Clothing/InnerTop` | InnerTop | inner top | 9 |
| Outfit | `Clothing/Onepiece` | Onepiece | one-piece outfit (replaces top and bottom) | 43 |
| Outfit | `Clothing/Shoes` | Shoes | shoes | 69 |
| Outfit | `Clothing/Socks` | Socks | socks, stockings or bare legs | 34 |
| Outfit | `Clothing/Tops` | Tops | top (shirt, jacket, sweater...) | 102 |
| Hairstyle | `Custom/AllHair` | AllHair | whole hairstyle | 3 |
| Accessories | `Custom/ArmAccessory` | ArmAccessory | arm accessory | 2 |
| Hairstyle | `Custom/BaseHair` | BaseHair | base hair / scalp | 1 |
| Body | `Custom/BodySkin` | BodySkin | body skin | 10 |
| Outfit | `Custom/Bottoms` | Bottoms | bottom (skirt, trousers, shorts...) | 12 |
| Look | `Custom/Cheek` | Cheek | cheek blush | 2 |
| Face | `Custom/EyeHighlight` | EyeHighlight | eye highlight | 2 |
| Face | `Custom/EyeWhite` | EyeWhite | eye white | 2 |
| Face | `Custom/Eyebrow` | Eyebrow | eyebrows | 2 |
| Face | `Custom/Eyelash` | Eyelash | eyelashes | 2 |
| Face | `Custom/Eyeline` | Eyeline | eyeline | 2 |
| Look | `Custom/FacePaint` | FacePaint | face paint / makeup | 1 |
| Face | `Custom/FaceSkin` | FaceSkin | face skin | 8 |
| Hairstyle | `Custom/HairFront` | HairFront | bangs / front hair | 2 |
| Outfit | `Custom/InnerBottom` | InnerBottom | inner bottom | 10 |
| Outfit | `Custom/InnerTop` | InnerTop | inner top | 15 |
| Face | `Custom/Iris` | Iris | iris | 3 |
| Look | `Custom/Lip` | Lip | lips | 2 |
| Face | `Custom/Mouth` | Mouth | mouth (inner texture) | 2 |
| Look | `Custom/MouthLine` | MouthLine | mouth line | 3 |
| Look | `Custom/NoseLighting` | NoseLighting | nose lighting | 2 |
| Outfit | `Custom/Onepiece` | Onepiece | one-piece outfit (replaces top and bottom) | 8 |
| Outfit | `Custom/Shoes` | Shoes | shoes | 6 |
| Outfit | `Custom/Tops` | Tops | top (shirt, jacket, sweater...) | 13 |
| Face | `Face/Ear` | Ear | ear shape (preset) | 51 |
| Face | `Face/EyeHighlight` | EyeHighlight | eye highlight | 66 |
| Face | `Face/EyeSurrounding` | EyeSurrounding | eye surrounding | 51 |
| Face | `Face/EyeWhite` | EyeWhite | eye white | 11 |
| Face | `Face/Eyebrow` | Eyebrow | eyebrows | 65 |
| Face | `Face/Eyelash` | Eyelash | eyelashes | 47 |
| Face | `Face/Eyelid` | Eyelid | eyelid | 36 |
| Face | `Face/Eyeline` | Eyeline | eyeline | 67 |
| Face | `Face/FaceShape` | FaceShape | face shape | 52 |
| Face | `Face/Iris` | Iris | iris | 57 |
| Face | `Face/Mouth` | Mouth | mouth (inner texture) | 11 |
| Face | `Face/Nose` | Nose | nose shape | 51 |
| Hairstyle | `Hair/Ahoge` | HairAhoge | ahoge | 26 |
| Hairstyle | `Hair/AllHair` | AllHair | whole hairstyle | 41 |
| Hairstyle | `Hair/Back` | HairBack | back hair | 31 |
| Hairstyle | `Hair/Base` | BaseHair | base hair / scalp | 3 |
| Hairstyle | `Hair/Front` | HairFront | bangs / front hair | 50 |
| Hairstyle | `Hair/Hanege` | HairHanege | flipped ends | 66 |
| Hairstyle | `Hair/Sideburns` | HairSideburns | sideburns | 66 |
| Hairstyle | `Hair/Tied` | HairTied | tied hair | 72 |
| Look | `Overlay/Cheek` | Cheek | cheek blush | 37 |
| Look | `Overlay/FacePaint` | FacePaint | face paint / makeup | 31 |
| Look | `Overlay/Lip` | Lip | lips | 26 |
| Look | `Overlay/MouthLine` | MouthLine | mouth line | 11 |
| Look | `Overlay/NoseLighting` | NoseLighting | nose lighting | 39 |
| Body | `Skin/Body` | BodySkin | body skin | 7 |
| Face | `Skin/Face` | FaceSkin | face skin | 13 |
| Body | `VRoid/Body` | Arm, Chest, Hand, Head, Leg, Neck, Shoulder, Torso, Waist, WholeBody | Arm, Chest, Hand, Head, Leg, Neck, Shoulder, Torso, Waist, WholeBody | 20 |
| Outfit | `VRoid/ClothingSet` | ClothingSet | whole outfit | 69 |
| Face | `VRoid/EyeSet` | EyeSet | whole eye set | 52 |
| Face | `VRoid/EyeballSet` | EyeballSet | eyeballs | 51 |
| Face | `VRoid/FaceSet` | FaceSet | whole face | 52 |
| Look | `VRoid/FixedPreset` | FixedPreset | base model preset | 2 |
| Hairstyle | `VRoid/HairSet` | HairSet | ready-made whole hairstyle | 37 |

Use `vroid_list_presets(filter=...)` to search by category or resource path, `vroid_apply_preset(id=...)` to apply one, and `vroid_apply_custom(key=...|file=...)` for custom items. Presets that are not owned are hidden unless `include_locked=true` is passed.

## Complete MCP tool reference

The server exposes **53 tools**. This is the authoritative list; the same descriptions and JSON schemas are available to the client through MCP `tools/list`.

Tool names and arguments are always English. `vroid_help` is the only tool that works without VRoid; all others need VRoid Studio running with the bridge loaded.

### `vroid_help`

Show the built-in manual. Topics: overview, tools, lifecycle, export, framing, thumbnails, colors, outfit, sessions, errors, languages, batch. lang=en|fr|ja|zh-CN. Call this first when unsure.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `topic` | string | no | help topic (default overview) |  |
| `lang` | string | no | manual language: en (default), fr, ja, zh-CN | enum: en, fr, ja, zh, zh-CN |

### `vroid_batch`

Run several vroid_* operations sequentially in one MCP call and return a text summary plus optional images. Up to 200 operations, no nested batches, no automatic rollback. stop_on_error defaults to true. Images are capped (8 images / 16 MiB); excess images are reported by path only. Save before destructive sequences.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `operations` | array of objects (tool, args) | yes | Sequential operations; each item is `{tool: 'vroid_*', args: {...}}`. No nested batch, no rollback. | items: 1..200; nested: tool (string), args (object) |
| `stop_on_error` | boolean | no | stop at the first error (default true) |  |
| `include_images` | boolean | no | include returned images in the same response (default true, capped) |  |

### `vroid_status`

Report whether VRoid Studio responds, whether a model is open, its current file, whether it has unsaved changes (dirty) and whether the editor is ready.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_create`

Create a new model from the VRoid template (female or male), like the Create New Model dialog. VRoid must be at the model-select screen (no model open). Blocks until the model is ready. The new model has no file yet: use vroid_save with path to save it.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `gender` | string | yes | template to create | enum: female, male |

### `vroid_open`

Open a .vroid file and wait until the model is ready. VRoid must be at the model-select screen (no model open): save and call vroid_main_menu first if needed. path must be absolute.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `path` | string | yes | absolute path of the .vroid file |  |

### `vroid_save`

Save the open model. With path: Save As (creates the file). Without path: save in place, only if the model already has a .vroid file. A model created with vroid_create has no file yet: pass path.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `path` | string | no | absolute path of the .vroid file to write (optional) |  |

### `vroid_export_vrm`

Export the open model as a .vrm file with VRoid's own exporter, without clicks or file dialog (same options as the 'Export as VRM' screen). Options left out use VRoid's defaults: VRM 1.0, transparent meshes deleted, no reduction. Takes about 10-40 s. Reduction sliders are 0..100. material_mode: 0 Default, 1 = 2 materials, 2 = 8, 3 = 12. Texture size: with material_mode 0 use texture_mode 1 (Shrunk); with material reduction VRoid uses the atlas instead, so use atlas_resolution 1 (2048) to shrink textures. Any option VRoid refused is listed in 'warnings'. The model itself is not modified.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `path` | string | yes | absolute path of the .vrm to write |  |
| `version` | string | no | 1 = VRM 1.0 (default), 0 = VRM 0.x | enum: 1, 0 |
| `title` | string | no | model name in the VRM meta (default: file name) |  |
| `author` | string | no | author in the VRM meta |  |
| `model_version` | string | no | model version in the VRM meta |  |
| `delete_transparent` | boolean | no | Delete Transparent Meshes (default true) |  |
| `hair_cross_section` | boolean | no | Edit Hair Cross-Section (default false) |  |
| `hair_smoothness` | number | no | Hair Smoothness reduction 0..100 |  |
| `hair` | number | no | hair polygon reduction 0..100 |  |
| `face` | number | no | face polygon reduction 0..100 |  |
| `body` | number | no | body polygon reduction 0..100 |  |
| `outfit` | number | no | outfit polygon reduction 0..100 |  |
| `material_mode` | number | no | 0 Default, 1 = 2 materials, 2 = 8 materials, 3 = 12 materials |  |
| `combine_hair` | boolean | no | Combine Hair Mesh (default true) |  |
| `texture_mode` | number | no | 0 Original, 1 Shrunk (only without material reduction) |  |
| `atlas_resolution` | number | no | with material reduction: 0 = 4096, 1 = 2048 |  |
| `hair_bones` | number | no | Reduce Bones: Hair 0..100 |  |
| `leave` | boolean | no | return to the editor after export (default true); false leaves the export screen open |  |

### `vroid_export_vrm_options`

Open VRoid's export screen and return its current export settings and the available material / texture / atlas choices. Close it again with vroid_export_vrm or by passing leave.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `leave` | boolean | no | close the export screen after reading (default true) |  |

### `vroid_main_menu`

Return to the model-select screen without quitting VRoid, so another model can be opened or created. Refuses when there are unsaved changes unless discard=true.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `discard` | boolean | no | discard unsaved changes |  |

### `vroid_exit`

Quit VRoid Studio gracefully. Refuses unsaved changes unless discard=true. The response is sent before the process exits; use it after a generation sequence.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `discard` | boolean | no | discard unsaved changes before quitting |  |

### `vroid_framing_get`

Read thumbnail framing profiles per category/body part (e.g. Clothing/Tops, Clothing/Shoes, Hair, Face, VRoid/ClothingSet), never per individual garment: garment facts stay in the cache. top/bottom are fractions from the top of the model (0 = top, 1 = feet), half is the half-width (null = full width), distance is the zoom-out factor, yaw is the orientation in degrees (0 = front, 90 = profile, 180 = back), fit=region|full-body. Without category: all known categories.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `category` | string | no | category (e.g. Clothing/Tops); empty = all |  |

### `vroid_framing_set`

Change the framing of a category/body part (e.g. Clothing/Tops, Clothing/Shoes, Hair, Face, VRoid/ClothingSet), never an individual garment: the override is local and does not modify committed defaults. top/bottom in 0..1, half null or 0.01..1, distance 1..10, yaw -180..180 (0 = front, 90 = profile, 180 = back), fit=region|full-body. vroid_framing_reset restores the defaults.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `category` | string | yes | category (e.g. VRoid/ClothingSet) |  |
| `top` | number | no | fraction from the top (0 = top) |  |
| `bottom` | number | no | fraction from the top (1 = feet) |  |
| `half` | number | no | half-width as a fraction of height |  |
| `distance` | number | no | zoom-out factor (default 3.3; 4.2 for a whole outfit) |  |
| `yaw` | number | no | orientation in degrees: 0 front, 90 profile, 180 back |  |
| `fit` | string | no |  | enum: region, full-body |

### `vroid_framing_reset`

Clear framing overrides (all, or one category/body part) and return to the committed defaults in config/framing.json. Local overrides live in preset_cache/framing_overrides.json.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `category` | string | no | category to reset; empty = all |  |

### `vroid_list_groups`

List the editable groups of the open model (face, eyes, hair, body, outfits...). Each group has an id to pass to the other tools.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_get_params`

List the parameters of a group (blendshape sliders, bones, colors) with their current values.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | group id |  |

### `vroid_get_item_params`

List every adjustable parameter of the model's items, including the ones VRoid shows under Customize > Parameters for clothing (skirt tighter/wider/shorter/longer, sleeve length, collar...) but which live outside the outfit groups: vroid_list_groups and vroid_get_params do not see them. Returns groups (type, active flag, number of editable elements, current values) and the model's global parameters. Set one with vroid_set_blendshape or vroid_set_bone using the returned group id and key.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `type` | string | no | optional group type filter, e.g. TransferableGroupType.N00.Level1.Bottoms |  |

### `vroid_sections`

List editable sections and their categories (Face, Hairstyle, Body, Outfit, Accessories, Look), with group counts. High-level companion to vroid_list_groups.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_categories`

List categories in a section (or all categories), with category key, label, section and group count. Use with vroid_enter / vroid_set_param.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `section` | string | no | section name (optional: Face, Hairstyle, Body, Outfit, Accessories, Look) |  |

### `vroid_enter`

Select a section/category by name and return its group and enriched parameters (labels + stable section/category/key paths). Equivalent in spirit to enter(), without changing VRoid's UI tab.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `section` | string | yes | section, e.g. Face, Hairstyle, Body, Outfit |  |
| `category` | string | yes | category or human label from vroid_categories |  |

### `vroid_set_param`

Set a parameter by section/category and key or short label; dispatches to bone, blendshape or color. Accepts numbers, #RRGGBB or r,g,b for colors. Unified counterpart of vroid_set_bone / vroid_set_blendshape / vroid_set_color.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `section` | string | yes | section, e.g. Face, Hairstyle, Body, Outfit |  |
| `category` | string | yes | category or human label from vroid_categories |  |
| `param` | string | yes | parameter key, path or short label from vroid_enter |  |
| `value` | number or string | yes | numeric value, #RRGGBB or r,g,b |  |

### `vroid_set_blendshape`

Set a shape slider (blendshape) of a group. Undoable in VRoid (Ctrl+Z).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | group id |  |
| `key` | string | yes | parameter key (see vroid_get_params) |  |
| `value` | number | yes | new value |  |

### `vroid_set_bone`

Set a bone transform parameter (body proportions, size...).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | group id |  |
| `key` | string | yes | parameter key |  |
| `value` | number | yes | new value |  |

### `vroid_set_color`

Set a color (components 0..1). Undoable in VRoid.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | group id |  |
| `key` | string | yes | color parameter key |  |
| `r` | number | yes | red 0..1 |  |
| `g` | number | yes | green 0..1 |  |
| `b` | number | yes | blue 0..1 |  |
| `a` | number | no | alpha 0..1 (default 1) |  |

### `vroid_colorize`

Composite color pass: apply one color to both the global/material colors and the texture layers of a group (clothing or hair). target=global|texture|both. Fine-grained vroid_set_color / vroid_recolor_layer remain available. Undoable; hair textures may not be exposed, in which case a warning is returned.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | group id |  |
| `r` | number | yes | red 0..1 |  |
| `g` | number | yes | green 0..1 |  |
| `b` | number | yes | blue 0..1 |  |
| `target` | string | no | global colors, texture layers, or both (default) | enum: global, texture, both |
| `mode` | string | no | texture recolor mode (default multiply) | enum: multiply, colorize |
| `strength` | number | no | texture strength 0..1 (default 1) |  |
| `material` | string | no | hair material id (optional; default all) |  |
| `layer` | string | no | texture layer node (optional; default all) |  |

### `vroid_list_layers`

List the editable textures of a group (e.g. skirt = Bottoms): items (transferable), images and layers (node, name, opacity, visibility, blend mode). Clothes have no color sliders: their color is changed through their texture layers.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | group id |  |

### `vroid_recolor_layer`

Recolor a texture layer in place, preserving transparency; undoable. mode 'multiply': light fabric -> target color while keeping shadows and folds. mode 'colorize': keeps luminance, forces the hue (for already colored fabric).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `transferable` | string | yes | item id (vroid_list_layers) |  |
| `image` | string | yes | image id |  |
| `node` | string | yes | layer id |  |
| `r` | number | yes | red 0..1 |  |
| `g` | number | yes | green 0..1 |  |
| `b` | number | yes | blue 0..1 |  |
| `mode` | string | no |  | enum: multiply, colorize |
| `strength` | number | no | strength 0..1 (default 1) |  |

### `vroid_export_layer`

Export a texture layer as PNG (RGBA) to edit it with another tool.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `transferable` | string | yes | item id |  |
| `image` | string | yes | image id |  |
| `node` | string | yes | layer id |  |
| `path` | string | no | PNG output path (optional) |  |

### `vroid_import_layer`

Import a PNG into a layer (same size as the export) or as a new layer. Undoable.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `transferable` | string | yes | item id |  |
| `image` | string | yes | image id |  |
| `node` | string | no | layer id to replace (ignored if as_new_layer) |  |
| `path` | string | yes | PNG path |  |
| `as_new_layer` | boolean | no | add as a new layer instead of replacing |  |

### `vroid_list_hair_materials`

List hair materials (hair color is not exposed by vroid_get_params): id, name, adjustable colors (key + value) and textures with their layers (transferable/image/node usable with vroid_recolor_layer).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_set_hair_color`

Set a color of a hair material (components 0..1). Undoable. 'base:<id>' keys are the overlay hair tint of a preset: change that key to recolor a preset hairstyle (material is optional in that case). For hair whose color is painted in the texture, recolor the layers instead (mode colorize).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `material` | string | yes | material id (vroid_list_hair_materials) |  |
| `key` | string | yes | color key |  |
| `r` | number | yes | red 0..1 |  |
| `g` | number | yes | green 0..1 |  |
| `b` | number | yes | blue 0..1 |  |
| `a` | number | no | alpha 0..1 (default 1) |  |

### `vroid_list_hair_groups`

List hair groups: 'procedural' (adjustable length and strand count) or 'brush' (drawn strands: strand count, average length).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_set_procedural_hair`

Set the length and/or strand count of a procedural hair group. Undoable.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `transferable` | string | yes | item id (vroid_list_hair_groups) |  |
| `group` | string | yes | group id |  |
| `length` | number | no | new length (optional) |  |
| `hair_count` | number | no | strand count (optional) |  |

### `vroid_scale_brush_hair`

Lengthen (factor > 1) or shorten (factor < 1) all strands of a brush hair group from their root. Undoable (one step per point).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `transferable` | string | yes | item id |  |
| `group` | string | yes | group id |  |
| `factor` | number | yes | factor, e.g. 1.3 |  |

### `vroid_clone_brush_hair`

Duplicate a group of brush strands and offset the copy (in meters, model space) to add strands.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `transferable` | string | yes | item id |  |
| `group` | string | yes | group id |  |
| `dx` | number | no | X offset |  |
| `dy` | number | no | Y offset |  |
| `dz` | number | no | Z offset |  |

### `vroid_undo`

Undo the last change in VRoid Studio.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_redo`

Redo the last undone change.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_screenshot`

Capture a clean 3D preview of the avatar (no VRoid UI) and return the image. MSAA 4x and SSAA 2x by default; width/height override the output size; clean=false captures the whole window. Use it to inspect edits accurately.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `msaa` | number | no | MSAA samples 1..8 (default 4) |  |
| `ssaa` | number | no | supersampling factor 1..3 (default 2) |  |
| `width` | number | no | output width in pixels (0 = camera viewport) |  |
| `height` | number | no | output height in pixels (0 = camera viewport) |  |
| `clean` | boolean | no | true = 3D preview only (default), false = full window |  |

### `vroid_list_presets`

List VRoid presets (hairstyles, faces, outfits, bodies...). filter searches the resource path (e.g. 'Hair', 'Tops', 'Bottoms', 'Onepiece', 'Shoes', 'Face'). Also returns the list of categories. Only free or owned presets are listed unless include_locked.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `filter` | string | no | text to search for (optional) |  |
| `include_locked` | boolean | no | include paid presets that are not owned |  |
| `limit` | number | no | maximum number of results (default 200) |  |

### `vroid_apply_preset`

Apply a preset (replaces the item in the same category, like clicking its thumbnail). Undoable. Whole-set presets can replace several slots: verify with vroid_list_groups.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `id` | string | yes | preset id (vroid_list_presets) |  |
| `preserve_material` | boolean | no | keep the current material (colors) if possible |  |

### `vroid_clothing_colors`

List the adjustable colors of a clothing item (same preset): group + key to pass to vroid_set_color.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | clothing group id |  |

### `vroid_begin_clothing_edit`

Switch a preset clothing item to texture editing (like VRoid's Edit button): its layers become available to vroid_list_layers / vroid_recolor_layer. Undoable.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | clothing group id |  |

### `vroid_measure`

Measure the current model height in cm (same as VRoid's size label) and its bounds.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| — | — | — | — | No arguments. |

### `vroid_set_body_size`

Set the height (cm) directly through the gender silhouette slider (FigureHeight/FigureSlender, proportions preserved), and optionally weight (kg), converted to waist width via BMI (VRoid has no weight). gender: female, male or neutral. Undoable.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `height_cm` | number | yes | target height in cm |  |
| `weight_kg` | number | no | target weight in kg (optional) |  |
| `gender` | string | no | default female | enum: female, male, neutral |

### `vroid_preset_cache_search`

Search the shared preset and custom-item cache (no VRoid needed): labels, descriptions, tags and colors (manual and auto-generated), plus the thumbnail path. Each result has label/labelSource/generated and preview: {kind, mannequin, clothing, underwear, hair, keptSlot, orientation, yaw, capturedAt, pixels, source}. Situation thumbnails are captured on a nude mannequin and framed front-on. All query words must match (e.g. 'short pleated blue skirt').

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `query` | string | no | words to search for (optional) |  |
| `category` | string | no | e.g. Clothing/Tops (optional) |  |
| `annotated_only` | boolean | no | only presets that already have a description |  |
| `include_locked` | boolean | no | include paid presets that are not owned |  |
| `kind` | string | no | built-in presets or custom items | enum: preset, custom |
| `status` | string | no | new / changed in the last scan | enum: new, changed |
| `include_removed` | boolean | no | include items absent from VRoid |  |
| `limit` | number | no | default 50 |  |

### `vroid_preset_cache_annotate`

Add or correct the label, description, tags and colors of a preset in the shared cache, for other AIs. A manual label overrides the generated one. Short lowercase tags (type, color, length, style).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `key` | string | yes | preset resource path or id |  |
| `label` | string | no | manual label (overrides the generated label) |  |
| `description` | string | no | short text |  |
| `tags` | array of string | no |  |  |
| `colors` | array of string | no |  |  |
| `author` | string | yes | who annotates (e.g. AI model name) |  |
| `replace` | boolean | no | replace tags/colors instead of adding |  |

### `vroid_preset_thumbnail`

Return the thumbnail of a preset or custom item (image) to judge it without applying it: situation capture if available, otherwise VRoid's native icon (fetched on demand). Thumbnail metadata (mannequin, clothing, underwear, framing) is in the vroid_preset_cache_search result under preview.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `key` | string | yes | resource path or id |  |

### `vroid_preset_cache_sync`

Scan what VRoid currently exposes: built-in presets AND custom items (with the name given in VRoid). Reports new, changed (renamed custom item or new revision) and removed items without erasing annotations; generates structural labels for new entries. Runs automatically on each VRoid start. icons=true also fetches native preset icons (fast, nothing is applied).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `icons` | boolean | no | fetch missing native icons |  |
| `icon_limit` | number | no | maximum number of icons to fetch |  |

### `vroid_preset_cache_build`

Create situation thumbnails for a category (presets, or Custom/<slot> for custom items). Removes ALL clothes, accessories, underwear (including default underwear, which shows through swimwear) and hair except BaseHair/the tested item; frames the character front-on and centered on its bounds; applies each item, checks that nothing else remains, captures, crops, then restores the original outfit. Writes thumbnailMeta (nude mannequin, clothing=tested-item-only, underwear=removed, strippedSlots, camera with fit, pixels, sha1) into catalog.json. Also generates a label and visual metadata (colors, brightness, plain/patterned) from the thumbnail; manual labels are never overwritten. Whole outfits pull the camera back so shoes stay visible; orientation (profile yaw: back for back hair, three-quarter for shoes/arm accessories) is applied. Save the model first: restoration is not guaranteed to be identical. About 3 s per preset; native icons (sync icons=true) are faster.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `category` | string | yes | e.g. Clothing/Shoes |  |
| `refresh` | boolean | no | also rebuild existing thumbnails |  |
| `limit` | number | no | maximum number of presets to process |  |

### `vroid_camera`

Aim the VRoid 3D view at the model from another angle before a capture. action: get (state + preset rotations), angles (x,y in degrees), rotate (dx,dy), zoom (d), pan (x,y), reset (initial view), mode (VRoid preset rotation), projection (toggle perspective/orthographic), custom (px,py,pz,cx,cy,cz).

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `action` | string | yes |  | enum: get, angles, rotate, zoom, pan, reset, mode, projection, custom |
| `x` | number | no | angle or X offset |  |
| `y` | number | no | angle or Y offset |  |
| `dx` | number | no | relative X rotation |  |
| `dy` | number | no | relative Y rotation |  |
| `d` | number | no | zoom |  |
| `mode` | string | no | preset rotation name |  |
| `px` | number | no |  |  |
| `py` | number | no |  |  |
| `pz` | number | no |  |  |
| `cx` | number | no |  |  |
| `cy` | number | no |  |  |
| `cz` | number | no |  |  |

### `vroid_apply_custom`

Apply one of the user's custom items, like clicking it in VRoid's Custom tab: replaces the item in the same category. key = cache key (vroid_preset_cache_search kind=custom) or file = path to the .vroidcustomitem file. Undoable.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `key` | string | no | cache key (custom:...) |  |
| `file` | string | no | path of the .vroidcustomitem file |  |

### `vroid_remove_item`

Remove an item from the model (clothing, accessory, shoes...). group = group id, or a short type to remove all groups of that type (Tops, Bottoms, Onepiece, Socks, Shoes, InnerTop, ArmAccessory, NeckAccessory...). Useful to start from a model without clothes before creating thumbnails.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `group` | string | yes | id or short type |  |

### `vroid_face_preview`

Expression preview for a capture (open mouth to show teeth, smile, wink...): set the weight (0..100) of face blendshapes whose name ends with name (e.g. MTH_A, MTH_O, ALL_Joy, EYE_Close). Without name: list names (optional filter). Display only, nothing is saved; empty name with weight 0 resets everything.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `name` | string | no | blendshape name suffix |  |
| `weight` | number | no | 0..100 (default 100) |  |
| `filter` | string | no | filter for listing names |  |

### `vroid_begin_hair_edit`

Switch a hair material to texture editing (VRoid's Edit button): its texture becomes available to the layer tools. Useful for a preset hairstyle whose texture is not editable.

| Argument | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `material` | string | yes | material id (vroid_list_hair_materials) |  |

## Normalized 0..1 and paired-slider rules

`vroid_set_bone`, `vroid_set_blendshape` and the numeric branch of `vroid_set_param` use VRoid's normalized slider values, generally **0..1**. Values outside that range are not meaningful and may be clamped by VRoid. Colors are RGBA with components 0..1; `vroid_set_param` also accepts `#RRGGBB` or `r,g,b` for a color parameter.

Many controls are two halves of one UI slider. Set one and the other half returns to zero:

- `...Mag` / `...Shrink`
- `...Long` / `...Short`
- `...Wide` / `...Narrow`
- `...Up` / `...Down`
- `...Forward` / `...Backward`
- `FigureHeight<Gender>` / `FigureSlender<Gender>`
- `...Female` / `...Male`

## Workflows an agent can follow

### Inspect before changing

```text
vroid_status
vroid_sections
vroid_categories(section='Face')
vroid_list_groups
vroid_enter(section='Face', category='Iris')
vroid_get_params(group='<group id>')
```

### Change a face or body parameter

```text
vroid_enter(section='Face', category='Mouth')
vroid_set_param(section='Face', category='Mouth', param='Level2Mouth_ToothShortUpper', value=0.4)
vroid_screenshot
```

### Simple color versus complex clothing edit

Simple color (clothing color slots when the preset exposes them):

```text
vroid_clothing_colors(group='<clothing group id>')
vroid_set_color(group='<group id>', key='<color key>', r=0.2, g=0.4, b=0.8)
```

Complex texture edit (the clothing/preset tab's Edit button):

```text
vroid_begin_clothing_edit(group='<clothing group id>')
vroid_list_layers(group='<group id>')
vroid_recolor_layer(transferable='<transferable>', image='<image>', node='<node>', r=0.2, g=0.4, b=0.8, mode='multiply')
```

For a hair preset whose texture is not editable, call `vroid_begin_hair_edit(material=...)` first, then use the same layer tools. Hair colors are separate from hair textures: use `vroid_list_hair_materials` and `vroid_set_hair_color`.

### Preset variants and batches

```text
vroid_preset_cache_search(query='short pleated blue skirt', category='Clothing/Bottoms')
vroid_apply_preset(id='<preset resource path>')
vroid_list_groups
```

`vroid_batch` accepts up to 200 `{tool,args}` operations, runs them sequentially and returns a text summary plus at most 8 images / 16 MiB. It has no rollback, no nested batches and no `vroid_help` / `vroid_exit` inside a batch. Save before destructive sequences.

### Expression capture

```text
vroid_face_preview(filter='Fcl_')          # list names
vroid_face_preview(name='MTH_A', weight=80)
vroid_camera(action='angles', x=0, y=20)
vroid_screenshot(width=1200, height=1600)
vroid_face_preview(name='', weight=0)      # reset
```

## Failure modes and recovery

| Symptom | Meaning | Recovery |
|---|---|---|
| `VRoid Studio is not responding` | bridge/plugin not loaded or VRoid closed | start VRoid, wait for the first editor load, call `vroid_status` |
| `VRoid Studio is open` during install | installer refuses to modify a running game | close VRoid, retry |
| `model is dirty` / `unsaved changes` | lifecycle operation would discard work | `vroid_save` or `discard=true` (`vroid_main_menu`/`vroid_exit`) |
| group id not accepted | ids change when a model/outfit changes | call `vroid_list_groups` again; never cache ids across models |
| key not found | model type/slot does not expose it | `vroid_enter` / `vroid_get_params`; use a preset/texture path |
| image path returned but no image | response exceeded 8 images/16 MiB | read the file path, or request images separately |
| export option in `warnings` | VRoid refused the option | do not assume it was applied; inspect `settings` in the response |

## Source of truth and drift control

- `tools/list` (MCP) is the machine source of truth for names, descriptions and JSON schemas.
- `vroid_help` is the built-in narrative source of truth and works without VRoid.
- This document adds the UI/parameter catalog and workflows; tool schemas are generated from the live registry.
- Group ids are model-specific and must be read at runtime. Parameter keys and group types are stable for N00 models.
- If a future VRoid update changes the available groups, regenerate this file with VRoid open:

```text
python tools/gen_agent_reference_en.py
```

_Generated 2026-10-30 from VRoid MCP Bridge 0.14.0._
