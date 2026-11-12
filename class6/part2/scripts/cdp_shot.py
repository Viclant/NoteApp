#!/usr/bin/env python3
"""Drive a real (headless) Edge through the DevTools protocol to capture the
application's own interface while a forged Bearer token is used.

No screenshot is drawn: Edge renders the real NotesApp pages and the pixels are
read back from the browser itself.

Steps:
  1. start Edge with --remote-debugging-port,
  2. open http://127.0.0.1:8082/login and log in as alice with the normal form,
  3. open the real /dashboard page,
  4. run a fetch() with the forged teacher JWT and write the real answer into the
     page's own "Grade detail (API)" output area,
  5. capture the screen of the page.

A minimal WebSocket client is implemented here because the standard library has
none.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = os.path.join(os.environ.get("TEMP", os.getcwd()), "jwt-part2-edge-cdp")


class WS:
    """Very small WebSocket client (text frames only)."""

    def __init__(self, url: str):
        assert url.startswith("ws://")
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               f"Sec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(req.encode())
        self.buf = b""
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("handshake failed")
            self.buf += chunk
        head, _, rest_bytes = self.buf.partition(b"\r\n\r\n")
        if b"101" not in head.split(b"\r\n")[0]:
            raise RuntimeError("handshake rejected: " + head.split(b"\r\n")[0].decode())
        self.buf = rest_bytes

    def _recv_exact(self, count: int) -> bytes:
        while len(self.buf) < count:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError("connection closed")
            self.buf += chunk
        out, self.buf = self.buf[:count], self.buf[count:]
        return out

    def send(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        mask = os.urandom(4)
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < (1 << 16):
            header.append(0x80 | 126)
            header += struct.pack(">H", length)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", length)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def recv(self) -> str:
        while True:
            b1, b2 = self._recv_exact(2)
            opcode = b1 & 0x0F
            length = b2 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._recv_exact(8))[0]
            if b2 & 0x80:
                mask = self._recv_exact(4)
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(self._recv_exact(length)))
            else:
                data = self._recv_exact(length)
            if opcode == 0x1:
                return data.decode("utf-8", "replace")
            if opcode == 0x8:
                raise RuntimeError("browser closed the connection")

    def close(self) -> None:
        try:
            self.sock.close()
        except Exception:
            pass


class Browser:
    def __init__(self, port: int):
        self.port = port
        self.next_id = 0
        self.ws = WS(self.page_target()["webSocketDebuggerUrl"])

    def page_target(self) -> dict:
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=5) as fh:
                    targets = json.load(fh)
                for target in targets:
                    if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                        return target
            except Exception:
                pass
            time.sleep(0.5)
        raise RuntimeError("no debuggable page target")

    def call(self, method: str, params: dict | None = None, timeout: float = 30.0) -> dict:
        self.next_id += 1
        message_id = self.next_id
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = json.loads(self.ws.recv())
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method} -> {message['error']}")
                return message.get("result", {})
        raise TimeoutError(method)

    def evaluate(self, expression: str, await_promise: bool = True):
        result = self.call("Runtime.evaluate", {
            "expression": expression,
            "awaitPromise": await_promise,
            "returnByValue": True,
            "userGesture": True,
        })
        if result.get("exceptionDetails"):
            raise RuntimeError(json.dumps(result["exceptionDetails"])[:400])
        return result.get("result", {}).get("value")

    def navigate(self, url: str, settle: float = 2.0) -> None:
        self.call("Page.navigate", {"url": url})
        time.sleep(settle)

    def screenshot(self, path: str) -> None:
        data = self.call("Page.captureScreenshot", {"format": "png"})["data"]
        with open(path, "wb") as handle:
            handle.write(base64.b64decode(data))

    def close(self) -> None:
        self.ws.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8082")
    parser.add_argument("--username", default="alice")
    parser.add_argument("--password", default="alicepw")
    parser.add_argument("--note", type=int, default=3)
    parser.add_argument("--token", required=True, help="Bearer token to use")
    parser.add_argument("--label", default="the forged teacher JWT",
                        help="text put in the panel title")
    parser.add_argument("--out", required=True)
    parser.add_argument("--port", type=int, default=9222)
    args = parser.parse_args()

    edge = subprocess.Popen([
        EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
        f"--remote-debugging-port={args.port}", f"--user-data-dir={PROFILE}",
        "--window-size=1400,1000", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        browser = Browser(args.port)
        browser.call("Page.enable")
        browser.call("Runtime.enable")

        # 1. normal form login through the real login page
        browser.navigate(f"{args.base}/login", settle=2.0)
        browser.evaluate(f"""
            document.querySelector('input[name=username]').value = {json.dumps(args.username)};
            document.querySelector('input[name=password]').value = {json.dumps(args.password)};
            document.querySelector('form').submit();
            'submitted';
        """, await_promise=False)
        time.sleep(2.5)

        # 2. the real dashboard of the application
        browser.navigate(f"{args.base}/dashboard", settle=2.5)

        # 3. the application asks the API for the note with the forged token and
        #    the answer is written into the page's own output area
        script = f"""
            (async () => {{
              const res = await fetch('/api/notes/{args.note}', {{
                headers: {{ 'Authorization': 'Bearer {args.token}' }}
              }});
              const text = await res.text();
              const box = document.getElementById('apiOut');
              box.textContent = 'HTTP ' + res.status + ' ' + res.statusText + '\\n' + text;
              document.getElementById('noteId').value = '{args.note}';
              const head = document.querySelector('h2');
              head.textContent = 'Grade detail (API) - request sent with ' + {json.dumps(args.label)};
              return res.status;
            }})()
        """
        status = browser.evaluate(script)
        time.sleep(1.5)
        browser.screenshot(args.out)
        browser.close()
        print(f"captured {args.out} (HTTP {status} in the page)")
        return 0
    finally:
        edge.terminate()
        try:
            edge.wait(timeout=10)
        except Exception:
            edge.kill()


if __name__ == "__main__":
    raise SystemExit(main())
