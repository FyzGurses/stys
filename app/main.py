import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.ui.main_window import MainWindow
from app.core.database import get_db


def init_database():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            level INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_number TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            pin_hash TEXT,
            role_id INTEGER REFERENCES roles(id),
            default_zone TEXT DEFAULT 'DIRTY',
            workstation_id INTEGER,
            is_active INTEGER DEFAULT 1,
            can_approve_sterilization INTEGER DEFAULT 0,
            can_release_load INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine_type TEXT NOT NULL,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            zone TEXT,
            status TEXT DEFAULT 'IDLE',
            current_cycle_id INTEGER,
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            total_cycles INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS machine_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER REFERENCES machines(id),
            name TEXT NOT NULL,
            code TEXT,
            temperature REAL,
            pressure REAL,
            duration_minutes INTEGER,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS machine_cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_number TEXT UNIQUE NOT NULL,
            machine_id INTEGER REFERENCES machines(id),
            program_id INTEGER REFERENCES machine_programs(id),
            operator_id INTEGER REFERENCES operators(id),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'IDLE',
            temperature_achieved REAL,
            pressure_achieved REAL,
            ci_result TEXT DEFAULT 'PENDING',
            bi_lot_number TEXT,
            bi_result TEXT DEFAULT 'PENDING',
            bi_read_time TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            manufacturer TEXT,
            model_number TEXT,
            serial_number TEXT,
            max_cycles INTEGER DEFAULT 0,
            current_cycles INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ACTIVE',
            location TEXT,
            last_sterilization TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS instrument_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            department_id INTEGER REFERENCES departments(id),
            container_type TEXT,
            sterilization_method TEXT DEFAULT 'STEAM',
            validity_days INTEGER DEFAULT 30,
            status TEXT DEFAULT 'ACTIVE',
            total_instruments INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS set_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER REFERENCES instrument_sets(id),
            instrument_id INTEGER REFERENCES instruments(id),
            quantity INTEGER DEFAULT 1,
            is_mandatory INTEGER DEFAULT 1,
            position TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            barcode TEXT,
            item_type TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT,
            item_barcode TEXT,
            department_id INTEGER REFERENCES departments(id),
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'RECEIVED',
            current_zone TEXT DEFAULT 'DIRTY',
            source_department TEXT,
            destination_department TEXT,
            received_by INTEGER REFERENCES operators(id),
            received_at TIMESTAMP,
            notes TEXT,
            is_urgent INTEGER DEFAULT 0,
            due_date TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS process_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER REFERENCES work_orders(id),
            process_type TEXT NOT NULL,
            zone TEXT,
            workstation_id INTEGER,
            operator_id INTEGER REFERENCES operators(id),
            machine_id INTEGER REFERENCES machines(id),
            cycle_id INTEGER REFERENCES machine_cycles(id),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT,
            result TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS cycle_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER REFERENCES machine_cycles(id),
            work_order_id INTEGER REFERENCES work_orders(id),
            loaded_at TIMESTAMP,
            unloaded_at TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS sterilization_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_number TEXT UNIQUE NOT NULL,
            work_order_id INTEGER REFERENCES work_orders(id),
            item_type TEXT,
            item_id INTEGER,
            item_name TEXT,
            item_barcode TEXT,
            cycle_id INTEGER REFERENCES machine_cycles(id),
            machine_id INTEGER REFERENCES machines(id),
            sterilization_method TEXT,
            operator_id INTEGER REFERENCES operators(id),
            load_time TIMESTAMP,
            unload_time TIMESTAMP,
            status TEXT DEFAULT 'PENDING_CI',
            ci_result TEXT DEFAULT 'PENDING',
            ci_checked_by INTEGER REFERENCES operators(id),
            ci_checked_at TIMESTAMP,
            bi_lot_number TEXT,
            bi_result TEXT DEFAULT 'PENDING',
            bi_incubation_start TIMESTAMP,
            bi_read_by INTEGER REFERENCES operators(id),
            bi_read_at TIMESTAMP,
            released_by INTEGER REFERENCES operators(id),
            released_at TIMESTAMP,
            rejected_by INTEGER REFERENCES operators(id),
            rejected_at TIMESTAMP,
            rejection_reason TEXT,
            expiry_date TIMESTAMP,
            storage_location TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS sterilization_release_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sterilization_id INTEGER REFERENCES sterilization_records(id),
            action TEXT NOT NULL,
            performed_by INTEGER REFERENCES operators(id),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS reprocessing_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER REFERENCES work_orders(id),
            reason TEXT,
            initiated_by INTEGER REFERENCES operators(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_id INTEGER REFERENCES operators(id),
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()

    existing = db.fetchone("SELECT id FROM roles WHERE code = 'ADMIN'")
    if not existing:
        db.execute("INSERT INTO roles (code, name, level) VALUES ('ADMIN', 'Yönetici', 100)")
        db.execute("INSERT INTO roles (code, name, level) VALUES ('SUPERVISOR', 'Süpervizör', 80)")
        db.execute("INSERT INTO roles (code, name, level) VALUES ('OPERATOR', 'Operatör', 50)")
        db.execute("INSERT INTO roles (code, name, level) VALUES ('NURSE', 'Hemşire', 40)")
        db.execute("INSERT INTO roles (code, name, level) VALUES ('VIEWER', 'İzleyici', 10)")

        import hashlib
        pin_hash = hashlib.sha256("1234".encode()).hexdigest()

        db.execute("""
            INSERT INTO operators (badge_number, full_name, pin_hash, role_id, can_release_load)
            VALUES ('ADMIN001', 'Sistem Yöneticisi', ?, 1, 1)
        """, (pin_hash,))

        db.execute("""
            INSERT INTO departments (name, code) VALUES
            ('Ameliyathane', 'AME'),
            ('Endoskopi', 'END'),
            ('Yoğun Bakım', 'YBU'),
            ('Acil', 'ACL')
        """)

        db.execute("""
            INSERT INTO machines (name, machine_type, zone, status) VALUES
            ('Yıkama-1', 'WASHER_DISINFECTOR', 'DIRTY', 'IDLE'),
            ('Yıkama-2', 'WASHER_DISINFECTOR', 'DIRTY', 'IDLE'),
            ('Otoklav-1', 'STEAM', 'STERILE', 'IDLE'),
            ('Otoklav-2', 'STEAM', 'STERILE', 'IDLE'),
            ('Plazma-1', 'PLASMA', 'STERILE', 'IDLE')
        """)

        db.commit()


def main():
    init_database()

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
