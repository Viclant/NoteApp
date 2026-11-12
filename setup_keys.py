"""Fill missing local keys, preserving every existing nonempty key."""

from pathlib import Path
import secrets


def main():
    env_file = Path(__file__).resolve().parent / ".env"
    existing = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    lines = existing.splitlines()
    values = {}
    for line in lines:
        name, separator, value = line.partition("=")
        if separator and not line.lstrip().startswith("#"):
            values[name.strip()] = value.strip().strip("\"'")
    names = ("COMMENT_ENCRYPTION_KEY", "CSV_HMAC_KEY", "JWT_SECRET")
    missing = {name: secrets.token_hex(32) for name in names if not values.get(name)}
    if not missing:
        print("All three keys are already set; kept the existing .env.")
        return
    updated = set()
    for index, line in enumerate(lines):
        name, separator, _ = line.partition("=")
        name = name.strip()
        if separator and name in missing:
            lines[index] = name + "=" + missing[name]
            updated.add(name)
    lines.extend(name + "=" + missing[name] for name in names if name in missing and name not in updated)
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Added missing keys: " + ", ".join(name for name in names if name in missing))
    print("Existing keys were kept. Keep .env to read your encrypted comments.")


if __name__ == "__main__":
    main()
