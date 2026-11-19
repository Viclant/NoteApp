# Class 10 — Stored XSS hand-in

Submission notes and evidence-caption corrections: [SUBMISSION-NOTES.md](SUBMISSION-NOTES.md).

**Student:** WU YANLAN · **Student ID:** 2023905420

This hand-in covers the teacher's four outcomes: store a harmless script as a
teacher comment, observe it execute in Alice's browser, restore escaping in both
templates, and verify that a normal comment still displays correctly.

## Read these first

1. `Class10-Stored-XSS-Wu-Yanlan.pdf` — short report.
2. `HAND-IN.txt` — completed teacher checklist.
3. `REQUIREMENTS-CHECK.md` — requirements and observed results.
4. `PREDICTION.txt` — prediction written before the first test request.

## What I tested

The test ran only on an isolated copy of NotesApp at `127.0.0.1:8087`, with its
own database volume and fresh local keys. The only payload was the lesson's
harmless `alert('XSS by Eve')`; no cookies or data were read or sent anywhere.

The teacher stored the comment on Alice's note 1. The raw dashboard response
contained a live `<script>` element. A real headless Edge browser logged in as
Alice and generated a `Page.javascriptDialogOpening` event with the message
`XSS by Eve`. After the exact template fix, the same comment remained readable
as text, but Edge observed no dialog and the comment cell had no script element.
The teacher view was checked too. A normal `score < 10 ... & ...` comment also
rendered correctly.

Comments are encrypted at rest in this app, but they are decrypted before being
rendered. Encryption at rest did not prevent the stored XSS; output escaping did.

## Files

```
Class10-Stored-XSS-Wu-Yanlan.pdf / .md / .html
HAND-IN.txt
REQUIREMENTS-CHECK.md
PREDICTION.txt
class10-fix.patch
fixed-templates/dashboard.html
fixed-templates/teacher.html
evidence/screenshots/             five actual Edge screenshots
evidence/raw/                     HTTP bodies, browser event JSON, before/after templates
references/stored-xss.md          teacher's official instruction page
```

No `.env`, browser profile, or session-cookie jar is included.

## GitHub submission

The two root template fixes and this `class10/` directory are submitted on
`codex/class10-submission`, based on `main` at `d624cdd`. The supplied patch
passed `git apply --check` and was applied to both root templates.

The original isolated-lab fix was recorded in local commit `f0b04cd`. That
historical commit reference in the report is separate from this clean submission.
The existing 23 unit tests and four offline template rendering checks passed;
see `evidence/submission-verification.json`.

The PDF and evidence are a draft for the student to review. The pre-run prediction
was prepared as an aid; revise it into your own words if the course expects your
personal prediction.
