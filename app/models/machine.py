from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseModel
from app.config.constants import MachineTypes, MachineStatus


@dataclass
class MachineProgram(BaseModel):
    machine_id: int = 0
    name: str = ""
    code: str = ""
    temperature: float = 0.0
    pressure: float = 0.0
    duration_minutes: int = 0
    description: str = ""
    is_active: bool = True


@dataclass
class MachineCycle(BaseModel):
    cycle_number: str = ""
    machine_id: int = 0
    machine_name: str = ""
    program_id: Optional[int] = None
    program_name: str = ""
    operator_id: Optional[int] = None
    operator_name: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = MachineStatus.IDLE
    temperature_achieved: float = 0.0
    pressure_achieved: float = 0.0
    ci_result: str = "PENDING"
    bi_lot_number: str = ""
    bi_result: str = "PENDING"
    bi_read_time: Optional[datetime] = None
    notes: str = ""
    contents_count: int = 0

    @property
    def duration_minutes(self) -> int:
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0

    @property
    def is_complete(self) -> bool:
        return self.status == MachineStatus.COMPLETED

    @property
    def is_approved(self) -> bool:
        return self.ci_result == "PASS" and self.bi_result == "PASS"


@dataclass
class Machine(BaseModel):
    name: str = ""
    machine_type: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    zone: str = ""
    status: str = MachineStatus.IDLE
    current_cycle_id: Optional[int] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    total_cycles: int = 0
    ip_address: str = ""
    port: int = 0
    is_active: bool = True
    programs: List[MachineProgram] = field(default_factory=list)

    @property
    def category(self) -> str:
        return MachineTypes.CATEGORIES.get(self.machine_type, "UNKNOWN")

    @property
    def is_washer(self) -> bool:
        return self.category == "WASHER"

    @property
    def is_sterilizer(self) -> bool:
        return self.category == "STERILIZER"

    @property
    def is_available(self) -> bool:
        return self.status == MachineStatus.IDLE and self.is_active

    @property
    def needs_maintenance(self) -> bool:
        if self.next_maintenance is None:
            return False
        return datetime.now() >= self.next_maintenance
