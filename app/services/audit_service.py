from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.core.database import get_db
from app.core.session import current_session
from app.config.constants import AuditActions


@dataclass
class AuditEntry:
    id: int
    operator_id: Optional[int]
    operator_name: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    old_value: str
    new_value: str
    ip_address: str
    details: str
    created_at: datetime


class AuditService:
    def __init__(self):
        self.db = get_db()

    def log(self, action: str, entity_type: str, entity_id: int = None,
           old_value: str = "", new_value: str = "", details: str = ""):
        operator_id = None
        if current_session.current_user:
            operator_id = current_session.current_user.user_id

        try:
            self.db.execute("""
                INSERT INTO audit_log (
                    operator_id, action, entity_type, entity_id,
                    old_value, new_value, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operator_id,
                action,
                entity_type,
                entity_id,
                old_value,
                new_value,
                details,
                datetime.now()
            ))
            self.db.commit()
        except Exception:
            pass

    def log_create(self, entity_type: str, entity_id: int, details: str = ""):
        self.log(AuditActions.CREATE, entity_type, entity_id, details=details)

    def log_update(self, entity_type: str, entity_id: int,
                  old_value: str = "", new_value: str = "", details: str = ""):
        self.log(AuditActions.UPDATE, entity_type, entity_id,
                old_value, new_value, details)

    def log_delete(self, entity_type: str, entity_id: int, details: str = ""):
        self.log(AuditActions.DELETE, entity_type, entity_id, details=details)

    def log_view(self, entity_type: str, entity_id: int = None, details: str = ""):
        self.log(AuditActions.VIEW, entity_type, entity_id, details=details)

    def log_approve(self, entity_type: str, entity_id: int, details: str = ""):
        self.log(AuditActions.APPROVE, entity_type, entity_id, details=details)

    def log_reject(self, entity_type: str, entity_id: int, details: str = ""):
        self.log(AuditActions.REJECT, entity_type, entity_id, details=details)

    def log_scan(self, barcode: str, entity_type: str = "", entity_id: int = None):
        self.log(AuditActions.SCAN, entity_type, entity_id, details=f"Barkod: {barcode}")

    def log_print(self, entity_type: str, entity_id: int, details: str = ""):
        self.log(AuditActions.PRINT, entity_type, entity_id, details=details)

    def get_logs(self, entity_type: str = None, entity_id: int = None,
                operator_id: int = None, action: str = None,
                start_date: datetime = None, end_date: datetime = None,
                limit: int = 100) -> List[AuditEntry]:
        query = """
            SELECT al.*, o.full_name as operator_name
            FROM audit_log al
            LEFT JOIN operators o ON al.operator_id = o.id
            WHERE 1=1
        """
        params = []

        if entity_type:
            query += " AND al.entity_type = ?"
            params.append(entity_type)

        if entity_id:
            query += " AND al.entity_id = ?"
            params.append(entity_id)

        if operator_id:
            query += " AND al.operator_id = ?"
            params.append(operator_id)

        if action:
            query += " AND al.action = ?"
            params.append(action)

        if start_date:
            query += " AND al.created_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND al.created_at <= ?"
            params.append(end_date)

        query += " ORDER BY al.created_at DESC LIMIT ?"
        params.append(limit)

        rows = self.db.fetchall(query, tuple(params))

        return [AuditEntry(
            id=row['id'],
            operator_id=row['operator_id'],
            operator_name=row['operator_name'] or "Sistem",
            action=row['action'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            old_value=row['old_value'] or "",
            new_value=row['new_value'] or "",
            ip_address=row['ip_address'] or "",
            details=row['details'] or "",
            created_at=row['created_at']
        ) for row in rows]

    def get_entity_history(self, entity_type: str, entity_id: int) -> List[AuditEntry]:
        return self.get_logs(entity_type=entity_type, entity_id=entity_id, limit=1000)

    def get_user_activity(self, operator_id: int, days: int = 7) -> List[AuditEntry]:
        start_date = datetime.now() - timedelta(days=days)
        return self.get_logs(operator_id=operator_id, start_date=start_date)

    def get_recent_activity(self, hours: int = 24) -> List[AuditEntry]:
        start_date = datetime.now() - timedelta(hours=hours)
        return self.get_logs(start_date=start_date)

    def get_login_history(self, operator_id: int = None,
                         days: int = 30) -> List[AuditEntry]:
        start_date = datetime.now() - timedelta(days=days)
        return self.get_logs(
            action=AuditActions.LOGIN,
            operator_id=operator_id,
            start_date=start_date
        )

    def get_statistics(self, days: int = 7) -> Dict:
        start_date = datetime.now() - timedelta(days=days)

        total = self.db.fetchone("""
            SELECT COUNT(*) as cnt FROM audit_log WHERE created_at >= ?
        """, (start_date,))

        by_action = self.db.fetchall("""
            SELECT action, COUNT(*) as cnt
            FROM audit_log
            WHERE created_at >= ?
            GROUP BY action
            ORDER BY cnt DESC
        """, (start_date,))

        by_user = self.db.fetchall("""
            SELECT o.full_name, COUNT(*) as cnt
            FROM audit_log al
            JOIN operators o ON al.operator_id = o.id
            WHERE al.created_at >= ?
            GROUP BY al.operator_id
            ORDER BY cnt DESC
            LIMIT 10
        """, (start_date,))

        by_entity = self.db.fetchall("""
            SELECT entity_type, COUNT(*) as cnt
            FROM audit_log
            WHERE created_at >= ?
            GROUP BY entity_type
            ORDER BY cnt DESC
        """, (start_date,))

        return {
            'total': total['cnt'] if total else 0,
            'by_action': {row['action']: row['cnt'] for row in by_action},
            'by_user': {row['full_name']: row['cnt'] for row in by_user},
            'by_entity': {row['entity_type']: row['cnt'] for row in by_entity}
        }
