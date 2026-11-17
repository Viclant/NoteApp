# Class 9 injection lab — requirement-by-requirement check

Student: WU YANLAN (2023905420)  
Official task: <https://github.com/KristenPire/epita-security-labs/blob/main/docs/class9/injection.md>

## Scope and version choice

The teacher's login example contains both username and password in one SQL string.
That exact code is in commit `8d59164` of this NotesApp history. An isolated copy of
that commit was used for a fresh, literal run at `127.0.0.1:8086`. Only lab isolation
settings were changed: web port 8086, no host database port, and no Docker socket or
host-project bind mount.

The current project has evolved since that version. C5 (`9547348`) moved password
verification to Python and Argon2; therefore the document's `admin' -- ` input does
not bypass the password check there. The same SQL concatenation flaw remained and was
tested separately on the current app using a UNION payload. This submission applies the
current-app fix from `injection-fix.patch`. No claim is made that the literal
payload works on the post-C5 code.

## Prediction

`PREDICTION.txt` records a prediction at 18:09 on 17 November 2026, before the fresh
8086 baseline requests: the literal login payload should bypass the password condition;
the ping payload should execute `id`; parameter binding and argv execution should stop
both attacks; normal Alice login and ordinary ping should remain usable.

## Official hand-in checklist

| Teacher requirement | Test performed | Result | Evidence |
|---|---|---|---|
| Prove login as admin without a password (SQLi) | On the teacher-code snapshot, username `admin' -- ` and password `anything` | POST `/login` 302; `/admin` 200, Users page | screenshot 02; `raw/docver-fresh/fresh-admin-sqli-*` |
| Show the exact input works as a normal user too | `alice' -- ` with an empty password | POST `/login` 302; `/dashboard` 200, My grades | screenshot 01; `raw/docver-fresh/fresh-alice-*` |
| Fix `login` with a parameterised query | `%s` placeholders and a `(username, password)` tuple | Rebuilt the same isolated app | `teacher-version/web/app.py`; `raw/docver-fresh/docver-fix.patch` |
| Replay the same SQLi input after the fix | Replayed the admin and Alice inputs | Both show “Invalid credentials”; protected page returns 302 | screenshot 04; `raw/docver-fresh/fixed-*-sqli-*` |
| Prove command execution via admin ping | Host `127.0.0.1; id; head -2 /etc/passwd` | Output includes `uid=0(root)` and first two passwd entries | screenshot 03; `raw/docver-fresh/fresh-cmdi-break.html` |
| Fix `admin_ping` without a shell | `subprocess.run(["ping", "-c", "1", host], ...)` | Rebuilt isolated app; `shell=True` removed | `teacher-version/web/app.py`; `raw/docver-fresh/docver-fix.patch` |
| Replay the same command input after the fix | Same host string | Hostname resolution error; no uid/passwd output | screenshot 05; `raw/docver-fresh/fixed-cmdi.html` |
| Preserve normal Alice login | `alice` / `alicepw` | Login redirect; dashboard 200 | screenshot 06; earlier run `raw/docver/normal-alice.html` |
| Preserve normal ping | Host `127.0.0.1` | HTTP 200; `64 bytes from 127.0.0.1` | screenshot 07; `raw/docver-fresh/fixed-ping-normal.html` |
| Commit fixed `web/app.py` | Apply `injection-fix.patch` to the repository root | The current app preserves Argon2 | `../web/app.py` in this submission |

## Test record — fresh teacher-version run

The `class9-submit` Compose project ran an untouched `8d59164` app first, then the
document's reference fixes were applied and the same project rebuilt. It used an
independent database volume. HTTP results:

| Input | Before fix | After fix |
|---|---:|---:|
| `admin' -- ` / `anything` login | 302, `/admin` 200 | 200 with login error, `/admin` 302 |
| `alice' -- ` / empty password | 302, `/dashboard` 200 | 200 with login error, `/dashboard` 302 |
| `127.0.0.1; id; head -2 /etc/passwd` | Ping page 200 with `uid=0(root)` and passwd lines | Ping page 200 with “Name or service not known”; zero uid/passwd matches |
| `alice` / `alicepw` | — | Login 302, dashboard 200 |
| `127.0.0.1` | — | Ping page 200, `64 bytes from 127.0.0.1` |

Raw response bodies are under `evidence/raw/docver-fresh/`. Session JWTs were
redacted from the HTML responses. Browser
screenshots are actual Edge captures of the NotesApp pages; the small black footer
caption is an annotation added for readability, not app output.

## Current-app integration check

The current app keeps its C5 Argon2 password verification. Its SQLi fix parameterises
only the username (`WHERE username = %s`; `cur.execute(query, (username,))`), rather
than comparing the plaintext password against a stored Argon2 hash. The current
`admin_ping` uses the same argument-list fix. The submission applies
`injection-fix.patch` to the root app from `origin/main`.

Current-app before/after raw results are kept separately in `evidence/raw/current/`.
This separation avoids presenting a result from one code version as if it came from
another.

## Files included

- `PREDICTION.txt` — time-stamped prediction recorded before the fresh run.
- `HAND-IN.txt` — filled-in teacher template.
- `teacher-version/web/app.py` — complete fixed source for the version matching the
  lesson's SQL and plain seed passwords.
- `injection-fix.patch` and `fixed-web-app.py` — current project integration patch
  and the fixed current `web/app.py`.
- `evidence/screenshots/` — seven real browser captures.
- `evidence/raw/docver-fresh/` — primary before/after HTTP evidence and patch.
- `evidence/raw/current/` — current-app UNION and regression evidence.
- `appendix-docver/DOCVER-RESULTS.md` — explanatory version history and earlier run.
