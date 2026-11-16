# Class 8 — NotesApp access control

Verification run on 16 November 2026 using the course's seeded demo accounts and grades.

## Before the fix

At [`08beb32d`](https://github.com/Viclant/NoteApp/commit/08beb32dcd08e2a1a837877a120651959d31c160), the test logged in as `alice` through `POST /login`. With that student session, `GET /api/notes/3` returned **HTTP 200** and Bob's Mathematics grade **12.6**, with the comment “Solid work, keep it up.” The handler accepted a valid student session and returned the requested note without checking its owner.

## After the fix

At [`6231c039`](https://github.com/Viclant/NoteApp/commit/6231c039a9346d3f59756c321c4ce4156aae84be), [`api_notes`](https://github.com/Viclant/NoteApp/blob/6231c039a9346d3f59756c321c4ce4156aae84be/web/app.py#L256-L282) checks the note owner against the caller. A student requesting another student's note receives HTTP 404. Teachers and admins can still read the note.

- `alice` → `GET /api/notes/3` → **HTTP 404**, `{"error":"not found"}`.
- `alice` → `GET /api/notes/1` → **HTTP 200**, Alice's Mathematics grade **16.2**.
- `prof.turing` → `GET /api/notes/3` → **HTTP 200**, Bob's Mathematics grade **12.6**, with the comment “Solid work, keep it up.” The teacher logged in through `POST /login` and reached `/teacher` before the API request.

Each revision ran locally over HTTP on loopback using Python 3.10.6 and a freshly seeded PostgreSQL 18.3 database. Each account used a fresh login session. An unauthenticated request to the same endpoint returned HTTP 401 on both revisions.

[Recorded HTTP results](results.json) · [Lab hand-in requirements](https://github.com/KristenPire/epita-security-labs/blob/main/docs/class8/read-anyones-grade.md#what-you-hand-in)
