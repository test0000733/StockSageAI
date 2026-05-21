import sqlite3
import bcrypt
import secrets
import string
from datetime import datetime, timedelta
import pyotp
import smtplib
from email.mime.text import MIMEText
import os

class Database:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'Free User',
                    is_active BOOLEAN DEFAULT 1,
                    is_suspended BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    failed_attempts INTEGER DEFAULT 0,
                    lockout_until DATETIME,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    remember_token TEXT,
                    two_factor_secret TEXT,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    subscription_type TEXT DEFAULT 'free',
                    subscription_expires DATETIME
                )
            ''')

            # Password reset tokens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    token TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Activity logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # API usage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    endpoint TEXT NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_api_usage_user_endpoint
                ON api_usage (user_id, endpoint)
            ''')

            # Admin notifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Feature flags table for admin toggles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_name TEXT PRIMARY KEY,
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    description TEXT
                )
            ''')

            # Price alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    triggered BOOLEAN DEFAULT 0,
                    triggered_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_buy_price REAL NOT NULL,
                    entry_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, symbol)
                )
            ''')

            # Portfolio performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_value REAL,
                    daily_change REAL,
                    daily_change_pct REAL,
                    annual_return REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # System health metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_data TEXT,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

        self._ensure_default_user()
        self._initialize_default_feature_flags()

    def _ensure_default_user(self):
        default_username = 'Sandeep S Phadnis'
        default_email = 'sandeep.s.phadnis@example.com'
        default_password = 'Sandeep@2006'
        default_role = 'Admin'

        if not self.get_user(default_username) and not self.get_user(default_email):
            self.create_user(default_username, default_email, default_password, role=default_role)

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def generate_token(self, length=32):
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

    def create_user(self, username, email, password, role='Free User', is_active=1):
        password_hash = self.hash_password(password)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, email, password_hash, role, is_active))
                user_id = cursor.lastrowid
                conn.commit()
                return user_id
            except sqlite3.IntegrityError:
                return None

    def get_user(self, identifier):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE email = ? OR username = ?
            ''', (identifier, identifier))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_user_by_token(self, token):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE remember_token = ?
            ''', (token,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def update_user(self, user_id, **kwargs):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            cursor.execute(f'''
                UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            conn.commit()

    def increment_failed_attempts(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET failed_attempts = failed_attempts + 1,
                lockout_until = CASE
                    WHEN failed_attempts >= 4 THEN datetime('now', '+15 minutes')
                    ELSE NULL
                END
                WHERE id = ?
            ''', (user_id,))
            conn.commit()

    def reset_failed_attempts(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET failed_attempts = 0, lockout_until = NULL
                WHERE id = ?
            ''', (user_id,))
            conn.commit()

    def is_locked_out(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT lockout_until FROM users WHERE id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                lockout_time = datetime.fromisoformat(result[0])
                return datetime.now() < lockout_time
            return False

    def create_password_reset_token(self, email):
        token = self.generate_token()
        expires_at = datetime.now() + timedelta(hours=1)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO password_resets (email, token, expires_at)
                VALUES (?, ?, ?)
            ''', (email, token, expires_at.isoformat()))
            conn.commit()
        return token

    def verify_password_reset_token(self, token):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT email, expires_at, used FROM password_resets
                WHERE token = ? AND used = 0
            ''', (token,))
            result = cursor.fetchone()
            if result:
                email, expires_at, used = result
                if datetime.now() < datetime.fromisoformat(expires_at):
                    return email
            return None

    def use_password_reset_token(self, token):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE password_resets SET used = 1 WHERE token = ?
            ''', (token,))
            conn.commit()

    def create_pin_reset_token(self, email):
        token = self.generate_token()
        expires_at = datetime.now() + timedelta(hours=1)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO password_resets (email, token, expires_at, used)
                VALUES (?, ?, ?, 0)
            ''', (email, token, expires_at.isoformat()))
            conn.commit()
        return token

    def verify_pin_reset_token(self, token):
        return self.verify_password_reset_token(token)

    def use_pin_reset_token(self, token):
        return self.use_password_reset_token(token)

    def log_activity(self, user_id, action, details='', ip_address='', user_agent=''):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action, details, ip_address, user_agent))
            conn.commit()

    def get_activity_logs(self, limit=100, offset=0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.username FROM activity_logs a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.timestamp DESC LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def update_api_usage(self, user_id, endpoint):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO api_usage (user_id, endpoint, request_count, last_used)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, endpoint) DO UPDATE SET
                request_count = request_count + 1,
                last_used = CURRENT_TIMESTAMP
            ''', (user_id, endpoint))
            conn.commit()

    def get_api_usage_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.username, a.endpoint, a.request_count, a.last_used
                FROM api_usage a
                JOIN users u ON a.user_id = u.id
                ORDER BY a.last_used DESC
            ''')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_user_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    COUNT(*) as total_users,
                    SUM(CASE WHEN role = 'Super Admin' THEN 1 ELSE 0 END) as super_admins,
                    SUM(CASE WHEN role = 'Admin' THEN 1 ELSE 0 END) as admins,
                    SUM(CASE WHEN role = 'Premium User' THEN 1 ELSE 0 END) as premium_users,
                    SUM(CASE WHEN role = 'Free User' THEN 1 ELSE 0 END) as free_users,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
                    SUM(CASE WHEN is_suspended = 1 THEN 1 ELSE 0 END) as suspended_users,
                    SUM(CASE WHEN is_banned = 1 THEN 1 ELSE 0 END) as banned_users
                FROM users
            ''')
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    def get_all_users(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, is_active, is_suspended, is_banned,
                       failed_attempts, lockout_until, last_login, created_at,
                       subscription_type, subscription_expires, two_factor_enabled
                FROM users
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_pending_users(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, created_at
                FROM users
                WHERE is_active = 0 AND is_banned = 0
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_feature_flags(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT flag_name, enabled, description
                FROM feature_flags
                ORDER BY flag_name
            ''')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def set_feature_flag(self, flag_name, enabled):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE feature_flags SET enabled = ? WHERE flag_name = ?
            ''', (enabled, flag_name))
            conn.commit()

    def _initialize_default_feature_flags(self):
        default_flags = [
            ('beta_recommendations', 0, 'Enable beta recommendation engine'),
            ('live_sentiment', 1, 'Use live sentiment scoring for headlines'),
            ('advanced_heatmap', 1, 'Enable advanced portfolio heatmap visuals'),
            ('pending_approval_required', 1, 'Require admin approval for new signups')
        ]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for flag_name, enabled, description in default_flags:
                cursor.execute('''
                    INSERT OR IGNORE INTO feature_flags (flag_name, enabled, description)
                    VALUES (?, ?, ?)
                ''', (flag_name, enabled, description))
            conn.commit()

    def get_user_by_id(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def add_admin_notification(self, notification_type, message):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_notifications (type, message)
                VALUES (?, ?)
            ''', (notification_type, message))
            conn.commit()

    def get_admin_notifications(self, unread_only=False):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM admin_notifications'
            if unread_only:
                query += ' WHERE is_read = 0'
            query += ' ORDER BY created_at DESC'
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def mark_notification_read(self, notification_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE admin_notifications SET is_read = 1 WHERE id = ?
            ''', (notification_id,))
            conn.commit()

    # ===== Alert Management =====
    def create_alert(self, user_id, symbol, alert_type, threshold):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_alerts (user_id, symbol, alert_type, threshold)
                VALUES (?, ?, ?, ?)
            ''', (user_id, symbol, alert_type, threshold))
            alert_id = cursor.lastrowid
            conn.commit()
        return alert_id

    def get_user_alerts(self, user_id, active_only=True):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM price_alerts WHERE user_id = ?'
            if active_only:
                query += ' AND is_active = 1'
            query += ' ORDER BY created_at DESC'
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_all_active_alerts(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM price_alerts WHERE is_active = 1 AND triggered = 0
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def trigger_alert(self, alert_id, triggered_price):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE price_alerts SET triggered = 1, triggered_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (alert_id,))
            conn.commit()

    def deactivate_alert(self, alert_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE price_alerts SET is_active = 0 WHERE id = ?
            ''', (alert_id,))
            conn.commit()

    # ===== Portfolio Management =====
    def add_portfolio_holding(self, user_id, symbol, quantity, avg_buy_price, notes=''):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO portfolio (user_id, symbol, quantity, avg_buy_price, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, symbol, quantity, avg_buy_price, notes))
            conn.commit()

    def get_portfolio(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM portfolio WHERE user_id = ? AND is_active = 1
                ORDER BY entry_date DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def remove_portfolio_holding(self, user_id, symbol):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE portfolio SET is_active = 0 WHERE user_id = ? AND symbol = ?
            ''', (user_id, symbol))
            conn.commit()

    def update_portfolio_holding(self, user_id, symbol, quantity, avg_buy_price, notes=''):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE portfolio SET quantity = ?, avg_buy_price = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND symbol = ? AND is_active = 1
            ''', (quantity, avg_buy_price, notes, user_id, symbol))
            conn.commit()

    def record_portfolio_history(self, user_id, total_value, daily_change, daily_change_pct, annual_return):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_history (user_id, total_value, daily_change, daily_change_pct, annual_return)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, total_value, daily_change, daily_change_pct, annual_return))
            conn.commit()

    def get_portfolio_history(self, user_id, limit=30):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM portfolio_history WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    # ===== System Health Metrics =====
    def record_system_metric(self, metric_name, metric_value, metric_data=''):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (metric_name, metric_value, metric_data)
                VALUES (?, ?, ?)
            ''', (metric_name, metric_value, metric_data))
            conn.commit()

    def get_system_health(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE is_active = 1) as active_users,
                    (SELECT COUNT(*) FROM price_alerts WHERE is_active = 1) as active_alerts,
                    (SELECT COUNT(*) FROM activity_logs WHERE timestamp > datetime('now', '-24 hours')) as activities_24h,
                    (SELECT COUNT(*) FROM api_usage WHERE last_used > datetime('now', '-1 hour')) as api_calls_1h,
                    (SELECT AVG(request_count) FROM api_usage WHERE last_used > datetime('now', '-24 hours')) as avg_api_per_user
            ''')
            row = cursor.fetchone()
            if row:
                columns = ['active_users', 'active_alerts', 'activities_24h', 'api_calls_1h', 'avg_api_per_user']
                return dict(zip(columns, row))
        return {}

    def get_system_performance(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM system_metrics 
                ORDER BY recorded_at DESC LIMIT 50
            ''')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

# Email functions
def send_email(to_email, subject, body):
    # Configure your email settings here
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')

    if not smtp_username or not smtp_password:
        print("SMTP credentials not configured")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_username
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

# 2FA functions
def generate_2fa_secret():
    return pyotp.random_base32()

def get_2fa_uri(secret, username, issuer="StockSageAI"):
    return pyotp.totp.TOTP(secret, digits=4).provisioning_uri(name=username, issuer_name=issuer)

def verify_2fa_code(secret, code):
    totp = pyotp.TOTP(secret, digits=4)
    return totp.verify(code, valid_window=1)