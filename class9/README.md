# Class 9 — Injection (NotesApp)

**Student:** WU YANLAN · **Student ID:** 2023905420

This folder follows the teacher's Class 9 checklist: prove SQL injection and command
injection, fix both entry points, replay the same inputs, and show normal use still
works. It includes raw HTTP evidence and real browser screenshots.

## Start here

1. `Class9-Injection-Wu-Yanlan.pdf` — short student report.
2. `HAND-IN.txt` — completed version of the teacher's hand-in block.
3. `REQUIREMENTS-CHECK.md` — line-by-line checklist, test outcomes, and exact
   interpretation of the two code versions.
4. `PREDICTION.txt` — prediction recorded before the fresh test run.

## Important version note

The SQL shown in the lesson matches commit `8d59164`: it concatenates both username
and password into SQL. On that code, the teacher's exact `admin' -- ` input logs in
without a valid password. I re-ran this exact exercise on a clean, isolated copy of
that revision, then applied the reference fix and replayed the same input.

The working project has since added Argon2. In that current version, SQL looks up a
username and Python separately checks the password hash. Therefore, the literal
comment payload is not an authentication bypass there. The same SQL concatenation
bug was still present, and I tested it separately with UNION. This is documented
plainly; results from the old and current versions are stored in separate folders.

## Contents

```
class9/
  Class9-Injection-Wu-Yanlan.pdf
  Class9-Injection-Wu-Yanlan.md
  Class9-Injection-Wu-Yanlan.html
  HAND-IN.txt
  REQUIREMENTS-CHECK.md
  PREDICTION.txt
  fixed-web-app.py                current repo's fixed app.py
  injection-fix.patch             applies to current app / origin/main
  teacher-version/
    web/app.py                    complete fixed file for the lesson's 8d59164 code
    docker-compose.yml             isolated teaching snapshot (port 8086)
    db/init.sql
    web/Dockerfile
    web/requirements.txt
  evidence/
    screenshots/                  seven real Edge screenshots
    raw/docver-fresh/              fresh literal before/after HTTP evidence
    raw/docver/                    earlier literal run and source-version check
    raw/current/                   current-app UNION, fix, and regression evidence
  appendix-docver/DOCVER-RESULTS.md
```

The screenshot pixels are from the real NotesApp rendered in Edge. A small footer
caption was added to each capture to identify its test input/result.
The hand-in includes the saved response bodies, screenshots, and transcripts.
Session JWTs were redacted from the HTML responses, and cookie jars were omitted.

## Current application fix

This submission applies `injection-fix.patch` to the root `web/app.py` on a
branch from `origin/main`. The fixed app retains Argon2 password verification.
Use the isolated `teacher-version/` snapshot to reproduce the lesson's exact inputs.

## Reproducing the exact lesson version

The `teacher-version` directory is a self-contained fixed version. The recorded
before/after requests used the same source revision and an isolated Compose project
with an independent database volume at `127.0.0.1:8086`. The test environment has
been stopped after evidence capture.
