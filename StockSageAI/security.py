"""
Enterprise Security Module for SP 07 Platform
Comprehensive protection against common web vulnerabilities and data leaks
"""

import streamlit as st
import hashlib
import hmac
import secrets
import re
import json
from datetime import datetime, timedelta
from functools import wraps
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote, unquote

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & SECURITY CONSTANTS
# ============================================================================

SENSITIVE_DATA_PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'password': r'password\s*[:=]\s*[\'"][^\'"]+[\'"]',
    'api_key': r'(api[_-]?key|apikey|access[_-]?token)\s*[:=]\s*[\'"][^\'"]+[\'"]',
}

INJECTION_PATTERNS = {
    'sql': r"(\'|\"|\;|--|\/\*|\*\/|xp_|sp_|exec|execute|select|insert|update|delete|drop|create|alter)",
    'script': r'(<script|javascript:|onerror=|onclick=|onload=|eval\(|expression\()',
    'command': r'(;|\||&|`|\$\(|sh |bash |rm |dd |cat )',
}

# Maximum session duration (hours)
MAX_SESSION_DURATION = 8

# Rate limiting - failed login attempts
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 900  # seconds (15 minutes)

# ============================================================================
# DATA PROTECTION & SANITIZATION
# ============================================================================

class DataProtection:
    """Protect sensitive data from leaks and exposure"""

    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email for display: user****@domain.com"""
        if not email or '@' not in email:
            return "***"
        local, domain = email.split('@')
        if len(local) <= 2:
            masked_local = f"{local[0]}***"
        else:
            masked_local = f"{local[0:2]}***{local[-1]}" if len(local) > 2 else f"{local[0]}***"
        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number: ***-***-1234"""
        if not phone or len(phone) < 4:
            return "***"
        return f"***-***-{phone[-4:]}"

    @staticmethod
    def mask_credit_card(card: str) -> str:
        """Mask credit card: ****-****-****-1234"""
        card_clean = ''.join(filter(str.isdigit, card))
        if len(card_clean) < 4:
            return "****"
        return f"****-****-****-{card_clean[-4:]}"

    @staticmethod
    def redact_logs(text: str) -> str:
        """Remove sensitive data from logs"""
        result = text
        for pattern_type, pattern in SENSITIVE_DATA_PATTERNS.items():
            result = re.sub(pattern, f"[REDACTED_{pattern_type.upper()}]", result, flags=re.IGNORECASE)
        return result

    @staticmethod
    def detect_sensitive_data(text: str) -> Dict[str, list]:
        """Detect sensitive data patterns in text"""
        detected = {}
        for pattern_type, pattern in SENSITIVE_DATA_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected[pattern_type] = matches
        return detected


# ============================================================================
# INPUT VALIDATION & SANITIZATION
# ============================================================================

class InputValidator:
    """Comprehensive input validation to prevent injection attacks"""

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Validate username format and length"""
        if not username:
            return False, "Username is required"
        if len(username) < 3 or len(username) > 50:
            return False, "Username must be 3-50 characters"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscore, and hyphen"
        return True, "Valid"

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        if len(email) > 254:
            return False, "Email too long"
        return True, "Valid"

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        if len(password) > 128:
            return False, "Password too long"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letters"
        if not re.search(r'\d', password):
            return False, "Password must contain numbers"
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            return False, "Password must contain special characters"
        return True, "Valid"

    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize input to prevent injection attacks"""
        if not isinstance(text, str):
            return ""
        if len(text) > max_length:
            text = text[:max_length]
        # Check for injection patterns
        for pattern_type, pattern in INJECTION_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential {pattern_type} injection detected and removed")
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        # Remove null bytes
        text = text.replace('\x00', '')
        return text.strip()

    @staticmethod
    def validate_stock_symbol(symbol: str) -> tuple[bool, str]:
        """Validate stock symbol format"""
        if not symbol:
            return False, "Symbol is required"
        if not re.match(r'^[A-Z][A-Z0-9&-]{0,10}$', symbol):
            return False, "Invalid stock symbol format"
        return True, "Valid"


# ============================================================================
# CSRF & SESSION PROTECTION
# ============================================================================

class CSRFProtection:
    """Cross-Site Request Forgery protection"""

    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a unique CSRF token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def verify_csrf_token(token: str, session_token: Optional[str] = None) -> bool:
        """Verify CSRF token validity"""
        if not token or not isinstance(token, str):
            return False
        if session_token is None:
            session_token = st.session_state.get('_csrf_token')
        return hmac.compare_digest(token, session_token) if session_token else False

    @staticmethod
    def init_csrf_protection():
        """Initialize CSRF protection in session state"""
        if '_csrf_token' not in st.session_state:
            st.session_state._csrf_token = CSRFProtection.generate_csrf_token()


class SessionSecurity:
    """Session management and protection"""

    @staticmethod
    def init_session_timeout():
        """Initialize session timeout management"""
        if 'session_created_at' not in st.session_state:
            st.session_state.session_created_at = datetime.now()
        if 'session_last_activity' not in st.session_state:
            st.session_state.session_last_activity = datetime.now()

    @staticmethod
    def check_session_timeout() -> bool:
        """Check if session has expired"""
        if 'session_created_at' not in st.session_state:
            return False

        last_activity = st.session_state.get('session_last_activity', datetime.now())
        current_time = datetime.now()

        # Check for inactivity (30 minutes)
        if (current_time - last_activity).seconds > 1800:
            logger.warning("Session expired due to inactivity")
            return True

        # Check for max session duration
        if (current_time - st.session_state.session_created_at).seconds > MAX_SESSION_DURATION * 3600:
            logger.warning("Session expired: max duration reached")
            return True

        # Update last activity
        st.session_state.session_last_activity = current_time
        return False

    @staticmethod
    def invalidate_session():
        """Invalidate current session"""
        for key in list(st.session_state.keys()):
            if key not in ['page', 'theme']:  # Preserve non-sensitive keys
                del st.session_state[key]
        logger.info("Session invalidated")


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Rate limiting for brute force and DoS protection"""

    @staticmethod
    def check_login_attempts(identifier: str) -> tuple[bool, str]:
        """Check if user exceeded login attempt limit"""
        if 'login_attempts' not in st.session_state:
            st.session_state.login_attempts = {}

        current_time = datetime.now().timestamp()
        key = hashlib.sha256(identifier.encode()).hexdigest()

        if key in st.session_state.login_attempts:
            attempts, first_attempt_time = st.session_state.login_attempts[key]

            # Reset counter if window has passed
            if (current_time - first_attempt_time) > LOGIN_ATTEMPT_WINDOW:
                st.session_state.login_attempts[key] = (1, current_time)
                return True, "Try again"

            # Check if exceeded limit
            if attempts >= MAX_LOGIN_ATTEMPTS:
                remaining = int(LOGIN_ATTEMPT_WINDOW - (current_time - first_attempt_time))
                return False, f"Too many attempts. Try again in {remaining}s"

            # Increment counter
            st.session_state.login_attempts[key] = (attempts + 1, first_attempt_time)
        else:
            st.session_state.login_attempts[key] = (1, current_time)

        return True, "OK"

    @staticmethod
    def reset_login_attempts(identifier: str):
        """Reset login attempts for identifier"""
        if 'login_attempts' not in st.session_state:
            return
        key = hashlib.sha256(identifier.encode()).hexdigest()
        if key in st.session_state.login_attempts:
            del st.session_state.login_attempts[key]


# ============================================================================
# SECURE RESPONSE HEADERS
# ============================================================================

def get_secure_headers() -> Dict[str, str]:
    """Get secure HTTP headers for protection"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    }


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Comprehensive audit logging for compliance and security"""

    @staticmethod
    def log_security_event(event_type: str, user_id: Optional[str] = None, details: Optional[Dict] = None, severity: str = "INFO"):
        """Log security-related event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details or {},
            'severity': severity,
            'session_id': st.session_state.get('session_id'),
        }
        logger.warning(f"[{severity}] {event_type}: {json.dumps(log_entry)}")
        return log_entry

    @staticmethod
    def log_failed_login(identifier: str, reason: str = "Invalid credentials"):
        """Log failed login attempt"""
        AuditLogger.log_security_event(
            'FAILED_LOGIN_ATTEMPT',
            details={'identifier_hash': hashlib.sha256(identifier.encode()).hexdigest(), 'reason': reason},
            severity='WARNING'
        )

    @staticmethod
    def log_successful_login(user_id: str):
        """Log successful login"""
        AuditLogger.log_security_event('SUCCESSFUL_LOGIN', user_id=user_id, severity='INFO')

    @staticmethod
    def log_suspicious_activity(activity_type: str, user_id: Optional[str], details: Dict):
        """Log suspicious activity for investigation"""
        AuditLogger.log_security_event(activity_type, user_id=user_id, details=details, severity='CRITICAL')


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_security():
    """Initialize all security measures"""
    CSRFProtection.init_csrf_protection()
    SessionSecurity.init_session_timeout()
    if SessionSecurity.check_session_timeout():
        SessionSecurity.invalidate_session()
        st.session_state.page = 'login'
        st.warning("Your session has expired. Please login again.")
        st.rerun()
