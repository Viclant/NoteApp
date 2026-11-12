"""Check the Class 7 JWT repair on the local NotesApp (Python standard library)."""

import argparse
import base64
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import http.cookiejar
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener


def encode(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()


def old_teacher_token(algorithm):
    header = encode({"alg": algorithm, "typ": "JWT"})
    payload = encode({"user_id": 6, "username": "alice", "role": "teacher"})
    message = f"{header}.{payload}"
    signature = ""
    if algorithm == "HS256":
        signature = base64.urlsafe_b64encode(
            hmac.new(b"s3cr3t", message.encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
    return f"{message}.{signature}"


def request(client, base_url, path, token=None, form=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    data = None if form is None else urlencode(form).encode()
    req = Request(base_url + path, data=data, headers=headers)
    try:
        response = client.open(req, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        text = response.read().decode()
        try:
            body = json.loads(text)
        except ValueError:
            body = None
        return response.status, body, text, urlsplit(response.geturl()).path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--phase", choices=["before", "after"], default="after")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("Use your own loopback HTTP NotesApp only.")
    base_url = args.base_url.rstrip("/")
    bare = build_opener(ProxyHandler({}))  # No CookieProcessor; Bearer requests cannot use a session.
    session = build_opener(ProxyHandler({}), HTTPCookieProcessor(http.cookiejar.CookieJar()))
    cases = []

    def check(name, client, path, status, token=None, body=None, form=None, final_path=None):
        actual, response, text, final = request(client, base_url, path, token, form)
        passed = actual == status and (body is None or response == body)
        if status == 200 and path.startswith("/api/notes/"):
            note_id = int(path.rsplit("/", 1)[1])
            expected_student = {1: "alice", 3: "bob"}.get(note_id)
            passed = (passed and isinstance(response, dict)
                      and response.get("id") == note_id
                      and response.get("student") == expected_student
                      and isinstance(response.get("grade"), (int, float))
                      and isinstance(response.get("comment"), str))
        if final_path is not None:
            passed = passed and final == final_path
        cases.append({"name": name, "auth": "cookie-free" if client is bare else "session",
                      "expected_status": status, "status": actual, "body": response,
                      "passed": passed})
        print(f"{'PASS' if passed else 'FAIL'} {name}: HTTP {actual}")
        return text

    unsigned = old_teacher_token("none")
    weak_signed = old_teacher_token("HS256")
    forgery_status = 200 if args.phase == "before" else 401
    forgery_body = None if args.phase == "before" else {"error": "unauthorized"}
    check("no credentials", bare, "/api/notes/3", 401, body={"error": "unauthorized"})
    check("old alg:none teacher token", bare, "/api/notes/3", forgery_status,
          token=unsigned, body=forgery_body)
    check("old s3cr3t-signed teacher token", bare, "/api/notes/3", forgery_status,
          token=weak_signed, body=forgery_body)
    check("normal Alice login", session, "/login", 200,
          form={"username": "alice", "password": "alicepw"}, final_path="/dashboard")
    dashboard = check("Alice dashboard", session, "/dashboard", 200, final_path="/dashboard")
    match = re.search(r"\bconst\s+TOKEN\s*=\s*(.*?);", dashboard, re.DOTALL)
    if match is None:
        raise RuntimeError("The live dashboard did not provide a genuine token.")
    genuine = json.loads(match.group(1))
    check("fresh genuine Alice JWT, own note", bare, "/api/notes/1", 200, token=genuine)
    check("fresh Alice JWT, Bob note (Class 8)", bare, "/api/notes/3", 404,
          token=genuine, body={"error": "not found"})
    check("Alice session, own note", session, "/api/notes/1", 200)
    check("Alice session, Bob note (Class 8)", session, "/api/notes/3", 404,
          body={"error": "not found"})
    corrupted = genuine.rsplit(".", 1)[0] + ".invalid"
    check("bad JWT signature", bare, "/api/notes/1", 401,
          token=corrupted, body={"error": "unauthorized"})
    if args.phase == "after":
        check("bad Bearer with valid Alice session", session, "/api/notes/1", 401,
              token=corrupted, body={"error": "unauthorized"})
        check("unsigned Bearer with valid Alice session", session, "/api/notes/1", 401,
              token=unsigned, body={"error": "unauthorized"})
    result = {"recorded_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
              "phase": args.phase, "base_url": base_url,
              "method": "Automated real HTTP requests; old classroom forgeries reconstructed with the public old key; no tokens or cookies saved.",
              "cases": cases, "all_passed": all(c["passed"] for c in cases)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["all_passed"]:
        raise SystemExit(1)
    print(f"{len(cases)} checks passed ({args.phase}).")


if __name__ == "__main__":
    main()
