"""Verify the submission's listed file sizes and SHA-256 values (stdlib only)."""
from pathlib import Path
import hashlib
import json


def main():
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8-sig"))
    failures = []
    for name, expected in manifest["files"].items():
        path = root / name
        if (not path.is_file() or path.stat().st_size != expected["bytes"]
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]):
            failures.append(name)
    if failures:
        print("FAIL: " + ", ".join(failures))
        return 1
    print(f"PASS: {len(manifest['files'])} listed files match their sizes and SHA-256 values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
