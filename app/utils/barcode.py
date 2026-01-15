import uuid
import re
from datetime import datetime
from typing import Optional, Tuple


class BarcodeGenerator:

    @staticmethod
    def generate(prefix: str = "") -> str:
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def generate_work_order() -> str:
        date_part = datetime.now().strftime("%y%m%d")
        random_part = uuid.uuid4().hex[:4].upper()
        return f"WO{date_part}{random_part}"

    @staticmethod
    def generate_sterilization() -> str:
        date_part = datetime.now().strftime("%y%m%d")
        random_part = uuid.uuid4().hex[:4].upper()
        return f"SR{date_part}{random_part}"

    @staticmethod
    def generate_instrument(category: str = "") -> str:
        prefix = category[:3].upper() if category else "ALT"
        random_part = uuid.uuid4().hex[:6].upper()
        return f"{prefix}{random_part}"

    @staticmethod
    def generate_set(department: str = "") -> str:
        prefix = department[:3].upper() if department else "SET"
        random_part = uuid.uuid4().hex[:6].upper()
        return f"{prefix}{random_part}"

    @staticmethod
    def generate_cycle(machine_id: int) -> str:
        date_part = datetime.now().strftime("%y%m%d%H%M")
        return f"C{date_part}M{machine_id:02d}"


class BarcodeValidator:

    PATTERNS = {
        'work_order': r'^WO\d{6}[A-Z0-9]{4}$',
        'sterilization': r'^SR\d{6}[A-Z0-9]{4}$',
        'instrument': r'^[A-Z]{3}[A-Z0-9]{6}$',
        'set': r'^[A-Z]{3}[A-Z0-9]{6}$',
        'cycle': r'^C\d{10}M\d{2}$',
        'generic': r'^[A-Z0-9]{6,20}$'
    }

    @classmethod
    def validate(cls, barcode: str) -> Tuple[bool, str]:
        if not barcode:
            return False, "Barkod boş"

        barcode = barcode.strip().upper()

        if len(barcode) < 6:
            return False, "Barkod çok kısa"

        if len(barcode) > 20:
            return False, "Barkod çok uzun"

        if not re.match(r'^[A-Z0-9]+$', barcode):
            return False, "Geçersiz karakterler"

        return True, "Geçerli"

    @classmethod
    def get_type(cls, barcode: str) -> Optional[str]:
        barcode = barcode.strip().upper()

        if barcode.startswith('WO'):
            return 'work_order'
        elif barcode.startswith('SR'):
            return 'sterilization'
        elif barcode.startswith('C') and 'M' in barcode:
            return 'cycle'
        elif barcode.startswith('SET'):
            return 'set'
        elif barcode.startswith('ALT'):
            return 'instrument'

        return 'generic'

    @classmethod
    def is_work_order(cls, barcode: str) -> bool:
        return cls.get_type(barcode) == 'work_order'

    @classmethod
    def is_sterilization(cls, barcode: str) -> bool:
        return cls.get_type(barcode) == 'sterilization'

    @classmethod
    def is_set(cls, barcode: str) -> bool:
        return cls.get_type(barcode) == 'set'

    @classmethod
    def is_instrument(cls, barcode: str) -> bool:
        return cls.get_type(barcode) == 'instrument'
