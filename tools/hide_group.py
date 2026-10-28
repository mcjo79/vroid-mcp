"""Cache un vêtement en remplaçant ses calques de texture par du transparent.

Usage : python tools/hide_group.py <group_id> [<group_id> ...]
"""
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import Client  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call_json(client, name, args=None):
    res = client.call(name, args or {})
    for item in res.get("content") or []:
        if item.get("type") == "text":
            return json.loads(item["text"])
    raise RuntimeError(f"réponse sans texte : {res}")


def hide(client, group):
    layers = call_json(client, "vroid_list_layers", {"group": group})
    for t in layers:
        for im in t.get("images", []):
            for layer in im.get("layers", []):
                fd, tmp = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                try:
                    info = call_json(client, "vroid_export_layer", {
                        "transferable": t["transferable"], "image": im["image"],
                        "node": layer["node"], "path": tmp,
                    })
                    if not info.get("ok"):
                        print("export raté", info)
                        continue
                    Image.new("RGBA", (int(info["width"]), int(info["height"])), (0, 0, 0, 0)).save(tmp)
                    res = call_json(client, "vroid_import_layer", {
                        "transferable": t["transferable"], "image": im["image"],
                        "node": layer["node"], "path": tmp,
                    })
                    print(t["type"], layer["node"], "->", res)
                finally:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass


def main():
    client = Client()
    try:
        for group in sys.argv[1:]:
            print("=== groupe", group)
            hide(client, group)
    finally:
        client.close()


if __name__ == "__main__":
    main()
