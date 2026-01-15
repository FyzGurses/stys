from typing import Optional, List, Tuple
from datetime import datetime

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import SterilizationStatus, WorkOrderStatus, IndicatorResults


class ReleaseService:

    def __init__(self):
        self.db = get_db()

    def can_release(self, record_id: int) -> Tuple[bool, str]:
        record = self.db.fetchone(
            "SELECT * FROM sterilization_records WHERE id = ?",
            (record_id,)
        )
        if not record:
            return False, "Kayıt bulunamadı"

        if record['status'] != SterilizationStatus.PENDING_RELEASE:
            return False, "Kayıt onay bekliyor durumunda değil"

        if record['ci_result'] != IndicatorResults.PASS:
            return False, "CI sonucu başarısız"

        if record['bi_result'] != IndicatorResults.PASS:
            return False, "BI sonucu başarısız"

        return True, "Onaylanabilir"

    def release(self, record_id: int, notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        user = self.db.fetchone(
            "SELECT can_release_load FROM operators WHERE id = ?",
            (current_session.current_user.user_id,)
        )
        if not user or not user['can_release_load']:
            return False, "Onay yetkiniz yok"

        can_release, msg = self.can_release(record_id)
        if not can_release:
            return False, msg

        record = self.db.fetchone(
            "SELECT work_order_id FROM sterilization_records WHERE id = ?",
            (record_id,)
        )

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    status = ?,
                    released_by = ?,
                    released_at = ?,
                    notes = COALESCE(notes || ' ONAY: ' || ?, notes),
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

            if record and record['work_order_id']:
                self.db.execute("""
                    UPDATE work_orders SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (WorkOrderStatus.RELEASED, datetime.now(), record['work_order_id']))

            self.db.commit()
            self._log_action(record_id, "RELEASE", notes)

            return True, "Sterilizasyon onaylandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def reject(self, record_id: int, reason: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if not reason:
            return False, "Red nedeni belirtilmeli"

        record = self.db.fetchone(
            "SELECT work_order_id FROM sterilization_records WHERE id = ?",
            (record_id,)
        )
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

            if record['work_order_id']:
                self.db.execute("""
                    UPDATE work_orders SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (WorkOrderStatus.REJECTED, datetime.now(), record['work_order_id']))

            self.db.commit()
            self._log_action(record_id, "REJECT", reason)

            return True, "Sterilizasyon reddedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def recall(self, record_id: int, reason: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if not reason:
            return False, "Geri çağırma nedeni belirtilmeli"

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    status = ?,
                    notes = COALESCE(notes || ' RECALL: ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (SterilizationStatus.RECALLED, reason, datetime.now(), record_id))
            self.db.commit()

            self._log_action(record_id, "RECALL", reason)
            return True, "Geri çağırma kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def mark_as_used(self, record_id: int, notes: str = "") -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    status = ?,
                    notes = COALESCE(notes || ' ' || ?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (SterilizationStatus.USED, notes, datetime.now(), record_id))
            self.db.commit()

            self._log_action(record_id, "USED", notes)
            return True, "Kullanıldı olarak işaretlendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_pending_release(self) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT sr.id, sr.record_number, sr.item_name, sr.item_barcode,
                   sr.ci_result, sr.bi_result, sr.load_time, sr.unload_time,
                   m.name as machine_name, o.full_name as operator_name
            FROM sterilization_records sr
            LEFT JOIN machines m ON sr.machine_id = m.id
            LEFT JOIN operators o ON sr.operator_id = o.id
            WHERE sr.status = ?
            ORDER BY sr.unload_time
        """, (SterilizationStatus.PENDING_RELEASE,))
        return [dict(row) for row in rows]

    def get_released(self, limit: int = 50) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT sr.id, sr.record_number, sr.item_name, sr.item_barcode,
                   sr.released_at, sr.expiry_date, sr.storage_location,
                   rel.full_name as released_by_name
            FROM sterilization_records sr
            LEFT JOIN operators rel ON sr.released_by = rel.id
            WHERE sr.status = ?
            ORDER BY sr.released_at DESC
            LIMIT ?
        """, (SterilizationStatus.RELEASED, limit))
        return [dict(row) for row in rows]

    def get_rejected(self, limit: int = 50) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT sr.id, sr.record_number, sr.item_name, sr.item_barcode,
                   sr.rejected_at, sr.rejection_reason,
                   rej.full_name as rejected_by_name
            FROM sterilization_records sr
            LEFT JOIN operators rej ON sr.rejected_by = rej.id
            WHERE sr.status = ?
            ORDER BY sr.rejected_at DESC
            LIMIT ?
        """, (SterilizationStatus.REJECTED, limit))
        return [dict(row) for row in rows]

    def get_history(self, record_id: int) -> List[dict]:
        rows = self.db.fetchall("""
            SELECT srl.*, o.full_name as performed_by_name
            FROM sterilization_release_log srl
            LEFT JOIN operators o ON srl.performed_by = o.id
            WHERE srl.sterilization_id = ?
            ORDER BY srl.created_at
        """, (record_id,))
        return [dict(row) for row in rows]

    def _log_action(self, record_id: int, action: str, notes: str):
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
