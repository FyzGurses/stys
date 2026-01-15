"""
Sterilizasyon Takip Sistemi - Veritabanı Modülü v2.0
Kirli → Temiz → Steril Alan İş Akışı
"""

import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, List, Dict
import hashlib

DATABASE_PATH = os.path.expanduser("~/data/sterilizasyon.db")


def init_database():
    """Veritabanı ve tabloları oluştur"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        # ==================== ALAN VE İSTASYON TABLOLARI ====================

        # Çalışma Alanları (Kirli, Temiz, Steril)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                description TEXT,
                sequence INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # İş İstasyonları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workstations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                workstation_type TEXT NOT NULL,
                location TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id) REFERENCES zones (id)
            )
        """)

        # ==================== ROL VE YETKİ TABLOLARI ====================

        # Sistem Rolleri
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                level INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rol Yetkileri (İzinler)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                module TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rol-İzin İlişkisi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id),
                UNIQUE(role_id, permission_id)
            )
        """)

        # ==================== KULLANICI TABLOLARI ====================

        # Operatörler / Kullanıcılar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT UNIQUE NOT NULL,
                employee_id TEXT UNIQUE,
                name TEXT NOT NULL,
                title TEXT,
                pin_hash TEXT,
                password_hash TEXT,
                photo_path TEXT,
                email TEXT,
                phone TEXT,
                role_id INTEGER,
                role TEXT DEFAULT 'OPERATOR',
                department_id INTEGER,
                supervisor_id INTEGER,
                can_approve_sterilization INTEGER DEFAULT 0,
                can_release_load INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                locked INTEGER DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                password_changed_at TIMESTAMP,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (department_id) REFERENCES departments (id),
                FOREIGN KEY (supervisor_id) REFERENCES operators (id),
                FOREIGN KEY (created_by) REFERENCES operators (id)
            )
        """)

        # Operatör Alan Yetkileri
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operator_zone_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER NOT NULL,
                zone_id INTEGER NOT NULL,
                can_access INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (zone_id) REFERENCES zones (id),
                UNIQUE(operator_id, zone_id)
            )
        """)

        # Oturum Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER NOT NULL,
                zone_id INTEGER,
                workstation_id INTEGER,
                login_time TIMESTAMP NOT NULL,
                logout_time TIMESTAMP,
                logout_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (zone_id) REFERENCES zones (id),
                FOREIGN KEY (workstation_id) REFERENCES workstations (id)
            )
        """)

        # ==================== BÖLÜM VE DOKTOR TABLOLARI ====================

        # Bölümler
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                floor TEXT,
                building TEXT,
                contact_phone TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Doktorlar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT,
                department_id INTEGER,
                specialization TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        """)

        # ==================== MAKİNE VE EKİPMAN TABLOLARI ====================

        # Makineler (Yıkama, Otoklav, ETO, Plazma vb.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                machine_type TEXT NOT NULL,
                machine_category TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                serial_number TEXT,
                capacity INTEGER,
                location TEXT,
                ip_address TEXT,
                port INTEGER,
                status TEXT DEFAULT 'IDLE',
                last_cycle_end TIMESTAMP,
                installation_date DATE,
                last_maintenance DATE,
                next_maintenance DATE,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id) REFERENCES zones (id)
            )
        """)

        # Makine Programları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS machine_programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER NOT NULL,
                program_code TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                temperature REAL,
                pressure REAL,
                duration_minutes INTEGER,
                dry_time_minutes INTEGER,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                UNIQUE(machine_id, program_code)
            )
        """)

        # Makine Döngüleri (Batch)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS machine_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER NOT NULL,
                program_id INTEGER,
                batch_number TEXT UNIQUE NOT NULL,
                operator_id INTEGER NOT NULL,
                status TEXT DEFAULT 'RUNNING',
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                actual_temperature REAL,
                actual_pressure REAL,
                actual_duration INTEGER,
                cycle_result TEXT,
                bi_test_required INTEGER DEFAULT 0,
                bi_test_result TEXT,
                bi_result_time TIMESTAMP,
                ci_result TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (program_id) REFERENCES machine_programs (id),
                FOREIGN KEY (operator_id) REFERENCES operators (id)
            )
        """)

        # ==================== ALET VE SET TABLOLARI ====================

        # Alet Kategorileri
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instrument_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER,
                sterilization_method TEXT DEFAULT 'STEAM',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES instrument_categories (id)
            )
        """)

        # Cerrahi Aletler
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER,
                brand TEXT,
                model TEXT,
                serial_number TEXT,
                status TEXT DEFAULT 'AVAILABLE',
                condition TEXT DEFAULT 'GOOD',
                usage_count INTEGER DEFAULT 0,
                max_usage_count INTEGER,
                purchase_date DATE,
                warranty_end DATE,
                notes TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES instrument_categories (id)
            )
        """)

        # Setler
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                set_type TEXT DEFAULT 'STANDARD',
                department_id INTEGER,
                priority INTEGER DEFAULT 0,
                standard_count INTEGER DEFAULT 0,
                sterilization_method TEXT DEFAULT 'STEAM',
                validity_days INTEGER DEFAULT 30,
                status TEXT DEFAULT 'AVAILABLE',
                current_location TEXT,
                notes TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        """)

        # Set İçeriği
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS set_instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                instrument_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                position TEXT,
                is_required INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (set_id) REFERENCES sets (id),
                FOREIGN KEY (instrument_id) REFERENCES instruments (id),
                UNIQUE(set_id, instrument_id)
            )
        """)

        # ==================== KONTEYNER TABLOLARI ====================

        # Sterilizasyon Konteynerleri
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS containers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                container_type TEXT NOT NULL,
                size TEXT,
                brand TEXT,
                model TEXT,
                color TEXT,
                capacity INTEGER,
                status TEXT DEFAULT 'AVAILABLE',
                current_location TEXT,
                usage_count INTEGER DEFAULT 0,
                last_inspection DATE,
                next_inspection DATE,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (container_type) REFERENCES container_types (name)
            )
        """)

        # Konteyner Tipleri
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS container_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                filter_type TEXT,
                filter_change_cycles INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==================== İŞ AKIŞI TABLOLARI ====================

        # Ana İş Emri / Takip
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                item_type TEXT NOT NULL,
                set_id INTEGER,
                instrument_id INTEGER,
                container_id INTEGER,
                current_status TEXT DEFAULT 'RECEIVED',
                current_zone_id INTEGER,
                priority INTEGER DEFAULT 0,
                source_department_id INTEGER,
                source_description TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (set_id) REFERENCES sets (id),
                FOREIGN KEY (instrument_id) REFERENCES instruments (id),
                FOREIGN KEY (container_id) REFERENCES containers (id),
                FOREIGN KEY (current_zone_id) REFERENCES zones (id),
                FOREIGN KEY (source_department_id) REFERENCES departments (id),
                FOREIGN KEY (created_by) REFERENCES operators (id)
            )
        """)

        # İşlem Kayıtları (Tüm Adımlar)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                zone_id INTEGER NOT NULL,
                process_type TEXT NOT NULL,
                process_status TEXT DEFAULT 'COMPLETED',
                operator_id INTEGER NOT NULL,
                workstation_id INTEGER,
                machine_id INTEGER,
                cycle_id INTEGER,
                container_id INTEGER,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (zone_id) REFERENCES zones (id),
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (workstation_id) REFERENCES workstations (id),
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (cycle_id) REFERENCES machine_cycles (id),
                FOREIGN KEY (container_id) REFERENCES containers (id)
            )
        """)

        # Döngü İçeriği (Hangi iş emri hangi döngüde)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cycle_contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                work_order_id INTEGER NOT NULL,
                load_position TEXT,
                load_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unload_time TIMESTAMP,
                result TEXT,
                FOREIGN KEY (cycle_id) REFERENCES machine_cycles (id),
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                UNIQUE(cycle_id, work_order_id)
            )
        """)

        # ==================== STERİLİZASYON KAYITLARI ====================

        # Sterilizasyon Sonuçları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sterilization_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                cycle_id INTEGER NOT NULL,
                sterilization_date TIMESTAMP NOT NULL,
                expiry_date TIMESTAMP NOT NULL,
                label_printed INTEGER DEFAULT 0,
                label_print_time TIMESTAMP,
                status TEXT DEFAULT 'PENDING_RELEASE',
                ci_check_result TEXT,
                ci_checked_by INTEGER,
                ci_checked_at TIMESTAMP,
                bi_required INTEGER DEFAULT 0,
                bi_lot_number TEXT,
                bi_incubation_start TIMESTAMP,
                bi_result TEXT,
                bi_result_by INTEGER,
                bi_result_at TIMESTAMP,
                release_decision TEXT,
                released_by INTEGER,
                released_at TIMESTAMP,
                release_notes TEXT,
                rejection_reason TEXT,
                rejected_by INTEGER,
                rejected_at TIMESTAMP,
                reprocess_work_order_id INTEGER,
                recall_reason TEXT,
                recalled_by INTEGER,
                recalled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (cycle_id) REFERENCES machine_cycles (id),
                FOREIGN KEY (ci_checked_by) REFERENCES operators (id),
                FOREIGN KEY (bi_result_by) REFERENCES operators (id),
                FOREIGN KEY (released_by) REFERENCES operators (id),
                FOREIGN KEY (rejected_by) REFERENCES operators (id),
                FOREIGN KEY (reprocess_work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (recalled_by) REFERENCES operators (id)
            )
        """)

        # Sterilizasyon Onay/Red Kayıtları (Audit)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sterilization_release_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sterilization_record_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                action_by INTEGER NOT NULL,
                action_time TIMESTAMP NOT NULL,
                previous_status TEXT,
                new_status TEXT,
                ci_result TEXT,
                bi_result TEXT,
                reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sterilization_record_id) REFERENCES sterilization_records (id),
                FOREIGN KEY (action_by) REFERENCES operators (id)
            )
        """)

        # Tekrar İşleme (Reprocessing) Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reprocessing_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_work_order_id INTEGER NOT NULL,
                new_work_order_id INTEGER NOT NULL,
                original_sterilization_id INTEGER,
                reprocess_reason TEXT NOT NULL,
                reprocess_type TEXT NOT NULL,
                initiated_by INTEGER NOT NULL,
                initiated_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (new_work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (original_sterilization_id) REFERENCES sterilization_records (id),
                FOREIGN KEY (initiated_by) REFERENCES operators (id)
            )
        """)

        # Dağıtım Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distribution_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sterilization_record_id INTEGER NOT NULL,
                department_id INTEGER NOT NULL,
                requested_by TEXT,
                distributed_by INTEGER NOT NULL,
                distribution_time TIMESTAMP NOT NULL,
                return_time TIMESTAMP,
                returned_by INTEGER,
                patient_id TEXT,
                surgery_id TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sterilization_record_id) REFERENCES sterilization_records (id),
                FOREIGN KEY (department_id) REFERENCES departments (id),
                FOREIGN KEY (distributed_by) REFERENCES operators (id),
                FOREIGN KEY (returned_by) REFERENCES operators (id)
            )
        """)

        # ==================== KALİTE KONTROL TABLOLARI ====================

        # Set Kontrol Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                operator_id INTEGER NOT NULL,
                inspection_time TIMESTAMP NOT NULL,
                total_items INTEGER,
                checked_items INTEGER,
                passed_items INTEGER,
                failed_items INTEGER,
                missing_items TEXT,
                damaged_items TEXT,
                result TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (operator_id) REFERENCES operators (id)
            )
        """)

        # Paketleme Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS packaging_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                operator_id INTEGER NOT NULL,
                container_id INTEGER,
                packaging_type TEXT NOT NULL,
                packaging_time TIMESTAMP NOT NULL,
                double_wrap INTEGER DEFAULT 0,
                ci_placed INTEGER DEFAULT 1,
                ci_type TEXT,
                ci_lot_number TEXT,
                seal_integrity INTEGER DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (container_id) REFERENCES containers (id)
            )
        """)

        # ==================== OLAY VE BAKIM TABLOLARI ====================

        # Olay Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT NOT NULL,
                severity TEXT DEFAULT 'LOW',
                work_order_id INTEGER,
                instrument_id INTEGER,
                set_id INTEGER,
                container_id INTEGER,
                machine_id INTEGER,
                reported_by INTEGER NOT NULL,
                incident_time TIMESTAMP NOT NULL,
                description TEXT NOT NULL,
                action_taken TEXT,
                resolved_by INTEGER,
                resolved_at TIMESTAMP,
                status TEXT DEFAULT 'OPEN',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (instrument_id) REFERENCES instruments (id),
                FOREIGN KEY (set_id) REFERENCES sets (id),
                FOREIGN KEY (container_id) REFERENCES containers (id),
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (reported_by) REFERENCES operators (id),
                FOREIGN KEY (resolved_by) REFERENCES operators (id)
            )
        """)

        # Bakım Kayıtları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL,
                machine_id INTEGER,
                instrument_id INTEGER,
                container_id INTEGER,
                maintenance_type TEXT NOT NULL,
                performed_by TEXT,
                maintenance_date TIMESTAMP NOT NULL,
                next_maintenance_date TIMESTAMP,
                description TEXT,
                cost REAL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (instrument_id) REFERENCES instruments (id),
                FOREIGN KEY (container_id) REFERENCES containers (id)
            )
        """)

        # ==================== DEPO VE KONUM TABLOLARI ====================

        # Depo Konumları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location_type TEXT NOT NULL,
                shelf TEXT,
                row TEXT,
                column TEXT,
                capacity INTEGER,
                current_count INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id) REFERENCES zones (id)
            )
        """)

        # Stok Hareketleri
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER,
                from_location_id INTEGER,
                to_location_id INTEGER,
                operator_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                movement_time TIMESTAMP NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                FOREIGN KEY (from_location_id) REFERENCES storage_locations (id),
                FOREIGN KEY (to_location_id) REFERENCES storage_locations (id),
                FOREIGN KEY (operator_id) REFERENCES operators (id)
            )
        """)

        # ==================== SİSTEM TABLOLARI ====================

        # Sistem Audit Log (Tüm İşlemler)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER,
                session_id INTEGER,
                action_type TEXT NOT NULL,
                module TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                entity_barcode TEXT,
                action_description TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES operators (id),
                FOREIGN KEY (session_id) REFERENCES login_sessions (id)
            )
        """)

        # Sistem Ayarları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                value_type TEXT DEFAULT 'STRING',
                description TEXT,
                updated_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (updated_by) REFERENCES operators (id),
                UNIQUE(category, key)
            )
        """)

        # ==================== İNDEKSLER ====================

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operators_card ON operators(card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operators_role ON operators(role_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_machines_barcode ON machines(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_instruments_barcode ON instruments(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sets_barcode ON sets(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_containers_barcode ON containers(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_orders_barcode ON work_orders(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(current_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cycles_batch ON machine_cycles(batch_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sterilization_expiry ON sterilization_records(expiry_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sterilization_status ON sterilization_records(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_time ON audit_log(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_operator ON audit_log(operator_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_process_records_order ON process_records(work_order_id)")

        conn.commit()
        print(f"Veritabanı başlatıldı: {DATABASE_PATH}")


@contextmanager
def get_connection():
    """Veritabanı bağlantısı context manager"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ==================== OPERATÖR İŞLEMLERİ ====================

def authenticate_by_card(card_id: str) -> Optional[Dict]:
    """Kart ID ile operatör doğrulama"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, GROUP_CONCAT(z.code) as zone_permissions
            FROM operators o
            LEFT JOIN operator_zone_permissions ozp ON o.id = ozp.operator_id
            LEFT JOIN zones z ON ozp.zone_id = z.id AND ozp.can_access = 1
            WHERE o.card_id = ? AND o.active = 1
            GROUP BY o.id
        """, (card_id,))
        row = cursor.fetchone()
        if row:
            # Son giriş zamanını güncelle
            cursor.execute("UPDATE operators SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row['id'],))
            conn.commit()
            return dict(row)
        return None


def get_operator_zones(operator_id: int) -> List[Dict]:
    """Operatörün yetkili olduğu alanları getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT z.*
            FROM zones z
            JOIN operator_zone_permissions ozp ON z.id = ozp.zone_id
            WHERE ozp.operator_id = ? AND ozp.can_access = 1 AND z.active = 1
            ORDER BY z.sequence
        """, (operator_id,))
        return [dict(row) for row in cursor.fetchall()]


def create_login_session(operator_id: int, zone_id: int = None, workstation_id: int = None) -> int:
    """Yeni oturum oluştur"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO login_sessions (operator_id, zone_id, workstation_id, login_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (operator_id, zone_id, workstation_id))
        conn.commit()
        return cursor.lastrowid


def end_login_session(session_id: int, reason: str = "LOGOUT") -> bool:
    """Oturumu sonlandır"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE login_sessions
            SET logout_time = CURRENT_TIMESTAMP, logout_reason = ?
            WHERE id = ? AND logout_time IS NULL
        """, (reason, session_id))
        conn.commit()
        return cursor.rowcount > 0


# ==================== ALAN VE MAKİNE İŞLEMLERİ ====================

def get_all_zones() -> List[Dict]:
    """Tüm alanları getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM zones WHERE active = 1 ORDER BY sequence")
        return [dict(row) for row in cursor.fetchall()]


def get_zone_by_code(code: str) -> Optional[Dict]:
    """Alan koduna göre getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM zones WHERE code = ? AND active = 1", (code,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_machines_by_zone(zone_id: int, category: str = None) -> List[Dict]:
    """Alana göre makineleri getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM machines WHERE zone_id = ? AND active = 1"
        params = [zone_id]
        if category:
            query += " AND machine_category = ?"
            params.append(category)
        query += " ORDER BY name"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_machine_by_barcode(barcode: str) -> Optional[Dict]:
    """Makine barkoduna göre getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, z.code as zone_code, z.name as zone_name
            FROM machines m
            JOIN zones z ON m.zone_id = z.id
            WHERE m.barcode = ? AND m.active = 1
        """, (barcode,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_machine_status(machine_id: int, status: str) -> bool:
    """Makine durumunu güncelle"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE machines SET status = ? WHERE id = ?", (status, machine_id))
        conn.commit()
        return cursor.rowcount > 0


# ==================== İŞ EMRİ İŞLEMLERİ ====================

def create_work_order(item_type: str, item_id: int, operator_id: int, source_dept_id: int = None, source_desc: str = None) -> int:
    """Yeni iş emri oluştur"""
    import uuid
    barcode = f"WO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    with get_connection() as conn:
        cursor = conn.cursor()

        # Kirli alan ID'sini al
        cursor.execute("SELECT id FROM zones WHERE code = 'DIRTY'")
        dirty_zone = cursor.fetchone()
        zone_id = dirty_zone['id'] if dirty_zone else None

        set_id = item_id if item_type == 'SET' else None
        instrument_id = item_id if item_type == 'INSTRUMENT' else None
        container_id = item_id if item_type == 'CONTAINER' else None

        cursor.execute("""
            INSERT INTO work_orders (barcode, item_type, set_id, instrument_id, container_id,
                                    current_status, current_zone_id, source_department_id,
                                    source_description, created_by)
            VALUES (?, ?, ?, ?, ?, 'RECEIVED', ?, ?, ?, ?)
        """, (barcode, item_type, set_id, instrument_id, container_id, zone_id,
              source_dept_id, source_desc, operator_id))
        conn.commit()
        return cursor.lastrowid


def get_work_order_by_barcode(barcode: str) -> Optional[Dict]:
    """İş emri barkoduna göre getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wo.*,
                   s.name as set_name, s.barcode as set_barcode,
                   i.name as instrument_name, i.barcode as instrument_barcode,
                   c.name as container_name, c.barcode as container_barcode,
                   z.code as zone_code, z.name as zone_name,
                   d.name as source_department_name
            FROM work_orders wo
            LEFT JOIN sets s ON wo.set_id = s.id
            LEFT JOIN instruments i ON wo.instrument_id = i.id
            LEFT JOIN containers c ON wo.container_id = c.id
            LEFT JOIN zones z ON wo.current_zone_id = z.id
            LEFT JOIN departments d ON wo.source_department_id = d.id
            WHERE wo.barcode = ?
        """, (barcode,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_work_order_by_item(item_type: str, item_barcode: str) -> Optional[Dict]:
    """Ürün barkoduna göre aktif iş emri getir"""
    with get_connection() as conn:
        cursor = conn.cursor()

        if item_type == 'SET':
            cursor.execute("""
                SELECT wo.* FROM work_orders wo
                JOIN sets s ON wo.set_id = s.id
                WHERE s.barcode = ? AND wo.completed_at IS NULL
                ORDER BY wo.created_at DESC LIMIT 1
            """, (item_barcode,))
        elif item_type == 'INSTRUMENT':
            cursor.execute("""
                SELECT wo.* FROM work_orders wo
                JOIN instruments i ON wo.instrument_id = i.id
                WHERE i.barcode = ? AND wo.completed_at IS NULL
                ORDER BY wo.created_at DESC LIMIT 1
            """, (item_barcode,))
        else:
            return None

        row = cursor.fetchone()
        return dict(row) if row else None


def update_work_order_status(work_order_id: int, status: str, zone_id: int = None) -> bool:
    """İş emri durumunu güncelle"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if zone_id:
            cursor.execute("""
                UPDATE work_orders SET current_status = ?, current_zone_id = ?
                WHERE id = ?
            """, (status, zone_id, work_order_id))
        else:
            cursor.execute("UPDATE work_orders SET current_status = ? WHERE id = ?",
                         (status, work_order_id))
        conn.commit()
        return cursor.rowcount > 0


def get_work_orders_by_status(status: str, zone_code: str = None, limit: int = 50) -> List[Dict]:
    """Duruma göre iş emirlerini getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT wo.*,
                   s.name as set_name, s.barcode as set_barcode,
                   i.name as instrument_name,
                   z.code as zone_code, z.name as zone_name
            FROM work_orders wo
            LEFT JOIN sets s ON wo.set_id = s.id
            LEFT JOIN instruments i ON wo.instrument_id = i.id
            LEFT JOIN zones z ON wo.current_zone_id = z.id
            WHERE wo.current_status = ?
        """
        params = [status]

        if zone_code:
            query += " AND z.code = ?"
            params.append(zone_code)

        query += " ORDER BY wo.priority DESC, wo.created_at LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


# ==================== İŞLEM KAYDI İŞLEMLERİ ====================

def create_process_record(work_order_id: int, zone_id: int, process_type: str,
                         operator_id: int, **kwargs) -> int:
    """İşlem kaydı oluştur"""
    with get_connection() as conn:
        cursor = conn.cursor()

        fields = ['work_order_id', 'zone_id', 'process_type', 'operator_id', 'start_time']
        values = [work_order_id, zone_id, process_type, operator_id, datetime.now()]

        for key in ['workstation_id', 'machine_id', 'cycle_id', 'container_id', 'notes']:
            if key in kwargs and kwargs[key] is not None:
                fields.append(key)
                values.append(kwargs[key])

        placeholders = ', '.join(['?' for _ in values])
        field_names = ', '.join(fields)

        cursor.execute(f"INSERT INTO process_records ({field_names}) VALUES ({placeholders})", values)
        conn.commit()
        return cursor.lastrowid


def complete_process_record(record_id: int, status: str = 'COMPLETED', notes: str = None) -> bool:
    """İşlem kaydını tamamla"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE process_records
            SET end_time = CURRENT_TIMESTAMP, process_status = ?, notes = COALESCE(?, notes)
            WHERE id = ?
        """, (status, notes, record_id))
        conn.commit()
        return cursor.rowcount > 0


# ==================== MAKİNE DÖNGÜSÜ İŞLEMLERİ ====================

def create_machine_cycle(machine_id: int, operator_id: int, program_id: int = None) -> Dict:
    """Yeni makine döngüsü başlat"""
    batch_number = f"B-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO machine_cycles (machine_id, program_id, batch_number, operator_id, start_time)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (machine_id, program_id, batch_number, operator_id))

        cycle_id = cursor.lastrowid

        # Makine durumunu güncelle
        cursor.execute("UPDATE machines SET status = 'RUNNING' WHERE id = ?", (machine_id,))
        conn.commit()

        return {'id': cycle_id, 'batch_number': batch_number}


def add_to_cycle(cycle_id: int, work_order_id: int, position: str = None) -> int:
    """Döngüye iş emri ekle"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cycle_contents (cycle_id, work_order_id, load_position)
            VALUES (?, ?, ?)
        """, (cycle_id, work_order_id, position))
        conn.commit()
        return cursor.lastrowid


def complete_machine_cycle(cycle_id: int, result: str, **kwargs) -> bool:
    """Makine döngüsünü tamamla"""
    with get_connection() as conn:
        cursor = conn.cursor()

        updates = ['end_time = CURRENT_TIMESTAMP', 'status = ?', 'cycle_result = ?']
        values = ['COMPLETED', result]

        for key in ['actual_temperature', 'actual_pressure', 'actual_duration',
                    'bi_test_required', 'ci_result', 'notes']:
            if key in kwargs and kwargs[key] is not None:
                updates.append(f"{key} = ?")
                values.append(kwargs[key])

        values.append(cycle_id)
        cursor.execute(f"UPDATE machine_cycles SET {', '.join(updates)} WHERE id = ?", values)

        # Makine durumunu güncelle
        cursor.execute("""
            UPDATE machines SET status = 'IDLE', last_cycle_end = CURRENT_TIMESTAMP
            WHERE id = (SELECT machine_id FROM machine_cycles WHERE id = ?)
        """, (cycle_id,))

        conn.commit()
        return cursor.rowcount > 0


def get_cycle_contents(cycle_id: int) -> List[Dict]:
    """Döngü içeriğini getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cc.*, wo.barcode as work_order_barcode, wo.item_type,
                   s.name as set_name, s.barcode as set_barcode
            FROM cycle_contents cc
            JOIN work_orders wo ON cc.work_order_id = wo.id
            LEFT JOIN sets s ON wo.set_id = s.id
            WHERE cc.cycle_id = ?
        """, (cycle_id,))
        return [dict(row) for row in cursor.fetchall()]


# ==================== STERİLİZASYON KAYITLARI ====================

def create_sterilization_record(work_order_id: int, cycle_id: int, validity_days: int = 30) -> int:
    """Sterilizasyon kaydı oluştur"""
    now = datetime.now()
    expiry = now + timedelta(days=validity_days)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sterilization_records (work_order_id, cycle_id, sterilization_date, expiry_date)
            VALUES (?, ?, ?, ?)
        """, (work_order_id, cycle_id, now, expiry))
        conn.commit()
        return cursor.lastrowid


def get_sterilization_status(work_order_id: int) -> Optional[Dict]:
    """İş emrinin sterilizasyon durumunu getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sr.*, mc.batch_number, m.name as machine_name
            FROM sterilization_records sr
            JOIN machine_cycles mc ON sr.cycle_id = mc.id
            JOIN machines m ON mc.machine_id = m.id
            WHERE sr.work_order_id = ?
            ORDER BY sr.sterilization_date DESC LIMIT 1
        """, (work_order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ==================== SET VE ALET İŞLEMLERİ ====================

def get_set_by_barcode(barcode: str) -> Optional[Dict]:
    """Set barkoduna göre getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, d.name as department_name,
                   (SELECT COUNT(*) FROM set_instruments WHERE set_id = s.id) as instrument_count
            FROM sets s
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE s.barcode = ? AND s.active = 1
        """, (barcode,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_set_instruments(set_id: int) -> List[Dict]:
    """Set içeriğini getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT si.*, i.barcode, i.name, i.status, i.condition,
                   ic.name as category_name
            FROM set_instruments si
            JOIN instruments i ON si.instrument_id = i.id
            LEFT JOIN instrument_categories ic ON i.category_id = ic.id
            WHERE si.set_id = ?
            ORDER BY si.position, i.name
        """, (set_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_container_by_barcode(barcode: str) -> Optional[Dict]:
    """Konteyner barkoduna göre getir"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM containers WHERE barcode = ? AND active = 1", (barcode,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ==================== İSTATİSTİKLER ====================

def get_zone_statistics(zone_code: str) -> Dict:
    """Alan istatistiklerini getir"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM zones WHERE code = ?", (zone_code,))
        zone = cursor.fetchone()
        if not zone:
            return {}
        zone_id = zone['id']

        stats = {}

        # Bekleyen iş emirleri
        status_map = {
            'DIRTY': ['RECEIVED', 'WASHING'],
            'CLEAN': ['WASHED', 'INSPECTING', 'PACKAGING'],
            'STERILE': ['PACKAGED', 'STERILIZING', 'STERILIZED', 'STORED']
        }

        statuses = status_map.get(zone_code, [])
        if statuses:
            placeholders = ', '.join(['?' for _ in statuses])
            cursor.execute(f"""
                SELECT current_status, COUNT(*) as count
                FROM work_orders
                WHERE current_status IN ({placeholders})
                GROUP BY current_status
            """, statuses)
            stats['by_status'] = {row['current_status']: row['count'] for row in cursor.fetchall()}

        # Çalışan makineler
        cursor.execute("""
            SELECT COUNT(*) as running FROM machines
            WHERE zone_id = ? AND status = 'RUNNING'
        """, (zone_id,))
        stats['running_machines'] = cursor.fetchone()['running']

        # Bugünkü işlemler
        cursor.execute("""
            SELECT COUNT(*) as today_count FROM process_records
            WHERE zone_id = ? AND DATE(start_time) = DATE('now')
        """, (zone_id,))
        stats['today_processes'] = cursor.fetchone()['today_count']

        return stats


def get_dashboard_stats() -> Dict:
    """Genel dashboard istatistikleri"""
    with get_connection() as conn:
        cursor = conn.cursor()

        stats = {}

        # Toplam aktif iş emirleri
        cursor.execute("SELECT COUNT(*) as count FROM work_orders WHERE completed_at IS NULL")
        stats['active_work_orders'] = cursor.fetchone()['count']

        # Duruma göre dağılım
        cursor.execute("""
            SELECT current_status, COUNT(*) as count
            FROM work_orders WHERE completed_at IS NULL
            GROUP BY current_status
        """)
        stats['by_status'] = {row['current_status']: row['count'] for row in cursor.fetchall()}

        # Bugün tamamlanan
        cursor.execute("""
            SELECT COUNT(*) as count FROM work_orders
            WHERE DATE(completed_at) = DATE('now')
        """)
        stats['completed_today'] = cursor.fetchone()['count']

        # Süresi dolacaklar (7 gün)
        cursor.execute("""
            SELECT COUNT(*) as count FROM sterilization_records
            WHERE expiry_date BETWEEN datetime('now') AND datetime('now', '+7 days')
            AND status = 'VALID'
        """)
        stats['expiring_soon'] = cursor.fetchone()['count']

        # Süresi dolmuşlar
        cursor.execute("""
            SELECT COUNT(*) as count FROM sterilization_records
            WHERE expiry_date < datetime('now') AND status = 'VALID'
        """)
        stats['expired'] = cursor.fetchone()['count']

        # Açık olaylar
        cursor.execute("SELECT COUNT(*) as count FROM incidents WHERE status = 'OPEN'")
        stats['open_incidents'] = cursor.fetchone()['count']

        # Çalışan makineler
        cursor.execute("SELECT COUNT(*) as count FROM machines WHERE status = 'RUNNING'")
        stats['running_machines'] = cursor.fetchone()['count']

        return stats


# ==================== DEMO VERİ ====================

def insert_demo_data():
    """Kapsamlı demo veri"""

    print("=" * 60)
    print("  STERİLİZASYON TAKİP SİSTEMİ - DEMO VERİ")
    print("=" * 60)

    with get_connection() as conn:
        cursor = conn.cursor()

        # ==================== ALANLAR ====================
        print("\n[1/9] Çalışma alanları oluşturuluyor...")
        zones = [
            ("DIRTY", "Kirli Alan", "#e74c3c", "Dekontaminasyon ve yıkama alanı", 1),
            ("CLEAN", "Temiz Alan", "#f39c12", "Kontrol, montaj ve paketleme alanı", 2),
            ("STERILE", "Steril Alan", "#27ae60", "Sterilizasyon ve depolama alanı", 3),
        ]

        zone_ids = {}
        for code, name, color, desc, seq in zones:
            try:
                cursor.execute("""
                    INSERT INTO zones (code, name, color, description, sequence)
                    VALUES (?, ?, ?, ?, ?)
                """, (code, name, color, desc, seq))
                zone_ids[code] = cursor.lastrowid
                print(f"    + {name} ({code})")
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM zones WHERE code = ?", (code,))
                zone_ids[code] = cursor.fetchone()['id']

        # ==================== OPERATÖRLER ====================
        print("\n[2/9] Operatörler oluşturuluyor...")
        operators = [
            ("CARD001", "EMP001", "Ayşe Yılmaz", "Şef", "SUPERVISOR", ["DIRTY", "CLEAN", "STERILE"]),
            ("CARD002", "EMP002", "Fatma Kaya", "Teknisyen", "OPERATOR", ["DIRTY", "CLEAN"]),
            ("CARD003", "EMP003", "Zehra Demir", "Teknisyen", "OPERATOR", ["DIRTY", "CLEAN"]),
            ("CARD004", "EMP004", "Hatice Öztürk", "Teknisyen", "OPERATOR", ["CLEAN", "STERILE"]),
            ("CARD005", "EMP005", "Emine Çelik", "Teknisyen", "OPERATOR", ["STERILE"]),
            ("CARD006", "EMP006", "Merve Aydın", "Hemşire", "NURSE", ["STERILE"]),
            ("CARD007", "EMP007", "Selin Arslan", "Hemşire", "NURSE", ["STERILE"]),
            ("CARD008", "EMP008", "Deniz Şahin", "Yönetici", "ADMIN", ["DIRTY", "CLEAN", "STERILE"]),
        ]

        op_ids = {}
        for card_id, emp_id, name, title, role, zones_list in operators:
            try:
                cursor.execute("""
                    INSERT INTO operators (card_id, employee_id, name, title, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (card_id, emp_id, name, title, role))
                op_id = cursor.lastrowid
                op_ids[card_id] = op_id
                print(f"    + {card_id} - {name} ({role})")

                # Alan yetkileri
                for zone_code in zones_list:
                    zone_id = zone_ids.get(zone_code)
                    if zone_id:
                        cursor.execute("""
                            INSERT INTO operator_zone_permissions (operator_id, zone_id, can_access)
                            VALUES (?, ?, 1)
                        """, (op_id, zone_id))
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM operators WHERE card_id = ?", (card_id,))
                row = cursor.fetchone()
                if row:
                    op_ids[card_id] = row['id']

        # ==================== BÖLÜMLER ====================
        print("\n[3/9] Bölümler oluşturuluyor...")
        departments = [
            ("AME", "Ameliyathane", "2", "Ana Bina"),
            ("END", "Endoskopi Ünitesi", "1", "Ana Bina"),
            ("YBU", "Yoğun Bakım", "3", "Ana Bina"),
            ("ACL", "Acil Servis", "Zemin", "Ana Bina"),
            ("KDC", "Kalp Damar Cerrahisi", "4", "Cerrahi Blok"),
            ("ORT", "Ortopedi", "3", "Cerrahi Blok"),
            ("BNC", "Beyin Cerrahisi", "5", "Cerrahi Blok"),
        ]

        dept_ids = {}
        for code, name, floor, building in departments:
            try:
                cursor.execute("""
                    INSERT INTO departments (code, name, floor, building)
                    VALUES (?, ?, ?, ?)
                """, (code, name, floor, building))
                dept_ids[code] = cursor.lastrowid
                print(f"    + {name}")
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM departments WHERE code = ?", (code,))
                dept_ids[code] = cursor.fetchone()['id']

        # ==================== MAKİNELER ====================
        print("\n[4/9] Makineler oluşturuluyor...")
        machines = [
            # Kirli Alan - Yıkama Makineleri
            ("DIRTY", "WD-001", "Yıkama Dezenfektör 1", "WASHER_DISINFECTOR", "WASHER", "Getinge", "46-Series", 8),
            ("DIRTY", "WD-002", "Yıkama Dezenfektör 2", "WASHER_DISINFECTOR", "WASHER", "Getinge", "46-Series", 8),
            ("DIRTY", "US-001", "Ultrasonik Yıkama 1", "ULTRASONIC", "WASHER", "Elma", "S300H", 4),

            # Steril Alan - Otoklavlar
            ("STERILE", "ST-001", "Otoklav 1", "STEAM", "STERILIZER", "Getinge", "HS66-17", 6),
            ("STERILE", "ST-002", "Otoklav 2", "STEAM", "STERILIZER", "Getinge", "HS66-17", 6),
            ("STERILE", "ST-003", "Otoklav 3 (Acil)", "STEAM", "STERILIZER", "Tuttnauer", "3870EA", 2),
            ("STERILE", "PL-001", "Plazma Sterilizatör", "PLASMA", "STERILIZER", "Sterrad", "100NX", 4),
            ("STERILE", "ET-001", "ETO Sterilizatör", "ETO", "STERILIZER", "3M", "Steri-Vac", 4),
        ]

        machine_ids = {}
        for zone_code, barcode, name, m_type, category, brand, model, capacity in machines:
            try:
                zone_id = zone_ids.get(zone_code)
                cursor.execute("""
                    INSERT INTO machines (zone_id, barcode, name, machine_type, machine_category,
                                         brand, model, capacity, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'IDLE')
                """, (zone_id, barcode, name, m_type, category, brand, model, capacity))
                machine_ids[barcode] = cursor.lastrowid
                print(f"    + {barcode} - {name}")
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM machines WHERE barcode = ?", (barcode,))
                machine_ids[barcode] = cursor.fetchone()['id']

        # Makine Programları
        print("\n    Makine programları ekleniyor...")
        programs = [
            # Yıkama programları
            ("WD-001", "STD", "Standart Yıkama", 93, None, 45, 15),
            ("WD-001", "INT", "Yoğun Yıkama", 93, None, 60, 20),
            ("WD-002", "STD", "Standart Yıkama", 93, None, 45, 15),

            # Otoklav programları
            ("ST-001", "134-4", "134°C / 4 dk", 134, 2.1, 4, 20),
            ("ST-001", "121-15", "121°C / 15 dk", 121, 1.1, 15, 30),
            ("ST-002", "134-4", "134°C / 4 dk", 134, 2.1, 4, 20),
            ("ST-003", "FLASH", "Flash Sterilizasyon", 134, 2.1, 3, 10),

            # Plazma programları
            ("PL-001", "STD", "Standart Plazma", 50, None, 47, 15),
            ("PL-001", "ADV", "Gelişmiş Plazma", 50, None, 72, 20),
        ]

        for m_barcode, p_code, p_name, temp, pressure, duration, dry_time in programs:
            m_id = machine_ids.get(m_barcode)
            if m_id:
                try:
                    cursor.execute("""
                        INSERT INTO machine_programs (machine_id, program_code, name,
                                                     temperature, pressure, duration_minutes, dry_time_minutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (m_id, p_code, p_name, temp, pressure, duration, dry_time))
                except sqlite3.IntegrityError:
                    pass

        # ==================== ALET KATEGORİLERİ ====================
        print("\n[5/9] Alet kategorileri oluşturuluyor...")
        categories = [
            ("KES", "Kesici Aletler", "Makas, bistüri, osteotom", "STEAM"),
            ("TUT", "Tutucu Aletler", "Forseps, klemp, penset", "STEAM"),
            ("EKA", "Ekartörler", "Doku ve organ ayırıcılar", "STEAM"),
            ("SUT", "Sütür Aletleri", "İğne tutucu ve dikiş aletleri", "STEAM"),
            ("LAP", "Laparoskopik Aletler", "Minimal invaziv cerrahi", "PLASMA"),
            ("END", "Endoskopik Aletler", "Tanısal ve tedavi endoskoplar", "PLASMA"),
            ("ORT", "Ortopedik Aletler", "Kemik ve eklem cerrahisi", "STEAM"),
            ("KAR", "Kardiyovasküler Aletler", "Kalp ve damar cerrahisi", "STEAM"),
        ]

        cat_ids = {}
        for code, name, desc, method in categories:
            try:
                cursor.execute("""
                    INSERT INTO instrument_categories (code, name, description, sterilization_method)
                    VALUES (?, ?, ?, ?)
                """, (code, name, desc, method))
                cat_ids[code] = cursor.lastrowid
                print(f"    + {name}")
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM instrument_categories WHERE code = ?", (code,))
                cat_ids[code] = cursor.fetchone()['id']

        # ==================== ALETLER ====================
        print("\n[6/9] Cerrahi aletler oluşturuluyor...")
        instruments = [
            ("ALT-KES-001", "Metzenbaum Makas 18cm", "KES", "Aesculap"),
            ("ALT-KES-002", "Mayo Makas 17cm", "KES", "Martin"),
            ("ALT-KES-003", "İris Makas 11.5cm", "KES", "Storz"),
            ("ALT-KES-004", "Bistüri Sapı No:3", "KES", "Swann-Morton"),
            ("ALT-KES-005", "Bistüri Sapı No:4", "KES", "Swann-Morton"),
            ("ALT-TUT-001", "Kelly Forseps 14cm", "TUT", "Aesculap"),
            ("ALT-TUT-002", "Kocher Klemp 16cm", "TUT", "Martin"),
            ("ALT-TUT-003", "Mosquito Klemp", "TUT", "Storz"),
            ("ALT-TUT-004", "Allis Klemp 15cm", "TUT", "Aesculap"),
            ("ALT-TUT-005", "DeBakey Forseps 20cm", "TUT", "Scanlan"),
            ("ALT-TUT-006", "Adson Forseps 12cm", "TUT", "Aesculap"),
            ("ALT-EKA-001", "Langenbeck Ekartör", "EKA", "Aesculap"),
            ("ALT-EKA-002", "Army-Navy Ekartör", "EKA", "Sklar"),
            ("ALT-EKA-003", "Richardson Ekartör", "EKA", "Martin"),
            ("ALT-EKA-004", "Deaver Ekartör", "EKA", "Aesculap"),
            ("ALT-SUT-001", "Mayo-Hegar İğne Tutucu 18cm", "SUT", "Aesculap"),
            ("ALT-SUT-002", "Crile-Wood İğne Tutucu", "SUT", "Martin"),
            ("ALT-LAP-001", "Laparoskop 10mm 0°", "LAP", "Storz"),
            ("ALT-LAP-002", "Laparoskop 10mm 30°", "LAP", "Storz"),
            ("ALT-LAP-003", "Trokar 10mm", "LAP", "Ethicon"),
            ("ALT-LAP-004", "Trokar 5mm", "LAP", "Ethicon"),
            ("ALT-LAP-005", "Grasper 5mm", "LAP", "Storz"),
            ("ALT-LAP-006", "Makas 5mm", "LAP", "Storz"),
            ("ALT-END-001", "Gastroskop", "END", "Olympus"),
            ("ALT-END-002", "Kolonoskop", "END", "Olympus"),
            ("ALT-END-003", "Biyopsi Forsepsi", "END", "Olympus"),
            ("ALT-ORT-001", "Kemik Keskisi 10mm", "ORT", "Synthes"),
            ("ALT-ORT-002", "Liston Kemik Makası", "ORT", "Aesculap"),
            ("ALT-ORT-003", "Periost Elevatörü", "ORT", "Martin"),
            ("ALT-KAR-001", "Satinsky Klemp", "KAR", "Scanlan"),
            ("ALT-KAR-002", "Bulldog Klemp Seti", "KAR", "Scanlan"),
        ]

        inst_ids = {}
        for barcode, name, cat_code, brand in instruments:
            try:
                cat_id = cat_ids.get(cat_code)
                cursor.execute("""
                    INSERT INTO instruments (barcode, name, category_id, brand, status, condition)
                    VALUES (?, ?, ?, ?, 'AVAILABLE', 'GOOD')
                """, (barcode, name, cat_id, brand))
                inst_ids[barcode] = cursor.lastrowid
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM instruments WHERE barcode = ?", (barcode,))
                inst_ids[barcode] = cursor.fetchone()['id']
        print(f"    + {len(instruments)} alet eklendi")

        # ==================== SETLER ====================
        print("\n[7/9] Cerrahi setler oluşturuluyor...")
        sets_data = [
            ("SET-GEN-001", "Genel Cerrahi Temel Seti", "AME", 30, "STEAM",
             ["ALT-KES-001", "ALT-KES-002", "ALT-TUT-001", "ALT-TUT-002", "ALT-TUT-006",
              "ALT-EKA-001", "ALT-EKA-002", "ALT-SUT-001"]),
            ("SET-GEN-002", "Laparotomi Seti", "AME", 30, "STEAM",
             ["ALT-KES-001", "ALT-KES-004", "ALT-TUT-002", "ALT-TUT-004",
              "ALT-EKA-003", "ALT-EKA-004", "ALT-SUT-001", "ALT-SUT-002"]),
            ("SET-LAP-001", "Laparoskopi Seti", "AME", 14, "PLASMA",
             ["ALT-LAP-001", "ALT-LAP-003", "ALT-LAP-004", "ALT-LAP-005", "ALT-LAP-006"]),
            ("SET-LAP-002", "Laparoskopi Seti 2", "AME", 14, "PLASMA",
             ["ALT-LAP-002", "ALT-LAP-003", "ALT-LAP-004", "ALT-LAP-005"]),
            ("SET-END-001", "Üst GİS Endoskopi Seti", "END", 1, "PLASMA",
             ["ALT-END-001", "ALT-END-003"]),
            ("SET-END-002", "Alt GİS Endoskopi Seti", "END", 1, "PLASMA",
             ["ALT-END-002", "ALT-END-003"]),
            ("SET-ORT-001", "Ortopedi Temel Seti", "ORT", 30, "STEAM",
             ["ALT-ORT-001", "ALT-ORT-002", "ALT-ORT-003", "ALT-SUT-001"]),
            ("SET-KAR-001", "Kardiyak Cerrahi Seti", "KDC", 30, "STEAM",
             ["ALT-KAR-001", "ALT-KAR-002", "ALT-TUT-005", "ALT-SUT-001", "ALT-SUT-002"]),
            ("SET-ACL-001", "Acil Küçük Cerrahi Seti", "ACL", 30, "STEAM",
             ["ALT-KES-003", "ALT-KES-004", "ALT-TUT-003", "ALT-TUT-006", "ALT-SUT-002"]),
        ]

        set_ids = {}
        for barcode, name, dept_code, validity, method, inst_list in sets_data:
            try:
                dept_id = dept_ids.get(dept_code)
                cursor.execute("""
                    INSERT INTO sets (barcode, name, department_id, validity_days,
                                     sterilization_method, standard_count, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'AVAILABLE')
                """, (barcode, name, dept_id, validity, method, len(inst_list)))
                set_id = cursor.lastrowid
                set_ids[barcode] = set_id
                print(f"    + {barcode} - {name}")

                # Set içeriği
                for pos, inst_barcode in enumerate(inst_list, 1):
                    inst_id = inst_ids.get(inst_barcode)
                    if inst_id:
                        cursor.execute("""
                            INSERT INTO set_instruments (set_id, instrument_id, quantity, position)
                            VALUES (?, ?, 1, ?)
                        """, (set_id, inst_id, str(pos)))
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM sets WHERE barcode = ?", (barcode,))
                set_ids[barcode] = cursor.fetchone()['id']

        # ==================== KONTEYNERLER ====================
        print("\n[8/9] Konteynerler oluşturuluyor...")

        # Konteyner tipleri
        container_types = [
            ("RIGID_S", "Rijit Konteyner Small", "Küçük rijit konteyner", "PAPER", 500),
            ("RIGID_M", "Rijit Konteyner Medium", "Orta rijit konteyner", "PAPER", 500),
            ("RIGID_L", "Rijit Konteyner Large", "Büyük rijit konteyner", "PAPER", 500),
            ("FLASH", "Flash Konteyner", "Acil sterilizasyon", "NONE", None),
        ]

        for code, name, desc, filter_type, filter_cycles in container_types:
            try:
                cursor.execute("""
                    INSERT INTO container_types (code, name, description, filter_type, filter_change_cycles)
                    VALUES (?, ?, ?, ?, ?)
                """, (code, name, desc, filter_type, filter_cycles))
            except sqlite3.IntegrityError:
                pass

        containers = [
            ("CNT-001", "Konteyner A-01", "RIGID_M", "Aesculap", "JK789", "Mavi"),
            ("CNT-002", "Konteyner A-02", "RIGID_M", "Aesculap", "JK789", "Mavi"),
            ("CNT-003", "Konteyner B-01", "RIGID_L", "Aesculap", "JN440", "Yeşil"),
            ("CNT-004", "Konteyner B-02", "RIGID_L", "Aesculap", "JN440", "Yeşil"),
            ("CNT-005", "Konteyner C-01", "RIGID_S", "Case Medical", "SteriTite", "Gri"),
            ("CNT-006", "Flash Konteyner 1", "FLASH", "Aesculap", "JK100", "Kırmızı"),
        ]

        for barcode, name, c_type, brand, model, color in containers:
            try:
                cursor.execute("""
                    INSERT INTO containers (barcode, name, container_type, brand, model, color, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'AVAILABLE')
                """, (barcode, name, c_type, brand, model, color))
                print(f"    + {barcode} - {name}")
            except sqlite3.IntegrityError:
                pass

        # ==================== DEPO KONUMLARI ====================
        print("\n[9/9] Depo konumları oluşturuluyor...")
        locations = [
            ("STERILE", "LOC-A1-01", "Raf A1-01", "SHELF", "A1", "1", "01", 10),
            ("STERILE", "LOC-A1-02", "Raf A1-02", "SHELF", "A1", "1", "02", 10),
            ("STERILE", "LOC-A2-01", "Raf A2-01", "SHELF", "A2", "2", "01", 10),
            ("STERILE", "LOC-A2-02", "Raf A2-02", "SHELF", "A2", "2", "02", 10),
            ("STERILE", "LOC-B1-01", "Raf B1-01", "SHELF", "B1", "1", "01", 8),
            ("STERILE", "LOC-CART-01", "Dağıtım Arabası 1", "CART", None, None, None, 20),
        ]

        for zone_code, barcode, name, loc_type, shelf, row, col, capacity in locations:
            try:
                zone_id = zone_ids.get(zone_code)
                cursor.execute("""
                    INSERT INTO storage_locations (zone_id, barcode, name, location_type,
                                                  shelf, row, column, capacity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (zone_id, barcode, name, loc_type, shelf, row, col, capacity))
                print(f"    + {barcode} - {name}")
            except sqlite3.IntegrityError:
                pass

        conn.commit()

    print("\n" + "=" * 60)
    print("  DEMO VERİ YÜKLEME TAMAMLANDI!")
    print("=" * 60)
    print("""
Yüklenen veriler:
  - 3 Çalışma Alanı (Kirli, Temiz, Steril)
  - 8 Operatör (kart ile giriş)
  - 7 Bölüm
  - 8 Makine (Yıkama + Sterilizatör)
  - 8 Alet Kategorisi
  - 31 Cerrahi Alet
  - 9 Cerrahi Set
  - 6 Konteyner
  - 6 Depo Konumu

Test için kart ID'leri:
  - CARD001: Ayşe Yılmaz (Şef - Tüm alanlar)
  - CARD002: Fatma Kaya (Kirli + Temiz)
  - CARD005: Emine Çelik (Sadece Steril)
""")


if __name__ == "__main__":
    print("Veritabanı başlatılıyor...")
    init_database()
    print("\nDemo veri ekleniyor...")
    insert_demo_data()
    print("\nTamamlandı!")
