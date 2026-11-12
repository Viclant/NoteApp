#!/usr/bin/env python3
"""Optional strong-secret control. Local control keys are never printed or saved."""
import argparse
import json
import os
from pathlib import Path
from part2 import (Lab, PACKAGE_ROOT, load_wordlist, login_as_alice, make_token,
                   now, resolve_dir, sign_hs256, split_jwt)


def read_control_secret(path):
    value = os.environ.get("CONTROL_JWT_SECRET", "").strip()
    if not value and path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("CONTROL_JWT_SECRET="):
                value = line.partition("=")[2].strip()
                break
    if not value:
        raise ValueError("positive-control key missing: run class7-control/setup_keys.py and supply --secret-file or CONTROL_JWT_SECRET")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8083")
    parser.add_argument("--wordlist", type=Path, default=PACKAGE_ROOT / "lab/jwt-secrets.txt")
    parser.add_argument("--part2-results", type=Path, default=PACKAGE_ROOT / "evidence/part2-results.json")
    parser.add_argument("--secret-file", type=Path, default=PACKAGE_ROOT / "class7-control/.env")
    parser.add_argument("--out", help="new output directory; defaults to a unique evidence/reruns folder")
    args = parser.parse_args()
    try:
        words = load_wordlist(str(args.wordlist))
        source = json.loads(args.part2_results.read_text(encoding="utf-8-sig"))
        classroom_forged = source["forged_token"]["token"]
        teacher_payload = source["forged_token"]["payload"]
        if teacher_payload.get("role") != "teacher":
            raise ValueError("Part 2 input must contain a teacher token")
        secret = read_control_secret(args.secret_file)
        lab = Lab(args.base)
        out = Path(resolve_dir(args.out))
        if (out / "class7-control.json").exists():
            raise ValueError("output already contains control evidence; choose a new --out")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    started = now()
    real, _ = login_as_alice(lab, "alice", "alicepw")
    h, p, signature = split_jwt(real)
    if sign_hs256(secret, h, p) != signature:
        parser.error("the positive-control key does not match this instance")
    matching = [word for word in words if sign_hs256(word, h, p) == signature]
    tokens = [
        ("X1", "classroom-key teacher token", classroom_forged, 401),
        ("X2", "unsigned token", make_token(teacher_payload, None, "none"), 401),
        ("X3", "teacher token signed with the actual control key", make_token(teacher_payload, secret), 200),
    ]
    checks = []
    for cid, label, token, expected in tokens:
        exchange = lab.request("GET", "/api/notes/3", {"Authorization": "Bearer " + token})
        body = Lab.as_json(exchange)
        body_ok = body == {"error": "unauthorized"} if expected == 401 else (
            isinstance(body, dict) and all(body.get(k) == v for k, v in {
                "id": 3, "student": "bob", "student_id": 7, "class_name": "Mathematics",
                "grade": 12.6, "comment": "Solid work, keep it up."}.items()))
        ok = exchange["status"] == expected and body_ok and not exchange["request_cookie_sent"]
        checks.append({"id": cid, "check": label, "expected_status": expected,
                       "actual_status": exchange["status"], "body": body,
                       "cookie_sent": exchange["request_cookie_sent"], "pass": ok})
    lab.close()
    passed = not matching and len(checks) == 3 and all(c["pass"] for c in checks)
    result = {"scope": "optional separate strong-secret control", "started_at": started,
              "finished_at": now(), "target": args.base, "wordlist": str(args.wordlist.resolve()),
              "wordlist_size": len(words), "candidates_tried": len(words),
              "wordlist_match_on_strong_secret": matching or None,
              "positive_control_key_verified_against_real_jwt": True,
              "checks": checks, "overall_passed": passed}
    out.mkdir(parents=True, exist_ok=True)
    (out / "class7-control.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [f"Strong-secret control: {args.base}", f"Wordlist candidates tried: {len(words)}",
             f"Wordlist match: {'FOUND (unexpected)' if matching else 'none'}"]
    lines += [f"{c['id']}: {c['actual_status']} - {'PASS' if c['pass'] else 'FAIL'}" for c in checks]
    lines.append("Overall: " + ("PASS" if passed else "FAIL"))
    text = "\n".join(lines) + "\n"
    (out / "class7-control.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
