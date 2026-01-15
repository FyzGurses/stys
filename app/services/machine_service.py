from typing import Optional, List, Dict, Tuple
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.session import current_session
from app.models.machine import Machine, MachineProgram, MachineCycle
from app.config.constants import MachineStatus, MachineTypes, Zones


class MachineService:

    def __init__(self):
        self.db = get_db()

    def get_all_machines(self, zone: str = None, category: str = None) -> List[Machine]:
        query = "SELECT * FROM machines WHERE is_active = 1"
        params = []

        if zone:
            query += " AND zone = ?"
            params.append(zone)

        if category:
            types = [k for k, v in MachineTypes.CATEGORIES.items() if v == category]
            if types:
                placeholders = ','.join(['?' for _ in types])
                query += f" AND machine_type IN ({placeholders})"
                params.extend(types)

        query += " ORDER BY name"
        rows = self.db.fetchall(query, tuple(params))

        machines = []
        for row in rows:
            machine = Machine(
                id=row['id'],
                name=row['name'],
                machine_type=row['machine_type'],
                manufacturer=row['manufacturer'],
                model=row['model'],
                serial_number=row['serial_number'],
                zone=row['zone'],
                status=row['status'],
                current_cycle_id=row['current_cycle_id'],
                last_maintenance=row['last_maintenance'],
                next_maintenance=row['next_maintenance'],
                total_cycles=row['total_cycles'],
                is_active=bool(row['is_active'])
            )
            machine.programs = self._get_machine_programs(row['id'])
            machines.append(machine)
        return machines

    def get_machine(self, machine_id: int) -> Optional[Machine]:
        row = self.db.fetchone("SELECT * FROM machines WHERE id = ?", (machine_id,))
        if not row:
            return None

        machine = Machine(
            id=row['id'],
            name=row['name'],
            machine_type=row['machine_type'],
            manufacturer=row['manufacturer'],
            model=row['model'],
            serial_number=row['serial_number'],
            zone=row['zone'],
            status=row['status'],
            current_cycle_id=row['current_cycle_id'],
            last_maintenance=row['last_maintenance'],
            next_maintenance=row['next_maintenance'],
            total_cycles=row['total_cycles'],
            is_active=bool(row['is_active'])
        )
        machine.programs = self._get_machine_programs(machine_id)
        return machine

    def get_available_machines(self, zone: str, category: str) -> List[Machine]:
        machines = self.get_all_machines(zone, category)
        return [m for m in machines if m.is_available]

    def create_machine(self, data: Dict) -> Tuple[bool, str, Optional[int]]:
        try:
            self.db.execute("""
                INSERT INTO machines (
                    name, machine_type, manufacturer, model, serial_number,
                    zone, status, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'],
                data['machine_type'],
                data.get('manufacturer', ''),
                data.get('model', ''),
                data.get('serial_number', ''),
                data.get('zone', Zones.DIRTY),
                MachineStatus.IDLE,
                True,
                datetime.now(),
                datetime.now()
            ))
            self.db.commit()
            machine_id = self.db.get_last_insert_id()
            return True, "Makine oluşturuldu", machine_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def update_machine(self, machine_id: int, data: Dict) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE machines SET
                    name = COALESCE(?, name),
                    machine_type = COALESCE(?, machine_type),
                    manufacturer = COALESCE(?, manufacturer),
                    model = COALESCE(?, model),
                    serial_number = COALESCE(?, serial_number),
                    zone = COALESCE(?, zone),
                    is_active = COALESCE(?, is_active),
                    updated_at = ?
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('machine_type'),
                data.get('manufacturer'),
                data.get('model'),
                data.get('serial_number'),
                data.get('zone'),
                data.get('is_active'),
                datetime.now(),
                machine_id
            ))
            self.db.commit()
            return True, "Makine güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def set_status(self, machine_id: int, status: str) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                UPDATE machines SET status = ?, updated_at = ? WHERE id = ?
            """, (status, datetime.now(), machine_id))
            self.db.commit()
            return True, "Durum güncellendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def _generate_cycle_number(self, machine_id: int) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        count = self.db.fetchone("""
            SELECT COUNT(*) as cnt FROM machine_cycles
            WHERE machine_id = ? AND cycle_number LIKE ?
        """, (machine_id, f"C{date_part}%"))
        seq = (count['cnt'] or 0) + 1
        return f"C{date_part}M{machine_id:02d}{seq:03d}"

    def start_cycle(self, machine_id: int, program_id: int = None) -> Tuple[bool, str, Optional[int]]:
        if not current_session.current_user:
            return False, "Oturum açık değil", None

        machine = self.get_machine(machine_id)
        if not machine:
            return False, "Makine bulunamadı", None

        if not machine.is_available:
            return False, "Makine kullanılabilir değil", None

        cycle_number = self._generate_cycle_number(machine_id)

        try:
            self.db.execute("""
                INSERT INTO machine_cycles (
                    cycle_number, machine_id, program_id, operator_id,
                    start_time, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                cycle_number,
                machine_id,
                program_id,
                current_session.current_user.user_id,
                datetime.now(),
                MachineStatus.RUNNING,
                datetime.now()
            ))

            cycle_id = self.db.get_last_insert_id()

            self.db.execute("""
                UPDATE machines SET
                    status = ?,
                    current_cycle_id = ?,
                    updated_at = ?
                WHERE id = ?
            """, (MachineStatus.RUNNING, cycle_id, datetime.now(), machine_id))

            self.db.commit()
            return True, "Çevrim başlatıldı", cycle_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None

    def complete_cycle(self, cycle_id: int, temperature: float = 0,
                      pressure: float = 0, ci_result: str = "PENDING") -> Tuple[bool, str]:
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return False, "Çevrim bulunamadı"

        try:
            self.db.execute("""
                UPDATE machine_cycles SET
                    end_time = ?,
                    status = ?,
                    temperature_achieved = ?,
                    pressure_achieved = ?,
                    ci_result = ?
                WHERE id = ?
            """, (
                datetime.now(),
                MachineStatus.COMPLETED,
                temperature,
                pressure,
                ci_result,
                cycle_id
            ))

            self.db.execute("""
                UPDATE machines SET
                    status = ?,
                    current_cycle_id = NULL,
                    total_cycles = total_cycles + 1,
                    updated_at = ?
                WHERE id = ?
            """, (MachineStatus.IDLE, datetime.now(), cycle.machine_id))

            self.db.commit()
            return True, "Çevrim tamamlandı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def abort_cycle(self, cycle_id: int, reason: str) -> Tuple[bool, str]:
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return False, "Çevrim bulunamadı"

        try:
            self.db.execute("""
                UPDATE machine_cycles SET
                    end_time = ?,
                    status = ?,
                    notes = ?
                WHERE id = ?
            """, (datetime.now(), MachineStatus.ERROR, reason, cycle_id))

            self.db.execute("""
                UPDATE machines SET
                    status = ?,
                    current_cycle_id = NULL,
                    updated_at = ?
                WHERE id = ?
            """, (MachineStatus.ERROR, datetime.now(), cycle.machine_id))

            self.db.commit()
            return True, "Çevrim iptal edildi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_cycle(self, cycle_id: int) -> Optional[MachineCycle]:
        row = self.db.fetchone("""
            SELECT mc.*, m.name as machine_name, mp.name as program_name,
                   o.full_name as operator_name
            FROM machine_cycles mc
            LEFT JOIN machines m ON mc.machine_id = m.id
            LEFT JOIN machine_programs mp ON mc.program_id = mp.id
            LEFT JOIN operators o ON mc.operator_id = o.id
            WHERE mc.id = ?
        """, (cycle_id,))

        if not row:
            return None

        cycle = MachineCycle(
            id=row['id'],
            cycle_number=row['cycle_number'],
            machine_id=row['machine_id'],
            machine_name=row['machine_name'] or "",
            program_id=row['program_id'],
            program_name=row['program_name'] or "",
            operator_id=row['operator_id'],
            operator_name=row['operator_name'] or "",
            start_time=row['start_time'],
            end_time=row['end_time'],
            status=row['status'],
            temperature_achieved=row['temperature_achieved'] or 0,
            pressure_achieved=row['pressure_achieved'] or 0,
            ci_result=row['ci_result'] or "PENDING",
            bi_lot_number=row['bi_lot_number'] or "",
            bi_result=row['bi_result'] or "PENDING",
            notes=row['notes'] or ""
        )

        contents = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM cycle_contents WHERE cycle_id = ?",
            (cycle_id,)
        )
        cycle.contents_count = contents['cnt'] if contents else 0

        return cycle

    def get_cycle_contents(self, cycle_id: int) -> List[Dict]:
        rows = self.db.fetchall("""
            SELECT cc.*, wo.order_number, wo.item_name, wo.item_barcode
            FROM cycle_contents cc
            JOIN work_orders wo ON cc.work_order_id = wo.id
            WHERE cc.cycle_id = ?
        """, (cycle_id,))

        return [dict(row) for row in rows]

    def add_to_cycle(self, cycle_id: int, work_order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                INSERT INTO cycle_contents (cycle_id, work_order_id, loaded_at)
                VALUES (?, ?, ?)
            """, (cycle_id, work_order_id, datetime.now()))
            self.db.commit()
            return True, "Eklendi"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def remove_from_cycle(self, cycle_id: int, work_order_id: int) -> Tuple[bool, str]:
        try:
            self.db.execute("""
                DELETE FROM cycle_contents
                WHERE cycle_id = ? AND work_order_id = ?
            """, (cycle_id, work_order_id))
            self.db.commit()
            return True, "Çıkarıldı"
        except Exception as e:
            self.db.rollback()
            return False, str(e)

    def get_active_cycles(self) -> List[MachineCycle]:
        rows = self.db.fetchall("""
            SELECT id FROM machine_cycles WHERE status = ?
        """, (MachineStatus.RUNNING,))
        return [self.get_cycle(row['id']) for row in rows]

    def get_recent_cycles(self, machine_id: int = None, limit: int = 20) -> List[MachineCycle]:
        query = "SELECT id FROM machine_cycles"
        params = []

        if machine_id:
            query += " WHERE machine_id = ?"
            params.append(machine_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = self.db.fetchall(query, tuple(params))
        return [self.get_cycle(row['id']) for row in rows]

    def _get_machine_programs(self, machine_id: int) -> List[MachineProgram]:
        rows = self.db.fetchall("""
            SELECT * FROM machine_programs
            WHERE machine_id = ? AND is_active = 1
            ORDER BY name
        """, (machine_id,))

        return [MachineProgram(
            id=row['id'],
            machine_id=row['machine_id'],
            name=row['name'],
            code=row['code'] or "",
            temperature=row['temperature'] or 0,
            pressure=row['pressure'] or 0,
            duration_minutes=row['duration_minutes'] or 0,
            description=row['description'] or "",
            is_active=bool(row['is_active'])
        ) for row in rows]

    def add_program(self, machine_id: int, data: Dict) -> Tuple[bool, str, Optional[int]]:
        try:
            self.db.execute("""
                INSERT INTO machine_programs (
                    machine_id, name, code, temperature, pressure,
                    duration_minutes, description, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                machine_id,
                data['name'],
                data.get('code', ''),
                data.get('temperature', 0),
                data.get('pressure', 0),
                data.get('duration_minutes', 0),
                data.get('description', ''),
                True,
                datetime.now()
            ))
            self.db.commit()
            program_id = self.db.get_last_insert_id()
            return True, "Program eklendi", program_id
        except Exception as e:
            self.db.rollback()
            return False, str(e), None
