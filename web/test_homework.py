"""Small checks for the C3 encryption and C4 CSV signature."""

import base64
import os
import secrets
import unittest
from unittest.mock import patch

from cryptography.exceptions import InvalidTag

from comment_crypto import ENCRYPTED_PREFIX, decrypt_comment, encrypt_comment
from csv_hmac import sign_csv, verify_csv


class HomeworkTests(unittest.TestCase):
    def setUp(self):
        keys = {
            "COMMENT_ENCRYPTION_KEY": secrets.token_hex(32),
            "CSV_HMAC_KEY": secrets.token_hex(32),
        }
        self.key_patch = patch.dict(os.environ, keys)
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)

    def test_comment_round_trip_and_different_nonces(self):
        for comment in ("", "Good work", "评语\nSecond line", "<b>Good</b>"):
            first = encrypt_comment(comment)
            second = encrypt_comment(comment)
            self.assertNotEqual(first, second)
            self.assertEqual(decrypt_comment(first), comment)
            self.assertEqual(decrypt_comment(second), comment)
        self.assertIsNone(decrypt_comment(encrypt_comment(None)))

    def test_changed_comment_and_wrong_key_are_rejected(self):
        encrypted = encrypt_comment("Good work")
        original = base64.b64decode(encrypted[len(ENCRYPTED_PREFIX):])
        for position in (0, 12, len(original) - 1):
            changed = bytearray(original)
            changed[position] ^= 1
            damaged = ENCRYPTED_PREFIX + base64.b64encode(changed).decode("ascii")
            with self.assertRaises(InvalidTag):
                decrypt_comment(damaged)
        with patch.dict(os.environ, {"COMMENT_ENCRYPTION_KEY": secrets.token_hex(32)}):
            with self.assertRaises(InvalidTag):
                decrypt_comment(encrypted)

    def test_csv_changes_are_rejected(self):
        data = b"student,grade\r\nalice,14\r\n"
        signature = sign_csv(data)
        self.assertTrue(verify_csv(data, signature))
        self.assertFalse(verify_csv(data.replace(b"14", b"18"), signature))
        self.assertFalse(verify_csv(data.replace(b"\r\n", b"\n"), signature))
        self.assertFalse(verify_csv(data, "not a signature"))
        with patch.dict(os.environ, {"CSV_HMAC_KEY": secrets.token_hex(32)}):
            self.assertFalse(verify_csv(data, signature))

    def test_invalid_keys_are_rejected(self):
        for value in ("", "not-hex", "ab" * 16):
            with patch.dict(os.environ, {"COMMENT_ENCRYPTION_KEY": value, "CSV_HMAC_KEY": value}):
                with self.assertRaises(ValueError):
                    encrypt_comment("Good work")
                with self.assertRaises(ValueError):
                    sign_csv(b"student,grade\n")


if __name__ == "__main__":
    unittest.main()
