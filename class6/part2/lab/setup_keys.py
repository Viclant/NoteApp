"""Create local keys once. Existing keys are never overwritten."""

from pathlib import Path
import secrets


def main():
    env_file = Path(__file__).resolve().parent / ".env"
    try:
        with env_file.open("x", encoding="utf-8") as output:
            output.write("COMMENT_ENCRYPTION_KEY=" + secrets.token_hex(32) + "\n")
            output.write("CSV_HMAC_KEY=" + secrets.token_hex(32) + "\n")
    except FileExistsError:
        print(".env already exists; kept the existing keys.")
        return
    print("Created .env with two different random keys. Keep it to read your encrypted comments.")


if __name__ == "__main__":
    main()
