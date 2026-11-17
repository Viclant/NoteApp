# Class 9 — literal run on the teacher's version (commit 8d59164)

Purpose: confirm that the class document's exact inputs work on the version it was
written against, and that the same fixes close them there too.

## Which version is "the teacher's version"

| Commit | Date | What it did |
|---|---|---|
| `8d59164` | 2026-09-10 | Login SQL concatenates username and password, matching the class document |
| `9547348` | 2026-10-22 | C5 Argon2: removes the SQL password condition and verifies the password in Python |
| `39bdaff` | 2026-11-17 | Current-app Class 9 fix; parameterises username and keeps Argon2 |

The literal inputs were run on an isolated copy of `8d59164`, not represented as
working against the post-C5 app. In the current app, the same SQL concatenation flaw
was separately demonstrated using UNION.

## Lab setup

* Source: `git archive 8d59164`
* Isolated Compose project on `127.0.0.1:8085`; independent database volume
* Host DB port, Docker socket, and host-project bind mount removed for isolation
* Fresh replay after the pre-run prediction used a separate project on port 8086
* Both lab projects were stopped and their disposable volumes removed after testing

## Results

| Check | Before fix | After fix |
|---|---|---|
| `admin' -- ` / password `anything` | POST `/login` 302; `/admin` **200** (Users page) | “Invalid credentials”; `/admin` 302 |
| `alice' -- ` / empty password | POST `/login` 302; `/dashboard` **200** (Alice) | “Invalid credentials”; `/dashboard` 302 |
| `alice' -- ` / password `wrongpass` | Dashboard **200**; password ignored | “Invalid credentials”; dashboard 302 |
| `host = 127.0.0.1; id; head -2 /etc/passwd` | `uid=0(root)`, `root:x:0:0...`, `daemon:x:1:1...` | `Name or service not known`; no uid/passwd output |
| Normal `alice` / `alicepw` | — | Dashboard 200 |
| Plain `host = 127.0.0.1` | — | Ping 200; `64 bytes from 127.0.0.1` |

The quote ends the SQL string; `--` comments out `AND password = '...'`, and the
returned row logs the user in.

## Reference fix applied to this version

```python
query = (
    "SELECT id, username, role FROM users "
    "WHERE username = %s AND password = %s"
)
cur.execute(query, (username, password))
```

This matches the teacher's reference shape and works with this revision's plaintext
seed passwords. It is not suitable for post-C5 Argon2 hashes. The current-app patch
therefore parameterises only the username and retains Python's Argon2 verification.

## Evidence

* Fresh baseline and fixed responses: `../evidence/raw/docver-fresh/`
* Earlier baseline/fix responses: `../evidence/raw/docver/`
* Seven Edge screenshots: `../evidence/screenshots/`
* Fresh run transcript: `../evidence/raw/docver-fresh/session-transcript.md`
* Teacher-version fix: `../evidence/raw/docver-fresh/docver-fix.patch`
* Official instructions captured as read: `teacher-injection.md`

Cookie jars were intentionally excluded from the hand-in folder; the raw response
bodies and screenshots are retained.
