class Roles:
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    OPERATOR = "OPERATOR"
    NURSE = "NURSE"
    VIEWER = "VIEWER"

    @classmethod
    def all(cls):
        return [cls.ADMIN, cls.SUPERVISOR, cls.OPERATOR, cls.NURSE, cls.VIEWER]

    @classmethod
    def get_level(cls, role: str) -> int:
        levels = {
            cls.ADMIN: 100,
            cls.SUPERVISOR: 80,
            cls.OPERATOR: 50,
            cls.NURSE: 40,
            cls.VIEWER: 10,
        }
        return levels.get(role, 0)


class Zones:
    DIRTY = "DIRTY"
    CLEAN = "CLEAN"
    STERILE = "STERILE"

    NAMES = {
        DIRTY: "Kirli Alan",
        CLEAN: "Temiz Alan",
        STERILE: "Steril Alan",
    }

    COLORS = {
        DIRTY: "#e74c3c",
        CLEAN: "#f39c12",
        STERILE: "#27ae60",
    }


class WorkOrderStatus:
    RECEIVED = "RECEIVED"
    WASHING = "WASHING"
    WASHED = "WASHED"
    INSPECTING = "INSPECTING"
    INSPECTION_FAILED = "INSPECTION_FAILED"
    PACKAGING = "PACKAGING"
    PACKAGED = "PACKAGED"
    STERILIZING = "STERILIZING"
    STERILIZED = "STERILIZED"
    PENDING_RELEASE = "PENDING_RELEASE"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"
    STORED = "STORED"
    DISTRIBUTED = "DISTRIBUTED"
    REPROCESSING = "REPROCESSING"
    RECALLED = "RECALLED"
    COMPLETED = "COMPLETED"

    @classmethod
    def get_zone(cls, status: str) -> str:
        dirty = [cls.RECEIVED, cls.WASHING, cls.WASHED]
        clean = [cls.INSPECTING, cls.INSPECTION_FAILED, cls.PACKAGING, cls.PACKAGED]
        sterile = [cls.STERILIZING, cls.STERILIZED, cls.PENDING_RELEASE,
                   cls.RELEASED, cls.REJECTED, cls.STORED, cls.DISTRIBUTED]

        if status in dirty:
            return Zones.DIRTY
        elif status in clean:
            return Zones.CLEAN
        elif status in sterile:
            return Zones.STERILE
        return None


class SterilizationStatus:
    PENDING_CI = "PENDING_CI"
    PENDING_BI = "PENDING_BI"
    PENDING_RELEASE = "PENDING_RELEASE"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"
    RECALLED = "RECALLED"
    EXPIRED = "EXPIRED"
    USED = "USED"


class MachineTypes:
    WASHER_DISINFECTOR = "WASHER_DISINFECTOR"
    ULTRASONIC = "ULTRASONIC"
    MANUAL_SINK = "MANUAL_SINK"
    STEAM = "STEAM"
    PLASMA = "PLASMA"
    ETO = "ETO"
    DRY_HEAT = "DRY_HEAT"

    CATEGORIES = {
        WASHER_DISINFECTOR: "WASHER",
        ULTRASONIC: "WASHER",
        MANUAL_SINK: "WASHER",
        STEAM: "STERILIZER",
        PLASMA: "STERILIZER",
        ETO: "STERILIZER",
        DRY_HEAT: "STERILIZER",
    }


class MachineStatus:
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class PackagingTypes:
    WRAP_SINGLE = "WRAP_SINGLE"
    WRAP_DOUBLE = "WRAP_DOUBLE"
    POUCH = "POUCH"
    CONTAINER = "CONTAINER"
    PEEL_PACK = "PEEL_PACK"


class IndicatorResults:
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    NOT_APPLICABLE = "N/A"


class IncidentTypes:
    DAMAGE = "DAMAGE"
    LOST = "LOST"
    CONTAMINATION = "CONTAMINATION"
    STERILITY_BREACH = "STERILITY_BREACH"
    MACHINE_FAILURE = "MACHINE_FAILURE"
    PROCESS_DEVIATION = "PROCESS_DEVIATION"
    RECALL = "RECALL"
    OTHER = "OTHER"


class SeverityLevels:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditActions:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RELEASE = "RELEASE"
    RECALL = "RECALL"
    PRINT = "PRINT"
    SCAN = "SCAN"
