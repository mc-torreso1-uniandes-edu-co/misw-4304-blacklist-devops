from typing import Optional

from app.application.ports.blacklist_repository import BlacklistRepository
from app.domain.blacklist_entry import BlacklistEntry


class CheckEmailInBlacklist:
    def __init__(self, repository: BlacklistRepository):
        self._repository = repository

    def execute(self, email: str) -> Optional[BlacklistEntry]:
        raise NotImplementedError
