"""Restaure le cache des presets après l'incident (scan à vide qui l'avait vidé).

Ouvre un modèle si nécessaire, puis lance la synchro du catalogue.
"""
import json
import os
import sys

MCP = r"C:\Users\vroid\AppData\Local\VRoidMcp\mcp_server"
sys.path.insert(0, MCP)
os.chdir(MCP)
import vroid_mcp as m  # noqa: E402

st = m.call_bridge("/status")
print("avant :", json.dumps({k: st.get(k) for k in ("modelOpen", "ready")}, ensure_ascii=False), flush=True)

if not st.get("modelOpen"):
    r = m.call_bridge("/create", body={"gender": "female"}, timeout=180)
    print("create :", json.dumps(r, ensure_ascii=False)[:120], flush=True)
    st = m.call_bridge("/status")
    print("apres create :", json.dumps({k: st.get(k) for k in ("modelOpen", "ready")}, ensure_ascii=False), flush=True)

res = m.run_tool("vroid_preset_cache_sync", {})
print("sync :", json.dumps(res, ensure_ascii=False)[:400], flush=True)
