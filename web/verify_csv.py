"""Check a downloaded CSV against its HMAC file."""

import argparse
import os
from pathlib import Path
import sys

from csv_hmac import verify_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a CSV export using HMAC-SHA256.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("hmac_file", type=Path)
    parser.add_argument(
        "--env-file", type=Path,
        default=Path(__file__).resolve().parents[1] / ".env",
        help="Key configuration file (default: repository root .env).",
    )
    args = parser.parse_args()

    try:
        if "CSV_HMAC_KEY" not in os.environ and args.env_file.is_file():
            for line in args.env_file.read_text(encoding="utf-8-sig").splitlines():
                name, separator, value = line.strip().partition("=")
                if separator and name.strip() == "CSV_HMAC_KEY":
                    os.environ["CSV_HMAC_KEY"] = value.strip().strip("\"'")
                    break

        csv_bytes = args.csv_file.read_bytes()
        signature = args.hmac_file.read_text(encoding="ascii")
        valid = verify_csv(csv_bytes, signature)
    except (OSError, ValueError) as error:
        print(f"Verification error: {error}", file=sys.stderr)
        return 2

    if valid:
        print("PASS: CSV HMAC matches.")
        return 0
    print("FAIL: CSV HMAC does not match.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
