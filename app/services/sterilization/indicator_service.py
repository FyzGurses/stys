from typing import Optional, Tuple
from datetime import datetime

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import SterilizationStatus, IndicatorResults


class IndicatorService:

    def __init__(self):
        self.db = get_db()

    def check_ci(self, record_id: int, result: str,
                notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if result not in [IndicatorResults.PASS, IndicatorResults.FAIL]:
            return False, "Geçersiz sonuç"

        new_status = (SterilizationStatus.PENDING_BI
                     if result == IndicatorResults.PASS
                     else SterilizationStatus.REJECTED)

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    ci_result = ?,
                    ci_checked_by = ?,
                    ci_checked_at = ?,
                    status = ?,
                    notes = COALESCE(notes || ' CI: ' || ?, notes),
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
                self._log_action(record_id, "CI_FAIL", f"CI başarısız: {notes}")

            return True, "CI kontrolü kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def start_bi_incubation(self, record_id: int,
                           lot_number: str) -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if not lot_number:
            return False, "Lot numarası gerekli"

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    bi_lot_number = ?,
                    bi_incubation_start = ?,
                    updated_at = ?
                WHERE id = ?
            """, (lot_number, datetime.now(), datetime.now(), record_id))
            self.db.commit()

            self._log_action(record_id, "BI_START", f"Lot: {lot_number}")
            return True, "BI inkübasyonu başlatıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def read_bi_result(self, record_id: int, result: str,
                      notes: str = "") -> Tuple[bool, str]:
        if not current_session.current_user:
            return False, "Oturum açık değil"

        if result not in [IndicatorResults.PASS, IndicatorResults.FAIL]:
            return False, "Geçersiz sonuç"

        new_status = (SterilizationStatus.PENDING_RELEASE
                     if result == IndicatorResults.PASS
                     else SterilizationStatus.REJECTED)

        try:
            self.db.execute("""
                UPDATE sterilization_records SET
                    bi_result = ?,
                    bi_read_by = ?,
                    bi_read_at = ?,
                    status = ?,
                    notes = COALESCE(notes || ' BI: ' || ?, notes),
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

            action = "BI_PASS" if result == IndicatorResults.PASS else "BI_FAIL"
            self._log_action(record_id, action, notes)

            return True, "BI sonucu kaydedildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_ci_pending(self) -> list:
        rows = self.db.fetchall("""
            SELECT sr.id, sr.record_number, sr.item_name, sr.item_barcode,
                   sr.load_time, m.name as machine_name
            FROM sterilization_records sr
            LEFT JOIN machines m ON sr.machine_id = m.id
            WHERE sr.status = ?
            ORDER BY sr.load_time
        """, (SterilizationStatus.PENDING_CI,))
        return [dict(row) for row in rows]

    def get_bi_pending(self) -> list:
        rows = self.db.fetchall("""
            SELECT sr.id, sr.record_number, sr.item_name, sr.item_barcode,
                   sr.bi_lot_number, sr.bi_incubation_start,
                   m.name as machine_name
            FROM sterilization_records sr
            LEFT JOIN machines m ON sr.machine_id = m.id
            WHERE sr.status = ?
            ORDER BY sr.bi_incubation_start
        """, (SterilizationStatus.PENDING_BI,))
        return [dict(row) for row in rows]

    def get_bi_ready_to_read(self, hours: int = 24) -> list:
        rows = self.db.fetchall("""
            SELECT sr.id, sr.record_number, sr.item_name, sr.item_barcode,
                   sr.bi_lot_number, sr.bi_incubation_start,
                   m.name as machine_name
            FROM sterilization_records sr
            LEFT JOIN machines m ON sr.machine_id = m.id
            WHERE sr.status = ?
              AND sr.bi_incubation_start IS NOT NULL
              AND datetime(sr.bi_incubation_start, '+' || ? || ' hours') <= datetime('now')
            ORDER BY sr.bi_incubation_start
        """, (SterilizationStatus.PENDING_BI, hours))
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
