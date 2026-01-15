from typing import Optional, List, Tuple
from datetime import datetime

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import WorkOrderStatus, Zones


class DirtyZoneService:

    def __init__(self):
        self.db = get_db()

    def receive_item(self, item_type: str, item_id: int,
                    department_id: int = None, priority: int = 0,
                    notes: str = "") -> Tuple[bool, str, Optional[int]]:
        if not current_session.current_user:
            return False, "Oturum açık değil", None

        item_info = self._get_item_info(item_type, item_id)
        if not item_info:
            return False, "Ürün bulunamadı", None

        order_number = self._generate_order_number()

        try:
            self.db.execute("""
                INSERT INTO work_orders (
                    order_number, item_type, item_id, item_name, item_barcode,
                    department_id, priority, status, current_zone,
                    received_by, received_at, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_number,
                item_type,
                item_id,
                item_info['name'],
                item_info['barcode'],
                department_id,
                priority,
                WorkOrderStatus.RECEIVED,
                Zones.DIRTY,
                current_session.current_user.user_id,
                datetime.now(),
                notes,
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            order_id = self.db.get_last_insert_id()

            self._add_process_record(order_id, "RECEIVE")
            return True, "Ürün kabul edildi", order_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def start_washing(self, order_id: int, machine_id: int,
                     cycle_id: int) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (WorkOrderStatus.WASHING, datetime.now(), order_id))

            self.db.execute("""
                INSERT INTO cycle_contents (cycle_id, work_order_id, loaded_at)
                VALUES (?, ?, ?)
            """, (cycle_id, order_id, datetime.now()))

            self.db.commit()
            self._add_process_record(order_id, "WASH_START", machine_id, cycle_id)
            return True, "Yıkama başlatıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def complete_washing(self, order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (WorkOrderStatus.WASHED, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "WASH_COMPLETE")
            return True, "Yıkama tamamlandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_pending_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.current_zone = ? AND wo.status = ?
            ORDER BY wo.priority DESC, wo.created_at
        """, (Zones.DIRTY, WorkOrderStatus.RECEIVED))
        return [dict(row) for row in rows]

    def get_washing_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at
        """, (WorkOrderStatus.WASHING,))
        return [dict(row) for row in rows]

    def get_washed_items(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.created_at
        """, (WorkOrderStatus.WASHED,))
        return [dict(row) for row in rows]

    def _generate_order_number(self) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        count = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM work_orders WHERE order_number LIKE ?",
            (f"WO{date_part}%",)
        )
        seq = (count['cnt'] or 0) + 1
        return f"WO{date_part}{seq:04d}"

    def _get_item_info(self, item_type: str, item_id: int) -> Optional[dict]:
        if item_type == "SET":
            row = self.db.fetchone(
                "SELECT name, barcode FROM instrument_sets WHERE id = ?",
                (item_id,)
            )
        elif item_type == "INSTRUMENT":
            row = self.db.fetchone(
                "SELECT name, barcode FROM instruments WHERE id = ?",
                (item_id,)
            )
        else:
            return None

        if row:
            return {'name': row['name'], 'barcode': row['barcode']}
        return None

    def _add_process_record(self, order_id: int, process_type: str,
                           machine_id: int = None, cycle_id: int = None):
        self.db.execute("""
            INSERT INTO process_records (
                work_order_id, process_type, zone, operator_id,
                machine_id, cycle_id, start_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            process_type,
            Zones.DIRTY,
            current_session.current_user.user_id if current_session.current_user else None,
            machine_id,
            cycle_id,
            datetime.now(),
            datetime.now()
        ))
        self.db.commit()
