# Optional strong-secret comparison instance

This directory is the runnable source for the completed submission, not an unfinished handoff.
See `../README.md` for the portable scripts, independent project names, evidence and cleanup.
Default HTTP port: 8083. Set CONTROL_PORT to override it.

```powershell
python setup_keys.py
docker compose up -d --build
```

Stop with `docker compose down` to keep the data volume. Retain the generated `.env`
with its volume; it is deliberately excluded from the submitted files.
The Class 8 ownership check remains in the source. Both instances reject alg:none.
The signing key is a fresh 64-hex-character value generated locally as CONTROL_JWT_SECRET. It is not the classroom key.
