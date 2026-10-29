"""Vérifie le serveur MCP sur son vrai transport : stdio + JSON-RPC.

Nos tests hors ligne appellent run_tool() directement. Ici on parle au serveur comme
le font Claude Code et DeepSeek Harness : initialize, tools/list, tools/call.

À lancer dans l'invité avec le Python embarqué :
    python.exe probe_stdio.py
"""
import json
import subprocess

PY = r"C:\Users\vroid\AppData\Local\VRoidMcp\python\python.exe"
SRV = r"C:\Users\vroid\AppData\Local\VRoidMcp\mcp_server\vroid_mcp.py"


def main():
    proc = subprocess.Popen(
        [PY, "-X", "utf8", "-E", "-s", SRV],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", bufsize=1,
    )

    def send(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def recv(want_id, limit=40):
        for _ in range(limit):
            line = proc.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == want_id:
                return msg
        return None

    report = {}

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "probe", "version": "1"}}})
    init = recv(1)
    srv = (init or {}).get("result", {}).get("serverInfo", {})
    report["initialize"] = {"server": srv.get("name"), "version": srv.get("version")}

    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools_msg = recv(2)
    tools = (tools_msg or {}).get("result", {}).get("tools", [])
    report["tools/list"] = {"count": len(tools), "first": [t["name"] for t in tools[:3]]}

    send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
          "params": {"name": "vroid_status", "arguments": {}}})
    call = recv(3)
    content = (call or {}).get("result", {}).get("content", [])
    text = content[0].get("text", "") if content else ""
    report["tools/call vroid_status"] = {"ok": bool(call and "result" in call),
                                         "extrai": text[:160]}

    send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
          "params": {"name": "vroid_help", "arguments": {"topic": "overview"}}})
    call2 = recv(4)
    content2 = (call2 or {}).get("result", {}).get("content", [])
    text2 = content2[0].get("text", "") if content2 else ""
    report["tools/call vroid_help"] = {"ok": bool(call2 and "result" in call2),
                                       "longueur": len(text2)}

    proc.terminate()
    err = ""
    try:
        err = proc.stderr.read()[-400:]
    except Exception:  # noqa: BLE001
        pass
    if err.strip():
        report["stderr"] = err.strip()

    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
