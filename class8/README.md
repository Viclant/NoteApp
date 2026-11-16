# Class 8 — NotesApp access control

Wu Yanlan · 16 November 2026

## Before the fix

I used an automated HTTP test on my local copy of NotesApp. On the [version before the fix](https://github.com/Viclant/NoteApp/commit/08beb32dcd08e2a1a837877a120651959d31c160), the test logged in normally as `alice` and asked for note 3. `GET /api/notes/3` returned **HTTP 200**, Bob's Mathematics grade **12.6**, and the comment “Solid work, keep it up.” The app checked that Alice was logged in and then returned the note without checking who owned it.

## After the fix

The fix in `api_notes` compares the note's `student_id` with the logged-in user's ID. Teachers and admins can still read other students' notes. For a student asking for someone else's note, the response is **404 `not found`**. That response keeps the existence of the note hidden from the student. [Fixed handler](https://github.com/Viclant/NoteApp/blob/6231c039a9346d3f59756c321c4ce4156aae84be/web/app.py#L256-L282)

- `alice` → `GET /api/notes/3` → **HTTP 404**, `{"error":"not found"}`.
- `alice` → `GET /api/notes/1` → **HTTP 200**, Alice's Mathematics grade **16.2**.
- `prof.turing` → `GET /api/notes/3` → **HTTP 200**, Bob's Mathematics grade **12.6** and the same comment. The test signed in normally as `prof.turing` and reached `/teacher` before making the request.

I used a fresh database with the course's demo data for each version and a fresh login session for each account. [Recorded HTTP results](results.json)

[Lab hand-in requirements](https://github.com/KristenPire/epita-security-labs/blob/main/docs/class8/read-anyones-grade.md#what-you-hand-in)
