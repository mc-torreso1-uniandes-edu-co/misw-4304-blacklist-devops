from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.ports.blacklist_repository import BlacklistRepository
from app.domain.blacklist_entry import BlacklistEntry


class AddEmailToBlacklist:
    def __init__(self, repository: BlacklistRepository):
        self._repository = repository

    def execute(
        self,
        email: str,
        app_uuid: UUID,
        blocked_reason: Optional[str],
        request_ip: str,
        requested_at: datetime,
    ) -> BlacklistEntry:
        raise NotImplementedError
