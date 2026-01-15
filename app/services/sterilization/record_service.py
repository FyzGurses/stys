from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import SterilizationStatus, IndicatorResults
from app.config.settings import settings


class SterilizationRecordService:

    def __init__(self):
        self.db = get_db()

    def create(self, work_order_id: int, cycle_id: int,
              method: str) -> Tuple[bool, str, Optional[int]]:
        if not current_session.current_user:
            return False, "Oturum açık değil", None

        work_order = self.db.fetchone(
            "SELECT * FROM work_orders WHERE id = ?",
            (work_order_id,)
        )
        if not work_order:
            return False, "İş emri bulunamadı", None

        cycle = self.db.fetchone("""
            SELECT mc.*, m.id as machine_id, m.name as machine_name
            FROM machine_cycles mc
            JOIN machines m ON mc.machine_id = m.id
            WHERE mc.id = ?
        """, (cycle_id,))
        if not cycle:
            return False, "Çevrim bulunamadı", None

        validity_days = self._get_validity_days(method)
        expiry_date = datetime.now() + timedelta(days=validity_days)
        record_number = self._generate_number()

        try:
            self.db.execute("""
                INSERT INTO sterilization_records (
                    record_number, work_order_id, item_type, item_id,
                    item_name, item_barcode, cycle_id, machine_id,
                    sterilization_method, operator_id, load_time,
                    status, expiry_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_number,
                work_order_id,
                work_order['item_type'],
                work_order['item_id'],
                work_order['item_name'],
                work_order['item_barcode'],
                cycle_id,
                cycle['machine_id'],
                method,
                current_session.current_user.user_id,
                datetime.now(),
                SterilizationStatus.PENDING_CI,
                expiry_date,
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            record_id = self.db.get_last_insert_id()
            return True, "Kayıt oluşturuldu", record_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def get(self, record_id: int) -> Optional[dict]:
        row = self.db.fetchone("""
            SELECT sr.*, mc.cycle_number, m.name as machine_name,
                   o.full_name as operator_name
            FROM sterilization_records sr
            LEFT JOIN machine_cycles mc ON sr.cycle_id = mc.id
            LEFT JOIN machines m ON sr.machine_id = m.id
            LEFT JOIN operators o ON sr.operator_id = o.id
            WHERE sr.id = ?
        """, (record_id,))
        return dict(row) if row else None

    def get_by_barcode(self, barcode: str) -> Optional[dict]:
        row = self.db.fetchone("""
            SELECT id FROM sterilization_records
            WHERE item_barcode = ?
            ORDER BY created_at DESC LIMIT 1
        """, (barcode,))
        if row:
            return self.get(row['id'])
        return None

    def get_by_cycle(self, cycle_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT id FROM sterilization_records WHERE cycle_id = ?
        """, (cycle_id,))
        return [self.get(row['id']) for row in rows]

    def get_by_status(self, status: str) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT id FROM sterilization_records
            WHERE status = ?
            ORDER BY created_at
        """, (status,))
        return [self.get(row['id']) for row in rows]

    def get_pending(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT id FROM sterilization_records
            WHERE status IN (?, ?, ?)
            ORDER BY created_at
        """, (
            SterilizationStatus.PENDING_CI,
            SterilizationStatus.PENDING_BI,
            SterilizationStatus.PENDING_RELEASE
        ))
        return [self.get(row['id']) for row in rows]

    def get_expiring(self, days: int = 7) -> List[dict]:
        threshold = datetime.now() + timedelta(days=days)
        rows = self.db.fetchall("""
            SELECT id FROM sterilization_records
            WHERE status = ? AND expiry_date <= ?
            ORDER BY expiry_date
        """, (SterilizationStatus.RELEASED, threshold))
        return [self.get(row['id']) for row in rows]

    def update_status(self, record_id: int, status: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE sterilization_records SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, datetime.now(), record_id))
            self.db.commit()
            return True, "Durum güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def set_unload_time(self, record_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE sterilization_records SET unload_time = ?, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), datetime.now(), record_id))
            self.db.commit()
            return True, "Çıkış zamanı kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _generate_number(self) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        count = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM sterilization_records WHERE record_number LIKE ?",
            (f"SR{date_part}%",)
        )
        seq = (count['cnt'] or 0) + 1
        return f"SR{date_part}{seq:04d}"

    def _get_validity_days(self, method: str) -> int:
        if method == "STEAM":
            return settings.sterilization.steam_validity_days
        elif method == "PLASMA":
            return settings.sterilization.plasma_validity_days
        elif method == "ETO":
            return settings.sterilization.eto_validity_days
        return settings.sterilization.default_validity_days
