from typing import Optional, List, Dict
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseModel


@dataclass
class Permission(BaseModel):
    code: str = ""
    name: str = ""
    description: str = ""
    module: str = ""


@dataclass
class Role(BaseModel):
    code: str = ""
    name: str = ""
    level: int = 0
    description: str = ""
    permissions: List[Permission] = field(default_factory=list)

    def has_permission(self, permission_code: str) -> bool:
        return any(p.code == permission_code for p in self.permissions)


@dataclass
class User(BaseModel):
    badge_number: str = ""
    full_name: str = ""
    pin_hash: Optional[str] = None
    role_id: Optional[int] = None
    role: Optional[Role] = None
    default_zone: str = "DIRTY"
    workstation_id: Optional[int] = None
    is_active: bool = True
    can_approve_sterilization: bool = False
    can_release_load: bool = False
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until

    @property
    def display_name(self) -> str:
        return f"{self.full_name} ({self.badge_number})"

    def has_permission(self, permission_code: str) -> bool:
        if self.role:
            return self.role.has_permission(permission_code)
        return False
