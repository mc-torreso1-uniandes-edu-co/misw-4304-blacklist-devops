from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class BlacklistEntry:
    email: str
    app_uuid: UUID
    blocked_reason: Optional[str]
    ip_address: str
    created_at: datetime
