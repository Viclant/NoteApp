# Test notes

These are the details behind the short lab report in [README.md](README.md).
The full application is in `../web/app.py`; `fixed-verify_jwt.py` is an excerpt.

## Saved results

The checks ran against the real local NotesApp at `http://127.0.0.1:8080` on
12 November 2026. Before the fix, both recreated teacher tokens returned Bob's
note with HTTP 200. After the fix, both returned HTTP 401. Alice could still log
in and read her own note. Alice's request for Bob's note still returned HTTP 404.

The saved results are in `evidence/`:

- `before.json` and `after.json`: actual HTTP responses before and after the fix.
- `test-summary.json`: 12 Class 7 HTTP checks, 23 unit tests and 11 Class 8
  HTTP checks passed.
- `prediction.json`: prediction recorded by Codex after reading the source,
  before the baseline requests and changes.
- `provenance.json`: source version and hashes for the tested application.

The Bearer-only checks used a client without cookies. Extra checks confirmed
that invalid Bearer tokens are rejected even with a valid Alice session.
Key setup checks confirmed that the existing comment encryption and CSV HMAC
keys were preserved and that running setup again did not change the keys.

Codex made the changes and ran the automated checks on this computer. The two
old classroom tokens were recreated for the test; this was not a new weak-key
cracking experiment. No partner name was provided. The recorded prediction
does not claim to be a student's independent classroom prediction. No tokens,
cookies or real secret values are included in these records.

## Run again

From the repository root:

```powershell
python setup_keys.py
docker compose up -d --build
docker compose exec -T web python -m unittest test_jwt test_homework test_passwords -v
```

For the existing desktop setup, the Compose command is:

```powershell
docker compose -p viclant-noteapp -f docker-compose.yml -f ../noteapp.local.yml up -d --build
```

Generate a new local key after cloning. In production, use a secrets store and
keep real values out of committed files. This lab fixes the JWT login exercise;
other intentional teaching flaws remain in NotesApp.

[Class 7 instructions](https://kristenpire.github.io/epita-security-labs/class7/fix-the-login/)
