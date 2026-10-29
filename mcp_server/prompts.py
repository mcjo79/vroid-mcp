"""MCP prompts of the vroid server (prompts/list, prompts/get).

Claude Code shows them as /mcp__vroid__<name> commands, Claude Desktop as prompts to insert,
other clients in their own prompt picker. Each prompt is a short, ready-to-run brief: it tells
the assistant what to read first (vroid_status, MCP resources vroid://agent/...) and which
rules matter, so a session starts with the right context without loading the whole reference.
"""
import help_i18n

LANG_ARG = {"name": "lang", "description": "en (default), fr, ja, zh-CN", "required": False}

PROMPTS = [
    {
        "name": "help",
        "description": "VRoid Studio MCP manual (English, French, Japanese, Simplified Chinese)",
        "arguments": [
            {"name": "topic", "description": "overview, tools, lifecycle, export, framing, thumbnails, colors, "
                                             "outfit, sessions, errors, languages, batch", "required": False},
            LANG_ARG,
        ],
    },
    {
        "name": "start",
        "description": "Start a VRoid working session: check VRoid, the open model and unsaved changes, "
                       "then summarize what can be done.",
        "arguments": [
            {"name": "goal", "description": "what you want to do today (optional)", "required": False},
        ],
    },
    {
        "name": "character",
        "description": "Create or restyle a VRoid character from a description (hair, face, body, outfit, colors).",
        "arguments": [
            {"name": "description", "description": "the character to make, in any language", "required": True},
            {"name": "save_as", "description": "absolute path of the .vroid to save (optional)", "required": False},
            {"name": "base", "description": "new (create a model, default) or current (restyle the open one)",
             "required": False},
        ],
    },
    {
        "name": "export_vrm",
        "description": "Export the open model as VRM with a preset: full quality, balanced or light.",
        "arguments": [
            {"name": "path", "description": "absolute path of the .vrm to write", "required": True},
            {"name": "preset", "description": "full (default), balanced or light", "required": False},
            {"name": "version", "description": "1 (VRM 1.0, default) or 0 (VRM 0.x)", "required": False},
        ],
    },
]

COMMON = (
    "Use the `vroid` MCP tools (vroid_*). Reply in the user's language; tool names and arguments stay English. "
    "Rules: one model at a time; save before vroid_create, vroid_open or vroid_main_menu; never overwrite the "
    "user's file or discard changes without asking; group ids are per model (re-read them with "
    "vroid_list_groups); sliders are 0..1 and colors RGBA 0..1; one VRoid operation at a time; vroid_undo "
    "after a bad change. Read only the MCP resource section you need (vroid://agent/start, face, hairstyle, "
    "body, outfit, accessories, look, physical, presets, tools, workflows, troubleshooting) or vroid_help."
)

EXPORT_PRESETS = {
    "full": "no reduction: keep every option at its default (transparent meshes deleted, original textures)",
    "balanced": "hair=30 face=20 body=20 outfit=30 hair_bones=30 material_mode=3 (12 materials) "
                "atlas_resolution=0 (4096)",
    "light": "hair=60 face=40 body=40 outfit=60 hair_bones=60 material_mode=1 (2 materials) "
             "atlas_resolution=1 (2048)",
}


def _text(text):
    return {"messages": [{"role": "user", "content": {"type": "text", "text": text}}]}


def get(name, args, tools):
    """prompts/get payload for one prompt."""
    a = args or {}
    if name == "help":
        out = _text(help_i18n.help_text(a.get("topic", "overview"), a.get("lang", "en"), tools))
        out["description"] = "VRoid Studio MCP help"
        return out
    if name == "start":
        goal = (a.get("goal") or "").strip()
        out = _text(
            "Start a VRoid Studio working session.\n\n"
            "1. Call vroid_status and tell me in two lines: is VRoid reachable, which model is open, "
            "are there unsaved changes.\n"
            "2. If VRoid is unreachable, tell me to start VRoid Studio (the first launch after an install "
            "takes 1-2 extra minutes) and stop there.\n"
            "3. Read the MCP resource vroid://agent/start (or vroid_help topic=overview).\n"
            + ("4. Then propose a short plan for this goal and wait for my go-ahead: " + goal + "\n" if goal else
               "4. Then list in a few bullets what I can ask you to do (edit face/hair/body, presets, colors, "
               "textures, screenshots, VRM export) and wait for my request.\n")
            + "\n" + COMMON)
        out["description"] = "Start a VRoid working session"
        return out
    if name == "character":
        desc = (a.get("description") or "").strip()
        if not desc:
            raise ValueError("argument 'description' is required")
        base = (a.get("base") or "new").strip().lower()
        save_as = (a.get("save_as") or "").strip()
        steps = [
            "Make this VRoid character: " + desc,
            "",
            "1. vroid_status. If a model is open with unsaved changes, ask me before leaving it.",
            ("2. Work on the open model." if base == "current" else
             "2. Create a new model (vroid_create gender=female|male, chosen from the description; go back "
             "to the model menu first if needed, after saving)."),
            "3. Read vroid://agent/presets, then for each part (hair, outfit, shoes, accessories) search "
            "vroid_preset_cache_search with words from the description and apply the best match. "
            "Check vroid_list_groups after a one-piece or *Set preset.",
            "4. Adjust face and body with vroid_set_param (read vroid://agent/face and vroid://agent/body "
            "for the parameter names), then colors (hair: vroid_set_hair_color; clothes: "
            "vroid_clothing_colors + vroid_set_color).",
            "5. After each part, vroid_screenshot and show me the result; ask before big changes of direction.",
            ("6. Save with vroid_save path=" + save_as + "." if save_as else
             "6. Ask me where to save it (vroid_save path=...); never overwrite an existing file without asking."),
            "",
            COMMON,
        ]
        out = _text("\n".join(steps))
        out["description"] = "Create a VRoid character"
        return out
    if name == "export_vrm":
        path = (a.get("path") or "").strip()
        if not path:
            raise ValueError("argument 'path' is required")
        preset = (a.get("preset") or "full").strip().lower()
        if preset not in EXPORT_PRESETS:
            raise ValueError("preset must be full, balanced or light")
        version = "0" if str(a.get("version", "1")).strip() in ("0", "0.x", "vrm0") else "1"
        out = _text(
            f"Export the open VRoid model to {path} as VRM {'0.x' if version == '0' else '1.0'}.\n\n"
            "1. vroid_status: a model must be open and ready; tell me if not.\n"
            "2. Reset any facial expression preview first (vroid_face_preview name='' weight=0).\n"
            f"3. Call vroid_export_vrm path={path} version={version} with the '{preset}' preset: "
            f"{EXPORT_PRESETS[preset]}.\n"
            "4. Report the file size, the time taken and any 'warnings' (options VRoid refused). "
            "The .vroid file is not modified.\n\n" + COMMON)
        out["description"] = "Export the open model as VRM"
        return out
    raise KeyError(name)
