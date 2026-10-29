"""Balayage des outils MCP contre l'instance VRoid en cours.

À exécuter DANS l'invité, avec le Python embarqué. Chaque outil est appelé avec un
argumentaire minimal mais valide, dans un thread avec délai maximal : un outil qui
bloque le thread principal de VRoid est signalé comme HANG au lieu de figer le balayage.

Sortie : sweep.json à côté du script.
"""
import json
import os
import sys
import threading
import time
import traceback

MCP = r"C:\Users\vroid\AppData\Local\VRoidMcp\mcp_server"
sys.path.insert(0, MCP)
os.chdir(MCP)

import vroid_mcp as m  # noqa: E402

TIMEOUT = 45
TIMEOUTS = {"vroid_export_vrm": 180, "vroid_screenshot": 90, "vroid_preset_cache_sync": 120}
SKIP = {
    "vroid_create": "destructif et connu pour figer (déjà testé)",
    "vroid_open": "destructif (change de modèle)",
    "vroid_main_menu": "destructif (ferme le modèle)",
    "vroid_exit": "destructif (quitte VRoid)",
    "vroid_remove_item": "destructif (retire un élément du modèle)",
    "vroid_preset_cache_build": "long scan complet, hors périmètre",
    "vroid_preset_cache_annotate": "écrit dans le cache partagé",
}


def call(name, args):
    box = {}

    def run():
        try:
            box["value"] = m.run_tool(name, args)
        except Exception as exc:  # noqa: BLE001
            box["error"] = f"{type(exc).__name__}: {exc}"
            box["trace"] = traceback.format_exc(limit=2)

    t = threading.Thread(target=run, daemon=True)
    start = time.time()
    t.start()
    limit = TIMEOUTS.get(name, TIMEOUT)
    t.join(limit)
    elapsed = round(time.time() - start, 1)
    if t.is_alive():
        return {"status": "HANG", "seconds": elapsed, "detail": f"> {limit}s, thread bloqué"}
    if "error" in box:
        return {"status": "ERREUR", "seconds": elapsed, "detail": box["error"]}
    val = box.get("value")
    txt = json.dumps(val, ensure_ascii=False)
    return {"status": "OK", "seconds": elapsed, "detail": txt[:220]}


def first(seq, **match):
    for item in seq:
        if all(item.get(k) == v for k, v in match.items()):
            return item
    return None


def main():
    ctx = {}
    try:
        ctx["groups"] = m.call_bridge("/groups")
    except Exception as exc:  # noqa: BLE001
        print("impossible de lire /groups:", exc)
        ctx["groups"] = []
    groups = ctx["groups"]
    ctx["arm"] = first(groups, type="TransferableGroupType.N00.Level1.Arm")
    ctx["face"] = first(groups, type="TransferableGroupType.N00.Level1.Face")
    ctx["body"] = first(groups, type="TransferableGroupType.N00.Level1.Body")
    clothing = [g for g in groups if "Clothing" in (g.get("type") or "") or "Outfit" in (g.get("type") or "")]
    hair = [g for g in groups if "Hair" in (g.get("type") or "")]
    ctx["clothing"] = clothing[0] if clothing else None
    ctx["hair"] = hair[0] if hair else None
    try:
        pres = m.call_bridge("/presets")
        if isinstance(pres, dict):
            pres = pres.get("presets") or pres.get("items") or pres.get("all") or []
        ctx["presets"] = pres if isinstance(pres, list) else []
    except Exception:  # noqa: BLE001
        ctx["presets"] = []
    try:
        ctx["params"] = m.call_bridge("/params?group=" + (ctx["arm"] or {}).get("id", "")) if ctx["arm"] else []
    except Exception:  # noqa: BLE001
        ctx["params"] = []

    gid = lambda k: (ctx.get(k) or {}).get("id")  # noqa: E731
    bone = next((p for p in ctx["params"] if p.get("kind") == "bone"), None)
    preset = (ctx["presets"] or [None])[0]

    ARGS = {
        "vroid_help": {},
        "vroid_batch": {"operations": [{"tool": "vroid_status", "args": {}}]},
        "vroid_status": {},
        "vroid_save": {"path": r"C:\Users\vroid\sweep_test.vroid"},
        "vroid_export_vrm": {"path": r"C:\Users\vroid\sweep_test.vrm"},
        "vroid_export_vrm_options": {},
        "vroid_framing_get": {},
        "vroid_framing_set": {"category": "Face", "zoom": 1.0},
        "vroid_framing_reset": {},
        "vroid_list_groups": {},
        "vroid_get_params": {"group": gid("arm")},
        "vroid_sections": {},
        "vroid_categories": {},
        "vroid_enter": {"group": gid("clothing")},
        "vroid_set_param": ({"group": gid("arm"), "key": bone["key"], "value": 0.0} if bone else {}),
        "vroid_set_blendshape": ({"group": gid("face"), "key": "Fcl_EYE_Close", "value": 0.3} if gid("face") else {}),
        "vroid_set_bone": ({"group": gid("arm"), "key": bone["key"], "value": 0.0} if bone else {}),
        "vroid_set_color": ({"group": gid("clothing"), "key": "BaseColor", "r": 0.5, "g": 0.5, "b": 0.5} if gid("clothing") else {}),
        "vroid_colorize": ({"group": gid("clothing"), "r": 0.6, "g": 0.6, "b": 0.6} if gid("clothing") else {}),
        "vroid_list_layers": {"group": gid("clothing")},
        "vroid_recolor_layer": {},
        "vroid_export_layer": {},
        "vroid_import_layer": {},
        "vroid_list_hair_materials": {},
        "vroid_set_hair_color": {},
        "vroid_list_hair_groups": {},
        "vroid_set_procedural_hair": {},
        "vroid_scale_brush_hair": {},
        "vroid_clone_brush_hair": {},
        "vroid_undo": {},
        "vroid_redo": {},
        "vroid_screenshot": {},
        "vroid_list_presets": {},
        "vroid_apply_preset": ({"id": preset.get("id")} if preset and preset.get("id") else {}),
        "vroid_clothing_colors": {"group": gid("clothing")},
        "vroid_begin_clothing_edit": {"group": gid("clothing")},
        "vroid_measure": {},
        "vroid_set_body_size": {"height_cm": 160},
        "vroid_preset_cache_search": {},
        "vroid_preset_thumbnail": ({"id": preset.get("id")} if preset and preset.get("id") else {}),
        "vroid_preset_cache_sync": {"limit": 5},
        "vroid_camera": {"action": "reset"},
        "vroid_apply_custom": {},
        "vroid_face_preview": {"group": gid("face")},
        "vroid_begin_hair_edit": {"group": gid("hair")},
    }

    results = {}
    for tool in m.TOOLS:
        name = tool["name"]
        if name in SKIP:
            results[name] = {"status": "IGNORÉ", "detail": SKIP[name]}
            continue
        args = ARGS.get(name)
        if args is None:
            results[name] = {"status": "IGNORÉ", "detail": "pas d'argumentaire défini"}
            continue
        results[name] = call(name, args)
        print(f"{name:32} {results[name]['status']:8} {results[name].get('seconds','')}", flush=True)
        if results[name]["status"] == "HANG":
            # si le pont ne répond plus, inutile de continuer à l'aveugle
            alive = True
            try:
                m.call_bridge("/status", timeout=5)
            except Exception:  # noqa: BLE001
                alive = False
            if not alive:
                for rest in m.TOOLS[m.TOOLS.index(tool) + 1:]:
                    if rest["name"] not in results:
                        results[rest["name"]] = {"status": "NON TESTÉ",
                                                 "detail": "pont figé après un HANG"}
                break

    with open(r"C:\Users\vroid\sweep.json", "w", encoding="utf-8") as fh:
        json.dump({"unity": m.call_bridge("/status"), "results": results}, fh,
                  ensure_ascii=False, indent=1)
    print("rapport écrit")


if __name__ == "__main__":
    main()
