"""Construit le paquet de release dist/VRoidMcp-v<version>.zip.

    python installer/build_release.py <version> <chemin de VRoidMcpBridge.dll compilé>

Contenu : Installer.cmd, install.ps1, register_mcp.py, merge_cache.py, plugin/, mcp_server/ (sans cache),
tools/, docs/, config/ (defaults de cadrage), README.md, README-fr.md, README-ja.md, README-zh.md, LICENSE,
THIRD_PARTY_NOTICES.md. BepInEx n'est pas inclus : l'installeur le télécharge et vérifie son empreinte.
Les données du cache des presets ne sont jamais incluses.
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"__pycache__", "preset_cache", "bin", "obj"}


def add_tree(z, src, arc):
    for dirpath, dirnames, files in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".pyc", ".tmp", ".lock")):
                continue
            p = os.path.join(dirpath, f)
            z.write(p, os.path.join(arc, os.path.relpath(p, src)))


def main(version, dll):
    out = os.path.join(ROOT, "dist", f"VRoidMcp-v{version}.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    base = f"VRoidMcp-v{version}"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("Installer.cmd", "install.ps1", "register_mcp.py", "merge_cache.py"):
            z.write(os.path.join(ROOT, "installer", f), f"{base}/{f}")
        z.write(dll, f"{base}/plugin/VRoidMcpBridge.dll")
        for d in ("mcp_server", "tools", "docs", "config"):
            add_tree(z, os.path.join(ROOT, d), f"{base}/{d}")
        for f in ("README.md", "README-fr.md", "README-ja.md", "README-zh.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
            z.write(os.path.join(ROOT, f), f"{base}/{f}")
    names = zipfile.ZipFile(out).namelist()
    assert not any("preset_cache/" in n for n in names), "données de cache dans le paquet"
    print(out, len(names), "fichiers", os.path.getsize(out) // 1024, "Ko")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
