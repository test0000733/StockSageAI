import unittest
from unittest.mock import patch, MagicMock
import streamlit as st

from StockSageAI import auth as auth_module


class AuthManagerTests(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()
        self.mock_db = MagicMock()
        self.mock_db.hash_password.return_value = "hashed"
        self.mock_db.verify_password.return_value = True

        self.database_patcher = patch.object(auth_module, "Database", return_value=self.mock_db)
        self.database_patcher.start()

        self.auth_manager = auth_module.AuthManager()

    def tearDown(self):
        self.database_patcher.stop()
        st.session_state.clear()

    def test_defaults_initialize_session_state(self):
        self.assertFalse(st.session_state.authenticated)
        self.assertIsNone(st.session_state.user)
        self.assertEqual(st.session_state.page, "login")

    def test_get_current_user_returns_none_by_default(self):
        self.assertIsNone(self.auth_manager.get_current_user())

    def test_is_authenticated_returns_false_by_default(self):
        self.assertFalse(self.auth_manager.is_authenticated())

    def test_is_authenticated_returns_true_when_set(self):
        st.session_state.authenticated = True
        self.assertTrue(self.auth_manager.is_authenticated())

    def test_has_role_returns_false_when_not_authenticated(self):
        st.session_state.authenticated = False
        st.session_state.user = {"role": "Admin"}
        self.assertFalse(self.auth_manager.has_role("Admin"))

    def test_has_role_returns_true_for_matching_role(self):
        st.session_state.authenticated = True
        st.session_state.user = {"role": "Admin"}
        self.assertTrue(self.auth_manager.has_role("Admin"))

    def test_has_role_returns_false_for_non_matching_role(self):
        st.session_state.authenticated = True
        st.session_state.user = {"role": "User"}
        self.assertFalse(self.auth_manager.has_role("Admin"))

    def test_has_any_role_returns_true_for_matching_role(self):
        st.session_state.authenticated = True
        st.session_state.user = {"role": "Super Admin"}
        self.assertTrue(self.auth_manager.has_any_role(["Admin", "Super Admin"]))

    def test_has_any_role_returns_false_for_non_matching_roles(self):
        st.session_state.authenticated = True
        st.session_state.user = {"role": "User"}
        self.assertFalse(self.auth_manager.has_any_role(["Admin", "Super Admin"]))


if __name__ == "__main__":
    unittest.main()
