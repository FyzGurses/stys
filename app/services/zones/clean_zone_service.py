from typing import Optional, List, Tuple
from datetime import datetime

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import WorkOrderStatus, Zones, PackagingTypes


class CleanZoneService:

    def __init__(self):
        self.db = get_db()

    def transfer_from_dirty(self, order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    current_zone = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ? AND status = ?
            """, (Zones.CLEAN, WorkOrderStatus.INSPECTING, datetime.now(),
                  order_id, WorkOrderStatus.WASHED))
            self.db.commit()

            self._add_process_record(order_id, "TRANSFER_CLEAN")
            return True, "Temiz alana transfer edildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def start_inspection(self, order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (WorkOrderStatus.INSPECTING, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "INSPECT_START")
            return True, "Kontrol başlatıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def pass_inspection(self, order_id: int, notes: str = "") -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    notes = COALESCE(notes || ' ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.PACKAGING, notes, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "INSPECT_PASS", notes)
            return True, "Kontrol başarılı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def fail_inspection(self, order_id: int, reason: str) -> Tuple[bool, str]:
        if not reason:
            return False, "Başarısızlık nedeni belirtilmeli"

        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    notes = COALESCE(notes || ' FAIL: ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.INSPECTION_FAILED, reason, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "INSPECT_FAIL", reason)
            return True, "Kontrol başarısız kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def start_packaging(self, order_id: int,
                       packaging_type: str) -> Tuple[bool, str]:
        if packaging_type not in [PackagingTypes.WRAP_SINGLE,
                                   PackagingTypes.WRAP_DOUBLE,
                                   PackagingTypes.POUCH,
                                   PackagingTypes.CONTAINER,
                                   PackagingTypes.PEEL_PACK]:
            return False, "Geçersiz paketleme tipi"

        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.PACKAGING, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "PACKAGE_START", packaging_type)
            return True, "Paketleme başlatıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def complete_packaging(self, order_id: int,
                          packaging_type: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (WorkOrderStatus.PACKAGED, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "PACKAGE_COMPLETE", packaging_type)
            return True, "Paketleme tamamlandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_pending_inspection(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.current_zone = ? AND wo.status IN (?, ?)
            ORDER BY wo.priority DESC, wo.created_at
        """, (Zones.CLEAN, WorkOrderStatus.WASHED, WorkOrderStatus.INSPECTING))
        return [dict(row) for row in rows]

    def get_pending_packaging(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.priority DESC, wo.created_at
        """, (WorkOrderStatus.PACKAGING,))
        return [dict(row) for row in rows]

    def get_packaged_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at
        """, (WorkOrderStatus.PACKAGED,))
        return [dict(row) for row in rows]

    def get_failed_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at
        """, (WorkOrderStatus.INSPECTION_FAILED,))
        return [dict(row) for row in rows]

    def send_to_reprocess(self, order_id: int, reason: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    current_zone = ?,
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.REPROCESSING, Zones.DIRTY, datetime.now(), order_id))

            self.db.execute("""
                INSERT INTO reprocessing_records (
                    work_order_id, reason, initiated_by, created_at
                ) VALUES (?, ?, ?, ?)
            """, (
                order_id,
                reason,
                current_session.current_user.user_id if current_session.current_user else None,
                datetime.now()
            ))

            self.db.commit()
            return True, "Tekrar işleme gönderildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _add_process_record(self, order_id: int, process_type: str,
                           notes: str = ""):
        self.db.execute("""
            INSERT INTO process_records (
                work_order_id, process_type, zone, operator_id,
                start_time, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            process_type,
            Zones.CLEAN,
            current_session.current_user.user_id if current_session.current_user else None,
            datetime.now(),
            notes,
            datetime.now()
        ))
        self.db.commit()
