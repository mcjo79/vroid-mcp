"""Client MCP stdio minimal pour tester le serveur vroid_mcp.py sans le modifier.

Usage :
  python tools/mcp_client.py list
  python tools/mcp_client.py call vroid_status
  python tools/mcp_client.py batch calls.json   (liste de {"name":..., "arguments":{...}})
  python tools/mcp_client.py batch -            (lit le JSON sur stdin)

Les images renvoyées par vroid_screenshot sont écrites dans out/ et leur chemin est affiché.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "mcp_server", "vroid_mcp.py")
OUT = os.path.join(ROOT, "out")


class Client:
    def __init__(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        self.proc = subprocess.Popen(
            [sys.executable, SERVER],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
        )
        self.next_id = 1
        self.request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "dsh-test-client", "version": "0.1"},
        })
        self.notify("notifications/initialized", {})

    def notify(self, method, params):
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params):
        rid = self.next_id
        self.next_id += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                err = self.proc.stderr.read()
                raise RuntimeError(f"serveur MCP terminé. stderr:\n{err}")
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            if msg.get("id") != rid:
                continue
            if "error" in msg:
                raise RuntimeError(msg["error"])
            return msg["result"]

    def call(self, name, arguments=None):
        return self.request("tools/call", {"name": name, "arguments": arguments or {}})

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def render(result, image_prefix):
    """Affiche un résultat d'outil ; sauvegarde les images et renvoie (texte, [chemins])."""
    parts = []
    images = []
    for i, item in enumerate(result.get("content") or []):
        if item.get("type") == "text":
            try:
                parts.append(json.dumps(json.loads(item["text"]), ensure_ascii=False, indent=1))
            except Exception:
                parts.append(item["text"])
        elif item.get("type") == "image":
            os.makedirs(OUT, exist_ok=True)
            path = os.path.join(OUT, f"{image_prefix}_{i}.png")
            import base64
            with open(path, "wb") as f:
                f.write(base64.b64decode(item["data"]))
            images.append(path)
            parts.append(f"[image -> {path}]")
    text = "\n".join(parts)
    if result.get("isError"):
        text = "ERREUR: " + text
    return text, images


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    client = Client()
    try:
        if cmd == "list":
            tools = client.request("tools/list", {})["tools"]
            for t in tools:
                print(t["name"])
            return 0
        if cmd == "call":
            name = sys.argv[2]
            args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
            text, _ = render(client.call(name, args), name)
            print(text)
            return 0
        if cmd == "batch":
            src = sys.argv[2]
            raw = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
            calls = json.loads(raw)
            if isinstance(calls, dict):
                calls = calls["calls"]
            for i, c in enumerate(calls):
                text, _ = render(client.call(c["name"], c.get("arguments") or {}), f"{i:02d}_{c['name']}")
                print(f"===== {c['name']} =====")
                print(text)
            return 0
        print(f"commande inconnue : {cmd}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
