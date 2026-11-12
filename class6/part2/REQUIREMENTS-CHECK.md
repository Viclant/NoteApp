# Class 6 Part 2 - requirement check

Official source: https://github.com/KristenPire/epita-security-labs/blob/main/docs/class6/forge-a-token.md

- [x] Use only the local NotesApp clone and synthetic accounts/data.
- [x] Read Alice's real signed JWT; identify role=student and Base64url encoding, not encryption.
- [x] Compute candidate HMAC-SHA256 signatures over header.payload; match candidate 8, s3cr3t.
- [x] Sign a new HS256 teacher token with the recovered key.
- [x] Read Bob note 3: Mathematics 12.6 and "Solid work, keep it up.".
- [x] Explain why rejecting none does not stop a valid signature made with a guessed key.
- [x] Answer the random 32-character-key question without inventing a brute-force timing.
- [x] Provide the teacher's short finding in FINDING.txt and at the start of the report.
- [x] Distinguish historical Part 1 from this Part 2 run; keep the prior report as a reference.
- [x] Keep Class 8 authorization, use no Cookie on the API control matrix and retain negative controls.
- [x] Make portable scripts and runnable Compose sources; verify from a relocated copy.
- [x] Complete and record cleanup of the independent verification stacks without deleting volumes.
- [x] Preserve original captures/results and label new verification evidence separately.
- [x] Include a genuine prediction before the revision verification, with source and timestamp.

Historical limitation: the original first run has no saved separate prediction. The new
assistant prediction follows source/prior-result review and is explicitly a revision record;
it does not retroactively satisfy a first-run classroom prediction. No prior event is invented.
The optional brute-force extension was not run; its absence is not a missing core Part 2 result.
The public exercise does not provide a numeric scoring rubric.
