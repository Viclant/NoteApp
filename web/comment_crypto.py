"""AES-GCM encryption for comments stored in PostgreSQL."""

import base64
import os
import re

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ENCRYPTED_PREFIX = "aesgcm:v1:"


def load_comment_key():
    key_hex = os.environ.get("COMMENT_ENCRYPTION_KEY", "")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key_hex):
        raise ValueError("COMMENT_ENCRYPTION_KEY must contain 64 hexadecimal characters. Run setup_keys.py first.")
    return bytes.fromhex(key_hex)


def encrypt_comment(comment):
    if comment is None:
        return None
    nonce = os.urandom(12)
    ciphertext = AESGCM(load_comment_key()).encrypt(nonce, comment.encode("utf-8"), None)
    # AESGCM includes the authentication tag in ciphertext.
    return ENCRYPTED_PREFIX + base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_comment(value):
    if value is None:
        return None
    if not value.startswith(ENCRYPTED_PREFIX):
        raise ValueError("Comment is not encrypted. Run the comment migration first.")
    data = base64.b64decode(value[len(ENCRYPTED_PREFIX):], validate=True)
    if len(data) < 28:
        raise ValueError("Encrypted comment is too short.")
    plaintext = AESGCM(load_comment_key()).decrypt(data[:12], data[12:], None)
    return plaintext.decode("utf-8")
