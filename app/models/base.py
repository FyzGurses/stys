from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class BaseModel:
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @classmethod
    def from_row(cls, row) -> Optional['BaseModel']:
        if row is None:
            return None
        return cls(**dict(row))

    @classmethod
    def from_rows(cls, rows) -> List['BaseModel']:
        return [cls.from_row(row) for row in rows if row]
