import streamlit as st
import time
import logging
from StockSageAI.database import Database, send_email
from datetime import datetime, timedelta
import secrets

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.db = Database()
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'page' not in st.session_state:
            st.session_state.page = 'login'

    # Helpers that delegate to Database hashing/verification
    def hash_password(self, password):
        return self.db.hash_password(password)

    def verify_password(self, password, hashed):
        return self.db.verify_password(password, hashed)

    def login_required(self, func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('authenticated', False) or not st.session_state.get('user'):
                st.session_state.page = 'login'
                st.rerun()
            return func(*args, **kwargs)
        return wrapper

    def admin_required(self, func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('authenticated', False) or not st.session_state.get('user'):
                st.session_state.page = 'login'
                st.rerun()
            if st.session_state.user['role'] not in ['Super Admin', 'Admin']:
                st.error("Access denied. Admin privileges required.")
                return
            return func(*args, **kwargs)
        return wrapper

    def super_admin_required(self, func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('authenticated', False) or not st.session_state.get('user'):
                st.session_state.page = 'login'
                st.rerun()
            if st.session_state.user['role'] != 'Super Admin':
                st.error("Access denied. Super Admin privileges required.")
                return
            return func(*args, **kwargs)
        return wrapper

    def logout(self):
        if st.session_state.user:
            self.db.log_activity(
                st.session_state.user['id'],
                'logout',
                'User logged out'
            )
        st.session_state.user = None
        st.session_state.authenticated = False
        st.session_state.page = 'login'
        st.query_params.clear()
        st.rerun()

    def login(self, identifier, password, remember_me=False):
        logger.debug("Login attempt for identifier=%s", identifier)
        user = self.db.get_user(identifier)
        if not user:
            logger.debug("Login failed: user not found for identifier=%s", identifier)
            return False, "Invalid username or email.", None

        if not user['is_active'] and user['role'] not in ['Admin', 'Super Admin']:
            return False, "Account is deactivated.", None

        if user['is_banned']:
            return False, "Account is banned.", None

        if user['is_suspended']:
            return False, "Account is suspended.", None

        if self.db.is_locked_out(user['id']):
            logger.debug("Login blocked: user id %s is locked out", user.get('id'))
            return False, "Account is temporarily locked due to failed login attempts.", None

        if not self.db.verify_password(password, user['password_hash']):
            self.db.increment_failed_attempts(user['id'])
            logger.debug("Invalid password for user id %s", user.get('id'))
            return False, "Invalid password.", None

        # Reset failed attempts on successful password validation
        self.db.reset_failed_attempts(user['id'])

        # Check PIN protection before full authentication
        if user.get('two_factor_enabled') and user.get('two_factor_secret'):
            # Ensure the stored secret is a bcrypt hash (our expected PIN storage).
            secret = user.get('two_factor_secret') or ''
            if not isinstance(secret, str) or not secret.startswith('$2'):
                # Legacy or TOTP secret detected - require PIN reset to migrate to numeric PIN flow
                logger.warning("User id %s has non-hashed two_factor_secret; forcing PIN reset", user.get('id'))
                return False, "Security PIN is in legacy format. Please reset your PIN via 'Reset Security PIN' link.", None
            logger.debug("User id %s requires PIN", user.get('id'))
            return True, "PIN required", user

        # Update last login timestamp
        self.db.update_user(user['id'], last_login=datetime.now().isoformat())

        # Generate remember token if requested
        if remember_me:
            remember_token = secrets.token_urlsafe(32)
            self.db.update_user(user['id'], remember_token=remember_token)
            user['remember_token'] = remember_token
            st.query_params['remember_token'] = remember_token

        # Log activity
        logger.debug("Login successful for user id %s", user.get('id'))
        self.db.log_activity(user['id'], 'login', 'Successful login')

        st.session_state.user = user
        st.session_state.authenticated = True
        st.session_state.session_token = secrets.token_urlsafe(32)
        return True, "Login successful.", user

    def _validate_pin_format(self, pin):
        return bool(pin and pin.isdigit() and len(pin) == 4)

    def enable_security_pin(self, user_id, pin):
        if not self._validate_pin_format(pin):
            return False, "PIN must be exactly 4 digits."
        pin_hash = self.hash_password(pin)
        self.db.update_user(user_id, two_factor_secret=pin_hash, two_factor_enabled=True)
        return True, "Security PIN enabled successfully."

    def disable_security_pin(self, user_id):
        self.db.update_user(user_id, two_factor_secret=None, two_factor_enabled=False)
        return True, "Security PIN disabled successfully."

    def validate_security_pin(self, user, pin, remember_me=False):
        if not self._validate_pin_format(pin):
            return False, "PIN must be exactly 4 digits."
        if not user.get('two_factor_enabled') or not user.get('two_factor_secret'):
            return False, "Security PIN is not enabled for this account."
        if self.verify_password(pin, user['two_factor_secret']):
            self.db.update_user(user['id'], last_login=datetime.now().isoformat())
            self.db.reset_failed_attempts(user['id'])
            if remember_me:
                remember_token = secrets.token_urlsafe(32)
                self.db.update_user(user['id'], remember_token=remember_token)
                user['remember_token'] = remember_token
                st.query_params['remember_token'] = remember_token
            st.session_state.user = user
            st.session_state.authenticated = True
            st.session_state.session_token = secrets.token_urlsafe(32)
            self.db.log_activity(user['id'], 'login', 'Successful PIN authentication')
            return True, "Login successful."
        self.db.increment_failed_attempts(user['id'])
        return False, "Invalid PIN."

    def request_pin_reset(self, email):
        user = self.db.get_user(email)
        if not user:
            return False, "Email not found."
        token = self.db.create_pin_reset_token(email)
        reset_link = f"http://localhost:8501/?page=pin_reset&token={token}"
        subject = "StockSageAI Security PIN Reset"
        body = f"""
        Hi {user['username']},

        A request has been received to reset your StockSageAI security PIN.
        Click the link below to reset your PIN securely:
        {reset_link}

        This link expires in one hour.

        If you did not request this, please contact support immediately.
        """
        if send_email(email, subject, body):
            self.db.log_activity(user['id'], 'pin_reset_requested', 'PIN reset email sent')
            return True, "PIN reset email sent successfully."
        return False, "Failed to send PIN reset email."

    def reset_security_pin(self, token, pin):
        if not self._validate_pin_format(pin):
            return False, "PIN must be exactly 4 digits."
        email = self.db.verify_pin_reset_token(token)
        if not email:
            return False, "Invalid or expired PIN reset token."
        user = self.db.get_user(email)
        if not user:
            return False, "User not found."
        pin_hash = self.hash_password(pin)
        self.db.update_user(user['id'], two_factor_secret=pin_hash, two_factor_enabled=True)
        self.db.use_pin_reset_token(token)
        self.db.log_activity(user['id'], 'pin_reset', 'Security PIN reset successfully')
        return True, "Security PIN has been reset successfully."

    def check_remember_me(self):
        try:
            params = st.query_params
            token = params.get('remember_token')
            if token:
                if isinstance(token, list):
                    token = token[0]
                if token and not st.session_state.get('authenticated', False):
                    user = self.db.get_user_by_token(token)
                    if user and (user['role'] in ['Admin', 'Super Admin'] or user['is_active']):
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        return True
        except Exception:
            pass
        return False

    def signup(self, username, email, password, confirm_password):
        if password != confirm_password:
            return False, "Passwords do not match."

        if len(password) < 8:
            return False, "Password must be at least 8 characters long."

        if self.db.get_user(email):
            return False, "Email already registered."

        if self.db.get_user(username):
            return False, "Username already taken."

        user_id = self.db.create_user(username, email, password, role='Free User', is_active=0)
        if user_id:
            self.db.log_activity(user_id, 'signup', 'User account created and pending approval')
            return True, "Account request submitted successfully. Your login will be enabled after admin approval."
        return False, "Failed to create account."

    def forgot_password(self, email):
        user = self.db.get_user(email)
        if not user:
            return False, "Email not found."

        token = self.db.create_password_reset_token(email)
        reset_link = f"http://localhost:8501/?page=reset_password&token={token}"

        subject = "Password Reset - StockSageAI"
        body = f"""
        Hi {user['username']},

        You requested a password reset for your StockSageAI account.

        Click the link below to reset your password:
        {reset_link}

        This link will expire in 1 hour.

        If you didn't request this reset, please ignore this email.

        Best regards,
        StockSageAI Team
        """

        if send_email(email, subject, body):
            return True, "Password reset email sent."
        return False, "Failed to send email."

    def reset_password(self, token, new_password, confirm_password):
        if new_password != confirm_password:
            return False, "Passwords do not match."

        if len(new_password) < 8:
            return False, "Password must be at least 8 characters long."

        email = self.db.verify_password_reset_token(token)
        if not email:
            return False, "Invalid or expired token."

        user = self.db.get_user(email)
        if not user:
            return False, "User not found."

        password_hash = self.db.hash_password(new_password)
        self.db.update_user(user['id'], password_hash=password_hash)
        self.db.use_password_reset_token(token)
        self.db.log_activity(user['id'], 'password_reset', 'Password reset successfully')

        return True, "Password reset successfully."

    def get_current_user(self):
        return st.session_state.get('user')

    def is_authenticated(self):
        return st.session_state.get('authenticated', False)

    def has_role(self, role):
        if not self.is_authenticated():
            return False
        user = st.session_state.get('user')
        return bool(user and user.get('role') == role)

    def has_any_role(self, roles):
        if not self.is_authenticated():
            return False
        user = st.session_state.get('user')
        return bool(user and user.get('role') in roles)

# Global auth manager instance
auth_manager = AuthManager()