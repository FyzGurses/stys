from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.config.settings import settings
from app.config.constants import Roles, Zones


@dataclass
class UserSession:
    user_id: int
    badge_number: str
    full_name: str
    role: str
    zone: str
    workstation_id: Optional[int] = None
    permissions: Dict[str, bool] = field(default_factory=dict)
    login_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    @property
    def role_level(self) -> int:
        return Roles.get_level(self.role)

    def has_permission(self, permission: str) -> bool:
        if self.role == Roles.ADMIN:
            return True
        return self.permissions.get(permission, False)

    def can_access_zone(self, zone: str) -> bool:
        if self.role in [Roles.ADMIN, Roles.SUPERVISOR]:
            return True
        return self.zone == zone

    def is_expired(self) -> bool:
        timeout = timedelta(minutes=settings.security.session_timeout_minutes)
        return datetime.now() - self.last_activity > timeout

    def refresh(self):
        self.last_activity = datetime.now()


class SessionManager:
    _instance: Optional['SessionManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._current_session: Optional[UserSession] = None
        self._session_history: list = []
        self._initialized = True

    @property
    def current_user(self) -> Optional[UserSession]:
        if self._current_session and self._current_session.is_expired():
            self.logout()
            return None
        return self._current_session

    @property
    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def login(self, user_data: Dict[str, Any], permissions: Dict[str, bool]) -> UserSession:
        if self._current_session:
            self.logout()

        self._current_session = UserSession(
            user_id=user_data['id'],
            badge_number=user_data['badge_number'],
            full_name=user_data['full_name'],
            role=user_data['role'],
            zone=user_data.get('default_zone', Zones.DIRTY),
            workstation_id=user_data.get('workstation_id'),
            permissions=permissions
        )

        return self._current_session

    def logout(self) -> bool:
        if self._current_session:
            self._session_history.append({
                'user_id': self._current_session.user_id,
                'badge_number': self._current_session.badge_number,
                'login_time': self._current_session.login_time,
                'logout_time': datetime.now()
            })
            self._current_session = None
            return True
        return False

    def switch_zone(self, zone: str) -> bool:
        if not self._current_session:
            return False

        if not self._current_session.can_access_zone(zone):
            return False

        self._current_session.zone = zone
        self._current_session.refresh()
        return True

    def refresh_session(self):
        if self._current_session:
            self._current_session.refresh()

    def get_session_duration(self) -> Optional[timedelta]:
        if self._current_session:
            return datetime.now() - self._current_session.login_time
        return None


current_session = SessionManager()
