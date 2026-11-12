# Class 6 - Authentication, Part 1

WU YANLAN (Viclant) | Student ID: 2023905420  
Prepared 31 October 2026

[One-page English report](Authentication-Part1-Wu-Yanlan.pdf)

## 1. Aim

Understand why an unsigned JWT can expose another student's grade in the local NotesApp lab.

## 2. Before the exercise

Prediction: Not recorded in the saved notes.

## 3. Saved result

The local Part 1 script uses a teacher identity claim in an unsigned token. The saved screenshot shows a record for bob: Mathematics, grade 12.6, with the comment "Solid work, keep it up." The record ID is 3 and the student ID is 7.

![Saved grade response](evidence/response-excerpt.png)

Figure 1. Response excerpt from the saved screenshot. The response is unchanged.

## 4. Explanation

A JWT contains claims about a user. Decoding those claims does not prove who created them. In the reviewed NotesApp code, the server can accept unsigned claims as the request identity. The grade API also does not check who owns the requested record. This explains why another student's grade can be exposed.

## 5. Conclusion

I learned that the server must verify a token before trusting its identity or role. For this API, it should reject unsigned tokens and check whether the user is allowed to read the grade. The implementation of the JWT fixes belongs to the Class 7 lab.

This write-up uses the saved result and a code review; the lab was not rerun during preparation.

## References

- Kristen Pire, *Authentication Sessions JWT MFA.pdf*, PDF pages 14-17 and 24.
- [NotesApp source used for the explanation](https://github.com/Viclant/NoteApp/blob/e4a88a5a5e79f6307c99beb7b1506a2b870a4e99/web/app.py).

Original screenshot details and file hashes are in [evidence/provenance.json](evidence/provenance.json).
