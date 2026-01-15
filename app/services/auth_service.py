import hashlib
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.session import current_session, UserSession
from app.config.settings import settings
from app.config.constants import AuditActions


class AuthService:
    def __init__(self):
        self.db = get_db()

    def _hash_pin(self, pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()

    def authenticate_by_badge(self, badge_number: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.db.fetchone("""
            SELECT o.*, r.code as role_code, r.name as role_name, r.level as role_level
            FROM operators o
            LEFT JOIN roles r ON o.role_id = r.id
            WHERE o.badge_number = ? AND o.is_active = 1
        """, (badge_number,))

        if not user:
            return False, "Kullanici bulunamadi", None

        if user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                remaining = int((locked_until - datetime.now()).total_seconds() / 60)
                return False, f"Hesap kilitli. {remaining} dakika sonra tekrar deneyin.", None

        permissions = self._get_user_permissions(user['role_id'])

        user_data = {
            'id': user['id'],
            'badge_number': user['badge_number'],
            'full_name': user['full_name'],
            'role': user['role_code'],
            'role_name': user['role_name'],
            'default_zone': user['default_zone'],
            'workstation_id': user['workstation_id'],
            'can_approve_sterilization': bool(user['can_approve_sterilization']),
            'can_release_load': bool(user['can_release_load'])
        }

        session = current_session.login(user_data, permissions)
        self._update_login_info(user['id'])
        self._log_action(user['id'], AuditActions.LOGIN, "Kart ile giris")

        return True, "Giris basarili", user_data

    def authenticate_with_pin(self, badge_number: str, pin: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.db.fetchone("""
            SELECT o.*, r.code as role_code, r.name as role_name
            FROM operators o
            LEFT JOIN roles r ON o.role_id = r.id
            WHERE o.badge_number = ? AND o.is_active = 1
        """, (badge_number,))

        if not user:
            return False, "Kullanici bulunamadi", None

        if user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                remaining = int((locked_until - datetime.now()).total_seconds() / 60)
                return False, f"Hesap kilitli. {remaining} dakika sonra tekrar deneyin.", None

        pin_hash = self._hash_pin(pin)
        if user['pin_hash'] != pin_hash:
            self._handle_failed_attempt(user['id'], user['failed_attempts'])
            return False, "Hatali PIN", None

        permissions = self._get_user_permissions(user['role_id'])

        user_data = {
            'id': user['id'],
            'badge_number': user['badge_number'],
            'full_name': user['full_name'],
            'role': user['role_code'],
            'role_name': user['role_name'],
            'default_zone': user['default_zone'],
            'workstation_id': user['workstation_id'],
            'can_approve_sterilization': bool(user['can_approve_sterilization']),
            'can_release_load': bool(user['can_release_load'])
        }

        session = current_session.login(user_data, permissions)
        self._reset_failed_attempts(user['id'])
        self._update_login_info(user['id'])
        self._log_action(user['id'], AuditActions.LOGIN, "PIN ile giris")

        return True, "Giris basarili", user_data

    def logout(self) -> bool:
        if current_session.current_user:
            user_id = current_session.current_user.user_id
            self._log_action(user_id, AuditActions.LOGOUT, "Oturum kapatildi")
        return current_session.logout()

    def verify_pin_for_action(self, pin: str) -> bool:
        if not current_session.current_user:
            return False

        user = self.db.fetchone(
            "SELECT pin_hash FROM operators WHERE id = ?",
            (current_session.current_user.user_id,)
        )

        if not user or not user['pin_hash']:
            return False

        return user['pin_hash'] == self._hash_pin(pin)

    def change_pin(self, old_pin: str, new_pin: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum acik degil"

        user_id = current_session.current_user.user_id
        user = self.db.fetchone("SELECT pin_hash FROM operators WHERE id = ?", (user_id,))

        if user['pin_hash'] and user['pin_hash'] != self._hash_pin(old_pin):
            return False, "Mevcut PIN hatali"

        if len(new_pin) < 4 or len(new_pin) > 6:
            return False, "PIN 4-6 karakter olmali"

        self.db.execute(
            "UPDATE operators SET pin_hash = ?, updated_at = ? WHERE id = ?",
            (self._hash_pin(new_pin), datetime.now(), user_id)
        )
        self.db.commit()

        return True, "PIN degistirildi"

    def _get_user_permissions(self, role_id: int) -> Dict[str, bool]:
        if not role_id:
            return {}

        permissions = self.db.fetchall("""
            SELECT p.code
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = ?
        """, (role_id,))

        return {p['code']: True for p in permissions}

    def _handle_failed_attempt(self, user_id: int, current_attempts: int):
        attempts = current_attempts + 1
        locked_until = None

        if attempts >= settings.security.max_failed_attempts:
            locked_until = datetime.now() + timedelta(
                minutes=settings.security.lockout_duration_minutes
            )

        self.db.execute("""
            UPDATE operators
            SET failed_attempts = ?, locked_until = ?, updated_at = ?
            WHERE id = ?
        """, (attempts, locked_until, datetime.now(), user_id))
        self.db.commit()

    def _reset_failed_attempts(self, user_id: int):
        self.db.execute("""
            UPDATE operators
            SET failed_attempts = 0, locked_until = NULL, updated_at = ?
            WHERE id = ?
        """, (datetime.now(), user_id))
        self.db.commit()

    def _update_login_info(self, user_id: int):
        self.db.execute("""
            UPDATE operators
            SET last_login = ?, updated_at = ?
            WHERE id = ?
        """, (datetime.now(), datetime.now(), user_id))
        self.db.commit()

    def _log_action(self, user_id: int, action: str, details: str):
        self.db.execute("""
            INSERT INTO audit_log (operator_id, action, entity_type, details, created_at)
            VALUES (?, ?, 'SESSION', ?, ?)
        """, (user_id, action, details, datetime.now()))
        self.db.commit()
