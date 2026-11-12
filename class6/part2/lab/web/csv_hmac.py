"""HMAC-SHA256 for the exact bytes of a CSV export."""

import hashlib
import hmac
import os
import re


def sign_csv(csv_bytes: bytes) -> str:
    key_hex = os.environ.get("CSV_HMAC_KEY")
    if not key_hex:
        raise ValueError("CSV_HMAC_KEY is missing; set it in the environment or root .env.")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key_hex):
        raise ValueError("CSV_HMAC_KEY must contain exactly 64 hexadecimal characters (32 bytes).")

    key = bytes.fromhex(key_hex)
    return hmac.new(key, csv_bytes, hashlib.sha256).hexdigest()


def verify_csv(csv_bytes: bytes, signature: str) -> bool:
    expected = sign_csv(csv_bytes)
    signature = signature.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", signature):
        return False
    return hmac.compare_digest(expected, signature.lower())
