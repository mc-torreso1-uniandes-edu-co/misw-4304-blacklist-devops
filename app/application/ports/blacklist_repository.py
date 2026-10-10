from abc import ABC, abstractmethod
from typing import Optional

from app.domain.blacklist_entry import BlacklistEntry


class BlacklistRepository(ABC):
    @abstractmethod
    def add(self, entry: BlacklistEntry) -> None:
        ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[BlacklistEntry]:
        ...
