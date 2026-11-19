# Class 10 Stored XSS — requirement check

Student: WU YANLAN (2023905420)  
Official instructions: `references/stored-xss.md`

## Scope

All attack/fix testing was performed on an isolated current-version NotesApp copy
at `http://127.0.0.1:8087`, with a disposable database volume and fresh random
keys. The ordinary 8080 database was not used to plant or modify the test
comment. The payload was only the harmless lesson string
`<script>alert('XSS by Eve')</script>`.

## Pre-run prediction

`PREDICTION.txt` was recorded at 16:45 (+08:00), before the first test request.
It predicted that the dashboard would return a live script element and Edge
would display the alert, and that restoring Jinja autoescaping would make the
same input inert while preserving normal text. The prediction file notes that
it was prepared as an aid and should be personalized by the student if required.

## Official checklist

| Requirement | Test and result | Evidence |
|---|---|---|
| Store a script comment as a teacher | `prof.turing` posted the exact payload to `/grades` for note 1; response 302 | `evidence/raw/teacher-save-comment.html` |
| Show the script in Alice's dashboard response | Alice login 302; dashboard 200; response contained raw `<script>alert('XSS by Eve')</script>` in the comment cell | `evidence/raw/alice-dashboard-before.html` |
| Prove it runs in a real browser | Headless Edge logged in as Alice and opened `/dashboard`; CDP observed `Page.javascriptDialogOpening`, message `XSS by Eve`; DOM had a script element | `evidence/raw/alice-browser-before.json`; screenshot 01 |
| Fix dashboard template | Removed `{% autoescape false %}`; retained `{{ n.comment }}` | `evidence/raw/after/dashboard.html`; patch |
| Fix teacher template | Removed `{% autoescape false %}`; retained `{{ n.comment }}` | `evidence/raw/after/teacher.html`; patch |
| Replay exact payload on dashboard after fix | Same comment re-saved; no dialog; cell HTML was escaped and had no script element | `evidence/raw/alice-dashboard-after.html`, `alice-browser-after.json`; screenshot 02 |
| Check teacher view after fix | Teacher page returned 200; comment escaped; Edge observed no dialog or script element | `evidence/raw/teacher-page-after.html`, `teacher-browser-after.json` |
| Normal comments still work | Saved `score < 10 on part 1 & 2, see me`; both templates showed correct text with escaped HTML source | `evidence/raw/alice-dashboard-normal.html`, `teacher-page-normal.html`, browser JSON; screenshot 04 |
| Commit both template fixes | Both root template changes reapplied from the supplied patch on `codex/class10-submission`, based on `main` at `d624cdd` | Root template diff; `class10-fix.patch` |

Screenshots 03 and 05 capture the same top-of-page teacher viewport; grade
comments are below it. They provide page context only. Teacher comment
verification comes from the corresponding raw HTML and browser JSON files.
See `SUBMISSION-NOTES.md` for corrections to the original report captions.

## Browser results

Before fix:

```json
{
  "alertObserved": true,
  "alertMessage": "XSS by Eve",
  "dom": {
    "commentHTML": "<script>alert('XSS by Eve')</script>",
    "scriptElementPresent": true
  }
}
```

After fix, on Alice's dashboard and the teacher page:

```json
{
  "alertObserved": false,
  "alertMessage": null,
  "dom": {
    "commentText": "<script>alert('XSS by Eve')</script>",
    "commentHTML": "&lt;script&gt;alert('XSS by Eve')&lt;/script&gt;",
    "scriptElementPresent": false
  }
}
```

Normal comment check:

```text
DOM text: score < 10 on part 1 & 2, see me
HTML:     score &lt; 10 on part 1 &amp; 2, see me
```

## Live service note

The actual 8080 app was rebuilt with the same two-template patch. Existing unit
tests passed (23/23), and Alice login/dashboard returned 302/200. During this
read-only dashboard check, a pre-existing comment matching
`<script>alert('XSS by Eve')</script>` was returned from the live database and was
HTML-escaped by the fixed template. Its origin is unknown. I did not write to or
alter the 8080 database. The isolated lab was the only database used for planting
the payload.

## Test environment cleanup

After evidence capture, the isolated Compose project and its disposable volume
were removed. The normal NotesApp service on port 8080 remains running.
