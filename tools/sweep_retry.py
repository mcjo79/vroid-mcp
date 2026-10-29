"""Rejoue les outils dont l'argumentaire manquait, avec de vrais identifiants."""
import json
import os
import sys
import traceback

MCP = r"C:\Users\vroid\AppData\Local\VRoidMcp\mcp_server"
sys.path.insert(0, MCP)
os.chdir(MCP)
import vroid_mcp as m  # noqa: E402

out = {}


def run(name, args):
    try:
        val = m.run_tool(name, args)
        out[name] = {"status": "OK", "detail": json.dumps(val, ensure_ascii=False)[:300]}
    except Exception as exc:  # noqa: BLE001
        out[name] = {"status": "ERREUR", "detail": f"{type(exc).__name__}: {exc}"}
    print(f"{name:30} {out[name]['status']}", flush=True)


groups = m.call_bridge("/groups")
tops = next((g for g in groups if (g.get("type") or "").endswith(".Tops")), None)
secs = m.call_bridge("/sections")
presets = m.call_bridge("/presets")
if isinstance(presets, dict):
    presets = presets.get("presets") or presets.get("items") or []
mats = m.call_bridge("/hair_materials")
params = m.call_bridge("/params?group=" + (tops["id"] if tops else ""))

run("vroid_enter", {"section": "Body", "category": "Arm"})
run("vroid_set_param", {"section": "Body", "category": "Arm",
                        "param": "Level2Arm_ArmShort", "value": 0.15})

if presets:
    first = presets[0]
    key = first.get("key") or first.get("resource") or first.get("id")
    run("vroid_preset_thumbnail", {"key": key})
    run("vroid_apply_custom", {"key": key})

if mats:
    run("vroid_begin_hair_edit", {"material": mats[0]["material"]})

if tops:
    run("vroid_colorize", {"group": tops["id"], "r": 0.6, "g": 0.6, "b": 0.7})
    run("vroid_clothing_colors", {"group": tops["id"]})

out["_context"] = {
    "tops": tops["type"] if tops else None,
    "sections": [s["section"] for s in secs.get("sections", [])],
    "presets": len(presets),
    "hair_materials": len(mats),
    "params": len(params),
}
json.dump(out, open(r"C:\Users\vroid\sweep2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
