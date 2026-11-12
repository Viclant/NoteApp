# Class 6 - JWT Part 2 submission

WU YANLAN | Student ID 2023905420

Start with `FINDING.txt` (the teacher's short finding) or
`Authentication-Part2-Wu-Yanlan.pdf` (three-page report with three original screenshots).
`REQUIREMENTS-CHECK.md` maps the exercise requirements. `TEST-RESULTS.md` records the checks.

## Repeat the local lab

Run the commands from this extracted submission folder. Python 3.10+ and Docker Compose
are required. The example uses ports 8085/8086 to avoid the older local exercises.
The source remains a classroom lab with its public weak key; the control is a separate
strong-secret comparison, not a claim that every teaching-app issue has been fixed.

```powershell
$env:PART2_PORT = "8085"
Push-Location .\lab
python setup_keys.py
docker compose up -d --build
Pop-Location
python .\scripts\part2.py --base http://127.0.0.1:8085 --out .\evidence\reruns\my-run
```

The default wordlist is found relative to the script's package root, regardless of the
working directory. Omitting `--out` creates a unique timestamped directory under
`evidence/reruns/`. An existing result or transcript will not be overwritten.
The script logs in only as Alice and matches HMAC signatures against the course list.
All eight API checks verify status, response content and absence of a Cookie header.

## Optional strong-secret comparison

```powershell
$env:CONTROL_PORT = "8086"
Push-Location .\class7-control
python setup_keys.py
docker compose up -d --build
Pop-Location
python .\scripts\part2-class7-control.py --base http://127.0.0.1:8086 --part2-results .\evidence\reruns\my-run\part2-results.json --out .\evidence\reruns\my-run
```

`class7-control/setup_keys.py` generates CONTROL_JWT_SECRET plus the encryption/HMAC
keys in its local `.env`, retaining existing values. The control script reads that
file by default for its mandatory positive control, or accepts `--secret-file` or
CONTROL_JWT_SECRET from the environment. It never prints or saves that private key.
The recovery script does not read this key. Missing inputs or checks cannot produce PASS.

## Stop both copies, retaining data

```powershell
Push-Location .\lab
docker compose down
Pop-Location
Push-Location .\class7-control
docker compose down
Pop-Location
```

Keep each generated `.env` with its data volume: encrypted comments need the same key
on the next start. No generated `.env` or database data is included in the submission.

## Evidence and dates

- Original final run: `evidence/part2-results.json`, 18:17:28 UTC+8, 8/8 passed,
  candidate 8 of 15 was `s3cr3t`, 0.0004 s. The 6-character spelling is intentional.
- Original images 01-10, raw transcripts and curl capture commands are unchanged.
  Auxiliary older captures may show another timing sample; they are not revision images.
- Revision: `evidence/revision-verification/summary.json`, fresh relocated stacks on
  8085/8086, 8/8 Part 2, 3/3 strong-secret control, 4/4 error checks, cleanup passed.
- `references/part1/` is historical reference only. Part 1 was not repeated.
- `scripts/cdp_shot.py` and `capture-terminal.ps1` are optional Windows capture helpers.
  The archived `.cmd` files in evidence retain their original machine paths; use the
  portable Python entry points above to repeat the experiment.
- Optional live page: `python scripts/part2-evidence-server.py --base http://127.0.0.1:8085 --port 8099`.
  It makes real requests when opened; it does not replay saved JSON as a live result.
- `manifest.json` lists file sizes and SHA-256, excluding itself, caches and local keys.

Run `python scripts/verify_manifest.py` to check the submitted files without starting
Docker. The verification-driver sources under evidence are archived procedure records;
their recorded host paths are not used by the portable entry points in scripts/.

The original run did not save a separate Part 2 prediction. The report labels the
assistant's recorded pre-verification prediction as a later revision prediction.
GitHub hand-in: https://github.com/Viclant/NoteApp/tree/main/class6/part2
No separate course-platform submission is recorded.
