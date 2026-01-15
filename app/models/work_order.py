from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseModel
from app.config.constants import WorkOrderStatus, Zones


@dataclass
class ProcessRecord(BaseModel):
    work_order_id: int = 0
    process_type: str = ""
    zone: str = ""
    workstation_id: Optional[int] = None
    workstation_name: str = ""
    operator_id: Optional[int] = None
    operator_name: str = ""
    machine_id: Optional[int] = None
    machine_name: str = ""
    cycle_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = ""
    result: str = ""
    notes: str = ""


@dataclass
class WorkOrder(BaseModel):
    order_number: str = ""
    barcode: str = ""
    item_type: str = ""
    item_id: int = 0
    item_name: str = ""
    item_barcode: str = ""
    department_id: Optional[int] = None
    department_name: str = ""
    priority: int = 0
    status: str = WorkOrderStatus.RECEIVED
    current_zone: str = Zones.DIRTY
    source_department: str = ""
    destination_department: str = ""
    received_by: Optional[int] = None
    received_at: Optional[datetime] = None
    notes: str = ""
    is_urgent: bool = False
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    process_records: List[ProcessRecord] = field(default_factory=list)

    @property
    def zone(self) -> str:
        return WorkOrderStatus.get_zone(self.status) or self.current_zone

    @property
    def is_in_dirty_zone(self) -> bool:
        return self.zone == Zones.DIRTY

    @property
    def is_in_clean_zone(self) -> bool:
        return self.zone == Zones.CLEAN

    @property
    def is_in_sterile_zone(self) -> bool:
        return self.zone == Zones.STERILE

    @property
    def is_completed(self) -> bool:
        return self.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.DISTRIBUTED]

    @property
    def is_rejected(self) -> bool:
        return self.status == WorkOrderStatus.REJECTED

    @property
    def needs_reprocessing(self) -> bool:
        return self.status in [WorkOrderStatus.INSPECTION_FAILED,
                                WorkOrderStatus.REJECTED,
                                WorkOrderStatus.REPROCESSING]

    def get_last_process(self, process_type: str = None) -> Optional[ProcessRecord]:
        records = self.process_records
        if process_type:
            records = [r for r in records if r.process_type == process_type]
        return records[-1] if records else None
