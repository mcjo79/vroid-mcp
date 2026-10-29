"""Déclare (ou retire) le serveur MCP "vroid" dans un fichier de configuration Claude.

    python register_mcp.py <config.json> <python.exe> <vroid_mcp.py>
    python register_mcp.py --remove <config.json>

Fonctionne pour ~/.claude.json (Claude Code) et claude_desktop_config.json (Claude Desktop).
Le fichier est sauvegardé (.bak-vroidmcp) avant modification ; le reste de son contenu est conservé.

Le serveur est lancé avec -X utf8 -E -s : UTF-8 imposé, variables PYTHON* ignorées et site-packages
utilisateur désactivé. Un Python installé à côté (même 3.12) ne peut donc pas contaminer le Python local.
"""
import json
import os
import shutil
import sys

# Isolation du Python local : aucune dépendance à l'environnement de la machine.
PYFLAGS = ["-X", "utf8", "-E", "-s"]


def main():
    args = sys.argv[1:]
    remove = args and args[0] == "--remove"
    if remove:
        args = args[1:]
    path = args[0]
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        data = json.loads(text) if text.strip() else {}
        shutil.copy2(path, path + ".bak-vroidmcp")
    elif remove:
        return
    servers = data.setdefault("mcpServers", {})
    if remove:
        if servers.pop("vroid", None) is None:
            print(f"  {path} : rien à retirer")
            return
    else:
        python, server = args[1], args[2]
        entry = {"command": python, "args": PYFLAGS + [server], "env": {}}
        if os.path.basename(path) == ".claude.json":
            entry = {"type": "stdio", **entry}
        servers["vroid"] = entry
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    print(f"  {path} : serveur vroid {'retiré' if remove else 'déclaré'}")


if __name__ == "__main__":
    main()
