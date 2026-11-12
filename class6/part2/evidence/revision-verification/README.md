# Revision verification records

The final run passed at 18:49:12 UTC+8 on 12 November 2026. See summary.json.
It used a relocated package, two fresh Docker databases, ports 8085/8086,
and the delivered Python entry points. Both temporary projects were stopped
without deleting their volumes. Existing course services were left running.

- part2/: eight actual status/body/no-Cookie checks and HMAC comparison.
- control/: fifteen unsuccessful candidates plus three strong-secret controls.
- revision-prediction.json: recorded before this verification, based on source
  and known prior results. It is not the missing original first-run prediction.
- commands.json: actual commands and outputs, including error-case checks.
- initial-attempt/: a failed clean build exposed a broken quote in the original
  control Dockerfile. The repair and successful final run are separate records.
- verify_revision.py: archived verification driver, with original host paths;
  retained as a procedure record. Repeat the experiment using the portable
  scripts/part2.py and scripts/part2-class7-control.py and the package README.

The later optional evidence-page helper check also succeeded against the
existing local 8082 lab after adding --base/--wordlist CLI options. No new
screenshot is represented as an original experiment capture.
