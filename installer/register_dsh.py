"""Déclare (ou retire) le connecteur VRoid dans DeepSeek Harness.

    python register_dsh.py <python.exe> <vroid_mcp.py> [--profile <nom>] [--remove]

Le harnais charge ses connecteurs via un patch Cordis : on insère une entrée
`@deepseek-ai/dsh-mcp-client` de transport stdio, qui lance le serveur MCP avec le
Python embarqué. Le bloc est encadré par des marqueurs pour être remplaçable et
retirable sans toucher au reste du fichier.

Sans --profile, tous les profils du harnais sont traités (web, desktop, ...) : chaque
dossier de ~/.dsh/profiles dont le package.json déclare un profil dsh.
Fichier cible : ~/.dsh/profiles/<profil>/cordis.patch.yml (sauvegarde .bak-vroidmcp).

Code de retour : 0 si tout va bien, 2 si DeepSeek Harness n'est pas installé, 1 en cas d'erreur.
"""
import argparse
import json
import os
import shutil
import sys

BEGIN = "# >>> vroid-mcp (genere par l'installeur) >>>"
END = "# <<< vroid-mcp <<<"
HEADER = ("# Your patch layer for this dsh profile, applied after every bundle layer:\n"
          "# a top-level YAML array of loader patch entries (id-targeted config\n"
          "# overrides, disables, and insert lists; `!!js` expressions allowed).\n")
# Délai par appel d'outil : un export VRM ou une génération de vignettes peut durer
# plusieurs minutes (le serveur accepte jusqu'à 15 min pour l'export).
TOOL_TIMEOUT_MS = 900000


def dsh_home():
    return os.environ.get("DSH_HOME") or os.path.join(os.path.expanduser("~"), ".dsh")


def profiles_dir():
    return os.path.join(dsh_home(), "profiles")


def patch_path(profile):
    return os.path.join(profiles_dir(), profile, "cordis.patch.yml")


def is_profile(name):
    """Un profil dsh : dossier dont le package.json contient dsh.profile."""
    pkg = os.path.join(profiles_dir(), name, "package.json")
    try:
        with open(pkg, encoding="utf-8") as fh:
            return "profile" in (json.load(fh).get("dsh") or {})
    except (OSError, ValueError, AttributeError):
        return False


def all_profiles():
    root = profiles_dir()
    if not os.path.isdir(root):
        return []
    return sorted(n for n in os.listdir(root) if n != "node_modules" and is_profile(n))


def yaml_str(value):
    """Chaîne YAML entre guillemets doubles, échappée."""
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(python, server):
    return "\n".join([
        BEGIN,
        "- insert:",
        "    - id: mcp-vroid",
        '      name: "@deepseek-ai/dsh-mcp-client"',
        "      config:",
        "        transport: stdio",
        "        serverName: vroid",
        "        command: " + yaml_str(python),
        "        args:",
        '          - "-X"',
        '          - "utf8"',
        '          - "-E"',
        '          - "-s"',
        "          - " + yaml_str(server),
        f"        toolCallTimeoutMs: {TOOL_TIMEOUT_MS}",
        "        failOnStartupError: false",
        END,
    ])


def strip_block(text):
    """Retire le bloc existant, s'il y en a un."""
    out = []
    inside = False
    for line in text.splitlines():
        if line.strip() == BEGIN:
            inside = True
            continue
        if line.strip() == END:
            inside = False
            continue
        if not inside:
            out.append(line)
    # évite d'accumuler des lignes vides en fin de fichier
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def update(profile, python, server, remove):
    path = patch_path(profile)
    exists = os.path.exists(path)
    if not exists and remove:
        return 0
    text = ""
    if exists:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

    new = strip_block(text)
    if not remove:
        block = render(python, server)
        base = new if new.strip() else HEADER.rstrip("\n")
        new = base + "\n\n" + block + "\n"
    else:
        new += "\n"

    if new == text:
        print(f"  {path} : déjà à jour")
        return 0

    if exists:
        shutil.copy2(path, path + ".bak-vroidmcp")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new)
    try:
        os.replace(tmp, path)
    except PermissionError:
        # L'app DeepSeek Harness ouverte tient le fichier de son profil : Windows refuse de le
        # remplacer, mais accepte en général une réécriture sur place.
        os.remove(tmp)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
        except PermissionError:
            print(f"  {path} : verrouillé par DeepSeek Harness. Fermez-le puis relancez l'installation.")
            return 1
    print(f"  {path} : connecteur vroid {'retiré' if remove else 'déclaré'}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("python")
    ap.add_argument("server")
    ap.add_argument("--profile", help="un seul profil (défaut : tous)")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    if args.profile:
        if not os.path.isdir(os.path.join(profiles_dir(), args.profile)):
            print(f"  profil {args.profile} absent de {profiles_dir()}")
            return 2
        profiles = [args.profile]
    else:
        profiles = all_profiles()
        if not profiles:
            print(f"  {profiles_dir()} : aucun profil (DeepSeek Harness n'est pas installé)")
            return 2

    rc = 0
    for profile in profiles:
        try:
            if update(profile, args.python, args.server, args.remove):
                rc = 1
        except OSError as e:
            print(f"  {patch_path(profile)} : erreur {e}")
            rc = 1
    if not args.remove:
        print("  Redémarrez DeepSeek Harness pour charger les outils vroid_* (mcp__vroid__...).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
