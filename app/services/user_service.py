import hashlib
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from app.core.database import get_db
from app.models.user import User, Role, Permission


class UserService:

    def __init__(self):
        self.db = get_db()

    def _hash_pin(self, pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()

    def get_all_users(self, include_inactive: bool = False) -> List[User]:
        query = """
            SELECT o.*, r.code as role_code, r.name as role_name
            FROM operators o
            LEFT JOIN roles r ON o.role_id = r.id
        """
        if not include_inactive:
            query += " WHERE o.is_active = 1"
        query += " ORDER BY o.full_name"

        rows = self.db.fetchall(query)
        users = []
        for row in rows:
            user = User(
                id=row['id'],
                badge_number=row['badge_number'],
                full_name=row['full_name'],
                role_id=row['role_id'],
                default_zone=row['default_zone'],
                is_active=bool(row['is_active']),
                can_approve_sterilization=bool(row['can_approve_sterilization']),
                can_release_load=bool(row['can_release_load']),
                last_login=row['last_login'],
                created_at=row['created_at']
            )
            if row['role_id']:
                user.role = Role(
                    id=row['role_id'],
                    code=row['role_code'],
                    name=row['role_name']
                )
            users.append(user)
        return users

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        row = self.db.fetchone("""
            SELECT o.*, r.code as role_code, r.name as role_name
            FROM operators o
            LEFT JOIN roles r ON o.role_id = r.id
            WHERE o.id = ?
        """, (user_id,))

        if not row:
            return None

        user = User(
            id=row['id'],
            badge_number=row['badge_number'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            default_zone=row['default_zone'],
            is_active=bool(row['is_active']),
            can_approve_sterilization=bool(row['can_approve_sterilization']),
            can_release_load=bool(row['can_release_load']),
            last_login=row['last_login'],
            created_at=row['created_at']
        )
        if row['role_id']:
            user.role = Role(
                id=row['role_id'],
                code=row['role_code'],
                name=row['role_name']
            )
        return user

    def get_user_by_badge(self, badge_number: str) -> Optional[User]:
        row = self.db.fetchone("""
            SELECT o.*, r.code as role_code, r.name as role_name
            FROM operators o
            LEFT JOIN roles r ON o.role_id = r.id
            WHERE o.badge_number = ?
        """, (badge_number,))

        if not row:
            return None

        user = User(
            id=row['id'],
            badge_number=row['badge_number'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            default_zone=row['default_zone'],
            is_active=bool(row['is_active']),
            can_approve_sterilization=bool(row['can_approve_sterilization']),
            can_release_load=bool(row['can_release_load'])
        )
        return user

    def create_user(self, data: Dict) -> Tuple[bool, str, Optional[int]]:
        existing = self.get_user_by_badge(data['badge_number'])
        if existing:
            return False, "Bu kart numarası zaten kayıtlı", None

        pin_hash = None
        if data.get('pin'):
            pin_hash = self._hash_pin(data['pin'])

        try:
            self.db.execute("""
                INSERT INTO operators (
                    badge_number, full_name, pin_hash, role_id, default_zone,
                    workstation_id, is_active, can_approve_sterilization,
                    can_release_load, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['badge_number'],
                data['full_name'],
                pin_hash,
                data.get('role_id'),
                data.get('default_zone', 'DIRTY'),
                data.get('workstation_id'),
                data.get('is_active', True),
                data.get('can_approve_sterilization', False),
                data.get('can_release_load', False),
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            user_id = self.db.get_last_insert_id()
            return True, "Kullanıcı oluşturuldu", user_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def update_user(self, user_id: int, data: Dict) -> Tuple[bool, str]:
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "Kullanıcı bulunamadı"

        if data.get('badge_number') and data['badge_number'] != user.badge_number:
            existing = self.get_user_by_badge(data['badge_number'])
            if existing:
                return False, "Bu kart numarası başka bir kullanıcıda kayıtlı"

        try:
            self.db.execute("""
                UPDATE operators SET
                    badge_number = COALESCE(?, badge_number),
                    full_name = COALESCE(?, full_name),
                    role_id = COALESCE(?, role_id),
                    default_zone = COALESCE(?, default_zone),
                    workstation_id = ?,
                    is_active = COALESCE(?, is_active),
                    can_approve_sterilization = COALESCE(?, can_approve_sterilization),
                    can_release_load = COALESCE(?, can_release_load),
                    updated_at = ?
                WHERE id = ?
            """, (
                data.get('badge_number'),
                data.get('full_name'),
                data.get('role_id'),
                data.get('default_zone'),
                data.get('workstation_id'),
                data.get('is_active'),
                data.get('can_approve_sterilization'),
                data.get('can_release_load'),
                datetime.now(),
                user_id
            ))
            self.db.commit()
            return True, "Kullanıcı güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE operators SET is_active = 0, updated_at = ? WHERE id = ?
            """, (datetime.now(), user_id))
            self.db.commit()
            return True, "Kullanıcı devre dışı bırakıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def reset_pin(self, user_id: int, new_pin: str) -> Tuple[bool, str]:
        if len(new_pin) < 4 or len(new_pin) > 6:
            return False, "PIN 4-6 karakter olmalı"

        try:
            self.db.execute("""
                UPDATE operators SET pin_hash = ?, updated_at = ? WHERE id = ?
            """, (self._hash_pin(new_pin), datetime.now(), user_id))
            self.db.commit()
            return True, "PIN sıfırlandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_all_roles(self) -> List[Role]:
        rows = self.db.fetchall("SELECT * FROM roles ORDER BY level DESC")
        return [Role(
            id=row['id'],
            code=row['code'],
            name=row['name'],
            level=row['level'],
            description=row['description']
        ) for row in rows]

    def get_users_by_zone(self, zone: str) -> List[User]:
        rows = self.db.fetchall("""
            SELECT o.*, r.code as role_code, r.name as role_name
            FROM operators o
            LEFT JOIN roles r ON o.role_id = r.id
            WHERE o.is_active = 1 AND o.default_zone = ?
            ORDER BY o.full_name
        """, (zone,))

        users = []
        for row in rows:
            user = User(
                id=row['id'],
                badge_number=row['badge_number'],
                full_name=row['full_name'],
                role_id=row['role_id'],
                default_zone=row['default_zone'],
                is_active=True
            )
            users.append(user)
        return users
