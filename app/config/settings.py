import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class DatabaseSettings:
    path: str = os.path.expanduser("~/data/sterilizasyon.db")
    backup_path: str = os.path.expanduser("~/data/backups")
    auto_backup: bool = True
    backup_interval_hours: int = 24


@dataclass
class UISettings:
    window_title: str = "Sterilizasyon Takip Sistemi"
    fullscreen: bool = True
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size_base: int = 12
    hide_cursor_timeout: int = 0
    screen_timeout_minutes: int = 15


@dataclass
class SterilizationSettings:
    default_validity_days: int = 30
    steam_validity_days: int = 30
    plasma_validity_days: int = 180
    eto_validity_days: int = 365
    bi_incubation_hours: int = 24
    bi_required_for_implants: bool = True
    ci_check_required: bool = True


@dataclass
class SecuritySettings:
    session_timeout_minutes: int = 30
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30
    require_pin_for_release: bool = True
    require_supervisor_for_reject: bool = True


@dataclass
class Settings:
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    ui: UISettings = field(default_factory=UISettings)
    sterilization: SterilizationSettings = field(default_factory=SterilizationSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)

    @classmethod
    def load(cls) -> 'Settings':
        return cls()


settings = Settings.load()
