from typing import Optional

from sqlalchemy.orm import scoped_session

from app.application.ports.blacklist_repository import BlacklistRepository
from app.domain.blacklist_entry import BlacklistEntry


class SqlAlchemyBlacklistRepository(BlacklistRepository):
    def __init__(self, session: scoped_session):
        self._session = session

    def add(self, entry: BlacklistEntry) -> None:
        raise NotImplementedError

    def find_by_email(self, email: str) -> Optional[BlacklistEntry]:
        raise NotImplementedError
