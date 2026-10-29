"""Construit le paquet de release dist/VRoidMcp-v<version>.zip.

    python installer/build_release.py <version> <chemin de VRoidMcpBridge.dll compilé>

Contenu : Installer.cmd (CLI), Installer-GUI.cmd/.ps1 (graphique), install.ps1,
register_mcp.py, register_dsh.py, merge_cache.py, plugin/, mcp_server/ (sans cache),
tools/, docs/, config/ (defaults de cadrage), **python/ (CPython Windows embarqué)**, README*.md, LICENSE,
THIRD_PARTY_NOTICES.md.

Le Python embarqué vient de python-build-standalone (Astral) : archive Windows x86_64 précompilée,
téléchargée depuis Linux et vérifiée par SHA-256 — aucune compilation croisée. L'archive est mise en
cache dans installer/vendor/ (non versionné) et re-téléchargée si absente.

BepInEx n'est pas inclus : l'installeur le télécharge et vérifie son empreinte.
Les données du cache des presets ne sont jamais incluses.
"""
import hashlib
import os
import sys
import tarfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"__pycache__", "preset_cache", "bin", "obj"}

# --- Python embarqué (python-build-standalone) ---------------------------------
PBS_TAG = "20261026"
PBS_VERSION = "3.12.16"
PBS_NAME = f"cpython-{PBS_VERSION}+{PBS_TAG}-x86_64-pc-windows-msvc-install_only_stripped.tar.gz"
PBS_URL = (
    f"https://github.com/astral-sh/python-build-standalone/releases/download/{PBS_TAG}/"
    f"cpython-{PBS_VERSION}%2B{PBS_TAG}-x86_64-pc-windows-msvc-install_only_stripped.tar.gz"
)
PBS_SHA256 = "1f2ab53880fc67ea323398c6388e05af28addc99a8e389209f08a51fdff4b149"
VENDOR = os.path.join(ROOT, "installer", "vendor")

# Retiré du paquet : inutile pour un serveur MCP headless (tkinter/tcl, en-têtes,
# idle, ensurepip, cache de bytecode). ~60 Mo extraits -> ~35 Mo, ~10 Mo compressés.
SKIP_PYTHON_PREFIXES = (
    "__pycache__/",
    "Lib/test/",
    "Lib/tkinter/",
    "Lib/turtledemo/",
    "Lib/idlelib/",
    "Lib/ensurepip/",
    "include/",
    "libs/",
    "tcl/",
)
SKIP_PYTHON_FILES = ("_tkinter.pyd", "tcl86t.dll", "tk86t.dll", "tcl90t.dll", "tk90t.dll")


def add_tree(z, src, arc):
    for dirpath, dirnames, files in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".pyc", ".tmp", ".lock")):
                continue
            p = os.path.join(dirpath, f)
            z.write(p, os.path.join(arc, os.path.relpath(p, src)))


def python_archive():
    """Chemin de l'archive Python, téléchargée et vérifiée si nécessaire."""
    os.makedirs(VENDOR, exist_ok=True)
    path = os.path.join(VENDOR, PBS_NAME)
    if not os.path.exists(path):
        print(f"téléchargement du Python embarqué {PBS_VERSION} ({PBS_TAG})...")
        tmp = path + ".part"
        with urllib.request.urlopen(PBS_URL, timeout=120) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        os.replace(tmp, path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != PBS_SHA256:
        raise SystemExit(f"empreinte du Python embarqué invalide : {h.hexdigest()}")
    return path


def add_python(z, arc):
    """Ajoute l'arbre python/ (python.exe, DLLs, Lib/...) au paquet."""
    with tarfile.open(python_archive(), "r:gz") as t:
        for m in t:
            if not m.isfile() or not m.name.startswith("python/"):
                continue
            rel = m.name[len("python/"):]
            if not rel or rel.startswith(SKIP_PYTHON_PREFIXES):
                continue
            base = os.path.basename(rel)
            if base in SKIP_PYTHON_FILES or base.startswith("_test"):
                continue
            z.writestr(os.path.join(arc, "python", rel), t.extractfile(m).read())


def main(version, dll):
    out = os.path.join(ROOT, "dist", f"VRoidMcp-v{version}.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    base = f"VRoidMcp-v{version}"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in ("Installer.cmd", "Installer-GUI.cmd", "Installer-GUI.ps1", "install.ps1",
                  "register_mcp.py", "register_dsh.py", "merge_cache.py"):
            z.write(os.path.join(ROOT, "installer", f), f"{base}/{f}")
        z.write(dll, f"{base}/plugin/VRoidMcpBridge.dll")
        for d in ("mcp_server", "tools", "docs", "config"):
            add_tree(z, os.path.join(ROOT, d), f"{base}/{d}")
        for f in ("README.md", "README-fr.md", "README-ja.md", "README-zh.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
            z.write(os.path.join(ROOT, f), f"{base}/{f}")
        add_python(z, base)
    names = zipfile.ZipFile(out).namelist()
    assert not any("preset_cache/" in n for n in names), "données de cache dans le paquet"
    assert f"{base}/python/python.exe" in names, "Python embarqué absent du paquet"
    print(out, len(names), "fichiers", os.path.getsize(out) // 1024, "Ko")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
