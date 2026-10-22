# NotesApp

A small grades application used throughout the Computer Security course. Teachers
record grades and comments for their classes, students read their own grades, and an
admin manages users and classes.

## Student information

- Student ID: 2023905420
- Name: WU YANLAN
- English name: Viclant

## Run it

You need Docker with the Compose plugin.

```
git clone https://github.com/Viclant/NoteApp.git notesapp
cd notesapp
python setup_keys.py
docker compose up --build
```

The first start builds the image, launches PostgreSQL, and loads the seed data
automatically. When it is ready, open:

```
http://localhost:8080
```

`setup_keys.py` creates `.env` with two random keys. It leaves an existing `.env`
unchanged. Keep this file when restarting: existing encrypted comments need the
same key. `.env` is ignored by Git. `.env.example` lists the two variable names.

## Test accounts

| Role    | Username      | Password   |
|---------|---------------|------------|
| Student | `alice`       | `alicepw`  |
| Teacher | `prof.turing` | `teach123` |
| Admin   | `admin`       | `admin123` |

(There are ~30 students in total; each student's password is their username + `pw`,
e.g. `bob` / `bobpw`.)

## Stack

- Python 3.11 + Flask (server-rendered Jinja2 pages and a small JSON API)
- PostgreSQL 15
- Docker Compose (`web` and `db` services)

## C3: encrypted comments

Comments use AES-GCM before they are saved in PostgreSQL. Each write gets a fresh
12-byte random nonce. The database stores `aesgcm:v1:` followed by Base64 of the
nonce and ciphertext, including its authentication tag.

On startup, the app encrypts the old comments in one transaction. Running it again
keeps existing ciphertext unchanged and checks that the key can still decrypt it.
The student page, teacher page, grade API and CSV export decrypt comments for use.

To check the database after startup:

```
docker compose exec db psql -U notesapp -d notesapp -c "SELECT id, comment FROM notes LIMIT 3;"
```

The comments should start with `aesgcm:v1:`. In the browser, the original comments
should still be readable. Save a new comment as a teacher and check both places.

## C4: HMAC-signed CSV export

The teacher page has an **export CSV + HMAC** link for each class. It downloads a
ZIP containing `grades.csv` and `grades.csv.hmac`. The HMAC uses SHA-256 and the
exact UTF-8 bytes of the CSV, with a separate key from comment encryption.
The original CSV link also includes an `X-CSV-HMAC-SHA256` response header.

Extract the ZIP into a folder called `export`, then check it from the project root:

```
python web/verify_csv.py export/grades.csv export/grades.csv.hmac
```

It should print `PASS`. Change a grade in the CSV without changing the HMAC file,
then run it again: it should print `FAIL`. The verifier reads the local `.env`, or
uses `CSV_HMAC_KEY` from the environment if it is already set.

To run the small encryption and HMAC tests:

```
docker compose exec web python -m unittest test_homework -v
```

## Reset

```
docker compose down -v   # wipes the database volume
docker compose up        # reloads the seed data
```

## Updating your fork

The course repository is sometimes updated. Your fork does **not** update by itself.
To pull the latest changes into your fork:

**Easiest (GitHub website):** open your fork, and if it says *"This branch is behind
KristenPire/NoteApp"*, click **Sync fork → Update branch**. Then, in your local clone:

```
git pull
```

**Command line (keeps your own commits):**

```
git remote add upstream https://github.com/KristenPire/NoteApp.git   # once
git fetch upstream
git merge upstream/main
git push
```

Then **rebuild**, because the app code is baked into the Docker image:

```
docker compose up --build
```

A plain `docker compose up` would keep running the old image.
