from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseModel


@dataclass
class Instrument(BaseModel):
    barcode: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    purchase_date: Optional[datetime] = None
    warranty_end: Optional[datetime] = None
    max_cycles: int = 0
    current_cycles: int = 0
    status: str = "ACTIVE"
    location: str = ""
    last_sterilization: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    notes: str = ""
    image_path: str = ""

    @property
    def cycles_remaining(self) -> int:
        if self.max_cycles <= 0:
            return -1
        return max(0, self.max_cycles - self.current_cycles)

    @property
    def needs_maintenance(self) -> bool:
        if self.next_maintenance is None:
            return False
        return datetime.now() >= self.next_maintenance

    @property
    def is_expired(self) -> bool:
        if self.max_cycles <= 0:
            return False
        return self.current_cycles >= self.max_cycles


@dataclass
class SetContent(BaseModel):
    set_id: int = 0
    instrument_id: int = 0
    quantity: int = 1
    is_mandatory: bool = True
    position: str = ""
    instrument: Optional[Instrument] = None


@dataclass
class InstrumentSet(BaseModel):
    barcode: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    department_id: Optional[int] = None
    department_name: str = ""
    container_type: str = ""
    sterilization_method: str = "STEAM"
    validity_days: int = 30
    status: str = "ACTIVE"
    total_instruments: int = 0
    contents: List[SetContent] = field(default_factory=list)
    notes: str = ""
    image_path: str = ""
    last_sterilization: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        mandatory_count = sum(1 for c in self.contents if c.is_mandatory)
        actual_count = sum(1 for c in self.contents if c.is_mandatory and c.instrument)
        return mandatory_count == actual_count

    @property
    def is_sterile(self) -> bool:
        if self.expiry_date is None:
            return False
        return datetime.now() < self.expiry_date

    @property
    def days_until_expiry(self) -> int:
        if self.expiry_date is None:
            return 0
        delta = self.expiry_date - datetime.now()
        return max(0, delta.days)
