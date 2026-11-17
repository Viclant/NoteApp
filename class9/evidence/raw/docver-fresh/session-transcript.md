# Fresh Class 9 run — teacher version 8d59164

Prediction was saved in `PREDICTION.txt` at 18:09 (+08:00). The clean baseline
requests below were run afterwards against the isolated app on port 8086. The source
was then patched and rebuilt in the same Compose project.

## Baseline: SQL injection

Request:

```text
POST /login
username = admin' -- 
password = anything
```

Observed: POST `/login` -> **302**; GET `/admin` with the returned cookie -> **200**.
The page contains `<h1>Users</h1>`.

Saved responses:

* `fresh-admin-sqli-login.html`
* `fresh-admin-sqli-page.html`

Second request:

```text
POST /login
username = alice' -- 
password = (empty)
```

Observed: POST `/login` -> **302**; GET `/dashboard` -> **200**, page identifies Alice
and contains `<h1>My grades</h1>`.

Saved responses: `fresh-alice-sqli-login.html`, `fresh-alice-dashboard.html`.

## Baseline: command injection

First log in normally as `admin` / `admin123`, then:

```text
POST /admin/ping
host = 127.0.0.1; id; head -2 /etc/passwd
```

Observed: HTTP **200**. The output includes:

```text
uid=0(root) gid=0(root) groups=0(root)
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin/nologin
```

Saved response: `fresh-cmdi-break.html`.

## Fix and replay

The login query was changed to `%s` placeholders with
`cur.execute(query, (username, password))`. Ping was changed to
`subprocess.run(["ping", "-c", "1", host], ...)` with no `shell=True`. The app was
rebuilt. Source diff: `docver-fix.patch`.

| Replay | Observed |
|---|---|
| `admin' -- ` / `anything` | login HTTP 200 with “Invalid credentials”; `/admin` 302 |
| `alice' -- ` / empty password | login HTTP 200 with “Invalid credentials”; `/dashboard` 302 |
| same injected ping host | HTTP 200; “Name or service not known”; zero `uid`/passwd matches |
| normal `alice` / `alicepw` | login 302; dashboard 200 |
| normal ping `127.0.0.1` | HTTP 200; `64 bytes from 127.0.0.1` |

Saved responses: `fixed-admin-sqli-login.html`, `fixed-alice-sqli-login.html`,
`fixed-cmdi.html`, and `fixed-ping-normal.html`. Screenshot 06 shows normal
Alice login. The earlier run also includes [the saved dashboard response](../docver/normal-alice.html).

The browser screenshots in `../../screenshots/` are actual Edge renders of these
results. Their small footer captions are annotations added for identification.
