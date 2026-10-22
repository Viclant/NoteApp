"""Login and upgrade-on-login checks with Argon2 and an in-memory database."""

import unittest
from unittest.mock import patch

from argon2 import PasswordHasher

import app as notesapp


class PasswordDatabase:
    def __init__(self, password):
        self.user = {"id": 1, "username": "alice", "role": "student", "password": password}
        self.password_updates = []
        self.created_users = []

    def cursor(self):
        return self

    def execute(self, query, params=None):
        if query.startswith("SELECT "):
            return
        if query.startswith("UPDATE users SET password"):
            password, user_id = params
            if user_id != self.user["id"]:
                raise AssertionError("Password update used the wrong user ID")
            self.user["password"] = password
            self.password_updates.append(password)
            return
        if query.startswith("INSERT INTO users"):
            self.created_users.append(params)
            return
        raise AssertionError(f"Unexpected query: {query}")

    def fetchone(self):
        return self.user.copy()

    def close(self):
        pass


class PasswordTests(unittest.TestCase):
    def setUp(self):
        self.database = PasswordDatabase("alicepw")
        self.hasher = PasswordHasher()
        for change in (
            patch.object(notesapp, "get_db", return_value=self.database),
            patch.object(notesapp, "log"),
            patch.dict(notesapp.app.config, {"TESTING": True}),
        ):
            change.start()
            self.addCleanup(change.stop)
        self.client = notesapp.app.test_client()

    def login(self, password):
        return self.client.post("/login", data={"username": "alice", "password": password})

    def assert_logged_in(self, response):
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], self.database.user["id"])

    def assert_rejected(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid credentials.", response.data)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_wrong_legacy_password_does_not_upgrade(self):
        self.assert_rejected(self.login("wrong-password"))
        self.assertEqual(self.database.user["password"], "alicepw")
        self.assertEqual(self.database.password_updates, [])

    def test_correct_legacy_password_upgrades_to_argon2(self):
        self.assert_logged_in(self.login("alicepw"))
        stored = self.database.user["password"]
        self.assertTrue(stored.startswith("$argon2id$"))
        self.assertTrue(self.hasher.verify(stored, "alicepw"))
        self.assertEqual(len(self.database.password_updates), 1)

    def test_second_login_verifies_without_rewriting_hash(self):
        self.assert_logged_in(self.login("alicepw"))
        first_hash = self.database.user["password"]
        self.client.get("/logout")
        self.assert_logged_in(self.login("alicepw"))
        self.assertEqual(self.database.user["password"], first_hash)
        self.assertEqual(len(self.database.password_updates), 1)

    def test_wrong_password_for_argon2_account_is_rejected(self):
        stored = self.hasher.hash("alicepw")
        self.database.user["password"] = stored
        self.assert_rejected(self.login("wrong-password"))
        self.assertEqual(self.database.user["password"], stored)
        self.assertEqual(self.database.password_updates, [])

    def test_old_argon2_parameters_are_refreshed_after_login(self):
        old_hasher = PasswordHasher(time_cost=2, memory_cost=8192, parallelism=1)
        stored = old_hasher.hash("alicepw")
        self.database.user["password"] = stored
        self.assert_logged_in(self.login("alicepw"))
        updated = self.database.user["password"]
        self.assertNotEqual(updated, stored)
        self.assertTrue(self.hasher.verify(updated, "alicepw"))
        self.assertFalse(self.hasher.check_needs_rehash(updated))

    def test_malformed_argon2_is_rejected_without_server_error(self):
        for stored in (
            "$argon2id$broken",
            "$argon2id$v=19$m=65536,t=3,p=4$bad$bad",
        ):
            with self.subTest(stored=stored):
                self.database.user["password"] = stored
                self.assert_rejected(self.login("alicepw"))
                self.assertEqual(self.database.user["password"], stored)
                self.assertEqual(self.database.password_updates, [])

    def test_new_user_password_is_stored_as_argon2(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["role"] = "admin"
        response = self.client.post("/admin/users", data={
            "action": "create", "username": "new.student",
            "password": "new-password", "role": "student",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.database.created_users), 1)
        username, stored, role, teacher_id = self.database.created_users[0]
        self.assertEqual((username, role, teacher_id), ("new.student", "student", None))
        self.assertTrue(stored.startswith("$argon2id$"))
        self.assertTrue(self.hasher.verify(stored, "new-password"))


if __name__ == "__main__":
    unittest.main()
