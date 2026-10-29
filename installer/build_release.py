"""Construit la release : dist/VRoidMcp-Setup-v<version>.exe (installeur NSIS) et dist/VRoidMcp-v<version>.zip.

    python installer/build_release.py <version> <chemin de VRoidMcpBridge.dll compilé> [--no-setup]

L'installeur NSIS (installer/nsis/VRoidMcp.nsi) embarque le contenu du zip et exécute install.ps1
sans console. NSIS portable est téléchargé dans installer/vendor/ et vérifié par SHA-256
(ou variable MAKENSIS / makensis dans le PATH).

Contenu du zip : install.ps1, agent/ (skill vroid-studio pour Claude Code et DeepSeek Harness),
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
import shutil
import subprocess
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
WHEEL_DIR = os.path.join(VENDOR, "wheels")

# Roues Windows CPython 3.12 pour les fonctions image (vignettes, labels).
# Elles sont extraites dans python/Lib/site-packages : aucun pip/réseau à l'installation.
IMAGE_WHEELS = (
    (
        "numpy-2.5.4-cp312-cp312-win_amd64.whl",
        "a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a",
        "https://files.pythonhosted.org/packages/12/33/fefe62073dc8acfd0f2b9ed7c003af2f50aa61555e113e6db02b8f79f145/numpy-2.5.4-cp312-cp312-win_amd64.whl",
    ),
    (
        "pillow-13.0.0-cp312-cp312-win_amd64.whl",
        "ff3fe9eb621fbb9db4c4be33ab946f6bac5f98ab50ca8d3260503653656c961b",
        "https://files.pythonhosted.org/packages/ff/cd/73a79ecdc822076002eb24b5e1e4a530b0bb5310fcb6d239abbec877110b/pillow-13.0.0-cp312-cp312-win_amd64.whl",
    ),
)

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


def wheel_file(name, expected, url):
    """Télécharge et vérifie une roue Windows, puis retourne son chemin."""
    os.makedirs(WHEEL_DIR, exist_ok=True)
    path = os.path.join(WHEEL_DIR, name)
    if not os.path.exists(path):
        print(f"téléchargement de {name}...")
        tmp = path + ".part"
        with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
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
    if h.hexdigest() != expected:
        raise SystemExit(f"empreinte invalide pour {name} : {h.hexdigest()}")
    return path


def add_image_wheels(z, arc):
    """Extrait numpy/Pillow dans python/Lib/site-packages (offline à l'installation)."""
    for name, expected, url in IMAGE_WHEELS:
        path = wheel_file(name, expected, url)
        with zipfile.ZipFile(path) as w:
            for member in w.namelist():
                if member.endswith("/") or member.endswith(".pyc") or "__pycache__" in member:
                    continue
                rel = member
                if ".data/purelib/" in rel:
                    rel = rel.split(".data/purelib/", 1)[1]
                elif ".data/platlib/" in rel:
                    rel = rel.split(".data/platlib/", 1)[1]
                elif ".data/" in rel:
                    continue
                z.writestr(os.path.join(arc, "python", "Lib", "site-packages", rel), w.read(member))


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
        for f in ("install.ps1", "register_mcp.py", "register_dsh.py", "merge_cache.py"):
            z.write(os.path.join(ROOT, "installer", f), f"{base}/{f}")
        z.write(dll, f"{base}/plugin/VRoidMcpBridge.dll")
        for d in ("mcp_server", "tools", "docs", "config", "agent"):
            add_tree(z, os.path.join(ROOT, d), f"{base}/{d}")
        for f in ("README.md", "README-fr.md", "README-ja.md", "README-zh.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
            z.write(os.path.join(ROOT, f), f"{base}/{f}")
        add_python(z, base)
        add_image_wheels(z, base)
    names = zipfile.ZipFile(out).namelist()
    assert not any("preset_cache/" in n for n in names), "données de cache dans le paquet"
    assert f"{base}/python/python.exe" in names, "Python embarqué absent du paquet"
    assert f"{base}/agent/skills/vroid-studio/SKILL.md" in names, "skill vroid-studio absent du paquet"
    assert f"{base}/mcp_server/prompts.py" in names, "prompts MCP absents du paquet"
    assert f"{base}/python/Lib/site-packages/numpy/__init__.py" in names, "numpy absent du paquet"
    assert f"{base}/python/Lib/site-packages/PIL/__init__.py" in names, "Pillow absent du paquet"
    print(out, len(names), "fichiers", os.path.getsize(out) // 1024, "Ko")
    return out


# --- Installeur NSIS ----------------------------------------------------------
NSIS_VERSION = "3.11"
NSIS_URL = f"https://downloads.sourceforge.net/project/nsis/NSIS%203/{NSIS_VERSION}/nsis-{NSIS_VERSION}.zip"
NSIS_SHA256 = "c7d27f780ddb6cffb4730138cd1591e841f4b7edb155856901cdf5f214394fa1"


def makensis():
    """Chemin de makensis : MAKENSIS, PATH, sinon NSIS portable téléchargé dans installer/vendor."""
    if os.environ.get("MAKENSIS"):
        return os.environ["MAKENSIS"]
    found = shutil.which("makensis")
    if found:
        return found
    exe = os.path.join(VENDOR, "nsis", f"nsis-{NSIS_VERSION}", "makensis.exe")
    if not os.path.exists(exe):
        os.makedirs(VENDOR, exist_ok=True)
        archive = os.path.join(VENDOR, f"nsis-{NSIS_VERSION}.zip")
        if not os.path.exists(archive):
            print(f"téléchargement de NSIS {NSIS_VERSION}...")
            with urllib.request.urlopen(NSIS_URL, timeout=120) as r, open(archive + ".part", "wb") as f:
                shutil.copyfileobj(r, f)
            os.replace(archive + ".part", archive)
        with open(archive, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != NSIS_SHA256:
            raise SystemExit(f"empreinte NSIS invalide : {digest}")
        with zipfile.ZipFile(archive) as z:
            z.extractall(os.path.join(VENDOR, "nsis"))
    return exe


def build_setup(version, zip_path):
    """Extrait le zip dans out/nsis_payload puis compile installer/nsis/VRoidMcp.nsi."""
    payload_root = os.path.join(ROOT, "out", "nsis_payload")
    shutil.rmtree(payload_root, ignore_errors=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(payload_root)
    payload = os.path.join(payload_root, f"VRoidMcp-v{version}")
    dist = os.path.join(ROOT, "dist")
    nsi = os.path.join(ROOT, "installer", "nsis", "VRoidMcp.nsi")
    numeric = version.split("-")[0]
    # makensis (32 bits) projette son bloc compressé via des fichiers temporaires : un dossier dédié
    # évite les échecs "error creating mmap" quand %TEMP% est restreint.
    tmp = os.path.join(ROOT, "out", "nsis_tmp")
    os.makedirs(tmp, exist_ok=True)
    env = dict(os.environ, TMP=tmp, TEMP=tmp)
    subprocess.run([makensis(), "/V2", "/INPUTCHARSET", "UTF8", f"/DVERSION={numeric}",
                    f"/DPAYLOAD={payload}", f"/DOUTDIR={dist}", nsi], check=True, env=env)
    shutil.rmtree(tmp, ignore_errors=True)
    exe = os.path.join(dist, f"VRoidMcp-Setup-v{numeric}.exe")
    print(exe, os.path.getsize(exe) // 1024, "Ko")
    shutil.rmtree(payload_root, ignore_errors=True)
    return exe


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    zip_path = main(args[0], args[1])
    if "--no-setup" not in sys.argv:
        build_setup(args[0], zip_path)
