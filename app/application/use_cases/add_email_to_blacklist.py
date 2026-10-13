from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.ports.blacklist_repository import BlacklistRepository
from app.domain.blacklist_entry import BlacklistEntry
from app.domain.email import normalize_email
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
        normalized_email = normalize_email(email)
        if self._repository.find_by_email(normalized_email) is not None:
            raise EmailAlreadyBlacklistedError(normalized_email)
        entry = BlacklistEntry(
            email=normalized_email,
            app_uuid=app_uuid,
            blocked_reason=blocked_reason,
            ip_address=ip_address,
            created_at=requested_at,
        )
        return self._repository.add(entry)
