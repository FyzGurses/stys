from typing import Optional, List, Dict, Tuple
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.session import current_session
from app.models.work_order import WorkOrder, ProcessRecord
from app.config.constants import WorkOrderStatus, Zones, AuditActions


class WorkOrderService:

    def __init__(self):
        self.db = get_db()

    def _generate_order_number(self) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        count = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM work_orders WHERE order_number LIKE ?",
            (f"WO{date_part}%",)
        )
        seq = (count['cnt'] or 0) + 1
        return f"WO{date_part}{seq:04d}"

    def create_work_order(self, item_type: str, item_id: int,
                         department_id: int = None, priority: int = 0,
                         notes: str = "") -> Tuple[bool, str, Optional[int]]:
        if not current_session.current_user:
            return False, "Oturum açık değil", None

        item_info = self._get_item_info(item_type, item_id)
        if not item_info:
            return False, "Ürün bulunamadı", None

        order_number = self._generate_order_number()
        barcode = f"WO{uuid.uuid4().hex[:8].upper()}"

        try:
            self.db.execute("""
                INSERT INTO work_orders (
                    order_number, barcode, item_type, item_id, item_name, item_barcode,
                    department_id, priority, status, current_zone, received_by,
                    received_at, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_number,
                barcode,
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

            self._add_process_record(order_id, "RECEIVE", Zones.DIRTY)

            return True, "İş emri oluşturuldu", order_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def get_work_order(self, order_id: int) -> Optional[WorkOrder]:
        row = self.db.fetchone("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.id = ?
        """, (order_id,))

        if not row:
            return None

        order = WorkOrder(
            id=row['id'],
            order_number=row['order_number'],
            barcode=row['barcode'],
            item_type=row['item_type'],
            item_id=row['item_id'],
            item_name=row['item_name'],
            item_barcode=row['item_barcode'],
            department_id=row['department_id'],
            department_name=row['department_name'] or "",
            priority=row['priority'],
            status=row['status'],
            current_zone=row['current_zone'],
            received_by=row['received_by'],
            received_at=row['received_at'],
            notes=row['notes'],
            created_at=row['created_at']
        )

        order.process_records = self._get_process_records(order_id)
        return order

    def get_work_order_by_barcode(self, barcode: str) -> Optional[WorkOrder]:
        row = self.db.fetchone(
            "SELECT id FROM work_orders WHERE barcode = ? OR item_barcode = ?",
            (barcode, barcode)
        )
        if row:
            return self.get_work_order(row['id'])
        return None

    def get_work_orders_by_zone(self, zone: str, status: str = None) -> List[WorkOrder]:
        query = """
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.current_zone = ?
        """
        params = [zone]

        if status:
            query += " AND wo.status = ?"
            params.append(status)

        query += " ORDER BY wo.priority DESC, wo.created_at"

        rows = self.db.fetchall(query, tuple(params))
        return [self._row_to_work_order(row) for row in rows]

    def get_work_orders_by_status(self, status: str) -> List[WorkOrder]:
        rows = self.db.fetchall("""
            SELECT wo.*, d.name as department_name
            FROM work_orders wo
            LEFT JOIN departments d ON wo.department_id = d.id
            WHERE wo.status = ?
            ORDER BY wo.priority DESC, wo.created_at
        """, (status,))
        return [self._row_to_work_order(row) for row in rows]

    def update_status(self, order_id: int, new_status: str,
                     notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        order = self.get_work_order(order_id)
        if not order:
            return False, "İş emri bulunamadı"

        new_zone = WorkOrderStatus.get_zone(new_status)
        if new_zone and not current_session.current_user.can_access_zone(new_zone):
            return False, f"{new_zone} alanına erişim yetkiniz yok"

        try:
            self.db.execute("""
                UPDATE work_orders SET
                    status = ?,
                    current_zone = COALESCE(?, current_zone),
                    updated_at = ?
                WHERE id = ?
            """, (new_status, new_zone, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, new_status, new_zone or order.current_zone, notes)

            return True, "Durum güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def start_washing(self, order_id: int, machine_id: int,
                     cycle_id: int = None) -> Tuple[bool, str]:
        return self._start_machine_process(
            order_id, machine_id, cycle_id,
            WorkOrderStatus.WASHING, "WASH"
        )

    def complete_washing(self, order_id: int) -> Tuple[bool, str]:
        return self.update_status(order_id, WorkOrderStatus.WASHED)

    def start_inspection(self, order_id: int) -> Tuple[bool, str]:
        return self.update_status(order_id, WorkOrderStatus.INSPECTING)

    def pass_inspection(self, order_id: int) -> Tuple[bool, str]:
        return self.update_status(order_id, WorkOrderStatus.PACKAGING)

    def fail_inspection(self, order_id: int, reason: str) -> Tuple[bool, str]:
        return self.update_status(order_id, WorkOrderStatus.INSPECTION_FAILED, reason)

    def complete_packaging(self, order_id: int, packaging_type: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (WorkOrderStatus.PACKAGED, datetime.now(), order_id))
            self.db.commit()

            self._add_process_record(order_id, "PACKAGE", Zones.CLEAN, packaging_type)
            return True, "Paketleme tamamlandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def start_sterilization(self, order_id: int, machine_id: int,
                           cycle_id: int) -> Tuple[bool, str]:
        return self._start_machine_process(
            order_id, machine_id, cycle_id,
            WorkOrderStatus.STERILIZING, "STERILIZE"
        )

    def send_to_reprocessing(self, order_id: int, reason: str) -> Tuple[bool, str]:
        order = self.get_work_order(order_id)
        if not order:
            return False, "İş emri bulunamadı"

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
            """, (order_id, reason, current_session.current_user.user_id, datetime.now()))

            self.db.commit()
            return True, "Tekrar işleme gönderildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _start_machine_process(self, order_id: int, machine_id: int,
                              cycle_id: int, status: str,
                              process_type: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        try:
            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ? WHERE id = ?
            """, (status, datetime.now(), order_id))

            if cycle_id:
                self.db.execute("""
                    INSERT INTO cycle_contents (cycle_id, work_order_id, loaded_at)
                    VALUES (?, ?, ?)
                """, (cycle_id, order_id, datetime.now()))

            self.db.commit()

            zone = WorkOrderStatus.get_zone(status)
            self._add_process_record(order_id, process_type, zone, "", machine_id, cycle_id)

            return True, "İşlem başlatıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _add_process_record(self, order_id: int, process_type: str,
                           zone: str, notes: str = "",
                           machine_id: int = None, cycle_id: int = None):
        self.db.execute("""
            INSERT INTO process_records (
                work_order_id, process_type, zone, operator_id,
                machine_id, cycle_id, start_time, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            process_type,
            zone,
            current_session.current_user.user_id if current_session.current_user else None,
            machine_id,
            cycle_id,
            datetime.now(),
            notes,
            datetime.now()
        ))
        self.db.commit()

    def _get_process_records(self, order_id: int) -> List[ProcessRecord]:
        rows = self.db.fetchall("""
            SELECT pr.*, o.full_name as operator_name, m.name as machine_name
            FROM process_records pr
            LEFT JOIN operators o ON pr.operator_id = o.id
            LEFT JOIN machines m ON pr.machine_id = m.id
            WHERE pr.work_order_id = ?
            ORDER BY pr.created_at
        """, (order_id,))

        return [ProcessRecord(
            id=row['id'],
            work_order_id=row['work_order_id'],
            process_type=row['process_type'],
            zone=row['zone'],
            operator_id=row['operator_id'],
            operator_name=row['operator_name'] or "",
            machine_id=row['machine_id'],
            machine_name=row['machine_name'] or "",
            cycle_id=row['cycle_id'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            notes=row['notes']
        ) for row in rows]

    def _get_item_info(self, item_type: str, item_id: int) -> Optional[Dict]:
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

    def _row_to_work_order(self, row) -> WorkOrder:
        return WorkOrder(
            id=row['id'],
            order_number=row['order_number'],
            barcode=row['barcode'],
            item_type=row['item_type'],
            item_id=row['item_id'],
            item_name=row['item_name'],
            item_barcode=row['item_barcode'],
            department_id=row['department_id'],
            department_name=row['department_name'] or "",
            priority=row['priority'],
            status=row['status'],
            current_zone=row['current_zone'],
            notes=row['notes'],
            created_at=row['created_at']
        )
