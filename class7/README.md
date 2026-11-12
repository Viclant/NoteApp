# Class 7 - Fix the login

Name: WU YANLAN<br/>
Student ID: 2023905420<br/>
Date: 12 November 2026

Before the fix, NotesApp accepted an unsigned teacher token and used the weak
signing key `s3cr3t`. Both test tokens could read Bob's Mathematics grade, 12.6,
at `/api/notes/3`.

With Codex's help, I changed `verify_jwt` to accept only `HS256` and check the
signature with `hmac.compare_digest`. `JWT_SECRET` is now required from the
environment, with no default value. A new random 32-byte key was generated in
`.env`. Invalid Bearer tokens are also rejected when a browser session is present.

After rebuilding the app, the results were:

- `alg:none` token: HTTP 401, `unauthorized`.
- Token signed with `s3cr3t`: HTTP 401, `unauthorized`.
- Normal Alice login: worked. Her own note returned HTTP 200, with grade 16.2.

Rejecting `none` stops the first token. The second token fails because its
signature was made with the old key. A fresh token from a normal login still
works with the new key.

Codex automated the local checks. The old test tokens were recreated for these
checks, and the JWT requests used no cookies. The real key is kept out of Git.
In production, it should come from a secrets store rather than a committed file.

[Audit line](Audit.txt) · [Fixed function](fixed-verify_jwt.py) · [Test notes](TESTING.md)
