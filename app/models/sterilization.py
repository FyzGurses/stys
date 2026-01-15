from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseModel
from app.config.constants import SterilizationStatus, IndicatorResults


@dataclass
class SterilizationRelease(BaseModel):
    sterilization_id: int = 0
    action: str = ""
    performed_by: Optional[int] = None
    performed_by_name: str = ""
    reason: str = ""
    notes: str = ""
    performed_at: Optional[datetime] = None

    @property
    def is_release(self) -> bool:
        return self.action == "RELEASE"

    @property
    def is_rejection(self) -> bool:
        return self.action == "REJECT"


@dataclass
class SterilizationRecord(BaseModel):
    record_number: str = ""
    work_order_id: int = 0
    work_order_number: str = ""
    item_type: str = ""
    item_id: int = 0
    item_name: str = ""
    item_barcode: str = ""
    cycle_id: int = 0
    cycle_number: str = ""
    machine_id: int = 0
    machine_name: str = ""
    sterilization_method: str = ""
    operator_id: Optional[int] = None
    operator_name: str = ""
    load_time: Optional[datetime] = None
    unload_time: Optional[datetime] = None
    status: str = SterilizationStatus.PENDING_CI
    ci_result: str = IndicatorResults.PENDING
    ci_checked_by: Optional[int] = None
    ci_checked_at: Optional[datetime] = None
    bi_lot_number: str = ""
    bi_result: str = IndicatorResults.PENDING
    bi_incubation_start: Optional[datetime] = None
    bi_read_by: Optional[int] = None
    bi_read_at: Optional[datetime] = None
    released_by: Optional[int] = None
    released_by_name: str = ""
    released_at: Optional[datetime] = None
    rejected_by: Optional[int] = None
    rejected_by_name: str = ""
    rejected_at: Optional[datetime] = None
    rejection_reason: str = ""
    expiry_date: Optional[datetime] = None
    storage_location: str = ""
    notes: str = ""
    release_history: List[SterilizationRelease] = field(default_factory=list)
    reprocessing_count: int = 0

    @property
    def is_pending(self) -> bool:
        return self.status in [
            SterilizationStatus.PENDING_CI,
            SterilizationStatus.PENDING_BI,
            SterilizationStatus.PENDING_RELEASE
        ]

    @property
    def is_released(self) -> bool:
        return self.status == SterilizationStatus.RELEASED

    @property
    def is_rejected(self) -> bool:
        return self.status == SterilizationStatus.REJECTED

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return datetime.now() > self.expiry_date

    @property
    def is_sterile(self) -> bool:
        return self.is_released and not self.is_expired

    @property
    def days_until_expiry(self) -> int:
        if self.expiry_date is None:
            return 0
        delta = self.expiry_date - datetime.now()
        return max(0, delta.days)

    @property
    def ci_passed(self) -> bool:
        return self.ci_result == IndicatorResults.PASS

    @property
    def bi_passed(self) -> bool:
        return self.bi_result == IndicatorResults.PASS

    @property
    def indicators_passed(self) -> bool:
        return self.ci_passed and self.bi_passed

    @property
    def can_be_released(self) -> bool:
        return (self.status == SterilizationStatus.PENDING_RELEASE and
                self.indicators_passed)
