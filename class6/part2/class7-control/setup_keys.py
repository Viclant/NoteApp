"""Create local keys once. Existing keys are never overwritten."""

from pathlib import Path
import secrets


def main():
    env_file = Path(__file__).resolve().parent / ".env"
    existing = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    names = {line.partition("=")[0] for line in existing.splitlines() if "=" in line}
    missing = [name for name in ("COMMENT_ENCRYPTION_KEY", "CSV_HMAC_KEY", "CONTROL_JWT_SECRET") if name not in names]
    if not missing:
        print(".env already has all keys; kept the existing values.")
        return
    with env_file.open("a", encoding="utf-8") as output:
        if existing and not existing.endswith("\n"):
            output.write("\n")
        for name in missing:
            output.write(name + "=" + secrets.token_hex(32) + "\n")
    print("Created missing local keys without replacing existing keys. Keep .env with this control instance.")


if __name__ == "__main__":
    main()
