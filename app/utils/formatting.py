from typing import Optional


class Formatter:

    @staticmethod
    def truncate(text: str, length: int = 50, suffix: str = "...") -> str:
        if not text:
            return ""
        if len(text) <= length:
            return text
        return text[:length - len(suffix)] + suffix

    @staticmethod
    def pad_left(text: str, length: int, char: str = " ") -> str:
        return text.rjust(length, char)

    @staticmethod
    def pad_right(text: str, length: int, char: str = " ") -> str:
        return text.ljust(length, char)

    @staticmethod
    def number_format(number: float, decimals: int = 0) -> str:
        if decimals == 0:
            return f"{int(number):,}".replace(",", ".")
        return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def currency(amount: float, symbol: str = "₺") -> str:
        formatted = Formatter.number_format(amount, 2)
        return f"{formatted} {symbol}"

    @staticmethod
    def percentage(value: float, decimals: int = 1) -> str:
        return f"%{value:.{decimals}f}"

    @staticmethod
    def duration_minutes(minutes: int) -> str:
        if minutes < 60:
            return f"{minutes} dk"
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} saat"
        return f"{hours} saat {mins} dk"

    @staticmethod
    def duration_seconds(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds} sn"
        return Formatter.duration_minutes(seconds // 60)

    @staticmethod
    def file_size(bytes_size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    @staticmethod
    def phone_number(phone: str) -> str:
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]} {digits[6:8]} {digits[8:]}"
        return phone

    @staticmethod
    def badge_number(badge: str) -> str:
        return badge.upper().strip()

    @staticmethod
    def status_text(status: str) -> str:
        translations = {
            'RECEIVED': 'Kabul Edildi',
            'WASHING': 'Yıkanıyor',
            'WASHED': 'Yıkandı',
            'INSPECTING': 'Kontrol Ediliyor',
            'INSPECTION_FAILED': 'Kontrol Başarısız',
            'PACKAGING': 'Paketleniyor',
            'PACKAGED': 'Paketlendi',
            'STERILIZING': 'Sterilize Ediliyor',
            'STERILIZED': 'Sterilize Edildi',
            'PENDING_RELEASE': 'Onay Bekliyor',
            'RELEASED': 'Onaylandı',
            'REJECTED': 'Reddedildi',
            'STORED': 'Depolandı',
            'DISTRIBUTED': 'Dağıtıldı',
            'REPROCESSING': 'Tekrar İşlemde',
            'RECALLED': 'Geri Çağrıldı',
            'COMPLETED': 'Tamamlandı',
            'PENDING_CI': 'CI Bekliyor',
            'PENDING_BI': 'BI Bekliyor',
            'EXPIRED': 'Süresi Doldu',
            'USED': 'Kullanıldı',
            'IDLE': 'Boşta',
            'RUNNING': 'Çalışıyor',
            'ERROR': 'Hata',
            'MAINTENANCE': 'Bakımda',
            'OFFLINE': 'Çevrimdışı',
            'PASS': 'Başarılı',
            'FAIL': 'Başarısız',
            'PENDING': 'Bekliyor',
            'ACTIVE': 'Aktif',
            'INACTIVE': 'Pasif'
        }
        return translations.get(status, status)

    @staticmethod
    def zone_text(zone: str) -> str:
        zones = {
            'DIRTY': 'Kirli Alan',
            'CLEAN': 'Temiz Alan',
            'STERILE': 'Steril Alan'
        }
        return zones.get(zone, zone)

    @staticmethod
    def role_text(role: str) -> str:
        roles = {
            'ADMIN': 'Yönetici',
            'SUPERVISOR': 'Süpervizör',
            'OPERATOR': 'Operatör',
            'NURSE': 'Hemşire',
            'VIEWER': 'İzleyici'
        }
        return roles.get(role, role)
