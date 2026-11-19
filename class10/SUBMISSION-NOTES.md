# Submission verification — 19 November 2026

The submission branch `codex/class10-submission` starts from `main` at `d624cdd`.
The supplied `class10-fix.patch` passed `git apply --check` and was applied to
`web/templates/dashboard.html` and `web/templates/teacher.html` in the repository
root. Other coursework commits were not included.

All 38 entries in the source package's SHA-256 manifest matched before copying.
The original package remains unchanged. This submission copy redacts the embedded
isolated-lab JWT from the three Alice dashboard raw HTML files. The comment
evidence in those files is preserved. `MANIFEST.sha256` hashes the final files
relative to this `class10/` directory, excluding the manifest itself. Local
attributes preserve these file bytes across Windows and Linux checkouts.

## Evidence-caption correction

Teacher screenshots 03 and 05 are identical captures of the top of the teacher
page. The grade-comment cells are below their viewport. References in the
original PDF, HTML, and Markdown report to these images showing a teacher comment
should be read as page context only. Verification of teacher comments is recorded
in `evidence/raw/teacher-page-after.html`, `teacher-page-normal.html`,
`teacher-browser-after.json`, and `teacher-browser-normal.json`. The requirements
checklist reflects this distinction. The original report files are retained.

The report's `f0b04cd` reference identifies the original local lab fix. The
submitted branch contains the same template changes as a new commit based on
`main`.

## Checks on this submission

- Existing unit suite: 23 tests passed (`python -m unittest discover -s . -p
  'test_*.py' -v`, from `web/`, using a temporary test signing secret).
- Four offline checks rendered both actual root templates with the lesson script
  and a normal comment containing `<`, `>`, and `&`. Comment text was preserved,
  HTML metacharacters were escaped, and neither comment cell contained a script
  element.
- The new offline checks did not use a database or a browser login. Browser
  evidence in the package comes from the original isolated lab.

Machine-readable results: `evidence/submission-verification.json`.
