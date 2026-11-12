# Part 2 - recorded test results

All times are UTC+8 on 12 November 2026.

## Original final run

18:17:28, local port 8082. All 8 HTTP statuses matched. Actual Bob response: Mathematics, grade 12.6, comment "Solid work, keep it up.". The course list has 15 candidates; candidate 8 matched in 0.0004 s. See evidence/part2-results.json.

## Revision verification

18:48:51-18:49:12, copied to a different directory, with fresh isolated databases on 8085/8086. Default wordlist discovery was exercised from outside the package. Original evidence was not overwritten.

- No credentials -> Bob note 3: 401 - PASS (status, body and no-Cookie checked).

- Unsigned alg:none -> Bob note 3: 401 - PASS (status, body and no-Cookie checked).

- Real Alice token -> own note 1: 200; grade 16.2 - PASS (status, body and no-Cookie checked).

- Real Alice token -> Bob note 3: 404 - PASS (status, body and no-Cookie checked).

- Recovered-key teacher token -> Bob note 3: 200; grade 12.6 - PASS (status, body and no-Cookie checked).

- Tampered signature -> Bob note 3: 401 - PASS (status, body and no-Cookie checked).

- Recovered-key student token -> Bob note 3: 404 - PASS (status, body and no-Cookie checked).

- Wrong signing key -> Bob note 3: 401 - PASS (status, body and no-Cookie checked).



Strong-secret comparison: 15 candidates tried, no match. Old classroom-key token -> 401; unsigned -> 401; valid token signed with the actual private control key -> 200 and Bob's grade/comment. 3/3 PASS.

Error checks: missing wordlist, empty wordlist, missing positive-control key and existing output each returned a nonzero exit code. 4/4 PASS.

Live evidence page: real local requests and relative wordlist discovery PASS.

## Cleanup

Both jwt-part2-review-final-weak and jwt-part2-review-final-control were stopped with docker compose down, without -v. No containers remain for these projects; their volumes are retained. Existing 8080/8082/8083 services were not stopped.

## Problems repaired

The first revision attempt exposed an unterminated quote in the supplied control Dockerfile. It was repaired using the identical teaching image definition; the final clean build and tests passed. Initial-attempt logs remain under evidence/revision-verification/initial-attempt/.

Fixed package-relative paths, output overwrite protection, response-body assertions, required positive control, empty-input errors, old README claims, cookie wording and inconsistent timing. The control key is now generated locally instead of embedded in Compose.

## Not executed

Part 1 was not rerun. No long brute-force attack or measured full-keyspace duration is claimed. The 32-character-key discussion is theoretical. Original screenshots were retained rather than represented as new revision captures.

## Verification files

evidence/revision-verification/summary.json; part2/part2-results.json; control/class7-control.json; commands.json. These contain actual outputs and source/container hashes.
