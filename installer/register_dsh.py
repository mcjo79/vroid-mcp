"""Déclare (ou retire) le connecteur VRoid dans DeepSeek Harness.

    python register_dsh.py <python.exe> <vroid_mcp.py> [--profile web] [--remove]

Le harnais charge ses connecteurs via un patch Cordis : on insère une entrée
`@deepseek-ai/dsh-mcp-client` de transport stdio, qui lance le serveur MCP avec le
Python embarqué. Le bloc est encadré par des marqueurs pour être remplaçable et
retirable sans toucher au reste du fichier.

Fichier cible : ~/.dsh/profiles/<profil>/cordis.patch.yml (sauvegarde .bak-vroidmcp).
"""
import argparse
import os
import shutil
import sys

BEGIN = "# >>> vroid-mcp (genere par l'installeur) >>>"
END = "# <<< vroid-mcp <<<"


def dsh_home():
    return os.environ.get("DSH_HOME") or os.path.join(os.path.expanduser("~"), ".dsh")


def patch_path(profile):
    return os.path.join(dsh_home(), "profiles", profile, "cordis.patch.yml")


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
        "        toolCallTimeoutMs: 300000",
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("python")
    ap.add_argument("server")
    ap.add_argument("--profile", default="web")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    path = patch_path(args.profile)
    if not os.path.exists(path):
        print(f"  {path} : absent (DeepSeek Harness n'est pas installé pour ce profil)")
        return 2

    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    new = strip_block(text)
    if not args.remove:
        block = render(args.python, args.server)
        new = (new + "\n\n" + block + "\n") if new.strip() else block + "\n"
    else:
        new += "\n"

    if new == text:
        print(f"  {path} : déjà à jour")
        return 0

    shutil.copy2(path, path + ".bak-vroidmcp")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(new)
    os.replace(tmp, path)
    print(f"  {path} : connecteur vroid {'retiré' if args.remove else 'déclaré'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
