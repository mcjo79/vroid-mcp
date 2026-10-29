#!/usr/bin/env python3
"""Generate docs/AGENT_REFERENCE_EN.md from the live VRoid MCP registry.

Run with VRoid Studio open (the plugin must be loaded) from the repository root:

    python tools/gen_agent_reference_en.py

The generated document is committed and shipped in the release `docs/` folder.
It is intentionally agent-facing: tool schemas, UI/parameter mapping, physical
parameters, expression limits and workflows in one English file.
"""
from __future__ import annotations

import collections
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcp_server"))

import preset_cache as pc  # noqa: E402
import vroid_mcp as v  # noqa: E402

OUT = os.path.join(ROOT, "docs", "AGENT_REFERENCE_EN.md")

SECTION_ACCESS = {
    "Face": "Direct groups. Most entries are normalized 0..1 bone or blendshape sliders; colors are RGBA 0..1. Some entries are overlays/textures rather than sliders.",
    "Hairstyle": "Preset sub-slots plus procedural/brush hair. Base hair exposes material colors; front/back/side/ahoge/tied/hanege are replaced by presets and can be texture-edited.",
    "Body": "Direct groups. Bone and blendshape sliders for proportions; skin material colors. Paired sliders are mutually exclusive.",
    "Outfit": "No numeric sliders. Items are presets occupying a slot. Simple colors use `vroid_clothing_colors`; complex edits use `vroid_begin_clothing_edit` then layers.",
    "Accessories": "Preset slots (Attachment/*, AccessoryArm/Neck). No dedicated numeric parameter group; apply/remove presets, then use layers only if the item exposes them.",
    "Look": "Overlay presets and a few color/parameter groups. FixedPreset selects the base model; MouthLine/NoseLighting are colors; Cheek/FacePaint/Lip are presets.",
}

SLOT_DESC = {
    "Hat": "head wear",
    "AnimalEar": "animal ears",
    "Tail": "tail",
    "Glasses": "glasses",
    "ArmAccessory": "arm accessory",
    "NeckAccessory": "neck accessory",
    "Tops": "top (shirt, jacket, sweater...)",
    "Bottoms": "bottom (skirt, trousers, shorts...)",
    "Onepiece": "one-piece outfit (replaces top and bottom)",
    "Shoes": "shoes",
    "Socks": "socks, stockings or bare legs",
    "InnerTop": "inner top",
    "InnerBottom": "inner bottom",
    "Ear": "ear shape (preset)",
    "EyeHighlight": "eye highlight",
    "EyeSurrounding": "eye surrounding",
    "EyeWhite": "eye white",
    "Eyebrow": "eyebrows",
    "Eyelash": "eyelashes",
    "Eyelid": "eyelid",
    "Eyeline": "eyeline",
    "FaceShape": "face shape",
    "Iris": "iris",
    "Mouth": "mouth (inner texture)",
    "Nose": "nose shape",
    "HairAhoge": "ahoge",
    "AllHair": "whole hairstyle",
    "HairBack": "back hair",
    "BaseHair": "base hair / scalp",
    "HairFront": "bangs / front hair",
    "HairHanege": "flipped ends",
    "HairSideburns": "sideburns",
    "HairTied": "tied hair",
    "Cheek": "cheek blush",
    "FacePaint": "face paint / makeup",
    "Lip": "lips",
    "MouthLine": "mouth line",
    "NoseLighting": "nose lighting",
    "BodySkin": "body skin",
    "FaceSkin": "face skin",
    "Body": "body preset (one file per body part)",
    "ClothingSet": "whole outfit",
    "EyeSet": "whole eye set",
    "EyeballSet": "eyeballs",
    "FaceSet": "whole face",
    "FixedPreset": "base model preset",
    "HairSet": "ready-made whole hairstyle",
}

SECTION_ORDER = ["Face", "Hairstyle", "Body", "Outfit", "Accessories", "Look"]


def esc(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def kind_text(prop: dict) -> str:
    t = prop.get("type")
    if isinstance(t, list):
        return " or ".join(str(x) for x in t)
    if t == "array":
        item = prop.get("items", {})
        if item.get("type") == "object":
            fields = ", ".join(item.get("properties", {}).keys())
            return f"array of objects ({fields})"
        return f"array of {item.get('type', 'items')}"
    return str(t or "any")


def schema_rows(tool: dict) -> list[str]:
    schema = tool.get("inputSchema") or {}
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    if not props:
        return ["| — | — | — | — | No arguments. |"]
    rows = []
    for name, prop in props.items():
        bits = []
        if "enum" in prop:
            bits.append("enum: " + ", ".join(str(x) for x in prop["enum"]))
        if "minimum" in prop or "maximum" in prop:
            bits.append(f"range: {prop.get('minimum', '?')}..{prop.get('maximum', '?')}")
        if "minItems" in prop or "maxItems" in prop:
            bits.append(f"items: {prop.get('minItems', '?')}..{prop.get('maxItems', '?')}")
        if "default" in prop:
            bits.append(f"default: {prop['default']}")
        if prop.get("type") == "array" and prop.get("items", {}).get("properties"):
            nested = prop["items"]["properties"]
            bits.append("nested: " + ", ".join(f"{k} ({kind_text(v)})" for k, v in nested.items()))
        desc = prop.get("description", "")
        if tool["name"] == "vroid_batch" and name == "operations":
            desc = "Sequential operations; each item is `{tool: 'vroid_*', args: {...}}`. No nested batch, no rollback."
        rows.append("| `{}` | {} | {} | {} | {} |".format(
            esc(name),
            esc(kind_text(prop)),
            "yes" if name in required else "no",
            esc(desc),
            esc("; ".join(bits)),
        ))
    return rows


def tool_section() -> list[str]:
    out = []
    out += [
        "## 13. Complete MCP tool reference",
        "",
        f"The server exposes **{len(v.TOOLS)} tools**. This is the authoritative list; "
        "the same descriptions and JSON schemas are available to the client through MCP `tools/list`.",
        "",
        "Tool names and arguments are always English. `vroid_help` is the only tool that works without VRoid; "
        "all others need VRoid Studio running with the bridge loaded.",
        "",
    ]
    for idx, tool in enumerate(v.TOOLS, 1):
        desc = tool.get("description", "").strip()
        if tool["name"] == "vroid_help":
            desc = desc.replace("lang=en|fr|ja.", "lang=en|fr|ja|zh-CN.")
        out += [f"### 13.{idx} `{tool['name']}`", "", desc, ""]
        out += ["| Argument | Type | Required | Description | Constraints |", "|---|---|---|---|---|"]
        out += schema_rows(tool)
        out.append("")
    return out


def param_table(params: list[dict]) -> list[str]:
    if not params:
        return ["_No numeric or color parameter is exposed for this category._", ""]
    rows = ["| Key | Kind | UI label | Range / notes |", "|---|---|---|---|"]
    for p in params:
        kind = p.get("kind", "?")
        note = "0..1 normalized (VRoid may clamp)" if kind in ("bone", "blendshape") else "RGBA components 0..1"
        if kind == "bone":
            note += "; bone/proportion slider"
        elif kind == "blendshape":
            note += "; shape slider"
        elif kind == "color":
            note += "; `vroid_set_color` / `vroid_set_param`"
        rows.append(f"| `{esc(p.get('key'))}` | {esc(kind)} | {esc(p.get('label', ''))} | {esc(note)} |")
    rows.append("")
    return rows


def category_table() -> list[str]:
    out = ["## 3. UI map and access modes", "",
           "This is the current section/category map. It is read with `vroid_sections` / `vroid_categories`; "
           "`category` is the stable name used by `vroid_enter`, `vroid_set_param` and preset filters. "
           "A group id is model-specific: get it at runtime with `vroid_list_groups` or `vroid_enter`.", "",
           "| Section | Category | Groups | Access mode |", "|---|---|---:|---|"]
    for sec in v._sections().get("sections", []):
        for c in sec.get("categories", []):
            cat = c["category"]
            if cat in ("Tops", "Bottoms", "Onepiece", "Shoes", "Socks", "InnerTop", "InnerBottom"):
                mode = "preset + color/texture layers (complex)"
            elif cat in ("AllHair", "BaseHair"):
                mode = "hair preset/procedural + material colors/textures"
            elif cat in ("FixedPreset",):
                mode = "preset choice"
            elif cat in ("MouthLine", "NoseLighting", "Cheek"):
                mode = "color/overlay"
            else:
                try:
                    params = v._enter(sec["section"], cat).get("params", [])
                    kinds = {p.get("kind") for p in params}
                    if not kinds:
                        mode = "preset/texture (no numeric params)"
                    elif kinds <= {"color"}:
                        mode = "color parameters only"
                    elif kinds <= {"bone", "blendshape"}:
                        mode = "sliders (bone/blendshape)"
                    else:
                        mode = "sliders + colors"
                except Exception:
                    mode = "read at runtime"
            out.append(f"| {esc(sec['section'])} | `{esc(cat)}` | {c.get('groups', 0)} | {esc(mode)} |")
    out += [
        "",
        "**Accessories** is absent from `vroid_sections` when the model has no accessory group. "
        "It is preset-driven: `Attachment/*` (Hat, AnimalEar, Tail, Glasses) and "
        "`Clothing/AccessoryArm` / `Clothing/AccessoryNeck`. Apply them with `vroid_apply_preset` or "
        "`vroid_apply_custom`, remove them with `vroid_remove_item`, then inspect `vroid_list_groups` "
        "if a layer edit is needed.",
        "",
        "`vroid_enter` is data-level: it does not switch VRoid's visible tab. Use it to read the "
        "group and its parameters, then write with `vroid_set_param`. The visible VRoid tab is only a UI; "
        "the section/category names below are the API names.",
        "",
    ]
    return out


def hair_tools_section() -> list[str]:
    return [
        "### Hair controls beyond group parameters",
        "",
        "The hairstyle section has two levels: preset sub-slots and procedural/brush groups. "
        "The commands below replace what the VRoid hair tabs expose.",
        "",
        "| Need | Tool / keys |",
        "|---|---|",
        "| Replace bangs, back, sideburns, ahoge, tied or whole hair | `vroid_list_presets(filter='Hair')`, `vroid_apply_preset(id=...)` |",
        "| Read procedural/brush groups | `vroid_list_hair_groups` |",
        "| Procedural length / strand count | `vroid_set_procedural_hair(transferable=..., group=..., length=..., hair_count=...)` |",
        "| Lengthen/shorten drawn strands | `vroid_scale_brush_hair(transferable=..., group=..., factor=...)` |",
        "| Duplicate drawn strands | `vroid_clone_brush_hair(transferable=..., group=..., dx,dy,dz)` |",
        "| Hair material colors | `vroid_list_hair_materials`, `vroid_set_hair_color(material=..., key=..., r,g,b)` |",
        "| Make a preset texture editable | `vroid_begin_hair_edit(material=...)`, then `vroid_list_layers` / `vroid_recolor_layer` |",
        "",
        "Hair colors are not in `vroid_get_params`. Preset hair tint is often the `base:<id>` key; "
        "if the hairstyle paints its color into the texture, recolor the layer in `colorize` mode instead. "
        "`Hair/Ahoge`, `Hair/Front`, `Hair/Back`, `Hair/Sideburns`, `Hair/Tied` and `Hair/Hanege` "
        "are preset sub-slots, not numeric groups.",
        "",
    ]


def outfit_tools_section() -> list[str]:
    return [
        "### Outfit controls and simple/complex access",
        "",
        "Clothes have **no numeric slider group** in VRoid. The VRoid `Outfit` tab is a set of preset slots; "
        "the Edit button opens textures. This is the main simple/complex distinction:",
        "",
        "| Access | Use | Tools |",
        "|---|---|---|",
        "| Simple preset | change the garment / shoes / socks | `vroid_list_presets(filter='Tops'|'Bottoms'|'Onepiece'|'Shoes'|'Socks')`, `vroid_apply_preset`, `vroid_apply_custom`, `vroid_remove_item` |",
        "| Simple color | change a preset's exposed color slots | `vroid_clothing_colors(group=...)`, `vroid_set_color(group=..., key=..., r,g,b)` |",
        "| Complex texture | recolor a layer, export/import a PNG | `vroid_begin_clothing_edit(group=...)`, `vroid_list_layers`, `vroid_recolor_layer`, `vroid_export_layer`, `vroid_import_layer` |",
        "",
        "`Onepiece` replaces Tops and Bottoms; `ClothingSet` can replace the whole outfit. After any whole-set apply, "
        "call `vroid_list_groups` because the number and ids of clothing groups can change. "
        "`InnerTop` / `InnerBottom` are separate layers, not underwear color sliders.",
        "",
    ]


def accessories_section() -> list[str]:
    return [
        "## Accessories parameters",
        "",
        "A head/body accessory is a preset in a slot, not a numeric group. There is no dedicated "
        "`vroid_set_*` parameter group for a hat, glasses, ears or tail. The workflow is:",
        "",
        "1. `vroid_list_presets(filter='Attachment')` or `filter='Accessory'`, then `vroid_apply_preset`.",
        "2. For a user item: `vroid_apply_custom(key=...|file=...)`.",
        "3. `vroid_list_groups` to see the resulting group. If the item exposes layers, use "
        "`vroid_list_layers` and the layer tools; otherwise it is preset-only.",
        "4. `vroid_remove_item(group=...)` to remove it; a short slot name removes every group of that type.",
        "",
        "| Preset category | Slot | Access |",
        "|---|---|---|",
        "| `Attachment/BaseballCap`, `SilkHat`, `StrawHat`, `WitchHat`, `WorkCap` | `Hat` | preset |",
        "| `Attachment/CatEar`, `RabbitEar` | `AnimalEar` | preset |",
        "| `Attachment/CatTail`, `FoxTail`, `RabbitTail` | `Tail` | preset |",
        "| `Attachment/GlassesHi`, `GlassesLow` | `Glasses` | preset |",
        "| `Clothing/AccessoryArm` | `ArmAccessory` | preset, optional texture layers |",
        "| `Clothing/AccessoryNeck` | `NeckAccessory` | preset, optional texture layers |",
        "",
        "The current model's `vroid_sections` has no Accessories group because it has no accessory applied. "
        "This is expected; the preset categories above are still available.",
        "",
    ]


def section_parameter_sections() -> list[str]:
    out = []
    sections = v._sections().get("sections", [])
    for sec in sections:
        section = sec["section"]
        if section == "Look":
            out += accessories_section()
        out += [f"## {section} parameters", "",
                SECTION_ACCESS.get(section, ""), "",
                "Each category below is addressed with `vroid_enter(section, category)`. "
                "The returned `params` are the keys accepted by `vroid_set_param` (or by "
                "`vroid_set_bone` / `vroid_set_blendshape` / `vroid_set_color`).", ""]
        for c in sec.get("categories", []):
            cat = c["category"]
            out += [f"### {section} / {cat} — {c.get('label', cat)}", ""]
            try:
                d = v._enter(section, cat)
                params = d.get("params", [])
                out += param_table(params)
            except Exception as exc:  # pragma: no cover - diagnostic path
                out.append(f"_Could not read this category in the current model: {exc}_")
                out.append("")
        if section == "Hairstyle":
            out += hair_tools_section()
        if section == "Outfit":
            out += outfit_tools_section()
    return out


def preset_section() -> list[str]:
    groups = collections.defaultdict(list)
    try:
        entries = pc.load().get("presets", {}).values()
    except Exception:
        entries = []
    for e in entries:
        cat = e.get("category") or "?"
        slot = e.get("slot") or "?"
        groups[cat].append(slot)

    def section_for(cat: str) -> str:
        if cat.startswith("Custom/"):
            name = cat.split("/", 1)[1]
            if name in ("ArmAccessory", "NeckAccessory"):
                return "Accessories"
            if name in ("Tops", "Bottoms", "Onepiece", "Shoes", "Socks", "InnerTop", "InnerBottom"):
                return "Outfit"
            if name in ("AllHair", "BaseHair", "HairFront"):
                return "Hairstyle"
            if name in ("FacePaint", "Lip", "Cheek", "MouthLine", "NoseLighting"):
                return "Look"
            if name in ("BodySkin",):
                return "Body"
            if name in ("Iris", "Mouth", "Eyebrow", "Eyelash", "Eyeline", "EyeHighlight", "EyeWhite", "FaceSkin"):
                return "Face"
            return "Other"
        if cat.startswith("Attachment/") or "AccessoryArm" in cat or "AccessoryNeck" in cat:
            return "Accessories"
        if cat.startswith("Clothing/") or cat in ("VRoid/ClothingSet",):
            return "Outfit"
        if cat.startswith("Face/") or cat in ("Skin/Face", "VRoid/FaceSet", "VRoid/EyeSet", "VRoid/EyeballSet"):
            return "Face"
        if cat.startswith("Hair/") or cat in ("VRoid/HairSet",):
            return "Hairstyle"
        if cat.startswith("Skin/Body") or cat in ("VRoid/Body",):
            return "Body"
        if cat.startswith("Overlay/") or cat in ("VRoid/FixedPreset",):
            return "Look"
        return "Other"

    out = ["## 12. Preset categories and replacement slots", "",
           "A preset is a resource path, not a group id. Applying a preset replaces the item in its slot; "
           "whole-set presets such as `ClothingSet`, `HairSet` or `FaceSet` can replace several slots at once. "
           "Always verify the result with `vroid_list_groups` after a whole-set apply.", "",
           "| Section | Preset category | Slot(s) | What it replaces | Presets |", "|---|---|---|---|---:|"]
    for cat in sorted(groups):
        slots = sorted(set(groups[cat]))
        desc = SLOT_DESC.get(slots[0]) if len(slots) == 1 else ", ".join(SLOT_DESC.get(s, s) for s in slots)
        out.append(f"| {section_for(cat)} | `{esc(cat)}` | {esc(', '.join(slots))} | {esc(desc)} | {len(groups[cat])} |")
    out += ["", "Use `vroid_list_presets(filter=...)` to search by category or resource path, "
            "`vroid_apply_preset(id=...)` to apply one, and `vroid_apply_custom(key=...|file=...)` for custom items. "
            "Presets that are not owned are hidden unless `include_locked=true` is passed.", ""]
    return out


def physical_section() -> list[str]:
    return [
        "## 10. Physical parameters, iris, ears, teeth and mouth",
        "",
        "All slider values are **normalized 0..1**; the AI should not try to interpret them as centimetres. "
        "Use `vroid_measure` and `vroid_set_body_size` for height. Group ids are obtained with `vroid_list_groups` "
        "or `vroid_enter`; keys below are stable across N00 models.",
        "",
        "### Height, weight and silhouette",
        "",
        "| Key | Effect |",
        "|---|---|",
        "| `Level2WholeBody_FigureHeightFemale/Male/Neutral` | shrink the figure while preserving proportions |",
        "| `Level2WholeBody_FigureSlenderFemale/Male/Neutral` | make the figure taller and thinner |",
        "| `Level2WholeBody_WholeBodyScaleMag/Shrink` | global scale |",
        "| `Level2Waist_WaistScaleMag/Shrink` | waist width; `vroid_set_body_size` converts weight to this |",
        "| `Level2Breast_Bust*` | chest shape (bust up/down/open/close/scale) |",
        "",
        "`vroid_set_body_size(height_cm, weight_kg?, gender?)` runs a search on the silhouette slider "
        "and reports the actual height; the VRoid slider is limited to -1..1, so an extreme target can be "
        "reported as unreachable. Weight is not a VRoid slider: it is approximated as BMI and mapped to waist width.",
        "",
        "### Iris / eye size",
        "",
        "| Key | Effect |",
        "|---|---|",
        "| `Level3Iris_EyeIrisScaleXMag` / `Shrink` | iris width |",
        "| `Level3Iris_EyeIrisScaleYMag` / `Shrink` | iris height |",
        "| `Level2Eye_EyeSizeX` / `Shrink` | eye width |",
        "| `Level2Eye_EyeSizeY` / `Shrink` | eye height |",
        "| `Level3Iris_GazeUpward/Downward/Inside/Outside` | gaze direction |",
        "| `Level3Iris_MaterialColor` / `LeftOverlayColor` / `RightOverlayColor` | iris colors (RGBA) |",
        "",
        "### Ears",
        "",
        "| Key | Effect |",
        "|---|---|",
        "| `Level2Ear_EarScaleMag` / `Shrink` | ear size |",
        "| `Level2Ear_EarTipUp/Wide/Down` | ear tip direction |",
        "| `Level2Ear_EarStandUp` / `LieDown` | ear rotation |",
        "| `Level2Ear_EarRound` | roundness |",
        "| `Level2Ear_EarOff` | blendshape that removes/hides the ear mesh |",
        "",
        "### Teeth, lips and mouth",
        "",
        "| Key | Effect |",
        "|---|---|",
        "| `Level2Mouth_ToothFung1/2/3` (+ `Lower`, `Upper`) | fang/tooth shape |",
        "| `Level2Mouth_ToothShort` (+ `Lower`, `Upper`) | tooth length |",
        "| `Level2Mouth_ToothHide` (+ `Lower`, `Upper`) | hide teeth |",
        "| `Level2Mouth_LipsFlat` | flatten lips |",
        "| `Level2Mouth_LipsThick1Upper/Lower`, `LipsThick2Upper/Lower` | lip thickness |",
        "| `Level2Mouth_MouthUp/Down/Narrow/Wide/CornerUp/CornerDown` | mouth placement |",
        "",
        "### Facial expression preview (vowels and emotions)",
        "",
        "`vroid_face_preview` is a **display-only** expression preview for captures. It is not a saved model "
        "parameter and should not be used with `vroid_set_blendshape`.",
        "",
        "| Name suffix | Meaning |",
        "|---|---|",
        "| `MTH_A`, `MTH_I`, `MTH_U`, `MTH_E`, `MTH_O` | Japanese vowel mouth shapes |",
        "| `ALL_Neutral`, `ALL_Angry`, `ALL_Fun`, `ALL_Joy`, `ALL_Sorrow`, `ALL_Surprised` | full-face emotions |",
        "| `EYE_Close`, `EYE_Close_L`, `EYE_Close_R` | both eyes / left / right |",
        "| `EYE_Extra` | extra eye expression exposed by VRoid |",
        "",
        "The tool sets the weight of every Face blendshape whose name ends with `name`, 0..100 (default 100). "
        "Call it with no `name` to list names; add `filter` to narrow the list. Use an empty name and weight 0 "
        "to reset. This is for a screenshot, not for the persistent model. The available names are VRoid's "
        "Face renderer names; this is the complete set exposed by the current VRoid 2.16 build.",
        "",
    ]


def workflow_section() -> list[str]:
    return [
        "## 14. Normalized 0..1 and paired-slider rules",
        "",
        "`vroid_set_bone`, `vroid_set_blendshape` and the numeric branch of `vroid_set_param` use VRoid's "
        "normalized slider values, generally **0..1**. Values outside that range are not meaningful and may be "
        "clamped by VRoid. Colors are RGBA with components 0..1; `vroid_set_param` also accepts `#RRGGBB` or "
        "`r,g,b` for a color parameter.",
        "",
        "Many controls are two halves of one UI slider. Set one and the other half returns to zero:",
        "",
        "- `...Mag` / `...Shrink`",
        "- `...Long` / `...Short`",
        "- `...Wide` / `...Narrow`",
        "- `...Up` / `...Down`",
        "- `...Forward` / `...Backward`",
        "- `FigureHeight<Gender>` / `FigureSlender<Gender>`",
        "- `...Female` / `...Male`",
        "",
        "## 15. Workflows an agent can follow",
        "",
        "### Inspect before changing",
        "",
        """```text
vroid_status
vroid_sections
vroid_categories(section='Face')
vroid_list_groups
vroid_enter(section='Face', category='Iris')
vroid_get_params(group='<group id>')
```""",
        "",
        "### Change a face or body parameter",
        "",
        """```text
vroid_enter(section='Face', category='Mouth')
vroid_set_param(section='Face', category='Mouth', param='Level2Mouth_ToothShortUpper', value=0.4)
vroid_screenshot
```""",
        "",
        "### Simple color versus complex clothing edit",
        "",
        "Simple color (clothing color slots when the preset exposes them):",
        "",
        """```text
vroid_clothing_colors(group='<clothing group id>')
vroid_set_color(group='<group id>', key='<color key>', r=0.2, g=0.4, b=0.8)
```""",
        "",
        "Complex texture edit (the clothing/preset tab's Edit button):",
        "",
        """```text
vroid_begin_clothing_edit(group='<clothing group id>')
vroid_list_layers(group='<group id>')
vroid_recolor_layer(transferable='<transferable>', image='<image>', node='<node>', r=0.2, g=0.4, b=0.8, mode='multiply')
```""",
        "",
        "For a hair preset whose texture is not editable, call `vroid_begin_hair_edit(material=...)` first, "
        "then use the same layer tools. Hair colors are separate from hair textures: use "
        "`vroid_list_hair_materials` and `vroid_set_hair_color`.",
        "",
        "### Preset variants and batches",
        "",
        """```text
vroid_preset_cache_search(query='short pleated blue skirt', category='Clothing/Bottoms')
vroid_apply_preset(id='<preset resource path>')
vroid_list_groups
```""",
        "",
        "`vroid_batch` accepts up to 200 `{tool,args}` operations, runs them sequentially and returns a text summary "
        "plus at most 8 images / 16 MiB. It has no rollback, no nested batches and no `vroid_help` / `vroid_exit` "
        "inside a batch. Save before destructive sequences.",
        "",
        "### Expression capture",
        "",
        """```text
vroid_face_preview(filter='Fcl_')          # list names
vroid_face_preview(name='MTH_A', weight=80)
vroid_camera(action='angles', x=0, y=20)
vroid_screenshot(width=1200, height=1600)
vroid_face_preview(name='', weight=0)      # reset
```""",
        "",
        "## 16. Failure modes and recovery",
        "",
        "| Symptom | Meaning | Recovery |",
        "|---|---|---|",
        "| `VRoid Studio is not responding` | bridge/plugin not loaded or VRoid closed | start VRoid, wait for the first editor load, call `vroid_status` |",
        "| `VRoid Studio is open` during install | installer refuses to modify a running game | close VRoid, retry |",
        "| `model is dirty` / `unsaved changes` | lifecycle operation would discard work | `vroid_save` or `discard=true` (`vroid_main_menu`/`vroid_exit`) |",
        "| group id not accepted | ids change when a model/outfit changes | call `vroid_list_groups` again; never cache ids across models |",
        "| key not found | model type/slot does not expose it | `vroid_enter` / `vroid_get_params`; use a preset/texture path |",
        "| image path returned but no image | response exceeded 8 images/16 MiB | read the file path, or request images separately |",
        "| export option in `warnings` | VRoid refused the option | do not assume it was applied; inspect `settings` in the response |",
        "",
        "## 17. Source of truth and drift control",
        "",
        "- `tools/list` (MCP) is the machine source of truth for names, descriptions and JSON schemas.",
        "- `vroid_help` is the built-in narrative source of truth and works without VRoid.",
        "- This document adds the UI/parameter catalog and workflows; tool schemas are generated from the live registry.",
        "- Group ids are model-specific and must be read at runtime. Parameter keys and group types are stable for N00 models.",
        "- If a future VRoid update changes the available groups, regenerate this file with VRoid open:",
        "",
        """```text
python tools/gen_agent_reference_en.py
```""",
        "",
        f"_Generated {datetime.date.today().isoformat()} from VRoid MCP Bridge 0.12.0._",
        "",
    ]


def main() -> None:
    lines: list[str] = [
        "# VRoid MCP Bridge — Agent Reference (English)",
        "",
        "Version 0.12.0 · generated from the live MCP tool registry and a model-open N00 session.",
        "",
        "Audience: an AI agent using the **`vroid`** MCP server through DeepSeek Harness (or any MCP client). "
        "It assumes no access to the VRoid Studio or VRoid MCP source code. The server, plugin, Python runtime "
        "and client integration are already installed.",
        "",
        "## 1. What is available",
        "",
        "- **52 MCP tools** named `vroid_*`; names, arguments and JSON schemas are available from the client's `tools/list`.",
        "- **One open model at a time**. Edits are real VRoid edits, undoable with Ctrl+Z / `vroid_undo`.",
        "- **`vroid_help`** works without VRoid and supports `en`, `fr`, `ja`, `zh-CN`; topics: "
        "`overview`, `tools`, `lifecycle`, `export`, `framing`, `thumbnails`, `colors`, `outfit`, `sessions`, "
        "`errors`, `languages`, `batch`.",
        "- **Preset cache tools** can search without VRoid; `vroid_preset_cache_*` does not require an open model.",
        "- The HTTP bridge listens on `127.0.0.1:7811`; the MCP server runs over stdio.",
        "",
        "## 2. Start and lifecycle",
        "",
        "Always start with:",
        "",
        """```text
vroid_help(topic='overview')
vroid_status()
```""",
        "",
        "`vroid_status` returns: `plugin`, `unity`, `modelOpen`, `modelType`, `isEditing`, `canUndo`, `canRedo`, "
        "`ready`, `currentFile`, `dirty`, `canSave`.",
        "",
        "Rules:",
        "",
        "1. `vroid_create` / `vroid_open` are only valid at the model-select screen (no model open).",
        "2. A new model has no file: use `vroid_save(path=...)` before leaving it.",
        "3. `vroid_main_menu` refuses unsaved changes unless `discard=true`; `vroid_exit` does the same.",
        "4. Save before a destructive batch or an export sequence.",
        "5. Only one model is open; finish with the current one before opening another.",
        "",
    ]
    lines += category_table()
    lines += section_parameter_sections()
    lines += physical_section()
    lines += preset_section()
    lines += tool_section()
    lines += workflow_section()
    text = "\n".join(lines).rstrip() + "\n"
    # Keep headings readable even when a section is absent (Accessories) or a
    # generator function adds a section dynamically.
    text = re.sub(r"^(#{2,3}) \d+(?:\.\d+)?\.? ", r"\1 ", text, flags=re.M)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{OUT} ({len(text)} chars, {len(v.TOOLS)} tools)")


if __name__ == "__main__":
    main()
