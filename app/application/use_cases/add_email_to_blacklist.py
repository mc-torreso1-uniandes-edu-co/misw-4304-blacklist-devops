from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.ports.blacklist_repository import BlacklistRepository
from app.domain.blacklist_entry import BlacklistEntry
from app.domain.errors import EmailAlreadyBlacklistedError


class AddEmailToBlacklist:
    def __init__(self, repository: BlacklistRepository):
        self._repository = repository

    def execute(
        self,
        email: str,
        app_uuid: UUID,
        blocked_reason: Optional[str],
        ip_address: str,
        requested_at: datetime,
    ) -> BlacklistEntry:
        if self._repository.find_by_email(email) is not None:
            raise EmailAlreadyBlacklistedError(email)
        entry = BlacklistEntry(
            email=email,
            app_uuid=app_uuid,
            blocked_reason=blocked_reason,
            ip_address=ip_address,
            created_at=requested_at,
        )
        self._repository.add(entry)
        return entry
