from datetime import datetime, timedelta, date
from typing import Optional, Tuple


class DateUtils:

    DATE_FORMAT = "%d.%m.%Y"
    TIME_FORMAT = "%H:%M"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"
    DATETIME_FULL_FORMAT = "%d.%m.%Y %H:%M:%S"

    @classmethod
    def now(cls) -> datetime:
        return datetime.now()

    @classmethod
    def today(cls) -> date:
        return date.today()

    @classmethod
    def format_date(cls, dt: datetime) -> str:
        if not dt:
            return ""
        return dt.strftime(cls.DATE_FORMAT)

    @classmethod
    def format_time(cls, dt: datetime) -> str:
        if not dt:
            return ""
        return dt.strftime(cls.TIME_FORMAT)

    @classmethod
    def format_datetime(cls, dt: datetime) -> str:
        if not dt:
            return ""
        return dt.strftime(cls.DATETIME_FORMAT)

    @classmethod
    def format_datetime_full(cls, dt: datetime) -> str:
        if not dt:
            return ""
        return dt.strftime(cls.DATETIME_FULL_FORMAT)

    @classmethod
    def parse_date(cls, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, cls.DATE_FORMAT)
        except (ValueError, TypeError):
            return None

    @classmethod
    def parse_datetime(cls, datetime_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(datetime_str, cls.DATETIME_FORMAT)
        except (ValueError, TypeError):
            return None

    @classmethod
    def get_relative_time(cls, dt: datetime) -> str:
        if not dt:
            return ""

        now = datetime.now()
        diff = now - dt

        if diff.total_seconds() < 60:
            return "Az önce"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} dakika önce"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} saat önce"
        elif diff.days == 1:
            return "Dün"
        elif diff.days < 7:
            return f"{diff.days} gün önce"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} hafta önce"
        else:
            return cls.format_date(dt)

    @classmethod
    def get_time_remaining(cls, target: datetime) -> str:
        if not target:
            return ""

        now = datetime.now()
        if target < now:
            return "Süresi dolmuş"

        diff = target - now

        if diff.days > 0:
            return f"{diff.days} gün"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} saat"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} dakika"
        else:
            return "Az kaldı"

    @classmethod
    def add_days(cls, dt: datetime, days: int) -> datetime:
        return dt + timedelta(days=days)

    @classmethod
    def add_hours(cls, dt: datetime, hours: int) -> datetime:
        return dt + timedelta(hours=hours)

    @classmethod
    def get_start_of_day(cls, dt: datetime = None) -> datetime:
        if dt is None:
            dt = datetime.now()
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @classmethod
    def get_end_of_day(cls, dt: datetime = None) -> datetime:
        if dt is None:
            dt = datetime.now()
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    @classmethod
    def get_week_range(cls, dt: datetime = None) -> Tuple[datetime, datetime]:
        if dt is None:
            dt = datetime.now()
        start = dt - timedelta(days=dt.weekday())
        start = cls.get_start_of_day(start)
        end = start + timedelta(days=6)
        end = cls.get_end_of_day(end)
        return start, end

    @classmethod
    def get_month_range(cls, dt: datetime = None) -> Tuple[datetime, datetime]:
        if dt is None:
            dt = datetime.now()
        start = dt.replace(day=1)
        start = cls.get_start_of_day(start)

        if dt.month == 12:
            end = dt.replace(year=dt.year + 1, month=1, day=1)
        else:
            end = dt.replace(month=dt.month + 1, day=1)
        end = end - timedelta(days=1)
        end = cls.get_end_of_day(end)

        return start, end
