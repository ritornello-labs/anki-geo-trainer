"""Evaluate JS in the AnkiDroid card WebView over raw CDP (no Playwright).

Usage: python3 scripts/droid_cdp.py '<js expression>'
Assumes `adb forward tcp:9223 localabstract:webview_devtools_remote_<pid>` is up.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import sys
import urllib.request


def ws_connect(url: str) -> socket.socket:
    # url: ws://localhost:9223/devtools/page/<id>
    _, rest = url.split("://", 1)
    hostport, path = rest.split("/", 1)
    host, port = hostport.split(":")
    s = socket.create_connection((host, int(port)), timeout=15)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
        f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    )
    s.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += s.recv(4096)
    if b"101" not in resp.split(b"\r\n", 1)[0]:
        raise RuntimeError("websocket handshake failed: " + resp.decode(errors="replace")[:200])
    return s


def ws_send(s: socket.socket, payload: str) -> None:
    data = payload.encode()
    header = bytearray([0x81])
    mask = os.urandom(4)
    n = len(data)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header.append(0x80 | 126)
        header += struct.pack(">H", n)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", n)
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    s.sendall(bytes(header) + masked)


def ws_recv(s: socket.socket) -> str:
    def read(n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = s.recv(n - len(buf))
            if not chunk:
                raise RuntimeError("socket closed")
            buf += chunk
        return buf

    b1, b2 = read(2)
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack(">H", read(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", read(8))[0]
    if b2 & 0x80:
        mask = read(4)
        data = read(length)
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    else:
        data = read(length)
    return data.decode(errors="replace")


def evaluate(expression: str, port: int = 9223) -> object:
    pages = json.load(urllib.request.urlopen(f"http://localhost:{port}/json"))
    page = next(p for p in pages if p.get("type") in (None, "page") or "Flashcard" in p.get("title", ""))
    s = ws_connect(page["webSocketDebuggerUrl"])
    ws_send(s, json.dumps({
        "id": 1, "method": "Runtime.evaluate",
        "params": {"expression": expression, "returnByValue": True, "awaitPromise": True},
    }))
    while True:
        msg = json.loads(ws_recv(s))
        if msg.get("id") == 1:
            s.close()
            result = msg.get("result", {}).get("result", {})
            if "value" in result:
                return result["value"]
            return result


if __name__ == "__main__":
    print(json.dumps(evaluate(sys.argv[1]), indent=2, ensure_ascii=False))
