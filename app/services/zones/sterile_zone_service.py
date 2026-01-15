from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import WorkOrderStatus, SterilizationStatus, Zones
from app.config.settings import settings


class SterileZoneService:

    def __init__(self):
        self.db = get_db()

    def transfer_from_clean(self, order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    current_zone = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ? AND status = ?
            """, (Zones.STERILE, WorkOrderStatus.STERILIZING, datetime.now(),
                  order_id, WorkOrderStatus.PACKAGED))
            self.db.commit()

            self._add_process_record(order_id, "TRANSFER_STERILE")
            return True, "Steril alana transfer edildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def load_to_sterilizer(self, order_id: int, machine_id: int,
                          cycle_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.STERILIZING, datetime.now(), order_id))

            self.db.execute("""
                INSERT INTO cycle_contents (cycle_id, work_order_id, loaded_at)
                VALUES (?, ?, ?)
            """, (cycle_id, order_id, datetime.now()))

            self.db.commit()
            self._add_process_record(order_id, "STERILIZE_LOAD", "", machine_id, cycle_id)
            return True, "Sterilizatöre yüklendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def unload_from_sterilizer(self, order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.STERILIZED, datetime.now(), order_id))

            self.db.execute("""
                UPDATE cycle_contents SET unloaded_at = ?
                WHERE work_order_id = ? AND unloaded_at IS NULL
            """, (datetime.now(), order_id))

            self.db.commit()
            self._add_process_record(order_id, "STERILIZE_UNLOAD")
            return True, "Sterilizatörden çıkarıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def set_pending_release(self, order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (WorkOrderStatus.PENDING_RELEASE, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "PENDING_RELEASE")
            return True, "Onay bekleniyor"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def release_item(self, order_id: int, notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        user = self.db.fetchone(
            "SELECT can_release_load FROM operators WHERE id = ?",
            (current_session.current_user.user_id,)
        )
        if not user or not user['can_release_load']:
            return False, "Onay yetkiniz yok"

        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    notes = COALESCE(notes || ' ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.RELEASED, notes, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "RELEASE", notes)
            return True, "Ürün onaylandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def reject_item(self, order_id: int, reason: str) -> Tuple[bool, str]:
        if not reason:
            return False, "Red nedeni belirtilmeli"

        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    notes = COALESCE(notes || ' REJECT: ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.REJECTED, reason, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "REJECT", reason)
            return True, "Ürün reddedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def store_item(self, order_id: int, location: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    notes = COALESCE(notes || ' DEPO: ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.STORED, location, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "STORE", location)
            return True, "Depoya alındı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def distribute_item(self, order_id: int,
                       destination: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    destination_department = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.DISTRIBUTED, destination, datetime.now(),
                  datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "DISTRIBUTE", destination)
            return True, "Dağıtıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_sterilizing_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at
        """, (WorkOrderStatus.STERILIZING,))
        return [dict(row) for row in rows]

    def get_pending_release_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.priority DESC, wo.created_at
        """, (WorkOrderStatus.PENDING_RELEASE,))
        return [dict(row) for row in rows]

    def get_released_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at DESC
        """, (WorkOrderStatus.RELEASED,))
        return [dict(row) for row in rows]

    def get_stored_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at DESC
        """, (WorkOrderStatus.STORED,))
        return [dict(row) for row in rows]

    def get_rejected_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at DESC
        """, (WorkOrderStatus.REJECTED,))
        return [dict(row) for row in rows]

    def _add_process_record(self, order_id: int, process_type: str,
                           notes: str = "", machine_id: int = None,
                           cycle_id: int = None):
        self.db.execute("""
            INSERT INTO process_records (
                work_order_id, process_type, zone, operator_id,
                machine_id, cycle_id, start_time, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            process_type,
            Zones.STERILE,
            current_session.current_user.user_id if current_session.current_user else None,
            machine_id,
            cycle_id,
            datetime.now(),
            notes,
            datetime.now()
        ))
        self.db.commit()
