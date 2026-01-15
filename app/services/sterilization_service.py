from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.session import current_session
from app.models.sterilization import SterilizationRecord, SterilizationRelease
from app.config.constants import (
    SterilizationStatus, WorkOrderStatus, IndicatorResults, AuditActions
)
from app.config.settings import settings


class SterilizationService:

    def __init__(self):
        self.db = get_db()

    def _generate_record_number(self) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        count = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM sterilization_records WHERE record_number LIKE ?",
            (f"SR{date_part}%",)
        )
        seq = (count['cnt'] or 0) + 1
        return f"SR{date_part}{seq:04d}"

    def create_record(self, work_order_id: int, cycle_id: int,
                     sterilization_method: str) -> Tuple[bool, str, Optional[int]]:
        if not current_session.current_user:
            return False, "Oturum açık değil", None

        work_order = self.db.fetchone(
            "SELECT * FROM work_orders WHERE id = ?",
            (work_order_id,)
        )
        if not work_order:
            return False, "İş emri bulunamadı", None

        cycle = self.db.fetchone("""
            SELECT mc.*, m.name as machine_name, m.id as machine_id
            FROM machine_cycles mc
            JOIN machines m ON mc.machine_id = m.id
            WHERE mc.id = ?
        """, (cycle_id,))
        if not cycle:
            return False, "Çevrim bulunamadı", None

        validity_days = self._get_validity_days(sterilization_method)
        expiry_date = datetime.now() + timedelta(days=validity_days)

        record_number = self._generate_record_number()

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
                sterilization_method,
                current_session.current_user.user_id,
                datetime.now(),
                SterilizationStatus.PENDING_CI,
                expiry_date,
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            record_id = self.db.get_last_insert_id()

            return True, "Sterilizasyon kaydı oluşturuldu", record_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def get_record(self, record_id: int) -> Optional[SterilizationRecord]:
        row = self.db.fetchone("""
            SELECT sr.*, mc.cycle_number, m.name as machine_name,
                   o.full_name as operator_name,
                   rel.full_name as released_by_name,
                   rej.full_name as rejected_by_name
            FROM sterilization_records sr
            LEFT JOIN machine_cycles mc ON sr.cycle_id = mc.id
            LEFT JOIN machines m ON sr.machine_id = m.id
            LEFT JOIN operators o ON sr.operator_id = o.id
            LEFT JOIN operators rel ON sr.released_by = rel.id
            LEFT JOIN operators rej ON sr.rejected_by = rej.id
            WHERE sr.id = ?
        """, (record_id,))

        if not row:
            return None

        record = SterilizationRecord(
            id=row['id'],
            record_number=row['record_number'],
            work_order_id=row['work_order_id'],
            item_type=row['item_type'],
            item_id=row['item_id'],
            item_name=row['item_name'],
            item_barcode=row['item_barcode'],
            cycle_id=row['cycle_id'],
            cycle_number=row['cycle_number'] or "",
            machine_id=row['machine_id'],
            machine_name=row['machine_name'] or "",
            sterilization_method=row['sterilization_method'],
            operator_id=row['operator_id'],
            operator_name=row['operator_name'] or "",
            load_time=row['load_time'],
            unload_time=row['unload_time'],
            status=row['status'],
            ci_result=row['ci_result'] or IndicatorResults.PENDING,
            bi_lot_number=row['bi_lot_number'] or "",
            bi_result=row['bi_result'] or IndicatorResults.PENDING,
            released_by=row['released_by'],
            released_by_name=row['released_by_name'] or "",
            released_at=row['released_at'],
            rejected_by=row['rejected_by'],
            rejected_by_name=row['rejected_by_name'] or "",
            rejected_at=row['rejected_at'],
            rejection_reason=row['rejection_reason'] or "",
            expiry_date=row['expiry_date'],
            storage_location=row['storage_location'] or "",
            created_at=row['created_at']
        )

        record.release_history = self._get_release_history(record_id)
        return record

    def get_record_by_barcode(self, barcode: str) -> Optional[SterilizationRecord]:
        row = self.db.fetchone(
            "SELECT id FROM sterilization_records WHERE item_barcode = ? ORDER BY created_at DESC LIMIT 1",
            (barcode,)
        )
        if row:
            return self.get_record(row['id'])
        return None

    def check_ci(self, record_id: int, result: str, notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if result not in [IndicatorResults.PASS, IndicatorResults.FAIL]:
            return False, "Geçersiz sonuç"

        new_status = SterilizationStatus.PENDING_BI if result == IndicatorResults.PASS else SterilizationStatus.REJECTED

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    ci_result = ?,
                    ci_checked_by = ?,
                    ci_checked_at = ?,
                    status = ?,
                    notes = COALESCE(notes || ' ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (
                result,
                current_session.current_user.user_id,
                datetime.now(),
                new_status,
                notes,
                datetime.now(),
                record_id
            ))
            self.db.commit()

            if result == IndicatorResults.FAIL:
                self._add_release_log(record_id, "CI_FAIL", f"CI başarısız: {notes}")

            return True, "CI kontrolü kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def start_bi_incubation(self, record_id: int, lot_number: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    bi_lot_number = ?,
                    bi_incubation_start = ?,
                    updated_at = ?
                WHERE id = ?
            """, (lot_number, datetime.now(), datetime.now(), record_id))
            self.db.commit()
            return True, "BI inkübasyonu başlatıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def read_bi_result(self, record_id: int, result: str, notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if result not in [IndicatorResults.PASS, IndicatorResults.FAIL]:
            return False, "Geçersiz sonuç"

        new_status = SterilizationStatus.PENDING_RELEASE if result == IndicatorResults.PASS else SterilizationStatus.REJECTED

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    bi_result = ?,
                    bi_read_by = ?,
                    bi_read_at = ?,
                    status = ?,
                    notes = COALESCE(notes || ' ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (
                result,
                current_session.current_user.user_id,
                datetime.now(),
                new_status,
                notes,
                datetime.now(),
                record_id
            ))
            self.db.commit()

            if result == IndicatorResults.FAIL:
                self._add_release_log(record_id, "BI_FAIL", f"BI başarısız: {notes}")

            return True, "BI sonucu kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def release(self, record_id: int, notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if not current_session.current_user.has_permission('sterilization.release'):
            user = self.db.fetchone(
                "SELECT can_release_load FROM operators WHERE id = ?",
                (current_session.current_user.user_id,)
            )
            if not user or not user['can_release_load']:
                return False, "Onay yetkiniz yok"

        record = self.get_record(record_id)
        if not record:
            return False, "Kayıt bulunamadı"

        if not record.can_be_released:
            return False, "Bu kayıt onaylanamaz. İndikatör sonuçlarını kontrol edin."

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    status = ?,
                    released_by = ?,
                    released_at = ?,
                    notes = COALESCE(notes || ' ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (
                SterilizationStatus.RELEASED,
                current_session.current_user.user_id,
                datetime.now(),
                notes,
                datetime.now(),
                record_id
            ))

            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.RELEASED, datetime.now(), record.work_order_id))

            self.db.commit()

            self._add_release_log(record_id, "RELEASE", notes)

            return True, "Sterilizasyon onaylandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def reject(self, record_id: int, reason: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if not reason:
            return False, "Red nedeni belirtilmeli"

        record = self.get_record(record_id)
        if not record:
            return False, "Kayıt bulunamadı"

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    status = ?,
                    rejected_by = ?,
                    rejected_at = ?,
                    rejection_reason = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                SterilizationStatus.REJECTED,
                current_session.current_user.user_id,
                datetime.now(),
                reason,
                datetime.now(),
                record_id
            ))

            self.db.execute("""
                UPDATE work_orders SET status = ?, updated_at = ?
                WHERE id = ?
            """, (WorkOrderStatus.REJECTED, datetime.now(), record.work_order_id))

            self.db.commit()

            self._add_release_log(record_id, "REJECT", reason)

            return True, "Sterilizasyon reddedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_pending_records(self) -> List[SterilizationRecord]:
        rows = self.db.fetchall("""
            SELECT id FROM sterilization_records
            WHERE status IN (?, ?, ?)
            ORDER BY created_at
        """, (
            SterilizationStatus.PENDING_CI,
            SterilizationStatus.PENDING_BI,
            SterilizationStatus.PENDING_RELEASE
        ))
        return [self.get_record(row['id']) for row in rows]

    def get_records_by_cycle(self, cycle_id: int) -> List[SterilizationRecord]:
        rows = self.db.fetchall(
            "SELECT id FROM sterilization_records WHERE cycle_id = ?",
            (cycle_id,)
        )
        return [self.get_record(row['id']) for row in rows]

    def get_expiring_records(self, days: int = 7) -> List[SterilizationRecord]:
        threshold = datetime.now() + timedelta(days=days)
        rows = self.db.fetchall("""
            SELECT id FROM sterilization_records
            WHERE status = ? AND expiry_date <= ?
            ORDER BY expiry_date
        """, (SterilizationStatus.RELEASED, threshold))
        return [self.get_record(row['id']) for row in rows]

    def recall(self, record_id: int, reason: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    status = ?,
                    notes = COALESCE(notes || ' RECALL: ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (SterilizationStatus.RECALLED, reason, datetime.now(), record_id))
            self.db.commit()

            self._add_release_log(record_id, "RECALL", reason)

            return True, "Geri çağırma kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _get_validity_days(self, method: str) -> int:
        if method == "STEAM":
            return settings.sterilization.steam_validity_days
        elif method == "PLASMA":
            return settings.sterilization.plasma_validity_days
        elif method == "ETO":
            return settings.sterilization.eto_validity_days
        return settings.sterilization.default_validity_days

    def _add_release_log(self, record_id: int, action: str, notes: str):
        self.db.execute("""
            INSERT INTO sterilization_release_log (
                sterilization_id, action, performed_by, notes, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            record_id,
            action,
            current_session.current_user.user_id if current_session.current_user else None,
            notes,
            datetime.now()
        ))
        self.db.commit()

    def _get_release_history(self, record_id: int) -> List[SterilizationRelease]:
        rows = self.db.fetchall("""
            SELECT srl.*, o.full_name as performed_by_name
            FROM sterilization_release_log srl
            LEFT JOIN operators o ON srl.performed_by = o.id
            WHERE srl.sterilization_id = ?
            ORDER BY srl.created_at
        """, (record_id,))

        return [SterilizationRelease(
            id=row['id'],
            sterilization_id=row['sterilization_id'],
            action=row['action'],
            performed_by=row['performed_by'],
            performed_by_name=row['performed_by_name'] or "",
            notes=row['notes'] or "",
            performed_at=row['created_at']
        ) for row in rows]
