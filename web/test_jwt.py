"""Class 7 JWT regression checks; no database or real signing key is needed."""

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import app as notesapp


TEST_SECRET = "class7-unit-test-signing-key-with-at-least-32-characters"
ALICE = {"user_id": 6, "username": "alice", "role": "student"}
TEACHER = {"user_id": 6, "username": "alice", "role": "teacher"}


def encode_bytes(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def encode_json(value):
    return encode_bytes(json.dumps(value, separators=(",", ":")).encode("utf-8"))


def sign_parts(header_part, payload_part, secret=TEST_SECRET):
    """Independently sign test input, including intentionally invalid JSON shapes."""
    message = f"{header_part}.{payload_part}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{encode_bytes(signature)}"


def signed_token(header, payload, secret=TEST_SECRET):
    return sign_parts(encode_json(header), encode_json(payload), secret)


class JWTTests(unittest.TestCase):
    def setUp(self):
        key_patch = patch.object(notesapp, "JWT_SECRET", TEST_SECRET)
        key_patch.start()
        self.addCleanup(key_patch.stop)

    def test_app_issued_token_round_trip(self):
        token = notesapp.make_jwt(ALICE.copy())
        self.assertEqual(notesapp.verify_jwt(token), ALICE)

    def test_independently_signed_hs256_token_is_accepted(self):
        token = signed_token({"alg": "HS256", "typ": "JWT"}, ALICE)
        self.assertEqual(notesapp.verify_jwt(token), ALICE)

    def test_none_cannot_be_revived_by_old_environment_switch(self):
        token = f"{encode_json({'alg': 'none', 'typ': 'JWT'})}.{encode_json(TEACHER)}."
        with patch.dict(os.environ, {"JWT_ALLOW_NONE": "true"}), patch.object(
            notesapp, "JWT_ALLOW_NONE", True, create=True
        ):
            self.assertIsNone(notesapp.verify_jwt(token))

    def test_old_public_weak_key_teacher_forgery_is_rejected(self):
        token = signed_token({"alg": "HS256", "typ": "JWT"}, TEACHER, "s3cr3t")
        self.assertIsNone(notesapp.verify_jwt(token))

    def test_algorithm_must_be_exactly_hs256(self):
        for algorithm in ("hs256", "Hs256", "HS256 ", "HS384", "none", "", None, 256, []):
            with self.subTest(algorithm=algorithm):
                token = signed_token({"alg": algorithm, "typ": "JWT"}, ALICE)
                self.assertIsNone(notesapp.verify_jwt(token))
        self.assertIsNone(notesapp.verify_jwt(signed_token({"typ": "JWT"}, ALICE)))

    def test_non_object_header_and_payload_are_rejected(self):
        for value in (None, [], "text", 123, True):
            with self.subTest(position="header", value=value):
                self.assertIsNone(notesapp.verify_jwt(signed_token(value, ALICE)))
            with self.subTest(position="payload", value=value):
                token = signed_token({"alg": "HS256", "typ": "JWT"}, value)
                self.assertIsNone(notesapp.verify_jwt(token))

    def test_malformed_base64_json_and_utf8_are_rejected(self):
        header = encode_json({"alg": "HS256", "typ": "JWT"})
        payload = encode_json(ALICE)
        tokens = (
            "", "one.two", "one.two.three.four", "..",
            f"a.{payload}.signature", f"{header}.a.signature",
            sign_parts(encode_bytes(b"not json"), payload),
            sign_parts(header, encode_bytes(b"not json")),
            sign_parts(encode_bytes(b"\xff"), payload),
            sign_parts(header, encode_bytes(b"\xff")),
        )
        for index, token in enumerate(tokens):
            with self.subTest(case=index):
                self.assertIsNone(notesapp.verify_jwt(token))

    def test_empty_and_non_ascii_signatures_are_rejected(self):
        header, payload, _ = notesapp.make_jwt(ALICE.copy()).split(".")
        for signature in ("", "not-a-signature", "签名", "\u00e9"):
            with self.subTest(signature=signature):
                self.assertIsNone(notesapp.verify_jwt(f"{header}.{payload}.{signature}"))

    def test_changed_payload_and_signature_are_rejected(self):
        header, payload, signature = notesapp.make_jwt(ALICE.copy()).split(".")
        self.assertIsNone(notesapp.verify_jwt(f"{header}.{encode_json(TEACHER)}.{signature}"))
        changed = ("A" if signature[0] != "A" else "B") + signature[1:]
        self.assertIsNone(notesapp.verify_jwt(f"{header}.{payload}.{changed}"))

    def test_invalid_bearer_does_not_fall_back_to_valid_session(self):
        client = notesapp.app.test_client()
        with client.session_transaction() as session:
            session.update(ALICE)
        tokens = (
            "broken-token",
            signed_token({"alg": "HS256", "typ": "JWT"}, TEACHER, "s3cr3t"),
            f"{encode_json({'alg': 'none'})}.{encode_json(TEACHER)}.",
        )
        with patch.object(notesapp, "get_db") as database:
            for index, token in enumerate(tokens):
                with self.subTest(case=index):
                    response = client.get("/api/notes/1", headers={"Authorization": "Bearer " + token})
                    self.assertEqual(response.status_code, 401)
                    self.assertEqual(response.get_json(), {"error": "unauthorized"})
            database.assert_not_called()

    def test_session_without_bearer_still_reads_own_note(self):
        client = notesapp.app.test_client()
        with client.session_transaction() as session:
            session.update(ALICE)
        note = {"id": 1, "student_id": 6, "class_id": 1, "grade": 16.2,
                "comment": "Good work", "student": "alice", "class_name": "Mathematics"}
        with patch.object(notesapp, "get_db") as database, patch.object(
            notesapp, "decrypt_comment", side_effect=lambda value: value
        ):
            database.return_value.cursor.return_value.fetchone.return_value = note
            response = client.get("/api/notes/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["student_id"], 6)

    def test_missing_and_blank_signing_secret_prevent_startup(self):
        environment = os.environ.copy()
        environment["JWT_SECRET"] = TEST_SECRET
        command = [sys.executable, "-c", "import app"]
        options = {"cwd": str(Path(__file__).resolve().parent), "capture_output": True,
                   "text": True, "timeout": 20}
        control = subprocess.run(command, env=environment, **options)
        self.assertEqual(control.returncode, 0, "App import failed even with a valid test secret")
        for value in (None, "", "   "):
            with self.subTest(value=value):
                if value is None:
                    environment.pop("JWT_SECRET", None)
                else:
                    environment["JWT_SECRET"] = value
                result = subprocess.run(command, env=environment, **options)
                self.assertNotEqual(result.returncode, 0, "Missing signing secret was accepted")
                self.assertIn("JWT_SECRET", result.stderr)


if __name__ == "__main__":
    unittest.main()
