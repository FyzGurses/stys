from typing import Optional, List, Dict, Tuple
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.instrument import Instrument, InstrumentSet, SetContent


class InstrumentService:

    def __init__(self):
        self.db = get_db()

    def _generate_barcode(self, prefix: str) -> str:
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def get_all_instruments(self, category: str = None,
                           status: str = None) -> List[Instrument]:
        query = "SELECT * FROM instruments WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY name"
        rows = self.db.fetchall(query, tuple(params))

        return [Instrument(
            id=row['id'],
            barcode=row['barcode'],
            name=row['name'],
            description=row['description'] or "",
            category=row['category'] or "",
            manufacturer=row['manufacturer'] or "",
            model_number=row['model_number'] or "",
            serial_number=row['serial_number'] or "",
            max_cycles=row['max_cycles'] or 0,
            current_cycles=row['current_cycles'] or 0,
            status=row['status'],
            location=row['location'] or "",
            last_sterilization=row['last_sterilization'],
            created_at=row['created_at']
        ) for row in rows]

    def get_instrument(self, instrument_id: int) -> Optional[Instrument]:
        row = self.db.fetchone(
            "SELECT * FROM instruments WHERE id = ?",
            (instrument_id,)
        )
        if not row:
            return None

        return Instrument(
            id=row['id'],
            barcode=row['barcode'],
            name=row['name'],
            description=row['description'] or "",
            category=row['category'] or "",
            manufacturer=row['manufacturer'] or "",
            model_number=row['model_number'] or "",
            serial_number=row['serial_number'] or "",
            max_cycles=row['max_cycles'] or 0,
            current_cycles=row['current_cycles'] or 0,
            status=row['status'],
            location=row['location'] or "",
            last_sterilization=row['last_sterilization'],
            created_at=row['created_at']
        )

    def get_instrument_by_barcode(self, barcode: str) -> Optional[Instrument]:
        row = self.db.fetchone(
            "SELECT id FROM instruments WHERE barcode = ?",
            (barcode,)
        )
        if row:
            return self.get_instrument(row['id'])
        return None

    def create_instrument(self, data: Dict) -> Tuple[bool, str, Optional[int]]:
        barcode = data.get('barcode') or self._generate_barcode("ALT")

        existing = self.get_instrument_by_barcode(barcode)
        if existing:
            return False, "Bu barkod zaten kayıtlı", None

        try:
            self.db.execute("""
                INSERT INTO instruments (
                    barcode, name, description, category, manufacturer,
                    model_number, serial_number, max_cycles, status,
                    location, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                barcode,
                data['name'],
                data.get('description', ''),
                data.get('category', ''),
                data.get('manufacturer', ''),
                data.get('model_number', ''),
                data.get('serial_number', ''),
                data.get('max_cycles', 0),
                'ACTIVE',
                data.get('location', ''),
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            instrument_id = self.db.get_last_insert_id()
            return True, "Alet oluşturuldu", instrument_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def update_instrument(self, instrument_id: int, data: Dict) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE instruments SET
                    name = COALESCE(?, name),
                    description = COALESCE(?, description),
                    category = COALESCE(?, category),
                    manufacturer = COALESCE(?, manufacturer),
                    model_number = COALESCE(?, model_number),
                    serial_number = COALESCE(?, serial_number),
                    max_cycles = COALESCE(?, max_cycles),
                    status = COALESCE(?, status),
                    location = COALESCE(?, location),
                    updated_at = ?
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('description'),
                data.get('category'),
                data.get('manufacturer'),
                data.get('model_number'),
                data.get('serial_number'),
                data.get('max_cycles'),
                data.get('status'),
                data.get('location'),
                datetime.now(),
                instrument_id
            ))
            self.db.commit()
            return True, "Alet güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def increment_cycle_count(self, instrument_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE instruments SET
                    current_cycles = current_cycles + 1,
                    last_sterilization = ?,
                    updated_at = ?
                WHERE id = ?
            """, (datetime.now(), datetime.now(), instrument_id))
            self.db.commit()
            return True, "Sayaç güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_all_sets(self, department_id: int = None,
                    status: str = None) -> List[InstrumentSet]:
        query = """
            SELECT s.*, d.name as department_name
            FROM instrument_sets s
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE 1=1
        """
        params = []

        if department_id:
            query += " AND s.department_id = ?"
            params.append(department_id)

        if status:
            query += " AND s.status = ?"
            params.append(status)

        query += " ORDER BY s.name"
        rows = self.db.fetchall(query, tuple(params))

        return [InstrumentSet(
            id=row['id'],
            barcode=row['barcode'],
            name=row['name'],
            description=row['description'] or "",
            category=row['category'] or "",
            department_id=row['department_id'],
            department_name=row['department_name'] or "",
            container_type=row['container_type'] or "",
            sterilization_method=row['sterilization_method'] or "STEAM",
            validity_days=row['validity_days'] or 30,
            status=row['status'],
            total_instruments=row['total_instruments'] or 0,
            created_at=row['created_at']
        ) for row in rows]

    def get_set(self, set_id: int) -> Optional[InstrumentSet]:
        row = self.db.fetchone("""
            SELECT s.*, d.name as department_name
            FROM instrument_sets s
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE s.id = ?
        """, (set_id,))

        if not row:
            return None

        instrument_set = InstrumentSet(
            id=row['id'],
            barcode=row['barcode'],
            name=row['name'],
            description=row['description'] or "",
            category=row['category'] or "",
            department_id=row['department_id'],
            department_name=row['department_name'] or "",
            container_type=row['container_type'] or "",
            sterilization_method=row['sterilization_method'] or "STEAM",
            validity_days=row['validity_days'] or 30,
            status=row['status'],
            total_instruments=row['total_instruments'] or 0,
            created_at=row['created_at']
        )

        instrument_set.contents = self._get_set_contents(set_id)
        return instrument_set

    def get_set_by_barcode(self, barcode: str) -> Optional[InstrumentSet]:
        row = self.db.fetchone(
            "SELECT id FROM instrument_sets WHERE barcode = ?",
            (barcode,)
        )
        if row:
            return self.get_set(row['id'])
        return None

    def create_set(self, data: Dict) -> Tuple[bool, str, Optional[int]]:
        barcode = data.get('barcode') or self._generate_barcode("SET")

        existing = self.get_set_by_barcode(barcode)
        if existing:
            return False, "Bu barkod zaten kayıtlı", None

        try:
            self.db.execute("""
                INSERT INTO instrument_sets (
                    barcode, name, description, category, department_id,
                    container_type, sterilization_method, validity_days,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                barcode,
                data['name'],
                data.get('description', ''),
                data.get('category', ''),
                data.get('department_id'),
                data.get('container_type', ''),
                data.get('sterilization_method', 'STEAM'),
                data.get('validity_days', 30),
                'ACTIVE',
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            set_id = self.db.get_last_insert_id()
            return True, "Set oluşturuldu", set_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def update_set(self, set_id: int, data: Dict) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE instrument_sets SET
                    name = COALESCE(?, name),
                    description = COALESCE(?, description),
                    category = COALESCE(?, category),
                    department_id = COALESCE(?, department_id),
                    container_type = COALESCE(?, container_type),
                    sterilization_method = COALESCE(?, sterilization_method),
                    validity_days = COALESCE(?, validity_days),
                    status = COALESCE(?, status),
                    updated_at = ?
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('description'),
                data.get('category'),
                data.get('department_id'),
                data.get('container_type'),
                data.get('sterilization_method'),
                data.get('validity_days'),
                data.get('status'),
                datetime.now(),
                set_id
            ))
            self.db.commit()
            return True, "Set güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def add_instrument_to_set(self, set_id: int, instrument_id: int,
                             quantity: int = 1, is_mandatory: bool = True,
                             position: str = "") -> Tuple[bool, str]:
        try:
            self.db.execute("""
                INSERT INTO set_contents (
                    set_id, instrument_id, quantity, is_mandatory, position
                ) VALUES (?, ?, ?, ?, ?)
            """, (set_id, instrument_id, quantity, is_mandatory, position))

            self.db.execute("""
                UPDATE instrument_sets SET
                    total_instruments = (
                        SELECT SUM(quantity) FROM set_contents WHERE set_id = ?
                    ),
                    updated_at = ?
                WHERE id = ?
            """, (set_id, datetime.now(), set_id))

            self.db.commit()
            return True, "Alet eklendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def remove_instrument_from_set(self, set_id: int,
                                  instrument_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                DELETE FROM set_contents
                WHERE set_id = ? AND instrument_id = ?
            """, (set_id, instrument_id))

            self.db.execute("""
                UPDATE instrument_sets SET
                    total_instruments = COALESCE((
                        SELECT SUM(quantity) FROM set_contents WHERE set_id = ?
                    ), 0),
                    updated_at = ?
                WHERE id = ?
            """, (set_id, datetime.now(), set_id))

            self.db.commit()
            return True, "Alet çıkarıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _get_set_contents(self, set_id: int) -> List[SetContent]:
        rows = self.db.fetchall("""
            SELECT sc.*, i.barcode, i.name, i.status
            FROM set_contents sc
            JOIN instruments i ON sc.instrument_id = i.id
            WHERE sc.set_id = ?
            ORDER BY sc.position, i.name
        """, (set_id,))

        contents = []
        for row in rows:
            content = SetContent(
                id=row['id'],
                set_id=row['set_id'],
                instrument_id=row['instrument_id'],
                quantity=row['quantity'],
                is_mandatory=bool(row['is_mandatory']),
                position=row['position'] or ""
            )
            content.instrument = Instrument(
                id=row['instrument_id'],
                barcode=row['barcode'],
                name=row['name'],
                status=row['status']
            )
            contents.append(content)
        return contents

    def get_categories(self) -> List[str]:
        rows = self.db.fetchall("""
            SELECT DISTINCT category FROM instruments
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """)
        return [row['category'] for row in rows]

    def search_instruments(self, query: str) -> List[Instrument]:
        search = f"%{query}%"
        rows = self.db.fetchall("""
            SELECT id FROM instruments
            WHERE name LIKE ? OR barcode LIKE ? OR description LIKE ?
            ORDER BY name
            LIMIT 50
        """, (search, search, search))
        return [self.get_instrument(row['id']) for row in rows]

    def search_sets(self, query: str) -> List[InstrumentSet]:
        search = f"%{query}%"
        rows = self.db.fetchall("""
            SELECT id FROM instrument_sets
            WHERE name LIKE ? OR barcode LIKE ? OR description LIKE ?
            ORDER BY name
            LIMIT 50
        """, (search, search, search))
        return [self.get_set(row['id']) for row in rows]
